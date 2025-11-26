from app.dao.base_dao import BaseDAO
from datetime import datetime, timedelta
import json
import traceback

def get_maintenance_status_data():
    """获取当前维护状态车辆占比数据
    
    Returns:
        dict: 维护状态分析数据
    """
    try:
        # 获取所有可用车辆数量
        total_vehicles_query = """
        SELECT COUNT(*) as total
        FROM vehicles
        WHERE is_available = 1
        """
        total_result = BaseDAO.execute_query(total_vehicles_query)
        total_vehicles = int(total_result[0]['total'] if total_result else 0)
        
        # 获取维护中车辆数量
        maintenance_query = """
        SELECT COUNT(*) as count
        FROM vehicles
        WHERE current_status = '维护中' 
        AND is_available = 1
        """
        maintenance_result = BaseDAO.execute_query(maintenance_query)
        maintenance_count = int(maintenance_result[0]['count'] if maintenance_result else 0)
        
        # 获取正常运营车辆数量（非维护状态的可用车辆）
        operating_count = total_vehicles - maintenance_count
        
        # 计算维护中车辆占比
        maintenance_percentage = round(maintenance_count / total_vehicles * 100, 1) if total_vehicles > 0 else 0
        
        # 构建返回数据
        return {
            'maintenance_count': maintenance_count,
            'operating_count': operating_count,
            'total_vehicles': total_vehicles,
            'maintenance_percentage': maintenance_percentage,
            'chart_data': {
                'labels': ['维护中', '运营中'],
                'data': [maintenance_count, operating_count],
                'colors': ['rgba(255, 99, 132, 0.8)', 'rgba(54, 162, 235, 0.8)']
            }
        }
    except Exception as e:
        print(f"获取维护状态数据失败: {str(e)}")
        return {
            'maintenance_count': 0,
            'operating_count': 0,
            'total_vehicles': 0,
            'maintenance_percentage': 0,
            'chart_data': {
                'labels': ['维护中', '运营中'],
                'data': [0, 0],
                'colors': ['rgba(255, 99, 132, 0.8)', 'rgba(54, 162, 235, 0.8)']
            }
        }

def get_upcoming_maintenance_data():
    """获取即将到期维护车辆时间分布数据
    
    根据上次维护时间和维护间隔参数计算下次应该维护的时间
    
    Returns:
        dict: 即将到期维护车辆时间分布数据
    """
    try:
        # 导入系统参数配置
        from app.config.vehicle_params import MAINTENANCE_INTERVAL
        
        # 获取当前日期
        current_date = datetime.now().date()
        
        # 使用上次维护时间加上维护间隔计算预计的下次维护时间
        # 获取已逾期维护的车辆数量（上次维护日期加上维护间隔小于当前日期）
        overdue_query = """
        SELECT COUNT(*) as count
        FROM vehicles
        WHERE is_available = 1
        AND last_maintenance_date IS NOT NULL
        AND DATE_ADD(last_maintenance_date, INTERVAL %s DAY) < CURDATE()
        """
        overdue_result = BaseDAO.execute_query(overdue_query, (MAINTENANCE_INTERVAL,))
        overdue_count = int(overdue_result[0]['count'] if overdue_result else 0)
        
        # 获取7天内到期维护车辆数量
        within_7_days_query = """
        SELECT COUNT(*) as count
        FROM vehicles
        WHERE is_available = 1
        AND last_maintenance_date IS NOT NULL
        AND DATE_ADD(last_maintenance_date, INTERVAL %s DAY) BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
        """
        within_7_days_result = BaseDAO.execute_query(within_7_days_query, (MAINTENANCE_INTERVAL,))
        within_7_days_count = int(within_7_days_result[0]['count'] if within_7_days_result else 0)
        
        # 获取8-30天内到期维护车辆数量
        within_30_days_query = """
        SELECT COUNT(*) as count
        FROM vehicles
        WHERE is_available = 1
        AND last_maintenance_date IS NOT NULL
        AND DATE_ADD(last_maintenance_date, INTERVAL %s DAY) BETWEEN DATE_ADD(CURDATE(), INTERVAL 8 DAY) 
        AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        """
        within_30_days_result = BaseDAO.execute_query(within_30_days_query, (MAINTENANCE_INTERVAL,))
        within_30_days_count = int(within_30_days_result[0]['count'] if within_30_days_result else 0)
        
        # 获取31-90天内到期维护车辆数量
        within_90_days_query = """
        SELECT COUNT(*) as count
        FROM vehicles
        WHERE is_available = 1
        AND last_maintenance_date IS NOT NULL
        AND DATE_ADD(last_maintenance_date, INTERVAL %s DAY) BETWEEN DATE_ADD(CURDATE(), INTERVAL 31 DAY) 
        AND DATE_ADD(CURDATE(), INTERVAL 90 DAY)
        """
        within_90_days_result = BaseDAO.execute_query(within_90_days_query, (MAINTENANCE_INTERVAL,))
        within_90_days_count = int(within_90_days_result[0]['count'] if within_90_days_result else 0)
        
        # 获取91-180天内到期维护车辆数量
        within_180_days_query = """
        SELECT COUNT(*) as count
        FROM vehicles
        WHERE is_available = 1
        AND last_maintenance_date IS NOT NULL
        AND DATE_ADD(last_maintenance_date, INTERVAL %s DAY) BETWEEN DATE_ADD(CURDATE(), INTERVAL 91 DAY) 
        AND DATE_ADD(CURDATE(), INTERVAL 180 DAY)
        """
        within_180_days_result = BaseDAO.execute_query(within_180_days_query, (MAINTENANCE_INTERVAL,))
        within_180_days_count = int(within_180_days_result[0]['count'] if within_180_days_result else 0)
        
        # 获取180天以上到期维护车辆数量
        over_180_days_query = """
        SELECT COUNT(*) as count
        FROM vehicles
        WHERE is_available = 1
        AND last_maintenance_date IS NOT NULL
        AND DATE_ADD(last_maintenance_date, INTERVAL %s DAY) > DATE_ADD(CURDATE(), INTERVAL 180 DAY)
        """
        over_180_days_result = BaseDAO.execute_query(over_180_days_query, (MAINTENANCE_INTERVAL,))
        over_180_days_count = int(over_180_days_result[0]['count'] if over_180_days_result else 0)
        
        # 构建返回数据
        return {
            'labels': ['已逾期', '7天内', '30天内', '90天内', '180天内', '180天以上'],
            'data': [overdue_count, within_7_days_count, within_30_days_count, within_90_days_count, within_180_days_count, over_180_days_count],
            'colors': [
                'rgba(220, 53, 69, 0.9)',   # 红色 - 已逾期
                'rgba(255, 99, 132, 0.9)',  # 粉红 - 7天内
                'rgba(255, 159, 64, 0.9)',  # 橙色 - 30天内
                'rgba(255, 205, 86, 0.9)',  # 黄色 - 90天内
                'rgba(75, 192, 192, 0.9)',  # 蓝绿色 - 180天内
                'rgba(54, 162, 235, 0.9)'   # 蓝色 - 180天以上
            ],
            'borderColors': [
                'rgb(220, 53, 69)',  # 已逾期
                'rgb(255, 99, 132)',
                'rgb(255, 159, 64)',
                'rgb(255, 205, 86)',
                'rgb(75, 192, 192)',
                'rgb(54, 162, 235)'
            ]
        }
    except Exception as e:
        print(f"获取即将到期维护车辆时间分布数据失败: {str(e)}")
        traceback.print_exc()
        return {
            'labels': ['已逾期', '7天内', '30天内', '90天内', '180天内', '180天以上'],
            'data': [0, 0, 0, 0, 0, 0],
            'colors': [
                'rgba(220, 53, 69, 0.9)',
                'rgba(255, 99, 132, 0.9)',
                'rgba(255, 159, 64, 0.9)',
                'rgba(255, 205, 86, 0.9)',
                'rgba(75, 192, 192, 0.9)',
                'rgba(54, 162, 235, 0.9)'
            ],
            'borderColors': [
                'rgb(220, 53, 69)',
                'rgb(255, 99, 132)',
                'rgb(255, 159, 64)',
                'rgb(255, 205, 86)',
                'rgb(75, 192, 192)',
                'rgb(54, 162, 235)'
            ]
        }

def get_maintenance_frequency_by_model():
    """获取各车型维护频率数据
    
    Returns:
        dict: 各车型维护频率数据
    """
    try:
        # 获取各车型的车辆数量和维护记录数量
        query = """
        SELECT 
            v.model,
            COUNT(DISTINCT v.vehicle_id) as vehicle_count,
            COUNT(DISTINCT vl.log_id) as maintenance_count
        FROM 
            vehicles v
            LEFT JOIN vehicle_logs vl ON v.vehicle_id = vl.vehicle_id AND vl.log_type = '维护记录'
        WHERE 
            v.is_available = 1
        GROUP BY 
            v.model
        """
        results = BaseDAO.execute_query(query)
        
        models = []
        frequencies = []
        
        for item in results:
            model = item['model']
            vehicle_count = int(item['vehicle_count'])
            maintenance_count = int(item['maintenance_count'])
            
            # 计算每辆车平均维护次数
            frequency = round(maintenance_count / vehicle_count, 2) if vehicle_count > 0 else 0
            
            models.append(model)
            frequencies.append(frequency)
        
        return {
            'models': models,
            'frequencies': frequencies
        }
    except Exception as e:
        print(f"获取车型维护频率数据失败: {str(e)}")
        return {
            'models': [],
            'frequencies': []
        }

def get_maintenance_cost_breakdown():
    """获取维护成本分类数据
    
    Returns:
        dict: 维护成本分类数据
    """
    try:
        # 获取最近3个月的维护支出数据，按描述分类
        query = """
        SELECT 
            SUBSTRING_INDEX(description, ' - ', 1) as category,
            SUM(amount) as total_amount
        FROM 
            expense
        WHERE 
            type = '车辆支出'
            AND date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
        GROUP BY 
            SUBSTRING_INDEX(description, ' - ', 1)
        ORDER BY 
            total_amount DESC
        LIMIT 5
        """
        results = BaseDAO.execute_query(query)
        
        categories = []
        amounts = []
        
        for item in results:
            category = item['category'] if item['category'] else '其他'
            amount = float(item['total_amount'])
            
            categories.append(category)
            amounts.append(amount)
        
        # 如果结果少于5类，添加"其他"分类
        if len(categories) < 5:
            categories.append('其他')
            amounts.append(0)
        
        return {
            'categories': categories,
            'amounts': amounts
        }
    except Exception as e:
        print(f"获取维护成本分类数据失败: {str(e)}")
        return {
            'categories': [],
            'amounts': []
        }

def get_maintenance_trend_data():
    """获取车辆维护趋势数据
    
    Returns:
        dict: 维护趋势数据
    """
    try:
        # 获取最近6个月的每月维护记录数
        query = """
        SELECT 
            DATE_FORMAT(created_at, '%Y-%m') as month,
            COUNT(*) as count
        FROM 
            vehicle_logs
        WHERE 
            log_type = '维护记录'
            AND created_at >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY 
            DATE_FORMAT(created_at, '%Y-%m')
        ORDER BY 
            month
        """
        results = BaseDAO.execute_query(query)
        
        months = []
        counts = []
        
        for item in results:
            month = item['month']
            count = int(item['count'])
            
            months.append(month)
            counts.append(count)
        
        return {
            'months': months,
            'counts': counts
        }
    except Exception as e:
        print(f"获取维护趋势数据失败: {str(e)}")
        return {
            'months': [],
            'counts': []
        }

def get_model_maintenance_remaining_time():
    """获取各车型距维护剩余时间的平均值
    
    Returns:
        dict: 各车型距维护平均剩余天数
    """
    try:
        # 导入系统参数配置
        from app.config.vehicle_params import MAINTENANCE_INTERVAL
        
        # 获取当前日期
        current_date = datetime.now().date()
        
        # 获取各车型的车辆数据和维护日期信息
        query = """
        SELECT 
            model,
            last_maintenance_date,
            next_maintenance_date
        FROM 
            vehicles
        WHERE 
            is_available = 1
            AND last_maintenance_date IS NOT NULL
        """
        results = BaseDAO.execute_query(query)
        
        # 按车型分组计算平均剩余天数
        model_data = {}
        
        for vehicle in results:
            model = vehicle['model']
            last_maintenance = vehicle['last_maintenance_date']
            
            if last_maintenance:
                # 使用维护间隔计算预期下次维护日期
                expected_next_maintenance = last_maintenance + timedelta(days=MAINTENANCE_INTERVAL)
                # 计算距离下次维护的剩余天数（负值表示已逾期）
                remaining_days = (expected_next_maintenance - current_date).days
                
                if model not in model_data:
                    model_data[model] = []
                
                model_data[model].append(remaining_days)
        
        # 计算每个车型的平均剩余天数
        models = []
        avg_remaining_days = []
        
        for model, days_list in model_data.items():
            if days_list:  # 确保有数据
                avg_days = round(sum(days_list) / len(days_list), 1)
                models.append(model)
                avg_remaining_days.append(avg_days)
        
        # 排序结果（可选）
        sorted_data = sorted(zip(models, avg_remaining_days), key=lambda x: x[1])
        sorted_models, sorted_days = zip(*sorted_data) if sorted_data else ([], [])
        
        return {
            'models': list(sorted_models),
            'remaining_days': list(sorted_days),
            'maintenance_interval': MAINTENANCE_INTERVAL
        }
    except Exception as e:
        print(f"获取各车型维护剩余时间数据失败: {str(e)}")
        traceback.print_exc()
        return {
            'models': [],
            'remaining_days': [],
            'maintenance_interval': 90  # 默认值，避免前端出错
        }

def get_model_maintenance_frequency():
    """获取各车型平均每车维护次数（每两条维护记录算一次完整维护）
    
    Returns:
        dict: 各车型平均每车维护次数
    """
    try:
        # 获取各车型的车辆数量和维护记录数量
        query = """
        SELECT 
            v.model,
            COUNT(DISTINCT v.vehicle_id) as vehicle_count,
            COUNT(vl.log_id) as total_maintenance_records
        FROM 
            vehicles v
            LEFT JOIN vehicle_logs vl ON v.vehicle_id = vl.vehicle_id AND vl.log_type = '维护记录'
        WHERE 
            v.is_available = 1
        GROUP BY 
            v.model
        """
        results = BaseDAO.execute_query(query)
        
        models = []
        frequencies = []
        
        for item in results:
            model = item['model']
            vehicle_count = int(item['vehicle_count'])
            total_records = int(item['total_maintenance_records'])
            
            # 每两条记录计为一次完整维护
            complete_maintenance_count = total_records / 2 
            
            # 计算每辆车平均维护次数
            frequency = round(complete_maintenance_count / vehicle_count, 1) if vehicle_count > 0 else 0
            
            models.append(model)
            frequencies.append(frequency)
        
        # 按频率排序
        sorted_data = sorted(zip(models, frequencies), key=lambda x: x[1], reverse=True)
        sorted_models, sorted_frequencies = zip(*sorted_data) if sorted_data else ([], [])
        
        return {
            'models': list(sorted_models),
            'frequencies': list(sorted_frequencies)
        }
    except Exception as e:
        print(f"获取车型平均维护次数数据失败: {str(e)}")
        traceback.print_exc()
        return {
            'models': [],
            'frequencies': []
        }

def get_vehicle_age_maintenance_relation():
    """获取车辆年龄与维护次数关系数据
    
    计算每辆车的年龄和维护次数，以及累计维护成本
    
    Returns:
        dict: 车辆年龄与维护次数关系数据
    """
    try:
        # 获取车辆的年龄、维护记录数和支出信息
        query = """
        SELECT 
            v.vehicle_id,
            v.model,
            v.plate_number,
            TIMESTAMPDIFF(MONTH, v.registration_date, CURDATE())/12 as vehicle_age,
            COUNT(vl.log_id) as maintenance_records_count,
            COALESCE(SUM(e.amount), 0) as maintenance_cost
        FROM 
            vehicles v
            LEFT JOIN vehicle_logs vl ON v.vehicle_id = vl.vehicle_id AND vl.log_type = '维护记录'
            LEFT JOIN expense e ON v.vehicle_id = e.vehicle_id AND e.type = '车辆支出'
        WHERE 
            v.is_available = 1
            AND v.registration_date IS NOT NULL
        GROUP BY 
            v.vehicle_id, v.model, v.plate_number, vehicle_age
        """
        results = BaseDAO.execute_query(query)
        
        # 处理查询结果
        data_points = []
        
        for item in results:
            vehicle_age = float(item['vehicle_age'])
            # 每两条记录算一次完整维护
            maintenance_count = int(item['maintenance_records_count']) / 2
            maintenance_cost = float(item['maintenance_cost']) / 1000  # 转换为千元单位
            model = item['model']
            plate_number = item['plate_number']
            
            # 确保维护成本至少为1千元，确保气泡可见
            bubble_size = max(1, maintenance_cost)
            
            data_points.append({
                'x': round(vehicle_age, 1),                # 车辆年龄(年)
                'y': round(maintenance_count, 1),          # 维护次数
                'r': round(bubble_size * 2.5, 1),          # 气泡大小(与成本平方根成正比)
                'cost': round(maintenance_cost, 1),        # 维护成本(千元)
                'model': model,                            # 车型
                'plate': plate_number                      # 车牌号
            })
        
        # 计算趋势线数据
        if data_points:
            # 提取x和y值用于计算线性回归
            x_values = [point['x'] for point in data_points]
            y_values = [point['y'] for point in data_points]
            
            # 线性回归计算
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_xx = sum(x * x for x in x_values)
            
            # 计算斜率和截距
            if n > 0 and (n * sum_xx - sum_x * sum_x) != 0:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
                intercept = (sum_y - slope * sum_x) / n
                
                # 计算相关系数
                mean_x = sum_x / n
                mean_y = sum_y / n
                
                # 计算分子(协方差)
                numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
                
                # 计算分母(标准差乘积)
                denominator_x = sum((x - mean_x) ** 2 for x in x_values) ** 0.5
                denominator_y = sum((y - mean_y) ** 2 for y in y_values) ** 0.5
                denominator = denominator_x * denominator_y
                
                # 计算相关系数
                correlation = round(numerator / denominator, 2) if denominator != 0 else 0
                
                # 生成趋势线的点
                min_x = min(x_values)
                max_x = max(x_values)
                trendline = [
                    {'x': min_x, 'y': min_x * slope + intercept},
                    {'x': max_x, 'y': max_x * slope + intercept}
                ]
            else:
                slope = 0
                intercept = 0
                correlation = 0
                trendline = []
        else:
            slope = 0
            intercept = 0
            correlation = 0
            trendline = []
        
        # 按车型分组
        models = list(set(point['model'] for point in data_points))
        
        return {
            'data_points': data_points,
            'trendline': trendline,
            'correlation': correlation,
            'models': models
        }
    except Exception as e:
        print(f"获取车辆年龄与维护次数关系数据失败: {str(e)}")
        traceback.print_exc()
        return {
            'data_points': [],
            'trendline': [],
            'correlation': 0,
            'models': []
        }

def get_vehicle_age_distribution():
    """获取车辆年龄分布数据
    
    按照车辆年龄进行分组统计
    
    Returns:
        dict: 车辆年龄分布数据
    """
    try:
        # 获取车辆的年龄分布信息
        query = """
        SELECT 
            FLOOR(TIMESTAMPDIFF(MONTH, registration_date, CURDATE())/12) as age_year,
            COUNT(*) as vehicle_count,
            model
        FROM 
            vehicles
        WHERE 
            is_available = 1
            AND registration_date IS NOT NULL
        GROUP BY 
            age_year, model
        ORDER BY 
            age_year
        """
        results = BaseDAO.execute_query(query)
        
        # 处理查询结果
        age_groups = {}
        models = []
        
        # 收集所有车型
        for item in results:
            model = item['model']
            if model not in models:
                models.append(model)
        
        # 按车龄分组处理数据
        for item in results:
            age = float(item['age_year'])
            count = int(item['vehicle_count'])
            model = item['model']
            
            # 将车龄四舍五入到最接近的0.5
            rounded_age = round(age * 2) / 2
            
            # 创建键名
            age_key = str(rounded_age)
            
            if age_key not in age_groups:
                age_groups[age_key] = {model: 0 for model in models}
                age_groups[age_key]['total'] = 0
            
            # 确保该车型的键存在
            if model not in age_groups[age_key]:
                age_groups[age_key][model] = 0
                
            age_groups[age_key][model] += count
            age_groups[age_key]['total'] += count
        
        # 转换为图表所需格式
        labels = sorted(age_groups.keys(), key=lambda x: float(x))
        datasets = []
        
        # 为每个车型创建一个数据集
        colors = [
            'rgba(255, 99, 132, 0.7)',   # 红色
            'rgba(54, 162, 235, 0.7)',   # 蓝色
            'rgba(255, 206, 86, 0.7)',   # 黄色
            'rgba(75, 192, 192, 0.7)',   # 绿色
            'rgba(153, 102, 255, 0.7)',  # 紫色
            'rgba(255, 159, 64, 0.7)',   # 橙色
            'rgba(199, 199, 199, 0.7)',  # 灰色
            'rgba(83, 102, 255, 0.7)',   # 靛蓝色
            'rgba(255, 99, 255, 0.7)',   # 粉色
            'rgba(99, 255, 132, 0.7)'    # 浅绿色
        ]
        
        for i, model in enumerate(models):
            data = []
            for age in labels:
                data.append(age_groups[age][model])
            
            color_index = i % len(colors)
            
            datasets.append({
                'label': model,
                'data': data,
                'backgroundColor': colors[color_index],
                'borderColor': colors[color_index].replace('0.7', '1'),
                'borderWidth': 1
            })
        
        return {
            'labels': [f"{label}年" for label in labels],
            'datasets': datasets
        }
    except Exception as e:
        print(f"获取车辆年龄分布数据失败: {str(e)}")
        traceback.print_exc()
        return {
            'labels': [],
            'datasets': []
        }
