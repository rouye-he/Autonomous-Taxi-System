from flask import Flask, request, session
from app.extensions import db  # 从extensions导入db
import os
from flask_babel import Babel
from app.admin.vehicles import vehicles_bp
from app.admin.orders import orders_bp
from app.admin.finance import finance_bp
from app.admin.analytics import analytics_bp
from app.admin.customer_service import customer_service_bp
from app.admin.dashboard import dashboard_bp
from app.admin.users import users_bp
from app.admin.settings import settings_bp
from app.admin.algorithm import algorithm_bp
from app.admin.notifications import notifications_bp
from app.admin.order_details import order_details_bp
from app.admin.user_marketing import user_marketing_bp
from app.admin.financial_health import financial_health_bp
from app.api.v1 import api_v1
from app.api.credit import credit_bp
import sys
from flask_socketio import SocketIO
from flask_cors import CORS
from app.admin.vehicles import ZeroBatteryCheckerThread
from app.admin import admin_bp
from app.admin.map_obstacles import map_obstacles_bp
from datetime import datetime
from app.admin.coupons import coupons_bp
from app.admin.language import language_bp

# 创建SocketIO对象，供所有模块使用
socketio = SocketIO()

# 创建Babel对象，供所有模块使用
babel = Babel()

def get_locale():
    """获取当前语言设置"""
    # 1. 首先检查URL参数
    locale = request.args.get('lang')
    if locale in ['zh', 'en']:
        session['language'] = locale
        return locale
    
    # 2. 检查session中的语言设置
    if 'language' in session:
        return session['language']
    
    # 3. 检查浏览器Accept-Language头
    return request.accept_languages.best_match(['zh', 'en']) or 'zh'

def create_app():
    """创建和配置Flask应用"""
    global app, db, zero_battery_checker_thread
    
    app = Flask(__name__, instance_relative_config=True)
    app.jinja_env.add_extension('jinja2.ext.loopcontrols')
    app.jinja_env.add_extension('jinja2.ext.i18n')
    
    # 先从config.py中加载默认配置
    config_class = 'ProductionConfig'  # 默认使用生产环境配置
    
    # 根据环境参数选择不同的配置
    if '--dev' in sys.argv:
        config_class = 'DevelopmentConfig'
    elif '--test' in sys.argv:
        config_class = 'TestingConfig'
    
    # 打印当前使用的配置类型
    print(f"使用配置: {config_class}")
    
    # 加载配置
    app.config.from_object(f'app.config.{config_class}')
    
    # 配置Babel
    app.config['BABEL_DEFAULT_LOCALE'] = 'zh'
    app.config['BABEL_SUPPORTED_LOCALES'] = ['zh', 'en']
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
    
    # 初始化扩展
    db.init_app(app)
    cors = CORS(app)
    babel.init_app(app, locale_selector=get_locale)
    
    # 初始化Socket.IO
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
    
    # 添加根路由重定向到dashboard
    @app.route('/')
    def index():
        from flask import redirect
        return redirect('/dashboard/')
    
    # 启动零电量检测线程
    with app.app_context():
        zero_battery_checker_thread = ZeroBatteryCheckerThread(check_interval=300)  # 5分钟检查一次
        zero_battery_checker_thread.daemon = True
        zero_battery_checker_thread.start()

    # 调用初始化函数    
    init_app()
    
    # 注册自定义过滤器
    @app.template_filter('datetime')
    def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
        if value is None:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    value = datetime.strptime(value, '%Y-%m-%d')
                except ValueError:
                    return value
        return value.strftime(format)
    
    @app.template_filter('date')
    def format_date(value, format='%Y-%m-%d'):
        if value is None:
            return ""
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    value = datetime.strptime(value, '%Y-%m-%d')
                except ValueError:
                    return value
        return value.strftime(format)
    
    @app.template_filter('yesno')
    def yesno_filter(value, yes_text='是', no_text='否'):
        return yes_text if value else no_text
    
    return app

def init_test_notifications():
    """初始化测试通知数据"""
    from app.utils.notification_service import NotificationService
    import random
    from datetime import datetime, timedelta
    
    # 创建一些测试车辆通知
    vehicle_ids = [1001, 1002, 1025, 3078, 4096]
    battery_levels = [5, 8, 12, 15, 20]
    maintenance_reasons = [
        "轮胎磨损需要更换", 
        "制动系统故障", 
        "传感器校准需要维护",
        "定期保养",
        "车身清洗"
    ]
    statuses = ["空闲", "行驶中", "维护中", "充电中", "电量不足"]
    
    for i in range(3):
        vehicle_id = random.choice(vehicle_ids)
        
        # 低电量通知
        if random.random() < 0.7:
            battery_level = random.choice(battery_levels)
            NotificationService.notify_vehicle_low_battery(vehicle_id, battery_level)
        
        # 维护通知
        if random.random() < 0.5:
            reason = random.choice(maintenance_reasons)
            NotificationService.notify_vehicle_maintenance_required(vehicle_id, reason)
        
        # 状态变更通知
        if random.random() < 0.8:
            old_status = random.choice(statuses)
            new_status = random.choice([s for s in statuses if s != old_status])
            NotificationService.notify_vehicle_status_changed(vehicle_id, old_status, new_status)
    
    # 创建一些测试订单通知
    order_ids = [10001, 10025, 10086, 10099, 10105]
    origins = ["北京市海淀区中关村", "上海市浦东新区陆家嘴", "广州市天河区珠江新城", "深圳市南山区科技园", "杭州市西湖区"]
    destinations = ["北京市朝阳区三里屯", "上海市静安区南京西路", "广州市越秀区北京路", "深圳市福田区华强北", "杭州市滨江区"]
    cancel_reasons = ["用户取消", "系统故障", "车辆故障", "道路拥堵", "天气原因"]
    
    for i in range(3):
        order_id = random.choice(order_ids)
        
        # 新订单通知
        if random.random() < 0.7:
            origin = random.choice(origins)
            destination = random.choice([d for d in destinations if d != origin])
            NotificationService.notify_new_order(order_id, origin, destination)
        
        # 完成订单通知
        if random.random() < 0.6:
            duration = random.randint(15, 90)
            distance = round(random.uniform(2.0, 30.0), 1)
            amount = round(distance * random.uniform(2.0, 3.5), 2)
            NotificationService.notify_order_completed(order_id, duration, distance, amount)
        
        # 取消订单通知
        if random.random() < 0.4:
            reason = random.choice(cancel_reasons)
            NotificationService.notify_order_cancelled(order_id, reason)
    
    # 创建一些测试系统通知
    error_messages = [
        "数据库连接失败，请检查配置",
        "网络连接超时，无法访问远程服务",
        "地图服务API返回错误，无法规划路线",
        "文件系统空间不足，需要清理",
        "Redis缓存服务不可用，使用备用模式"
    ]
    
    # 系统错误通知
    for i in range(2):
        if random.random() < 0.5:
            error_message = random.choice(error_messages)
            NotificationService.notify_system_error(error_message)
    
    # 将一些通知标记为已读
    from app.dao.notification_dao import NotificationDAO
    notification_ids = list(range(1, 14))  # 假设有13个通知
    read_ids = random.sample(notification_ids, 5)  # 随机选择5个标记为已读
    
    for notification_id in read_ids:
        NotificationDAO.mark_as_read(notification_id)
        
    print(f"已初始化{len(notification_ids)}个测试通知，其中{len(read_ids)}个标记为已读")

def init_app():
    """初始化Flask应用"""
    
    # 创建数据库表
    with app.app_context():
        try:
            db.create_all()
            
            # 检查并确保系统通知表中有content列
            from app.dao.base_dao import BaseDAO
            check_query = "SHOW COLUMNS FROM system_notifications LIKE 'content'"
            check_result = BaseDAO.execute_query(check_query)
            
            if not check_result:
                print("系统通知表中不存在content列，正在添加...")
                add_column_query = """
                ALTER TABLE system_notifications 
                ADD COLUMN content VARCHAR(255) COMMENT '通知详细内容' AFTER title
                """
                BaseDAO.execute_update(add_column_query)
                print("已成功添加content列到系统通知表")
                
            # 初始化车辆参数
            from app.config.vehicle_params import init_params
            init_params()
                
        except Exception as e:
            app.logger.error(f"数据库初始化错误: {str(e)}")

    # 添加旧API路径重定向
    @app.route('/api/system_parameters', methods=['GET', 'POST'])
    def redirect_system_parameters():
        from flask import request, redirect, url_for
        # 重定向到v1版本的API
        return redirect(url_for('api_v1.get_system_parameters' if request.method == 'GET' else 'api_v1.update_system_parameters'))

    app.register_blueprint(admin_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(customer_service_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(order_details_bp)
    app.register_blueprint(api_v1)
    app.register_blueprint(algorithm_bp)
    app.register_blueprint(map_obstacles_bp)
    app.register_blueprint(credit_bp)
    app.register_blueprint(user_marketing_bp)
    app.register_blueprint(financial_health_bp)
    app.register_blueprint(coupons_bp)
    app.register_blueprint(language_bp)
    
    # 初始化数据
    init_test_data_if_needed()

def init_test_data_if_needed():
    """根据需要初始化测试数据"""
    # 检查是否设置了初始化测试数据的命令行参数
    if '--init-test-data' in sys.argv:
        print("正在初始化测试数据...")
        init_test_notifications()
        print("测试数据初始化完成")
    else:
        # 只创建系统启动通知
        from app.utils.notification_service import NotificationService
        NotificationService.notify_system_startup() 