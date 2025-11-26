from flask import Blueprint

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# 导入API路由
from app.api.v1 import users
from app.api.v1 import notifications
from app.api.v1 import system_parameters
# 以下模块尚未创建，暂时注释掉
# from app.api.v1 import vehicles, orders

# 注册其他路由函数... 