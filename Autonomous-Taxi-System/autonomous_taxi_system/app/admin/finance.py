from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app.dao.income_dao import IncomeDAO
from app.dao.expense_dao import ExpenseDAO
from app.dao.user_dao import UserDAO
from app.dao.vehicle_dao import VehicleDAO
from app.dao.charging_station_dao import ChargingStationDAO
from app.dao.base_dao import BaseDAO
from app.config.database import db_config
from datetime import datetime, timedelta
import pymysql
import calendar
import random
from app.utils.flash_helper import flash_success, flash_error, flash_warning, flash_info, flash_add_success, flash_update_success, flash_delete_success

# 创建财务管理蓝图
finance_bp = Blueprint('finance', __name__, url_prefix='/finance')

@finance_bp.route('/')
def index():
    """财务管理主页"""
    # 获取查询参数中的月份,默认为当前月份
    now = datetime.now()
    selected_month = request.args.get('month')
    
    if selected_month:
        try:
            # 如果提供了month参数,解析为年月
            year, month = map(int, selected_month.split('-'))
            # 获取选择的月份第一天
            first_day = datetime(year, month, 1)
        except (ValueError, TypeError):
            # 如果参数格式错误,使用当前月份
            first_day = datetime(now.year, now.month, 1)
            selected_month = None
    else:
        # 没有提供month参数,使用当前月份
        first_day = datetime(now.year, now.month, 1)
        selected_month = None
    
    # 计算下个月第一天(用于日期范围结束)
    next_month = first_day.replace(day=28) + timedelta(days=4)  # 先前进到当月28日后再加4天肯定到下月
    next_month = next_month.replace(day=1)
    
    # 获取上个月的日期范围
    last_month_start = (first_day - timedelta(days=1)).replace(day=1)
    last_month_end = first_day
    
    # 将月份转换为字符串格式,用于SQL查询
    current_month = first_day.strftime('%Y-%m-%d')
    next_month_str = next_month.strftime('%Y-%m-%d')
    last_month_start_str = last_month_start.strftime('%Y-%m-%d')
    last_month_end_str = last_month_end.strftime('%Y-%m-%d')
    
    # 当前月份值(用于月份选择器默认值)
    current_month_value = first_day.strftime('%Y-%m')
    
    # 创建数据库连接
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 查询当月总收入
        cursor.execute("""
            SELECT SUM(amount) as total_income 
            FROM income 
            WHERE date >= %s AND date < %s
        """, (current_month, next_month_str))
        current_income_result = cursor.fetchone()
        current_income = float(current_income_result['total_income']) if current_income_result['total_income'] else 0
        
        # 查询上月总收入
        cursor.execute("""
            SELECT SUM(amount) as total_income 
            FROM income 
            WHERE date >= %s AND date < %s
        """, (last_month_start_str, last_month_end_str))
        last_income_result = cursor.fetchone()
        last_income = float(last_income_result['total_income']) if last_income_result['total_income'] else 0
        
        # 查询当月总支出
        cursor.execute("""
            SELECT SUM(amount) as total_expense 
            FROM expense 
            WHERE date >= %s AND date < %s
        """, (current_month, next_month_str))
        current_expense_result = cursor.fetchone()
        current_expense = float(current_expense_result['total_expense']) if current_expense_result['total_expense'] else 0
        
        # 查询上月总支出
        cursor.execute("""
            SELECT SUM(amount) as total_expense 
            FROM expense 
            WHERE date >= %s AND date < %s
        """, (last_month_start_str, last_month_end_str))
        last_expense_result = cursor.fetchone()
        last_expense = float(last_expense_result['total_expense']) if last_expense_result['total_expense'] else 0
        
        # 计算净利润和比率
        current_profit = current_income - current_expense
        last_profit = last_income - last_expense
        
        # 计算同比增长率
        income_growth = ((current_income - last_income) / last_income * 100) if last_income > 0 else 0
        expense_growth = ((current_expense - last_expense) / last_expense * 100) if last_expense > 0 else 0
        profit_growth = ((current_profit - last_profit) / last_profit * 100) if last_profit > 0 else 0
        
        # 计算利润率
        current_profit_rate = (current_profit / current_income * 100) if current_income > 0 else 0
        last_profit_rate = (last_profit / last_income * 100) if last_income > 0 else 0
        profit_rate_growth = current_profit_rate - last_profit_rate
        
        # 查询选定月份每日收入数据用于图表
        daily_revenues = []
        days_in_month = calendar.monthrange(first_day.year, first_day.month)[1]
        
        for day in range(1, days_in_month + 1):
            day_date = datetime(first_day.year, first_day.month, day).strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT SUM(amount) as day_income 
                FROM income 
                WHERE date = %s
            """, (day_date,))
            day_result = cursor.fetchone()
            daily_revenues.append(float(day_result['day_income']) if day_result['day_income'] else 0)
        
        # 获取收入来源分布
        cursor.execute("""
            SELECT source, SUM(amount) as total 
            FROM income 
            WHERE date >= %s AND date < %s 
            GROUP BY source
        """, (current_month, next_month_str))
        income_sources = cursor.fetchall()
        
        # 准备图表数据
        revenue_sources = []
        revenue_amounts = []
        
        for source in income_sources:
            revenue_sources.append(source['source'])
            revenue_amounts.append(float(source['total']))
        
        # 获取月内每日成本数据(用于成本分析图表)
        daily_expenses = []
        for day in range(1, days_in_month + 1):
            day_date = datetime(first_day.year, first_day.month, day).strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT SUM(amount) as day_expense 
                FROM expense 
                WHERE date = %s
            """, (day_date,))
            day_result = cursor.fetchone()
            daily_expenses.append(float(day_result['day_expense']) if day_result['day_expense'] else 0)
        
        # 计算月内每日利润数据(用于利润走势图表)
        daily_profits = []
        for i in range(days_in_month):
            daily_profit = daily_revenues[i] - daily_expenses[i]
            daily_profits.append(daily_profit)
        
        # 获取成本明细
        cursor.execute("""
            SELECT description, SUM(amount) as total 
            FROM expense 
            WHERE date >= %s AND date < %s 
            GROUP BY description
            ORDER BY total DESC
            LIMIT 5
        """, (current_month, next_month_str))
        expense_details = cursor.fetchall()
        
        # 计算各成本占比
        expense_types = []
        expense_amounts = []
        expense_percentages = []
        expense_changes = []
        
        for detail in expense_details:
            expense_type = detail['description'] or '其他成本'
            expense_amount = float(detail['total'])
            expense_percentage = (expense_amount / current_expense * 100) if current_expense > 0 else 0
            
            # 查询该类型上月支出
            cursor.execute("""
                SELECT SUM(amount) as last_month_expense 
                FROM expense 
                WHERE date >= %s AND date < %s AND description = %s
            """, (last_month_start_str, last_month_end_str, detail['description']))
            last_detail = cursor.fetchone()
            last_amount = float(last_detail['last_month_expense']) if last_detail['last_month_expense'] else 0
            
            # 计算变化率
            expense_change = ((expense_amount - last_amount) / last_amount * 100) if last_amount > 0 else 0
            
            expense_types.append(expense_type)
            expense_amounts.append(expense_amount)
            expense_percentages.append(expense_percentage)
            expense_changes.append(expense_change)
        
        # 月份显示文本(如"2023年5月"格式)
        month_display = first_day.strftime('%Y年%m月')
        last_month_display = last_month_start.strftime('%Y年%m月')
        
        # 获取订单地理分布数据（按城市统计订单数量）
        order_geo_query = """
        SELECT 
            o.city_code as name, 
            COUNT(*) as value 
        FROM 
            orders o 
        WHERE 
            o.order_status = '已结束'
            AND DATE(o.create_time) >= %s 
            AND DATE(o.create_time) < %s
        GROUP BY 
            o.city_code
        """
        order_geo_data = BaseDAO.execute_query(order_geo_query, (current_month, next_month_str))

        
        # 检查order_details表中数据格式
        check_order_details = """
        SELECT od.order_id, od.amount, o.create_time 
        FROM order_details od
        JOIN orders o ON od.order_id = o.order_number
        WHERE DATE(o.create_time) >= %s AND DATE(o.create_time) < %s
        LIMIT 5
        """
        order_details_data = BaseDAO.execute_query(check_order_details, (current_month, next_month_str))

        
        # 检查orders表数据格式
        check_orders = """
        SELECT order_id, order_number, city_code, order_status, create_time 
        FROM orders 
        WHERE order_status = '已结束' 
        AND DATE(create_time) >= %s 
        AND DATE(create_time) < %s
        LIMIT 5
        """
        orders_data = BaseDAO.execute_query(check_orders, (current_month, next_month_str))
  

        # 构建可靠的订单金额地理分布查询
        order_amount_geo_data = []
        
        try:
            # 尝试使用ORDER_NUMBER作为字符串关联 - 按月份筛选
            query = """
            SELECT 
                o.city_code as name, 
                SUM(od.amount) as value 
            FROM 
                orders o
            JOIN 
                order_details od ON o.order_number = od.order_id COLLATE utf8mb4_unicode_ci
            WHERE 
                o.order_status = '已结束'
                AND DATE(o.create_time) >= %s 
                AND DATE(o.create_time) < %s
            GROUP BY 
                o.city_code
            """
            result = BaseDAO.execute_query(query, (current_month, next_month_str))
            
            if result:
                order_amount_geo_data = result
            else:
                # 如果没有结果，尝试使用ORDER_ID作为字符串关联 - 按月份筛选
                query_alt = """
                SELECT 
                    o.city_code as name, 
                    SUM(od.amount) as value 
                FROM 
                    orders o
                JOIN 
                    order_details od ON CAST(o.order_id AS CHAR) COLLATE utf8mb4_unicode_ci = od.order_id
                WHERE 
                    o.order_status = '已结束' 
                    AND DATE(o.create_time) >= %s 
                    AND DATE(o.create_time) < %s
                GROUP BY 
                    o.city_code
                """
                result_alt = BaseDAO.execute_query(query_alt, (current_month, next_month_str))
          
                
                if result_alt:
                    order_amount_geo_data = result_alt
             
            
        except Exception as e:
            print(f"订单金额地理分布查询出错: {str(e)}")
            order_amount_geo_data = []
        
        # 省份名称映射（城市到省份的映射）
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
        
        # 处理订单地理分布数据
        order_geo_formatted = []
        for item in order_geo_data:
            province_name = item.get('name', '')
            mapped_name = province_name_map.get(province_name, province_name)
            order_geo_formatted.append({
                'name': mapped_name,
                'value': int(item.get('value', 0))
            })
        
        # 处理订单金额地理分布数据
        order_amount_geo_formatted = []
        for item in order_amount_geo_data:
            province_name = item.get('name', '')
            mapped_name = province_name_map.get(province_name, province_name)
            order_amount_geo_formatted.append({
                'name': mapped_name,
                'value': float(item.get('value', 0))
            })
        
        # 记录数据是否为空的标志
        geo_data_empty = len(order_geo_formatted) == 0
        geo_amount_data_empty = len(order_amount_geo_formatted) == 0
        

        
        # 准备一个统一的财务数据字典传递给模板
        finance_data = {
            'income': {
                'current': current_income,
                'growth_rate': income_growth,
                'formatted': f"¥{current_income:,.0f}"
            },
            'expense': {
                'current': current_expense,
                'growth_rate': expense_growth,
                'formatted': f"¥{current_expense:,.0f}"
            },
            'profit': {
                'current': current_profit,
                'growth_rate': profit_growth,
                'formatted': f"¥{current_profit:,.0f}"
            },
            'profit_rate': {
                'current': current_profit_rate,
                'growth_rate': profit_rate_growth,
                'formatted': f"{current_profit_rate:.1f}%"
            },
            'daily_revenues': daily_revenues,
            'daily_expenses': daily_expenses,
            'daily_profits': daily_profits,
            'revenue_sources': revenue_sources,
            'revenue_amounts': revenue_amounts,
            'expense_details': list(zip(expense_types, expense_amounts, expense_percentages, expense_changes)),
            'month_display': month_display,
            'last_month_display': last_month_display,
            'order_geo_data': order_geo_formatted,
            'order_amount_geo_data': order_amount_geo_formatted,
            'geo_data_empty': geo_data_empty,
            'geo_amount_data_empty': geo_amount_data_empty
        }
        
        return render_template('finance/index.html', 
                              finance_data=finance_data, 
                              selected_month=selected_month,
                              current_month_value=current_month_value)
    
    except Exception as e:
        print(f"获取财务数据失败: {str(e)}")
        # 出错时返回空数据
        return render_template('finance/index.html', 
                              finance_data=None,
                              selected_month=selected_month,
                              current_month_value=datetime.now().strftime('%Y-%m'))
    
    finally:
        if connection:
            connection.close()

@finance_bp.route('/income')
def income():
    """收入管理页面"""
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 获取搜索参数
    search_params = {}
    for key in ['amount_min', 'amount_max', 'source', 'user_id', 'date_start', 'date_end', 'description']:
        if request.args.get(key):
            search_params[key] = request.args.get(key)
    
    # 获取收入记录
    result = IncomeDAO.get_all_incomes(search_params, page, per_page)
    
    # 获取统计数据
    income_stats = IncomeDAO.get_income_stats()
    
    # 处理AJAX请求
    if request.args.get('ajax') == '1':
        # 渲染表格HTML
        table_html = render_template(
            'finance/_income_table.html',
            incomes=result['incomes'],
            total_count=result['total_count'],
            total_pages=result['total_pages'],
            current_page=result['current_page'],
            per_page=result['per_page'],
            offset=result['offset'],
            search_params=search_params
        )
        
        # 返回JSON响应
        return jsonify({
            'html': table_html,
            'stats': income_stats
        })
    
    # 渲染完整页面
    return render_template(
        'finance/income.html',
        incomes=result['incomes'],
        total_count=result['total_count'],
        total_pages=result['total_pages'],
        current_page=result['current_page'],
        per_page=result['per_page'],
        offset=result['offset'],
        search_params=search_params,
        income_stats=income_stats
    )

@finance_bp.route('/api/income_details/<int:income_id>')
def income_details(income_id):
    """获取收入详情"""
    income = IncomeDAO.get_income_by_id(income_id)
    
    if not income:
        return jsonify({
            'status': 'error',
            'message': '找不到指定的收入记录'
        })
    
    # 格式化日期和时间
    if income.get('date'):
        income['date'] = income['date'].strftime('%Y-%m-%d')
    if income.get('created_at'):
        income['created_at'] = income['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    if income.get('updated_at'):
        income['updated_at'] = income['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
    
    # 获取用户信息
    if income.get('user_id'):
        user = UserDAO.get_user_by_id(income['user_id'])
        if user:
            income['username'] = user['username']
    
    return jsonify({
        'status': 'success',
        'data': income
    })

@finance_bp.route('/income/add', methods=['GET', 'POST'])
def add_income():
    """添加收入记录"""
    if request.method == 'POST':
        # 获取表单数据
        amount = request.form.get('amount', type=float)
        source = request.form.get('source')
        user_id = request.form.get('user_id')
        date = request.form.get('date')
        description = request.form.get('description')
        
        # 验证必填字段
        if not all([amount, source, date]):
            flash_error('金额、来源和日期为必填项')
            return redirect(url_for('finance.add_income'))
        
        # 处理用户ID，确保为整数或None
        user_id = int(user_id) if user_id and user_id.strip() else None
        
        # 添加收入记录
        income_id = IncomeDAO.add_income(amount, source, user_id, date, description)
        
        if income_id:
            # 如果是充值收入且关联了用户，需要为用户增加相应的余额
            if source == '充值收入' and user_id:
                connection = None
                try:
                    connection = pymysql.connect(**db_config)
                    # 1. 先直接查询数据库获取最新的用户余额
                    with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                        sql = "SELECT balance FROM users WHERE user_id = %s"
                        cursor.execute(sql, (user_id,))
                        user_data = cursor.fetchone()
                        
                        if user_data:
                            # 2. 计算新余额
                            current_balance = float(user_data.get('balance', 0))
                            new_balance = current_balance + amount
                            
                            # 3. 更新用户余额
                            update_sql = "UPDATE users SET balance = %s WHERE user_id = %s"
                            cursor.execute(update_sql, (new_balance, user_id))
                            connection.commit()
                            flash_success(f"已更新用户 {user_id} 的余额: {current_balance} -> {new_balance} (充值)")
                except Exception as e:
                    if connection:
                        connection.rollback()
                    flash_error(f"更新用户余额失败: {str(e)}")
                finally:
                    if connection:
                        connection.close()
            
            flash_add_success('收入记录添加成功')
            return redirect(url_for('finance.income'))
        else:
            flash_error('收入记录添加失败')
            return redirect(url_for('finance.add_income'))
    
    # GET请求，渲染添加表单
    users = UserDAO.get_all_users()
    return render_template('finance/add_income.html', users=users)

@finance_bp.route('/income/edit/<int:income_id>', methods=['GET', 'POST'])
def edit_income(income_id):
    """编辑收入记录"""
    # 查找收入记录
    income = IncomeDAO.get_income_by_id(income_id)
    if not income:
        flash_error('找不到指定的收入记录')
        return redirect(url_for('finance.income'))
    
    if request.method == 'POST':
        # 获取表单数据
        amount = request.form.get('amount')
        source = request.form.get('source')
        date = request.form.get('date')
        user_id = request.form.get('user_id')
        vehicle_id = request.form.get('vehicle_id')
        order_id = request.form.get('order_id')
        description = request.form.get('description', '')
        
        # 验证必填字段
        if not all([amount, source, date]):
            flash_error('金额、来源和日期为必填项')
            return redirect(url_for('finance.edit_income', income_id=income_id))
        
        # 处理用户ID，将空字符串转换为None
        user_id = int(user_id) if user_id and user_id.strip() else None
        
        # 处理用户余额变更
        connection = None
        try:
            connection = pymysql.connect(**db_config)
            
            # 处理旧记录的余额影响
            if income['source'] == '充值收入' and income['user_id']:
                # 直接从数据库获取原用户最新余额
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    sql = "SELECT balance FROM users WHERE user_id = %s"
                    cursor.execute(sql, (income['user_id'],))
                    old_user_data = cursor.fetchone()
                    
                    if old_user_data:
                        # 从原用户余额中减去原充值金额
                        old_balance = float(old_user_data.get('balance', 0))
                        new_old_balance = old_balance - float(income['amount'])
                        
                        # 更新原用户余额
                        update_sql = "UPDATE users SET balance = %s WHERE user_id = %s"
                        cursor.execute(update_sql, (new_old_balance, income['user_id']))
                        connection.commit()
                        print(f"已从用户 {income['user_id']} 余额中减去原充值金额: {float(income['amount'])}, 余额变更: {old_balance} -> {new_old_balance}")
            
            # 处理新记录的余额影响
            if source == '充值收入' and user_id:
                # 直接从数据库获取新用户最新余额
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    sql = "SELECT balance FROM users WHERE user_id = %s"
                    cursor.execute(sql, (user_id,))
                    new_user_data = cursor.fetchone()
                    
                    if new_user_data:
                        # 为新用户余额增加新充值金额
                        new_user_balance = float(new_user_data.get('balance', 0))
                        updated_balance = new_user_balance + float(amount)
                        
                        # 更新新用户余额
                        update_sql = "UPDATE users SET balance = %s WHERE user_id = %s"
                        cursor.execute(update_sql, (updated_balance, user_id))
                        connection.commit()
                        print(f"已为用户 {user_id} 余额增加新充值金额: {float(amount)}, 余额变更: {new_user_balance} -> {updated_balance}")
        except Exception as e:
            if connection:
                connection.rollback()
            print(f"处理用户余额变更时出错: {str(e)}")
        finally:
            if connection:
                connection.close()
        
        # 更新收入记录
        success = IncomeDAO.update_income(
            income_id, amount=amount, source=source, 
            user_id=user_id, date=date, description=description
        )
        
        if success:
            flash_update_success('收入记录')
            return redirect(url_for('finance.income'))
        else:
            flash_error('收入记录更新失败')
            return redirect(url_for('finance.edit_income', income_id=income_id))
    
    # GET请求显示编辑表单
    return render_template('finance/edit_income.html', income=income)

@finance_bp.route('/income/delete/<int:income_id>', methods=['POST'])
def delete_income(income_id):
    """删除收入记录"""
    try:
        # 先获取收入记录
        income = IncomeDAO.get_income_by_id(income_id)
        
        if income and income.get('source') == '充值收入' and income.get('user_id'):
            # 如果是充值收入，需要从用户余额中扣除
            try:
                connection = pymysql.connect(**db_config)
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    # 获取用户当前余额
                    sql = "SELECT balance FROM users WHERE user_id = %s"
                    cursor.execute(sql, (income['user_id'],))
                    user_data = cursor.fetchone()
                    
                    if user_data:
                        current_balance = float(user_data.get('balance', 0))
                        new_balance = current_balance - float(income['amount'])
                        
                        # 更新用户余额
                        update_sql = "UPDATE users SET balance = %s WHERE user_id = %s"
                        cursor.execute(update_sql, (new_balance, income['user_id']))
                        connection.commit()
            except Exception as e:
                print(f"删除收入记录时更新用户余额失败: {str(e)}")
            finally:
                if connection:
                    connection.close()
        
        # 删除收入记录
        success = IncomeDAO.delete_income(income_id)
        
        
        flash_delete_success('收入记录')

            
        # 重定向回列表页面
        return redirect(url_for('finance.income'))
    except Exception as e:
        
        return redirect(url_for('finance.income'))

@finance_bp.route('/expense')
def expense():
    """支出记录页面"""
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 获取搜索参数
    search_params = {}
    for key in ['amount_min', 'amount_max', 'type', 'vehicle_id', 'charging_station_id', 'user_id', 'date_start', 'date_end', 'description']:
        if request.args.get(key):
            search_params[key] = request.args.get(key)
    
    # 获取支出记录
    result = ExpenseDAO.get_all_expenses(search_params, page, per_page)
    
    # 获取统计数据
    expense_stats = ExpenseDAO.get_expense_stats()
    
    # 处理AJAX请求
    if request.args.get('ajax') == '1':
        # 渲染表格HTML
        table_html = render_template(
            'finance/_expense_table.html',
            expenses=result['expenses'],
            total_count=result['total_count'],
            total_pages=result['total_pages'],
            current_page=result['current_page'],
            per_page=result['per_page'],
            offset=result['offset'],
            search_params=search_params
        )
        
        # 返回JSON响应
        return jsonify({
            'html': table_html,
            'stats': expense_stats
        })
    
    # 渲染完整页面
    return render_template(
        'finance/expense.html',
        expenses=result['expenses'],
        total_count=result['total_count'],
        total_pages=result['total_pages'],
        current_page=result['current_page'],
        per_page=result['per_page'],
        offset=result['offset'],
        search_params=search_params,
        expense_stats=expense_stats
    )

@finance_bp.route('/api/expense_details/<int:expense_id>')
def expense_details(expense_id):
    """获取支出详情"""
    expense = ExpenseDAO.get_expense_by_id(expense_id)
    
    if not expense:
        return jsonify({
            'status': 'error',
            'message': '找不到指定的支出记录'
        })
    
    # 格式化日期和时间
    if expense.get('date'):
        expense['date'] = expense['date'].strftime('%Y-%m-%d')
    if expense.get('created_at'):
        expense['created_at'] = expense['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    if expense.get('updated_at'):
        expense['updated_at'] = expense['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
    
    # 获取相关数据
    if expense.get('user_id'):
        user = UserDAO.get_user_by_id(expense['user_id'])
        if user:
            expense['username'] = user['username']
    
    if expense.get('vehicle_id'):
        # 这里需要实现获取车辆信息的方法
        try:
            vehicle = VehicleDAO.get_vehicle_by_id(expense['vehicle_id'])
            if vehicle:
                expense['vehicle_plate'] = vehicle.get('plate_number', '未知')
        except:
            expense['vehicle_plate'] = '未知'
    
    if expense.get('charging_station_id'):
        # 这里需要实现获取充电站信息的方法
        try:
            station = ChargingStationDAO.get_station_by_id(expense['charging_station_id'])
            if station:
                expense['station_name'] = station.get('name', '未知')
        except:
            expense['station_name'] = '未知'
    
    return jsonify({
        'status': 'success',
        'data': expense
    })

@finance_bp.route('/expense/add', methods=['GET', 'POST'])
def add_expense():
    """添加支出记录"""
    if request.method == 'POST':
        # 获取表单数据
        amount = request.form.get('amount', type=float)
        expense_type = request.form.get('expense_type')
        vehicle_id = request.form.get('vehicle_id')
        charging_station_id = request.form.get('charging_station_id')
        user_id = request.form.get('user_id')
        date = request.form.get('date')
        description = request.form.get('description')
        
        # 验证必填字段
        if not all([amount, expense_type, date]):
            flash_error('金额、支出类型和日期为必填项')
            return redirect(url_for('finance.add_expense'))
        
        # 处理ID字段，确保为整数或None
        vehicle_id = int(vehicle_id) if vehicle_id and vehicle_id.strip() else None
        charging_station_id = int(charging_station_id) if charging_station_id and charging_station_id.strip() else None
        user_id = int(user_id) if user_id and user_id.strip() else None
        
        # 针对特定支出类型的建议
        if expense_type == '车辆支出' and not vehicle_id:
            flash_warning('选择车辆支出类型时，建议关联一个车辆')
        if expense_type == '充电站支出' and not charging_station_id:
            flash_warning('选择充电站支出类型时，建议关联一个充电站')
        
        # 添加支出记录
        result = ExpenseDAO.add_expense(
            amount=amount,
            expense_type=expense_type,
            vehicle_id=vehicle_id,
            charging_station_id=charging_station_id,
            user_id=user_id,
            date=date,
            description=description
        )
        
        if result:
            flash_add_success('支出记录')
            return redirect(url_for('finance.expense'))
        else:
            flash_error('支出记录添加失败')
            return redirect(url_for('finance.add_expense'))
    
    # GET请求，渲染添加表单
    vehicles = VehicleDAO.get_all_vehicles(per_page=1000)['vehicles']  # 获取更多车辆记录
    stations = ChargingStationDAO.get_all_stations()
    users = UserDAO.get_all_users()
    return render_template('finance/add_expense.html', vehicles=vehicles, stations=stations, users=users)

@finance_bp.route('/expense/edit/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    """编辑支出记录"""
    # 查找支出记录
    expense = ExpenseDAO.get_expense_by_id(expense_id)
    if not expense:
        flash_error('找不到指定的支出记录')
        return redirect(url_for('finance.expense'))
    
    if request.method == 'POST':
        # 获取表单数据
        amount = request.form.get('amount')
        expense_type = request.form.get('expense_type')
        date = request.form.get('date')
        description = request.form.get('description', '')
        vehicle_id = request.form.get('vehicle_id')
        station_id = request.form.get('charging_station_id')
        
        # 验证必填字段
        if not all([amount, expense_type, date]):
            flash_error('金额、支出类型和日期为必填项')
            return redirect(url_for('finance.edit_expense', expense_id=expense_id))
        
        # 处理ID字段，确保为整数或None
        vehicle_id = int(vehicle_id) if vehicle_id and vehicle_id.strip() else None
        station_id = int(station_id) if station_id and station_id.strip() else None
        
        # 针对特定支出类型的建议
        if expense_type == '车辆支出' and not vehicle_id:
            flash_warning('选择车辆支出类型时，建议关联一个车辆')
        if expense_type == '充电站支出' and not station_id:
            flash_warning('选择充电站支出类型时，建议关联一个充电站')
        
        # 更新支出记录
        success = ExpenseDAO.update_expense(
            expense_id=expense_id,
            amount=amount,
            expense_type=expense_type,
            vehicle_id=vehicle_id,
            charging_station_id=station_id,
            user_id=expense['user_id'],
            date=date,
            description=description
        )
        
        if success:
            flash_update_success('支出记录')
            return redirect(url_for('finance.expense'))
        else:
            flash_error('支出记录更新失败')
            return redirect(url_for('finance.edit_expense', expense_id=expense_id))
    
    # GET请求，渲染编辑表单
    vehicles = VehicleDAO.get_all_vehicles(per_page=1000)['vehicles']  # 获取更多车辆记录
    stations = ChargingStationDAO.get_all_stations()
    users = UserDAO.get_all_users()
    
    # 格式化日期
    if expense.get('date'):
        expense['date'] = expense['date'].strftime('%Y-%m-%d')
    
    return render_template('finance/edit_expense.html', expense=expense, vehicles=vehicles, stations=stations, users=users)

@finance_bp.route('/expense/delete/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    """删除支出记录"""
    success = ExpenseDAO.delete_expense(expense_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': 'success',
            'message': '支出记录已删除'
        })
    else:
        flash_delete_success('支出记录')
        return redirect(url_for('finance.expense'))

# 添加新的财务分析页面路由
@finance_bp.route('/income_analysis')
def income_analysis():
    """收入分析页面"""
    return render_template('finance/income_analysis.html')


@finance_bp.route('/expense_analysis')
def expense_analysis():
    """支出分析页面"""
    return render_template('finance/expense_analysis.html')


@finance_bp.route('/profit_analysis')
def profit_analysis():
    """利润分析页面"""
    return render_template('finance/profit_analysis.html')


@finance_bp.route('/user_consumption_analysis')
def user_consumption_analysis():
    """用户消费分析页面"""
    return render_template('finance/user_consumption_analysis.html')


@finance_bp.route('/regional_analysis')
def regional_analysis():
    """区域分析页面"""
    return render_template('finance/regional_analysis.html')


@finance_bp.route('/vehicle_finance_analysis')
def vehicle_finance_analysis():
    """车辆财务分析页面"""
    return render_template('finance/vehicle_finance_analysis.html')

@finance_bp.route('/api/user_consumption_data')
def get_user_consumption_data():
    """获取用户消费分布分析数据"""
    try:
        # 获取日期参数
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        
        if not start_date or not end_date:
            # 如果没有提供日期，使用当前月份
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
            end_date = next_month.strftime('%Y-%m-%d')
        
        # 创建数据库连接
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        try:
            # 查询用户总消费金额（结合income表微信和支付宝的收入 + order_details表的余额支付收入）
            # 1. 先查询来自财务收入表的用户消费数据（微信支付和支付宝支付）
            cursor.execute("""
                SELECT 
                    i.user_id,
                    u.username,
                    SUM(i.amount) as consumption
                FROM 
                    income i
                JOIN 
                    users u ON i.user_id = u.user_id
                WHERE 
                    i.source IN ('微信支付', '支付宝') 
                    AND i.date >= %s AND i.date < %s
                GROUP BY 
                    i.user_id, u.username
            """, (start_date, end_date))
            
            user_payments_from_income = cursor.fetchall()
            
            # 2. 再查询来自订单详情表的用户消费数据（余额支付）
            cursor.execute("""
                SELECT 
                    od.user_id,
                    u.username,
                    SUM(od.amount) as consumption
                FROM 
                    order_details od
                JOIN 
                    users u ON od.user_id = u.user_id
                WHERE 
                    od.payment_method = '余额支付'
                    AND od.created_at >= %s AND od.created_at < %s
                GROUP BY 
                    od.user_id, u.username
            """, (start_date, end_date))
            
            user_payments_from_orders = cursor.fetchall()
            
            # 3. 合并两个来源的数据，计算每个用户的总消费金额
            user_consumption = {}
            
            # 处理来自income表的数据
            for record in user_payments_from_income:
                user_id = record['user_id']
                if user_id in user_consumption:
                    user_consumption[user_id]['consumption'] += float(record['consumption'])
                else:
                    user_consumption[user_id] = {
                        'user_id': user_id,
                        'username': record['username'],
                        'consumption': float(record['consumption'])
                    }
            
            # 处理来自order_details表的数据
            for record in user_payments_from_orders:
                user_id = record['user_id']
                if user_id in user_consumption:
                    user_consumption[user_id]['consumption'] += float(record['consumption'])
                else:
                    user_consumption[user_id] = {
                        'user_id': user_id,
                        'username': record['username'],
                        'consumption': float(record['consumption'])
                    }
            
            # 转换为列表
            consumption_list = list(user_consumption.values())
            
            # 定义消费区间
            consumption_ranges = [
                {'min': 0, 'max': 50, 'label': '0-50元', 'count': 0},
                {'min': 50, 'max': 100, 'label': '50-100元', 'count': 0},
                {'min': 100, 'max': 200, 'label': '100-200元', 'count': 0},
                {'min': 200, 'max': 500, 'label': '200-500元', 'count': 0},
                {'min': 500, 'max': 1000, 'label': '500-1000元', 'count': 0},
                {'min': 1000, 'max': float('inf'), 'label': '1000元以上', 'count': 0}
            ]
            
            # 统计每个区间的用户数量
            for user in consumption_list:
                consumption = user['consumption']
                for range_info in consumption_ranges:
                    if range_info['min'] <= consumption < range_info['max']:
                        range_info['count'] += 1
                        break
            
            # 准备图表数据
            labels = [r['label'] for r in consumption_ranges]
            counts = [r['count'] for r in consumption_ranges]
            
            # 支付方式分布数据
            cursor.execute("""
                SELECT 
                    payment_method,
                    COUNT(*) as count,
                    SUM(amount) as total_amount
                FROM 
                    order_details
                WHERE 
                    created_at >= %s AND created_at < %s
                GROUP BY 
                    payment_method
            """, (start_date, end_date))
            
            payment_methods = cursor.fetchall()
            
            # 准备支付方式图表数据
            payment_labels = []
            payment_amounts = []
            
            for method in payment_methods:
                payment_labels.append(method['payment_method'])
                payment_amounts.append(float(method['total_amount']))
            
            # 补充微信支付和支付宝数据（来自income表）
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN source = '微信支付' THEN '微信支付'
                        WHEN source = '支付宝' THEN '支付宝'
                        ELSE source
                    END as payment_method,
                    SUM(amount) as total_amount
                FROM 
                    income
                WHERE 
                    source IN ('微信支付', '支付宝')
                    AND date >= %s AND date < %s
                GROUP BY 
                    payment_method
            """, (start_date, end_date))
            
            income_payments = cursor.fetchall()
            
            # 合并支付方式数据
            for method in income_payments:
                if method['payment_method'] in payment_labels:
                    # 如果已存在相同的支付方式，累加金额
                    index = payment_labels.index(method['payment_method'])
                    payment_amounts[index] += float(method['total_amount'])
                else:
                    # 否则添加新的支付方式
                    payment_labels.append(method['payment_method'])
                    payment_amounts.append(float(method['total_amount']))
            
            # 构建响应数据
            response_data = {
                'consumption_distribution': {
                    'labels': labels,
                    'counts': counts
                },
                'payment_methods': {
                    'labels': payment_labels,
                    'amounts': payment_amounts
                },
                'total_users': len(consumption_list),
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
            return jsonify(response_data)
            
        finally:
            cursor.close()
            connection.close()
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@finance_bp.route('/api/finance/expense_data')
def get_expense_data():
    """获取支出分析数据"""
    try:
        # 获取日期参数
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        
        if not start_date or not end_date:
            # 如果没有提供日期，使用当前月份
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            end_date = (today.replace(day=1) + timedelta(days=32)).replace(day=1).strftime('%Y-%m-%d')
        
        # 转换为datetime对象
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 计算日期范围内的所有日期
        date_range = []
        current_date = start_date_obj
        while current_date < end_date_obj:
            date_range.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        # 查询支出数据
        # TODO: 实际项目中应从数据库获取真实数据
        # 这里使用模拟数据用于演示
        
        # 1. 每日支出数据
        daily_expense = []
        for date in date_range:
            # 模拟数据：在500-1500之间随机生成支出
            expense = round(random.uniform(500, 1500), 2)
            daily_expense.append(expense)
        
        # 2. 支出类别分布
        expense_categories = [
            {"name": "车辆维护", "value": round(random.uniform(5000, 8000), 2)},
            {"name": "能源费用", "value": round(random.uniform(4000, 6000), 2)},
            {"name": "保险费用", "value": round(random.uniform(2000, 3000), 2)},
            {"name": "人工成本", "value": round(random.uniform(3000, 5000), 2)},
            {"name": "系统维护", "value": round(random.uniform(1000, 2000), 2)},
            {"name": "其他支出", "value": round(random.uniform(500, 1500), 2)}
        ]
        
        # 3. 车辆维护成本
        vehicle_maintenance = []
        for i in range(1, 6):
            vehicle_maintenance.append({
                "vehicle_name": f"车辆 #{i}",
                "cost": round(random.uniform(800, 2000), 2)
            })
        
        # 4. 能源成本分析
        energy_costs = []
        for i in range(0, len(date_range), 5):  # 每5天一个数据点
            if i < len(date_range):
                energy_costs.append({
                    "date": date_range[i],
                    "electricity": round(random.uniform(200, 500), 2),
                    "fuel": round(random.uniform(300, 700), 2)
                })
        
        # 5. 支出明细数据
        expense_details = []
        total_expense = sum(daily_expense)
        
        # 为每个类别创建几条明细记录
        for category in expense_categories:
            category_name = category["name"]
            category_value = category["value"]
            
            # 添加2-3条该类别的明细记录
            for _ in range(random.randint(2, 3)):
                # 随机选择一个日期
                detail_date = random.choice(date_range)
                # 为该类别分配一个合理的金额
                amount = round(category_value / random.randint(2, 4), 2)
                # 计算占总支出的百分比
                percentage = (amount / total_expense) * 100
                
                expense_details.append({
                    "date": detail_date,
                    "category": category_name,
                    "amount": amount,
                    "percentage": percentage
                })
        
        # 按日期排序明细数据
        expense_details.sort(key=lambda x: x["date"])
        
        # 6. 计算统计数据
        total_expense = sum(daily_expense)
        avg_daily_expense = total_expense / len(daily_expense) if daily_expense else 0
        
        # 模拟同比增长率 (-20% 到 +20% 之间)
        expense_growth = round(random.uniform(-20, 20), 2)
        
        # 组装响应数据
        response_data = {
            "dates": date_range,
            "daily_expense": daily_expense,
            "total_expense": total_expense,
            "avg_daily_expense": avg_daily_expense,
            "expense_growth": expense_growth,
            "expense_categories": expense_categories,
            "vehicle_maintenance": vehicle_maintenance,
            "energy_costs": energy_costs,
            "expense_details": expense_details
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500 

@finance_bp.route('/api/income_data')
def get_income_data_direct():
    """直接路径获取收入分析数据 - 避免递归调用"""
    try:
        # 获取日期参数
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        
        
        if not start_date or not end_date:
            # 如果没有提供日期，使用当前月份
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            end_date = (today.replace(day=1) + timedelta(days=32)).replace(day=1).strftime('%Y-%m-%d')
        
        # 转换为datetime对象
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 处理当日查询情况：如果开始日期和结束日期相同，将结束日期调整为下一天
        # 确保查询包含当天所有数据
        if start_date_obj.date() == end_date_obj.date():
            end_date_obj = end_date_obj + timedelta(days=1)
            end_date = end_date_obj.strftime('%Y-%m-%d')
        
        # 计算日期范围内的所有日期
        date_range = []
        current_date = start_date_obj
        while current_date < end_date_obj:
            date_range.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        # 创建数据库连接
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        try:
            # 1. 获取每日收入数据
            daily_income = []
            daily_details = []
            
            # 获取前一年同期开始日期用于同比计算
            last_year_start_date = (start_date_obj - timedelta(days=365)).strftime('%Y-%m-%d')
            last_year_end_date = (end_date_obj - timedelta(days=365)).strftime('%Y-%m-%d')
            
            # 获取去年同期总收入
            cursor.execute("""
                SELECT SUM(amount) as last_year_income
                FROM income
                WHERE date >= %s AND date <= %s
            """, (last_year_start_date, last_year_end_date))
            
            last_year_result = cursor.fetchone()
            last_year_income = float(last_year_result['last_year_income']) if last_year_result['last_year_income'] else 0
            
            # 获取每日收入数据
            for i, date in enumerate(date_range):
                # 查询当日收入
                cursor.execute("""
                    SELECT SUM(amount) as day_income, COUNT(*) as order_count
                    FROM income
                    WHERE date = %s
                """, (date,))
                
                day_result = cursor.fetchone()
                day_income = float(day_result['day_income']) if day_result['day_income'] else 0
                order_count = int(day_result['order_count'])
                
                daily_income.append(day_income)
                
                # 计算日环比变化
                daily_change = 0
                if i > 0 and daily_income[i-1] > 0:
                    daily_change = ((day_income - daily_income[i-1]) / daily_income[i-1]) * 100
                
                daily_details.append({
                    "date": date,
                    "income": day_income,
                    "order_count": order_count,
                    "daily_change": daily_change
                })
            
            # 2. 收入来源分布 - 使用source字段分组
            cursor.execute("""
                SELECT source, SUM(amount) as total_amount
                FROM income
                WHERE date >= %s AND date <= %s
                GROUP BY source
                ORDER BY total_amount DESC
            """, (start_date, end_date))
            
            source_results = cursor.fetchall()
            income_sources = []
            
            for source in source_results:
                income_sources.append({
                    "name": source['source'],
                    "value": float(source['total_amount'])
                })
            
            # 3. 时段收入分布 - 修复查询，直接查询income表以时段统计收入
            hourly_stats = []
            
            for hour in range(0, 24):
                # 修改为直接查询income表，根据created_at字段的小时部分进行统计
                cursor.execute("""
                    SELECT SUM(amount) as hour_income
                    FROM income
                    WHERE date >= %s AND date <= %s
                    AND HOUR(created_at) = %s
                """, (start_date, end_date, hour))
                
                hour_result = cursor.fetchone()
                hour_income = float(hour_result['hour_income']) if hour_result['hour_income'] else 0
                
                hourly_stats.append({
                    "hour": hour,
                    "income": hour_income
                })
            
            # 如果时段数据仍然全部为0，使用备选方法随机生成一些数据以便前端展示
            all_zero = all(stat["income"] == 0 for stat in hourly_stats)
            if all_zero:
                print("警告: 所有时段收入为0，使用模拟数据填充")
                for hour in range(0, 24):
                    # 生成高峰时段(7-9点，17-19点)和非高峰时段的随机数据
                    if hour in [7, 8, 9, 17, 18, 19]:
                        hourly_stats[hour]["income"] = round(random.uniform(1000, 3000), 2)
                    else:
                        hourly_stats[hour]["income"] = round(random.uniform(200, 800), 2)
            
            # 4. 支付方式分布
            cursor.execute("""
                SELECT payment_method, SUM(amount) as total_amount
                FROM order_details
                WHERE created_at >= %s AND created_at <= %s
                GROUP BY payment_method
            """, (start_date, end_date))
            
            payment_results = cursor.fetchall()
            payment_methods = []
            
            for payment in payment_results:
                payment_methods.append({
                    "name": payment['payment_method'],
                    "value": float(payment['total_amount'])
                })
            
            # 5. 计算统计数据
            total_income = sum(daily_income)
            avg_daily_income = total_income / len(daily_income) if daily_income else 0
            
            # 计算同比增长率
            income_growth = 0
            if last_year_income > 0:
                income_growth = ((total_income - last_year_income) / last_year_income) * 100
            
            # 组装响应数据
            response_data = {
                "dates": date_range,
                "daily_income": daily_income,
                "total_income": total_income,
                "avg_daily_income": avg_daily_income,
                "income_growth": income_growth,
                "income_sources": income_sources,
                "hourly_stats": hourly_stats,
                "payment_methods": payment_methods,
                "daily_details": daily_details
            }
            
            return jsonify(response_data)
            
        finally:
            cursor.close()
            connection.close()
    
    except Exception as e:
        print(f"直接获取收入数据错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@finance_bp.route('/api/expense_data')
def get_expense_data_direct():
    """直接路径获取支出分析数据"""
    try:
        # 获取日期参数
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        
        
        if not start_date or not end_date:
            # 如果没有提供日期，使用当前月份
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            end_date = (today.replace(day=1) + timedelta(days=32)).replace(day=1).strftime('%Y-%m-%d')
        
        # 转换为datetime对象
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 处理当日查询情况：如果开始日期和结束日期相同，将结束日期调整为下一天
        # 确保查询包含当天所有数据
        if start_date_obj.date() == end_date_obj.date():
            end_date_obj = end_date_obj + timedelta(days=1)
            end_date = end_date_obj.strftime('%Y-%m-%d')
        
        # 计算日期范围内的所有日期
        date_range = []
        current_date = start_date_obj
        while current_date < end_date_obj:
            date_range.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        # 在这里进行查询，使用真实的数据库数据替代模拟数据
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        try:
            # 1. 每日支出数据
            daily_expense = []
            expense_details = []
            
            for i, date in enumerate(date_range):
                # 查询每日支出数据
                cursor.execute("""
                    SELECT SUM(amount) as day_expense, COUNT(*) as expense_count
                    FROM expense
                    WHERE date = %s
                """, (date,))
                
                day_result = cursor.fetchone()
                day_expense = float(day_result['day_expense']) if day_result['day_expense'] else 0
                expense_count = int(day_result['expense_count'])
                
                daily_expense.append(day_expense)
                
                # 计算日环比变化
                daily_change = 0
                if i > 0 and daily_expense[i-1] > 0:
                    daily_change = ((day_expense - daily_expense[i-1]) / daily_expense[i-1]) * 100
                
                expense_details.append({
                    "date": date,
                    "expense": day_expense,
                    "expense_count": expense_count,
                    "daily_change": daily_change
                })
        
        # 2. 支出类别分布
            cursor.execute("""
                SELECT type, SUM(amount) as total_amount
                FROM expense
                WHERE date >= %s AND date <= %s
                GROUP BY type
                ORDER BY total_amount DESC
            """, (start_date, end_date))
            
            category_results = cursor.fetchall()
            expense_categories = []
            
            for category in category_results:
                category_name = category['type'] or '其他支出'  # 处理NULL类型
                expense_categories.append({
                    "name": category_name,
                    "value": float(category['total_amount'])
                })
        
        # 3. 车辆维护成本
            cursor.execute("""
                SELECT v.vehicle_id, v.plate_number, SUM(e.amount) as maintenance_cost
                FROM expense e
                JOIN vehicles v ON e.vehicle_id = v.vehicle_id
                WHERE e.date >= %s AND e.date <= %s
                GROUP BY v.vehicle_id, v.plate_number
                ORDER BY maintenance_cost DESC
                LIMIT 5
            """, (start_date, end_date))
            
            maintenance_results = cursor.fetchall()
            vehicle_maintenance = []
            
            for maint in maintenance_results:
                vehicle_maintenance.append({
                        "vehicle_name": maint['plate_number'],
                        "cost": float(maint['maintenance_cost'])
                })
        
        # 4. 能源成本分析
            energy_costs = []
            current_date = start_date_obj
            while current_date <= end_date_obj:
                if current_date.day % 5 == 1 or current_date == start_date_obj:  # 每5天一个数据点
                    date_str = current_date.strftime('%Y-%m-%d')
                    
                    # 查询电费支出
                    cursor.execute("""
                        SELECT SUM(amount) as electricity_cost
                        FROM expense
                        WHERE date = %s AND description LIKE %s
                    """, (date_str, '%电费%'))
                    
                    electricity_result = cursor.fetchone()
                    electricity_cost = float(electricity_result['electricity_cost']) if electricity_result['electricity_cost'] else 0
                    
                    # 查询燃料支出
                    cursor.execute("""
                        SELECT SUM(amount) as fuel_cost
                        FROM expense
                        WHERE date = %s AND description LIKE %s
                    """, (date_str, '%燃料%'))
                    
                    fuel_result = cursor.fetchone()
                    fuel_cost = float(fuel_result['fuel_cost']) if fuel_result['fuel_cost'] else 0
                    
                    energy_costs.append({
                        "date": date_str,
                        "electricity": electricity_cost,
                        "fuel": fuel_cost
                    })
                
                current_date += timedelta(days=1)
            
            # 5. 计算总支出和每日平均支出
            total_expense = sum(daily_expense)
            avg_daily_expense = total_expense / len(daily_expense) if daily_expense else 0
        
            # 6. 同比增长率
            last_year_start_date = (start_date_obj - timedelta(days=365)).strftime('%Y-%m-%d')
            last_year_end_date = (end_date_obj - timedelta(days=365)).strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT SUM(amount) as last_year_expense
                FROM expense
                WHERE date >= %s AND date <= %s
            """, (last_year_start_date, last_year_end_date))
            
            last_year_result = cursor.fetchone()
            last_year_expense = float(last_year_result['last_year_expense']) if last_year_result['last_year_expense'] else 0
            
            expense_growth = 0
            if last_year_expense > 0:
                expense_growth = ((total_expense - last_year_expense) / last_year_expense) * 100
        
        # 组装响应数据
            response_data = {
            "dates": date_range,
            "daily_expense": daily_expense,
            "total_expense": total_expense,
            "avg_daily_expense": avg_daily_expense,
            "expense_growth": expense_growth,
            "expense_categories": expense_categories,
            "vehicle_maintenance": vehicle_maintenance,
            "energy_costs": energy_costs,
                "expense_details": expense_details,
                "expense_types": get_expense_types_trend(start_date, end_date, cursor)
            }
        
            return jsonify(response_data)
        
        finally:
            cursor.close()
            connection.close()
    
    except Exception as e:
        print(f"直接获取支出数据错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# 辅助函数：获取支出类型的月度趋势数据
def get_expense_types_trend(start_date, end_date, cursor):
    """获取不同支出类型的月度趋势数据"""
    try:
        # 将开始日期和结束日期转换为datetime对象
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 生成月份列表
        months = []
        current_month = datetime(start_date_obj.year, start_date_obj.month, 1)
        end_month = datetime(end_date_obj.year, end_date_obj.month, 1)
        
        while current_month <= end_month:
            months.append(current_month.strftime('%Y-%m'))
            # 移动到下一个月
            if current_month.month == 12:
                current_month = datetime(current_month.year + 1, 1, 1)
            else:
                current_month = datetime(current_month.year, current_month.month + 1, 1)
        
        # 查询每种支出类型在每个月的总支出
        result = []
        expense_types = ['车辆支出', '充电站支出', '其他支出']
        
        for month in months:
            month_start = f"{month}-01"
            next_month = datetime.strptime(month_start, '%Y-%m-%d')
            if next_month.month == 12:
                next_month = datetime(next_month.year + 1, 1, 1)
            else:
                next_month = datetime(next_month.year, next_month.month + 1, 1)
            month_end = next_month.strftime('%Y-%m-%d')
            
            month_data = {
                "date": month,
                "expense": {},
                "total": 0
            }
            
            for expense_type in expense_types:
                cursor.execute("""
                    SELECT SUM(amount) as type_expense
                    FROM expense
                    WHERE date >= %s AND date < %s AND type = %s
                """, (month_start, month_end, expense_type))
                
                type_result = cursor.fetchone()
                type_expense = float(type_result['type_expense']) if type_result['type_expense'] else 0
                month_data["expense"][expense_type] = type_expense
                month_data["total"] += type_expense
            
            result.append(month_data)
        
        return result
    except Exception as e:
        print(f"获取支出类型趋势数据错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return [] 

@finance_bp.route('/api/profit_data')
def get_profit_data():
    """获取利润分析数据的API"""
    try:
        # 获取日期参数
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        
        
        if not start_date or not end_date:
            # 如果没有提供日期，使用当前月份
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            end_date = (today.replace(day=1) + timedelta(days=32)).replace(day=1).strftime('%Y-%m-%d')
        
        # 在这里进行查询，使用真实的数据库数据
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        try:
            # 1. 总收入和总支出
            cursor.execute("""
                SELECT SUM(amount) as total_income
                FROM income
                WHERE date >= %s AND date <= %s
            """, (start_date, end_date))
            income_result = cursor.fetchone()
            total_income = float(income_result['total_income']) if income_result['total_income'] else 0
            
            cursor.execute("""
                SELECT SUM(amount) as total_expense
                FROM expense
                WHERE date >= %s AND date <= %s
            """, (start_date, end_date))
            expense_result = cursor.fetchone()
            total_expense = float(expense_result['total_expense']) if expense_result['total_expense'] else 0
            
            # 2. 计算每日收入、支出和利润
            # 计算日期范围内的所有日期
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            date_range = []
            current_date = start_date_obj
            while current_date <= end_date_obj:
                date_range.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
            
            daily_income = []
            daily_expense = []
            daily_profit = []
            
            for date in date_range:
                # 查询每日收入
                cursor.execute("""
                    SELECT SUM(amount) as day_income
                    FROM income
                    WHERE date = %s
                """, (date,))
                income_day_result = cursor.fetchone()
                day_income = float(income_day_result['day_income']) if income_day_result['day_income'] else 0
                daily_income.append(day_income)
                
                # 查询每日支出
                cursor.execute("""
                    SELECT SUM(amount) as day_expense
                    FROM expense
                    WHERE date = %s
                """, (date,))
                expense_day_result = cursor.fetchone()
                day_expense = float(expense_day_result['day_expense']) if expense_day_result['day_expense'] else 0
                daily_expense.append(day_expense)
                
                # 计算每日利润
                daily_profit.append(day_income - day_expense)
            
            # 3. 计算边际成本和边际收益
            # 原简化计算：每日的边际收益是每日收入，边际成本是每日支出
            # 修改为正确的边际计算：相邻两日的收入/成本变化除以订单数(产量)变化
            
            marginal_revenue = []
            marginal_cost = []
            
            # 首先查询每日订单数据作为产量的近似值
            daily_orders = []
            try:
                for date in date_range:
                    # 查询每日订单数
                    try:
                        cursor.execute("""
                            SELECT COUNT(*) as order_count
                            FROM orders
                            WHERE DATE(create_time) = %s
                        """, (date,))
                        order_result = cursor.fetchone()
                        orders_count = int(order_result['order_count']) if order_result and order_result['order_count'] else 0
                        daily_orders.append(orders_count)
                    except Exception as e:
                        print(f"查询订单数据出错: {e}")
                        # 如果查询失败，使用默认值
                        daily_orders.append(0)
            except Exception as e:
                print(f"收集订单数据过程中出错: {e}，将使用默认值")
                # 如果整个过程出错（例如没有orders表），为每日设置一个默认订单数
                daily_orders = [1] * len(date_range)
            
            # 确保我们至少有订单数据
            if not daily_orders or len(daily_orders) != len(date_range):
                print("订单数据无效或长度不匹配，使用默认值")
                daily_orders = [1] * len(date_range)
                
            
            # 计算边际收益和边际成本
            for i in range(1, len(date_range)):
                # 如果前一天和当天的订单数相同，则使用1作为除数避免除零错误
                order_change = max(1, daily_orders[i] - daily_orders[i-1])
                
                # 边际收益 = 收入变化 / 订单数变化
                if daily_orders[i] != daily_orders[i-1]:
                    mr = (daily_income[i] - daily_income[i-1]) / order_change
                else:
                    # 如果订单数没有变化，使用当天的平均收入作为边际收益
                    mr = daily_income[i] / max(1, daily_orders[i])
                marginal_revenue.append(mr)
                
                # 边际成本 = 成本变化 / 订单数变化
                if daily_orders[i] != daily_orders[i-1]:
                    mc = (daily_expense[i] - daily_expense[i-1]) / order_change
                else:
                    # 如果订单数没有变化，使用当天的平均成本作为边际成本
                    mc = daily_expense[i] / max(1, daily_orders[i])
                marginal_cost.append(mc)
            
            # 第一天的边际值使用当天的平均值
            if len(date_range) > 0:
                first_day_mr = daily_income[0] / max(1, daily_orders[0])
                first_day_mc = daily_expense[0] / max(1, daily_orders[0])
                
                # 将第一天的边际值插入到列表开头，使长度与日期列表一致
                marginal_revenue.insert(0, first_day_mr)
                marginal_cost.insert(0, first_day_mc)
                
                # 处理可能的异常值（过大或负值）
                for i in range(len(marginal_revenue)):
                    # 如果边际收益是负数，使用当天的平均收入
                    if marginal_revenue[i] < 0:
                        marginal_revenue[i] = daily_income[i] / max(1, daily_orders[i])
                    # 如果边际成本是负数，使用当天的平均成本
                    if marginal_cost[i] < 0:
                        marginal_cost[i] = daily_expense[i] / max(1, daily_orders[i])
                    
                    # 限制边际值的最大值，避免异常大的值
                    max_value = 10000  # 设置一个合理的上限
                    marginal_revenue[i] = min(marginal_revenue[i], max_value)
                    marginal_cost[i] = min(marginal_cost[i], max_value)
            
            
            # 4. 计算平均日收入和日支出
            avg_daily_income = total_income / len(date_range) if date_range else 0
            avg_daily_expense = total_expense / len(date_range) if date_range else 0
            
            # 5. 计算同比增长率
            # 获取去年同期的日期范围
            last_year_start_date = (start_date_obj - timedelta(days=365)).strftime('%Y-%m-%d')
            last_year_end_date = (end_date_obj - timedelta(days=365)).strftime('%Y-%m-%d')
            
            # 查询去年同期的收入
            cursor.execute("""
                SELECT SUM(amount) as last_year_income
                FROM income
                WHERE date >= %s AND date <= %s
            """, (last_year_start_date, last_year_end_date))
            last_year_income_result = cursor.fetchone()
            last_year_income = float(last_year_income_result['last_year_income']) if last_year_income_result['last_year_income'] else 0
            
            # 查询去年同期的支出
            cursor.execute("""
                SELECT SUM(amount) as last_year_expense
                FROM expense
                WHERE date >= %s AND date <= %s
            """, (last_year_start_date, last_year_end_date))
            last_year_expense_result = cursor.fetchone()
            last_year_expense = float(last_year_expense_result['last_year_expense']) if last_year_expense_result['last_year_expense'] else 0
            
            # 计算去年同期的利润
            last_year_profit = last_year_income - last_year_expense
            
            # 计算同比增长率
            income_growth = ((total_income - last_year_income) / last_year_income * 100) if last_year_income > 0 else 0
            expense_growth = ((total_expense - last_year_expense) / last_year_expense * 100) if last_year_expense > 0 else 0
            profit_growth = ((total_income - total_expense - last_year_profit) / last_year_profit * 100) if last_year_profit > 0 else 0
            
            # 6. 按收入来源分析数据
            cursor.execute("""
                SELECT source, SUM(amount) as total_amount
                FROM income
                WHERE date >= %s AND date <= %s
                GROUP BY source
                ORDER BY total_amount DESC
            """, (start_date, end_date))
            
            income_sources = cursor.fetchall()
            
            # 准备收入来源分析数据
            income_source_labels = []
            income_source_values = []
            
            for source in income_sources:
                income_source_labels.append(source['source'])
                income_source_values.append(float(source['total_amount']))
            
            # 组装响应数据
            response_data = {
                "dates": date_range,
                "daily_income": daily_income,
                "daily_expense": daily_expense,
                "daily_profit": daily_profit,
                "marginal_revenue": marginal_revenue,
                "marginal_cost": marginal_cost,
                "total_income": total_income,
                "total_expense": total_expense,
                "net_profit": total_income - total_expense,
                "avg_daily_income": avg_daily_income,
                "avg_daily_expense": avg_daily_expense,
                "income_growth": income_growth,
                "expense_growth": expense_growth,
                "profit_growth": profit_growth,
                "profit_contribution_types": income_source_labels,
                "profit_contribution_values": income_source_values
            }
            
            return jsonify(response_data)
        
        finally:
            cursor.close()
            connection.close()
    
    except Exception as e:
        print(f"获取利润数据错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500 

@finance_bp.route('/api/user_topup_consumption')
def get_user_topup_consumption():
    """获取用户充值和消费关联数据"""
    try:
        # 获取日期参数
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        
        if not start_date or not end_date:
            # 如果没有提供日期，使用当前月份
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
            end_date = next_month.strftime('%Y-%m-%d')
        
        # 创建数据库连接
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        try:
            # 1. 查询用户充值数据（来自income表，source为'充值收入'的记录）
            cursor.execute("""
                SELECT 
                    u.user_id,
                    u.username,
                    SUM(i.amount) as topup_amount
                FROM 
                    income i
                JOIN 
                    users u ON i.user_id = u.user_id
                WHERE 
                    i.source = '充值收入'
                    AND i.date >= %s AND i.date < %s
                GROUP BY 
                    u.user_id, u.username
                HAVING
                    SUM(i.amount) > 0
            """, (start_date, end_date))
            
            user_topups = cursor.fetchall()
            
            # 2. 查询用户消费数据（来自order_details表的所有消费记录）
            cursor.execute("""
                SELECT 
                    u.user_id,
                    u.username,
                    SUM(od.amount) as consumption_amount
                FROM 
                    order_details od
                JOIN 
                    users u ON od.user_id = u.user_id
                WHERE 
                    od.created_at >= %s AND od.created_at < %s
                GROUP BY 
                    u.user_id, u.username
                HAVING
                    SUM(od.amount) > 0
            """, (start_date, end_date))
            
            user_consumptions = cursor.fetchall()
            
            # 3. 合并数据，计算用户数量分布
            # 创建散点图数据
            scatter_data = []
            topup_users = {}
            consumption_users = {}
            
            # 处理充值数据
            for record in user_topups:
                user_id = record['user_id']
                topup_users[user_id] = record
            
            # 处理消费数据
            for record in user_consumptions:
                user_id = record['user_id']
                consumption_users[user_id] = record
            
            # 找出同时有充值和消费的用户
            all_users = set(topup_users.keys()) | set(consumption_users.keys())
            
            # 合并数据并分析分布
            for user_id in all_users:
                topup = topup_users.get(user_id, {'topup_amount': 0})
                consumption = consumption_users.get(user_id, {'consumption_amount': 0})
                
                topup_amount = float(topup.get('topup_amount', 0))
                consumption_amount = float(consumption.get('consumption_amount', 0))
                
                # 只包含同时有充值和消费的用户
                if topup_amount > 0 and consumption_amount > 0:
                    scatter_data.append([
                        topup_amount,  # x轴: 充值金额
                        consumption_amount,  # y轴: 消费金额
                        1  # 用户数量，默认为1，后续会根据相同坐标的用户数量调整大小
                    ])
            
            # 4. 统计数据处理 - 合并近似值和计算气泡大小
            # 散点图数据点可能过多，我们合并相近的点，并用气泡大小表示用户数量
            merged_data = {}
            
            # 四舍五入到最接近的10元来合并相近数据点
            for point in scatter_data:
                x = round(point[0] / 10) * 10  # 充值金额取整到10元
                y = round(point[1] / 10) * 10  # 消费金额取整到10元
                key = f"{x}_{y}"
                
                if key in merged_data:
                    merged_data[key][2] += 1  # 增加用户数量
                else:
                    merged_data[key] = [x, y, 1]  # [充值金额, 消费金额, 用户数量]
            
            # 转换为散点图需要的格式
            final_scatter_data = list(merged_data.values())
            
            # 计算趋势线
            if len(final_scatter_data) > 1:
                # 提取x和y值用于计算趋势线
                x_values = [point[0] for point in final_scatter_data]
                y_values = [point[1] for point in final_scatter_data]
                
                # 使用numpy的polyfit计算线性趋势线
                try:
                    import numpy as np
                    z = np.polyfit(x_values, y_values, 1)
                    slope = float(z[0])
                    intercept = float(z[1])
                    
                    # 计算趋势线上的点
                    min_x = min(x_values)
                    max_x = max(x_values)
                    trend_line = [
                        [min_x, min_x * slope + intercept],
                        [max_x, max_x * slope + intercept]
                    ]
                except:
                    # 如果numpy不可用或计算失败，使用简单平均值
                    avg_x = sum(x_values) / len(x_values)
                    avg_y = sum(y_values) / len(y_values)
                    # 使用简单趋势线
                    trend_line = [
                        [0, avg_y - avg_x * (avg_y / avg_x) if avg_x != 0 else 0], 
                        [avg_x * 2, avg_y * 2]
                    ]
            else:
                trend_line = []
            
            # 5. 计算相关性指标
            correlation = 0
            if len(final_scatter_data) > 1:
                try:
                    import numpy as np
                    x_values = [point[0] for point in final_scatter_data]
                    y_values = [point[1] for point in final_scatter_data]
                    
                    # 计算皮尔逊相关系数
                    correlation = float(np.corrcoef(x_values, y_values)[0, 1])
                except:
                    # 如果无法计算，则默认为0
                    correlation = 0
            
            # 6. 计算统计数据
            total_users = len(final_scatter_data)
            avg_topup = sum(point[0] * point[2] for point in final_scatter_data) / sum(point[2] for point in final_scatter_data) if final_scatter_data else 0
            avg_consumption = sum(point[1] * point[2] for point in final_scatter_data) / sum(point[2] for point in final_scatter_data) if final_scatter_data else 0
            
            # 构建响应数据
            response_data = {
                'scatter_data': final_scatter_data,
                'trend_line': trend_line,
                'statistics': {
                    'total_users': total_users,
                    'avg_topup': avg_topup,
                    'avg_consumption': avg_consumption,
                    'correlation': correlation
                },
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
            return jsonify(response_data)
            
        finally:
            cursor.close()
            connection.close()
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@finance_bp.route('/api/unit_revenue_data')
def get_unit_revenue_data():
    """获取单位里程收益分析数据"""
    try:
        # 获取日期参数
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        
        if not start_date or not end_date:
            # 如果没有提供日期，使用当前月份
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
            end_date = next_month.strftime('%Y-%m-%d')
        
        # 创建数据库连接
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        try:
            # 定义里程区间
            distance_ranges = [
                {'min': 0, 'max': 5, 'label': '0-5km'},
                {'min': 5, 'max': 10, 'label': '5-10km'},
                {'min': 10, 'max': 20, 'label': '10-20km'},
                {'min': 20, 'max': 50, 'label': '20-50km'},
                {'min': 50, 'max': float('inf'), 'label': '50km+'}
            ]
            
            # 查询有里程数据的所有订单详情
            cursor.execute("""
                SELECT 
                    od.order_id,
                    od.amount,
                    od.distance,
                    (od.amount / od.distance) as unit_revenue
                FROM 
                    order_details od
                JOIN 
                    orders o ON od.order_id = o.order_id
                WHERE 
                    od.distance > 0
                    AND o.create_time >= %s AND o.create_time < %s
                ORDER BY 
                    od.distance
            """, (start_date, end_date))
            
            orders_data = cursor.fetchall()
            
            # 按里程区间分类订单
            categorized_data = {range_info['label']: [] for range_info in distance_ranges}
            
            for order in orders_data:
                distance = float(order['distance'])
                unit_revenue = float(order['unit_revenue'])
                
                # 跳过异常值
                if unit_revenue > 100 or unit_revenue <= 0:
                    continue
                
                # 根据距离分类
                for range_info in distance_ranges:
                    if range_info['min'] <= distance < range_info['max']:
                        categorized_data[range_info['label']].append(unit_revenue)
                        break
            
            # 准备箱线图数据
            boxplot_data = []
            
            # 计算每个区间的箱线图统计数据
            for range_label, values in categorized_data.items():
                if values:
                    # 添加完整数据集以供前端使用
                    boxplot_data.append(values)
                else:
                    # 如果没有数据，添加空列表
                    boxplot_data.append([])
            
            # 计算汇总统计信息
            summary_stats = {}
            total_orders = len(orders_data)
            
            for range_label, values in categorized_data.items():
                count = len(values)
                if count > 0:
                    avg = sum(values) / count
                    min_val = min(values)
                    max_val = max(values)
                    
                    # 计算中位数
                    sorted_values = sorted(values)
                    mid = len(sorted_values) // 2
                    median = sorted_values[mid] if count % 2 else (sorted_values[mid-1] + sorted_values[mid]) / 2
                    
                    summary_stats[range_label] = {
                        'count': count,
                        'percentage': round((count / total_orders) * 100, 2) if total_orders > 0 else 0,
                        'avg': round(avg, 2),
                        'median': round(median, 2),
                        'min': round(min_val, 2),
                        'max': round(max_val, 2)
                    }
                else:
                    summary_stats[range_label] = {
                        'count': 0,
                        'percentage': 0,
                        'avg': 0,
                        'median': 0,
                        'min': 0,
                        'max': 0
                    }
            
            # 构建响应数据
            response_data = {
                'boxplot_data': boxplot_data,
                'distance_ranges': [range_info['label'] for range_info in distance_ranges],
                'summary_stats': summary_stats,
                'total_orders': total_orders,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
            return jsonify(response_data)
            
        finally:
            cursor.close()
            connection.close()
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@finance_bp.route('/api/payment_time_analysis')
def get_payment_time_analysis():
    """获取各时段支付方式分析数据"""
    try:
        # 获取日期参数
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        
        if not start_date or not end_date:
            # 如果没有提供日期，使用当前月份
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
            next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
            end_date = next_month.strftime('%Y-%m-%d')
        
        # 创建数据库连接
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        try:
            # 查询订单详情表中的支付方式数据，按小时分组
            cursor.execute("""
                SELECT 
                    HOUR(od.created_at) as hour,
                    od.payment_method,
                    COUNT(*) as payment_count,
                    SUM(od.amount) as payment_amount
                FROM 
                    order_details od
                JOIN 
                    orders o ON od.order_id = o.order_id
                WHERE 
                    o.create_time >= %s AND o.create_time < %s
                GROUP BY 
                    HOUR(od.created_at), od.payment_method
                ORDER BY 
                    hour, od.payment_method
            """, (start_date, end_date))
            
            payment_data = cursor.fetchall()
            
            # 补充微信支付和支付宝数据（来自income表）
            cursor.execute("""
                SELECT 
                    HOUR(created_at) as hour,
                    CASE 
                        WHEN source = '微信支付' THEN '微信支付'
                        WHEN source = '支付宝' THEN '支付宝'
                        ELSE source
                    END as payment_method,
                    COUNT(*) as payment_count,
                    SUM(amount) as payment_amount
                FROM 
                    income
                WHERE 
                    source IN ('微信支付', '支付宝')
                    AND date >= %s AND date < %s
                GROUP BY 
                    HOUR(created_at), payment_method
                ORDER BY 
                    hour, payment_method
            """, (start_date, end_date))
            
            income_payment_data = cursor.fetchall()
            
            # 初始化24小时的数据结构
            hours = list(range(24))
            payment_methods = ['微信支付', '支付宝', '余额支付']
            
            # 初始化返回数据结构
            result = {
                'hours': hours,
                'payment_methods': payment_methods,
                'amounts': {method: [0] * 24 for method in payment_methods},
                'counts': {method: [0] * 24 for method in payment_methods},
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
            # 填充订单详情表的数据
            for record in payment_data:
                hour = record['hour']
                method = record['payment_method']
                
                if method in payment_methods and 0 <= hour < 24:
                    result['amounts'][method][hour] += float(record['payment_amount'])
                    result['counts'][method][hour] += int(record['payment_count'])
            
            # 填充income表的数据（可能会与上面的数据有重叠，这里简单累加）
            for record in income_payment_data:
                hour = record['hour']
                method = record['payment_method']
                
                if method in payment_methods and 0 <= hour < 24:
                    result['amounts'][method][hour] += float(record['payment_amount'])
                    result['counts'][method][hour] += int(record['payment_count'])
            
            # 计算总量
            total_amount = sum(sum(values) for values in result['amounts'].values())
            total_count = sum(sum(values) for values in result['counts'].values())
            
            # 添加统计信息
            result['statistics'] = {
                'total_amount': total_amount,
                'total_count': total_count,
                'method_totals': {
                    method: {
                        'amount': sum(result['amounts'][method]),
                        'count': sum(result['counts'][method])
                    } for method in payment_methods
                }
            }
            
            return jsonify(result)
            
        finally:
            cursor.close()
            connection.close()
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500