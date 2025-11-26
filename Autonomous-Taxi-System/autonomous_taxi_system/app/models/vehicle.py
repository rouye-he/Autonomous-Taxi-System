from app import db
from datetime import datetime

class Vehicle(db.Model):
    """车辆模型类"""
    __tablename__ = 'vehicles'
    
    vehicle_id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    vin = db.Column(db.String(50), unique=True)
    model = db.Column(db.String(50))
    current_status = db.Column(db.String(20))
    battery_level = db.Column(db.Float)
    mileage = db.Column(db.Float)
    current_location_name = db.Column(db.String(100))
    current_location_x = db.Column(db.Float)
    current_location_y = db.Column(db.Float)
    current_city = db.Column(db.String(50))
    operating_city = db.Column(db.String(50))
    last_maintenance_date = db.Column(db.Date)
    is_available = db.Column(db.Boolean, default=True)
    manufacture_date = db.Column(db.Date)
    registration_date = db.Column(db.Date)
    rating = db.Column(db.Float, default=5.0)
    total_orders = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """将模型转换为字典"""
        result = {
            'vehicle_id': self.vehicle_id,
            'plate_number': self.plate_number,
            'vin': self.vin,
            'model': self.model,
            'current_status': self.current_status,
            'battery_level': int(self.battery_level) if self.battery_level is not None else 0,
            'mileage': float(self.mileage) if self.mileage is not None else 0,
            'current_location_name': self.current_location_name,
            'current_location_x': self.current_location_x,
            'current_location_y': self.current_location_y,
            'current_city': self.current_city,
            'operating_city': self.operating_city,
            'is_available': bool(self.is_available) if self.is_available is not None else False,
            'rating': float(self.rating) if self.rating is not None else 5.0,
            'total_orders': int(self.total_orders) if self.total_orders is not None else 0
        }
        
        # 处理日期格式
        if self.last_maintenance_date:
            result['last_maintenance_date'] = self.last_maintenance_date.strftime('%Y-%m-%d')
        else:
            result['last_maintenance_date'] = None
            
        if self.manufacture_date:
            result['manufacture_date'] = self.manufacture_date.strftime('%Y-%m-%d')
        else:
            result['manufacture_date'] = None
            
        if self.registration_date:
            result['registration_date'] = self.registration_date.strftime('%Y-%m-%d')
        else:
            result['registration_date'] = None
            
        # 添加格式化的距离
        result['mileage_formatted'] = f"{result['mileage']:,.0f} km"
        
        return result 