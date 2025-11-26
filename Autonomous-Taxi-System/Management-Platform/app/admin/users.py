from flask import Blueprint, render_template, request, redirect, url_for, jsonify, send_file, Response, flash
from app.models import User
from app import db
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import io
import tempfile
import os
from sqlalchemy.sql import func
from app.utils.flash_helper import flash_success, flash_error, flash_warning, flash_info, flash_add_success, flash_update_success, flash_delete_success

# 导入PDF生成相关库
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 设置Matplotlib后端，避免需要GUI

# 注册中文字体
try:
    # 尝试注册Windows系统中的宋体（添加详细的错误日志）
    try:
        pdfmetrics.registerFont(TTFont('SimSun', 'C:/Windows/Fonts/simsun.ttc'))
        print("成功注册宋体")
        CHINESE_FONT_REGISTERED = True
    except Exception as e:
        print(f"注册宋体失败: {str(e)}")
        # 尝试注册黑体
        try:
            pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
            print("成功注册黑体")
            CHINESE_FONT_REGISTERED = True
        except Exception as e:
            print(f"注册黑体失败: {str(e)}")
            # 尝试注册楷体
            try:
                pdfmetrics.registerFont(TTFont('SimKai', 'C:/Windows/Fonts/simkai.ttf'))
                print("成功注册楷体")
                CHINESE_FONT_REGISTERED = True
            except Exception as e:
                print(f"注册楷体失败: {str(e)}")
                # 尝试注册粗体宋体
                try:
                    pdfmetrics.registerFont(TTFont('SimSunB', 'C:/Windows/Fonts/simsunb.ttf'))
                    print("成功注册粗体宋体")
                    CHINESE_FONT_REGISTERED = True
                except Exception as e:
                    print(f"注册粗体宋体失败: {str(e)}")
                    CHINESE_FONT_REGISTERED = False
except Exception as e:
    print(f"中文字体注册过程中发生错误: {str(e)}")
    CHINESE_FONT_REGISTERED = False

# 设置默认中文字体名称
CHINESE_FONT_NAME = 'SimSun'  # 默认为宋体
if CHINESE_FONT_REGISTERED:
    if 'SimSun' in pdfmetrics.getRegisteredFontNames():
        CHINESE_FONT_NAME = 'SimSun'
    elif 'SimHei' in pdfmetrics.getRegisteredFontNames():
        CHINESE_FONT_NAME = 'SimHei'
    elif 'SimKai' in pdfmetrics.getRegisteredFontNames():
        CHINESE_FONT_NAME = 'SimKai'
    elif 'SimSunB' in pdfmetrics.getRegisteredFontNames():
        CHINESE_FONT_NAME = 'SimSunB'
    print(f"使用中文字体: {CHINESE_FONT_NAME}")
else:
    print("未能注册中文字体，PDF中的中文可能无法正确显示")

# 创建蓝图
users_bp = Blueprint('users', __name__, url_prefix='/users')

# 用户列表页面
@users_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    users = User.query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 检查是否是AJAX请求
    is_ajax = request.args.get('ajax') == '1'
    include_stats = request.args.get('include_stats') == '1'
    
    # 字段名称映射，用于显示搜索标签
    field_names = {
        'user_id': '用户ID',
        'username': '用户名',
        'real_name': '真实姓名',
        'phone': '手机号',
        'email': '邮箱',
        'gender': '性别',
        'status': '状态',
        'credit_score_min': '最低信用分',
        'credit_score_max': '最高信用分',
        'balance_min': '最低余额',
        'balance_max': '最高余额',
        'registration_time_start': '注册时间(开始)',
        'registration_time_end': '注册时间(结束)',
        'registration_city': '注册城市',
        'tags': '用户标签',
        'registration_channel': '注册渠道',
    }
    
    if is_ajax:
        # 准备AJAX响应
        response_data = {
            'html': render_template('users/_user_table.html', 
                                   users=users, 
                                   search_params={})
        }
        
        # 如果需要，添加统计数据
        if include_stats:
            response_data['stats'] = {
                'total': users.total
            }
        
        return jsonify(response_data)
    
    # 常规页面请求
    return render_template('users/index.html', 
                         users=users, 
                         search_params={},
                         field_names=field_names)

# 获取用户详情API
@users_bp.route('/details/<int:user_id>')
def get_user_details(user_id):
    user = User.query.get_or_404(user_id)
    user_data = user.to_dict()
    
    # 将标签字符串转换为列表（如果存在）
    if user_data.get('tags'):
        user_data['tags'] = user_data['tags'].split(',')
    
    return jsonify({
        'success': True,
        'user': user_data
    })

# 导出用户数据到Excel
@users_bp.route('/export')
def export_users():
    users = User.query.all()
    users_data = [user.to_dict() for user in users]
    
    df = pd.DataFrame(users_data)
    # 重命名列
    df = df.rename(columns={
        'user_id': 'ID',
        'username': '用户名',
        'real_name': '真实姓名',
        'phone': '手机号',
        'email': '邮箱',
        'gender': '性别',
        'birth_date': '出生日期',
        'id_card': '身份证号',
        'credit_score': '信用分',
        'balance': '账户余额',
        'registration_time': '注册时间',
        'status': '状态',
        'last_login_time': '最后登录时间',
        'created_at': '创建时间',
        'updated_at': '更新时间'
    })
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='用户数据')
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'用户数据_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )

# 添加用户页面
@users_bp.route('/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        try:
            user = User(
                username=request.form['username'],
                password=request.form['password'],
                real_name=request.form['real_name'],
                phone=request.form['phone'],
                email=request.form['email'],
                gender=request.form['gender'],
                birth_date=datetime.strptime(request.form['birth_date'], '%Y-%m-%d') if request.form['birth_date'] else None,
                id_card=request.form['id_card'],
                credit_score=int(request.form['credit_score']),
                balance=float(request.form['balance']),
                registration_city=request.form['registration_city'],
                registration_channel=request.form['registration_channel'],
                tags=request.form['tags'],
                status=request.form['status']
            )
            db.session.add(user)
            db.session.commit()
            flash_success('用户添加成功！')
            return redirect(url_for('users.index'))
        except Exception as e:
            return redirect(url_for('users.add_user'))
    return render_template('users/add_user.html')

# 编辑用户页面
@users_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    # 获取返回页码
    page = request.args.get('page', '1')
    
    # 获取所有搜索参数
    search_params = {}
    for key, value in request.args.items():
        if key != 'page' and key != 'per_page':
            search_params[key] = value
    
    if request.method == 'POST':
        try:
            user.username = request.form['username']
            user.real_name = request.form['real_name']
            user.phone = request.form['phone']
            user.email = request.form['email']
            user.gender = request.form['gender']
            user.birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d') if request.form['birth_date'] else None
            user.id_card = request.form['id_card']
            user.credit_score = int(request.form['credit_score'])
            user.balance = float(request.form['balance'])
            user.registration_city = request.form['registration_city']
            user.registration_channel = request.form['registration_channel']
            user.tags = request.form['tags']
            user.status = request.form['status']
            
            # 获取表单中的页码
            page = request.form.get('page', '1')
            
            db.session.commit()
            
            # 检查是否是AJAX请求
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            if is_ajax:
                # 获取最新的用户总数
                total_users = User.query.count()
                
                # 返回JSON响应
                return jsonify({
                    'success': True,
                    'message': '用户信息更新成功！',
                    'user': user.to_dict(),
                    'stats': {
                        'total': total_users
                    }
                })
            else:
                flash_success('用户信息更新成功！')
                
                # 如果存在搜索参数，返回到搜索结果页面
                if search_params:
                    # 将页码添加到搜索参数中
                    params = search_params.copy()
                    params['page'] = page
                    return redirect(url_for('users.advanced_search', **params))
                else:
                    return redirect(url_for('users.index', page=page))
        except Exception as e:
            # 如果出现异常，回滚事务
            db.session.rollback()
            
            # 检查是否是AJAX请求
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': f'更新用户失败：{str(e)}'
                }), 400
            else:
                flash_error(f'更新用户失败：{str(e)}')
                if search_params:
                    redirect_url = url_for('users.edit_user', user_id=user_id, page=page, **search_params)
                else:
                    redirect_url = url_for('users.edit_user', user_id=user_id, page=page)
                return redirect(redirect_url)
    
    # 将搜索参数传递给模板，用于返回按钮
    search_query_string = '&'.join([f"{key}={value}" for key, value in search_params.items()]) if search_params else ''
    
    return render_template('users/edit_user.html', user=user, page=page, 
                          search_params=search_params,
                          search_query_string=search_query_string)

# 删除用户
@users_bp.route('/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    try:
        # 获取用户信息
        user = User.query.get_or_404(user_id)
        username = user.username  # 保存用户名，用于消息提示
        
        # 直接删除用户,不需要处理vehicle_logs表,因为没有关联关系
        db.session.delete(user)
        db.session.commit()
        
        # 检查是否是AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            # 获取当前用户总数
            total_count = User.query.count()
            
            # AJAX响应
            return jsonify({
                'success': True,
                'message': f'用户 {username} 已成功删除',
                'stats': {
                    'total': total_count
                }
            })
        else:
            # 传统表单提交的响应
            flash_success(f'用户 {username} 已成功删除')
            
            # 获取返回页码，如果没有则默认为1
            page = request.args.get('page', '1')
            
            # 获取所有搜索参数
            search_params = {}
            for key, value in request.args.items():
                if key != 'page' and key != 'per_page':
                    search_params[key] = value
            
            # 如果存在搜索参数，返回到搜索结果页面
            if search_params:
                # 将页码添加到搜索参数中
                params = search_params.copy()
                params['page'] = page
                return redirect(url_for('users.advanced_search', **params))
            else:
                return redirect(url_for('users.index', page=page))
    except Exception as e:
        # 发生错误时回滚事务
        db.session.rollback()
        
        # 记录错误详情
        error_message = f"删除用户出错: {str(e)}"
        print(error_message)
        import traceback
        traceback.print_exc()
        
        # 检查是否是AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            return jsonify({
                'success': False,
                'message': f'删除用户失败: {str(e)}'
            }), 500
        else:
            flash_error(f'删除用户失败: {str(e)}')
            return redirect(url_for('users.index'))

# 搜索用户
@users_bp.route('/search')
def search_user():
    query = request.args.get('query', '')
    users = User.query.filter(
        (User.username.contains(query)) |
        (User.real_name.contains(query)) |
        (User.phone.contains(query)) |
        (User.email.contains(query))
    ).all()
    
    # 字段名称映射，用于显示搜索标签
    field_names = {
        'user_id': '用户ID',
        'username': '用户名',
        'real_name': '真实姓名',
        'phone': '手机号',
        'email': '邮箱',
        'gender': '性别',
        'status': '状态',
        'credit_score_min': '最低信用分',
        'credit_score_max': '最高信用分',
        'balance_min': '最低余额',
        'balance_max': '最高余额',
        'registration_time_start': '注册时间(开始)',
        'registration_time_end': '注册时间(结束)',
        'registration_city': '注册城市',
        'tags': '用户标签',
        'registration_channel': '注册渠道',
    }
    
    # 构建搜索参数
    search_params = {'query': query} if query else {}
    
    return render_template('users/index.html', 
                          users=users, 
                          search_query=query,
                          search_params=search_params,
                          field_names=field_names)

# 高级搜索用户
@users_bp.route('/advanced_search')
def advanced_search():
    """高级搜索功能，支持多条件组合查询用户"""
    # 获取所有搜索参数
    search_params = {}
    query = User.query
    
    # 用户ID搜索
    user_id = request.args.get('user_id', '')
    if user_id:
        search_params['user_id'] = user_id
        query = query.filter(User.user_id == user_id)
    
    # 用户名搜索
    username = request.args.get('username', '')
    if username:
        search_params['username'] = username
        query = query.filter(User.username.contains(username))
    
    # 真实姓名搜索
    real_name = request.args.get('real_name', '')
    if real_name:
        search_params['real_name'] = real_name
        query = query.filter(User.real_name.contains(real_name))
    
    # 手机号搜索
    phone = request.args.get('phone', '')
    if phone:
        search_params['phone'] = phone
        query = query.filter(User.phone.contains(phone))
    
    # 邮箱搜索
    email = request.args.get('email', '')
    if email:
        search_params['email'] = email
        query = query.filter(User.email.contains(email))
    
    # 身份证号搜索
    id_card = request.args.get('id_card', '')
    if id_card:
        search_params['id_card'] = id_card
        query = query.filter(User.id_card.contains(id_card))
    
    # 状态搜索
    status = request.args.get('status', '')
    if status:
        search_params['status'] = status
        query = query.filter(User.status == status)
    
    # 性别搜索
    gender = request.args.get('gender', '')
    if gender:
        search_params['gender'] = gender
        query = query.filter(User.gender == gender)
    
    # 信用分范围搜索
    credit_score_min = request.args.get('credit_score_min', '')
    if credit_score_min:
        search_params['credit_score_min'] = credit_score_min
        query = query.filter(User.credit_score >= int(credit_score_min))
    
    credit_score_max = request.args.get('credit_score_max', '')
    if credit_score_max:
        search_params['credit_score_max'] = credit_score_max
        query = query.filter(User.credit_score <= int(credit_score_max))
    
    # 余额范围搜索
    balance_min = request.args.get('balance_min', '')
    if balance_min:
        search_params['balance_min'] = balance_min
        query = query.filter(User.balance >= float(balance_min))
    
    balance_max = request.args.get('balance_max', '')
    if balance_max:
        search_params['balance_max'] = balance_max
        query = query.filter(User.balance <= float(balance_max))
    
    # 注册时间范围搜索
    registration_time_start = request.args.get('registration_time_start', '')
    if registration_time_start:
        search_params['registration_time_start'] = registration_time_start
        start_date = datetime.strptime(registration_time_start, '%Y-%m-%d')
        query = query.filter(User.registration_time >= start_date)
    
    registration_time_end = request.args.get('registration_time_end', '')
    if registration_time_end:
        search_params['registration_time_end'] = registration_time_end
        end_date = datetime.strptime(registration_time_end, '%Y-%m-%d')
        # 设置为当天的最后一秒
        end_date = end_date.replace(hour=23, minute=59, second=59)
        query = query.filter(User.registration_time <= end_date)
    
    # 注册城市搜索
    registration_city = request.args.get('registration_city', '')
    if registration_city:
        search_params['registration_city'] = registration_city
        query = query.filter(User.registration_city.contains(registration_city))
    
    # 用户标签搜索
    tags = request.args.get('tags', '')
    if tags:
        search_params['tags'] = tags
        query = query.filter(User.tags.contains(tags))
    
    # 注册渠道搜索
    registration_channel = request.args.get('registration_channel', '')
    if registration_channel:
        search_params['registration_channel'] = registration_channel
        query = query.filter(User.registration_channel == registration_channel)
    
    # 分页
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    users = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 字段名称映射，用于显示搜索标签
    field_names = {
        'user_id': '用户ID',
        'username': '用户名',
        'real_name': '真实姓名',
        'phone': '手机号',
        'email': '邮箱',
        'gender': '性别',
        'status': '状态',
        'credit_score_min': '最低信用分',
        'credit_score_max': '最高信用分',
        'balance_min': '最低余额',
        'balance_max': '最高余额',
        'registration_time_start': '注册时间(开始)',
        'registration_time_end': '注册时间(结束)',
        'registration_city': '注册城市',
        'tags': '用户标签',
        'registration_channel': '注册渠道',
    }
    
    # 检查是否是AJAX请求
    is_ajax = request.args.get('ajax') == '1'
    include_stats = request.args.get('include_stats') == '1'
    
    if is_ajax:
        # 准备AJAX响应
        response_data = {
            'html': render_template('users/_user_table.html', 
                                   users=users, 
                                   search_params=search_params)
        }
        
        # 如果需要，添加统计数据
        if include_stats:
            response_data['stats'] = {
                'total': users.total
            }
        
        return jsonify(response_data)
    
    # 常规页面请求
    return render_template('users/index.html', 
                          users=users, 
                          search_params=search_params,
                          field_names=field_names)

# 用户数据分析页面
@users_bp.route('/analytics')
def analytics():
    """用户数据分析页面"""
    try:
        # 获取分析数据
        analytics_data = get_analytics_data()
        
        # 获取中国地图GeoJSON数据
        china_map_geo = get_china_geo_json()
        
        return render_template('users/analytics.html', 
                            analytics_data=analytics_data,
                            china_map_geo=china_map_geo)
    except Exception as e:
        flash_error(f'加载分析数据时出错: {str(e)}')
        return redirect(url_for('users.index'))

def calculate_user_tags():
    """计算用户标签分布"""
    # 获取所有有标签的用户
    users_with_tags = User.query.filter(User.tags.isnot(None)).all()
    
    # 统计各标签出现次数
    tag_counts = {}
    for user in users_with_tags:
        if not user.tags:
            continue
            
        # 将标签以逗号分隔
        user_tags = user.tags.split(',')
        for tag in user_tags:
            tag = tag.strip()
            if tag:
                if tag in tag_counts:
                    tag_counts[tag] += 1
                else:
                    tag_counts[tag] = 1
    
    # 转换为前端需要的格式并按出现次数排序
    result = [{"name": tag, "count": count} for tag, count in tag_counts.items()]
    result.sort(key=lambda x: x['count'], reverse=True)
    
    # 只返回前50个标签
    return result[:50]

def calculate_retention_rates():
    """计算最近6个月的用户留存率数据"""
    now = datetime.now()
    retention_data = {
        'months': [],
        'one_month_retention': [],
        'three_month_retention': [],
        'six_month_retention': []
    }
    
    # 计算最近6个月的月份标签
    for i in range(5, -1, -1):
        # 生成月份标签
        month_label = f'{6-i}个月前'
        retention_data['months'].append(month_label)
        
        # 当前月份的起始日期
        current_month_date = now.replace(day=1) - relativedelta(months=i)
        
        # 计算本月对应的过去30天区间
        last_30_days_end = now
        if i > 0:  # 非当前月需要往前推
            last_30_days_end = now - relativedelta(months=i)
        last_30_days_start = last_30_days_end - timedelta(days=30)
        
        # 计算1个月留存：30-60天前注册的用户中，最近30天内有登录记录的比例
        one_month_reg_start = last_30_days_start - timedelta(days=30)  # 60天前
        one_month_reg_end = last_30_days_start  # 30天前
        
        users_30_60_days_ago = User.query.filter(
            User.registration_time >= one_month_reg_start,
            User.registration_time < one_month_reg_end
        ).count()
        
        retained_one_month = User.query.filter(
            User.registration_time >= one_month_reg_start,
            User.registration_time < one_month_reg_end,
            User.last_login_time >= last_30_days_start,
            User.last_login_time <= last_30_days_end
        ).count()
        
        one_month_rate = round((retained_one_month / users_30_60_days_ago) * 100, 1) if users_30_60_days_ago > 0 else 0
        retention_data['one_month_retention'].append(one_month_rate)
        
        # 计算3个月留存：90-120天前注册的用户中，最近30天内有登录记录的比例
        three_month_reg_start = last_30_days_start - timedelta(days=90)  # 120天前
        three_month_reg_end = last_30_days_start - timedelta(days=60)  # 90天前
        
        users_90_120_days_ago = User.query.filter(
            User.registration_time >= three_month_reg_start,
            User.registration_time < three_month_reg_end
        ).count()
        
        retained_three_month = User.query.filter(
            User.registration_time >= three_month_reg_start,
            User.registration_time < three_month_reg_end,
            User.last_login_time >= last_30_days_start,
            User.last_login_time <= last_30_days_end
        ).count()
        
        three_month_rate = round((retained_three_month / users_90_120_days_ago) * 100, 1) if users_90_120_days_ago > 0 else 0
        retention_data['three_month_retention'].append(three_month_rate)
        
        # 计算6个月留存：180-210天前注册的用户中，最近30天内有登录记录的比例
        six_month_reg_start = last_30_days_start - timedelta(days=180)  # 210天前
        six_month_reg_end = last_30_days_start - timedelta(days=150)  # 180天前
        
        users_180_210_days_ago = User.query.filter(
            User.registration_time >= six_month_reg_start,
            User.registration_time < six_month_reg_end
        ).count()
        
        retained_six_month = User.query.filter(
            User.registration_time >= six_month_reg_start,
            User.registration_time < six_month_reg_end,
            User.last_login_time >= last_30_days_start,
            User.last_login_time <= last_30_days_end
        ).count()
        
        six_month_rate = round((retained_six_month / users_180_210_days_ago) * 100, 1) if users_180_210_days_ago > 0 else 0
        retention_data['six_month_retention'].append(six_month_rate)
    
    return retention_data

def get_analytics_data():
    """获取用户数据分析所需的数据"""
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)
    ninety_days_ago = now - timedelta(days=90)
    last_year = now - timedelta(days=365)
    
    # 计算当前月份和年份
    current_month = now.month
    current_year = now.year
    
    # 计算用户总数和同比增长率
    total_users = User.query.count()
    users_last_year = User.query.filter(User.registration_time <= last_year).count()
    if users_last_year > 0:
        yoy_growth = round(((total_users - users_last_year) / users_last_year) * 100, 1)
    else:
        yoy_growth = 100
    
    # 计算本月新增用户数和环比增长率
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    new_users_this_month = User.query.filter(User.registration_time >= this_month_start).count()
    new_users_last_month = User.query.filter(User.registration_time >= last_month_start,
                                           User.registration_time < this_month_start).count()
    
    if new_users_last_month > 0:
        mom_growth = round(((new_users_this_month - new_users_last_month) / new_users_last_month) * 100, 1)
    else:
        mom_growth = 100
    
    # 计算用户活跃率
    active_users = User.query.filter(User.last_login_time >= thirty_days_ago).count()
    if total_users > 0:
        activity_rate = round((active_users / total_users) * 100, 1)
    else:
        activity_rate = 0
    
    # 计算上个月的活跃率，用于环比计算
    active_users_last_month = User.query.filter(User.last_login_time >= sixty_days_ago, 
                                              User.last_login_time < thirty_days_ago).count()
    users_last_month = User.query.filter(User.registration_time < thirty_days_ago).count()
    
    if users_last_month > 0:
        activity_rate_last_month = (active_users_last_month / users_last_month) * 100
        activity_rate_change = round(activity_rate - activity_rate_last_month, 1)
    else:
        activity_rate_change = 0
    
    # 计算用户留存率
    users_30_60_days_ago = User.query.filter(User.registration_time >= sixty_days_ago,
                                           User.registration_time < thirty_days_ago).count()
    retained_users = User.query.filter(User.registration_time >= sixty_days_ago,
                                     User.registration_time < thirty_days_ago,
                                     User.last_login_time >= thirty_days_ago).count()
    
    if users_30_60_days_ago > 0:
        retention_rate = round((retained_users / users_30_60_days_ago) * 100, 1)
    else:
        retention_rate = 0
    
    # 计算上个月的留存率，用于环比计算
    users_60_90_days_ago = User.query.filter(User.registration_time >= ninety_days_ago,
                                           User.registration_time < sixty_days_ago).count()
    retained_users_last_month = User.query.filter(User.registration_time >= ninety_days_ago,
                                                User.registration_time < sixty_days_ago,
                                                User.last_login_time >= sixty_days_ago,
                                                User.last_login_time < thirty_days_ago).count()
    
    if users_60_90_days_ago > 0:
        retention_rate_last_month = (retained_users_last_month / users_60_90_days_ago) * 100
        retention_rate_change = round(retention_rate - retention_rate_last_month, 1)
    else:
        retention_rate_change = 0
    
    # 生成近12个月用户增长趋势数据
    growth_trend_data = generate_growth_trend_data()
    
    # 计算用户注册渠道分布
    channel_distribution = calculate_channel_distribution()
    
    # 计算用户年龄分布
    age_distribution = calculate_age_distribution()
    
    # 计算用户性别分布
    gender_distribution = calculate_gender_distribution()
    
    # 计算用户信用分分布
    credit_score_distribution = calculate_credit_score_distribution()
    
    # 计算用户地理分布
    geographic_distribution = calculate_geographic_distribution()
    
    # 计算用户标签分布
    user_tags = calculate_user_tags()
    
    # 计算用户留存率数据
    retention_data = calculate_retention_rates()
    
    # 返回所有数据
    return {
        'total_users': total_users,
        'yoy_growth': yoy_growth,
        'new_users_this_month': new_users_this_month,
        'mom_growth': mom_growth,
        'activity_rate': activity_rate,
        'activity_rate_change': activity_rate_change,
        'retention_rate': retention_rate,
        'retention_rate_change': retention_rate_change,
        'growth_trend_data': growth_trend_data,
        'channel_distribution': channel_distribution,
        'age_distribution': age_distribution,
        'gender_distribution': gender_distribution,
        'credit_score_distribution': credit_score_distribution,
        'geographic_distribution': geographic_distribution,
        'user_tags': user_tags,
        'retention_data': retention_data
    }

def generate_growth_trend_data():
    """生成近12个月用户增长趋势数据"""
    now = datetime.now()
    months = []
    new_users = []
    active_users = []
    
    for i in range(11, -1, -1):
        # 计算月份
        month_date = now.replace(day=1) - relativedelta(months=i)
        next_month = month_date + relativedelta(months=1)
        
        # 添加月份标签
        month_label = month_date.strftime('%Y年%m月')
        months.append(month_label)
        
        # 计算该月新增用户数
        month_new_users = User.query.filter(
            User.registration_time >= month_date,
            User.registration_time < next_month
        ).count()
        new_users.append(month_new_users)
        
        # 计算该月活跃用户数
        month_active_users = User.query.filter(
            User.last_login_time >= month_date,
            User.last_login_time < next_month
        ).count()
        active_users.append(month_active_users)
    
    return {
        'months': months,
        'new_users': new_users,
        'active_users': active_users
    }

def calculate_channel_distribution():
    """计算用户注册渠道分布"""
    channels = ['手机应用', '网站', '微信小程序', '合作推广', '其他']
    counts = []
    
    for channel in channels:
        count = User.query.filter(User.registration_channel == channel).count()
        counts.append(count)
    
    return {
        'channels': channels,
        'counts': counts
    }

def calculate_age_distribution():
    """计算用户年龄分布"""
    labels = ['18-24岁', '25-34岁', '35-44岁', '45-54岁', '55岁以上']
    data = [0, 0, 0, 0, 0]
    
    users = User.query.all()
    for user in users:
        if not user.birth_date:
            continue
            
        age = (datetime.now().date() - user.birth_date).days // 365
        
        if 18 <= age <= 24:
            data[0] += 1
        elif 25 <= age <= 34:
            data[1] += 1
        elif 35 <= age <= 44:
            data[2] += 1
        elif 45 <= age <= 54:
            data[3] += 1
        elif age >= 55:
            data[4] += 1
    
    return {
        'labels': labels,
        'data': data
    }

def calculate_gender_distribution():
    """计算用户性别分布"""
    male_count = User.query.filter(User.gender == '男').count()
    female_count = User.query.filter(User.gender == '女').count()
    other_count = User.query.filter(User.gender == '其他').count()
    
    total = male_count + female_count + other_count
    if total > 0:
        male_percent = round((male_count / total) * 100, 1)
        female_percent = round((female_count / total) * 100, 1)
        other_percent = round((other_count / total) * 100, 1)
    else:
        male_percent = female_percent = other_percent = 0
    
    return {
        'labels': ['男性', '女性', '其他'],
        'data': [male_percent, female_percent, other_percent]
    }

def calculate_credit_score_distribution():
    """计算用户信用分分布"""
    labels = ['0-30', '31-60', '61-90', '91-120', '121-150']
    data = [0, 0, 0, 0, 0]
    
    users = User.query.all()
    for user in users:
        score = user.credit_score or 0
        
        if score < 30:
            data[0] += 1
        elif 30 <= score < 60:
            data[1] += 1
        elif 60 <= score < 90:
            data[2] += 1
        elif 90 <= score < 120:
            data[3] += 1
        elif score >= 120:
            data[4] += 1
    
    return {
        'labels': labels,
        'data': data
    }

def calculate_geographic_distribution():
    """计算用户地理分布"""
    # 获取所有有注册城市的用户
    users_with_location = User.query.filter(User.registration_city.isnot(None)).all()
    
    # 城市到省份的映射表
    city_to_province = {
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
        '西安市': '陕西省',
        # 可以添加更多城市到省份的映射
    }
    
    # 省份名称映射（转换为地图要求的名称格式）
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
        '澳门': '澳门特别行政区'
    }
    
    # 统计各省份用户数量
    province_counts = {}
    for user in users_with_location:
        city = user.registration_city
        if not city:
            continue
            
        # 先通过城市到省份的映射表转换为省份
        province = city_to_province.get(city)
        
        # 如果城市不在映射表中，尝试直接使用（可能本身就是省份）
        if not province:
            province = city
            
        # 再通过省份映射表转换为标准格式
        mapped_province = province_name_map.get(province, province)
        
        if mapped_province in province_counts:
            province_counts[mapped_province] += 1
        else:
            province_counts[mapped_province] = 1
    
    # 转换为前端需要的格式
    result = [{"name": province, "value": count} for province, count in province_counts.items()]
    
    return result

def get_china_geo_json():
    """
    获取中国地图GeoJSON数据
    使用更精确的坐标点来描述中国地图的轮廓
    """
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "china",
                "properties": {"name": "中国"},
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        # 中国大陆主体
                        [[
                            [73.5, 34.3], [73.5, 40.0], [80.0, 45.0], [88.0, 49.1], 
                            [96.4, 49.1], [96.4, 44.0], [90.0, 40.0], [84.0, 34.3], 
                            [78.0, 31.0], [73.5, 34.3]
                        ]],
                        # 东北地区
                        [[
                            [121.2, 43.4], [121.2, 46.0], [124.0, 48.0], [127.0, 50.0], 
                            [131.0, 51.5], [135.1, 53.6], [135.1, 50.0], [133.0, 48.0], 
                            [131.0, 47.0], [129.0, 45.5], [127.0, 44.5], [124.0, 43.4], 
                            [121.2, 43.4]
                        ]],
                        # 华北地区
                        [[
                            [114.5, 36.0], [114.2, 38.0], [114.5, 40.5], [116.0, 42.5], 
                            [117.5, 42.5], [119.5, 42.0], [119.5, 40.0], [118.5, 38.0], 
                            [119.0, 36.0], [116.0, 36.5], [114.5, 36.0]
                        ]],
                        # 华东地区
                        [[
                            [116.3, 30.8], [116.3, 32.5], [117.5, 34.0], [118.5, 35.1], 
                            [120.0, 35.1], [121.9, 34.5], [121.9, 32.0], [120.5, 31.0], 
                            [118.5, 30.8], [116.3, 30.8]
                        ]],
                        # 华南地区
                        [[
                            [109.7, 20.2], [109.7, 22.5], [110.5, 24.0], [113.5, 25.5], 
                            [117.3, 25.5], [117.3, 23.0], [116.0, 21.5], [114.0, 20.2], 
                            [109.7, 20.2]
                        ]],
                        # 西南地区
                        [[
                            [97.3, 26.0], [97.3, 30.0], [101.0, 33.0], [104.5, 34.3], 
                            [108.5, 34.3], [108.5, 31.0], [105.5, 28.5], [102.0, 26.0], 
                            [97.3, 26.0]
                        ]],
                        # 西北地区
                        [[
                            [92.6, 32.6], [92.6, 36.0], [98.0, 39.0], [102.0, 42.8], 
                            [108.7, 42.8], [108.7, 38.0], [105.0, 35.0], [101.0, 32.6], 
                            [92.6, 32.6]
                        ]],
                        # 海南岛
                        [[
                            [108.6, 18.1], [108.6, 19.0], [109.5, 20.1], [111.0, 20.1], 
                            [111.0, 19.0], [110.0, 18.1], [108.6, 18.1]
                        ]],
                        # 台湾岛
                        [[
                            [120.0, 21.5], [120.0, 25.0], [122.0, 25.5], [122.0, 21.5], 
                            [120.0, 21.5]
                        ]]
                    ]
                }
            }
        ]
    }

# 导出用户分析报表 (Excel格式)
@users_bp.route('/export_analytics_report')
def export_analytics_report():
    """导出用户分析报表 (Excel格式)"""
    try:
        # 从数据库获取真实数据
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)
        ninety_days_ago = now - timedelta(days=90)
        last_year = now - timedelta(days=365)
        
        # 计算当前月份和年份
        current_month = now.month
        current_year = now.year
        
        # 计算用户总数和同比增长率
        total_users = User.query.count()
        users_last_year = User.query.filter(User.registration_time <= last_year).count()
        if users_last_year > 0:
            yoy_growth = ((total_users - users_last_year) / users_last_year) * 100
        else:
            yoy_growth = 100
        
        # 计算本月新增用户数和环比增长率
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_users_this_month = User.query.filter(
            User.registration_time >= this_month_start,
            User.registration_time <= now
        ).count()
        
        # 计算上月新增用户
        last_month = now - relativedelta(months=1)
        last_month_start = last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_end = this_month_start - timedelta(seconds=1)
        new_users_last_month = User.query.filter(
            User.registration_time >= last_month_start,
            User.registration_time <= last_month_end
        ).count()
        
        # 计算环比增长
        if new_users_last_month > 0:
            mom_growth = ((new_users_this_month - new_users_last_month) / new_users_last_month) * 100
        else:
            mom_growth = 100
        
        # 计算用户活跃率
        active_users = User.query.filter(User.last_login_time >= thirty_days_ago).count()
        activity_rate = (active_users / total_users) * 100 if total_users > 0 else 0
        
        # 计算平均用户消费/余额
        avg_balance = db.session.query(func.avg(User.balance)).scalar() or 0
        
        # 计算近12个月的用户增长数据
        months = []
        user_growth = []
        monthly_active_users = []
        
        for i in range(11, -1, -1):
            # 计算当前循环月份的开始和结束日期
            month_start = (now - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i > 0:
                next_month = (now - relativedelta(months=i-1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                month_end = next_month - timedelta(seconds=1)
            else:
                month_end = now
            
            # 获取月份名称
            if month_start.year < now.year:
                month_label = f'上年{month_start.month}月'
            else:
                month_label = f'本年{month_start.month}月'
            months.append(month_label)
            
            # 统计每月新增用户数
            monthly_new_users = User.query.filter(
                User.registration_time >= month_start,
                User.registration_time <= month_end
            ).count()
            user_growth.append(monthly_new_users)
            
            # 统计每月活跃用户
            monthly_active = User.query.filter(
                User.last_login_time >= month_start,
                User.last_login_time <= month_end
            ).count()
            monthly_active_users.append(monthly_active)
        
        # 计算用户注册渠道分布
        channel_distribution = {}
        channels = ['手机应用', '网站', '微信小程序', '合作推广', '其他']
        
        for channel in channels:
            count = User.query.filter(User.registration_channel == channel).count()
            percentage = round((count / total_users) * 100, 1) if total_users > 0 else 0
            channel_distribution[channel] = percentage
        
        # 计算用户年龄分布
        age_distribution = {}
        age_labels = ['18-24岁', '25-34岁', '35-44岁', '45-54岁', '55岁以上']
        age_counts = [0, 0, 0, 0, 0]
        
        users_with_birth_date = User.query.filter(User.birth_date != None).all()
        for user in users_with_birth_date:
            age = current_year - user.birth_date.year
            if 18 <= age <= 24:
                age_counts[0] += 1
            elif 25 <= age <= 34:
                age_counts[1] += 1
            elif 35 <= age <= 44:
                age_counts[2] += 1
            elif 45 <= age <= 54:
                age_counts[3] += 1
            elif age >= 55:
                age_counts[4] += 1
        
        for i, label in enumerate(age_labels):
            age_distribution[label] = age_counts[i]
        
        # 计算性别比例
        gender_distribution = {}
        male_count = User.query.filter(User.gender == '男').count()
        female_count = User.query.filter(User.gender == '女').count()
        other_gender_count = User.query.filter(User.gender == '其他').count()
        
        total_with_gender = male_count + female_count + other_gender_count
        if total_with_gender > 0:
            gender_distribution['男性'] = round((male_count / total_with_gender) * 100, 1)
            gender_distribution['女性'] = round((female_count / total_with_gender) * 100, 1)
            gender_distribution['其他'] = round((other_gender_count / total_with_gender) * 100, 1)
        else:
            gender_distribution = {'男性': 0, '女性': 0, '其他': 0}
        
        # 计算信用分分布
        credit_score_distribution = {}
        credit_labels = ['0-30', '31-60', '61-90', '91-120', '121-150']
        credit_counts = [0, 0, 0, 0, 0]
        
        users_with_credit = User.query.all()
        for user in users_with_credit:
            score = user.credit_score or 0
            if score < 30:
                credit_counts[0] += 1
            elif 30 <= score < 60:
                credit_counts[1] += 1
            elif 60 <= score < 90:
                credit_counts[2] += 1
            elif 90 <= score < 120:
                credit_counts[3] += 1
            elif score >= 120:
                credit_counts[4] += 1
        
        for i, label in enumerate(credit_labels):
            credit_score_distribution[label] = credit_counts[i]
        
        # 计算用户地理分布
        geographic_distribution = {}
        provinces = [
            '北京', '天津', '上海', '重庆', '河北', '河南', '云南', '辽宁', '黑龙江', 
            '湖南', '安徽', '山东', '江苏', '浙江', '江西', '湖北', '广西', '甘肃', 
            '山西', '内蒙古', '陕西', '吉林', '福建', '贵州', '广东', '青海', '西藏', 
            '四川', '宁夏', '海南', '台湾', '香港', '澳门'
        ]
        
        # 城市到省份的映射表
        city_to_province = {
            '沈阳市': '辽宁',
            '上海市': '上海',
            '北京市': '北京',
            '广州市': '广东',
            '深圳市': '广东',
            '杭州市': '浙江',
            '南京市': '江苏',
            '成都市': '四川',
            '重庆市': '重庆',
            '武汉市': '湖北',
            '西安市': '陕西',
            # 可以添加更多城市到省份的映射
        }
        
        # 省份名称映射（转换为地图要求的名称格式）
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
            '澳门': '澳门特别行政区'
        }
        
        # 创建省份-用户数量映射字典
        province_counts = {province: 0 for province in provinces}
        
        # 获取所有有注册城市信息的用户
        users_with_location = User.query.filter(User.registration_city != None, User.registration_city != '').all()
        
        # 统计各省份用户数量
        for user in users_with_location:
            city = user.registration_city
            
            # 先通过城市到省份的映射表转换为省份
            province = city_to_province.get(city)
            
            # 如果城市不在映射表中，尝试直接使用（可能本身就是省份）
            if not province:
                province = city
                
            if province in province_counts:
                province_counts[province] += 1
        
        # 将地理分布数据添加到导出数据中
        for province, count in province_counts.items():
            if count > 0:  # 只包含有用户的省份
                # 使用映射转换省份名称
                mapped_province = province_name_map.get(province, province)
                geographic_distribution[mapped_province] = count
        
        # 创建多个数据表
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 核心指标表
            core_metrics = pd.DataFrame([
                {"指标名称": "总用户数", "值": total_users, "同比增长": f"{round(yoy_growth, 1)}%"},
                {"指标名称": "本月新增用户", "值": new_users_this_month, "环比增长": f"{round(mom_growth, 1)}%"},
                {"指标名称": "用户活跃率", "值": f"{round(activity_rate, 1)}%", "环比变化": f"{'+' if activity_rate > 0 else ''}{round(activity_rate, 1)}%"},
                {"指标名称": "平均用户余额", "值": f"¥{round(avg_balance, 2)}", "同比增长": ""}
            ])
            core_metrics.to_excel(writer, index=False, sheet_name='核心指标')
            
            # 用户增长趋势
            growth_df = pd.DataFrame({
                "月份": months,
                "新增用户数": user_growth,
                "活跃用户数": monthly_active_users
            })
            growth_df.to_excel(writer, index=False, sheet_name='用户增长趋势')
            
            # 用户注册渠道
            channel_df = pd.DataFrame([
                {"渠道": k, "占比": f"{v}%"} for k, v in channel_distribution.items()
            ])
            channel_df.to_excel(writer, index=False, sheet_name='注册渠道分布')
            
            # 用户年龄分布
            age_df = pd.DataFrame([
                {"年龄段": k, "用户数": v} for k, v in age_distribution.items()
            ])
            age_df.to_excel(writer, index=False, sheet_name='年龄分布')
            
            # 用户性别比例
            gender_df = pd.DataFrame([
                {"性别": k, "占比": f"{v}%"} for k, v in gender_distribution.items()
            ])
            gender_df.to_excel(writer, index=False, sheet_name='性别比例')
            
            # 信用分分布
            credit_df = pd.DataFrame([
                {"信用分范围": k, "用户数": v} for k, v in credit_score_distribution.items()
            ])
            credit_df.to_excel(writer, index=False, sheet_name='信用分分布')
            
            # 地理分布
            geo_df = pd.DataFrame([
                {"省份": k, "用户数": v} for k, v in geographic_distribution.items()
            ])
            geo_df.to_excel(writer, index=False, sheet_name='地理分布')
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'用户数据分析报表_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
    except Exception as e:
        # 清理图表文件
        for chart_file in chart_files:
            if os.path.exists(chart_file):
                os.remove(chart_file)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
        raise e 

# 导出用户分析报表 (PDF格式)
@users_bp.route('/export_analytics_report_pdf')
def export_analytics_report_pdf():
    """导出用户分析报表 (PDF格式)"""
    try:
        # 从数据库获取真实数据
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)
        ninety_days_ago = now - timedelta(days=90)
        last_year = now - timedelta(days=365)
        
        # 计算当前月份和年份
        current_month = now.month
        current_year = now.year
        
        # 计算用户总数和同比增长率
        total_users = User.query.count()
        users_last_year = User.query.filter(User.registration_time <= last_year).count()
        if users_last_year > 0:
            yoy_growth = ((total_users - users_last_year) / users_last_year) * 100
        else:
            yoy_growth = 100
        
        # 计算本月新增用户数和环比增长率
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_users_this_month = User.query.filter(
            User.registration_time >= this_month_start,
            User.registration_time <= now
        ).count()
        
        # 计算上月新增用户
        last_month = now - relativedelta(months=1)
        last_month_start = last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_end = this_month_start - timedelta(seconds=1)
        new_users_last_month = User.query.filter(
            User.registration_time >= last_month_start,
            User.registration_time <= last_month_end
        ).count()
        
        # 计算环比增长
        if new_users_last_month > 0:
            mom_growth = ((new_users_this_month - new_users_last_month) / new_users_last_month) * 100
        else:
            mom_growth = 100
        
        # 计算用户活跃率
        active_users = User.query.filter(User.last_login_time >= thirty_days_ago).count()
        activity_rate = (active_users / total_users) * 100 if total_users > 0 else 0
        
        # 计算平均用户消费/余额
        avg_balance = db.session.query(func.avg(User.balance)).scalar() or 0
        
        # 计算近12个月的用户增长数据
        months = []
        user_growth = []
        monthly_active_users = []
        
        for i in range(11, -1, -1):
            # 计算当前循环月份的开始和结束日期
            month_start = (now - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i > 0:
                next_month = (now - relativedelta(months=i-1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                month_end = next_month - timedelta(seconds=1)
            else:
                month_end = now
            
            # 获取月份名称
            if month_start.year < now.year:
                month_label = f'上年{month_start.month}月'
            else:
                month_label = f'本年{month_start.month}月'
            months.append(month_label)
            
            # 统计每月新增用户数
            monthly_new_users = User.query.filter(
                User.registration_time >= month_start,
                User.registration_time <= month_end
            ).count()
            user_growth.append(monthly_new_users)
            
            # 统计每月活跃用户
            monthly_active = User.query.filter(
                User.last_login_time >= month_start,
                User.last_login_time <= month_end
            ).count()
            monthly_active_users.append(monthly_active)
        
        # 计算用户注册渠道分布
        channel_distribution = {}
        channels = ['手机应用', '网站', '微信小程序', '合作推广', '其他']
        
        for channel in channels:
            count = User.query.filter(User.registration_channel == channel).count()
            percentage = round((count / total_users) * 100, 1) if total_users > 0 else 0
            channel_distribution[channel] = percentage
        
        # 计算用户年龄分布
        age_distribution = {}
        age_labels = ['18-24岁', '25-34岁', '35-44岁', '45-54岁', '55岁以上']
        age_counts = [0, 0, 0, 0, 0]
        
        users_with_birth_date = User.query.filter(User.birth_date != None).all()
        for user in users_with_birth_date:
            age = current_year - user.birth_date.year
            if 18 <= age <= 24:
                age_counts[0] += 1
            elif 25 <= age <= 34:
                age_counts[1] += 1
            elif 35 <= age <= 44:
                age_counts[2] += 1
            elif 45 <= age <= 54:
                age_counts[3] += 1
            elif age >= 55:
                age_counts[4] += 1
        
        for i, label in enumerate(age_labels):
            age_distribution[label] = age_counts[i]
        
        # 计算性别比例
        gender_distribution = {}
        male_count = User.query.filter(User.gender == '男').count()
        female_count = User.query.filter(User.gender == '女').count()
        other_gender_count = User.query.filter(User.gender == '其他').count()
        
        total_with_gender = male_count + female_count + other_gender_count
        if total_with_gender > 0:
            gender_distribution['男性'] = round((male_count / total_with_gender) * 100, 1)
            gender_distribution['女性'] = round((female_count / total_with_gender) * 100, 1)
            gender_distribution['其他'] = round((other_gender_count / total_with_gender) * 100, 1)
        else:
            gender_distribution = {'男性': 0, '女性': 0, '其他': 0}
        
        # 计算信用分分布
        credit_score_distribution = {}
        credit_labels = ['0-30', '31-60', '61-90', '91-120', '121-150']
        credit_counts = [0, 0, 0, 0, 0]
        
        users_with_credit = User.query.all()
        for user in users_with_credit:
            score = user.credit_score or 0
            if score < 30:
                credit_counts[0] += 1
            elif 30 <= score < 60:
                credit_counts[1] += 1
            elif 60 <= score < 90:
                credit_counts[2] += 1
            elif 90 <= score < 120:
                credit_counts[3] += 1
            elif score >= 120:
                credit_counts[4] += 1
        
        for i, label in enumerate(credit_labels):
            credit_score_distribution[label] = credit_counts[i]
        
        # 计算用户地理分布
        geographic_distribution = {}
        provinces = [
            '北京', '天津', '上海', '重庆', '河北', '河南', '云南', '辽宁', '黑龙江', 
            '湖南', '安徽', '山东', '江苏', '浙江', '江西', '湖北', '广西', '甘肃', 
            '山西', '内蒙古', '陕西', '吉林', '福建', '贵州', '广东', '青海', '西藏', 
            '四川', '宁夏', '海南', '台湾', '香港', '澳门'
        ]
        
        # 城市到省份的映射表
        city_to_province = {
            '沈阳市': '辽宁',
            '上海市': '上海',
            '北京市': '北京',
            '广州市': '广东',
            '深圳市': '广东',
            '杭州市': '浙江',
            '南京市': '江苏',
            '成都市': '四川',
            '重庆市': '重庆',
            '武汉市': '湖北',
            '西安市': '陕西',
            # 可以添加更多城市到省份的映射
        }
        
        # 省份名称映射（转换为地图要求的名称格式）
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
            '澳门': '澳门特别行政区'
        }
        
        # 创建省份-用户数量映射字典
        province_counts = {province: 0 for province in provinces}
        
        # 获取所有有注册城市信息的用户
        users_with_location = User.query.filter(User.registration_city != None, User.registration_city != '').all()
        
        # 统计各省份用户数量
        for user in users_with_location:
            city = user.registration_city
            
            # 先通过城市到省份的映射表转换为省份
            province = city_to_province.get(city)
            
            # 如果城市不在映射表中，尝试直接使用（可能本身就是省份）
            if not province:
                province = city
                
            if province in province_counts:
                province_counts[province] += 1
        
        # 将地理分布数据添加到导出数据中
        for province, count in province_counts.items():
            if count > 0:  # 只包含有用户的省份
                # 使用映射转换省份名称
                mapped_province = province_name_map.get(province, province)
                geographic_distribution[mapped_province] = count
        
        # 合并所有数据
        user_data = {
            "总用户数": total_users,
            "本月新增用户": new_users_this_month,
            "用户活跃率": f"{round(activity_rate, 1)}%",
            "平均用户消费": round(avg_balance, 2),
            "用户增长": user_growth,
            "用户注册渠道": channel_distribution,
            "用户年龄分布": age_distribution,
            "用户性别比例": gender_distribution,
            "信用分分布": credit_score_distribution,
            "地理分布": geographic_distribution
        }
        
        # 创建临时目录存放图表
        temp_dir = tempfile.mkdtemp()
        chart_files = []
        
        try:
            # 设置matplotlib的中文字体
            if CHINESE_FONT_REGISTERED:
                plt.rcParams['font.sans-serif'] = [CHINESE_FONT_NAME, 'SimHei', 'SimSun', 'SimKai', 'SimSunB']  # 尝试多种字体
                plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
            else:
                # 如果没有注册成功任何字体，尝试使用matplotlib自身支持的字体
                try:
                    # 尝试使用系统中可能存在的字体
                    from matplotlib.font_manager import FontProperties
                    font_paths = [
                        'C:/Windows/Fonts/simsun.ttc',
                        'C:/Windows/Fonts/simhei.ttf',
                        'C:/Windows/Fonts/simkai.ttf',
                        'C:/Windows/Fonts/simsunb.ttf'
                    ]
                    
                    for font_path in font_paths:
                        if os.path.exists(font_path):
                            print(f"Matplotlib尝试使用字体: {font_path}")
                            font_prop = FontProperties(fname=font_path)
                            plt.rcParams['font.sans-serif'] = ['sans-serif']
                            # 在每个图表中使用此字体
                            break
                    
                    plt.rcParams['axes.unicode_minus'] = False
                except Exception as e:
                    print(f"Matplotlib设置中文字体失败: {str(e)}")
                    print("图表中的中文可能无法正确显示")
            
            # 生成图表
            try:
                # 1. 用户增长趋势图
                plt.figure(figsize=(10, 4))
                plt.plot(months, user_data["用户增长"], marker='o', linewidth=2, color='#3366cc')
                plt.title('用户增长趋势 (近12个月)')
                plt.ylabel('新增用户数')
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.xticks(rotation=45)
                plt.tight_layout()
                growth_chart = os.path.join(temp_dir, 'growth_chart.png')
                plt.savefig(growth_chart)
                chart_files.append(growth_chart)
                plt.close()
                
                # 2. 用户注册渠道饼图
                plt.figure(figsize=(6, 6))
                channels = list(user_data["用户注册渠道"].keys())
                values = list(user_data["用户注册渠道"].values())
                plt.pie(values, labels=channels, autopct='%1.1f%%', startangle=90, 
                        colors=['#3366cc', '#dc3912', '#ff9900', '#109618', '#990099'])
                plt.title('用户注册渠道分布')
                plt.axis('equal')
                channel_chart = os.path.join(temp_dir, 'channel_chart.png')
                plt.savefig(channel_chart)
                chart_files.append(channel_chart)
                plt.close()
                
                # 3. 用户年龄分布条形图
                plt.figure(figsize=(8, 5))
                age_groups = list(user_data["用户年龄分布"].keys())
                age_counts = list(user_data["用户年龄分布"].values())
                plt.bar(age_groups, age_counts, color='#3366cc')
                plt.title('用户年龄分布')
                plt.ylabel('用户数量')
                plt.grid(True, axis='y', linestyle='--', alpha=0.7)
                age_chart = os.path.join(temp_dir, 'age_chart.png')
                plt.savefig(age_chart)
                chart_files.append(age_chart)
                plt.close()
                
                # 4. 信用分分布条形图
                plt.figure(figsize=(8, 5))
                credit_ranges = list(user_data["信用分分布"].keys())
                credit_counts = list(user_data["信用分分布"].values())
                plt.bar(credit_ranges, credit_counts, color=['#ff9999', '#ffcc99', '#ffff99', '#99ff99', '#99ccff'])
                plt.title('用户信用分分布')
                plt.ylabel('用户数量')
                plt.grid(True, axis='y', linestyle='--', alpha=0.7)
                credit_chart = os.path.join(temp_dir, 'credit_chart.png')
                plt.savefig(credit_chart)
                chart_files.append(credit_chart)
                plt.close()
                
                # 5. 用户地理分布图
                plt.figure(figsize=(10, 6))
                geo_provinces = list(user_data["地理分布"].keys())
                geo_counts = list(user_data["地理分布"].values())
                
                # 根据用户数量从大到小排序
                sorted_indices = sorted(range(len(geo_counts)), key=lambda k: geo_counts[k], reverse=True)
                sorted_provinces = [geo_provinces[i] for i in sorted_indices]
                sorted_counts = [geo_counts[i] for i in sorted_indices]
                
                # 只显示用户数量最多的10个省份
                top_n = min(10, len(sorted_provinces))
                plt.bar(sorted_provinces[:top_n], sorted_counts[:top_n], color='#749cea')
                plt.title('用户地理分布前十省份')
                plt.ylabel('用户数量')
                plt.xlabel('省份')
                plt.xticks(rotation=45)
                plt.grid(True, axis='y', linestyle='--', alpha=0.7)
                plt.tight_layout()
                geo_chart = os.path.join(temp_dir, 'geo_chart.png')
                plt.savefig(geo_chart)
                chart_files.append(geo_chart)
                plt.close()
                
            except Exception as e:
                print(f"生成图表时出错: {str(e)}")
                # 如果图表生成失败，创建一个简单的文本提示图
                for chart_name, title in [
                    ('growth_chart.png', '用户增长趋势图生成失败'),
                    ('channel_chart.png', '渠道分布图生成失败'),
                    ('age_chart.png', '年龄分布图生成失败'),
                    ('credit_chart.png', '信用分分布图生成失败'),
                    ('geo_chart.png', '地理分布图生成失败')
                ]:
                    try:
                        plt.figure(figsize=(8, 5))
                        plt.text(0.5, 0.5, title, ha='center', va='center', fontsize=20)
                        plt.axis('off')
                        chart_path = os.path.join(temp_dir, chart_name)
                        plt.savefig(chart_path)
                        chart_files.append(chart_path)
                        plt.close()
                    except:
                        pass
            
            # 生成PDF文件
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                pdf_buffer, 
                pagesize=A4,
                title="用户数据分析报表",
                author="无人驾驶出租车管理平台"
            )
            
            # 初始化样式
            styles = getSampleStyleSheet()
            title_style = styles['Title']
            heading_style = styles['Heading2']
            normal_style = styles['Normal']
            
            # 自定义中文样式
            if CHINESE_FONT_REGISTERED:
                # 创建中文标题样式
                title_style = ParagraphStyle(
                    name='ChineseTitle',
                    fontName=CHINESE_FONT_NAME,
                    fontSize=18,
                    leading=22,
                    alignment=1,  # 居中
                    spaceAfter=6
                )
                
                # 创建中文标题2样式
                heading_style = ParagraphStyle(
                    name='ChineseHeading2',
                    fontName=CHINESE_FONT_NAME,
                    fontSize=14,
                    leading=18,
                    spaceAfter=6
                )
                
                # 创建中文正文样式
                normal_style = ParagraphStyle(
                    name='ChineseNormal',
                    fontName=CHINESE_FONT_NAME,
                    fontSize=10,
                    leading=14
                )
                
                # PDF生成方案：使用注册的中文字体
                print("使用方案1：已注册中文字体用于PDF生成")
            else:
                # 如果没有成功注册中文字体，我们将把中文内容转换成图片
                print("使用方案2：将中文内容转换为图片后嵌入PDF")
            
            # 准备内容
            content = []
            
            # 报表标题
            try:
                # 报表标题
                if CHINESE_FONT_REGISTERED:
                    content.append(Paragraph("用户数据分析报表", title_style))
                    content.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
                else:
                    # 如果没有中文字体，使用英文替代关键标题，避免乱码
                    content.append(Paragraph("User Data Analysis Report", title_style))
                    content.append(Paragraph(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
                content.append(Spacer(1, 20))
                
                # 核心指标表格
                if CHINESE_FONT_REGISTERED:
                    content.append(Paragraph("核心指标概览", heading_style))
                else:
                    content.append(Paragraph("Core Metrics Overview", heading_style))
                
                # 核心指标数据
                core_data = [['指标名称', '数值', '同比增长']] if CHINESE_FONT_REGISTERED else [['Metric', 'Value', 'YoY Growth']]
                core_data.append(['总用户数' if CHINESE_FONT_REGISTERED else 'Total Users', 
                             f"{user_data['总用户数']}", f"+{round(yoy_growth, 1)}%"])
                core_data.append(['本月新增用户' if CHINESE_FONT_REGISTERED else 'New Users This Month', 
                             f"{user_data['本月新增用户']}", f"+{round(mom_growth, 1)}%"])
                core_data.append(['用户活跃率' if CHINESE_FONT_REGISTERED else 'User Activity Rate', 
                             f"{user_data['用户活跃率']}", f"{'+' if activity_rate > 0 else ''}{round(activity_rate, 1)}%"])
                core_data.append(['平均用户余额' if CHINESE_FONT_REGISTERED else 'Average User Balance', 
                             f"¥{user_data['平均用户消费']}", ""])
                
                core_table = Table(core_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
                table_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ]
                
                # 如果成功注册了中文字体，为表格设置中文字体
                if CHINESE_FONT_REGISTERED:
                    table_style.append(('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT_NAME))
                else:
                    table_style.append(('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'))
                    
                core_table.setStyle(TableStyle(table_style))
                content.append(core_table)
                content.append(Spacer(1, 20))
                
                # 用户增长趋势
                if CHINESE_FONT_REGISTERED:
                    content.append(Paragraph("用户增长趋势 (近12个月)", heading_style))
                else:
                    content.append(Paragraph("User Growth Trend (Last 12 Months)", heading_style))
                    
                if os.path.exists(growth_chart):
                    content.append(Image(growth_chart, width=6*inch, height=2.5*inch))
                content.append(Spacer(1, 20))
                
                # 用户注册渠道
                if CHINESE_FONT_REGISTERED:
                    content.append(Paragraph("用户注册渠道分布", heading_style))
                else:
                    content.append(Paragraph("User Registration Channel Distribution", heading_style))
                    
                if os.path.exists(channel_chart):
                    content.append(Image(channel_chart, width=4*inch, height=4*inch))
                content.append(Spacer(1, 20))
                
                # 用户年龄分布
                if CHINESE_FONT_REGISTERED:
                    content.append(Paragraph("用户年龄分布", heading_style))
                else:
                    content.append(Paragraph("User Age Distribution", heading_style))
                    
                if os.path.exists(age_chart):
                    content.append(Image(age_chart, width=6*inch, height=3*inch))
                content.append(Spacer(1, 20))
                
                # 用户信用分分布
                if CHINESE_FONT_REGISTERED:
                    content.append(Paragraph("用户信用分分布", heading_style))
                else:
                    content.append(Paragraph("User Credit Score Distribution", heading_style))
                    
                if os.path.exists(credit_chart):
                    content.append(Image(credit_chart, width=6*inch, height=3*inch))
                content.append(Spacer(1, 20))
                
                # 用户地理分布
                if CHINESE_FONT_REGISTERED:
                    content.append(Paragraph("用户地理分布（前十省份）", heading_style))
                else:
                    content.append(Paragraph("User Geographic Distribution (Top 10 Provinces)", heading_style))
                    
                if os.path.exists(geo_chart):
                    content.append(Image(geo_chart, width=6*inch, height=3*inch))
            
            except Exception as e:
                print(f"准备PDF内容时出错: {str(e)}")
                # 添加错误信息页面
                content = []
                content.append(Paragraph("Error in Report Generation", styles['Title']))
                content.append(Paragraph(f"Error details: {str(e)}", styles['Normal']))
            
            # 生成PDF
            try:
                doc.build(content)
                pdf_buffer.seek(0)
                print("PDF生成成功")
            except Exception as e:
                print(f"构建PDF文档时出错: {str(e)}")
                # 如果PDF生成失败，返回一个简单的错误信息PDF
                try:
                    pdf_buffer = io.BytesIO()
                    c = canvas.Canvas(pdf_buffer, pagesize=A4)
                    c.setFont("Helvetica", 14)
                    c.drawString(100, 700, "Error generating PDF report")
                    c.setFont("Helvetica", 10)
                    c.drawString(100, 680, f"Error details: {str(e)}")
                    c.save()
                    pdf_buffer.seek(0)
                    print("生成了错误信息PDF")
                except Exception as e2:
                    print(f"生成错误信息PDF时也失败了: {str(e2)}")
                    # 如果连错误信息PDF也无法生成，直接抛出异常
                    raise Exception("无法生成PDF报告")
            
            # 删除临时图表文件
            for chart_file in chart_files:
                if os.path.exists(chart_file):
                    os.remove(chart_file)
            os.rmdir(temp_dir)
            
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'用户数据分析报表_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            )
        except Exception as e:
            # 清理图表文件
            for chart_file in chart_files:
                if os.path.exists(chart_file):
                    os.remove(chart_file)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
            raise e 
    except Exception as e:
        # 清理图表文件
        for chart_file in chart_files:
            if os.path.exists(chart_file):
                os.remove(chart_file)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
        raise e 

# 用户信用管理页面
@users_bp.route('/credit-management')
def credit_management():
    """用户信用管理页面，包括信用等级规则和信用变动记录"""
    # 获取信用等级规则
    # 从数据库获取
    from app.dao.credit_level_dao import CreditLevelDAO
    credit_levels = CreditLevelDAO.get_all_credit_levels()
    
    if not credit_levels:
        # 如果数据库中没有数据，使用硬编码的演示数据
        credit_levels = [
            {
                'level_id': 1,
                'level_name': '极低信用',
                'min_score': 0,
                'max_score': 30,
                'benefits': '无特殊权益',
                'limitations': '1. 需支付额外押金\n2. 限制预约功能\n3. 无法使用高峰期服务\n4. 部分车型不可用'
            },
            {
                'level_id': 2,
                'level_name': '低信用',
                'min_score': 31,
                'max_score': 60,
                'benefits': '基础服务访问',
                'limitations': '1. 高峰期限制预约\n2. 无优惠折扣\n3. 需要较长预约提前期'
            },
            {
                'level_id': 3,
                'level_name': '一般信用',
                'min_score': 61,
                'max_score': 90,
                'benefits': '1. 正常使用全部基础功能\n2. 可享受基础会员价格',
                'limitations': '无特殊限制'
            },
            {
                'level_id': 4,
                'level_name': '良好信用',
                'min_score': 91,
                'max_score': 120,
                'benefits': '1. 高峰期优先派车\n2. 享受9折优惠\n3. 免除部分额外费用',
                'limitations': '无限制'
            },
            {
                'level_id': 5,
                'level_name': '优秀信用',
                'min_score': 121,
                'max_score': 150,
                'benefits': '1. 最高优先级派车\n2. 享受8折优惠\n3. 特殊节假日预约保障\n4. 专属客服通道\n5. 免押金服务',
                'limitations': '无限制'
            }
        ]
    
    # 获取信用分变动规则
    # 从数据库获取
    from app.dao.credit_rule_dao import CreditRuleDAO
    credit_rules = CreditRuleDAO.get_all_credit_rules()
    
    if not credit_rules:
        # 如果数据库中没有数据，使用硬编码的演示数据
        credit_rules = [
            {
                'rule_id': 1,
                'rule_name': '按时完成订单',
                'rule_type': '奖励',
                'trigger_event': '订单正常完成',
                'score_change': 1,
                'description': '用户按时完成订单，无任何异常行为'
            },
            {
                'rule_id': 2,
                'rule_name': '按时支付',
                'rule_type': '奖励',
                'trigger_event': '订单结束后立即支付',
                'score_change': 1,
                'description': '用户在订单结束后10分钟内完成支付'
            },
            {
                'rule_id': 3,
                'rule_name': '月度安全奖励',
                'rule_type': '奖励',
                'trigger_event': '连续30天无违规',
                'score_change': 5,
                'description': '用户连续30天没有任何违规行为'
            },
            {
                'rule_id': 4,
                'rule_name': '违约取消订单',
                'rule_type': '惩罚',
                'trigger_event': '车辆到达后取消订单',
                'score_change': -5,
                'description': '车辆到达指定位置后用户取消订单'
            },
            {
                'rule_id': 5,
                'rule_name': '迟到付款',
                'rule_type': '惩罚',
                'trigger_event': '订单结束24小时后仍未支付',
                'score_change': -2,
                'description': '用户在订单结束24小时后仍未完成支付'
            },
            {
                'rule_id': 6,
                'rule_name': '车内不良行为',
                'rule_type': '惩罚',
                'trigger_event': '车内吸烟、吃食物等',
                'score_change': -10,
                'description': '用户在车内吸烟、食用有气味食物等行为'
            },
            {
                'rule_id': 7,
                'rule_name': '定期信用恢复',
                'rule_type': '恢复',
                'trigger_event': '连续30天无减分记录',
                'score_change': 5,
                'description': '用户连续30天内没有任何信用减分记录，自动恢复部分信用分(最高恢复至90分)'
            },
            {
                'rule_id': 8,
                'rule_name': '任务信用修复',
                'rule_type': '恢复',
                'trigger_event': '完成10次无违规订单',
                'score_change': 10,
                'description': '连续完成10次无任何违规记录的订单，恢复部分信用分'
            }
        ]
    
    # 获取信用变动记录
    # 实际项目中应该从数据库获取，带分页
    credit_logs = [
        {
            'log_id': 1,
            'user_id': 101,
            'username': '张三',
            'change_amount': 1,
            'credit_before': 98,
            'credit_after': 99,
            'change_type': '订单完成',
            'reason': '按时完成订单',
            'related_order_id': 'ORD20230415001',
            'operator': '系统',
            'created_at': '2023-04-15 18:30:42'
        },
        {
            'log_id': 2,
            'user_id': 102,
            'username': '李四',
            'change_amount': -5,
            'credit_before': 95,
            'credit_after': 90,
            'change_type': '违规行为',
            'reason': '违约取消订单',
            'related_order_id': 'ORD20230416002',
            'operator': '系统',
            'created_at': '2023-04-16 09:15:23'
        },
        {
            'log_id': 3,
            'user_id': 103,
            'username': '王五',
            'change_amount': 5,
            'credit_before': 85,
            'credit_after': 90,
            'change_type': '系统奖励',
            'reason': '连续30天无违规',
            'related_order_id': None,
            'operator': '系统',
            'created_at': '2023-04-17 00:00:11'
        },
        {
            'log_id': 4,
            'user_id': 101,
            'username': '张三',
            'change_amount': 10,
            'credit_before': 99,
            'credit_after': 109,
            'change_type': '人工修改',
            'reason': '客户投诉处理补偿',
            'related_order_id': 'ORD20230418003',
            'operator': 'admin',
            'created_at': '2023-04-18 14:22:35'
        },
        {
            'log_id': 5,
            'user_id': 104,
            'username': '赵六',
            'change_amount': -10,
            'credit_before': 100,
            'credit_after': 90,
            'change_type': '违规行为',
            'reason': '车内吸烟',
            'related_order_id': 'ORD20230419004',
            'operator': '系统',
            'created_at': '2023-04-19 21:08:17'
        }
    ]
    
    # 构造分页对象 (在实际应用中应当使用SQLAlchemy的分页)
    class Pagination:
        def __init__(self, page, per_page, total):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.prev_num = page - 1 if page > 1 else None
            self.next_num = page + 1 if page < self.pages else None
            self.has_prev = page > 1
            self.has_next = page < self.pages
            
        def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
            last = 0
            for num in range(1, self.pages + 1):
                if num <= left_edge or \
                   (num > self.page - left_current - 1 and num < self.page + right_current) or \
                   num > self.pages - right_edge:
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num
    
    pagination = Pagination(page=1, per_page=10, total=len(credit_logs))
    
    # 处理benefits和limitations中的换行符，将其替换为<br>标签
    for level in credit_levels:
        if level.get('benefits'):
            level['benefits'] = level['benefits'].replace('\n', '<br>')
        if level.get('limitations'):
            level['limitations'] = level['limitations'].replace('\n', '<br>')
    
    return render_template(
        'users/credit_management.html',
        credit_levels=credit_levels,
        credit_rules=credit_rules,
        credit_logs=credit_logs,
        pagination=pagination
    )

# 添加信用变动记录API路由
@users_bp.route('/api/credit/logs', methods=['GET'])
def get_credit_logs():
    """获取信用变动记录API"""
    try:
        print("开始请求信用变动记录API...")
        
        # 获取DataTables发送的参数
        draw = request.args.get('draw', 1, type=int)
        start = request.args.get('start', 0, type=int)
        length = request.args.get('length', 10, type=int)
        
        # 搜索参数
        search_value = request.args.get('search[value]', '')
        
        # 排序参数
        order_column_index = request.args.get('order[0][column]', 0, type=int)
        order_column_name = request.args.get(f'columns[{order_column_index}][data]', 'log_id')
        order_dir = request.args.get('order[0][dir]', 'desc')
        
        # 自定义筛选条件
        user_id = request.args.get('user_id', '')
        change_type = request.args.get('change_type', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # 尝试从数据库获取
        try:
            from app.dao.user_dao import UserDAO
            user_dao = UserDAO()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if user_id:
                conditions.append("l.user_id = %s")
                params.append(int(user_id))
            
            if change_type:
                conditions.append("l.change_type = %s")
                params.append(change_type)
            
            if date_from:
                conditions.append("l.created_at >= %s")
                params.append(f"{date_from} 00:00:00")
            
            if date_to:
                conditions.append("l.created_at <= %s")
                params.append(f"{date_to} 23:59:59")
            
            # 全局搜索
            if search_value:
                search_conditions = [
                    "l.log_id LIKE %s",
                    "l.user_id LIKE %s",
                    "u.username LIKE %s",
                    "l.change_type LIKE %s",
                    "l.reason LIKE %s",
                    "l.related_order_id LIKE %s",
                    "l.operator LIKE %s"
                ]
                conditions.append(f"({' OR '.join(search_conditions)})")
                search_param = f"%{search_value}%"
                params.extend([search_param] * 7)  # 7个搜索条件
                
            # 构建WHERE子句
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            # 获取总记录数
            count_sql = f"""
                SELECT COUNT(*) as total 
                FROM user_credit_logs l
                LEFT JOIN users u ON l.user_id = u.user_id
                {where_clause}
            """
            
            count_result = user_dao.execute_query(count_sql, params)
            total_records = count_result[0]['total'] if count_result else 0
            
            # 没有筛选时的记录总数
            count_all_sql = "SELECT COUNT(*) as total FROM user_credit_logs"
            count_all_result = user_dao.execute_query(count_all_sql)
            total_records_all = count_all_result[0]['total'] if count_all_result else 0
            
            # 有效的排序字段映射
            column_mapping = {
                'log_id': 'l.log_id',
                'user_id': 'l.user_id',
                'change_amount': 'l.change_amount',
                'credit_before': 'l.credit_before',
                'credit_after': 'l.credit_after',
                'change_type': 'l.change_type',
                'reason': 'l.reason',
                'related_order_id': 'l.related_order_id',
                'operator': 'l.operator',
                'created_at': 'l.created_at'
            }
            
            # 获取实际排序字段
            sort_column = column_mapping.get(order_column_name, 'l.log_id')
            sort_direction = "DESC" if order_dir.lower() == "desc" else "ASC"
            
            # 获取分页数据
            if total_records > 0:
                data_sql = f"""
                    SELECT l.*, u.username
                    FROM user_credit_logs l
                    LEFT JOIN users u ON l.user_id = u.user_id
                    {where_clause}
                    ORDER BY {sort_column} {sort_direction}
                    LIMIT %s OFFSET %s
                """
                params.extend([length, start])
                
                credit_logs = user_dao.execute_query(data_sql, params)
                print(f"从数据库查询到 {len(credit_logs)} 条记录")
                
                # 格式化数据
                for log in credit_logs:
                    if 'created_at' in log and log['created_at']:
                        log['created_at'] = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                
                # 构建DataTables所需的返回格式
                response_data = {
                    'draw': draw,
                    'recordsTotal': total_records_all,
                    'recordsFiltered': total_records,
                    'data': credit_logs
                }
                
                return jsonify(response_data)
            else:
                # 无数据
                response_data = {
                    'draw': draw,
                    'recordsTotal': 0,
                    'recordsFiltered': 0,
                    'data': []
                }
                
                return jsonify(response_data)
            
        except Exception as e:
            print(f"数据库查询失败: {str(e)}")
            # 出错时返回错误信息
            return jsonify({
                'draw': draw,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': str(e)
            })
    
    except Exception as e:
        import traceback
        print(f"获取信用记录异常: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'draw': request.args.get('draw', 1, type=int),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': str(e)
        })

# 添加信用变动记录导出API
@users_bp.route('/api/credit/logs/export', methods=['GET'])
def export_credit_logs():
    """导出信用变动记录"""
    try:
        # 获取请求参数
        user_id = request.args.get('user_id', '')
        change_type = request.args.get('change_type', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # 构建SQL查询条件
        conditions = []
        params = []
        
        if user_id:
            conditions.append("user_id = %s")
            params.append(user_id)
        
        if change_type:
            conditions.append("change_type = %s")
            params.append(change_type)
        
        if date_from:
            conditions.append("created_at >= %s")
            params.append(f"{date_from} 00:00:00")
        
        if date_to:
            conditions.append("created_at <= %s")
            params.append(f"{date_to} 23:59:59")
        
        # 构建SQL语句
        sql_where = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        # 使用DAO获取数据
        from app.dao.user_dao import UserDAO
        user_dao = UserDAO()
        
        data_sql = f"""
            SELECT l.*, u.username
            FROM user_credit_logs l
            LEFT JOIN users u ON l.user_id = u.user_id
            {sql_where}
            ORDER BY l.created_at DESC
        """
        
        credit_logs = user_dao.execute_query(data_sql, params)
        
        # 生成CSV文件
        import csv
        from io import StringIO
        import datetime
        
        output = StringIO()
        writer = csv.writer(output)
        
        # 写入标题行
        writer.writerow(['记录ID', '用户ID', '用户名', '变动分值', '变动前分值', '变动后分值', 
                         '变动类型', '变动原因', '关联订单', '操作人', '时间'])
        
        # 写入数据行
        for log in credit_logs:
            writer.writerow([
                log.get('log_id', ''),
                log.get('user_id', ''),
                log.get('username', ''),
                log.get('change_amount', ''),
                log.get('credit_before', ''),
                log.get('credit_after', ''),
                log.get('change_type', ''),
                log.get('reason', ''),
                log.get('related_order_id', '') or '-',
                log.get('operator', '') or '系统',
                log.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if isinstance(log.get('created_at'), datetime.datetime) else log.get('created_at', '')
            ])
        
        # 设置响应头，返回CSV文件
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=credit_logs_{timestamp}.csv"}
        )
    
    except Exception as e:
        print(f"导出信用记录异常: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'导出信用记录失败: {str(e)}'
        })

@users_bp.route('/user-reviews')
def user_reviews():
    """用户评价管理页面"""
    try:
        # 从数据库获取真实评价数据
        from app.dao.base_dao import BaseDAO
        
        # 获取评价数据
        query = """
        SELECT e.id, e.order_id, e.user_id, e.rating, e.comment, e.created_at,
               u.username
        FROM evaluations e
        LEFT JOIN users u ON e.user_id = u.user_id
        ORDER BY e.created_at DESC
        """
        
        reviews = BaseDAO.execute_query(query)
        
        # 计算评分统计
        ratings_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total_rating = 0
        
        for review in reviews:
            rating = review.get('rating', 0)
            if 1 <= rating <= 5:
                ratings_count[rating] += 1
                total_rating += rating
        
        # 计算平均评分
        avg_rating = round(total_rating / len(reviews), 1) if reviews else 0
        
        # 计算好评率和差评率
        good_ratings = ratings_count[4] + ratings_count[5]
        bad_ratings = ratings_count[1] + ratings_count[2]
        total_count = len(reviews)
        
        good_rating_percent = round((good_ratings / total_count) * 100) if total_count > 0 else 0
        bad_rating_percent = round((bad_ratings / total_count) * 100) if total_count > 0 else 0
        
        return render_template('users/user_reviews.html', 
                              reviews=reviews,
                              ratings_count=ratings_count,
                              avg_rating=avg_rating,
                              good_rating_percent=good_rating_percent,
                              bad_rating_percent=bad_rating_percent)
                              
    except Exception as e:
        print(f"获取评价数据出错: {str(e)}")
        # 发生错误时提供空数据
        return render_template('users/user_reviews.html', 
                              reviews=[],
                              ratings_count={1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                              avg_rating=0,
                              good_rating_percent=0,
                              bad_rating_percent=0)

@users_bp.route('/ai-customer-service')
def ai_customer_service():
    """智能客服管理页面"""
    try:
        from app.dao.base_dao import BaseDAO
        import datetime
        
        # 获取用户聊天会话数据
        # 查询所有有聊天记录的用户
        query = """
        SELECT DISTINCT cr.user_id, 
               u.username,
               MIN(cr.created_at) as first_message_time,
               MAX(cr.created_at) as last_message_time,
               COUNT(cr.id) as message_count
        FROM chat_records cr
        JOIN users u ON cr.user_id = u.user_id
        GROUP BY cr.user_id, u.username
        ORDER BY last_message_time DESC
        """
        
        user_sessions = BaseDAO.execute_query(query)
        
        # 统计卡片1：使用过智能客服的用户数
        unique_users = len(user_sessions)
        
        # 统计卡片2：用户平均聊天次数
        avg_chats_query = """
        SELECT AVG(message_count) as avg_chats
        FROM (
            SELECT user_id, COUNT(*) as message_count
            FROM chat_records
            GROUP BY user_id
        ) as user_counts
        """
        avg_chats_result = BaseDAO.execute_query(avg_chats_query)
        avg_chats_per_user = avg_chats_result[0]['avg_chats'] if avg_chats_result and avg_chats_result[0]['avg_chats'] else 0
        
        # 统计卡片3：今日聊天次数
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        today_chats_query = """
        SELECT COUNT(*) as today_count
        FROM chat_records
        WHERE DATE(created_at) = %s
        """
        today_chats_result = BaseDAO.execute_query(today_chats_query, (today,))
        today_chats = today_chats_result[0]['today_count'] if today_chats_result else 0
        
        # 统计卡片4：平均响应时效
        response_time_query = """
        SELECT AVG(TIMESTAMPDIFF(SECOND, user_msg.created_at, ai_msg.created_at)) as avg_response_time
        FROM (
            SELECT user_id, created_at, id
            FROM chat_records
            WHERE is_user = 1
        ) as user_msg
        JOIN (
            SELECT user_id, created_at, id
            FROM chat_records
            WHERE is_user = 0
        ) as ai_msg
        ON user_msg.user_id = ai_msg.user_id
        WHERE ai_msg.id = (
            SELECT MIN(id) 
            FROM chat_records 
            WHERE user_id = user_msg.user_id AND is_user = 0 AND created_at > user_msg.created_at
        )
        """
        response_time_result = BaseDAO.execute_query(response_time_query)
        avg_response_time = round(response_time_result[0]['avg_response_time'], 1) if response_time_result and response_time_result[0]['avg_response_time'] else 2.5
        
        # 处理会话数据
        sessions = []
        for idx, session in enumerate(user_sessions):
            # 计算会话持续时间
            if session.get('first_message_time') and session.get('last_message_time'):
                first_time = session.get('first_message_time')
                last_time = session.get('last_message_time')
                
                # 计算会话时长（分钟）
                duration_seconds = (last_time - first_time).total_seconds()
                duration_minutes = int(duration_seconds / 60)
                duration = f"{duration_minutes}分钟"
                
                # 获取最后一条消息判断是否已解决
                last_message_query = """
                SELECT msg, is_user 
                FROM chat_records 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1
                """
                last_message = BaseDAO.execute_query(last_message_query, (session.get('user_id'),))
                
                # 根据最后一条消息判断解决状态
                resolution_status = "未解决"
                if last_message and len(last_message) > 0:
                    # 如果最后一条是系统回复，可能已解决
                    if not last_message[0].get('is_user'):
                        resolution_status = "已解决"
                
                sessions.append({
                    'id': idx + 1,
                    'user_id': session.get('user_id'),
                    'username': session.get('username'),
                    'session_id': f"CHAT{session.get('user_id')}",
                    'start_time': session.get('first_message_time').strftime('%Y-%m-%d %H:%M:%S') if session.get('first_message_time') else '',
                    'end_time': session.get('last_message_time').strftime('%Y-%m-%d %H:%M:%S') if session.get('last_message_time') else '',
                    'last_time': session.get('last_message_time').strftime('%Y-%m-%d %H:%M:%S') if session.get('last_message_time') else '',
                    'duration': duration,
                    'message_count': session.get('message_count', 0),
                    'resolution_status': resolution_status
                })
        
        # 获取所有会话记录数据
        all_messages_query = """
        SELECT cr.id, cr.user_id, u.username, cr.msg as content, cr.is_user, cr.created_at
        FROM chat_records cr
        LEFT JOIN users u ON cr.user_id = u.user_id
        ORDER BY cr.user_id ASC, cr.created_at ASC
        """
        
        all_messages = BaseDAO.execute_query(all_messages_query)
        
        # 处理消息数据，确保格式一致
        for message in all_messages:
            if 'created_at' in message and message['created_at']:
                message['created_at'] = message['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if 'username' not in message or not message['username']:
                message['username'] = f"用户{message['user_id']}"
        
        return render_template('users/ai_customer_service.html', 
                              sessions=sessions, 
                              all_messages=all_messages,
                              unique_users=unique_users,
                              avg_chats_per_user=avg_chats_per_user,
                              today_chats=today_chats,
                              avg_response_time=avg_response_time)
        
    except Exception as e:
        print(f"获取客服会话数据出错: {str(e)}")
        # 发生错误时使用模拟数据
        # 模拟会话数据
        sessions = [
            {
                'id': 1,
                'user_id': 1001,
                'username': '张三',
                'session_id': 'CHAT1001',
                'start_time': '2023-06-01 10:30:15',
                'end_time': '2023-06-01 10:45:22',
                'last_time': '2023-06-01 10:45:22',
                'duration': '15分钟',
                'message_count': 8,
                'resolution_status': '已解决'
            },
            {
                'id': 2,
                'user_id': 1002,
                'username': '李四',
                'session_id': 'CHAT1002',
                'start_time': '2023-06-02 14:20:10',
                'end_time': '2023-06-02 14:35:45',
                'last_time': '2023-06-02 14:35:45',
                'duration': '15分钟',
                'message_count': 6,
                'resolution_status': '已解决'
            },
            {
                'id': 3,
                'user_id': 1003,
                'username': '王五',
                'session_id': 'CHAT1003',
                'start_time': '2023-06-03 09:10:05',
                'end_time': '2023-06-03 09:18:30',
                'last_time': '2023-06-03 09:18:30',
                'duration': '8分钟',
                'message_count': 5,
                'resolution_status': '未解决'
            }
        ]
        
        # 模拟聊天记录数据
        all_messages = [
            {
                'id': 1,
                'user_id': 1001,
                'username': '张三',
                'content': '你好，我想咨询一下订单问题',
                'is_user': True,
                'created_at': '2023-06-01 10:30:15'
            },
            {
                'id': 2,
                'user_id': 1001,
                'username': '张三',
                'content': '您好，请问有什么可以帮助您的？',
                'is_user': False,
                'created_at': '2023-06-01 10:30:25'
            },
            {
                'id': 3,
                'user_id': 1001,
                'username': '张三',
                'content': '我的订单显示已完成，但是我没有收到退款',
                'is_user': True,
                'created_at': '2023-06-01 10:31:10'
            },
            {
                'id': 4,
                'user_id': 1001,
                'username': '张三',
                'content': '请提供您的订单号，我来为您查询',
                'is_user': False,
                'created_at': '2023-06-01 10:31:30'
            },
            {
                'id': 5,
                'user_id': 1002,
                'username': '李四',
                'content': '你好，我需要取消订单',
                'is_user': True,
                'created_at': '2023-06-02 14:20:10'
            },
            {
                'id': 6,
                'user_id': 1002,
                'username': '李四',
                'content': '您好，请问是哪个订单需要取消？',
                'is_user': False,
                'created_at': '2023-06-02 14:20:25'
            },
            {
                'id': 7,
                'user_id': 1003,
                'username': '王五',
                'content': '车辆到达时间是什么时候？',
                'is_user': True,
                'created_at': '2023-06-03 09:10:05'
            },
            {
                'id': 8,
                'user_id': 1003,
                'username': '王五',
                'content': '根据系统显示，您的车辆预计在5分钟内到达',
                'is_user': False,
                'created_at': '2023-06-03 09:10:30'
            }
        ]
        
        return render_template('users/ai_customer_service.html', 
                              sessions=sessions, 
                              all_messages=all_messages,
                              unique_users=3,
                              avg_chats_per_user=6.3,
                              today_chats=0,
                              avg_response_time=2.5)

@users_bp.route('/view-chat-history/<int:user_id>')
def view_chat_history(user_id):
    """查看用户聊天历史"""
    try:
        # 获取用户信息
        from app.dao.base_dao import BaseDAO
        
        # 打印调试信息
        print(f"正在查询用户ID: {user_id}")
        
        # 使用参数化查询，确保user_id作为整数处理
        user_query = "SELECT user_id, username, real_name FROM users WHERE user_id = %s"
        user_result = BaseDAO.execute_query(user_query, (int(user_id),))
        
        print(f"查询结果: {user_result}")
        
        # 如果没有找到用户，返回错误
        if not user_result or len(user_result) == 0:
            # 尝试直接从chat_records表获取用户ID确认
            check_query = "SELECT DISTINCT user_id FROM chat_records WHERE user_id = %s LIMIT 1"
            check_result = BaseDAO.execute_query(check_query, (int(user_id),))
            
            if not check_result or len(check_result) == 0:
                flash('用户不存在或没有聊天记录', 'error')
                return redirect(url_for('users.ai_customer_service'))
            
            # 用户在聊天记录中存在但在用户表中不存在，创建一个临时用户信息
            user_info = {
                'user_id': user_id,
                'username': f'用户{user_id}',
                'real_name': '未知'
            }
        else:
            user_info = user_result[0]
        
        # 获取聊天记录
        chat_query = """
        SELECT id, user_id, msg, is_user, created_at 
        FROM chat_records 
        WHERE user_id = %s 
        ORDER BY created_at ASC
        """
        chat_records = BaseDAO.execute_query(chat_query, (int(user_id),))
        
        if not chat_records or len(chat_records) == 0:
            flash('该用户没有聊天记录', 'warning')
            # 但仍然显示页面，只是没有聊天内容
        
        return render_template(
            'users/chat_history.html',
            user_info=user_info,
            chat_records=chat_records or []
        )
    except Exception as e:
        print(f"查看聊天历史出错: {str(e)}")
        flash(f'加载聊天历史失败: {str(e)}', 'error')
        return redirect(url_for('users.ai_customer_service'))