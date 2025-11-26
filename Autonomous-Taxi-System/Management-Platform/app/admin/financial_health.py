from flask import Blueprint, jsonify, request
from app.dao.base_dao import BaseDAO
from datetime import datetime, timedelta
import json
from decimal import Decimal
import numpy as np
import pandas as pd

# 创建蓝图
financial_health_bp = Blueprint('financial_health', __name__, url_prefix='/analytics/api')

# 添加Decimal序列化处理函数
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

# 获取日期范围的辅助函数
def get_date_range(days=30):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

# 使用numpy实现简单线性回归函数
def linear_regression(x, y):
    """使用numpy实现简单线性回归
    
    Args:
        x: 自变量数组
        y: 因变量数组
        
    Returns:
        tuple: (斜率, 截距)
    """
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    
    # 计算斜率 (slope)
    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean) ** 2)
    
    slope = numerator / denominator if denominator != 0 else 0
    
    # 计算截距 (intercept)
    intercept = y_mean - slope * x_mean
    
    return slope, intercept

@financial_health_bp.route('/finance_balance_data')
def finance_balance_data():
    """获取实时收支动态平衡仪表盘数据API
    
    Returns:
        JSON: 包含总收入、总支出、收支平衡和收支明细的数据
    """
    try:
        # 从请求中获取日期参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 如果没有提供日期参数，则使用默认的最近30天
        if not start_date or not end_date:
            start_date, end_date = get_date_range(30)
        
        # 获取总收入
        income_query = """
        SELECT COALESCE(SUM(amount), 0) as total_income
        FROM income
        WHERE date BETWEEN %s AND %s
        """
        income_result = BaseDAO.execute_query(income_query, (start_date, end_date))
        total_income = float(income_result[0]['total_income'] if income_result else 0)
        
        # 获取总支出
        expense_query = """
        SELECT COALESCE(SUM(amount), 0) as total_expense
        FROM expense
        WHERE date BETWEEN %s AND %s
        """
        expense_result = BaseDAO.execute_query(expense_query, (start_date, end_date))
        total_expense = float(expense_result[0]['total_expense'] if expense_result else 0)
        
        # 计算收支平衡和利润率
        balance = total_income - total_expense
        profit_margin = round(balance / total_income * 100, 1) if total_income > 0 else 0
        
        # 获取收入明细数据
        income_breakdown_query = """
        SELECT source, COALESCE(SUM(amount), 0) as total
        FROM income
        WHERE date BETWEEN %s AND %s
        GROUP BY source
        ORDER BY total DESC
        """
        income_breakdown_result = BaseDAO.execute_query(income_breakdown_query, (start_date, end_date))
        
        # 构建收入明细字典
        income_breakdown = {}
        for item in income_breakdown_result:
            income_breakdown[item['source']] = float(item['total'])
        
        # 获取支出明细数据
        expense_breakdown_query = """
        SELECT type, COALESCE(SUM(amount), 0) as total
        FROM expense
        WHERE date BETWEEN %s AND %s
        GROUP BY type
        ORDER BY total DESC
        """
        expense_breakdown_result = BaseDAO.execute_query(expense_breakdown_query, (start_date, end_date))
        
        # 构建支出明细字典
        expense_breakdown = {}
        for item in expense_breakdown_result:
            expense_breakdown[item['type']] = float(item['total'])
        
        # 构建返回数据
        result = {
            'totalIncome': total_income,
            'totalExpense': total_expense,
            'balance': balance,
            'profitMargin': profit_margin,
            'incomeBreakdown': income_breakdown,
            'expenseBreakdown': expense_breakdown
        }
        
        return jsonify(result)
    
    except Exception as e:
        print(f"获取收支平衡数据失败: {str(e)}")
        # 返回服务器错误状态码
        return jsonify({
            'error': '获取数据失败',
            'message': str(e)
        }), 500

@financial_health_bp.route('/cost_structure_data')
def cost_structure_data():
    """获取成本结构桑基图数据API
    
    Returns:
        JSON: 包含桑基图节点和链接数据
    """
    try:
        # 从请求中获取日期参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 如果没有提供日期参数，则使用默认的最近90天
        if not start_date or not end_date:
            start_date, end_date = get_date_range(90)
        
        # 获取支出主类型数据
        expense_types_query = """
        SELECT type, COALESCE(SUM(amount), 0) as total
        FROM expense
        WHERE date BETWEEN %s AND %s
        GROUP BY type
        ORDER BY total DESC
        """
        expense_types_result = BaseDAO.execute_query(expense_types_query, (start_date, end_date))
        
        # 构建节点和连接数据
        nodes = [{'name': '总支出'}]
        links = []
        
        # 计算总支出
        total_expense = 0
        for item in expense_types_result:
            total_expense += float(item['total'])
            # 添加支出类型节点
            nodes.append({'name': item['type']})
            # 添加从总支出到各类型的链接
            links.append({
                'source': '总支出',
                'target': item['type'],
                'value': float(item['total'])
            })
        
        # 获取详细支出分类数据（基于描述）
        # 1. 获取车辆支出的详细分类
        vehicle_expense_query = """
        SELECT 
            CASE 
                WHEN description LIKE '%保险%' THEN '车辆保险'
                WHEN description LIKE '%维护%' OR description LIKE '%维修%' OR description LIKE '%保养%' THEN '车辆维护'
                WHEN description LIKE '%购置%' OR description LIKE '%购买%' OR description LIKE '%采购%' THEN '车辆采购'
                ELSE '其他车辆支出'
            END as sub_type,
            COALESCE(SUM(amount), 0) as total
        FROM expense
        WHERE type = '车辆支出' AND date BETWEEN %s AND %s
        GROUP BY sub_type
        ORDER BY total DESC
        """
        vehicle_expense_result = BaseDAO.execute_query(vehicle_expense_query, (start_date, end_date))
        
        # 添加车辆支出的子节点和链接
        for item in vehicle_expense_result:
            sub_type = item['sub_type']
            amount = float(item['total'])
            # 添加子节点
            nodes.append({'name': sub_type})
            # 添加从车辆支出到子类型的链接
            links.append({
                'source': '车辆支出',
                'target': sub_type,
                'value': amount
            })
        
        # 2. 获取充电站支出的详细分类
        charging_expense_query = """
        SELECT 
            CASE 
                WHEN amount < 10000 THEN '充电费用'
                WHEN description LIKE '%维护%' OR description LIKE '%维修%' OR description LIKE '%检测%' THEN '充电站维护'
                WHEN description LIKE '%建设%' OR description LIKE '%建造%' OR description LIKE '%安装%' THEN '充电站建设'
                ELSE '其他充电站支出'
            END as sub_type,
            COALESCE(SUM(amount), 0) as total
        FROM expense
        WHERE type = '充电站支出' AND date BETWEEN %s AND %s
        GROUP BY sub_type
        ORDER BY total DESC
        """
        charging_expense_result = BaseDAO.execute_query(charging_expense_query, (start_date, end_date))
        
        # 添加充电站支出的子节点和链接
        for item in charging_expense_result:
            sub_type = item['sub_type']
            amount = float(item['total'])
            # 添加子节点
            nodes.append({'name': sub_type})
            # 添加从充电站支出到子类型的链接
            links.append({
                'source': '充电站支出',
                'target': sub_type,
                'value': amount
            })
        
        # 3. 获取其他支出的详细分类
        other_expense_query = """
        SELECT 
            CASE 
                WHEN description LIKE '%人工%' OR description LIKE '%工资%' OR description LIKE '%薪资%' THEN '人力成本'
                WHEN description LIKE '%平台%' OR description LIKE '%系统%' OR description LIKE '%服务器%' THEN '平台运营'
                WHEN description LIKE '%营销%' OR description LIKE '%推广%' OR description LIKE '%广告%' THEN '市场营销'
                ELSE '其他运营支出'
            END as sub_type,
            COALESCE(SUM(amount), 0) as total
        FROM expense
        WHERE type = '其他支出' AND date BETWEEN %s AND %s
        GROUP BY sub_type
        ORDER BY total DESC
        """
        other_expense_result = BaseDAO.execute_query(other_expense_query, (start_date, end_date))
        
        # 添加其他支出的子节点和链接
        for item in other_expense_result:
            sub_type = item['sub_type']
            amount = float(item['total'])
            # 添加子节点
            nodes.append({'name': sub_type})
            # 添加从其他支出到子类型的链接
            links.append({
                'source': '其他支出',
                'target': sub_type,
                'value': amount
            })
        
        # 构建最终返回数据
        result = {
            'nodes': nodes,
            'links': links
        }
        
        return jsonify(result)
    
    except Exception as e:
        print(f"获取成本结构数据失败: {str(e)}")
        # 返回服务器错误状态码
        return jsonify({
            'error': '获取数据失败',
            'message': str(e)
        }), 500

@financial_health_bp.route('/financial_metrics_forecast')
def financial_metrics_forecast():
    """获取关键财务指标预测趋势图数据API
    
    Returns:
        JSON: 包含历史和预测的收入、支出、利润数据
    """
    try:
        # 从请求中获取日期参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 如果没有提供日期参数，则使用默认的最近90天
        if not start_date or not end_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 获取按日期分组的收入数据
        income_query = """
        SELECT 
            date,
            COALESCE(SUM(amount), 0) as total_income
        FROM income
        WHERE date BETWEEN %s AND %s
        GROUP BY date
        ORDER BY date
        """
        income_data = BaseDAO.execute_query(income_query, (start_date, end_date))
        
        # 获取按日期分组的支出数据
        expense_query = """
        SELECT 
            date,
            COALESCE(SUM(amount), 0) as total_expense
        FROM expense
        WHERE date BETWEEN %s AND %s
        GROUP BY date
        ORDER BY date
        """
        expense_data = BaseDAO.execute_query(expense_query, (start_date, end_date))
        
        # 如果收入或支出数据为空，则抛出异常
        if not income_data or not expense_data:
            raise Exception("收入或支出数据获取失败，缺少足够的数据进行预测")
        
        # 将查询结果转换为DataFrame以便进行预测分析
        income_df = pd.DataFrame(income_data)
        income_df['date'] = pd.to_datetime(income_df['date'])
        income_df.set_index('date', inplace=True)
        
        expense_df = pd.DataFrame(expense_data)
        expense_df['date'] = pd.to_datetime(expense_df['date'])
        expense_df.set_index('date', inplace=True)
        
        # 确保数据连续性，使用日期作为索引并进行重采样
        date_range = pd.date_range(start=start_date, end=end_date)
        
        # 重建具有连续日期索引的数据框
        income_df_resampled = income_df.reindex(date_range, fill_value=0)
        expense_df_resampled = expense_df.reindex(date_range, fill_value=0)
        
        # 创建一个包含利润的DataFrame
        profit_df = pd.DataFrame(index=date_range)
        profit_df['total_profit'] = income_df_resampled['total_income'] - expense_df_resampled['total_expense']
        
        # 应用7天移动平均来平滑数据
        income_smooth = income_df_resampled['total_income'].rolling(window=7, min_periods=1).mean()
        expense_smooth = expense_df_resampled['total_expense'].rolling(window=7, min_periods=1).mean()
        profit_smooth = profit_df['total_profit'].rolling(window=7, min_periods=1).mean()
        
        # 使用线性回归进行简单预测
        forecast_days = 30  # 预测未来30天
        
        # 为预测准备X数据（数字序列）
        X_history = np.array(range(len(income_smooth)))
        
        # 为预测准备X数据（未来日期）
        X_future = np.array(range(len(income_smooth), len(income_smooth) + forecast_days))
        
        # 应用线性回归进行预测
        # 收入预测
        income_slope, income_intercept = linear_regression(X_history, income_smooth.values)
        income_forecast = income_slope * X_future + income_intercept
        
        # 支出预测
        expense_slope, expense_intercept = linear_regression(X_history, expense_smooth.values)
        expense_forecast = expense_slope * X_future + expense_intercept
        
        # 利润预测
        profit_slope, profit_intercept = linear_regression(X_history, profit_smooth.values)
        profit_forecast = profit_slope * X_future + profit_intercept
        
        # 确保预测值不为负
        income_forecast = np.maximum(income_forecast, 0)
        expense_forecast = np.maximum(expense_forecast, 0)
        
        # 生成预测日期
        last_date = date_range[-1]
        future_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
        
        # 构建返回数据结构
        all_dates = [d.strftime('%Y-%m-%d') for d in date_range] + [d.strftime('%Y-%m-%d') for d in future_dates]
        
        # 获取历史实际数据
        income_history = income_smooth.tolist()
        expense_history = expense_smooth.tolist()
        profit_history = profit_smooth.tolist()
        
        # 拼接历史数据和预测数据
        income_with_forecast = income_history + [None] * forecast_days
        expense_with_forecast = expense_history + [None] * forecast_days
        profit_with_forecast = profit_history + [None] * forecast_days
        
        income_forecast_full = [None] * len(income_history) + income_forecast.tolist()
        expense_forecast_full = [None] * len(expense_history) + expense_forecast.tolist()
        profit_forecast_full = [None] * len(profit_history) + profit_forecast.tolist()
        
        result = {
            'dates': all_dates,
            'incomeData': income_with_forecast,
            'expenseData': expense_with_forecast,
            'profitData': profit_with_forecast,
            'incomeDataForecast': income_forecast_full,
            'expenseDataForecast': expense_forecast_full,
            'profitDataForecast': profit_forecast_full
        }
        
        return jsonify(result)
    
    except Exception as e:
        print(f"获取财务指标预测数据失败: {str(e)}")
        # 返回服务器错误状态码
        return jsonify({
            'error': '获取数据失败',
            'message': str(e)
        }), 500

@financial_health_bp.route('/city_financial_data')
def city_financial_data():
    """获取城市收入雷达图数据API
    
    Returns:
        JSON: 包含城市财务表现的多维指标数据
    """
    try:
        # 从请求中获取日期参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 如果没有提供日期参数，则使用默认的最近60天
        if not start_date or not end_date:
            start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 查询各城市的订单总量
        orders_query = """
        SELECT 
            city_code,
            COUNT(*) as order_count
        FROM orders
        WHERE city_code IS NOT NULL 
        AND create_time BETWEEN %s AND %s
        GROUP BY city_code
        """
        orders_data = BaseDAO.execute_query(orders_query, (f"{start_date} 00:00:00", f"{end_date} 23:59:59"))
        
        # 查询各城市的订单完成率
        completion_query = """
        SELECT 
            city_code,
            COUNT(*) as total_orders,
            SUM(CASE WHEN order_status = '已结束' THEN 1 ELSE 0 END) as completed_orders
        FROM orders
        WHERE city_code IS NOT NULL 
        AND create_time BETWEEN %s AND %s
        GROUP BY city_code
        """
        completion_data = BaseDAO.execute_query(completion_query, (f"{start_date} 00:00:00", f"{end_date} 23:59:59"))
        
        # 查询各城市的人均订单金额
        avg_order_query = """
        SELECT 
            o.city_code,
            AVG(od.amount) as avg_amount
        FROM orders o
        JOIN order_details od ON o.order_number = od.order_id
        WHERE o.city_code IS NOT NULL 
        AND o.create_time BETWEEN %s AND %s
        GROUP BY o.city_code
        """
        avg_order_data = BaseDAO.execute_query(avg_order_query, (f"{start_date} 00:00:00", f"{end_date} 23:59:59"))
        
        # 查询各城市的订单行驶里程
        distance_query = """
        SELECT 
            o.city_code,
            AVG(od.distance) as avg_distance
        FROM orders o
        JOIN order_details od ON o.order_number = od.order_id
        WHERE o.city_code IS NOT NULL 
        AND o.create_time BETWEEN %s AND %s
        GROUP BY o.city_code
        """
        distance_data = BaseDAO.execute_query(distance_query, (f"{start_date} 00:00:00", f"{end_date} 23:59:59"))
        
        # 查询各城市的用户注册量
        user_query = """
        SELECT 
            registration_city,
            COUNT(*) as user_count
        FROM users
        WHERE registration_city IS NOT NULL
        AND registration_time BETWEEN %s AND %s
        GROUP BY registration_city
        """
        user_data = BaseDAO.execute_query(user_query, (f"{start_date} 00:00:00", f"{end_date} 23:59:59"))
        
        # 检查是否有数据
        if not orders_data and not completion_data and not avg_order_data and not distance_data and not user_data:
            # 如果所有查询都没有返回数据，返回一个空数据结构但不报错
            return jsonify({
                'indicators': [
                    {'name': '订单总量', 'max': 100},
                    {'name': '订单完成率', 'max': 100},
                    {'name': '平均订单金额', 'max': 100},
                    {'name': '平均行驶里程', 'max': 100},
                    {'name': '新增用户数', 'max': 100}
                ],
                'cities': []
            })
        
        # 合并数据并计算指标
        city_metrics = {}
        
        # 处理订单数据
        for item in orders_data:
            city = item['city_code']
            if city not in city_metrics:
                city_metrics[city] = {'city': city}
            city_metrics[city]['order_count'] = float(item['order_count'])
        
        # 处理完成率数据
        for item in completion_data:
            city = item['city_code']
            if city not in city_metrics:
                city_metrics[city] = {'city': city}
            total = float(item['total_orders'])
            completed = float(item['completed_orders'])
            city_metrics[city]['completion_rate'] = (completed / total * 100) if total > 0 else 0
        
        # 处理平均订单金额数据
        for item in avg_order_data:
            city = item['city_code']
            if city not in city_metrics:
                city_metrics[city] = {'city': city}
            city_metrics[city]['avg_amount'] = float(item['avg_amount'])
        
        # 处理平均行驶里程数据
        for item in distance_data:
            city = item['city_code']
            if city not in city_metrics:
                city_metrics[city] = {'city': city}
            city_metrics[city]['avg_distance'] = float(item['avg_distance'])
        
        # 处理用户注册量数据
        for item in user_data:
            city = item['registration_city']
            if city not in city_metrics:
                city_metrics[city] = {'city': city}
            city_metrics[city]['user_count'] = float(item['user_count'])
        
        # 设置默认值，确保所有城市都有完整的指标
        for city in city_metrics:
            city_metrics[city].setdefault('order_count', 0)
            city_metrics[city].setdefault('completion_rate', 0)
            city_metrics[city].setdefault('avg_amount', 0)
            city_metrics[city].setdefault('avg_distance', 0)
            city_metrics[city].setdefault('user_count', 0)
        
        # 检查是否有city_metrics数据
        if not city_metrics:
            return jsonify({
                'indicators': [
                    {'name': '订单总量', 'max': 100},
                    {'name': '订单完成率', 'max': 100},
                    {'name': '平均订单金额', 'max': 100},
                    {'name': '平均行驶里程', 'max': 100},
                    {'name': '新增用户数', 'max': 100}
                ],
                'cities': []
            })
        
        # 获取所有指标的最大值，用于数据标准化，防止除零错误
        order_count_values = [m['order_count'] for m in city_metrics.values()]
        avg_amount_values = [m['avg_amount'] for m in city_metrics.values()]
        avg_distance_values = [m['avg_distance'] for m in city_metrics.values()]
        user_count_values = [m['user_count'] for m in city_metrics.values()]
        
        max_order_count = max(order_count_values) if order_count_values and max(order_count_values) > 0 else 1
        max_completion_rate = 100  # 完成率最大为100%
        max_avg_amount = max(avg_amount_values) if avg_amount_values and max(avg_amount_values) > 0 else 1
        max_avg_distance = max(avg_distance_values) if avg_distance_values and max(avg_distance_values) > 0 else 1
        max_user_count = max(user_count_values) if user_count_values and max(user_count_values) > 0 else 1
        
        # 准备雷达图数据
        indicators = [
            {'name': '订单总量', 'max': 100},
            {'name': '订单完成率', 'max': 100},
            {'name': '平均订单金额', 'max': 100},
            {'name': '平均行驶里程', 'max': 100},
            {'name': '新增用户数', 'max': 100}
        ]
        
        # 准备各城市数据
        cities_data = []
        for city, metrics in city_metrics.items():
            # 标准化数据到0-100，防止除零错误
            data = [
                round(metrics['order_count'] / max_order_count * 100, 1) if max_order_count > 0 else 0,
                round(metrics['completion_rate'], 1),
                round(metrics['avg_amount'] / max_avg_amount * 100, 1) if max_avg_amount > 0 else 0,
                round(metrics['avg_distance'] / max_avg_distance * 100, 1) if max_avg_distance > 0 else 0,
                round(metrics['user_count'] / max_user_count * 100, 1) if max_user_count > 0 else 0
            ]
            
            # 添加原始值信息到雷达图数据
            cities_data.append({
                'name': city,
                'value': data,
                'originalData': {
                    '订单总量': metrics['order_count'],
                    '订单完成率': f"{metrics['completion_rate']}%",
                    '平均订单金额': f"{metrics['avg_amount']}元",
                    '平均行驶里程': f"{metrics['avg_distance']}公里",
                    '新增用户数': metrics['user_count']
                }
            })
        
        # 按照订单总量排序
        cities_data.sort(key=lambda x: x['value'][0], reverse=True)
        
        # 构建返回数据
        result = {
            'indicators': indicators,
            'cities': cities_data
        }
        
        return jsonify(result)
    
    except Exception as e:
        print(f"获取城市财务数据失败: {str(e)}")
        # 返回服务器错误状态码
        return jsonify({
            'indicators': [
                {'name': '订单总量', 'max': 100},
                {'name': '订单完成率', 'max': 100},
                {'name': '平均订单金额', 'max': 100},
                {'name': '平均行驶里程', 'max': 100},
                {'name': '新增用户数', 'max': 100}
            ],
            'cities': [],
            'error': '获取数据失败',
            'message': str(e)
        }), 500

@financial_health_bp.route('/credit_income_data')
def credit_income_data():
    """获取用户信用分vs.人均贡献收入气泡图数据API
    
    Returns:
        JSON: 包含用户信用分与收入贡献关系的气泡数据
    """
    try:
        # 确定日期范围，获取最近90天的数据
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 综合查询用户信用分、累计消费金额和订单数
        # 修改SQL查询，直接关联order_details表获取准确的用户贡献收入
        query = """
        SELECT 
            u.credit_score,
            COUNT(DISTINCT od.id) as order_count,
            COALESCE(SUM(od.amount), 0) as total_amount,
            COUNT(DISTINCT u.user_id) as user_count
        FROM 
            users u
            LEFT JOIN order_details od ON u.user_id = od.user_id 
            AND od.created_at BETWEEN %s AND %s
        WHERE 
            u.credit_score IS NOT NULL
        GROUP BY 
            u.credit_score
        ORDER BY 
            u.credit_score
        """
        
        # 执行查询
        result_data = BaseDAO.execute_query(query, (f"{start_date} 00:00:00", f"{end_date} 23:59:59"))
        
        if not result_data:
            raise Exception("未找到符合条件的用户信用分与收入数据")
        
        # 处理查询结果，准备气泡图数据
        bubble_data = []
        max_user_count = 0
        
        for item in result_data:
            credit_score = float(item['credit_score'])
            user_count = int(item['user_count'])
            
            # 计算人均贡献收入
            if user_count > 0 and item['order_count'] > 0:
                avg_income = float(item['total_amount']) / user_count
            else:
                avg_income = 0
            
            # 更新最大用户数量（用于气泡大小缩放）
            max_user_count = max(max_user_count, user_count)
            
            # 将数据添加到气泡图数据中
            bubble_data.append([credit_score, avg_income, user_count])
        
        # 构建返回数据
        result = {
            'bubbleData': bubble_data,
            'maxUserCount': max_user_count
        }
        
        return jsonify(result)
    
    except Exception as e:
        print(f"获取用户信用-收入数据失败: {str(e)}")
        # 返回服务器错误状态码
        return jsonify({
            'error': '获取数据失败',
            'message': str(e)
        }), 500

@financial_health_bp.route('/vehicle_roi_data')
def vehicle_roi_data():
    """获取车辆资产回报箱线图数据API
    
    Returns:
        JSON: 包含不同车型的投资回报数据
    """
    try:
        # 从请求中获取日期参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 如果没有提供日期参数，则使用默认的最近90天
        if not start_date or not end_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        # 获取所有车型列表
        models_query = """
        SELECT DISTINCT model 
        FROM vehicles
        ORDER BY model
        """
        models_result = BaseDAO.execute_query(models_query)
        
        if not models_result:
            raise Exception("未找到车辆型号数据")
        
        # 收集所有车型及其箱线图数据
        result_data = []
        
        for model_item in models_result:
            model = model_item['model']
            
            # 查询该车型的所有车辆数据，使用日期参数限定订单时间范围
            vehicles_query = """
            SELECT 
                v.vehicle_id,
                v.model,
                v.purchase_price,
                v.registration_date,
                v.total_orders,
                COALESCE(SUM(od.amount), 0) as total_income,
                DATEDIFF(NOW(), v.registration_date) as days_in_service
            FROM 
                vehicles v
                LEFT JOIN orders o ON v.vehicle_id = o.vehicle_id AND o.create_time BETWEEN %s AND %s
                LEFT JOIN order_details od ON o.order_number = od.order_id
            WHERE 
                v.model = %s
            GROUP BY 
                v.vehicle_id
            """
            
            vehicles_data = BaseDAO.execute_query(vehicles_query, (f"{start_date} 00:00:00", f"{end_date} 23:59:59", model))
            
            if not vehicles_data:
                continue
            
            # 计算投资回报率数据
            roi_data = []
            purchase_prices = []
            
            for vehicle in vehicles_data:
                # 避免除以零
                days_in_service = max(1, float(vehicle['days_in_service'] or 1))
                purchase_price = float(vehicle['purchase_price'] or 0)
                
                if purchase_price <= 0:
                    continue
                
                total_income = float(vehicle['total_income'] or 0)
                
                # 计算投资回报率(%)
                roi_percentage = (total_income / purchase_price) * 100
                
                # 计算每日平均回报率
                daily_roi = roi_percentage / days_in_service
                
                # 添加到数据集
                roi_data.append(daily_roi)
                purchase_prices.append(purchase_price)
            
            if not roi_data:
                continue
            
            # 计算箱线图数据(最小值、下四分位数、中位数、上四分位数、最大值)
            roi_min = min(roi_data)
            roi_max = max(roi_data)
            
            roi_sorted = sorted(roi_data)
            n = len(roi_sorted)
            
            roi_median = roi_sorted[n // 2] if n % 2 == 1 else (roi_sorted[n // 2 - 1] + roi_sorted[n // 2]) / 2
            roi_q1 = roi_sorted[n // 4]
            roi_q3 = roi_sorted[3 * n // 4]
            
            # 计算平均购置成本
            avg_purchase_price = sum(purchase_prices) / len(purchase_prices) if purchase_prices else 0
            
            # 添加到结果集
            model_data = {
                'model': model,
                'boxplot': [roi_min, roi_q1, roi_median, roi_q3, roi_max],
                'avgPurchasePrice': avg_purchase_price,
                'vehicleCount': len(roi_data)
            }
            
            result_data.append(model_data)
        
        # 返回结果
        return jsonify(result_data)
    
    except Exception as e:
        print(f"获取车辆资产回报数据失败: {str(e)}")
        # 返回服务器错误状态码
        return jsonify({
            'error': '获取数据失败',
            'message': str(e)
        }), 500

@financial_health_bp.route('/coupon_package_data')
def coupon_package_data():
    """获取优惠券套餐销售贡献旭日图数据API
    
    Returns:
        JSON: 包含优惠券套餐销售贡献数据
    """
    try:
        # 从请求中获取日期参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 如果没有提供日期参数，则使用默认的最近90天
        if not start_date or not end_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 查询优惠券套餐数据，根据日期限制销售统计
        # 使用coupons表而不是coupon_usage表
        packages_query = """
        SELECT 
            cp.id, 
            cp.name, 
            cp.price, 
            cp.original_price, 
            COUNT(c.coupon_id) as sale_count
        FROM 
            coupon_packages cp
            LEFT JOIN coupons c ON cp.id = c.source_id 
                AND c.source = '套餐购买'
                AND c.receive_time BETWEEN %s AND %s
        WHERE 
            cp.status = 1
        GROUP BY
            cp.id, cp.name, cp.price, cp.original_price
        """
        
        packages_data = BaseDAO.execute_query(packages_query, (f"{start_date} 00:00:00", f"{end_date} 23:59:59"))
        
        if not packages_data:
            raise Exception("未找到优惠券套餐数据")
        
        # 构建旭日图数据
        sunburst_data = []
        
        # 添加中心节点
        root_node = {
            'name': '优惠券套餐总销售',
            'value': 0,
            'itemStyle': {'color': '#5470c6'},
            'children': []
        }
        sunburst_data.append(root_node)
        
        # 按套餐类型分类
        packages_by_category = {}
        
        # 添加套餐节点
        for package in packages_data:
            package_id = package['id']
            package_name = package['name']
            package_price = float(package['price'])
            sales_count = int(package['sale_count'])
            sales_value = package_price * sales_count
            
            # 如果销售额为0，跳过
            if sales_value <= 0:
                continue
            
            # 累加到总销售额
            root_node['value'] += sales_value
            
            # 确定套餐类别（根据名称关键词来分类）
            category = '其他套餐'
            if '新用户' in package_name or '新人' in package_name:
                category = '新用户套餐'
            elif '商务' in package_name or '高级' in package_name or '精英' in package_name:
                category = '商务套餐'
            elif '经济' in package_name or '实惠' in package_name or '基础' in package_name:
                category = '经济套餐'
            elif '家庭' in package_name or '亲子' in package_name:
                category = '家庭套餐'
            
            # 将套餐归类到相应类别
            if category not in packages_by_category:
                packages_by_category[category] = {
                    'name': category,
                    'value': 0,
                    'itemStyle': {'color': get_category_color(category)},
                    'children': []
                }
            
            # 累加到类别销售额
            packages_by_category[category]['value'] += sales_value
            
            # 创建套餐节点
            package_node = {
                'name': package_name,
                'value': sales_value,
                'itemStyle': {'color': get_package_color(category, package_name)}
            }
            
            # 添加套餐节点到类别节点
            packages_by_category[category]['children'].append(package_node)
        
        # 将类别节点添加到根节点
        for category, category_data in packages_by_category.items():
            root_node['children'].append(category_data)
        
        # 返回结果
        return jsonify(sunburst_data)
    
    except Exception as e:
        print(f"获取优惠券套餐销售贡献数据失败: {str(e)}")
        # 返回服务器错误状态码
        return jsonify({
            'error': '获取数据失败',
            'message': str(e)
        }), 500

# 根据类别获取颜色
def get_category_color(category):
    color_map = {
        '新用户套餐': '#91cc75',
        '商务套餐': '#5470c6',
        '经济套餐': '#fac858',
        '家庭套餐': '#ee6666',
        '其他套餐': '#73c0de'
    }
    return color_map.get(category, '#73c0de')

# 根据套餐名称获取颜色
def get_package_color(category, package_name):
    base_color = get_category_color(category)
    # 生成与类别相似但略有不同的颜色
    r = int(base_color[1:3], 16)
    g = int(base_color[3:5], 16)
    b = int(base_color[5:7], 16)
    
    # 使用套餐名称的hash值稍微调整颜色
    name_hash = hash(package_name) % 50 - 25
    
    r = max(0, min(255, r + name_hash))
    g = max(0, min(255, g + name_hash))
    b = max(0, min(255, b + name_hash))
    
    return f'#{r:02x}{g:02x}{b:02x}'
