from flask import Blueprint, jsonify, request
from app.dao.base_dao import BaseDAO
from datetime import datetime, timedelta
import json
import traceback
import pandas as pd
import numpy as np

def get_charging_stations_utilization():
    """获取按城市统计的充电站利用率数据
    
    Returns:
        dict: 按城市统计的充电站利用率数据
    """
    try:
        # 11个指定城市
        cities = ["沈阳市", "上海市", "北京市", "广州市", "深圳市", "杭州市", "南京市", "成都市", "重庆市", "武汉市", "西安市"]
        
        # 按城市统计充电站当前使用情况
        query = """
        SELECT 
            city_code,
            SUM(current_vehicles) as total_current_vehicles,
            SUM(max_capacity) as total_max_capacity,
            ROUND(SUM(current_vehicles) / SUM(max_capacity) * 100, 1) as utilization_rate
        FROM 
            charging_stations
        WHERE 
            max_capacity > 0
        GROUP BY
            city_code
        """
        
        result = BaseDAO.execute_query(query)
        
        # 创建城市字典，保存每个城市的数据
        city_data = {}
        for city in cities:
            city_data[city] = {
                'city_code': city,
                'total_current_vehicles': 0,
                'total_max_capacity': 0,
                'utilization_rate': 0
            }
            
        # 填充查询结果数据
        for item in result:
            city = item['city_code']
            if city in city_data:
                city_data[city] = {
                    'city_code': city,
                    'total_current_vehicles': int(item['total_current_vehicles']),
                    'total_max_capacity': int(item['total_max_capacity']),
                    'utilization_rate': float(item['utilization_rate'])
                }
        
        # 转换为列表形式返回
        return [city_data[city] for city in cities]
    except Exception as e:
        print(f"获取充电站利用率数据失败: {str(e)}")
        traceback.print_exc()
        return []

def get_battery_level_distribution():
    """获取车辆电池电量分布数据，包括0%和100%
    
    Returns:
        dict: 电池电量分布数据
    """
    try:
        query = """
        SELECT 
            CASE 
                WHEN battery_level = 0 THEN 0
                WHEN battery_level = 100 THEN 100
                ELSE FLOOR(battery_level/10)*10 
            END as level_range,
            COUNT(*) as vehicle_count
        FROM 
            vehicles
        GROUP BY 
            CASE 
                WHEN battery_level = 0 THEN 0
                WHEN battery_level = 100 THEN 100
                ELSE FLOOR(battery_level/10)*10 
            END
        ORDER BY 
            level_range
        """
        
        result = BaseDAO.execute_query(query)
        
        # 处理数据为直方图格式
        ranges = []
        counts = []
        
        # 确保所有区间都有数据，包括0%和100%
        range_dict = {i: 0 for i in range(0, 101, 10)}
        
        for item in result:
            level = int(item['level_range'])
            range_dict[level] = int(item['vehicle_count'])
        
        # 转换为所需格式
        for level, count in sorted(range_dict.items()):
            if level == 0:
                ranges.append("0%")
            elif level == 100:
                ranges.append("100%")
            else:
                ranges.append(f"{level}-{level+10}%")
            counts.append(count)
        
        return {
            'ranges': ranges,
            'counts': counts
        }
    except Exception as e:
        print(f"获取电池电量分布数据失败: {str(e)}")
        traceback.print_exc()
        return {'ranges': [], 'counts': []}

def get_charging_peak_hours(start_date=None, end_date=None):
    """获取充电高峰时段热力图数据
    
    Args:
        start_date (datetime, optional): 开始日期，默认为None时取最近30天
        end_date (datetime, optional): 结束日期，默认为None时取当前日期
    
    Returns:
        dict: 高峰时段热力图数据
    """
    try:
        # 设置默认日期范围
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
            
        # 转换为字符串格式
        start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
        end_date_str = end_date.strftime('%Y-%m-%d 23:59:59')  # 确保包含结束日期的全天
        
        # 从expense表获取充电记录，使用创建时间字段而不是date字段，根据日期范围过滤
        query = """
        SELECT 
            DAYOFWEEK(created_at) as day_of_week,
            HOUR(created_at) as hour_of_day,
            COUNT(*) as charging_count
        FROM 
            expense
        WHERE 
            type = '充电站支出'
            AND amount < 10000  /* 只统计单次充电记录，不包括其他大额充电站支出 */
            AND created_at BETWEEN %s AND %s
        GROUP BY 
            DAYOFWEEK(created_at), HOUR(created_at)
        ORDER BY 
            day_of_week, hour_of_day
        """
        
        result = BaseDAO.execute_query(query, (start_date_str, end_date_str))
        
        # 创建7x24的数据矩阵
        heatmap_data = np.zeros((7, 24))
        
        # 填充数据
        for item in result:
            day = int(item['day_of_week']) - 1  # MySQL的DAYOFWEEK从1开始，转为0-6
            hour = int(item['hour_of_day'])
            count = int(item['charging_count'])
            heatmap_data[day, hour] = count
        
        # 准备返回数据
        days = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
        hours = [f"{h}时" for h in range(24)]
        
        # 转换为[x, y, value]格式的数据
        formatted_data = []
        for i in range(7):
            for j in range(24):
                formatted_data.append([j, i, int(heatmap_data[i, j])])
        
        # 计算日期范围内总充电次数
        total_charging = sum(sum(row) for row in heatmap_data)
        
        return {
            'days': days,
            'hours': hours,
            'data': formatted_data,
            'total_charging': int(total_charging)
        }
    except Exception as e:
        print(f"获取充电高峰时段数据失败: {str(e)}")
        traceback.print_exc()
        return {'days': [], 'hours': [], 'data': [], 'total_charging': 0}

def get_battery_level_map():
    """获取车辆平均电量地理位置热点图数据
    
    Returns:
        list: 按省份分组的车辆平均电量数据
    """
    try:
        # 省份名称映射（城市到省份）
        province_map = {
            '沈阳市': '辽宁省',
            '上海市': '上海市',
            '北京市': '北京市',
            '广州市': '广东省',
            '深圳市': '广东省',
            '杭州市': '浙江省',
            '南京市': '江苏省',
            '成都市': '四川省',
            '重庆市': '重庆市',
            '武汉市': '湖北省',
            '西安市': '陕西省'
        }
        
        # 查询每个城市的车辆平均电量
        query = """
        SELECT 
            current_city,
            AVG(battery_level) as avg_battery,
            COUNT(*) as vehicle_count
        FROM 
            vehicles
        WHERE 
            current_city IS NOT NULL
        GROUP BY 
            current_city
        """
        
        result = BaseDAO.execute_query(query)
        
        # 按省份分组处理数据
        province_data = {}
        for item in result:
            city = item['current_city']
            province = province_map.get(city, city)  # 如果没有映射则使用城市名
            
            battery_level = float(item['avg_battery'])
            count = int(item['vehicle_count'])
            
            # 如果省份已存在，更新数据（加权平均）
            if province in province_data:
                old_count = province_data[province]['count']
                old_battery = province_data[province]['value']
                
                # 计算加权平均电量
                new_count = old_count + count
                new_battery = (old_battery * old_count + battery_level * count) / new_count
                
                province_data[province] = {
                    'name': province,
                    'value': round(new_battery, 1),
                    'count': new_count
                }
            else:
                province_data[province] = {
                    'name': province,
                    'value': round(battery_level, 1),
                    'count': count
                }
        
        # 转换为列表
        map_data = list(province_data.values())
        
        return map_data
    except Exception as e:
        print(f"获取车辆平均电量地理位置数据失败: {str(e)}")
        traceback.print_exc()
        return []

def get_city_charging_demand_capacity():
    """获取各城市充电需求与容量对比数据
    
    Returns:
        dict: 城市充电需求与容量对比数据
    """
    try:
        # 预定义所有支持的城市列表
        all_cities = ["沈阳市", "上海市", "北京市", "广州市", "深圳市", "杭州市", "南京市", "成都市", "重庆市", "武汉市", "西安市"]
        
        # 获取各城市需要充电的车辆数（状态为充电中、等待充电、前往充电或电量不足）
        demand_query = """
        SELECT 
            operating_city,
            COUNT(*) as demand_count
        FROM 
            vehicles
        WHERE 
            current_status IN ('充电中', '等待充电', '前往充电', '电量不足') 
            AND operating_city IS NOT NULL
        GROUP BY 
            operating_city
        """
        
        # 获取各城市充电站容量
        capacity_query = """
        SELECT 
            city_code,
            SUM(max_capacity) as total_capacity
        FROM 
            charging_stations
        GROUP BY 
            city_code
        """
        
        # 执行查询
        demand_result = BaseDAO.execute_query(demand_query)
        capacity_result = BaseDAO.execute_query(capacity_query)
        
        # 创建城市需求字典和容量字典
        demand_dict = {item['operating_city']: int(item['demand_count']) for item in demand_result}
        capacity_dict = {item['city_code']: int(item['total_capacity']) for item in capacity_result}
        
        # 合并数据，确保所有城市都包含
        cities = []
        demand_data = []
        capacity_data = []
        
        # 遍历所有支持的城市，确保每个城市都有数据
        for city in all_cities:
            demand = demand_dict.get(city, 0)
            capacity = capacity_dict.get(city, 0)
            
            # 只添加有数据的城市或强制添加所有城市
            if demand > 0 or capacity > 0 or True:  # 设为True表示添加所有城市
                cities.append(city)
                demand_data.append(demand)
                capacity_data.append(capacity)
        
        # 获取低电量(<20%)但未在充电状态的车辆占比
        low_battery_query = """
        SELECT 
            operating_city,
            COUNT(*) as low_count 
        FROM 
            vehicles 
        WHERE 
            battery_level < 20 
            AND current_status NOT IN ('充电中', '等待充电', '前往充电')
            AND operating_city IS NOT NULL
        GROUP BY 
            operating_city
        """
        
        low_battery_result = BaseDAO.execute_query(low_battery_query)
        low_battery_dict = {item['operating_city']: int(item['low_count']) for item in low_battery_result}
        
        # 构建低电量车辆数据
        low_battery_data = [low_battery_dict.get(city, 0) for city in cities]
        
        # 计算需求/容量比例
        ratio_data = []
        for i in range(len(cities)):
            if capacity_data[i] > 0:
                ratio = round(demand_data[i] / capacity_data[i] * 100, 1)
            else:
                ratio = 0 if demand_data[i] == 0 else 999.9
            ratio_data.append(ratio)
        
        return {
            'cities': cities,
            'demand': demand_data,
            'capacity': capacity_data,
            'low_battery': low_battery_data,
            'ratio': ratio_data
        }
    except Exception as e:
        print(f"获取城市充电需求与容量数据失败: {str(e)}")
        traceback.print_exc()
        return {'cities': [], 'demand': [], 'capacity': [], 'low_battery': [], 'ratio': []}

def get_battery_data_for_chart(chart_id):
    """根据图表ID获取对应的电池数据
    
    Args:
        chart_id (str): 图表的DOM ID
    
    Returns:
        dict: 对应图表所需的数据
    """
    try:
        if chart_id == 'charging-stations-gauge':
            return get_charging_stations_utilization()
        elif chart_id == 'battery-level-histogram':
            return get_battery_level_distribution()
        elif chart_id == 'charging-peak-heatmap':
            return get_charging_peak_hours()
        elif chart_id == 'battery-level-map':
            return get_battery_level_map()
        elif chart_id == 'city-charging-capacity':
            return get_city_charging_demand_capacity()
        else:
            return {"error": "未知的图表ID"}
    except Exception as e:
        print(f"获取图表 {chart_id} 数据失败: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)} 