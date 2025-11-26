from app import db
from datetime import datetime

class Order(db.Model):
    """订单模型类 - 简化版"""
    __tablename__ = 'orders'
    
    order_id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.vehicle_id'))
    order_status = db.Column(db.String(20))
    create_time = db.Column(db.DateTime)
    arrival_time = db.Column(db.DateTime)
    pickup_location = db.Column(db.String(255))
    dropoff_location = db.Column(db.String(255))
    city_code = db.Column(db.String(50), comment='城市中文名称')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """将模型转换为字典"""
        result = {
            'order_id': self.order_id,
            'order_number': self.order_number,
            'user_id': self.user_id,
            'vehicle_id': self.vehicle_id,
            'order_status': self.order_status,
            'pickup_location': self.pickup_location,
            'dropoff_location': self.dropoff_location,
            'city_code': self.city_code
        }
        
        # 处理日期格式
        if self.create_time:
            result['create_time'] = self.create_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            result['create_time'] = None
            
        if self.arrival_time:
            result['arrival_time'] = self.arrival_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            result['arrival_time'] = None
        
        return result 