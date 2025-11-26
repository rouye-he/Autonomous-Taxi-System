from flask import Blueprint

from .dashboard import dashboard_bp
from .vehicles import vehicles_bp
from .users import users_bp
from .orders import orders_bp
from .analytics import analytics_bp
from .finance import finance_bp
from .coupons import coupons_bp
from .order_details import order_details_bp
from .map_obstacles import map_obstacles_bp
from .customer_service import customer_service_bp
from .notifications import notifications_bp
from .algorithm import algorithm_bp
from .settings import settings_bp
from .vehicle_statistics import vehicle_stats_bp
from .order_analysis import order_analysis_bp
from .user_marketing import user_marketing_bp

# 注册所有蓝图到admin总蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 注册子蓝图
admin_bp.register_blueprint(dashboard_bp)
admin_bp.register_blueprint(vehicles_bp)
admin_bp.register_blueprint(users_bp)
admin_bp.register_blueprint(orders_bp)
admin_bp.register_blueprint(analytics_bp)
admin_bp.register_blueprint(finance_bp)
admin_bp.register_blueprint(coupons_bp)
admin_bp.register_blueprint(order_details_bp)
admin_bp.register_blueprint(map_obstacles_bp)
admin_bp.register_blueprint(customer_service_bp)
admin_bp.register_blueprint(notifications_bp)
admin_bp.register_blueprint(algorithm_bp)
admin_bp.register_blueprint(settings_bp)
admin_bp.register_blueprint(vehicle_stats_bp)
admin_bp.register_blueprint(order_analysis_bp)
admin_bp.register_blueprint(user_marketing_bp) 