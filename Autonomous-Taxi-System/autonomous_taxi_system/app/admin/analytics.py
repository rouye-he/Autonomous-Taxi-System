from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.dao.vehicle_dao import VehicleDAO
from app.dao.user_dao import UserDAO
from app.dao.order_dao import OrderDAO
from app.dao.base_dao import BaseDAO
from datetime import datetime, timedelta
import traceback
import json
from decimal import Decimal
from app.admin.vehicle_statistics import calculate_statistics, get_mileage_distribution, get_model_rankings
from app.admin.battery_analytics import (
    get_charging_stations_utilization, 
    get_battery_level_distribution,
    get_charging_peak_hours,
    get_battery_level_map,
    get_city_charging_demand_capacity,
    get_battery_data_for_chart
)
from app.admin.vehicle_maintenance_analytics import (
    get_maintenance_status_data,
    get_upcoming_maintenance_data,
    get_maintenance_frequency_by_model,
    get_maintenance_cost_breakdown,
    get_maintenance_trend_data,
    get_model_maintenance_remaining_time,
    get_model_maintenance_frequency,
    get_vehicle_age_maintenance_relation,
    get_vehicle_age_distribution
)
from app.admin.financial_health import financial_health_bp

# 创建蓝图
analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

# 注册financial_health_bp作为子蓝图
analytics_bp.register_blueprint(financial_health_bp)

# 添加Decimal序列化处理函数
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def get_date_range(request):
    """根据请求参数获取日期范围
    
    Args:
        request: Flask请求对象
        
    Returns:
        tuple: (start_date, end_date) 日期对象
    """
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
            # 设置结束日期为当天的23:59:59
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            # 日期格式错误时使用默认值
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
        # last_30_days 是默认值，已经在前面设置了
    
    return start_date, end_date

@analytics_bp.route('/')
def index():
    """数据分析主页 - 重定向到充电和电池管理页面"""
    try:
        # 获取查询参数
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        date_range = request.args.get('date_range', 'last_30_days')
        
        # 重定向到充电和电池管理页面，保留日期参数
        return redirect(url_for('analytics.charging_battery', 
                                start_date=start_date, 
                                end_date=end_date, 
                                date_range=date_range))
    except Exception as e:
        print(f"重定向到充电和电池管理页面失败: {str(e)}")
        traceback.print_exc()
        # 如果重定向失败，尝试直接渲染页面
        return redirect(url_for('analytics.charging_battery'))

@analytics_bp.route('/finance_statistics')
def finance_statistics():
    """财务统计页面 - 重定向到finance蓝图的index页面"""
    # 获取查询参数中的月份,如果有的话一并传递过去
    selected_month = request.args.get('month')
    if selected_month:
        return redirect(url_for('finance.index', month=selected_month))
    return redirect(url_for('finance.index'))

@analytics_bp.route('/vehicle_statistics')
def vehicle_statistics():
    """车辆统计页面 - 重定向到vehicles蓝图的data_analysis页面"""
    try:
        return redirect(url_for('vehicles.data_analysis'))
    except Exception as e:
        print(f"重定向到车辆统计页面失败: {str(e)}")
        return redirect(url_for('analytics.index'))

@analytics_bp.route('/user_statistics')
def user_statistics():
    """用户统计页面 - 重定向到users蓝图的analytics页面"""
    try:
        return redirect(url_for('users.analytics'))
    except Exception as e:
        print(f"重定向到用户统计页面失败: {str(e)}")
        return redirect(url_for('analytics.index'))

# 新增的路由
@analytics_bp.route('/vehicle_efficiency')
def vehicle_efficiency():
    """车辆运营效率页面"""
    try:
        # 获取日期范围
        start_date, end_date = get_date_range(request)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 计算日期范围天数
        days_in_range = (end_date - start_date).days + 1
        
        # 获取可用车辆数
        vehicle_query = """
        SELECT COUNT(*) as total_vehicles
        FROM vehicles
        WHERE is_available = 1
        """
        vehicle_result = BaseDAO.execute_query(vehicle_query)
        total_vehicles = float(vehicle_result[0]['total_vehicles'] if vehicle_result else 0)
        
        # 单车每日收益
        income_query = """
        SELECT COALESCE(SUM(amount), 0) as total_income
        FROM income
        WHERE date BETWEEN %s AND %s
        """
        income_result = BaseDAO.execute_query(income_query, (start_date_str, end_date_str))
        total_income = float(income_result[0]['total_income'] if income_result else 0)
        
        daily_income_per_vehicle = round(total_income / total_vehicles / days_in_range, 2) if total_vehicles > 0 else 0
        
        # 车辆周转率 - 修改为在所选日期范围内的订单数据，并考虑日期范围
        orders_query = """
        SELECT COUNT(*) as total_orders
        FROM orders
        WHERE create_time BETWEEN %s AND %s
        AND order_status = '已结束'
        """
        orders_result = BaseDAO.execute_query(orders_query, (start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S')))
        total_orders = float(orders_result[0]['total_orders'] if orders_result else 0)
        
        # 计算车辆周转率 - 单车日均完成订单数（单/车/天）
        vehicle_turnover_rate = round(total_orders / total_vehicles / days_in_range, 2) if total_vehicles > 0 else 0
        
        # 车辆日均行驶里程
        mileage_query = """
        SELECT COALESCE(SUM(distance), 0) as total_distance
        FROM order_details
        WHERE created_at BETWEEN %s AND %s
        """
        mileage_result = BaseDAO.execute_query(mileage_query, (start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S')))
        total_mileage = float(mileage_result[0]['total_distance'] if mileage_result else 0)
        
        daily_mileage_per_vehicle = round(total_mileage / total_vehicles / days_in_range, 2) if total_vehicles > 0 else 0
        
        # 获取图表数据
        # 1. 车辆日均行驶里程分布
        mileage_distribution_data = get_mileage_distribution(start_date, end_date, days_in_range)
        
        # 2. 各车型累计完成订单数和里程排名
        model_rankings = get_model_rankings(start_date, end_date)
        model_labels = model_rankings['model_labels']
        model_orders_data = model_rankings['model_orders_data']
        model_mileage_data = model_rankings['model_mileage_data']
        
        # 返回模板 - 传递日期范围参数和图表数据
        return render_template('analytics/operational-efficiency.html', 
                              daily_income_per_vehicle=daily_income_per_vehicle,
                              vehicle_turnover_rate=vehicle_turnover_rate,
                              daily_mileage_per_vehicle=daily_mileage_per_vehicle,
                              mileage_distribution_data=json.dumps(mileage_distribution_data, default=decimal_default),
                              model_labels=json.dumps(model_labels, default=decimal_default),
                              model_orders_data=json.dumps(model_orders_data, default=decimal_default),
                              model_mileage_data=json.dumps(model_mileage_data, default=decimal_default),
                              start_date=start_date.strftime('%Y-%m-%d'),
                              end_date=end_date.strftime('%Y-%m-%d'),
                              date_range=request.args.get('date_range', 'last_30_days'))
    except Exception as e:
        print(f"获取车辆运营效率数据失败: {str(e)}")
        traceback.print_exc()
        return redirect(url_for('analytics.index'))

@analytics_bp.route('/charging_battery')
def charging_battery():
    """充电和电池管理页面"""
    try:
        # 获取日期范围
        start_date, end_date = get_date_range(request)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 获取可用车辆数
        vehicle_query = """
        SELECT COUNT(*) as total_vehicles
        FROM vehicles
        WHERE is_available = 1
        """
        vehicle_result = BaseDAO.execute_query(vehicle_query)
        total_vehicles = float(vehicle_result[0]['total_vehicles'] if vehicle_result else 0)
        
        # 获取总车费收入（从order_details表计算）
        income_query = """
        SELECT COALESCE(SUM(amount), 0) as total_income
        FROM order_details
        WHERE created_at BETWEEN %s AND %s
        """
        income_result = BaseDAO.execute_query(income_query, (start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S')))
        total_income = float(income_result[0]['total_income'] if income_result else 0)
        
        # 获取充电站支出（充电费用）
        charging_expense_query = """
        SELECT COALESCE(SUM(amount), 0) as total_charging_expense
        FROM expense
        WHERE type = '充电站支出'
        AND date BETWEEN %s AND %s
        """
        charging_expense_result = BaseDAO.execute_query(charging_expense_query, (start_date_str, end_date_str))
        total_charging_expense = float(charging_expense_result[0]['total_charging_expense'] if charging_expense_result else 0)
        
        # 计算车费充电费比值（电池利用效率）
        battery_usage_efficiency = round(total_income / total_charging_expense, 2) if total_charging_expense > 0 else 0
        
        # 车辆日均充电次数 - 修改为从expense表统计充电次数（金额小于1万的充电站支出）
        charging_query = """
        SELECT COUNT(*) as total_charging
        FROM expense
        WHERE type = '充电站支出'
        AND amount < 10000
        AND date BETWEEN %s AND %s
        """
        charging_result = BaseDAO.execute_query(charging_query, (start_date_str, end_date_str))
        total_charging = float(charging_result[0]['total_charging'] if charging_result else 0)
        
        # 计算日期范围天数
        days_in_range = (end_date - start_date).days + 1
        
        # 计算日均充电次数 - 避免除以0的情况
        if total_vehicles > 0:
            daily_charging_per_vehicle = round(total_charging / total_vehicles / days_in_range, 2)
        else:
            daily_charging_per_vehicle = 0
            
        # 获取充电站利用率数据
        charging_stations_data = get_charging_stations_utilization()
        
        # 获取电池电量分布数据
        battery_distribution = get_battery_level_distribution()
        
        # 获取充电高峰时段热力图数据 - 传递日期范围参数
        charging_peak_hours = get_charging_peak_hours(start_date, end_date)
        
        # 获取车辆平均电量地理位置热点图数据
        battery_map_data = get_battery_level_map()
        
        # 获取各城市充电需求与容量对比数据
        city_charging_data = get_city_charging_demand_capacity()
        
        # 记录数据返回大小，帮助调试
        print(f"充电站数据数量: {len(charging_stations_data)}")
        print(f"日期范围: {start_date_str} 至 {end_date_str}, 共{days_in_range}天")
        print(f"充电高峰热力图总充电次数: {charging_peak_hours.get('total_charging', 0)}")
        
        return render_template('analytics/battery-management.html',
                             battery_usage_efficiency=battery_usage_efficiency,
                             daily_charging_per_vehicle=daily_charging_per_vehicle,
                             charging_stations_data=json.dumps(charging_stations_data, default=decimal_default),
                             battery_distribution=json.dumps(battery_distribution, default=decimal_default),
                             charging_peak_hours=json.dumps(charging_peak_hours, default=decimal_default),
                             battery_map_data=json.dumps(battery_map_data, default=decimal_default),
                             city_charging_data=json.dumps(city_charging_data, default=decimal_default),
                             start_date=start_date.strftime('%Y-%m-%d'),
                             end_date=end_date.strftime('%Y-%m-%d'),
                             date_range=request.args.get('date_range', 'last_30_days'))
    except Exception as e:
        print(f"获取充电和电池管理数据失败: {str(e)}")
        traceback.print_exc()
        return redirect(url_for('analytics.index'))

@analytics_bp.route('/vehicle_maintenance')
def vehicle_maintenance():
    """车辆维护页面"""
    try:
        # 获取日期范围
        start_date, end_date = get_date_range(request)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 获取可用车辆数
        vehicle_query = """
        SELECT COUNT(*) as total_vehicles
        FROM vehicles
        WHERE is_available = 1
        """
        vehicle_result = BaseDAO.execute_query(vehicle_query)
        total_vehicles = float(vehicle_result[0]['total_vehicles'] if vehicle_result else 0)
        
        # 车辆维护频率
        maintenance_query = """
        SELECT COUNT(*) as total_maintenance
        FROM vehicle_logs
        WHERE log_type = '维护记录'
        AND created_at BETWEEN %s AND %s
        """
        maintenance_result = BaseDAO.execute_query(maintenance_query, (start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S')))
        total_maintenance = float(maintenance_result[0]['total_maintenance'] if maintenance_result else 0)
        
        maintenance_frequency = round(total_maintenance / total_vehicles, 2) if total_vehicles > 0 else 0
        
        # 维护成本占比
        maintenance_expense_query = """
        SELECT COALESCE(SUM(amount), 0) as maintenance_expense
        FROM expense
        WHERE type = '车辆支出'
        AND date BETWEEN %s AND %s
        """
        maintenance_expense_result = BaseDAO.execute_query(maintenance_expense_query, (start_date_str, end_date_str))
        maintenance_expense = float(maintenance_expense_result[0]['maintenance_expense'] if maintenance_expense_result else 0)
        
        # 获取总运营支出
        total_expense_query = """
        SELECT COALESCE(SUM(amount), 0) as total_expense
        FROM expense
        WHERE date BETWEEN %s AND %s
        """
        total_expense_result = BaseDAO.execute_query(total_expense_query, (start_date_str, end_date_str))
        total_expense = float(total_expense_result[0]['total_expense'] if total_expense_result else 0)
        
        maintenance_cost_ratio = round(maintenance_expense / total_expense * 100, 1) if total_expense > 0 else 0
        
        # 获取维护状态数据
        maintenance_status_data = get_maintenance_status_data()
        
        # 获取即将到期维护车辆时间分布数据
        upcoming_maintenance_data = get_upcoming_maintenance_data()
        
        # 获取各车型距离维护剩余时间的平均值
        model_remaining_time_data = get_model_maintenance_remaining_time()
        
        # 获取各车型平均每车维护次数（每两条记录算一次完整维护）
        model_maintenance_frequency_data = get_model_maintenance_frequency()
        
        # 获取车辆年龄分布数据
        vehicle_age_distribution_data = get_vehicle_age_distribution()
        
        # 获取维护成本分类数据
        maintenance_cost_data = get_maintenance_cost_breakdown()
        
        # 获取维护趋势数据
        maintenance_trend_data = get_maintenance_trend_data()
        
        return render_template('analytics/vehicle-maintenance.html',
                              maintenance_frequency=maintenance_frequency,
                              maintenance_cost_ratio=maintenance_cost_ratio,
                              maintenance_status_data=json.dumps(maintenance_status_data, default=decimal_default),
                              upcoming_maintenance_data=json.dumps(upcoming_maintenance_data, default=decimal_default),
                              model_remaining_time_data=json.dumps(model_remaining_time_data, default=decimal_default),
                              model_maintenance_frequency_data=json.dumps(model_maintenance_frequency_data, default=decimal_default),
                              vehicle_age_distribution_data=json.dumps(vehicle_age_distribution_data, default=decimal_default),
                              maintenance_cost_data=json.dumps(maintenance_cost_data, default=decimal_default),
                              maintenance_trend_data=json.dumps(maintenance_trend_data, default=decimal_default),
                              start_date=start_date.strftime('%Y-%m-%d'),
                              end_date=end_date.strftime('%Y-%m-%d'),
                              date_range=request.args.get('date_range', 'last_30_days'))
    except Exception as e:
        print(f"获取车辆维护数据失败: {str(e)}")
        traceback.print_exc()
        return redirect(url_for('analytics.index'))

@analytics_bp.route('/order_service')
def order_service():
    """订单服务质量分析页面"""
    try:
        # 获取日期范围
        start_date, end_date = get_date_range(request)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 平均订单完成率 - 直接从orders表查询
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
            end_date.strftime('%Y-%m-%d 23:59:59')
        ))
        completion_rate = round(float(completion_rate_result[0]['completion_rate'] if completion_rate_result and completion_rate_result[0]['completion_rate'] else 0), 1)
        
        # 订单完成时长(分钟) - 只考虑已结束的订单
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
            end_date.strftime('%Y-%m-%d 23:59:59')
        ))
        avg_duration = round(float(duration_result[0]['avg_duration'] if duration_result and duration_result[0]['avg_duration'] else 0), 1)
        
        # 平均订单金额
        avg_amount_query = """
        SELECT AVG(amount) as avg_amount 
        FROM order_details 
        WHERE created_at BETWEEN %s AND %s
        """
        amount_result = BaseDAO.execute_query(avg_amount_query, (
            start_date.strftime('%Y-%m-%d %H:%M:%S'), 
            end_date.strftime('%Y-%m-%d 23:59:59')
        ))
        avg_amount = round(float(amount_result[0]['avg_amount'] if amount_result and amount_result[0]['avg_amount'] else 0), 2)
        
        # 每日完成率数据
        daily_completion_query = """
        SELECT 
            DATE_FORMAT(create_time, '%%Y-%%m-%%d') as date,
            COALESCE(
                SUM(CASE WHEN order_status = '已结束' THEN 1 ELSE 0 END) / 
                NULLIF(COUNT(*), 0) * 100,
                0
            ) as completion_rate
        FROM orders
        WHERE create_time BETWEEN %s AND %s
        GROUP BY DATE_FORMAT(create_time, '%%Y-%%m-%%d')
        ORDER BY date
        """
        daily_completion_data = BaseDAO.execute_query(daily_completion_query, (
            start_date.strftime('%Y-%m-%d %H:%M:%S'), 
            end_date.strftime('%Y-%m-%d 23:59:59')
        ))
        
        dates = [item['date'] for item in daily_completion_data]
        completion_rates = [float(item['completion_rate']) for item in daily_completion_data]
        
        chart_data = {
            'labels': dates,
            'datasets': [{
                'label': '每日完成率 (%)',
                'data': completion_rates,
                'borderColor': 'rgba(75, 192, 192, 1)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'tension': 0.1
            }]
        }
        
        return render_template('analytics/service-quality.html', 
                              avg_duration=avg_duration,
                              avg_amount=avg_amount,
                              completion_rate=completion_rate,
                              chart_data=json.dumps(chart_data, default=decimal_default),
                              start_date=start_date.strftime('%Y-%m-%d'),
                              end_date=end_date.strftime('%Y-%m-%d'),
                              date_range=request.args.get('date_range', 'last_30_days'))
    except Exception as e:
        print(f"获取订单服务数据失败: {str(e)}")
        traceback.print_exc()
        return redirect(url_for('analytics.index'))

@analytics_bp.route('/user_marketing')
def user_marketing():
    """用户行为和营销页面"""
    try:
        # 获取日期范围
        start_date, end_date = get_date_range(request)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 获取总订单数
        orders_query = """
        SELECT COUNT(*) as total_orders
        FROM orders
        WHERE create_time BETWEEN %s AND %s
        """
        orders_result = BaseDAO.execute_query(orders_query, (start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S')))
        total_orders = float(orders_result[0]['total_orders'] if orders_result else 0)
        
        # 获取总收入
        income_query = """
        SELECT COALESCE(SUM(amount), 0) as total_income
        FROM income
        WHERE date BETWEEN %s AND %s
        """
        income_result = BaseDAO.execute_query(income_query, (start_date_str, end_date_str))
        total_income = float(income_result[0]['total_income'] if income_result else 0)
        
        # 用户重复使用率
        repeat_users_query = """
        SELECT 
            COUNT(DISTINCT user_id) as total_users,
            COUNT(DISTINCT CASE WHEN order_count >= 2 THEN user_id END) as repeat_users
        FROM (
            SELECT user_id, COUNT(*) as order_count
            FROM orders
            WHERE create_time BETWEEN %s AND %s
            GROUP BY user_id
        ) as user_orders
        """
        repeat_users_result = BaseDAO.execute_query(repeat_users_query, (start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S')))
        
        total_users = float(repeat_users_result[0]['total_users'] if repeat_users_result else 0)
        repeat_users = float(repeat_users_result[0]['repeat_users'] if repeat_users_result else 0)
        
        repeat_usage_rate = round(repeat_users / total_users * 100, 1) if total_users > 0 else 0
        
        # 优惠券投资回报率
        coupon_roi_query = """
        SELECT 
            COALESCE(SUM(i.amount), 0) as coupon_order_income,
            COUNT(DISTINCT c.coupon_id) * AVG(ct.value) as coupon_cost
        FROM 
            orders o
            JOIN income i ON o.order_number = i.order_id
            JOIN coupons c ON o.order_id = c.order_id
            JOIN coupon_types ct ON c.coupon_type_id = ct.id
        WHERE 
            o.create_time BETWEEN %s AND %s
            AND c.status = '已使用'
        """
        coupon_roi_result = BaseDAO.execute_query(coupon_roi_query, (start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S')))
        
        coupon_order_income = float(coupon_roi_result[0]['coupon_order_income'] if coupon_roi_result and coupon_roi_result[0]['coupon_order_income'] else 0)
        coupon_cost = float(coupon_roi_result[0]['coupon_cost'] if coupon_roi_result and coupon_roi_result[0]['coupon_cost'] else 0)
        
        coupon_roi = round((coupon_order_income - coupon_cost) / coupon_cost * 100, 1) if coupon_cost > 0 else 0
        
        # 新用户转化率 - 直接查询新用户和下单新用户数
        new_user_conversion_query = """
        SELECT
            COUNT(DISTINCT u.user_id) AS new_users,
            COUNT(DISTINCT CASE WHEN o.user_id IS NOT NULL THEN u.user_id END) AS converted_users
        FROM
            users u
            LEFT JOIN (
                SELECT DISTINCT user_id
                FROM orders
                WHERE create_time BETWEEN %s AND %s
            ) o ON u.user_id = o.user_id
        WHERE
            u.registration_time BETWEEN %s AND %s
        """
        conversion_result = BaseDAO.execute_query(new_user_conversion_query, (
            start_date.strftime('%Y-%m-%d %H:%M:%S'), 
            end_date.strftime('%Y-%m-%d 23:59:59'),
            start_date.strftime('%Y-%m-%d %H:%M:%S'), 
            end_date.strftime('%Y-%m-%d 23:59:59')
        ))
        
        if conversion_result and conversion_result[0]:
            new_users = float(conversion_result[0]['new_users'] if conversion_result[0]['new_users'] else 0)
            converted_users = float(conversion_result[0]['converted_users'] if conversion_result[0]['converted_users'] else 0)
            new_user_conversion = round(converted_users / new_users * 100, 1) if new_users > 0 else 0
        else:
            new_user_conversion = 0
        
        # 客单价
        customer_unit_price = round(total_income / total_orders, 2) if total_orders > 0 else 0
        
        # 提供额外数据，为下一步的图表准备
        # 这些数据会在前端通过AJAX请求获取，所以这里不需要直接传递
        
        return render_template('analytics/user-marketing.html',
                             repeat_usage_rate=repeat_usage_rate,
                             coupon_roi=coupon_roi,
                             new_user_conversion=new_user_conversion,
                             customer_unit_price=customer_unit_price,
                             start_date=start_date.strftime('%Y-%m-%d'),
                             end_date=end_date.strftime('%Y-%m-%d'),
                             date_range=request.args.get('date_range', 'last_30_days'))
    except Exception as e:
        print(f"获取用户行为和营销数据失败: {str(e)}")
        traceback.print_exc()
        return redirect(url_for('analytics.index'))

@analytics_bp.route('/finance_health')
def finance_health():
    """财务和整体健康页面"""
    try:
        # 获取日期范围
        start_date, end_date = get_date_range(request)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 计算日期范围天数
        days_in_range = (end_date - start_date).days + 1
        
        # 获取总收入
        income_query = """
        SELECT COALESCE(SUM(amount), 0) as total_income
        FROM income
        WHERE date BETWEEN %s AND %s
        """
        income_result = BaseDAO.execute_query(income_query, (start_date_str, end_date_str))
        total_income = float(income_result[0]['total_income'] if income_result else 0)
        
        # 获取总支出
        total_expense_query = """
        SELECT COALESCE(SUM(amount), 0) as total_expense
        FROM expense
        WHERE date BETWEEN %s AND %s
        """
        total_expense_result = BaseDAO.execute_query(total_expense_query, (start_date_str, end_date_str))
        total_expense = float(total_expense_result[0]['total_expense'] if total_expense_result else 0)
        
        # 运营利润率
        operating_profit = total_income - total_expense
        operating_profit_margin = round(operating_profit / total_income * 100, 1) if total_income > 0 else 0
        
        # 平均车辆投资回报期 - 修正计算方法
        # 获取车辆支出总额
        vehicle_expense_query = """
        SELECT COALESCE(SUM(amount), 0) as vehicle_expense
        FROM expense
        WHERE type = '车辆支出'
        """
        vehicle_expense_result = BaseDAO.execute_query(vehicle_expense_query)
        total_vehicle_expense = float(vehicle_expense_result[0]['vehicle_expense'] if vehicle_expense_result and vehicle_expense_result[0]['vehicle_expense'] else 0)
        
        # 计算日均收入
        daily_income = total_income / days_in_range if days_in_range > 0 else 0
        
        # 计算车辆投资回报期(天)
        vehicle_roi_period = round(total_vehicle_expense / daily_income) if daily_income > 0 else 0
        
        # 车队平均车龄
        fleet_age_query = """
        SELECT AVG(TIMESTAMPDIFF(MONTH, registration_date, CURDATE())) as avg_age
        FROM vehicles
        """
        fleet_age_result = BaseDAO.execute_query(fleet_age_query)
        fleet_average_age = float(fleet_age_result[0]['avg_age'] if fleet_age_result and fleet_age_result[0]['avg_age'] else 0)
        fleet_average_age = round(fleet_average_age, 1)
        
        # 系统预警率
        warnings_query = """
        SELECT COUNT(*) as warning_count
        FROM system_notifications
        WHERE priority = '警告'
        AND created_at BETWEEN %s AND %s
        """
        warnings_result = BaseDAO.execute_query(warnings_query, (start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S')))
        total_warnings = float(warnings_result[0]['warning_count'] if warnings_result else 0)
        
        system_warning_rate = round(total_warnings / days_in_range, 1)
        
        return render_template('analytics/financial-health.html',
                             operating_profit_margin=operating_profit_margin,
                             vehicle_roi_period=vehicle_roi_period,
                             fleet_average_age=fleet_average_age,
                             system_warning_rate=system_warning_rate,
                             start_date=start_date.strftime('%Y-%m-%d'),
                             end_date=end_date.strftime('%Y-%m-%d'),
                             date_range=request.args.get('date_range', 'last_30_days'))
    except Exception as e:
        print(f"获取财务和整体健康数据失败: {str(e)}")
        traceback.print_exc()
        return redirect(url_for('analytics.index'))

@analytics_bp.route('/vehicle-operation')
def vehicle_operation():
    return render_template('analytics/vehicle-operation.html')

@analytics_bp.route('/customer-behavior')
def customer_behavior():
    return render_template('analytics/customer-behavior.html')

@analytics_bp.route('/financial-metrics')
def financial_metrics():
    return render_template('analytics/financial-metrics.html')

# 辅助函数：获取各城市平均订单完成时长数据
def get_city_order_duration_data():
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
    GROUP BY 
        o.city_code
    ORDER BY 
        avg_duration ASC
    """
    
    # 执行查询
    from app.extensions import mysql
    cursor = mysql.connection.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    
    # 城市列表 - 按照数据库中的城市代码顺序
    cities = []
    durations = []
    
    # 处理查询结果
    for row in results:
        cities.append(row[0])  # 城市名称
        durations.append(round(float(row[1]), 1))  # 平均时长（四舍五入到1位小数）
    
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

# 添加service_quality路由
@analytics_bp.route('/service_quality')
def service_quality():
    """服务质量分析页面 - 重定向到admin.order_analysis.service_quality路由"""
    # 获取查询参数
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    date_range = request.args.get('date_range', 'last_30_days')
    
    # 重定向到order_analysis蓝图的service_quality路由
    return redirect(url_for('admin.order_analysis.service_quality', 
                           start_date=start_date, 
                           end_date=end_date, 
                           date_range=date_range))

@analytics_bp.route('/financial-risk-data')
def financial_risk_data():
    """获取财务健康风险评估数据"""
    try:
        # 实际项目中应该从数据库获取数据
        # 流动性比率、资产负债率、营业利润率、投资回报率、现金流量比、成本效率
        current_data = [7.8, 6.2, 8.1, 6.9, 5.5, 7.2]
        target_data = [9.0, 8.0, 9.5, 8.5, 8.0, 9.0]
        
        # 记录日志
        current_app.logger.info("财务健康风险数据已获取")
        
        return jsonify({
            "code": 200,
            "message": "success",
            "current": current_data,
            "target": target_data
        })
    except Exception as e:
        current_app.logger.error(f"获取财务健康风险数据失败: {str(e)}")
        return jsonify({
            "code": 500,
            "message": f"获取数据失败: {str(e)}"
        }), 500

@analytics_bp.route('/battery-data')
def battery_data():
    """获取电池管理页面图表数据的API端点"""
    try:
        chart_id = request.args.get('chart')
        if not chart_id:
            return jsonify({"error": "缺少chart参数"}), 400
            
        # 获取数据
        data = get_battery_data_for_chart(chart_id)
        
        # 返回JSON响应
        return jsonify(data)
    except Exception as e:
        print(f"获取电池数据API失败: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500 