from flask import Blueprint, render_template
from datetime import datetime, date, timedelta
import pymysql
from app.config.database import db_config
from app.models.vehicle import Vehicle
from app.models.order import Order
from app.extensions import db

# 创建蓝图
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = pymysql.connect(**db_config)
        return conn
    except Exception as e:
        print("数据库连接失败:", e)
        raise

def get_vehicle_stats(connection, today, yesterday):
    """获取车辆统计数据"""
    stats = {
        'total_vehicles': 0,
        'running_vehicles': 0, 
        'running_vehicles_percent_change': 0
    }
    
    try:
        with connection.cursor() as cursor:
            # 总车辆数
            cursor.execute("SELECT COUNT(*) FROM vehicles")
            stats['total_vehicles'] = cursor.fetchone()[0]
            print("总车辆数:", stats['total_vehicles'])
            
            # 运行中车辆数
            cursor.execute("SELECT COUNT(*) FROM vehicles WHERE current_status = '运行中'")
            stats['running_vehicles'] = cursor.fetchone()[0]
            print("运行中车辆数:", stats['running_vehicles'])
            
            # 昨日运行中车辆数（为了计算百分比变化）
            cursor.execute(
                "SELECT COUNT(*) FROM vehicle_logs WHERE log_type = '状态变更' "
                "AND log_content LIKE '%到\"运行中\"%' AND DATE(created_at) = %s", 
                (yesterday,)
            )
            yesterday_running = cursor.fetchone()[0]
            if yesterday_running > 0:
                stats['running_vehicles_percent_change'] = round(
                    ((stats['running_vehicles'] - yesterday_running) / yesterday_running) * 100
                )
            print("昨日运行中车辆数:", yesterday_running, "变化百分比:", stats['running_vehicles_percent_change'], "%")
    except Exception as e:
        print("获取车辆统计失败:", repr(e))
    
    return stats

def get_order_stats(connection, today, yesterday):
    """获取订单统计数据"""
    stats = {
        'today_orders': 0,
        'today_orders_percent_change': 0
    }
    
    try:
        # 检查order_details表
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'order_details'")
            if not cursor.fetchone():
                print("错误: order_details表不存在!")
                return stats
                
            # 检查表结构
            cursor.execute("DESCRIBE order_details")
            columns = [col[0] for col in cursor.fetchall()]
            print("order_details表字段:", columns)
            
            # 检查是否有created_at字段
            if 'created_at' not in columns:
                print("错误: order_details表没有created_at字段!")
                return stats
        
        # 尝试方法1: 使用DATE函数
        try:
            with connection.cursor() as cursor:
                # 今日完成订单数
                sql = "SELECT COUNT(*) FROM order_details WHERE DATE(created_at) = %s"
                print("执行SQL:", sql, "参数:", today)
                cursor.execute(sql, (today,))
                result = cursor.fetchone()
                print("今日订单查询结果:", result)
                
                if result and result[0] is not None:
                    stats['today_orders'] = result[0]
                
                # 昨日订单数
                cursor.execute(sql, (yesterday,))
                result = cursor.fetchone()
                print("昨日订单查询结果:", result)
                
                yesterday_orders = result[0] if result and result[0] is not None else 0
                    
                if yesterday_orders > 0:
                    stats['today_orders_percent_change'] = round(
                        ((stats['today_orders'] - yesterday_orders) / yesterday_orders) * 100
                    )
                
                print("方法1 - 今日订单数:", stats['today_orders'], "昨日订单数:", yesterday_orders)
        except Exception as e:
            print("方法1获取订单统计失败:", repr(e))
        
        # 如果方法1返回0，尝试方法2: 使用时间范围
        if stats['today_orders'] == 0:
            try:
                with connection.cursor() as cursor:
                    sql = "SELECT COUNT(*) FROM order_details WHERE created_at >= %s AND created_at < %s"
                    print("执行SQL:", sql, "参数:", today+" 00:00:00", today+" 23:59:59")
                    cursor.execute(sql, (today+" 00:00:00", today+" 23:59:59"))
                    result = cursor.fetchone()
                    print("方法2 - 今日订单查询结果:", result)
                    
                    if result and result[0] is not None and result[0] > 0:
                        stats['today_orders'] = result[0]
                        print("使用方法2更新今日订单数:", stats['today_orders'])
            except Exception as e:
                print("方法2获取订单统计失败:", repr(e))
        
        # 如果还是0，检查最近记录
        if stats['today_orders'] == 0:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT created_at FROM order_details ORDER BY created_at DESC LIMIT 5")
                    recent_orders = cursor.fetchall()
                    print("最近的订单记录创建时间:", recent_orders)
            except Exception as e:
                print("获取最近订单记录失败:", repr(e))
    except Exception as e:
        print("获取订单统计失败:", repr(e))
    
    return stats

def get_income_stats(connection, today, yesterday):
    """获取收入统计数据"""
    stats = {
        'today_income': 0,
        'today_income_percent_change': 0
    }
    
    try:
        # 检查income表
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'income'")
            if not cursor.fetchone():
                print("错误: income表不存在!")
                return stats
                
            # 检查表结构
            cursor.execute("DESCRIBE income")
            columns = [col[0] for col in cursor.fetchall()]
            print("income表字段:", columns)
            
            # 检查是否有date字段
            if 'date' not in columns:
                print("错误: income表没有date字段!")
                return stats
        
        # 尝试方法1: 使用DATE函数
        try:
            with connection.cursor() as cursor:
                # 今日收入
                sql = "SELECT COALESCE(SUM(amount), 0) FROM income WHERE DATE(date) = %s"
                print("执行SQL:", sql, "参数:", today)
                cursor.execute(sql, (today,))
                result = cursor.fetchone()
                print("今日收入查询结果:", result)
                
                if result and result[0] is not None:
                    stats['today_income'] = float(result[0])
                
                # 昨日收入
                cursor.execute(sql, (yesterday,))
                result = cursor.fetchone()
                print("昨日收入查询结果:", result)
                
                yesterday_income = float(result[0]) if result and result[0] is not None else 0
                    
                if yesterday_income > 0:
                    stats['today_income_percent_change'] = round(
                        ((stats['today_income'] - yesterday_income) / yesterday_income) * 100
                    )
                
                print("方法1 - 今日收入:", stats['today_income'], "昨日收入:", yesterday_income)
        except Exception as e:
            print("方法1获取收入统计失败:", repr(e))
        
        # 如果方法1返回0，尝试方法2: 直接匹配日期
        if stats['today_income'] == 0:
            try:
                with connection.cursor() as cursor:
                    sql = "SELECT COALESCE(SUM(amount), 0) FROM income WHERE date = %s"
                    print("执行SQL:", sql, "参数:", today)
                    cursor.execute(sql, (today,))
                    result = cursor.fetchone()
                    print("方法2 - 今日收入查询结果:", result)
                    
                    if result and result[0] is not None and float(result[0]) > 0:
                        stats['today_income'] = float(result[0])
                        print("使用方法2更新今日收入:", stats['today_income'])
            except Exception as e:
                print("方法2获取收入统计失败:", repr(e))
        
        # 如果还是0，检查最近记录
        if stats['today_income'] == 0:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT date, amount FROM income ORDER BY date DESC LIMIT 5")
                    recent_income = cursor.fetchall()
            except Exception as e:
                print("获取最近收入记录失败:", repr(e))
    except Exception as e:
        print("获取收入统计失败:", repr(e))
    
    return stats

def get_active_users_stats(connection, today, yesterday):
    """获取活跃用户统计数据"""
    stats = {
        'active_users': 0,
        'active_users_percent_change': 0
    }
    
    try:
        # 尝试方法1: 使用DATE函数
        try:
            with connection.cursor() as cursor:
                # 今日活跃用户
                sql = "SELECT COUNT(DISTINCT user_id) FROM order_details WHERE DATE(created_at) = %s"
                print("执行SQL:", sql, "参数:", today)
                cursor.execute(sql, (today,))
                result = cursor.fetchone()
                
                if result and result[0] is not None:
                    stats['active_users'] = result[0]
                
                # 昨日活跃用户
                cursor.execute(sql, (yesterday,))
                result = cursor.fetchone()
                
                yesterday_active = result[0] if result and result[0] is not None else 0
                    
                if yesterday_active > 0:
                    stats['active_users_percent_change'] = round(
                        ((stats['active_users'] - yesterday_active) / yesterday_active) * 100
                    )
                
        except Exception as e:
            print("方法1获取活跃用户统计失败:", repr(e))
        
        # 如果方法1返回0，尝试方法2: 使用时间范围
        if stats['active_users'] == 0:
            try:
                with connection.cursor() as cursor:
                    sql = "SELECT COUNT(DISTINCT user_id) FROM order_details WHERE created_at >= %s AND created_at < %s"
        
                    cursor.execute(sql, (today+" 00:00:00", today+" 23:59:59"))
                    result = cursor.fetchone()
                    
                    if result and result[0] is not None and result[0] > 0:
                        stats['active_users'] = result[0]
      
            except Exception as e:
                print("方法2获取活跃用户统计失败:", repr(e))
    except Exception as e:
        print("获取活跃用户统计失败:", repr(e))
    
    return stats

def get_dashboard_stats():
    """获取仪表盘统计信息"""
    today = date.today().strftime('%Y-%m-%d')
    yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

    
    stats = {
        'running_vehicles': 0,
        'total_vehicles': 0,
        'running_vehicles_percent_change': 0,
        'today_orders': 0,
        'today_orders_percent_change': 0,
        'today_income': 0,
        'today_income_percent_change': 0,
        'active_users': 0,
        'active_users_percent_change': 0
    }
    
    connection = None
    try:
        connection = get_db_connection()
        
        # 1. 获取车辆统计
        vehicle_stats = get_vehicle_stats(connection, today, yesterday)
        stats.update(vehicle_stats)
        
        # 2. 获取订单统计
        order_stats = get_order_stats(connection, today, yesterday)
        stats.update(order_stats)
        
        # 3. 获取收入统计
        income_stats = get_income_stats(connection, today, yesterday)
        stats.update(income_stats)
        
        # 4. 获取活跃用户统计
        user_stats = get_active_users_stats(connection, today, yesterday)
        stats.update(user_stats)
        
    except Exception as e:
        print("获取仪表盘统计信息失败:", repr(e))
    finally:
        if connection:
            connection.close()
    
    print("最终统计结果:", stats)
    return stats

def get_model_finance_data():
    """获取按车型的财务数据"""
    model_data = {
        'models': [],      # 车辆型号
        'income': [],      # 每种车型的总收入
        'expense': [],     # 每种车型的总支出
        'profit_rate': []  # 每种车型的利润率
    }
    
    connection = None
    try:
        connection = get_db_connection()
        
        # 查询所有活跃车型
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT model FROM vehicles 
                WHERE is_available = 1
                ORDER BY model
            """)
            models = [row[0] for row in cursor.fetchall()]
            
            model_data['models'] = models
            
            # 对每个车型查询财务数据
            for model in models:
                # 查询该车型的总收入
                try:
                    cursor.execute("""
                        SELECT COALESCE(SUM(i.amount), 0) 
                        FROM income i
                        JOIN order_details od ON i.order_id = od.order_id
                        JOIN vehicles v ON od.vehicle_id = v.vehicle_id
                        WHERE v.model = %s AND 
                              i.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                    """, (model,))
                    income = cursor.fetchone()[0] or 0
                    model_data['income'].append(float(income))
                except Exception as e:
                    print("查询车型", model, "收入失败，可能是表结构问题:", repr(e))
                    # 不使用随机数据，保持为0
                    model_data['income'].append(0.0)
                
                # 查询该车型的总支出
                try:
                    cursor.execute("""
                        SELECT COALESCE(SUM(amount), 0)
                        FROM expense
                        WHERE vehicle_id IN (SELECT vehicle_id FROM vehicles WHERE model = %s)
                        AND date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                    """, (model,))
                    expense = cursor.fetchone()[0] or 0
                    model_data['expense'].append(float(expense))
                except Exception as e:
                    print("查询车型", model, "支出失败，可能是表结构问题:", repr(e))
                    # 不使用随机数据，保持为0
                    model_data['expense'].append(0.0)
                
                # 计算利润率
                income = model_data['income'][-1]
                expense = model_data['expense'][-1]
                profit = income - expense
                profit_rate = (profit / income * 100) if income > 0 else 0
                model_data['profit_rate'].append(round(profit_rate, 1))
                
    except Exception as e:
        print("获取车型财务数据失败:", repr(e))
    finally:
        if connection:
            connection.close()
    
    return model_data

def get_chart_data():
    """获取图表数据"""
    chart_data = {
        'avg_order_amount': {
            'labels': [],
            'data': []
        },
        'avg_orders_per_vehicle': {
            'labels': [],
            'data': []
        }
    }
    
    # 获取最近7天日期
    today = date.today()
    date_labels = [(today - timedelta(days=i)).strftime('%m-%d') for i in range(6, -1, -1)]
    chart_data['avg_order_amount']['labels'] = date_labels
    chart_data['avg_orders_per_vehicle']['labels'] = date_labels
    
    connection = None
    try:
        connection = get_db_connection()
        
        # 1. 获取每日平均订单金额
        with connection.cursor() as cursor:
            avg_amounts = []
            for i in range(6, -1, -1):
                target_date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
                cursor.execute(
                    "SELECT AVG(amount) FROM order_details WHERE DATE(created_at) = %s", 
                    (target_date,)
                )
                result = cursor.fetchone()[0]
                # 如果没有数据，使用0
                avg_amounts.append(round(float(result), 2) if result is not None else 0)
            chart_data['avg_order_amount']['data'] = avg_amounts
        
        # 2. 获取每辆车每天完成的平均订单数
        with connection.cursor() as cursor:
            # 获取车辆总数
            cursor.execute("SELECT COUNT(*) FROM vehicles")
            vehicle_count = cursor.fetchone()[0]
            if vehicle_count == 0:  # 避免除零错误
                vehicle_count = 1
            
            # 计算每天的订单数除以车辆总数
            avg_orders_per_vehicle = []
            for i in range(6, -1, -1):
                target_date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
                # 计算每日订单总数
                cursor.execute(
                    "SELECT COUNT(*) FROM order_details WHERE DATE(created_at) = %s", 
                    (target_date,)
                )
                order_count = cursor.fetchone()[0]
                
                # 计算平均每辆车的订单数
                avg = round(order_count / vehicle_count, 2) if order_count > 0 else 0
                avg_orders_per_vehicle.append(avg)
            
            chart_data['avg_orders_per_vehicle']['data'] = avg_orders_per_vehicle
    
    except Exception as e:
        print("获取图表数据失败:", repr(e))
    finally:
        if connection:
            connection.close()
    
    return chart_data

def get_system_warnings():
    """获取系统警告通知"""
    warnings = []
    
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 获取优先级为"警告"的通知，按创建时间降序排序，限制4条
            query = """
                SELECT id, title, content, type, priority, status, created_at
                FROM system_notifications 
                WHERE priority = '警告'
                ORDER BY created_at DESC
                LIMIT 4
            """
            cursor.execute(query)
            warnings = cursor.fetchall()
            
            # 格式化日期时间
            for warning in warnings:
                if warning['created_at']:
                    warning['created_at'] = warning['created_at'].strftime('%Y-%m-%d %H:%M')
    
    except Exception as e:
        print("获取系统警告通知失败:", repr(e))
    finally:
        if connection:
            connection.close()
    
    return warnings

@dashboard_bp.route('/')
def index():
    """仪表盘主页"""
    print("开始加载仪表盘页面")
    stats = get_dashboard_stats()
    chart_data = get_chart_data()
    model_finance = get_model_finance_data()
    warnings = get_system_warnings()
    print("仪表盘数据加载完成，准备渲染页面")
    return render_template('dashboard/index.html', stats=stats, chart_data=chart_data, model_finance=model_finance, warnings=warnings) 