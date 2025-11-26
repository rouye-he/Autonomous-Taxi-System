from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import hashlib
import os
from sms_service import send_verify_code, verify_code
from email_service import init_mail, send_email_verify_code, verify_email_code  # 导入邮箱服务
from coze_service import coze_service
import datetime
import random
import string
import json
from sqlalchemy import text
from decimal import Decimal
from datetime import date, timedelta

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/autonomous_taxi_system'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False

CORS(app, supports_credentials=True)
db = SQLAlchemy(app)
mail = init_mail(app)  # 初始化邮件服务

# 全局变量，存储从数据库加载的参数
city_centers = {}
city_scale_factors = {}

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(50))
    phone = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(100), unique=True)
    gender = db.Column(db.String(10))
    birth_date = db.Column(db.Date)
    credit_score = db.Column(db.Integer, default=100)
    balance = db.Column(db.DECIMAL(10, 2), default=0.00)
    status = db.Column(db.Enum('正常', '禁用', '注销'), default='正常')
    avatar_url = db.Column(db.String(255))
    registration_time = db.Column(db.DateTime)
    last_login_time = db.Column(db.DateTime)
    registration_city = db.Column(db.String(50))
    registration_channel = db.Column(db.String(50))
    tags = db.Column(db.String(255))

class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer)
    vehicle_id = db.Column(db.Integer)
    order_status = db.Column(db.Enum('已结束', '进行中', '待分配', '已取消'), default='待分配')
    create_time = db.Column(db.DateTime)
    arrival_time = db.Column(db.DateTime)
    pickup_location = db.Column(db.String(255))
    pickup_location_x = db.Column(db.Integer)
    pickup_location_y = db.Column(db.Integer)
    dropoff_location = db.Column(db.String(255))
    dropoff_location_x = db.Column(db.Integer)
    dropoff_location_y = db.Column(db.Integer)
    city_code = db.Column(db.String(50))

class OrderDetail(db.Model): # 订单详情表
    __tablename__ = 'order_details'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), nullable=False) # 订单ID
    vehicle_id = db.Column(db.Integer, nullable=False) # 车辆ID
    user_id = db.Column(db.Integer, nullable=False) # 用户ID
    amount = db.Column(db.DECIMAL(10, 2), nullable=False) # 订单金额(元)
    distance = db.Column(db.DECIMAL(10, 2), nullable=False) # 行驶里程(km)
    payment_method = db.Column(db.Enum('微信支付', '支付宝', '银行卡', '余额支付'), default='微信支付') # 支付方式
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp()) # 创建时间
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp()) # 更新时间

class Coupon(db.Model):
    __tablename__ = 'coupons'
    coupon_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    coupon_type_id = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(50), nullable=False, default='平台发放')
    source_id = db.Column(db.Integer)
    receive_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    validity_start = db.Column(db.DateTime, nullable=False)
    validity_end = db.Column(db.DateTime, nullable=False)
    use_time = db.Column(db.DateTime)
    order_id = db.Column(db.String(50))
    status = db.Column(db.Enum('未使用', '已使用', '已过期'), default='未使用')

class SystemNotification(db.Model):
    __tablename__ = 'system_notifications'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(255))
    type = db.Column(db.String(20), nullable=False)  # vehicle/order/system
    priority = db.Column(db.String(10), default='通知')  # 通知/警告
    status = db.Column(db.String(10), default='未读')  # 未读/已读
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    read_at = db.Column(db.DateTime)

class UserNotification(db.Model):
    __tablename__ = 'user_notifications'
    notification_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    target_type = db.Column(db.Integer, nullable=False)  # 0=所有用户, 1=单个用户
    userid = db.Column(db.Integer)  # 目标用户ID，当target_type=1时使用
    is_read = db.Column(db.Boolean, default=False)  # 是否已读
    is_deleted = db.Column(db.Boolean, default=False)  # 是否已删除
    read_time = db.Column(db.DateTime)  # 阅读时间
    create_time = db.Column(db.DateTime, default=db.func.current_timestamp())  # 创建时间

class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)  # 使用订单ID
    user_id = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5星评分
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class SystemParameter(db.Model):
    __tablename__ = 'system_parameters'
    id = db.Column(db.Integer, primary_key=True)
    param_key = db.Column(db.String(100), unique=True, nullable=False)
    param_value = db.Column(db.Text, nullable=False)
    param_type = db.Column(db.Enum('int', 'float', 'string', 'boolean', 'json', 'array'), nullable=False)
    updated_at = db.Column(db.DateTime)

class CouponPackage(db.Model):
    __tablename__ = 'coupon_packages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.DECIMAL(10, 2), nullable=False)
    original_price = db.Column(db.DECIMAL(10, 2), nullable=False)
    status = db.Column(db.Integer, default=1)  # 1:上架, 0:下架
    validity_days = db.Column(db.Integer, default=30)
    coupon_details = db.Column(db.JSON, nullable=False)
    sale_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class CouponType(db.Model):
    __tablename__ = 'coupon_types'
    id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(50), nullable=False)
    coupon_category = db.Column(db.Enum('满减券', '折扣券'), nullable=True)
    value = db.Column(db.DECIMAL(10, 2), nullable=False)
    min_amount = db.Column(db.DECIMAL(10, 2), default=0.00)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# 信用等级规则表模型
class CreditLevelRule(db.Model):
    __tablename__ = 'credit_level_rules'
    level_id = db.Column(db.Integer, primary_key=True)
    level_name = db.Column(db.String(50), nullable=False, unique=True)
    min_score = db.Column(db.Integer, nullable=False)
    max_score = db.Column(db.Integer, nullable=False)
    benefits = db.Column(db.Text)
    limitations = db.Column(db.Text)
    icon_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

# 信用分变动规则表模型
class CreditRule(db.Model):
    __tablename__ = 'credit_rules'
    rule_id = db.Column(db.Integer, primary_key=True)
    rule_name = db.Column(db.String(64), nullable=False)
    rule_type = db.Column(db.Enum('奖励', '惩罚', '恢复'), nullable=False)
    trigger_event = db.Column(db.String(128), nullable=False)
    score_change = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

# 用户信用变动记录表模型
class UserCreditLog(db.Model):
    __tablename__ = 'user_credit_logs'
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    change_amount = db.Column(db.Integer, nullable=False)
    credit_before = db.Column(db.Integer, nullable=False)
    credit_after = db.Column(db.Integer, nullable=False)
    change_type = db.Column(db.Enum('订单完成', '违规行为', '系统奖励', '定期恢复', '人工修改'), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    related_order_id = db.Column(db.String(50))
    operator = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Income(db.Model):
    __tablename__ = 'income'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.DECIMAL(10, 2), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer)
    order_id = db.Column(db.String(50))
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Expense(db.Model):
    __tablename__ = 'expense'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.DECIMAL(10, 2), nullable=False)
    type = db.Column(db.Enum('车辆支出', '充电站支出', '其他支出', '提现支出'), nullable=False)
    vehicle_id = db.Column(db.Integer)
    charging_station_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Vehicle(db.Model): #车辆信息表
    __tablename__ = 'vehicles'
    vehicle_id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), nullable=False) #车牌号
    vin = db.Column(db.String(50), nullable=False, unique=True) #车辆识别号
    model = db.Column(db.String(50), nullable=False) #车辆型号
    manufacture_date = db.Column(db.Date) #制造日期
    registration_date = db.Column(db.Date) #注册日期
    current_status = db.Column(db.Enum('空闲中', '运行中', '充电中', '电量不足', '等待充电', '前往充电', '维护中'), default='空闲中') #当前状态
    battery_level = db.Column(db.Integer, default=100) #电池电量百分比
    mileage = db.Column(db.Integer, default=0) #总里程数
    current_location_x = db.Column(db.Integer) #当前位置X坐标
    current_location_y = db.Column(db.Integer) #当前位置Y坐标
    current_city = db.Column(db.String(50)) #当前所在城市
    current_location_name = db.Column(db.String(255)) #当前位置名称
    operating_city = db.Column(db.String(50)) #运营城市
    last_maintenance_date = db.Column(db.Date) #上次维护日期
    next_maintenance_date = db.Column(db.Date) #下次维护日期
    purchase_price = db.Column(db.DECIMAL(10, 2)) #购买价格
    daily_income = db.Column(db.DECIMAL(10, 2), default=0.00) #日收入
    total_orders = db.Column(db.Integer, default=0) #总订单数
    rating = db.Column(db.DECIMAL(3, 1), default=5.0) #车辆评分
    is_available = db.Column(db.Boolean, default=True) #是否可用
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class ChatRecord(db.Model): #对话记录表
    __tablename__ = 'chat_records'
    id = db.Column(db.Integer, primary_key=True) #记录ID
    user_id = db.Column(db.Integer, nullable=False) #用户ID
    msg = db.Column(db.Text, nullable=False) #消息内容
    is_user = db.Column(db.Boolean, nullable=False) #是否用户消息(1用户0客服)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp()) #发送时间

# 从数据库加载城市参数
def load_city_parameters():
    global city_centers, city_scale_factors
    
    try:
        # 先尝试清空之前可能加载的错误数据
        city_centers = {}
        city_scale_factors = {}
        
        print("开始从数据库加载城市参数...")
        
        # 加载系统参数表中的所有参数
        all_params = SystemParameter.query.all()
        print(f"找到系统参数记录总数: {len(all_params)}")
        
        # 打印所有参数键值，以便调试
        for param in all_params:
            print(f"参数: {param.param_key} = {param.param_value[:30]}... (类型: {param.param_type})")
        
        # 加载城市中心点坐标
        centers_param = SystemParameter.query.filter_by(param_key='city_centers').first()
        if not centers_param:
            # 尝试不同的大小写或格式
            centers_param = SystemParameter.query.filter(SystemParameter.param_key.like('%city%center%')).first()
            print(f"尝试模糊匹配city_centers参数: {centers_param and centers_param.param_key}")
        
        if centers_param and centers_param.param_value:
            try:
                city_centers = json.loads(centers_param.param_value)
                print(f"成功加载city_centers参数，包含城市数量: {len(city_centers)}")
                print(f"city_centers示例: {list(city_centers.items())[:2]}")
            except json.JSONDecodeError as e:
                raise ValueError(f"city_centers参数解析失败: {e}，原始值: {centers_param.param_value[:100]}")
        else:
            raise ValueError("数据库中未找到city_centers参数")
            
        # 加载城市缩放比例因子
        scale_factors_param = SystemParameter.query.filter_by(param_key='city_scale_factors').first()
        if not scale_factors_param:
            # 尝试不同的大小写或格式
            scale_factors_param = SystemParameter.query.filter(SystemParameter.param_key.like('%city%scale%')).first()
            print(f"尝试模糊匹配city_scale_factors参数: {scale_factors_param and scale_factors_param.param_key}")
        
        if scale_factors_param and scale_factors_param.param_value:
            try:
                city_scale_factors = json.loads(scale_factors_param.param_value)
                print(f"成功加载city_scale_factors参数，包含城市数量: {len(city_scale_factors)}")
                print(f"city_scale_factors示例: {list(city_scale_factors.items())[:2]}")
            except json.JSONDecodeError as e:
                raise ValueError(f"city_scale_factors参数解析失败: {e}，原始值: {scale_factors_param.param_value[:100]}")
        else:
            raise ValueError("数据库中未找到city_scale_factors参数")
            
        # 验证参数是否有效
        if not city_centers or not city_scale_factors:
            raise ValueError("城市参数加载不完整")
            
        # 验证常见城市是否存在
        common_cities = ["北京市", "上海市", "广州市"]
        for city in common_cities:
            if city in city_centers:
                print(f"城市 {city} 中心点坐标: {city_centers[city]}")
            else:
                print(f"警告: 城市 {city} 在city_centers中不存在")
                
            if city in city_scale_factors:
                print(f"城市 {city} 缩放因子: {city_scale_factors[city]}")
            else:
                print(f"警告: 城市 {city} 在city_scale_factors中不存在")
                
        print("城市参数加载成功，共加载城市数量:", len(city_centers))
        return True
    except Exception as e:
        print(f"加载城市参数出错: {e}")
        # 不要使用默认值，确保出错时能明确知道
        city_centers = {}
        city_scale_factors = {}
        raise Exception(f"加载城市参数出错: {e}")

# 将经纬度转换为系统内部坐标(0-999整数)
def geo_to_system_coordinates(longitude, latitude, city):
    # 检查城市参数是否存在
    if city not in city_centers or city not in city_scale_factors:
        raise ValueError(f"未找到城市信息: {city}，请确保数据库中包含该城市的参数")
    
    # 获取对应城市的中心点经纬度和缩放因子
    center_longitude, center_latitude = city_centers[city]
    scale_factor = city_scale_factors[city]
    
    # 使用高精度浮点数计算
    # 转换公式: x坐标 = 500 + (经度 - 城市中心经度) / 城市缩放因子
    x_float = 500.0 + ((float(longitude) - float(center_longitude))*500.0 / float(scale_factor))
    # 转换公式: y坐标 = 500 - (纬度 - 城市中心纬度) / 城市缩放因子
    y_float = 500.0 - ((float(latitude) - float(center_latitude))*500.0 / float(scale_factor))
    
    # 最终结果转换为整数
    x = int(round(x_float))
    y = int(round(y_float))
    
    # 确保坐标在0-999范围内
    x = max(0, min(999, x))
    y = max(0, min(999, y))
    
    print(f"转换坐标: 经度={longitude}, 纬度={latitude} => x={x}, y={y}")
    print(f"中心点: 经度={center_longitude}, 纬度={center_latitude}, 缩放因子={scale_factor}")
    print(f"计算过程: x_float={x_float}, y_float={y_float}")
    
    return {"x": x, "y": y}

# 将系统内部坐标(0-999整数)转换为经纬度
def system_to_geo_coordinates(x, y, city):
    # 检查城市参数是否存在
    if city not in city_centers or city not in city_scale_factors:
        raise ValueError(f"未找到城市信息: {city}，请确保数据库中包含该城市的参数")
    
    # 获取对应城市的中心点经纬度和缩放因子
    center_longitude, center_latitude = city_centers[city]
    scale_factor = city_scale_factors[city]
    
    # 使用高精度浮点数计算
    # 转换公式: 经度 = 城市中心经度 + (x坐标 - 500) * 城市缩放因子
    longitude = float(center_longitude) + ((float(x) - 500.0) * float(scale_factor)/500.0)
    # 转换公式: 纬度 = 城市中心纬度 + (y坐标 - 500) * 城市缩放因子
    latitude = float(center_latitude) - ((float(y) - 500.0) * float(scale_factor)/500.0)
    
    return {"longitude": longitude, "latitude": latitude}

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'code': 400, 'message': '邮箱和密码不能为空'}), 400
    
    # 查询用户
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404
    
    # 明文密码直接比较（演示系统）
    if user.password != password:
        return jsonify({'code': 401, 'message': '密码错误'}), 401
    
    if user.status != '正常':
        return jsonify({'code': 403, 'message': '账号已被禁用或注销'}), 403
    
    # 存储用户信息到session
    session['user_id'] = user.user_id
    session['username'] = user.username
    
    return jsonify({
        'code': 0,  # 修改返回码为0以匹配小程序中的判断逻辑
        'message': '登录成功',
        'data': {
            'token': 'token_' + str(user.user_id),  # 生成简单token
            'userInfo': {
                'user_id': user.user_id,
                'username': user.username,
                'phone': user.phone,
                'real_name': user.real_name,
                'credit_score': user.credit_score,
                'balance': float(user.balance) if user.balance else 0,
                'avatar_url': user.avatar_url
            }
        }
    })

@app.route('/api/send_verify_code', methods=['POST'])
def send_code():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'code': 400, 'message': '邮箱不能为空'}), 400
    
    # 发送邮箱验证码（注册时不需要验证邮箱是否存在）
    result = send_email_verify_code(mail, email)
    
    if result['success']:
        return jsonify({
            'code': 0,
            'message': '验证码发送成功'
        })
    else:
        return jsonify({
            'code': 500,
            'message': result['message']
        }), 500

@app.route('/api/send_login_verify_code', methods=['POST'])
def send_login_code():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'code': 400, 'message': '邮箱不能为空'}), 400
    
    # 验证邮箱是否存在
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'code': 404, 'message': '该邮箱未注册'}), 404
    
    # 发送邮箱验证码
    result = send_email_verify_code(mail, email)
    
    if result['success']:
        return jsonify({
            'code': 0,
            'message': '验证码发送成功'
        })
    else:
        return jsonify({
            'code': 500,
            'message': result['message']
        }), 500

@app.route('/api/login_by_code', methods=['POST'])
def login_by_code():
    data = request.get_json()
    email = data.get('email')
    code = data.get('verifyCode')
    
    if not email or not code:
        return jsonify({'code': 400, 'message': '邮箱和验证码不能为空'}), 400
    
    # 验证邮箱验证码
    verify_result = verify_email_code(email, code)
    
    if not verify_result['success']:
        return jsonify({
            'code': 401,
            'message': verify_result['message']
        }), 401
    
    # 查询用户
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404
    
    if user.status != '正常':
        return jsonify({'code': 403, 'message': '账号已被禁用或注销'}), 403
    
    # 存储用户信息到session
    session['user_id'] = user.user_id
    session['username'] = user.username
    
    return jsonify({
        'code': 0,
        'message': '登录成功',
        'data': {
            'token': 'token_' + str(user.user_id),
            'userInfo': {
                'user_id': user.user_id,
                'username': user.username,
                'phone': user.phone,
                'real_name': user.real_name,
                'credit_score': user.credit_score,
                'balance': float(user.balance) if user.balance else 0,
                'avatar_url': user.avatar_url
            }
        }
    })

@app.route('/api/register', methods=['POST']) # #新增注册API
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    registration_city = data.get('registration_city')
    verify_code = data.get('verifyCode')
    
    # 验证必填字段
    if not username or not password or not email or not registration_city or not verify_code:
        return jsonify({'code': 400, 'message': '用户名、密码、邮箱、注册城市和验证码不能为空'}), 400
    
    # 检查用户名是否已存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'code': 400, 'message': '用户名已存在'}), 400
    
    # 检查邮箱是否已存在
    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({'code': 400, 'message': '邮箱已被注册'}), 400
    
    # 验证邮箱验证码
    verify_result = verify_email_code(email, verify_code)
    if not verify_result['success']:
        return jsonify({'code': 401, 'message': verify_result['message']}), 401
    
    try:
        # 创建新用户
        new_user = User(
            username=username,
            password=password,  # #演示系统使用明文密码
            email=email,
            registration_city=registration_city,
            registration_time=datetime.datetime.now(),
            credit_score=100,
            balance=0.00,
            status='正常'
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': '注册成功',
            'data': {
                'user_id': new_user.user_id,
                'username': new_user.username,
                'email': new_user.email
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'注册失败: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'code': 200, 'message': '退出登录成功'})

@app.route('/api/user/current', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'code': 401, 'message': '用户未登录'}), 401
    
    user = User.query.get(user_id)
    if not user:
        session.clear()
        return jsonify({'code': 404, 'message': '用户不存在'}), 404
    
    return jsonify({
        'code': 200,
        'message': '获取用户信息成功',
        'data': {
            'user_id': user.user_id,
            'username': user.username,
            'real_name': user.real_name,
            'credit_score': user.credit_score,
            'balance': float(user.balance) if user.balance else 0,
            'avatar_url': user.avatar_url
        }
    })

@app.route('/api/user/detail', methods=['GET'])
def get_user_detail():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 查询用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取用户的订单数量（所有状态的订单）
        total_orders = Order.query.filter_by(user_id=user_id).count()
        
        # 获取用户未使用的优惠券数量
        coupon_count = Coupon.query.filter_by(user_id=user_id, status='未使用').count()
        
        # 构建用户详细信息（只包含模型中存在的字段）
        user_detail = {
            'user_id': user.user_id,
            'username': user.username,
            'real_name': user.real_name or '',
            'phone': user.phone or '',
            'email': user.email or '',
            'credit_score': user.credit_score or 100,
            'balance': float(user.balance) if user.balance else 0,
            'avatar_url': user.avatar_url or '',
            'status': user.status or '正常',
            'total_orders': total_orders,
            'coupon_count': coupon_count
        }
        
        # 尝试添加额外字段（如果模型中存在）
        try:
            if hasattr(user, 'gender'):
                user_detail['gender'] = user.gender or ''
        except: pass
        
        try:
            if hasattr(user, 'birth_date') and user.birth_date:
                user_detail['birth_date'] = user.birth_date.strftime('%Y-%m-%d')
        except: pass
        
        try:
            if hasattr(user, 'registration_time') and user.registration_time:
                user_detail['registration_time'] = user.registration_time.strftime('%Y-%m-%d %H:%M:%S')
        except: pass
        
        try: 
            if hasattr(user, 'last_login_time') and user.last_login_time:
                user_detail['last_login_time'] = user.last_login_time.strftime('%Y-%m-%d %H:%M:%S')
        except: pass
        
        try:
            if hasattr(user, 'registration_city'):
                user_detail['registration_city'] = user.registration_city or ''
        except: pass
        
        try:
            if hasattr(user, 'registration_channel'):
                user_detail['registration_channel'] = user.registration_channel or ''
        except: pass
        
        try:
            if hasattr(user, 'tags'):
                user_detail['tags'] = user.tags or ''
        except: pass
        
        print(f"用户详细信息API返回数据: {user_detail}")
        
        return jsonify({
            'code': 0,
            'message': '获取用户详细信息成功',
            'data': user_detail
        })
    except Exception as e:
        print(f"获取用户详细信息出错: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取用户详细信息出错: {str(e)}'}), 500

# 修改密码API
@app.route('/api/user/change_password', methods=['POST'])
def change_password():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据为空'}), 400
        
        old_password = data.get('oldPassword')
        new_password = data.get('newPassword')
        
        if not old_password or not new_password:
            return jsonify({'code': 400, 'message': '旧密码和新密码不能为空'}), 400
        
        # 验证旧密码
        if user.password != old_password:
            return jsonify({'code': 400, 'message': '旧密码错误'}), 400
        
        # 更新新密码（明文存储）
        user.password = new_password
        
        # 保存到数据库
        db.session.commit()
        
        print(f"用户 {user.username} 修改密码成功")
        
        return jsonify({
            'code': 0,
            'message': '密码修改成功',
            'data': {}
        })
    except Exception as e:
        db.session.rollback()
        print(f"修改密码失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'修改密码失败: {str(e)}'}), 500

# 更新用户资料API
@app.route('/api/user/update_profile', methods=['POST'])
def update_profile():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据为空'}), 400
        
        # 验证用户名唯一性（如果修改了用户名）
        new_username = data.get('username', '').strip()
        if new_username and new_username != user.username:
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user:
                return jsonify({'code': 400, 'message': '用户名已存在'}), 400
        
        # 验证邮箱唯一性（如果修改了邮箱）
        new_email = data.get('email', '').strip()
        if new_email and new_email != user.email:
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user:
                return jsonify({'code': 400, 'message': '邮箱已被使用'}), 400
        
        # 更新用户信息
        if new_username:
            user.username = new_username
        
        if data.get('real_name') is not None:
            user.real_name = data.get('real_name').strip()
        
        if new_email:
            user.email = new_email
        
        if data.get('gender') is not None:
            user.gender = data.get('gender')
        
        if data.get('birth_date') is not None:
            birth_date_str = data.get('birth_date')
            if birth_date_str:
                try:
                    from datetime import datetime
                    user.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'code': 400, 'message': '出生日期格式错误'}), 400
            else:
                user.birth_date = None
        
        # 保存到数据库
        db.session.commit()
        
        print(f"用户 {user.username} 更新资料成功")
        
        return jsonify({
            'code': 0,
            'message': '资料更新成功',
            'data': {}
        })
    except Exception as e:
        db.session.rollback()
        print(f"更新用户资料失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'更新用户资料失败: {str(e)}'}), 500

# 生成订单编号
def generate_order_number():
    now = datetime.datetime.now()
    date_part = now.strftime('%Y%m%d')
    random_part = ''.join(random.choices(string.digits, k=6))
    return f'O{date_part}{random_part}'

# 创建订单API
@app.route('/api/create_order', methods=['POST'])
def create_order():
    try:
        # 确保城市参数已加载
        if not city_centers or not city_scale_factors:
            try:
                print("城市参数未加载，尝试重新加载...")
                load_city_parameters()
            except Exception as param_error:
                return jsonify({'code': 500, 'message': f'加载城市参数失败: {str(param_error)}'}), 500
        
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据为空'}), 400
        
        # 获取必要参数
        pickup_location = data.get('pickupLocation')
        dropoff_location = data.get('dropoffLocation')
        city_code = data.get('cityCode')
        
        if not pickup_location or not dropoff_location or not city_code:
            return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
            
        print(f"处理订单请求: 城市={city_code}")
        
        # 检查城市是否在支持列表中
        if city_code not in city_centers or city_code not in city_scale_factors:
            return jsonify({
                'code': 400, 
                'message': f'不支持的城市: {city_code}，支持的城市有: {list(city_centers.keys())}'
            }), 400
        
        # 获取经纬度数据
        pickup_lng = pickup_location.get('longitude')
        pickup_lat = pickup_location.get('latitude')
        
        dropoff_lng = dropoff_location.get('longitude')
        dropoff_lat = dropoff_location.get('latitude')
        
        if pickup_lng is None or pickup_lat is None or dropoff_lng is None or dropoff_lat is None:
            return jsonify({'code': 400, 'message': '经纬度数据不完整'}), 400
            
        print(f"接收到坐标: 起点({pickup_lat}, {pickup_lng}), 终点({dropoff_lat}, {dropoff_lng})")
        
        # 将经纬度转换为系统内部坐标
        try:
            pickup_coords = geo_to_system_coordinates(pickup_lng, pickup_lat, city_code)
            dropoff_coords = geo_to_system_coordinates(dropoff_lng, dropoff_lat, city_code)
            
            print(f"转换后坐标: 起点({pickup_coords['x']}, {pickup_coords['y']}), 终点({dropoff_coords['x']}, {dropoff_coords['y']})")
        except ValueError as e:
            return jsonify({'code': 400, 'message': str(e)}), 400
        
        # 创建新订单
        new_order = Order(
            order_number=generate_order_number(),
            user_id=user_id,
            vehicle_id=None,  # 暂时为空，后续由系统分配
            order_status='待分配',
            create_time=datetime.datetime.now(),
            arrival_time=None,  # 暂时为空，后续由系统更新
            pickup_location=f"({pickup_lat}, {pickup_lng})",
            pickup_location_x=pickup_coords['x'],
            pickup_location_y=pickup_coords['y'],
            dropoff_location=f"({dropoff_lat}, {dropoff_lng})",
            dropoff_location_x=dropoff_coords['x'],
            dropoff_location_y=dropoff_coords['y'],
            city_code=city_code
        )
        
        # 保存到数据库
        db.session.add(new_order)
        db.session.commit()
        
        print(f"订单创建成功: {new_order.order_number}")
        
        return jsonify({
            'code': 0,
            'message': '订单创建成功',
            'data': {
                'order_id': new_order.order_id,
                'order_number': new_order.order_number,
                'order_status': new_order.order_status,
                'create_time': new_order.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'pickup_coords': pickup_coords,
                'dropoff_coords': dropoff_coords
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"订单创建失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'订单创建失败: {str(e)}'}), 500

# 获取用户订单列表API
@app.route('/api/user/orders', methods=['GET'])
def get_user_orders():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取查询参数
        status = request.args.get('status')  # 订单状态筛选
        page = int(request.args.get('page', 1))  # 页码
        per_page = int(request.args.get('per_page', 20))  # 每页数量
        
        # 构建查询
        query = Order.query.filter_by(user_id=user_id)
        
        # 状态筛选
        if status and status != 'all':
            if status == '待分配':
                query = query.filter_by(order_status='待分配')
            elif status == '进行中':
                query = query.filter_by(order_status='进行中')
            elif status == '已结束':
                query = query.filter_by(order_status='已结束')
            elif status == '已取消':
                query = query.filter_by(order_status='已取消')
        
        # 按创建时间倒序排列
        query = query.order_by(Order.create_time.desc())
        
        # 分页查询
        orders = query.offset((page - 1) * per_page).limit(per_page).all()
        total = query.count()
        
        # 构建订单列表
        order_list = []
        for order in orders:
            # 获取订单详情（金额和距离）- 使用正确的表结构
            order_detail_query = text("""
                SELECT amount, distance, payment_method 
                FROM order_details 
                WHERE order_id = :order_id
            """)
            order_detail = db.session.execute(order_detail_query, {'order_id': str(order.order_id)}).first()
            
            # 查询该订单是否使用了优惠券（仅已结束订单）
            original_price = None
            final_price = None
            coupon_info = "未使用优惠"
            
            if order.order_status == '已结束' and order_detail:
                used_coupon = Coupon.query.filter_by(order_id=str(order.order_id), status='已使用').first()
                
                original_price = float(order_detail.amount)
                final_price = float(order_detail.amount)
                
                if used_coupon:
                    # 获取优惠券类型信息
                    coupon_type_query = text("""
                        SELECT type_name, coupon_category, value, min_amount
                        FROM coupon_types 
                        WHERE id = :coupon_type_id
                    """)
                    coupon_type = db.session.execute(coupon_type_query, {'coupon_type_id': used_coupon.coupon_type_id}).first()
                    
                    if coupon_type:
                        if coupon_type.coupon_category == '折扣券':
                            # 折扣券：原价 = 实付金额 / 折扣率
                            original_price = final_price / float(coupon_type.value)
                            coupon_info = f"使用{coupon_type.type_name}"
                        elif coupon_type.coupon_category == '满减券':
                            # 满减券：原价 = 实付金额 + 减免金额
                            original_price = final_price + float(coupon_type.value)
                            coupon_info = f"使用{coupon_type.type_name}"
            
            order_data = {
                'order_id': order.order_id,
                'order_number': order.order_number,
                'status': order.order_status,
                'create_time': order.create_time.strftime('%Y-%m-%d %H:%M:%S') if order.create_time else '',
                'arrival_time': order.arrival_time.strftime('%Y-%m-%d %H:%M:%S') if order.arrival_time else '',
                'pickup_location': order.pickup_location or '',
                'pickup_location_x': order.pickup_location_x,  # 起点系统坐标X
                'pickup_location_y': order.pickup_location_y,  # 起点系统坐标Y
                'dropoff_location': order.dropoff_location or '',
                'dropoff_location_x': order.dropoff_location_x,  # 终点系统坐标X
                'dropoff_location_y': order.dropoff_location_y,  # 终点系统坐标Y
                'city_code': order.city_code or '',
                'vehicle_id': order.vehicle_id,
                'amount': float(order_detail.amount) if order_detail and order_detail.amount else 0,
                'distance': float(order_detail.distance) if order_detail and order_detail.distance else 0,
                'payment_method': order_detail.payment_method if order_detail else '',
                'original_price': original_price, # 原价
                'final_price': final_price, # 实付价格
                'coupon_info': coupon_info # 优惠券信息
            }
            order_list.append(order_data)
        
        print(f"用户 {user_id} 订单查询成功，共 {len(order_list)} 条记录")
        
        return jsonify({
            'code': 0,
            'message': '获取订单列表成功',
            'data': {
                'orders': order_list,
                'total': total,
                'page': page,
                'per_page': per_page,
                'has_more': total > page * per_page
            }
        })
    except Exception as e:
        print(f"获取用户订单失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取订单列表失败: {str(e)}'}), 500

# 取消订单API
@app.route('/api/user/cancel_order', methods=['POST'])
def cancel_order():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据为空'}), 400
        
        order_number = data.get('order_number')
        cancel_reason = data.get('cancel_reason', '用户主动取消')
        
        if not order_number:
            return jsonify({'code': 400, 'message': '订单号不能为空'}), 400
        
        # 验证订单是否存在且属于该用户
        order = Order.query.filter_by(order_number=order_number, user_id=user_id).first()
        if not order:
            return jsonify({'code': 404, 'message': '订单不存在或无权限'}), 404
        
        # 检查订单状态是否可以取消
        if order.order_status not in ['待分配']:
            return jsonify({'code': 400, 'message': f'订单状态为"{order.order_status}"，无法取消'}), 400
        
        # 更新订单状态为已取消
        order.order_status = '已取消'
        
        # 创建系统通知
        notification_title = f"订单取消通知"
        notification_content = f"用户{user.username}(ID:{user_id})取消了订单{order_number}。取消原因：{cancel_reason}。原订单状态：待分配。"
        
        new_notification = SystemNotification(
            title=notification_title,
            content=notification_content,
            type='order',  # 订单相关
            priority='通知',  # 取消订单设为通知级别
            status='未读'
        )
        
        # 保存到数据库
        db.session.add(new_notification)
        db.session.commit()
        
        print(f"用户 {user.username} 取消订单 {order_number}，原因：{cancel_reason}")
        
        return jsonify({
            'code': 0,
            'message': '订单取消成功',
            'data': {
                'order_number': order_number,
                'cancel_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"取消订单失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'取消订单失败: {str(e)}'}), 500

# 上报异常API
@app.route('/api/user/report_issue', methods=['POST'])
def report_issue():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据为空'}), 400
        
        order_number = data.get('order_number')
        issue_type = data.get('issue_type')
        description = data.get('description', '')
        
        if not order_number or not issue_type:
            return jsonify({'code': 400, 'message': '订单号和异常类型不能为空'}), 400
        
        # 验证订单是否存在且属于该用户
        order = Order.query.filter_by(order_number=order_number, user_id=user_id).first()
        if not order:
            return jsonify({'code': 404, 'message': '订单不存在或无权限'}), 404
        
        # 创建系统通知
        notification_title = f"用户异常上报 - {issue_type}"
        notification_content = f"用户{user.username}(ID:{user_id})在订单{order_number}中上报异常。异常类型：{issue_type}。详细描述：{description}。订单状态：{order.order_status}。请及时处理。"
        
        new_notification = SystemNotification(
            title=notification_title,
            content=notification_content,
            type='order',  # 订单相关异常
            priority='警告',  # 异常上报设为警告级别
            status='未读'
        )
        
        # 保存到数据库
        db.session.add(new_notification)
        db.session.commit()
        
        print(f"用户 {user.username} 上报订单 {order_number} 异常：{issue_type}")
        
        return jsonify({
            'code': 0,
            'message': '异常上报成功，我们会尽快处理',
            'data': {
                'notification_id': new_notification.id,
                'report_time': new_notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"上报异常失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'上报异常失败: {str(e)}'}), 500

# 提交评价API
@app.route('/api/user/submit_evaluation', methods=['POST'])
def submit_evaluation():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据为空'}), 400
        
        order_number = data.get('order_number')
        rating = data.get('rating')
        comment = data.get('comment', '')
        
        if not order_number or not rating:
            return jsonify({'code': 400, 'message': '订单号和评分不能为空'}), 400
        
        # 验证评分范围
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({'code': 400, 'message': '评分必须是1-5之间的整数'}), 400
        
        # 验证订单是否存在且属于该用户
        order = Order.query.filter_by(order_number=order_number, user_id=user_id).first()
        if not order:
            return jsonify({'code': 404, 'message': '订单不存在或无权限'}), 404
        
        # 检查订单状态是否为已结束
        if order.order_status != '已结束':
            return jsonify({'code': 400, 'message': f'订单状态为"{order.order_status}"，只有已结束的订单才能评价'}), 400
        
        # 检查是否已经评价过
        existing_evaluation = Evaluation.query.filter_by(order_id=order.order_id, user_id=user_id).first()
        if existing_evaluation:
            return jsonify({'code': 400, 'message': '该订单已经评价过了'}), 400
        
        # 创建评价记录
        new_evaluation = Evaluation(
            order_id=order.order_id,
            user_id=user_id,
            rating=rating,
            comment=comment
        )
        
        # 保存到数据库
        db.session.add(new_evaluation)
        db.session.commit()
        
        # 更新车辆评分
        if order.vehicle_id:
            update_vehicle_rating(order.vehicle_id)
        
        print(f"用户 {user.username} 对订单 {order_number} 提交评价：{rating}星")
        
        return jsonify({
            'code': 0,
            'message': '评价提交成功',
            'data': {
                'evaluation_id': new_evaluation.id,
                'order_id': order.order_id,
                'order_number': order_number,
                'rating': rating,
                'comment': comment,
                'created_at': new_evaluation.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"提交评价失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'提交评价失败: {str(e)}'}), 500

# 检查订单是否已评价API
@app.route('/api/user/check_evaluation', methods=['GET'])
def check_evaluation():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 获取订单号
        order_number = request.args.get('order_number')
        if not order_number:
            return jsonify({'code': 400, 'message': '订单号不能为空'}), 400
        
        # 验证订单是否存在且属于该用户
        order = Order.query.filter_by(order_number=order_number, user_id=user_id).first()
        if not order:
            return jsonify({'code': 404, 'message': '订单不存在或无权限'}), 404
        
        # 检查是否已经评价过
        existing_evaluation = Evaluation.query.filter_by(order_id=order.order_id, user_id=user_id).first()
        
        return jsonify({
            'code': 0,
            'message': '检查成功',
            'data': {
                'order_id': order.order_id,
                'order_number': order_number,
                'has_evaluated': existing_evaluation is not None,
                'evaluation': {
                    'id': existing_evaluation.id,
                    'rating': existing_evaluation.rating,
                    'comment': existing_evaluation.comment,
                    'created_at': existing_evaluation.created_at.strftime('%Y-%m-%d %H:%M:%S')
                } if existing_evaluation else None
            }
        })
    except Exception as e:
        print(f"检查评价失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'检查评价失败: {str(e)}'}), 500

# 获取用户评价列表API
@app.route('/api/user/evaluations', methods=['GET'])
def get_user_evaluations():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status = request.args.get('status', 'all')  # all/pending/completed
        
        # 获取用户的已结束订单
        orders_query = Order.query.filter_by(user_id=user_id, order_status='已结束')
        
        # 根据状态筛选
        if status == 'pending':
            # 待评价：已结束但未评价的订单
            evaluated_order_ids = db.session.query(Evaluation.order_id).filter_by(user_id=user_id).subquery()
            orders_query = orders_query.filter(~Order.order_id.in_(evaluated_order_ids))
        elif status == 'completed':
            # 已评价：已结束且已评价的订单
            evaluated_order_ids = db.session.query(Evaluation.order_id).filter_by(user_id=user_id).subquery()
            orders_query = orders_query.filter(Order.order_id.in_(evaluated_order_ids))
        
        # 分页查询
        orders_pagination = orders_query.order_by(Order.create_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        orders = orders_pagination.items
        evaluation_list = []
        
        for order in orders:
            # 获取订单详情（金额和距离）- 使用正确的表结构
            order_detail_query = text("""
                SELECT amount, distance, payment_method 
                FROM order_details 
                WHERE order_id = :order_id
            """)
            order_detail = db.session.execute(order_detail_query, {'order_id': str(order.order_id)}).first()
            
            # 获取评价信息
            evaluation = Evaluation.query.filter_by(order_id=order.order_id, user_id=user_id).first()
            
            evaluation_data = {
                'order_id': order.order_id,
                'order_number': order.order_number,
                'status': order.order_status,
                'create_time': order.create_time.strftime('%Y-%m-%d %H:%M:%S') if order.create_time else '',
                'arrival_time': order.arrival_time.strftime('%Y-%m-%d %H:%M:%S') if order.arrival_time else '',
                'pickup_location': order.pickup_location or '',
                'pickup_location_x': order.pickup_location_x,  # 起点系统坐标X
                'pickup_location_y': order.pickup_location_y,  # 起点系统坐标Y
                'dropoff_location': order.dropoff_location or '',
                'dropoff_location_x': order.dropoff_location_x,  # 终点系统坐标X
                'dropoff_location_y': order.dropoff_location_y,  # 终点系统坐标Y
                'city_code': order.city_code or '',
                'vehicle_id': order.vehicle_id,
                'amount': float(order_detail.amount) if order_detail and order_detail.amount else 0,
                'distance': float(order_detail.distance) if order_detail and order_detail.distance else 0,
                'payment_method': order_detail.payment_method if order_detail else '',
                'rating': evaluation.rating if evaluation else None,
                'comment': evaluation.comment if evaluation else None,
                'evaluation_time': evaluation.created_at.strftime('%Y-%m-%d %H:%M:%S') if evaluation else None
            }
            evaluation_list.append(evaluation_data)
        
        # 统计数据
        total_completed_orders = Order.query.filter_by(user_id=user_id, order_status='已结束').count()
        total_evaluations = Evaluation.query.filter_by(user_id=user_id).count()
        pending_evaluations = total_completed_orders - total_evaluations
        
        return jsonify({
            'code': 0,
            'message': '获取评价列表成功',
            'data': {
                'evaluations': evaluation_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': orders_pagination.total,
                    'pages': orders_pagination.pages,
                    'has_next': orders_pagination.has_next,
                    'has_prev': orders_pagination.has_prev
                },
                'stats': {
                    'total_completed_orders': total_completed_orders,
                    'total_evaluations': total_evaluations,
                    'pending_evaluations': pending_evaluations
                }
            }
        })
    except Exception as e:
        print(f"获取评价列表失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取评价列表失败: {str(e)}'}), 500

# 获取优惠券包列表API
@app.route('/api/coupon/packages', methods=['GET'])
def get_coupon_packages():
    try:
        # 获取所有上架的优惠券包
        packages = CouponPackage.query.filter_by(status=1).all()
        
        package_list = []
        for package in packages:
            # 获取套餐包含的优惠券类型详情
            coupon_details = []
            if package.coupon_details:
                for type_id, count in package.coupon_details.items():
                    coupon_type = CouponType.query.get(int(type_id))
                    if coupon_type:
                        coupon_details.append({
                            'type_name': coupon_type.type_name,
                            'category': coupon_type.coupon_category,
                            'value': float(coupon_type.value),
                            'min_amount': float(coupon_type.min_amount),
                            'count': count,
                            'description': coupon_type.description
                        })
            
            package_data = {
                'id': package.id,
                'name': package.name,
                'description': package.description,
                'price': float(package.price),
                'original_price': float(package.original_price),
                'validity_days': package.validity_days,
                'sale_count': package.sale_count,
                'coupon_details': coupon_details,
                'discount': round((1 - float(package.price) / float(package.original_price)) * 100, 1) if package.original_price > 0 else 0
            }
            package_list.append(package_data)
        
        return jsonify({
            'code': 0,
            'message': '获取优惠券包成功',
            'data': {
                'packages': package_list,
                'total': len(package_list)
            }
        })
    except Exception as e:
        print(f"获取优惠券包失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取优惠券包失败: {str(e)}'}), 500

# 购买优惠券包API
@app.route('/api/coupon/purchase', methods=['POST'])
def purchase_coupon_package():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据为空'}), 400
        
        package_id = data.get('package_id')
        payment_method = data.get('payment_method', '余额支付')
        
        if not package_id:
            return jsonify({'code': 400, 'message': '套餐ID不能为空'}), 400
        
        # 验证套餐是否存在且可购买
        package = CouponPackage.query.filter_by(id=package_id, status=1).first()
        if not package:
            return jsonify({'code': 404, 'message': '套餐不存在或已下架'}), 404
        
        # 检查用户余额（如果使用余额支付）
        if payment_method == '余额支付':
            if user.balance < package.price:
                return jsonify({'code': 400, 'message': f'余额不足，当前余额：{user.balance}元，需要：{package.price}元'}), 400
            
            # 扣除余额
            user.balance -= package.price
        
        # 生成优惠券
        validity_start = datetime.datetime.now()
        validity_end = validity_start + timedelta(days=package.validity_days)
        
        generated_coupons = []
        
        for type_id, count in package.coupon_details.items():
            for _ in range(count):
                new_coupon = Coupon(
                    user_id=user_id,
                    coupon_type_id=int(type_id),
                    source='套餐购买',
                    source_id=package_id,
                    validity_start=validity_start,
                    validity_end=validity_end,
                    status='未使用'
                )
                db.session.add(new_coupon)
                generated_coupons.append({
                    'coupon_type_id': int(type_id),
                    'validity_start': validity_start.strftime('%Y-%m-%d %H:%M:%S'),
                    'validity_end': validity_end.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # 更新套餐销量
        package.sale_count += 1
        
        # 在收入表中添加记录（平台收入）
        new_income = Income(
            amount=Decimal(str(package.price)),
            source='优惠券包',
            user_id=user_id,
            order_id=None,
            date=date.today(),
            description=f'用户{user.username}购买优惠券包：{package.name}，支付方式：{payment_method}'
        )
        db.session.add(new_income)
        
        # 保存到数据库
        db.session.commit()
        
        print(f"用户 {user.username} 购买优惠券包 {package.name}，支付方式：{payment_method}")
        
        return jsonify({
            'code': 0,
            'message': '购买成功',
            'data': {
                'package_name': package.name,
                'price': float(package.price),
                'payment_method': payment_method,
                'generated_coupons': generated_coupons,
                'validity_days': package.validity_days,
                'purchase_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"购买优惠券包失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'购买失败: {str(e)}'}), 500

# 获取用户优惠券API
@app.route('/api/user/coupons', methods=['GET'])
def get_user_coupons():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取查询参数
        status_filter = request.args.get('status')  # 可选的状态筛选
        
        # 构建查询
        query = db.session.query(
            Coupon.coupon_id,
            Coupon.user_id,
            Coupon.coupon_type_id,
            Coupon.source,
            Coupon.source_id,
            Coupon.receive_time,
            Coupon.validity_start,
            Coupon.validity_end,
            Coupon.use_time,
            Coupon.order_id,
            Coupon.status,
            CouponType.type_name,
            CouponType.coupon_category,
            CouponType.value,
            CouponType.min_amount,
            CouponType.description
        ).join(
            CouponType, Coupon.coupon_type_id == CouponType.id
        ).filter(
            Coupon.user_id == user_id
        )
        
        # 如果指定了状态筛选
        if status_filter:
            query = query.filter(Coupon.status == status_filter)
        
        # 按获得时间倒序排列
        coupons = query.order_by(Coupon.receive_time.desc()).all()
        
        # 格式化优惠券数据
        coupon_list = []
        for coupon in coupons:
            # 格式化日期
            validity_start_date = coupon.validity_start.strftime('%Y-%m-%d') if coupon.validity_start else None
            validity_end_date = coupon.validity_end.strftime('%Y-%m-%d') if coupon.validity_end else None
            receive_date = coupon.receive_time.strftime('%Y-%m-%d %H:%M:%S') if coupon.receive_time else None
            use_date = coupon.use_time.strftime('%Y-%m-%d %H:%M:%S') if coupon.use_time else None
            
            coupon_data = {
                'coupon_id': coupon.coupon_id,
                'coupon_type_id': coupon.coupon_type_id,
                'type_name': coupon.type_name,
                'coupon_category': coupon.coupon_category,
                'value': float(coupon.value),
                'min_amount': float(coupon.min_amount),
                'description': coupon.description,
                'source': coupon.source,
                'source_id': coupon.source_id,
                'receive_time': receive_date,
                'validity_start_date': validity_start_date,
                'validity_end_date': validity_end_date,
                'use_time': use_date,
                'order_id': coupon.order_id,
                'status': coupon.status
            }
            coupon_list.append(coupon_data)
        
        # 统计各状态的优惠券数量
        total_count = len(coupon_list)
        available_count = len([c for c in coupon_list if c['status'] == '未使用'])
        used_count = len([c for c in coupon_list if c['status'] == '已使用'])
        expired_count = len([c for c in coupon_list if c['status'] == '已过期'])
        
        print(f"用户 {user.username} 查询优惠券，总数：{total_count}，可用：{available_count}，已使用：{used_count}，已过期：{expired_count}")
        
        return jsonify({
            'code': 0,
            'message': '获取优惠券成功',
            'data': {
                'coupons': coupon_list,
                'statistics': {
                    'total': total_count,
                    'available': available_count,
                    'used': used_count,
                    'expired': expired_count
                }
            }
        })
    except Exception as e:
        print(f"获取用户优惠券失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取优惠券失败: {str(e)}'}), 500

# 获取用户钱包交易记录API
@app.route('/api/user/wallet/transactions', methods=['GET'])
def get_wallet_transactions():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        transaction_type = request.args.get('type', 'all')  # all/income/expense/stats
        
        # 如果是获取统计数据
        if transaction_type == 'stats':
            # 统计充值记录数（income表中"用户充值"类型且用户ID相同）
            income_count = db.session.query(db.func.count(Income.id)).filter_by(user_id=user_id, source='充值收入').scalar() or 0
            
            # 统计消费记录数（已结束订单 + 优惠券包 + 提现支出）
            # 车费消费：已结束订单数
            finished_orders_count = db.session.query(db.func.count(Order.order_id)).filter_by(user_id=user_id, order_status='已结束').scalar() or 0
            
            # 优惠券包消费
            coupon_expense_count = db.session.query(db.func.count(Income.id)).filter(
                Income.user_id == user_id,
                Income.source == '优惠券包'
            ).scalar() or 0
            
            # 提现支出
            withdraw_expense_count = db.session.query(db.func.count(Expense.id)).filter_by(
                user_id=user_id, type='提现支出'
            ).scalar() or 0
            
            expense_count = finished_orders_count + coupon_expense_count + withdraw_expense_count
            total_count = income_count + expense_count
            
            return jsonify({
                'code': 0,
                'message': '获取交易统计成功',
                'data': {
                    'stats': {
                        'income_count': income_count,
                        'expense_count': expense_count,
                        'total_count': total_count
                    }
                }
            })
        
        # 获取交易记录
        transactions = []
        
        # 获取充值记录（income表中"用户充值"类型且用户ID相同）
        if transaction_type in ['all', 'income']:
            income_records = Income.query.filter_by(user_id=user_id, source='充值收入').order_by(Income.created_at.desc()).all()
            for record in income_records:
                transactions.append({
                    'id': f'income_{record.id}',
                    'amount': float(record.amount),
                    'amount_type': 'income',
                    'type': '充值',
                    'date': record.date.strftime('%Y-%m-%d') if record.date else '',
                    'description': record.description,
                    'order_id': record.order_id,
                    'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else ''
                })
        
        # 获取消费记录
        if transaction_type in ['all', 'expense']:
            # 车费消费 - 从已结束订单中获取
            finished_orders = Order.query.filter_by(user_id=user_id, order_status='已结束').order_by(Order.create_time.desc()).all()
            
            for order in finished_orders:
                # 获取订单详情（金额和距离）
                order_detail_query = text("""
                    SELECT amount, distance, payment_method, created_at
                    FROM order_details 
                    WHERE order_id = :order_id
                """)
                order_detail = db.session.execute(order_detail_query, {'order_id': str(order.order_id)}).first()
                
                if order_detail:
                    # 查询该订单是否使用了优惠券 - 使用order_id而不是order_number
                    print(f"查询订单ID {order.order_id} 的优惠券使用情况")
                    used_coupon = Coupon.query.filter_by(order_id=str(order.order_id), status='已使用').first()
                    print(f"找到的优惠券: {used_coupon}")
                    
                    # 也尝试查询所有相关优惠券（调试用）
                    all_coupons_for_order = Coupon.query.filter_by(order_id=str(order.order_id)).all()
                    print(f"订单ID {order.order_id} 的所有相关优惠券: {len(all_coupons_for_order)}")
                    
                    original_price = float(order_detail.amount)
                    final_price = float(order_detail.amount)
                    coupon_info = "未使用优惠"
                    
                    if used_coupon:
                        print(f"订单ID {order.order_id} 使用了优惠券 {used_coupon.coupon_id}")
                        # 获取优惠券类型信息
                        from sqlalchemy import text as sql_text
                        coupon_type_query = sql_text("""
                            SELECT type_name, coupon_category, value, min_amount
                            FROM coupon_types 
                            WHERE id = :coupon_type_id
                        """)
                        coupon_type = db.session.execute(coupon_type_query, {'coupon_type_id': used_coupon.coupon_type_id}).first()
                        
                        if coupon_type:
                            if coupon_type.coupon_category == '折扣券':
                                # 折扣券：原价 = 实付金额 / 折扣率
                                original_price = final_price / float(coupon_type.value)
                                coupon_info = f"使用{coupon_type.type_name}(原价¥{original_price:.1f})"
                            elif coupon_type.coupon_category == '满减券':
                                # 满减券：原价 = 实付金额 + 减免金额
                                original_price = final_price + float(coupon_type.value)
                                coupon_info = f"使用{coupon_type.type_name}(原价¥{original_price:.1f})"
                    else:
                        print(f"订单ID {order.order_id} 未使用优惠券")
                    
                    # 构建用户友好的描述信息
                    user_description = f"车费支出 ¥{final_price:.1f} | {coupon_info}"
                    user_description += f" | 距离: {float(order_detail.distance)}km | 支付: {order_detail.payment_method}"
                    user_description += f" | 起点: ({order.pickup_location_x},{order.pickup_location_y}) | 终点: ({order.dropoff_location_x},{order.dropoff_location_y})"
                    
                    transactions.append({
                        'id': f'order_{order.order_id}',
                        'amount': final_price,
                        'amount_type': 'expense',
                        'type': '车费',
                        'date': order.create_time.strftime('%Y-%m-%d') if order.create_time else '',
                        'description': user_description,
                        'order_id': order.order_number,
                        'distance': float(order_detail.distance),
                        'payment_method': order_detail.payment_method,
                        'pickup_coords': f"({order.pickup_location_x},{order.pickup_location_y})",
                        'dropoff_coords': f"({order.dropoff_location_x},{order.dropoff_location_y})",
                        'original_price': original_price, # 原价
                        'final_price': final_price, # 实付价格
                        'coupon_info': coupon_info, # 优惠券信息
                        'created_at': order_detail.created_at.strftime('%Y-%m-%d %H:%M:%S') if order_detail.created_at else ''
                    })
            
            # 优惠券包（income表）
            coupon_income_records = Income.query.filter(
                Income.user_id == user_id,
                Income.source == '优惠券包'
            ).order_by(Income.created_at.desc()).all()
            
            for record in coupon_income_records:
                transactions.append({
                    'id': f'income_{record.id}',
                    'amount': float(record.amount),
                    'amount_type': 'expense',
                    'type': '优惠券包',
                    'date': record.date.strftime('%Y-%m-%d') if record.date else '',
                    'description': f"优惠券包购买 ¥{float(record.amount)}", # 简化描述
                    'order_id': None,
                    'distance': None,
                    'payment_method': None,
                    'pickup_coords': None,
                    'dropoff_coords': None,
                    'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else ''
                })
            
            # 提现支出（expense表）
            expense_records = Expense.query.filter_by(user_id=user_id, type='提现支出').order_by(Expense.created_at.desc()).all()
            for record in expense_records:
                transactions.append({
                    'id': f'expense_{record.id}',
                    'amount': float(record.amount),
                    'amount_type': 'expense',
                    'type': '提现',
                    'date': record.date.strftime('%Y-%m-%d') if record.date else '',
                    'description': f"提现 ¥{float(record.amount)}", # 简化描述
                    'order_id': None,
                    'distance': None,
                    'payment_method': None,
                    'pickup_coords': None,
                    'dropoff_coords': None,
                    'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else ''
                })
        
        # 按日期排序
        transactions.sort(key=lambda x: x['created_at'], reverse=True)
        
        # 分页处理
        total = len(transactions)
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_transactions = transactions[start_index:end_index]
        
        return jsonify({
            'code': 0,
            'message': '获取交易记录成功',
            'data': {
                'transactions': paginated_transactions,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page,
                    'has_next': end_index < total,
                    'has_prev': page > 1
                }
            }
        })
    except Exception as e:
        print(f"获取钱包交易记录失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取交易记录失败: {str(e)}'}), 500

# 充值API
@app.route('/api/user/wallet/recharge', methods=['POST'])
def recharge_wallet():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据为空'}), 400
        
        amount = data.get('amount')
        payment_method = data.get('payment_method', '微信支付')
        
        if not amount:
            return jsonify({'code': 400, 'message': '充值金额不能为空'}), 400
        
        try:
            amount = float(amount)
            if amount <= 0:
                return jsonify({'code': 400, 'message': '充值金额必须大于0'}), 400
            if amount > 10000:
                return jsonify({'code': 400, 'message': '单次充值金额不能超过10000元'}), 400
        except ValueError:
            return jsonify({'code': 400, 'message': '充值金额格式错误'}), 400
        
        # 更新用户余额 - 修复decimal类型转换问题
        amount_decimal = Decimal(str(amount))
        current_balance = user.balance or Decimal('0.00')
        user.balance = current_balance + amount_decimal
        
        # 在收入表中添加记录（平台收入）
        new_income = Income(
            amount=amount_decimal,
            source='充值收入',
            user_id=user_id,
            order_id=None,
            date=date.today(),
            description=f'用户{user.username}充值{amount}元，支付方式：{payment_method}'
        )
        
        # 保存到数据库
        db.session.add(new_income)
        db.session.commit()
        
        print(f"用户 {user.username} 充值成功：{amount}元，支付方式：{payment_method}")
        
        return jsonify({
            'code': 0,
            'message': '充值成功',
            'data': {
                'amount': amount,
                'payment_method': payment_method,
                'new_balance': float(user.balance),
                'income_id': new_income.id,
                'recharge_time': new_income.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"充值失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'充值失败: {str(e)}'}), 500

# 提现API
@app.route('/api/user/wallet/withdraw', methods=['POST'])
def withdraw_wallet():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据为空'}), 400
        
        amount = data.get('amount')
        withdraw_method = data.get('withdraw_method', '银行卡')
        
        if not amount:
            return jsonify({'code': 400, 'message': '提现金额不能为空'}), 400
        
        try:
            amount = float(amount)
            if amount <= 0:
                return jsonify({'code': 400, 'message': '提现金额必须大于0'}), 400
            if amount < 10:
                return jsonify({'code': 400, 'message': '单次提现金额不能少于10元'}), 400
            if amount > 5000:
                return jsonify({'code': 400, 'message': '单次提现金额不能超过5000元'}), 400
        except ValueError:
            return jsonify({'code': 400, 'message': '提现金额格式错误'}), 400
        
        # 检查余额是否充足 - 修复decimal类型转换问题
        amount_decimal = Decimal(str(amount))
        current_balance = user.balance or Decimal('0.00')
        if current_balance < amount_decimal:
            return jsonify({'code': 400, 'message': f'余额不足，当前余额：{current_balance}元'}), 400
        
        # 更新用户余额
        user.balance = current_balance - amount_decimal
        
        # 在支出表中添加记录
        new_expense = Expense(
            amount=amount_decimal,
            type='提现支出',
            vehicle_id=None,
            charging_station_id=None,
            user_id=user_id,
            date=date.today(),
            description=f'用户{user.username}提现{amount}元，提现方式：{withdraw_method}'
        )
        
        # 保存到数据库
        db.session.add(new_expense)
        db.session.commit()
        
        print(f"用户 {user.username} 提现成功：{amount}元，提现方式：{withdraw_method}")
        
        return jsonify({
            'code': 0,
            'message': '提现申请已提交，预计1-3个工作日到账',
            'data': {
                'amount': amount,
                'withdraw_method': withdraw_method,
                'new_balance': float(user.balance),
                'expense_id': new_expense.id,
                'withdraw_time': new_expense.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"提现失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'提现失败: {str(e)}'}), 500

# 获取信用等级列表API
@app.route('/api/credit/levels', methods=['GET'])
def get_credit_levels():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取所有信用等级
        levels = CreditLevelRule.query.order_by(CreditLevelRule.min_score.asc()).all()
        
        levels_data = []
        for level in levels:
            levels_data.append({
                'level_id': level.level_id,
                'level_name': level.level_name,
                'min_score': level.min_score,
                'max_score': level.max_score,
                'benefits': level.benefits or '',
                'limitations': level.limitations or '',
                'icon_url': level.icon_url or ''
            })
        
        return jsonify({
            'code': 0,
            'message': '获取信用等级成功',
            'data': levels_data
        })
    except Exception as e:
        print(f"获取信用等级失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取信用等级失败: {str(e)}'}), 500

# 获取信用规则列表API
@app.route('/api/credit/rules', methods=['GET'])
def get_credit_rules():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取所有激活的信用规则
        rules = CreditRule.query.filter_by(is_active=True).order_by(CreditRule.rule_type.asc(), CreditRule.score_change.desc()).all()
        
        rules_data = []
        for rule in rules:
            rules_data.append({
                'rule_id': rule.rule_id,
                'rule_name': rule.rule_name,
                'rule_type': rule.rule_type,
                'trigger_event': rule.trigger_event,
                'score_change': rule.score_change,
                'description': rule.description or '',
                'is_active': rule.is_active
            })
        
        return jsonify({
            'code': 0,
            'message': '获取信用规则成功',
            'data': rules_data
        })
    except Exception as e:
        print(f"获取信用规则失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取信用规则失败: {str(e)}'}), 500

# 获取用户信用变动记录API
@app.route('/api/credit/logs', methods=['GET'])
def get_credit_logs():
    try:
        # 从请求头中获取token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        # 解析token，获取用户ID
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 获取用户的信用变动记录
        logs_query = UserCreditLog.query.filter_by(user_id=user_id).order_by(UserCreditLog.created_at.desc())
        
        # 分页
        logs_pagination = logs_query.paginate(page=page, per_page=per_page, error_out=False)
        logs = logs_pagination.items
        
        logs_data = []
        for log in logs:
            logs_data.append({
                'log_id': log.log_id,
                'change_type': log.change_type,
                'reason': log.reason,
                'change_amount': log.change_amount,
                'credit_before': log.credit_before,
                'credit_after': log.credit_after,
                'operator': log.operator or '系统',
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else ''
            })
        
        return jsonify({
            'code': 0,
            'message': '获取信用记录成功',
            'data': logs_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': logs_pagination.total,
                'pages': logs_pagination.pages,
                'has_next': logs_pagination.has_next,
                'has_prev': logs_pagination.has_prev
            }
        })
    except Exception as e:
        print(f"获取信用记录失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取信用记录失败: {str(e)}'}), 500

# 智能客服API
@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    """智能客服对话接口"""
    try:
        # 验证用户身份
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据为空'}), 400
        
        content = data.get('content', '').strip()
        if not content:
            return jsonify({'code': 400, 'message': '消息内容不能为空'}), 400
        
        # 保存用户消息到数据库
        try:
            user_msg = ChatRecord(user_id=user_id, msg=content, is_user=True)
            db.session.add(user_msg); db.session.commit()
        except: db.session.rollback()
        
        # 调用Coze API
        result = coze_service.chat(str(user_id), content)
        
        # 保存客服回复到数据库
        try:
            bot_msg = ChatRecord(user_id=user_id, msg=result['content'], is_user=False)
            db.session.add(bot_msg); db.session.commit()
        except: db.session.rollback()
        
        if result.get('success'):
            return jsonify({
                'code': 0,
                'message': '对话成功',
                'data': {
                    'content': result['content'],
                    'conversation_id': result.get('conversation_id'),
                    'chat_id': result.get('chat_id')
                }
            })
        else:
            return jsonify({
                'code': 0,  # 仍返回成功，但使用降级回复
                'message': '对话成功',
                'data': {
                    'content': result['content']
                }
            })
            
    except Exception as e:
        print(f"智能客服对话失败: {str(e)}")
        # 降级回复内容
        fallback_msg = '抱歉，我暂时无法回答您的问题。您可以尝试：\n1. 重新描述问题\n2. 查看常见问题\n3. 联系人工客服'
        # 保存降级回复到数据库
        try:
            if 'user_id' in locals() and 'content' in locals():
                user_msg = ChatRecord(user_id=user_id, msg=content, is_user=True)
                bot_msg = ChatRecord(user_id=user_id, msg=fallback_msg, is_user=False)
                db.session.add(user_msg); db.session.add(bot_msg); db.session.commit()
        except: db.session.rollback()
        return jsonify({
            'code': 0,  # 降级处理，返回默认回复
            'message': '对话成功',
            'data': {
                'content': fallback_msg
            }
        })

# 获取用户通知列表API
@app.route('/api/user/notifications', methods=['GET'])
def get_user_notifications():
    """获取用户通知列表"""
    try:
        # 验证用户身份
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取查询参数
        is_read = request.args.get('is_read', type=int)  # 0=未读, 1=已读
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 构建查询条件
        query = UserNotification.query.filter(
            db.or_(
                UserNotification.target_type == 0,  # 系统通知
                db.and_(
                    UserNotification.target_type == 1,  # 个人通知
                    UserNotification.userid == user_id
                )
            ),
            UserNotification.is_deleted == False
        )
        
        # 根据is_read参数过滤
        if is_read is not None:
            if is_read == 0:
                query = query.filter(UserNotification.is_read == False)
            else:
                query = query.filter(UserNotification.is_read == True)
        
        # 按创建时间倒序排列
        query = query.order_by(UserNotification.create_time.desc())
        
        # 分页
        notifications_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        notifications = notifications_pagination.items
        
        # 构建返回数据
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'notification_id': notification.notification_id,
                'title': notification.title,
                'content': notification.content,
                'target_type': notification.target_type,
                'userid': notification.userid,
                'is_read': notification.is_read,
                'is_deleted': notification.is_deleted,
                'read_time': notification.read_time.strftime('%Y-%m-%d %H:%M:%S') if notification.read_time else None,
                'create_time': notification.create_time.strftime('%Y-%m-%d %H:%M:%S') if notification.create_time else None
            })
        
        return jsonify({
            'code': 0,
            'message': '获取通知列表成功',
            'data': notifications_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': notifications_pagination.total,
                'pages': notifications_pagination.pages,
                'has_next': notifications_pagination.has_next,
                'has_prev': notifications_pagination.has_prev
            }
        })
        
    except Exception as e:
        print(f"获取用户通知列表失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取通知列表失败: {str(e)}'}), 500

# 标记通知为已读API
@app.route('/api/user/notifications/<int:notification_id>/read', methods=['PUT'])
def mark_notification_as_read(notification_id):
    """标记通知为已读"""
    try:
        # 验证用户身份
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 查找通知
        notification = UserNotification.query.get(notification_id)
        if not notification:
            return jsonify({'code': 404, 'message': '通知不存在'}), 404
        
        # 检查权限：只能标记自己的通知或系统通知
        if notification.target_type == 1 and notification.userid != user_id:
            return jsonify({'code': 403, 'message': '无权限操作此通知'}), 403
        
        # 标记为已读
        notification.is_read = True
        notification.read_time = db.func.current_timestamp()
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': '标记为已读成功'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"标记通知为已读失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'标记为已读失败: {str(e)}'}), 500

# 标记所有通知为已读API
@app.route('/api/user/notifications/read-all', methods=['PUT'])
def mark_all_notifications_as_read():
    """标记所有通知为已读"""
    try:
        # 验证用户身份
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 标记所有未读通知为已读
        notifications = UserNotification.query.filter(
            db.or_(
                UserNotification.target_type == 0,  # 系统通知
                db.and_(
                    UserNotification.target_type == 1,  # 个人通知
                    UserNotification.userid == user_id
                )
            ),
            UserNotification.is_read == False,
            UserNotification.is_deleted == False
        ).all()
        
        count = 0
        for notification in notifications:
            notification.is_read = True
            notification.read_time = db.func.current_timestamp()
            count += 1
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'message': f'成功标记{count}条通知为已读'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"标记所有通知为已读失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'标记所有通知为已读失败: {str(e)}'}), 500

# 获取用户统计数据API
@app.route('/api/user/statistics', methods=['GET'])
def get_user_statistics():
    """获取用户统计数据概览"""
    try:
        # 验证用户身份
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取订单统计
        total_orders = db.session.query(Order).filter_by(user_id=user_id).count()
        
        # 获取订单详情表数据进行统计
        order_details_query = db.session.execute(text("""
            SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(amount), 0) as total_spent,
                COALESCE(SUM(distance), 0) as total_distance,
                COALESCE(AVG(amount), 0) as avg_amount
            FROM order_details 
            WHERE user_id = :user_id
        """), {'user_id': user_id}).fetchone()
        
        # 获取本月统计
        current_month = datetime.datetime.now().strftime('%Y-%m')
        monthly_stats = db.session.execute(text("""
            SELECT 
                COUNT(*) as monthly_orders,
                COALESCE(SUM(od.amount), 0) as monthly_spent
            FROM order_details od
            JOIN orders o ON od.order_id = o.order_id
            WHERE od.user_id = :user_id 
            AND DATE_FORMAT(o.create_time, '%Y-%m') = :current_month
        """), {'user_id': user_id, 'current_month': current_month}).fetchone()
        
        # 获取评分统计
        avg_rating = db.session.execute(text("""
            SELECT COALESCE(AVG(rating), 5.0) as avg_rating
            FROM evaluations 
            WHERE user_id = :user_id
        """), {'user_id': user_id}).fetchone()
        
        # 获取常用城市
        favorite_city = db.session.execute(text("""
            SELECT city_code, COUNT(*) as count
            FROM orders 
            WHERE user_id = :user_id AND city_code IS NOT NULL
            GROUP BY city_code 
            ORDER BY count DESC 
            LIMIT 1
        """), {'user_id': user_id}).fetchone()
        
        # 获取订单状态统计
        status_stats = db.session.execute(text("""
            SELECT 
                order_status as status,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM orders WHERE user_id = :user_id), 1) as percentage
            FROM orders 
            WHERE user_id = :user_id
            GROUP BY order_status
        """), {'user_id': user_id}).fetchall()
        
        # 构建返回数据
        statistics_data = {
            'totalOrders': order_details_query.total_orders if order_details_query else 0,
            'totalSpent': f"{float(order_details_query.total_spent):.2f}" if order_details_query and order_details_query.total_spent else "0.00",
            'totalDistance': f"{float(order_details_query.total_distance):.1f}" if order_details_query and order_details_query.total_distance else "0.0",
            'avgRating': f"{float(avg_rating.avg_rating):.1f}" if avg_rating else "5.0",
            'monthlyOrders': monthly_stats.monthly_orders if monthly_stats else 0,
            'monthlySpent': f"{float(monthly_stats.monthly_spent):.2f}" if monthly_stats and monthly_stats.monthly_spent else "0.00",
            'favoriteCity': favorite_city.city_code if favorite_city else "暂无",
            'orderStatusStats': [
                {
                    'status': row.status,
                    'count': row.count,
                    'percentage': f"{float(row.percentage):.1f}"
                } for row in status_stats
            ]
        }
        
        return jsonify({
            'code': 0,
            'message': '获取统计数据成功',
            'data': statistics_data
        })
        
    except Exception as e:
        print(f"获取用户统计数据失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取统计数据失败: {str(e)}'}), 500

# 获取用户订单趋势数据API
@app.route('/api/user/statistics/order-trend', methods=['GET'])
def get_user_order_trend():
    """获取用户订单趋势数据"""
    try:
        # 验证用户身份
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取查询参数
        period = request.args.get('period', 'month')  # month/week/day
        limit = int(request.args.get('limit', 30))
        
        # 根据period构建不同的查询
        if period == 'month':
            trend_data = db.session.execute(text("""
                SELECT 
                    DATE_FORMAT(create_time, '%Y-%m-%d') as date,
                    COUNT(*) as count
                FROM orders 
                WHERE user_id = :user_id 
                AND create_time >= DATE_SUB(NOW(), INTERVAL :limit DAY)
                GROUP BY DATE_FORMAT(create_time, '%Y-%m-%d')
                ORDER BY date ASC
            """), {'user_id': user_id, 'limit': limit}).fetchall()
        elif period == 'week':
            trend_data = db.session.execute(text("""
                SELECT 
                    DATE_FORMAT(create_time, '%Y-%u') as date,
                    COUNT(*) as count
                FROM orders 
                WHERE user_id = :user_id 
                AND create_time >= DATE_SUB(NOW(), INTERVAL :limit WEEK)
                GROUP BY DATE_FORMAT(create_time, '%Y-%u')
                ORDER BY date ASC
            """), {'user_id': user_id, 'limit': limit}).fetchall()
        else:  # day
            trend_data = db.session.execute(text("""
                SELECT 
                    DATE_FORMAT(create_time, '%H:00') as date,
                    COUNT(*) as count
                FROM orders 
                WHERE user_id = :user_id 
                AND DATE(create_time) = CURDATE()
                GROUP BY HOUR(create_time)
                ORDER BY HOUR(create_time) ASC
            """), {'user_id': user_id}).fetchall()
        
        # 构建返回数据
        trend_result = {
            'trendData': [
                {
                    'date': row.date,
                    'count': row.count
                } for row in trend_data
            ]
        }
        
        return jsonify({
            'code': 0,
            'message': '获取订单趋势数据成功',
            'data': trend_result
        })
        
    except Exception as e:
        print(f"获取订单趋势数据失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取订单趋势数据失败: {str(e)}'}), 500

# 获取用户消费分析数据API
@app.route('/api/user/statistics/spending-analysis', methods=['GET'])
def get_user_spending_analysis():
    """获取用户消费分析数据"""
    try:
        # 验证用户身份
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取查询参数
        period = request.args.get('period', 'month')
        
        # 获取消费统计
        spending_stats = db.session.execute(text("""
            SELECT 
                COALESCE(AVG(amount), 0) as avg_amount,
                COALESCE(MAX(amount), 0) as max_amount,
                COALESCE(MIN(amount), 0) as min_amount
            FROM order_details 
            WHERE user_id = :user_id
        """), {'user_id': user_id}).fetchone()
        
        # 获取消费趋势数据
        if period == 'month':
            trend_data = db.session.execute(text("""
                SELECT 
                    DATE_FORMAT(od.created_at, '%Y-%m-%d') as date,
                    COALESCE(SUM(od.amount), 0) as amount
                FROM order_details od
                WHERE od.user_id = :user_id 
                AND od.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY DATE_FORMAT(od.created_at, '%Y-%m-%d')
                ORDER BY date ASC
            """), {'user_id': user_id}).fetchall()
        else:
            trend_data = db.session.execute(text("""
                SELECT 
                    DATE_FORMAT(od.created_at, '%Y-%m') as date,
                    COALESCE(SUM(od.amount), 0) as amount
                FROM order_details od
                WHERE od.user_id = :user_id 
                AND od.created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
                GROUP BY DATE_FORMAT(od.created_at, '%Y-%m')
                ORDER BY date ASC
            """), {'user_id': user_id}).fetchall()
        
        # 获取支付方式分布
        payment_methods = db.session.execute(text("""
            SELECT 
                payment_method as method,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM order_details WHERE user_id = :user_id), 1) as percentage
            FROM order_details 
            WHERE user_id = :user_id
            GROUP BY payment_method
            ORDER BY count DESC
        """), {'user_id': user_id}).fetchall()
        
        # 构建返回数据
        spending_result = {
            'avgOrderAmount': f"{float(spending_stats.avg_amount):.2f}" if spending_stats else "0.00",
            'maxOrderAmount': f"{float(spending_stats.max_amount):.2f}" if spending_stats else "0.00",
            'minOrderAmount': f"{float(spending_stats.min_amount):.2f}" if spending_stats else "0.00",
            'trendData': [
                {
                    'date': row.date,
                    'amount': float(row.amount)
                } for row in trend_data
            ],
            'paymentMethods': [
                {
                    'method': row.method,
                    'count': row.count,
                    'percentage': f"{float(row.percentage):.1f}"
                } for row in payment_methods
            ]
        }
        
        return jsonify({
            'code': 0,
            'message': '获取消费分析数据成功',
            'data': spending_result
        })
        
    except Exception as e:
        print(f"获取消费分析数据失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取消费分析数据失败: {str(e)}'}), 500

# 获取用户出行习惯分析API
@app.route('/api/user/statistics/travel-habits', methods=['GET'])
def get_user_travel_habits():
    """获取用户出行习惯分析数据"""
    try:
        # 验证用户身份
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取查询参数
        status = request.args.get('status', None)
        
        # 构建基本SQL查询条件
        base_condition = "user_id = :user_id AND create_time IS NOT NULL"
        if status:
            base_condition += " AND order_status = :status"
        
        query_params = {'user_id': user_id}
        if status:
            query_params['status'] = status
        
        # 获取出行时间分布
        time_distribution = db.session.execute(text(f"""
            SELECT 
                HOUR(create_time) as hour,
                COUNT(*) as count
            FROM orders 
            WHERE {base_condition}
            GROUP BY HOUR(create_time)
            ORDER BY hour ASC
        """), query_params).fetchall()
        
        # 获取最常出行时间
        peak_hour = db.session.execute(text(f"""
            SELECT 
                HOUR(create_time) as hour,
                COUNT(*) as count
            FROM orders 
            WHERE {base_condition}
            GROUP BY HOUR(create_time)
            ORDER BY count DESC
            LIMIT 1
        """), query_params).fetchone()
        
        # 获取平均出行距离
        avg_distance_query = "user_id = :user_id"
        if status:
            avg_distance_query += " AND order_id IN (SELECT order_id FROM orders WHERE user_id = :user_id AND order_status = :status)"
        
        avg_distance = db.session.execute(text(f"""
            SELECT COALESCE(AVG(distance), 0) as avg_distance
            FROM order_details 
            WHERE {avg_distance_query}
        """), query_params).fetchone()
        
        # 获取城市分布
        city_distribution_count_query = f"COUNT(*) FROM orders WHERE user_id = :user_id AND city_code IS NOT NULL"
        if status:
            city_distribution_count_query += " AND order_status = :status"
            
        city_distribution = db.session.execute(text(f"""
            SELECT 
                city_code as city,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT {city_distribution_count_query}), 1) as percentage
            FROM orders 
            WHERE {base_condition} AND city_code IS NOT NULL
            GROUP BY city_code
            ORDER BY count DESC
        """), query_params).fetchall()
        
        # 获取最常用城市
        favorite_city = city_distribution[0].city if city_distribution else None
        
        # 构建返回数据
        habits_result = {
            'peakHour': f"{peak_hour.hour}:00-{peak_hour.hour+1}:00" if peak_hour else "暂无数据",
            'avgDistance': f"{float(avg_distance.avg_distance):.1f}" if avg_distance else "0.0",
            'favoriteCity': favorite_city if favorite_city else "暂无",
            'timeDistribution': [
                {
                    'hour': row.hour,
                    'count': row.count
                } for row in time_distribution
            ],
            'cityDistribution': [
                {
                    'city': row.city,
                    'count': row.count,
                    'percentage': f"{float(row.percentage):.1f}"
                } for row in city_distribution
            ]
        }
        
        return jsonify({
            'code': 0,
            'message': '获取出行习惯分析数据成功',
            'data': habits_result
        })
        
    except Exception as e:
        print(f"获取出行习惯分析数据失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取出行习惯分析数据失败: {str(e)}'}), 500

# 获取车辆实时位置API
@app.route('/api/vehicle/location/<int:vehicle_id>', methods=['GET'])
def get_vehicle_location(vehicle_id):
    """获取指定车辆的实时位置"""
    try:
        # 验证用户身份
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 查询车辆信息
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            return jsonify({'code': 404, 'message': '车辆不存在'}), 404
        
        # 检查用户是否有权限查看该车辆位置（必须是进行中的订单）
        active_order = Order.query.filter_by(
            user_id=user_id,
            vehicle_id=vehicle_id,
            order_status='进行中'
        ).first()
        
        if not active_order:
            return jsonify({'code': 403, 'message': '您没有权限查看该车辆位置'}), 403
        
        # 获取车辆当前位置坐标
        if vehicle.current_location_x is None or vehicle.current_location_y is None:
            return jsonify({'code': 404, 'message': '车辆位置信息不可用'}), 404
        
        # 将系统坐标转换为经纬度
        try:
            geo_coords = system_to_geo_coordinates(
                vehicle.current_location_x,
                vehicle.current_location_y,
                vehicle.current_city or active_order.city_code
            )
        except Exception as e:
            return jsonify({'code': 500, 'message': f'坐标转换失败: {str(e)}'}), 500
        
        # 构建返回数据
        location_data = {
            'vehicleId': vehicle.vehicle_id,
            'plateNumber': vehicle.plate_number,
            'currentStatus': vehicle.current_status,
            'batteryLevel': vehicle.battery_level,
            'location': {
                'longitude': geo_coords['longitude'],
                'latitude': geo_coords['latitude'],
                'systemX': vehicle.current_location_x,
                'systemY': vehicle.current_location_y,
                'locationName': vehicle.current_location_name,
                'city': vehicle.current_city
            },
            'orderInfo': {
                'orderId': active_order.order_id,
                'orderNumber': active_order.order_number,
                'orderStatus': active_order.order_status,
                'pickupLocation': active_order.pickup_location,
                'pickupLocationX': active_order.pickup_location_x,  # 系统坐标X
                'pickupLocationY': active_order.pickup_location_y,  # 系统坐标Y
                'dropoffLocation': active_order.dropoff_location,
                'dropoffLocationX': active_order.dropoff_location_x,  # 系统坐标X
                'dropoffLocationY': active_order.dropoff_location_y,  # 系统坐标Y
                'cityCode': active_order.city_code
            },
            'lastUpdate': vehicle.updated_at.strftime('%Y-%m-%d %H:%M:%S') if vehicle.updated_at else None
        }
        
        return jsonify({
            'code': 0,
            'message': '获取车辆位置成功',
            'data': location_data
        })
        
    except Exception as e:
        print(f"获取车辆位置失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取车辆位置失败: {str(e)}'}), 500

# 获取用户进行中订单的车辆位置API
@app.route('/api/user/active-order/vehicle-location', methods=['GET'])
def get_active_order_vehicle_location():
    """获取用户当前进行中订单的车辆位置"""
    try:
        # 验证用户身份
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 查询用户进行中的订单
        active_order = Order.query.filter_by(
            user_id=user_id,
            order_status='进行中'
        ).first()
        
        if not active_order:
            return jsonify({'code': 404, 'message': '您当前没有进行中的订单'}), 404
        
        if not active_order.vehicle_id:
            return jsonify({'code': 404, 'message': '订单尚未分配车辆'}), 404
        
        # 查询车辆信息
        vehicle = Vehicle.query.get(active_order.vehicle_id)
        if not vehicle:
            return jsonify({'code': 404, 'message': '车辆信息不存在'}), 404
        
        # 获取车辆当前位置坐标
        if vehicle.current_location_x is None or vehicle.current_location_y is None:
            return jsonify({'code': 404, 'message': '车辆位置信息不可用'}), 404
        
        # 将系统坐标转换为经纬度
        try:
            geo_coords = system_to_geo_coordinates(
                vehicle.current_location_x,
                vehicle.current_location_y,
                vehicle.current_city or active_order.city_code
            )
        except Exception as e:
            return jsonify({'code': 500, 'message': f'坐标转换失败: {str(e)}'}), 500
        
        # 构建返回数据
        location_data = {
            'vehicleId': vehicle.vehicle_id,
            'plateNumber': vehicle.plate_number,
            'model': vehicle.model,
            'currentStatus': vehicle.current_status,
            'batteryLevel': vehicle.battery_level,
            'rating': float(vehicle.rating) if vehicle.rating else 5.0,
            'location': {
                'longitude': geo_coords['longitude'],
                'latitude': geo_coords['latitude'],
                'systemX': vehicle.current_location_x,
                'systemY': vehicle.current_location_y,
                'locationName': vehicle.current_location_name,
                'city': vehicle.current_city
            },
            'orderInfo': {
                'orderId': active_order.order_id,
                'orderNumber': active_order.order_number,
                'orderStatus': active_order.order_status,
                'createTime': active_order.create_time.strftime('%Y-%m-%d %H:%M:%S') if active_order.create_time else None,
                'arrivalTime': active_order.arrival_time.strftime('%Y-%m-%d %H:%M:%S') if active_order.arrival_time else None,
                'pickupLocation': active_order.pickup_location,
                'pickupLocationX': active_order.pickup_location_x,  # 系统坐标X
                'pickupLocationY': active_order.pickup_location_y,  # 系统坐标Y
                'dropoffLocation': active_order.dropoff_location,
                'dropoffLocationX': active_order.dropoff_location_x,  # 系统坐标X
                'dropoffLocationY': active_order.dropoff_location_y,  # 系统坐标Y
                'cityCode': active_order.city_code
            },
            'lastUpdate': vehicle.updated_at.strftime('%Y-%m-%d %H:%M:%S') if vehicle.updated_at else None
        }
        
        return jsonify({
            'code': 0,
            'message': '获取车辆位置成功',
            'data': location_data
        })
        
    except Exception as e:
        print(f"获取进行中订单车辆位置失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取车辆位置失败: {str(e)}'}), 500

# 初始化应用上下文
try:
    with app.app_context():
        # 在应用启动时加载城市参数
        load_city_parameters()
        print("应用初始化完成，城市参数已加载")
except Exception as e:
    print(f"警告：应用启动时加载城市参数失败: {e}")
    print("将在API调用时重试加载参数")

# 获取城市中心点坐标API
@app.route('/api/system/city-centers', methods=['GET'])
def get_city_centers():
    """获取城市中心点坐标配置"""
    try:
        # 从数据库获取城市中心点参数
        centers_param = SystemParameter.query.filter_by(param_key='city_centers').first()
        if not centers_param:
            return jsonify({'code': 404, 'message': '城市中心点配置不存在'}), 404
        
        # 解析JSON数据
        try:
            city_centers = json.loads(centers_param.param_value)
        except json.JSONDecodeError as e:
            return jsonify({'code': 500, 'message': f'城市中心点配置解析失败: {str(e)}'}), 500
        
        return jsonify({
            'code': 0,
            'message': '获取城市中心点配置成功',
            'data': city_centers
        })
        
    except Exception as e:
        print(f"获取城市中心点配置失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取城市中心点配置失败: {str(e)}'}), 500

# 获取城市缩放因子API
@app.route('/api/system/city-scale-factors', methods=['GET'])
def get_city_scale_factors():
    """获取城市缩放因子配置"""
    try:
        # 从数据库获取城市缩放因子参数
        scale_param = SystemParameter.query.filter_by(param_key='city_scale_factors').first()
        if not scale_param:
            return jsonify({'code': 404, 'message': '城市缩放因子配置不存在'}), 404
        
        # 解析JSON数据
        try:
            city_scale_factors = json.loads(scale_param.param_value)
        except json.JSONDecodeError as e:
            return jsonify({'code': 500, 'message': f'城市缩放因子配置解析失败: {str(e)}'}), 500
        
        return jsonify({
            'code': 0,
            'message': '获取城市缩放因子配置成功',
            'data': city_scale_factors
        })
        
    except Exception as e:
        print(f"获取城市缩放因子配置失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取城市缩放因子配置失败: {str(e)}'}), 500

# 更新车辆评分函数
def update_vehicle_rating(vehicle_id):
    """更新车辆评分"""
    try:
        # 获取该车辆的所有评价
        evaluations = db.session.execute(text("""
            SELECT AVG(e.rating) as avg_rating
            FROM evaluations e
            JOIN orders o ON e.order_id = o.order_id
            WHERE o.vehicle_id = :vehicle_id
        """), {'vehicle_id': vehicle_id}).fetchone()
        
        if evaluations and evaluations.avg_rating:
            # 更新车辆评分
            db.session.execute(text("""
                UPDATE vehicles 
                SET rating = :rating 
                WHERE vehicle_id = :vehicle_id
            """), {
                'rating': round(float(evaluations.avg_rating), 1),
                'vehicle_id': vehicle_id
            })
            db.session.commit()
            print(f"车辆 {vehicle_id} 评分已更新为 {round(float(evaluations.avg_rating), 1)}")
        else:
            print(f"车辆 {vehicle_id} 暂无评价数据")
            
    except Exception as e:
        print(f"更新车辆评分失败: {str(e)}")
        db.session.rollback()

def get_city_order_price_factor(city_code):
    """获取城市订单价格系数"""
    try:
        # 获取城市价格系数配置
        city_factors_param = SystemParameter.query.filter_by(param_key='CITY_PRICE_FACTORS').first()
        
        if not city_factors_param:
            # 如果没有配置，创建默认配置并保存到数据库
            default_factors = {
                '沈阳市': {'orderPrice': 1.0},
                '上海市': {'orderPrice': 1.2},
                '北京市': {'orderPrice': 1.1},
                '广州市': {'orderPrice': 1.15},
                '深圳市': {'orderPrice': 1.25},
                '杭州市': {'orderPrice': 1.1},
                '南京市': {'orderPrice': 1.05},
                '成都市': {'orderPrice': 1.0},
                '重庆市': {'orderPrice': 0.95},
                '武汉市': {'orderPrice': 1.0},
                '西安市': {'orderPrice': 0.9}
            }
            
            new_param = SystemParameter(
                param_key='CITY_PRICE_FACTORS',
                param_value=json.dumps(default_factors, ensure_ascii=False),
                param_type='json'
            )
            db.session.add(new_param)
            db.session.commit()
        
            return default_factors.get(city_code, {}).get('orderPrice', 1.0)
        else:
            city_factors = json.loads(city_factors_param.param_value)
            return city_factors.get(city_code, {}).get('orderPrice', 1.0)
        
    except Exception as e:
        print(f"获取城市价格系数失败: {str(e)}")
        return 1.0  # 返回默认系数

# 获取车辆价格系数范围API
@app.route('/api/vehicle/price-coefficient-range', methods=['GET'])
def get_vehicle_price_coefficient_range():
    """获取车辆价格系数的最小值和最大值，用于计算订单价格区间"""
    try:
        # 查询所有车型的订单价格系数
        vehicle_price_params = SystemParameter.query.filter(
            SystemParameter.param_key.like('%_ORDER_PRICE')
        ).all()
        
        if not vehicle_price_params:
            # 如果没有配置，返回默认值
            return jsonify({
                'code': 0,
                'message': '获取成功',
                'data': {
                    'min_coefficient': 1.0,
                    'max_coefficient': 1.0,
                    'vehicle_models': {}
                }
            })
        
        # 提取所有价格系数
        coefficients = []
        vehicle_models = {}
        
        for param in vehicle_price_params:
            try:
                coefficient = float(param.param_value)
                coefficients.append(coefficient)
                
                # 提取车型名称（移除_ORDER_PRICE后缀）
                model_name = param.param_key.replace('_ORDER_PRICE', '')
                vehicle_models[model_name] = coefficient
            except ValueError:
                continue
        
        if not coefficients:
            # 如果没有有效的系数，返回默认值
            return jsonify({
                'code': 0,
                'message': '获取成功',
                'data': {
                    'min_coefficient': 1.0,
                    'max_coefficient': 1.0,
                    'vehicle_models': {}
                }
            })
        
        min_coefficient = min(coefficients)
        max_coefficient = max(coefficients)
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'min_coefficient': min_coefficient,
                'max_coefficient': max_coefficient,
                'vehicle_models': vehicle_models
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': f'获取车辆价格系数范围失败: {str(e)}'
        }), 500

# 获取订单价格预估API
@app.route('/api/order/price-estimate', methods=['POST'])
def get_order_price_estimate():
    """获取订单价格预估，返回价格区间"""
    try:
        data = request.get_json()
        pickup_location = data.get('pickup_location')
        dropoff_location = data.get('dropoff_location')
        city_code = data.get('city_code')
        
        if not pickup_location or not dropoff_location or not city_code:
            return jsonify({'code': 1, 'message': '缺少必要参数'}), 400
        
        # 获取经纬度数据
        pickup_lng = pickup_location.get('longitude')
        pickup_lat = pickup_location.get('latitude')
        dropoff_lng = dropoff_location.get('longitude')
        dropoff_lat = dropoff_location.get('latitude')
        
        if pickup_lng is None or pickup_lat is None or dropoff_lng is None or dropoff_lat is None:
            return jsonify({'code': 1, 'message': '经纬度数据不完整'}), 400
        
        # 将经纬度转换为系统内部坐标
        try:
            pickup_coords = geo_to_system_coordinates(pickup_lng, pickup_lat, city_code)
            dropoff_coords = geo_to_system_coordinates(dropoff_lng, dropoff_lat, city_code)
        except ValueError as e:
            return jsonify({'code': 1, 'message': str(e)}), 400
        
        # 计算系统坐标距离（欧氏距离）
        dx = dropoff_coords['x'] - pickup_coords['x']
        dy = dropoff_coords['y'] - pickup_coords['y']
        distance_in_units = ((dx ** 2 + dy ** 2) ** 0.5)  # 系统距离单位
        
        # 从系统参数表获取城市距离转换比例
        city_distance_param = SystemParameter.query.filter_by(param_key=city_code).first()
        if city_distance_param:
            city_ratio = float(city_distance_param.param_value)
        else:
            # 如果找不到对应城市的比例，使用默认值
            city_ratio = 0.1
            print(f"未找到城市 {city_code} 的距离转换比例，使用默认值 0.1")
        
        # 计算实际公里数
        distance = distance_in_units * city_ratio
        distance = round(distance, 2)  # 保留两位小数
        
        # 获取订单价格参数
        base_price_param = SystemParameter.query.filter_by(param_key='ORDER_BASE_PRICE').first()
        price_per_km_param = SystemParameter.query.filter_by(param_key='ORDER_PRICE_PER_KM').first()
        base_km_param = SystemParameter.query.filter_by(param_key='ORDER_BASE_KM').first()
        
        ORDER_BASE_PRICE = float(base_price_param.param_value) if base_price_param else 10.0
        ORDER_PRICE_PER_KM = float(price_per_km_param.param_value) if price_per_km_param else 2.5
        ORDER_BASE_KM = float(base_km_param.param_value) if base_km_param else 3.5
        
        # 获取城市价格系数
        city_price_factors_param = SystemParameter.query.filter_by(param_key='CITY_PRICE_FACTORS').first()
        if city_price_factors_param:
            city_price_factors = json.loads(city_price_factors_param.param_value)
            city_factor_data = city_price_factors.get(city_code, {})
            city_price_factor = city_factor_data.get('orderPrice', 1.0)
        else:
            city_price_factor = 1.0
        
        # 计算包含城市系数的价格参数（不显式告诉用户城市系数）
        adjusted_base_price = ORDER_BASE_PRICE * city_price_factor
        adjusted_price_per_km = ORDER_PRICE_PER_KM * city_price_factor
        
        # 计算基础金额（不含车辆系数）
        if distance <= ORDER_BASE_KM:
            base_amount = ORDER_BASE_PRICE
        else:
            base_amount = ORDER_BASE_PRICE + ((distance - ORDER_BASE_KM) * ORDER_PRICE_PER_KM)
        
        # 应用城市价格系数
        base_amount_with_city = base_amount * city_price_factor
        
        # 获取车辆价格系数范围
        vehicle_coefficients_response = get_vehicle_price_coefficient_range()
        vehicle_data = json.loads(vehicle_coefficients_response.data)['data']
        min_vehicle_coefficient = vehicle_data['min_coefficient']
        max_vehicle_coefficient = vehicle_data['max_coefficient']
        
        # 计算价格区间
        min_price = base_amount_with_city * min_vehicle_coefficient
        max_price = base_amount_with_city * max_vehicle_coefficient
        
        # 格式化价格区间字符串
        if abs(min_price - max_price) < 0.1:  # 价格差异很小时显示单一价格
            price_range = f"¥{min_price:.1f}"
        else:
            price_range = f"¥{min_price:.1f} - ¥{max_price:.1f}"
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'distance': distance,
                'base_amount': round(base_amount, 2),
                'city_price_factor': city_price_factor,
                'min_vehicle_coefficient': min_vehicle_coefficient,
                'max_vehicle_coefficient': max_vehicle_coefficient,
                'min_price': round(min_price, 2),
                'max_price': round(max_price, 2),
                'price_range': price_range,
                'pickup_coords': pickup_coords,
                'dropoff_coords': dropoff_coords,
                # 新增：包含城市系数的价格参数（不显式告诉用户城市系数）
                'base_distance': ORDER_BASE_KM,  # 起步距离
                'adjusted_base_price': round(adjusted_base_price, 2),  # 包含城市系数的起步价
                'adjusted_price_per_km': round(adjusted_price_per_km, 2)  # 包含城市系数的每公里价格
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': f'获取订单价格预估失败: {str(e)}'
        }), 500

# 获取用户对话历史记录API
@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    """获取用户对话历史记录"""
    try:
        # 验证用户身份
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'code': 401, 'message': '未登录或token无效'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = None
        if token.startswith('token_'):
            try:
                user_id = int(token.split('_')[1])
            except:
                return jsonify({'code': 401, 'message': 'token格式错误'}), 401
        
        # 检查用户是否存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在'}), 404
        
        # 获取查询参数
        date_filter = request.args.get('date')  # YYYY-MM-DD格式
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        # 构建查询
        query = ChatRecord.query.filter_by(user_id=user_id)
        
        # 如果指定了日期筛选
        if date_filter:
            try:
                # 验证日期格式
                from datetime import datetime
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                
                # 筛选指定日期的记录
                query = query.filter(
                    db.func.date(ChatRecord.created_at) == filter_date
                )
            except ValueError:
                return jsonify({'code': 400, 'message': '日期格式错误，请使用YYYY-MM-DD格式'}), 400
        
        # 按时间升序排列（对话顺序）
        query = query.order_by(ChatRecord.created_at.asc())
        
        # 分页查询
        records_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        records = records_pagination.items
        
        # 构建对话记录列表
        chat_history = []
        for record in records:
            chat_history.append({
                'id': record.id,
                'message': record.msg,
                'is_user': record.is_user,
                'role': 'user' if record.is_user else 'assistant',
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else '',
                'date': record.created_at.strftime('%Y-%m-%d') if record.created_at else '',
                'time': record.created_at.strftime('%H:%M:%S') if record.created_at else ''
            })
        
        # 获取可用日期列表（用户有对话记录的日期）
        available_dates_query = text("""
            SELECT DISTINCT DATE(created_at) as chat_date
            FROM chat_records 
            WHERE user_id = :user_id AND created_at IS NOT NULL
            ORDER BY chat_date DESC
        """)
        available_dates_result = db.session.execute(available_dates_query, {'user_id': user_id}).fetchall()
        available_dates = [str(row.chat_date) for row in available_dates_result]
        
        return jsonify({
            'code': 0,
            'message': '获取对话历史成功',
            'data': {
                'chat_history': chat_history,
                'available_dates': available_dates,
                'current_date_filter': date_filter,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': records_pagination.total,
                    'pages': records_pagination.pages,
                    'has_next': records_pagination.has_next,
                    'has_prev': records_pagination.has_prev
                }
            }
        })
        
    except Exception as e:
        print(f"获取对话历史失败: {str(e)}")
        return jsonify({'code': 500, 'message': f'获取对话历史失败: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)