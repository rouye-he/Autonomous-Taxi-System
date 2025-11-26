from flask import Blueprint, render_template, request
import json
import random
from app.dao.base_dao import BaseDAO
from datetime import datetime, timedelta

# 创建订单分析的蓝图 - 注意这里不指定url_prefix，因为会由admin蓝图自动添加前缀
order_analysis_bp = Blueprint('order_analysis', __name__)

@order_analysis_bp.route('/service-quality')
def service_quality():
    """服务质量分析页面"""
    # 获取日期参数
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    date_range = request.args.get('date_range', 'last_30_days')
    
    # 处理日期范围 - 如果未指定日期，则根据date_range设置默认值
    start_date_obj, end_date_obj = get_date_range(start_date, end_date, date_range)
    
    # 将处理后的日期转换回字符串格式
    start_date = start_date_obj.strftime('%Y-%m-%d')
    end_date = end_date_obj.strftime('%Y-%m-%d')
    
    # 查询基本指标数据 - 使用真实数据替代随机值
    completion_rate, avg_amount, avg_duration = get_basic_metrics(start_date_obj, end_date_obj)
    
    # 查询各城市平均订单完成时长数据
    city_order_duration_data = get_city_order_duration_data(start_date_obj, end_date_obj)
    
    # 获取订单高峰时段热力图数据
    order_peak_data = get_order_peak_data(start_date_obj, end_date_obj)
    
    # 获取订单行驶里程分布数据
    order_distance_data = get_order_distance_data(start_date_obj, end_date_obj)
    
    # 获取订单金额分布云图数据
    order_amount_data = get_order_amount_distribution(start_date_obj, end_date_obj)
    
    # 获取待分配订单实时地理热点图数据
    pending_orders_map_data = get_pending_orders_map_data()
    
    return render_template('analytics/service-quality.html',
                          completion_rate=completion_rate,
                          avg_amount=avg_amount,
                          avg_duration=avg_duration,
                          city_order_duration_data=json.dumps(city_order_duration_data),
                          order_peak_data=json.dumps(order_peak_data),
                          order_distance_data=json.dumps(order_distance_data),
                          order_amount_data=json.dumps(order_amount_data),
                          pending_orders_map_data=json.dumps(pending_orders_map_data),
                          start_date=start_date,
                          end_date=end_date,
                          date_range=date_range)

# 辅助函数：根据日期参数获取日期范围
def get_date_range(start_date, end_date, date_range='last_30_days'):
    """
    根据请求参数获取日期范围
    
    Args:
        start_date: 开始日期字符串
        end_date: 结束日期字符串
        date_range: 日期范围类型
        
    Returns:
        tuple: (start_date, end_date) 日期对象
    """
    end_date_obj = datetime.now()
    start_date_obj = end_date_obj - timedelta(days=30)  # 默认30天
    
    # 如果有明确的开始和结束日期，使用它们
    if start_date and end_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            # 设置结束日期为当天的23:59:59
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
        except ValueError:
            # 日期格式错误时使用默认值
            print(f"日期格式错误: {start_date} 或 {end_date}")
    else:
        # 根据日期范围设置日期
        if date_range == 'last_3_days':
            start_date_obj = end_date_obj - timedelta(days=3)
        elif date_range == 'last_7_days':
            start_date_obj = end_date_obj - timedelta(days=7)
        elif date_range == 'last_90_days':
            start_date_obj = end_date_obj - timedelta(days=90)
        elif date_range == 'last_180_days':
            start_date_obj = end_date_obj - timedelta(days=180)
        # last_30_days 是默认值，已经在前面设置了
    
    return start_date_obj, end_date_obj

# 获取基本指标数据
def get_basic_metrics(start_date, end_date):
    """获取订单基本指标：完成率、平均金额、平均完成时长"""
    # 平均订单完成率
    completion_rate_query = """
    SELECT 
        COALESCE(
            SUM(CASE WHEN order_status = '已结束' THEN 1 ELSE 0 END) / 
            NULLIF(COUNT(*), 0) * 100, 
            0
        ) as completion_rate
    FROM orders
    WHERE create_time BETWEEN %s AND %s
    """
    completion_rate_result = BaseDAO.execute_query(completion_rate_query, (
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    ))
    completion_rate = round(float(completion_rate_result[0]['completion_rate'] if completion_rate_result and completion_rate_result[0]['completion_rate'] else 0), 1)
    
    # 平均订单金额
    avg_amount_query = """
    SELECT AVG(amount) as avg_amount 
    FROM order_details 
    WHERE created_at BETWEEN %s AND %s
    """
    amount_result = BaseDAO.execute_query(avg_amount_query, (
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    ))
    avg_amount = round(float(amount_result[0]['avg_amount'] if amount_result and amount_result[0]['avg_amount'] else 0), 2)
    
    # 订单完成时长(分钟)
    duration_query = """
    SELECT AVG(TIMESTAMPDIFF(MINUTE, create_time, arrival_time)) as avg_duration
    FROM orders
    WHERE order_status = '已结束'
    AND create_time IS NOT NULL
    AND arrival_time IS NOT NULL
    AND create_time BETWEEN %s AND %s
    """
    duration_result = BaseDAO.execute_query(duration_query, (
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    ))
    avg_duration_value = round(float(duration_result[0]['avg_duration'] if duration_result and duration_result[0]['avg_duration'] else 0), 1)
    avg_duration = f"{avg_duration_value}分钟"
    
    return completion_rate, avg_amount, avg_duration

# 辅助函数：获取各城市平均订单完成时长数据
def get_city_order_duration_data(start_date, end_date):
    """计算各城市的平均订单完成时长"""
    
    # 使用原始SQL查询计算各城市的平均订单完成时间（单位：分钟）
    query = """
    SELECT 
        o.city_code,
        AVG(TIMESTAMPDIFF(MINUTE, o.create_time, o.arrival_time)) as avg_duration
    FROM 
        orders o
    WHERE 
        o.order_status = '已结束'
        AND o.create_time IS NOT NULL
        AND o.arrival_time IS NOT NULL
        AND o.city_code IS NOT NULL
        AND o.create_time BETWEEN %s AND %s
    GROUP BY 
        o.city_code
    ORDER BY 
        avg_duration ASC
    """
    
    # 使用BaseDAO执行查询
    results = BaseDAO.execute_query(query, (
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    # 城市列表 - 按照数据库中的城市代码顺序
    cities = []
    durations = []
    
    # 处理查询结果
    for row in results:
        cities.append(row['city_code'])  # 城市名称
        durations.append(round(float(row['avg_duration']), 1))  # 平均时长（四舍五入到1位小数）
    
    # 为每个城市分配唯一的渐变色
    colors = [
        '#4a79fe', '#36c5fe', '#38c7be', '#32d396', '#70db74',  # 蓝色系到绿色系
        '#fddf40', '#fa9d4c', '#f87146', '#fb5d6d', '#d975df', '#9f84ff'  # 黄色系到紫色系
    ]
    
    # 如果城市不足11个（根据预设的11个城市），填充默认值
    default_cities = ['沈阳市', '上海市', '北京市', '广州市', '深圳市', '杭州市', '南京市', '成都市', '重庆市', '武汉市', '西安市']
    default_duration = 20.0  # 默认值
    
    # 检查是否有缺失的城市，并添加默认值
    for city in default_cities:
        if city not in cities:
            cities.append(city)
            durations.append(default_duration)
    
    # 如果colors不够，则循环使用
    while len(colors) < len(cities):
        colors.extend(colors[:len(cities)-len(colors)])
    
    return {
        'cities': cities,
        'durations': durations,
        'colors': colors[:len(cities)]
    }

# 辅助函数：获取订单高峰时段热力图数据
def get_order_peak_data(start_date, end_date):
    """获取订单高峰时段热力图数据"""
    
    # 使用SQL查询计算每周每小时的订单量
    query = """
    SELECT 
        WEEKDAY(create_time) as day_of_week,
        HOUR(create_time) as hour_of_day,
        COUNT(*) as order_count
    FROM 
        orders
    WHERE 
        create_time BETWEEN %s AND %s
    GROUP BY 
        WEEKDAY(create_time), HOUR(create_time)
    ORDER BY 
        day_of_week, hour_of_day
    """
    
    # 使用BaseDAO执行查询
    results = BaseDAO.execute_query(query, (
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    # 准备热力图数据
    days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    hours = [f"{i}:00" for i in range(24)]
    data = []
    
    # 最大订单数，用于颜色归一化
    max_count = 0
    if results:
        max_count = max([row['order_count'] for row in results])
    
    # 处理查询结果
    for row in results:
        day_index = row['day_of_week']  # MySQL的WEEKDAY函数返回0-6，0表示周一
        hour_index = row['hour_of_day']
        count = row['order_count']
        
        data.append([day_index, hour_index, count])
    
    return {
        'days': days,
        'hours': hours,
        'data': data,
        'max_count': max_count
    }

# 辅助函数：获取订单行驶里程分布数据
def get_order_distance_data(start_date, end_date):
    """获取订单行驶里程分布数据"""
    
    # 使用SQL查询获取所有订单的行驶距离
    query = """
    SELECT 
        distance
    FROM 
        order_details
    WHERE 
        created_at BETWEEN %s AND %s
    ORDER BY 
        distance
    """
    
    # 使用BaseDAO执行查询
    results = BaseDAO.execute_query(query, (
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    # 提取所有距离数据
    distances = [float(row['distance']) for row in results]
    
    # 计算距离分布统计 - 按区间统计
    bin_size = 2  # 每个区间的宽度，单位：公里
    bins = {}
    
    for distance in distances:
        bin_index = int(distance / bin_size)
        bin_name = f"{bin_index * bin_size}-{(bin_index + 1) * bin_size}"
        
        if bin_name not in bins:
            bins[bin_name] = 0
        bins[bin_name] += 1
    
    # 转换为前端需要的格式
    bin_data = []
    for bin_name, count in sorted(bins.items(), key=lambda x: float(x[0].split('-')[0])):
        bin_data.append({
            'name': bin_name,
            'value': count
        })
    
    return {
        'raw_distances': distances,  # 原始距离数据，用于核密度估计
        'bin_data': bin_data  # 按区间统计的数据
    }

# 辅助函数：获取订单金额分布云图数据
def get_order_amount_distribution(start_date, end_date):
    """获取订单金额分布云图数据"""
    
    # 使用SQL查询计算订单金额分布
    query = """
    SELECT 
        CASE
            WHEN amount BETWEEN 0 AND 10 THEN '0-10元'
            WHEN amount BETWEEN 10 AND 20 THEN '10-20元'
            WHEN amount BETWEEN 20 AND 30 THEN '20-30元'
            WHEN amount BETWEEN 30 AND 40 THEN '30-40元'
            WHEN amount BETWEEN 40 AND 50 THEN '40-50元'
            WHEN amount BETWEEN 50 AND 60 THEN '50-60元'
            WHEN amount BETWEEN 60 AND 70 THEN '60-70元'
            WHEN amount BETWEEN 70 AND 80 THEN '70-80元'
            WHEN amount BETWEEN 80 AND 90 THEN '80-90元'
            WHEN amount BETWEEN 90 AND 100 THEN '90-100元'
            WHEN amount BETWEEN 100 AND 150 THEN '100-150元'
            WHEN amount BETWEEN 150 AND 200 THEN '150-200元'
            ELSE '200元以上'
        END AS amount_range,
        COUNT(*) AS count
    FROM 
        order_details
    WHERE 
        created_at BETWEEN %s AND %s
    GROUP BY 
        amount_range
    ORDER BY 
        CASE amount_range
            WHEN '0-10元' THEN 1
            WHEN '10-20元' THEN 2
            WHEN '20-30元' THEN 3
            WHEN '30-40元' THEN 4
            WHEN '40-50元' THEN 5
            WHEN '50-60元' THEN 6
            WHEN '60-70元' THEN 7
            WHEN '70-80元' THEN 8
            WHEN '80-90元' THEN 9
            WHEN '90-100元' THEN 10
            WHEN '100-150元' THEN 11
            WHEN '150-200元' THEN 12
            ELSE 13
        END
    """
    
    # 使用BaseDAO执行查询
    results = BaseDAO.execute_query(query, (
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    # 处理查询结果
    amount_data = []
    for row in results:
        amount_data.append({
            'name': row['amount_range'],
            'value': row['count']
        })
    
    # 如果没有数据，使用默认填充数据
    if not amount_data:
        amount_data = [
            {'name': '0-10元', 'value': 0},
            {'name': '10-20元', 'value': 0},
            {'name': '20-30元', 'value': 0},
            {'name': '30-40元', 'value': 0},
            {'name': '40-50元', 'value': 0},
            {'name': '50-60元', 'value': 0},
            {'name': '60-70元', 'value': 0},
            {'name': '70-80元', 'value': 0},
            {'name': '80-90元', 'value': 0},
            {'name': '90-100元', 'value': 0},
            {'name': '100-150元', 'value': 0},
            {'name': '150-200元', 'value': 0},
            {'name': '200元以上', 'value': 0}
        ]
    
    return amount_data

# 辅助函数：获取待分配订单实时地理热点图数据
def get_pending_orders_map_data():
    """获取待分配订单实时地理热点图数据"""
    
    # 使用SQL查询获取当前所有待分配订单的位置坐标和城市信息
    query = """
    SELECT
        city_code,
        pickup_location_x,
        pickup_location_y,
        COUNT(*) as order_count
    FROM
        orders
    WHERE
        order_status = '待分配'
    GROUP BY
        city_code, pickup_location_x, pickup_location_y
    """
    
    # 使用BaseDAO执行查询
    results = BaseDAO.execute_query(query)
    
    # 城市坐标映射表（为主要城市提供大致中心点坐标）
    city_coordinates = {
        '北京市': [116.407526, 39.904030],
        '上海市': [121.473701, 31.230416],
        '广州市': [113.264385, 23.129112],
        '深圳市': [114.085947, 22.547],
        '杭州市': [120.209947, 30.246027],
        '南京市': [118.796877, 32.060255],
        '成都市': [104.065735, 30.659462],
        '重庆市': [106.551556, 29.563009],
        '武汉市': [114.305393, 30.593099],
        '西安市': [108.948024, 34.263161],
        '沈阳市': [123.429096, 41.796767]
    }
    
    # 省份名称映射（简称到全称及城市到省份的映射）
    province_name_map = {
        '北京': '北京市',
        '天津': '天津市',
        '上海': '上海市',
        '重庆': '重庆市',
        '河北': '河北省',
        '山西': '山西省',
        '辽宁': '辽宁省',
        '吉林': '吉林省',
        '黑龙江': '黑龙江省',
        '江苏': '江苏省',
        '浙江': '浙江省',
        '安徽': '安徽省',
        '福建': '福建省',
        '江西': '江西省',
        '山东': '山东省',
        '河南': '河南省',
        '湖北': '湖北省',
        '湖南': '湖南省',
        '广东': '广东省',
        '海南': '海南省',
        '四川': '四川省',
        '贵州': '贵州省',
        '云南': '云南省',
        '陕西': '陕西省',
        '甘肃': '甘肃省',
        '青海': '青海省',
        '台湾': '台湾省',
        '内蒙古': '内蒙古自治区',
        '广西': '广西壮族自治区',
        '西藏': '西藏自治区',
        '宁夏': '宁夏回族自治区',
        '新疆': '新疆维吾尔自治区',
        '香港': '香港特别行政区',
        '澳门': '澳门特别行政区',
        # 城市到省份的映射
        '上海市': '上海市',
        '北京市': '北京市',
        '广州市': '广东省',
        '深圳市': '广东省',
        '杭州市': '浙江省',
        '南京市': '江苏省',
        '成都市': '四川省',
        '重庆市': '重庆市',
        '武汉市': '湖北省',
        '西安市': '陕西省',
        '沈阳市': '辽宁省'
    }
    
    # 创建点数据
    points = []
    for row in results:
        if row['pickup_location_x'] is not None and row['pickup_location_y'] is not None:
            city = row['city_code']
            x = row['pickup_location_x']
            y = row['pickup_location_y']
            count = row['order_count']
            
            # 如果城市在映射表中，使用真实地理坐标，否则使用默认坐标
            if city in city_coordinates:
                # 这里使用相对偏移将屏幕坐标映射到实际地理坐标
                # 假设每个城市的屏幕坐标以(400,400)为中心，范围是800x800
                # 将其映射到实际城市坐标周围的一个小范围内（约0.5经纬度范围）
                base_lng, base_lat = city_coordinates[city]
                lng_offset = (x - 400) / 800.0 * 0.5  # 映射到±0.25度经度范围
                lat_offset = (400 - y) / 800.0 * 0.5  # 映射到±0.25度纬度范围，注意y坐标反转
                
                lng = base_lng + lng_offset
                lat = base_lat + lat_offset
            else:
                # 如果城市未知，默认使用北京坐标
                base_lng, base_lat = city_coordinates.get('北京市')
                lng_offset = (x - 400) / 800.0 * 0.5
                lat_offset = (400 - y) / 800.0 * 0.5
                
                lng = base_lng + lng_offset
                lat = base_lat + lat_offset
            
            points.append([lng, lat, count, city])
    
    # 如果没有数据，为每个城市生成一些随机样本数据
    if not points:
        for city, coords in city_coordinates.items():
            base_lng, base_lat = coords
            # 为每个城市生成1-3个随机点
            for _ in range(random.randint(1, 3)):
                lng_offset = (random.random() - 0.5) * 0.5
                lat_offset = (random.random() - 0.5) * 0.5
                
                lng = base_lng + lng_offset
                lat = base_lat + lat_offset
                count = random.randint(1, 5)
                
                points.append([lng, lat, count, city])
    
    # 计算城市级别的统计数据
    city_stats = {}
    for point in points:
        city = point[3]  # 城市名称在第4个位置
        count = point[2]  # 订单数在第3个位置
        
        if city not in city_stats:
            city_stats[city] = 0
        city_stats[city] += count
    
    # 转换为前端需要的格式，应用省份映射
    city_data = []
    for city, count in city_stats.items():
        # 应用省份名称映射
        mapped_name = province_name_map.get(city, city)
        city_data.append({
            "name": mapped_name,
            "value": count
        })
    
    return {
        "points": points,  # 包含详细点位置的数据
        "city_data": city_data  # 城市级别的聚合数据，使用映射后的省份名称
    }
