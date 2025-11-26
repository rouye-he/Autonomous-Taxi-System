from flask import Blueprint, render_template

# 创建蓝图
customer_service_bp = Blueprint('customer_service', __name__, url_prefix='/customer_service')

@customer_service_bp.route('/')
def index():
    """客服管理主页"""
    return render_template('customer_service/index.html') 