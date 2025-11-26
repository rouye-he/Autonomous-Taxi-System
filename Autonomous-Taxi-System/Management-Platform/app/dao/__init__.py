"""
数据访问对象(DAO)模块
提供对数据库的操作封装
"""

from app.dao.vehicle_dao import VehicleDAO
from app.dao.order_dao import OrderDAO

__all__ = ['VehicleDAO', 'OrderDAO'] 