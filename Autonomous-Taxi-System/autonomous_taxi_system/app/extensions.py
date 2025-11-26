"""
存放Flask扩展实例的模块
将扩展实例放在单独文件中可以避免循环导入问题
"""
from flask_sqlalchemy import SQLAlchemy

# 创建数据库实例
db = SQLAlchemy() 