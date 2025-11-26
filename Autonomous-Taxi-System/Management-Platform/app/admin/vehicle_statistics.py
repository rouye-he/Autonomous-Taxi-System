from flask import Blueprint, render_template, request
from app.dao.base_dao import BaseDAO
from app.dao.vehicle_dao import VehicleDAO
from app.dao.order_dao import OrderDAO
from datetime import datetime, timedelta
import json
import traceback

# 创建蓝图
vehicle_stats_bp = Blueprint('vehicle_stats', __name__, url_prefix='/vehicle-stats')

def calculate_statistics(start_date, end_date):
    """计算所有车辆统计数据
    
    Args:
        start_date: 开始日期对象
        end_date: 结束日期对象
        
    Returns:
        dict: 包含所有统计数据的字典
    """
    try:
        stats = {}
        
        # 获取日期范围天数
        days_in_range = (end_date - start_date).days + 1
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 计算车辆日均行驶里程分布
        stats['mileage_distribution'] = get_mileage_distribution(start_date, end_date, days_in_range)
        
        # 计算各车型累计完成订单数和里程排名
        model_stats = get_model_rankings(start_date, end_date)
        stats.update(model_stats)
        
        return stats
    except Exception as e:
        print(f"计算车辆统计数据失败: {str(e)}")
        traceback.print_exc()
        return {}

def get_mileage_distribution(start_date, end_date, days_in_range):
    """计算车辆日均行驶里程分布数据
    
    Args:
        start_date: 开始日期对象
        end_date: 结束日期对象
        days_in_range: 日期范围天数
        
    Returns:
        list: 里程分布数据
    """
    # 计算每辆车在指定时间段内的日均行驶里程
    query = """
    SELECT 
        v.vehicle_id,
        v.model,
        COALESCE(SUM(od.distance), 0) as total_distance,
        COALESCE(SUM(od.distance) / %s, 0) as daily_distance
    FROM 
        vehicles v
    LEFT JOIN 
        order_details od ON v.vehicle_id = od.vehicle_id
    WHERE 
        od.created_at BETWEEN %s AND %s
    GROUP BY 
        v.vehicle_id, v.model
    """
    
    result = BaseDAO.execute_query(query, (
        days_in_range, 
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    # 按车型分组计算里程统计数据
    model_groups = {}
    for vehicle in result:
        model = vehicle['model']
        if model not in model_groups:
            model_groups[model] = []
        
        model_groups[model].append(float(vehicle['daily_distance']))
    
    # 处理成箱线图格式数据
    boxplot_data = []
    for model, distances in model_groups.items():
        if not distances:  # 跳过没有数据的车型
            continue
            
        distances.sort()
        n = len(distances)
        
        # 计算箱线图所需的五个数值点
        min_val = distances[0]
        max_val = distances[-1]
        
        # 计算四分位数
        q1_idx = int(n * 0.25)
        median_idx = int(n * 0.5)
        q3_idx = int(n * 0.75)
        
        q1 = distances[q1_idx]
        median = distances[median_idx]
        q3 = distances[q3_idx]
        
        boxplot_data.append({
            'label': model,
            'min': min_val,
            'q1': q1,
            'median': median,
            'q3': q3,
            'max': max_val
        })
    
    return boxplot_data

def get_model_rankings(start_date, end_date):
    """计算各车型的累计订单数和里程排名
    
    Args:
        start_date: 开始日期对象
        end_date: 结束日期对象
        
    Returns:
        dict: 包含车型排名数据的字典
    """
    # 各车型累计完成订单数排名
    orders_query = """
    SELECT 
        v.model, 
        COUNT(o.order_id) as total_orders
    FROM 
        vehicles v
    LEFT JOIN 
        orders o ON v.vehicle_id = o.vehicle_id
    WHERE 
        o.create_time BETWEEN %s AND %s
        AND o.order_status = '已结束'
    GROUP BY 
        v.model
    ORDER BY 
        total_orders DESC
    LIMIT 10
    """
    
    orders_result = BaseDAO.execute_query(orders_query, (
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    # 各车型累计行驶里程排名 - 使用vehicles表中的mileage字段获取车辆累计里程
    mileage_query = """
    SELECT 
        model,
        SUM(mileage) as total_mileage
    FROM 
        vehicles
    GROUP BY 
        model
    ORDER BY 
        total_mileage DESC
    LIMIT 10
    """
    
    mileage_result = BaseDAO.execute_query(mileage_query)
    
    # 提取标签和数据
    model_labels = [item['model'] for item in orders_result]
    model_orders_data = [int(item['total_orders']) for item in orders_result]
    
    # 确保里程数据与订单数据使用相同顺序的车型标签
    mileage_dict = {item['model']: float(item['total_mileage']) for item in mileage_result}
    model_mileage_data = []
    
    for model in model_labels:
        if model in mileage_dict:
            model_mileage_data.append(mileage_dict[model])
        else:
            model_mileage_data.append(0)
    
    return {
        'model_labels': model_labels,
        'model_orders_data': model_orders_data,
        'model_mileage_data': model_mileage_data
    }

@vehicle_stats_bp.route('/mileage-distribution')
def mileage_distribution():
    """车辆日均行驶里程分布页面"""
    try:
        # 获取日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # 默认30天
        
        date_range = request.args.get('date_range', 'last_30_days')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # 如果有明确的开始和结束日期，使用它们
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
            except ValueError:
                print(f"日期格式错误: {start_date_str} 或 {end_date_str}")
        else:
            # 根据日期范围设置日期
            if date_range == 'last_3_days':
                start_date = end_date - timedelta(days=3)
            elif date_range == 'last_7_days':
                start_date = end_date - timedelta(days=7)
            elif date_range == 'last_90_days':
                start_date = end_date - timedelta(days=90)
            elif date_range == 'last_180_days':
                start_date = end_date - timedelta(days=180)
        
        # 计算日期范围天数
        days_in_range = (end_date - start_date).days + 1
        
        # 获取车辆日均行驶里程分布数据
        mileage_distribution = get_mileage_distribution(start_date, end_date, days_in_range)
        
        return render_template('analytics/mileage-distribution.html',
                              mileage_distribution_data=json.dumps(mileage_distribution),
                              start_date=start_date.strftime('%Y-%m-%d'),
                              end_date=end_date.strftime('%Y-%m-%d'),
                              date_range=date_range)
                              
    except Exception as e:
        print(f"获取车辆日均行驶里程分布数据失败: {str(e)}")
        traceback.print_exc()
        return "数据获取失败"

@vehicle_stats_bp.route('/model-rankings')
def model_rankings():
    """各车型累计数据排名页面"""
    try:
        # 获取日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # 默认30天
        
        date_range = request.args.get('date_range', 'last_30_days')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # 如果有明确的开始和结束日期，使用它们
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
            except ValueError:
                print(f"日期格式错误: {start_date_str} 或 {end_date_str}")
        else:
            # 根据日期范围设置日期
            if date_range == 'last_3_days':
                start_date = end_date - timedelta(days=3)
            elif date_range == 'last_7_days':
                start_date = end_date - timedelta(days=7)
            elif date_range == 'last_90_days':
                start_date = end_date - timedelta(days=90)
            elif date_range == 'last_180_days':
                start_date = end_date - timedelta(days=180)
        
        # 获取车型排名数据
        model_rankings = get_model_rankings(start_date, end_date)
        
        return render_template('analytics/model-rankings.html',
                              model_labels=json.dumps(model_rankings['model_labels']),
                              model_orders_data=json.dumps(model_rankings['model_orders_data']),
                              model_mileage_data=json.dumps(model_rankings['model_mileage_data']),
                              start_date=start_date.strftime('%Y-%m-%d'),
                              end_date=end_date.strftime('%Y-%m-%d'),
                              date_range=date_range)
                              
    except Exception as e:
        print(f"获取车型排名数据失败: {str(e)}")
        traceback.print_exc()
        return "数据获取失败" 