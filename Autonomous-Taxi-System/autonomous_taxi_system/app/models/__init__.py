from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.order import Order

# 导出模型，使得from app.models import User这样的导入方式可用
__all__ = ['User', 'Vehicle', 'Order'] 