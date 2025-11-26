from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
import random
from datetime import datetime, timedelta
import pymysql
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库连接配置
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '123456')
DB_NAME = os.getenv('DB_NAME', 'autonomous_taxi_system')

# 创建优惠券蓝图
coupons_bp = Blueprint('coupons', __name__, url_prefix='/coupons')

# 模拟数据 - 优惠券套餐
coupon_packages = [
    {
        'id': 1,
        'name': '新用户大礼包',
        'description': '新用户专享优惠礼包，包含3张优惠券',
        'price': 9.9,
        'status': '销售中',
        'sales': 1245,
        'coupons': [
            {'type': '满减', 'value': '满30减10'},
            {'type': '折扣', 'value': '8折券'},
            {'type': '满减', 'value': '满100减30'}
        ],
        'validity_days': 30
    },
    {
        'id': 2,
        'name': '周末畅行礼包',
        'description': '周末出行更优惠，4张券一次搞定',
        'price': 19.9,
        'status': '销售中',
        'sales': 876,
        'coupons': [
            {'type': '满减', 'value': '满40减15'},
            {'type': '折扣', 'value': '7.5折券'},
            {'type': '满减', 'value': '满80减25'},
            {'type': '满减', 'value': '满200减80'}
        ],
        'validity_days': 60
    },
    {
        'id': 3,
        'name': '商务通勤套餐',
        'description': '上班族必备优惠礼包',
        'price': 29.9,
        'status': '已下架',
        'sales': 532,
        'coupons': [
            {'type': '满减', 'value': '满50减20'},
            {'type': '满减', 'value': '满100减50'},
            {'type': '折扣', 'value': '6.5折券'},
            {'type': '满减', 'value': '满150减60'},
            {'type': '折扣', 'value': '8折券'}
        ],
        'validity_days': 90
    }
]

# 模拟数据 - 优惠券活动
coupon_activities = [
    {
        'id': 1,
        'name': '新用户注册礼',
        'start_time': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'end_time': (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d'),
        'trigger_type': '注册',
        'trigger_condition': '新用户注册成功',
        'status': '进行中',
        'issued_count': 1280,
        'used_count': 463
    },
    {
        'id': 2,
        'name': '五一出行特惠',
        'start_time': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
        'end_time': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'),
        'trigger_type': '手动',
        'trigger_condition': '平台发放',
        'status': '进行中',
        'issued_count': 5000,
        'used_count': 1203
    },
    {
        'id': 3,
        'name': '邀请好友返利',
        'start_time': (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
        'end_time': (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
        'trigger_type': '邀请',
        'trigger_condition': '成功邀请1位好友',
        'status': '已结束',
        'issued_count': 3456,
        'used_count': 2789
    },
    {
        'id': 4,
        'name': '周末专享折扣',
        'start_time': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
        'end_time': (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
        'trigger_type': '消费',
        'trigger_condition': '单笔订单满80元',
        'status': '未开始',
        'issued_count': 0,
        'used_count': 0
    }
]

# 模拟数据 - 用户优惠券列表
user_coupons = []
status_options = ['未使用', '已使用', '已过期']
discount_types = ['满减', '折扣']

for i in range(1, 101):
    status = random.choice(status_options)
    discount_type = random.choice(discount_types)
    
    if discount_type == '满减':
        min_amount = random.randint(20, 100)
        discount_amount = random.randint(5, min_amount//2)
        value = f'满{min_amount}减{discount_amount}'
    else:
        discount_rate = round(random.uniform(0.5, 0.95), 1)
        value = f'{discount_rate*10}折'
    
    days_ago = random.randint(1, 60)
    validity_days = random.randint(10, 90)
    
    receive_time = datetime.now() - timedelta(days=days_ago)
    validity_start = receive_time
    validity_end = receive_time + timedelta(days=validity_days)
    
    use_time = None
    if status == '已使用':
        use_days = random.randint(1, min(days_ago, validity_days))
        use_time = receive_time + timedelta(days=use_days)
    
    source = random.choice(['注册礼包', '活动发放', '消费赠送', '套餐购买'])
    user_id = random.randint(1, 50)
    
    coupon = {
        'id': i,
        'name': f"{'新用户专享' if i%5==0 else ''}{'周末特惠' if i%3==0 else ''}{'节日福利' if i%7==0 else ''}优惠券" if i%15!=0 else f'VIP{random.randint(1,5)}特权券',
        'discount_type': discount_type,
        'value': value,
        'user_id': user_id,
        'user_name': f'用户{user_id}',
        'receive_time': receive_time.strftime('%Y-%m-%d %H:%M'),
        'validity_start': validity_start.strftime('%Y-%m-%d'),
        'validity_end': validity_end.strftime('%Y-%m-%d'),
        'use_time': use_time.strftime('%Y-%m-%d %H:%M') if use_time else None,
        'status': status,
        'source': source
    }
    user_coupons.append(coupon)

# 模拟数据 - 统计数据
statistics = {
    'total_coupons': 10000,
    'issued_coupons': 8500,
    'used_coupons': 3200,
    'expired_coupons': 1500,
    'usage_rate': 37.6,
    'type_stats': [
        {'type': '满减券', 'count': 5100, 'used': 2000, 'rate': 39.2},
        {'type': '折扣券', 'count': 3400, 'used': 1200, 'rate': 35.3}
    ],
    'source_stats': [
        {'source': '注册礼包', 'count': 2500, 'used': 1200, 'rate': 48.0},
        {'source': '活动发放', 'count': 3000, 'used': 1000, 'rate': 33.3},
        {'source': '消费赠送', 'count': 2000, 'used': 800, 'rate': 40.0},
        {'source': '套餐购买', 'count': 1000, 'used': 200, 'rate': 20.0}
    ],
    'monthly_data': [
        {'month': '1月', 'issued': 600, 'used': 200},
        {'month': '2月', 'issued': 800, 'used': 350},
        {'month': '3月', 'issued': 1200, 'used': 500},
        {'month': '4月', 'issued': 1600, 'used': 700},
        {'month': '5月', 'issued': 2000, 'used': 800},
        {'month': '6月', 'issued': 2300, 'used': 650}
    ]
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_coupon_types():
    """获取所有优惠券类型信息"""
    coupon_types = []
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM coupon_types ORDER BY id")
            coupon_types = cursor.fetchall()
    except Exception as e:
        print(f"获取优惠券类型数据时出错: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
    return coupon_types

# 获取套餐详情API
@coupons_bp.route('/api/packages/<int:package_id>')
def get_package_detail(package_id):
    """获取指定优惠券套餐的详细信息"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 获取套餐信息
            cursor.execute("""
                SELECT * FROM coupon_packages WHERE id = %s
            """, (package_id,))
            package = cursor.fetchone()
            
            if not package:
                return jsonify({"success": False, "message": "套餐不存在"}), 404
            
            # 解析JSON字符串为Python字典
            if isinstance(package['coupon_details'], str):
                package['coupon_details'] = json.loads(package['coupon_details'])
            
            # 格式化日期时间
            if 'created_at' in package and package['created_at']:
                if isinstance(package['created_at'], datetime):
                    package['created_at'] = package['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            # 获取优惠券类型信息
            coupon_types = get_coupon_types()
            
            # 构建返回数据
            result = {
                "success": True,
                "data": {
                    "package": package,
                    "coupon_types": coupon_types
                }
            }
            
            return jsonify(result)
    
    except Exception as e:
        print(f"获取套餐详情时出错: {e}")
        return jsonify({"success": False, "message": f"获取数据失败: {str(e)}"}), 500
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

# 添加/更新优惠券套餐API
@coupons_bp.route('/api/packages/save', methods=['POST'])
def save_package():
    """保存优惠券套餐（添加或更新）"""
    try:
        # 获取表单数据
        package_data = request.json
        if not package_data:
            return jsonify({"success": False, "message": "未接收到数据"}), 400
            
        package_id = package_data.get('id', 0)
        name = package_data.get('name', '')
        description = package_data.get('description', '')
        price = package_data.get('price', 0)
        original_price = package_data.get('original_price', 0)
        status = package_data.get('status', 1)
        validity_days = package_data.get('validity_days', 30)
        coupon_details = package_data.get('coupon_details', {})
        
        # 基本验证
        if not name or float(price) <= 0 or float(original_price) <= 0:
            return jsonify({"success": False, "message": "请填写完整的套餐信息"}), 400
            
        # 将优惠券详情转换为JSON字符串
        coupon_details_json = json.dumps(coupon_details)
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            if int(package_id) > 0:  # 更新
                cursor.execute("""
                    UPDATE coupon_packages 
                    SET name = %s, description = %s, price = %s, original_price = %s,
                        status = %s, validity_days = %s, coupon_details = %s
                    WHERE id = %s
                """, (
                    name, description, price, original_price,
                    status, validity_days, coupon_details_json, package_id
                ))
                message = "套餐更新成功"
            else:  # 新增
                cursor.execute("""
                    INSERT INTO coupon_packages 
                    (name, description, price, original_price, status, validity_days, coupon_details)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    name, description, price, original_price,
                    status, validity_days, coupon_details_json
                ))
                package_id = cursor.lastrowid
                message = "套餐创建成功"
                
            connection.commit()
            
            return jsonify({
                "success": True, 
                "message": message,
                "package_id": package_id
            })
    except Exception as e:
        print(f"保存套餐数据时出错: {e}")
        return jsonify({"success": False, "message": f"操作失败: {str(e)}"}), 500
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

# 获取所有优惠券类型API
@coupons_bp.route('/api/coupon_types')
def get_coupon_types_api():
    """获取所有优惠券类型列表"""
    try:
        coupon_types = get_coupon_types()
        return jsonify({
            "success": True,
            "data": coupon_types
        })
    except Exception as e:
        print(f"获取优惠券类型列表时出错: {e}")
        return jsonify({"success": False, "message": f"获取数据失败: {str(e)}"}), 500

# 优惠券套餐页面
@coupons_bp.route('/packages')
def packages():
    """从数据库获取优惠券套餐列表并显示"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
    # 获取优惠券套餐列表
            cursor.execute("""
                SELECT 
                    id, name, description, price, original_price, 
                    status, validity_days, coupon_details, sale_count, 
                    created_at
                FROM 
                    coupon_packages
                ORDER BY 
                    created_at DESC
            """)
            packages = cursor.fetchall()
            
            # 处理每个套餐中的优惠券明细数据
            for package in packages:
                # 解析JSON字符串为Python字典
                if isinstance(package['coupon_details'], str):
                    package['coupon_details'] = json.loads(package['coupon_details'])
                
                # 计算套餐中的优惠券总数量
                coupon_count = 0
                if package['coupon_details']:
                    for count in package['coupon_details'].values():
                        coupon_count += int(count)
                package['coupon_count'] = coupon_count
                
                # 格式化创建时间为字符串
                if 'created_at' in package and package['created_at']:
                    if isinstance(package['created_at'], datetime):
                        package['created_at'] = package['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    
    except Exception as e:
        print(f"获取优惠券套餐数据时出错: {e}")
        packages = []  # 出错时返回空列表
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
    
    return render_template('coupons/packages.html', packages=packages)

# 创建/编辑套餐页面
@coupons_bp.route('/packages/edit/<int:package_id>', methods=['GET', 'POST'])
def edit_package(package_id):
    if package_id == 0:  # 新建套餐
        package = {'id': 0, 'name': '', 'description': '', 'price': 0, 'coupons': [], 'validity_days': 30}
    else:
        package = next((p for p in coupon_packages if p['id'] == package_id), None)
        
    if request.method == 'POST':
        # 这里应该处理表单提交，但现在只是模拟
        flash('套餐保存成功！', 'success')
        return redirect(url_for('coupons.packages'))
        
    return render_template('coupons/package_edit.html', package=package)

# 活动管理页面
@coupons_bp.route('/activities')
def activities():
    return render_template('coupons/activities.html', activities=coupon_activities)

# 创建/编辑活动页面
@coupons_bp.route('/activities/edit/<int:activity_id>', methods=['GET', 'POST'])
def edit_activity(activity_id):
    if activity_id == 0:  # 新建活动
        activity = {
            'id': 0, 
            'name': '', 
            'start_time': datetime.now().strftime('%Y-%m-%d'),
            'end_time': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'trigger_type': '',
            'trigger_condition': ''
        }
    else:
        activity = next((a for a in coupon_activities if a['id'] == activity_id), None)
        
    if request.method == 'POST':
        # 这里应该处理表单提交，但现在只是模拟
        flash('活动保存成功！', 'success')
        return redirect(url_for('coupons.activities'))
        
    return render_template('coupons/activity_edit.html', activity=activity)

# 优惠券列表页面
@coupons_bp.route('/list')
def list():
    """获取优惠券列表，使用简化的表结构，关联优惠券类型表"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 构建查询条件
            conditions = []
            params = []
            
            # 获取过滤参数
            coupon_type = request.args.get('type', '')
            status = request.args.get('status', '')
            source = request.args.get('source', '')
            user_id = request.args.get('user_id', '')
            
            if coupon_type:
                conditions.append("ct.id = %s")
                params.append(coupon_type)
            
            if status:
                conditions.append("c.status = %s")
                params.append(status)
                
            if source:
                conditions.append("c.source = %s")
                params.append(source)
                
            if user_id:
                conditions.append("c.user_id = %s")
                params.append(user_id)
            
            # 构建查询SQL
            sql = """
                SELECT 
                    c.coupon_id, c.user_id, u.username as user_name, 
                    c.coupon_type_id, ct.type_name, ct.value, ct.min_amount, 
                    c.source, c.source_id,
                    c.receive_time, c.validity_start, c.validity_end, 
                    c.use_time, c.order_id, c.status
                FROM 
                    coupons c
                JOIN 
                    coupon_types ct ON c.coupon_type_id = ct.id
                JOIN 
                    users u ON c.user_id = u.user_id
            """
            
            # 添加条件
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
                
            # 添加排序
            sql += " ORDER BY c.receive_time DESC"
            
            # 添加分页
            page = request.args.get('page', 1, type=int)
            per_page = 20
            offset = (page - 1) * per_page
            
            # 获取总记录数
            count_sql = f"SELECT COUNT(*) as total FROM coupons c JOIN coupon_types ct ON c.coupon_type_id = ct.id JOIN users u ON c.user_id = u.user_id"
            if conditions:
                count_sql += " WHERE " + " AND ".join(conditions)
            
            cursor.execute(count_sql, params)
            total_count = cursor.fetchone()['total']
            
            # 加上分页限制
            sql += f" LIMIT {offset}, {per_page}"
            
            # 执行查询
            cursor.execute(sql, params)
            coupons = cursor.fetchall()
            
            # 处理日期时间格式
            for coupon in coupons:
                for date_field in ['receive_time', 'validity_start', 'validity_end', 'use_time']:
                    if coupon[date_field] and isinstance(coupon[date_field], datetime):
                        coupon[date_field] = coupon[date_field].strftime('%Y-%m-%d %H:%M:%S')
                
                # 格式化优惠券价值展示
                if 'type_name' in coupon and '折' in coupon['type_name']:
                    coupon['value_display'] = f"{coupon['value'] * 10}折"
                else:
                    coupon['value_display'] = f"¥{coupon['value']}"
            
            # 计算总页数
            total_pages = (total_count + per_page - 1) // per_page
            
            # 获取筛选条件下拉选项
            # 获取所有优惠券类型
            cursor.execute("SELECT id, type_name FROM coupon_types ORDER BY id")
            coupon_types = cursor.fetchall()
            
            # 获取所有来源类型
            cursor.execute("SELECT DISTINCT source FROM coupons")
            sources = [row['source'] for row in cursor.fetchall()]
            
            # 生成分页对象
            pagination = {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages,
                'prev_num': page - 1 if page > 1 else None,
                'next_num': page + 1 if page < total_pages else None,
                'iter_pages': range(max(1, page - 3), min(total_pages + 1, page + 4))
            }
            
            # 构建筛选参数
        filter_params = {
                    'type': coupon_type,
                    'status': status,
                    'source': source,
                    'user_id': user_id
        }
    
        return render_template('coupons/list.html', 
                            coupons=coupons,
                                    pagination=pagination,
                                    filter=filter_params,
                                    coupon_types=coupon_types,
                                    sources=sources,
                                    offset=offset)
            
    except Exception as e:
        print(f"获取优惠券列表时出错: {e}")
        return render_template('coupons/list.html', 
                              coupons=[],
                              error=f"加载数据失败: {str(e)}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

# 优惠券作废/延期操作
@coupons_bp.route('/operate/<int:coupon_id>', methods=['POST'])
def operate_coupon(coupon_id):
    """作废或延期优惠券"""
    try:
        operation = request.form.get('operation')
        if not operation:
            flash('未指定操作类型', 'danger')
            return redirect(url_for('admin.coupons.list'))
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 查询优惠券是否存在
            cursor.execute("SELECT * FROM coupons WHERE coupon_id = %s", (coupon_id,))
            coupon = cursor.fetchone()
            
            if not coupon:
                flash(f'优惠券 #{coupon_id} 不存在', 'danger')
                return redirect(url_for('admin.coupons.list'))
            
            if operation == 'invalidate':
                # 作废优惠券
                if coupon['status'] != '未使用':
                    flash(f'只能作废未使用的优惠券', 'warning')
                    return redirect(url_for('admin.coupons.list'))
                
                cursor.execute("""
                    UPDATE coupons 
                    SET status = '已过期', 
                        validity_end = NOW() 
                    WHERE coupon_id = %s
                """, (coupon_id,))
                
                connection.commit()
                flash(f'优惠券 #{coupon_id} 已成功作废', 'success')
                
            elif operation == 'extend':
                # 延期优惠券
                if coupon['status'] != '未使用':
                    flash(f'只能延期未使用的优惠券', 'warning')
                    return redirect(url_for('admin.coupons.list'))
                
                days = int(request.form.get('days', 7))
                if days <= 0:
                    flash(f'延期天数必须大于0', 'warning')
                    return redirect(url_for('admin.coupons.list'))
                
                cursor.execute("""
                    UPDATE coupons 
                    SET validity_end = DATE_ADD(validity_end, INTERVAL %s DAY)
                    WHERE coupon_id = %s
                """, (days, coupon_id))
                
                connection.commit()
                flash(f'优惠券 #{coupon_id} 已成功延期{days}天', 'success')
                
            else:
                flash(f'不支持的操作: {operation}', 'danger')
        
        return redirect(url_for('admin.coupons.list'))
        
    except Exception as e:
        flash(f'操作失败: {str(e)}', 'danger')
        return redirect(url_for('admin.coupons.list'))
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

# 优惠券详情页面
@coupons_bp.route('/detail/<int:coupon_id>')
def detail(coupon_id):
    """显示优惠券详情"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 获取优惠券信息及关联数据
            sql = """
                SELECT 
                    c.coupon_id, c.user_id, u.username as user_name, 
                    c.coupon_type_id, ct.type_name, ct.value, ct.min_amount, ct.description as type_description,
                    c.source, c.source_id, 
                    c.receive_time, c.validity_start, c.validity_end, 
                    c.use_time, c.order_id, c.status
                FROM 
                    coupons c
                JOIN 
                    coupon_types ct ON c.coupon_type_id = ct.id
                JOIN 
                    users u ON c.user_id = u.user_id
                WHERE 
                    c.coupon_id = %s
            """
            cursor.execute(sql, (coupon_id,))
            coupon = cursor.fetchone()
            
            if not coupon:
                flash(f'优惠券 #{coupon_id} 不存在', 'danger')
                return redirect(url_for('admin.coupons.list'))
            
            # 处理日期时间格式
            for date_field in ['receive_time', 'validity_start', 'validity_end', 'use_time']:
                if coupon[date_field] and isinstance(coupon[date_field], datetime):
                    coupon[date_field] = coupon[date_field].strftime('%Y-%m-%d %H:%M:%S')
            
            # 格式化优惠券价值展示
            if '折' in coupon['type_name']:
                coupon['value_display'] = f"{coupon['value'] * 10}折"
                coupon['discount_type'] = '折扣'
            else:
                coupon['value_display'] = f"¥{coupon['value']}"
                coupon['discount_type'] = '满减'
            
            # 如果是已使用的优惠券，获取订单信息
            order = None
            if coupon['status'] == '已使用' and coupon['order_id']:
                cursor.execute("""
                    SELECT * FROM orders WHERE order_number = %s
                """, (coupon['order_id'],))
                order = cursor.fetchone()
                
                if order and 'create_time' in order and isinstance(order['create_time'], datetime):
                    order['create_time'] = order['create_time'].strftime('%Y-%m-%d %H:%M:%S')
            
            # 如果来源是套餐购买，获取套餐信息
            package = None
            if coupon['source'] == '套餐购买' and coupon['source_id']:
                cursor.execute("""
                    SELECT * FROM coupon_packages WHERE id = %s
                """, (coupon['source_id'],))
                package = cursor.fetchone()
            
            return render_template('coupons/detail.html', 
                                  coupon=coupon,
                                  order=order,
                                  package=package)
    
    except Exception as e:
        flash(f'获取优惠券详情失败: {str(e)}', 'danger')
        return redirect(url_for('admin.coupons.list'))
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

# 使用统计页面
@coupons_bp.route('/statistics')
def statistics():
    """优惠券使用统计（更新为使用实际数据库数据）"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 获取基本统计数据
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_coupons,
                    SUM(CASE WHEN status = '已使用' THEN 1 ELSE 0 END) as used_coupons,
                    SUM(CASE WHEN status = '未使用' THEN 1 ELSE 0 END) as unused_coupons,
                    SUM(CASE WHEN status = '已过期' THEN 1 ELSE 0 END) as expired_coupons
                FROM coupons
            """)
            basic_stats = cursor.fetchone()
            
            # 计算使用率
            total = basic_stats['total_coupons']
            used = basic_stats['used_coupons']
            usage_rate = round((used / total) * 100, 1) if total > 0 else 0
            
            # 按类型统计
            cursor.execute("""
                SELECT 
                    ct.id, ct.type_name,
                    COUNT(c.coupon_id) as count,
                    SUM(CASE WHEN c.status = '已使用' THEN 1 ELSE 0 END) as used
                FROM 
                    coupons c
                JOIN 
                    coupon_types ct ON c.coupon_type_id = ct.id
                GROUP BY 
                    ct.id, ct.type_name
                ORDER BY 
                    count DESC
            """)
            type_stats = cursor.fetchall()
            
            # 计算各类型使用率
            for stat in type_stats:
                stat['rate'] = round((stat['used'] / stat['count']) * 100, 1) if stat['count'] > 0 else 0
            
            # 按来源统计
            cursor.execute("""
                SELECT 
                    c.source,
                    COUNT(c.coupon_id) as count,
                    SUM(CASE WHEN c.status = '已使用' THEN 1 ELSE 0 END) as used
                FROM 
                    coupons c
                GROUP BY 
                    c.source
                ORDER BY 
                    count DESC
            """)
            source_stats = cursor.fetchall()
            
            # 计算各来源使用率
            for stat in source_stats:
                stat['rate'] = round((stat['used'] / stat['count']) * 100, 1) if stat['count'] > 0 else 0
            
            # 按月份统计发放和使用情况
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(c.receive_time, '%Y-%m') as month,
                    COUNT(c.coupon_id) as issued,
                    SUM(CASE WHEN c.status = '已使用' THEN 1 ELSE 0 END) as used
                FROM 
                    coupons c
                WHERE 
                    c.receive_time >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                GROUP BY 
                    DATE_FORMAT(c.receive_time, '%Y-%m')
                ORDER BY 
                    month
            """)
            monthly_data = cursor.fetchall()
            
            # 格式化月份显示
            for item in monthly_data:
                year_month = item['month'].split('-')
                item['month_display'] = f"{year_month[0]}年{year_month[1]}月"
                item['month_short'] = f"{year_month[1]}月"
            
            # 构建完整的统计数据
        stats = {
                    'total_coupons': basic_stats['total_coupons'],
                    'used_coupons': basic_stats['used_coupons'],
                    'unused_coupons': basic_stats['unused_coupons'],
                    'expired_coupons': basic_stats['expired_coupons'],
                    'usage_rate': usage_rate,
                    'type_stats': type_stats,
                    'source_stats': source_stats,
                    'monthly_data': monthly_data
                }
                
        return render_template('coupons/statistics.html', 
                            stats=stats,
                            active_coupon_page='statistics')
            
    except Exception as e:
        print(f"获取优惠券统计数据时出错: {e}")
        # 返回空的统计数据
        stats = {
            'total_coupons': 0,
            'used_coupons': 0,
            'unused_coupons': 0,
            'expired_coupons': 0,
            'usage_rate': 0,
            'type_stats': [],
            'source_stats': [],
            'monthly_data': []
        }
        flash(f'获取统计数据失败: {str(e)}', 'danger')
        return render_template('coupons/statistics.html', 
                              stats=stats,
                              active_coupon_page='statistics',
                              error=True)
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

@coupons_bp.route('/campaigns')
def campaigns():
    # 获取活动列表
    campaign_list = [
        # 示例数据，实际项目中应从数据库获取
        {'id': 1, 'name': '新用户欢迎礼', 'type': '新用户注册', 'start_time': datetime.now(), 'end_time': datetime.now(), 'coupon_count': 1000, 'claimed_count': 500, 'status': '进行中'},
        {'id': 2, 'name': '中秋特惠', 'type': '节日促销', 'start_time': datetime.now(), 'end_time': datetime.now(), 'coupon_count': 800, 'claimed_count': 750, 'status': '已结束'},
        {'id': 3, 'name': '满100减20', 'type': '满额赠送', 'start_time': datetime.now(), 'end_time': datetime.now(), 'coupon_count': 500, 'claimed_count': 100, 'status': '进行中'},
    ]
    
    # 活动类型统计
    campaign_types = [
        {'type': '新用户注册', 'count': 5},
        {'type': '节日促销', 'count': 10},
        {'type': '满额赠送', 'count': 7},
        {'type': '限时折扣', 'count': 3},
    ]
    
    return render_template('coupons/campaigns.html', 
                          campaigns=campaign_list,
                          campaign_types=campaign_types,
                          active_coupon_page='campaigns')

# DataTables数据API接口
@coupons_bp.route('/data')
def data():
    """提供优惠券数据给DataTables服务器端处理"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 获取DataTables发送的参数
            draw = request.args.get('draw', '1')
            start = int(request.args.get('start', 0))
            length = int(request.args.get('length', 10))
            
            # 排序参数
            order_column_index = request.args.get('order[0][column]', 0)
            order_column_name = request.args.get(f'columns[{order_column_index}][data]', 'coupon_id')
            order_direction = request.args.get('order[0][dir]', 'desc')
            
            # 构建查询条件
            conditions = []
            params = []
            
            # 获取筛选参数
            coupon_type = request.args.get('type', '')
            status = request.args.get('status', '')
            source = request.args.get('source', '')
            user_id = request.args.get('user_id', '')
            
            if coupon_type:
                conditions.append("ct.id = %s")
                params.append(coupon_type)
            
            if status:
                conditions.append("c.status = %s")
                params.append(status)
                
            if source:
                conditions.append("c.source = %s")
                params.append(source)
                
            if user_id:
                conditions.append("c.user_id = %s")
                params.append(user_id)
            
            # DataTables搜索功能
            search_value = request.args.get('search[value]', '')
            if search_value:
                conditions.append("(c.coupon_id LIKE %s OR u.username LIKE %s OR ct.type_name LIKE %s OR c.source LIKE %s)")
                search_param = f"%{search_value}%"
                params.extend([search_param, search_param, search_param, search_param])
            
            # 构建查询SQL
            sql = """
                SELECT 
                    c.coupon_id, c.user_id, u.username as user_name, 
                    c.coupon_type_id, ct.type_name, ct.value, ct.min_amount, 
                    c.source, c.source_id,
                    c.receive_time, c.validity_start, c.validity_end, 
                    c.use_time, c.order_id, c.status
                FROM 
                    coupons c
                JOIN 
                    coupon_types ct ON c.coupon_type_id = ct.id
                JOIN 
                    users u ON c.user_id = u.user_id
            """
            
            # 添加条件
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
                
            # 获取总记录数(不带搜索)
            count_sql = "SELECT COUNT(*) as total FROM coupons c JOIN coupon_types ct ON c.coupon_type_id = ct.id JOIN users u ON c.user_id = u.user_id"
            if conditions:
                count_sql += " WHERE " + " AND ".join(conditions)
                
            cursor.execute(count_sql, params)
            total_count = cursor.fetchone()['total']
            
            # 处理排序
            # 安全处理排序列
            allowed_columns = {
                'coupon_id': 'c.coupon_id',
                'user_info': 'u.username',
                'type_name': 'ct.type_name',
                'value_display': 'ct.value',
                'condition': 'ct.min_amount',
                'source': 'c.source',
                'receive_time': 'c.receive_time',
                'validity_end': 'c.validity_end',
                'status_html': 'c.status'
            }
            # 默认排序
            order_by = "c.coupon_id DESC"
            if order_column_name in allowed_columns:
                order_by = f"{allowed_columns[order_column_name]} {order_direction}"
                
            sql += f" ORDER BY {order_by}"
            
            # 添加分页
            sql += f" LIMIT {start}, {length}"
            
            # 执行查询
            cursor.execute(sql, params)
            coupons = cursor.fetchall()
            
            # 处理数据格式供DataTables使用
            data = []
            for coupon in coupons:
                # 优惠券价值展示
                value_display = f"{coupon['value'] * 10}折" if '折' in coupon['type_name'] else f"¥{coupon['value']}"
                
                # 使用条件
                condition = f"满{coupon['min_amount']}元可用" if coupon['min_amount'] > 0 else "无门槛"
                
                # 格式化日期
                receive_time = coupon['receive_time'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(coupon['receive_time'], datetime) else coupon['receive_time']
                validity_end = coupon['validity_end'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(coupon['validity_end'], datetime) else coupon['validity_end']
                
                # 状态HTML显示
                status_class = "bg-success" if coupon['status'] == '未使用' else "bg-info" if coupon['status'] == '已使用' else "bg-secondary"
                status_html = f'<span class="badge {status_class}">{coupon["status"]}</span>'
                
                # 操作按钮HTML
                actions = f'<div class="btn-group btn-group-sm">'
                
                if coupon['status'] == '未使用':
                    actions += f'<button type="button" class="btn btn-outline-danger invalidate-btn" data-id="{coupon["coupon_id"]}"><i class="bi bi-x-circle"></i></button>'
                    actions += f'<button type="button" class="btn btn-outline-success extend-btn" data-id="{coupon["coupon_id"]}"><i class="bi bi-calendar-plus"></i></button>'
                
                actions += '</div>'
                
                # 用户信息
                user_info = f"{coupon['user_name']} (ID: {coupon['user_id']})"
                
                # 构建数据行
                row = {
                    'coupon_id': coupon['coupon_id'],
                    'user_info': user_info,
                    'type_name': coupon['type_name'],
                    'value_display': value_display,
                    'condition': condition,
                    'source': coupon['source'],
                    'receive_time': receive_time,
                    'validity_end': validity_end,
                    'status_html': status_html,
                    'actions': actions
                }
                data.append(row)
            
            # 返回DataTables需要的格式
            return jsonify({
                'draw': int(draw),
                'recordsTotal': total_count,
                'recordsFiltered': total_count,
                'data': data
            })
            
    except Exception as e:
        print(f"获取优惠券数据时出错: {e}")
        return jsonify({
            'draw': int(request.args.get('draw', '1')),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

# 优惠券种类管理
@coupons_bp.route('/types')
def types():
    """优惠券种类管理页面"""
    from app.models.coupon import CouponType
    
    # 获取所有优惠券种类
    coupon_types = CouponType.query.order_by(CouponType.id.desc()).all()
    
    return render_template('coupons/types.html', coupon_types=coupon_types)


@coupons_bp.route('/add_type', methods=['POST'])
def add_type():
    """添加优惠券种类"""
    from app.models.coupon import CouponType
    from app.extensions import db
    
    try:
        # 获取表单数据
        type_name = request.form.get('type_name')
        coupon_category = request.form.get('coupon_category')
        value = request.form.get('value')
        min_amount = request.form.get('min_amount', 0)
        description = request.form.get('description', '')
        
        # 数据验证
        if not type_name or not value or not coupon_category:
            return jsonify({'status': 'error', 'message': '类型名称、种类和面值不能为空'})
        
        # 检查是否已存在同名类型
        if CouponType.query.filter_by(type_name=type_name).first():
            return jsonify({'status': 'error', 'message': '同名优惠券种类已存在'})
        
        # 创建新优惠券种类
        new_type = CouponType(
            type_name=type_name,
            coupon_category=coupon_category,
            value=value,
            min_amount=min_amount,
            description=description
        )
        
        # 保存到数据库
        db.session.add(new_type)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '优惠券种类添加成功'})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"添加优惠券种类失败: {str(e)}")
        return jsonify({'status': 'error', 'message': f'系统错误: {str(e)}'})


@coupons_bp.route('/update_type', methods=['POST'])
def update_type():
    """更新优惠券种类"""
    from app.models.coupon import CouponType
    from app.extensions import db
    
    try:
        # 获取表单数据
        type_id = request.form.get('id')
        type_name = request.form.get('type_name')
        coupon_category = request.form.get('coupon_category')
        value = request.form.get('value')
        min_amount = request.form.get('min_amount', 0)
        description = request.form.get('description', '')
        
        # 数据验证
        if not type_id or not type_name or not value or not coupon_category:
            return jsonify({'status': 'error', 'message': '缺少必要参数'})
        
        # 查找要更新的优惠券种类
        coupon_type = CouponType.query.get(type_id)
        if not coupon_type:
            return jsonify({'status': 'error', 'message': '优惠券种类不存在'})
        
        # 检查是否已存在同名类型（排除自身）
        existing = CouponType.query.filter(CouponType.type_name == type_name, CouponType.id != type_id).first()
        if existing:
            return jsonify({'status': 'error', 'message': '同名优惠券种类已存在'})
        
        # 更新数据
        coupon_type.type_name = type_name
        coupon_type.coupon_category = coupon_category
        coupon_type.value = value
        coupon_type.min_amount = min_amount
        coupon_type.description = description
        
        # 保存到数据库
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '优惠券种类更新成功'})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新优惠券种类失败: {str(e)}")
        return jsonify({'status': 'error', 'message': f'系统错误: {str(e)}'})


@coupons_bp.route('/delete_type', methods=['POST'])
def delete_type():
    """删除优惠券种类"""
    from app.models.coupon import CouponType
    from app.extensions import db
    
    try:
        # 获取要删除的优惠券种类ID
        type_id = request.form.get('id')
        
        if not type_id:
            return jsonify({'status': 'error', 'message': '缺少必要参数'})
        
        # 查找要删除的优惠券种类
        coupon_type = CouponType.query.get(type_id)
        if not coupon_type:
            return jsonify({'status': 'error', 'message': '优惠券种类不存在'})
        
        # TODO: 检查是否有关联数据，如果有，可能需要提示用户或者级联删除
        
        # 从数据库中删除
        db.session.delete(coupon_type)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': '优惠券种类已删除'})
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除优惠券种类失败: {str(e)}")
        return jsonify({'status': 'error', 'message': f'系统错误: {str(e)}'})

def issue_coupons_to_user(conn, cursor, package, coupon_details, user_id):
    from datetime import datetime, timedelta
    
    now = datetime.now()
    
    # 首先定义package_id，确保在所有情况下都有值
    package_id = None
    
    # 设置优惠券有效期和获取package_id
    validity_days = 30  # 默认值
    if isinstance(package, dict):
        validity_days = package.get('validity_days', 30)
        package_id = package.get('id', 0)
    else:
        # 如果package是元组或列表
        try:
            package_id = package[0]  # 假设ID在第一个位置
            validity_days = package[6] if len(package) > 6 else 30  # 假设validity_days在第7个位置
        except (IndexError, TypeError):
            package_id = 0
            # 如果获取失败，使用默认值
    
    # 确保package_id有值
    if package_id is None:
        package_id = 0
    
    # 计算有效期
    validity_start = now
    validity_end = now + timedelta(days=validity_days)
    
    # 为用户发放每种优惠券
    for coupon_type_id, count in coupon_details.items():
        # 生成指定数量的优惠券
        for i in range(int(count)):
            try:
                # 使用表中实际存在的字段插入数据
                cursor.execute('''
                    INSERT INTO coupons 
                    (user_id, coupon_type_id, source, source_id, 
                     validity_start, validity_end, status) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (
                    user_id, 
                    coupon_type_id, 
                    '套餐购买', 
                    package_id,
                    validity_start,
                    validity_end,
                    '未使用'
                ))
            except Exception as e:
                print(f"插入优惠券失败: {str(e)}")
                # 尝试打印更详细的信息
                print(f"插入参数: user_id={user_id}, coupon_type_id={coupon_type_id}, " 
                      f"source='套餐购买', source_id={package_id}")

@coupons_bp.route('/buy_package', methods=['POST'])
def buy_package():
    try:
        # 获取请求数据
        data = request.json
        package_id = data.get('package_id')
        user_type = data.get('user_type')
        user_id = data.get('user_id')  # 当user_type为'all'时，这个值可能为None
        
        # 验证package_id是否有效
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查套餐是否存在
        cursor.execute('SELECT * FROM coupon_packages WHERE id = %s', (package_id,))
        package = cursor.fetchone()
        
        if not package:
            return jsonify({'success': False, 'message': '优惠券套餐不存在'})
        
        # 尝试直接使用package - 假设它已经是字典格式    
        try:
            # 如果是字典格式直接使用
            package_dict = package
            coupon_details = package_dict.get('coupon_details', '{}')
            price = package_dict.get('price', 0)  # 获取套餐价格
        except (TypeError, AttributeError):
            # 如果不是字典，尝试用索引访问
            try:
                # 尝试找到coupon_details的索引和price的索引
                cursor.execute('SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = "coupon_packages"')
                columns = cursor.fetchall()
                
                # 确定columns的格式并找到coupon_details的索引
                coupon_details_index = None
                price_index = None
                if isinstance(columns, list):
                    if columns and isinstance(columns[0], tuple):
                        column_names = [col[0] for col in columns]
                    elif columns and isinstance(columns[0], dict):
                        column_names = [col.get('COLUMN_NAME') for col in columns]
                    else:
                        column_names = columns
                    
                    try:
                        coupon_details_index = column_names.index('coupon_details')
                        coupon_details = package[coupon_details_index]
                        price_index = column_names.index('price')
                        price = package[price_index]
                    except (ValueError, IndexError):
                        coupon_details = '{}'
                        price = 0
                else:
                    coupon_details = '{}'
                    price = 0
            except Exception as e:
                print(f"尝试获取列名失败: {str(e)}")
                coupon_details = '{}'
                price = 0
        
        # 解析coupon_details
        import json
        if isinstance(coupon_details, str):
            coupon_details = json.loads(coupon_details)
        
        if not coupon_details:
            return jsonify({'success': False, 'message': '套餐中没有包含优惠券'})
        
        # 处理不同的用户类型
        if user_type == 'single':
            if not user_id:
                return jsonify({'success': False, 'message': '请选择用户'})
                
            # 检查用户是否存在
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return jsonify({'success': False, 'message': '所选用户不存在'})
            
            # 为单个用户发放优惠券
            issue_coupons_to_user(conn, cursor, package, coupon_details, user_id)
            
            # 尝试获取用户名
            try:
                if isinstance(user, dict):
                    username = user.get('username', str(user_id))
                else:
                    # 尝试用索引访问用户名
                    cursor.execute('SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = "users"')
                    user_columns = cursor.fetchall()
                    if user_columns and isinstance(user_columns[0], tuple):
                        column_names = [col[0] for col in user_columns]
                        try:
                            username_index = column_names.index('username')
                            username = user[username_index]
                        except (ValueError, IndexError):
                            username = str(user_id)
                    else:
                        username = str(user_id)
            except Exception:
                username = str(user_id)
                
            message = f'已成功为用户 {username} 购买套餐'
            
        elif user_type == 'all':
            # 获取所有用户
            cursor.execute('SELECT user_id FROM users')
            users = cursor.fetchall()
            
            if not users:
                return jsonify({'success': False, 'message': '系统中没有用户'})
            
            user_count = 0
            # 为所有用户发放优惠券
            for user in users:
                # 确定user_id的位置
                if isinstance(user, dict):
                    current_user_id = user.get('user_id')
                else:
                    current_user_id = user[0]  # 假设第一个元素是user_id
                
                if current_user_id:
                    issue_coupons_to_user(conn, cursor, package, coupon_details, current_user_id)
                    user_count += 1
                
            message = f'已成功为所有{user_count}位用户购买套餐'
        else:
            return jsonify({'success': False, 'message': '无效的用户类型'})
            
        # 更新套餐售出数量
        try:
            if user_type == 'single':
                # 单个用户购买，售出数量+1
                cursor.execute('UPDATE coupon_packages SET sale_count = sale_count + 1 WHERE id = %s', (package_id,))
            elif user_type == 'all':
                # 批量购买，售出数量+用户数量
                cursor.execute('UPDATE coupon_packages SET sale_count = sale_count + %s WHERE id = %s', (user_count, package_id,))
            
            # 添加收入记录
            from datetime import date
            today = date.today()
            
            if user_type == 'single':
                # 为单个用户添加收入记录
                cursor.execute("""
                    INSERT INTO income (amount, source, user_id, date, description)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    price,
                    '优惠券套餐购买',
                    user_id,
                    today,
                    f'用户{user_id}购买套餐"{package_dict.get("name", "未知套餐")}"'
                ))
            elif user_type == 'all':
                # 为批量购买添加收入记录
                cursor.execute("""
                    INSERT INTO income (amount, source, date, description)
                    VALUES (%s, %s, %s, %s)
                """, (
                    price * user_count,  # 总收入等于套餐价格乘以用户数
                    '其他',
                    today,
                    f'管理员为{user_count}位用户批量购买套餐"{package_dict.get("name", "未知套餐")}"'
                ))
            
            conn.commit()
        except Exception as e:
            print(f"更新售出数量或添加收入记录失败: {str(e)}")
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        # 打印详细错误信息以便调试
        import traceback
        print(f"购买套餐出错: {str(e)}")
        print(traceback.format_exc())
        if 'conn' in locals():
            conn.rollback()
        return jsonify({'success': False, 'message': f'处理购买请求时出错: {str(e)}'})
    finally:
        if 'conn' in locals():
            conn.close()

@coupons_bp.route('/users/api/list')
def get_users_list():
    """获取用户列表API，供选择用户时使用"""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        try:
            # 获取活跃用户列表，仅返回必要字段
            cursor.execute(
                "SELECT user_id, username, real_name, phone FROM users WHERE status = '正常' ORDER BY username LIMIT 500"
            )
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            
            # 将结果转换为字典列表
            users = []
            for row in rows:
                users.append(dict(zip(columns, row)))
            
            return jsonify({
                'success': True, 
                'data': users
            })
            
        except Exception as e:
            current_app.logger.error(f"获取用户列表时出错: {str(e)}")
            return jsonify({'success': False, 'message': f'获取用户列表失败: {str(e)}'})
            
        finally:
            cursor.close()
            
    except Exception as e:
        current_app.logger.error(f"连接数据库出错: {str(e)}")
        return jsonify({'success': False, 'message': f'系统错误: {str(e)}'})
        
    finally:
        if 'connection' in locals() and connection.open:
            connection.close() 