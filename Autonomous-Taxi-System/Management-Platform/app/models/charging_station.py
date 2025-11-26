from app.extensions import db
from datetime import datetime

class ChargingStation(db.Model):
    """充电站模型"""
    __tablename__ = 'charging_stations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='充电站名称')
    address = db.Column(db.String(255), nullable=False, comment='充电站地址')
    city = db.Column(db.String(50), nullable=False, comment='所在城市')
    total_ports = db.Column(db.Integer, default=0, comment='充电桩总数')
    available_ports = db.Column(db.Integer, default=0, comment='可用充电桩数')
    is_active = db.Column(db.Boolean, default=True, comment='是否运营中')
    latitude = db.Column(db.Float, comment='纬度')
    longitude = db.Column(db.Float, comment='经度')
    open_time = db.Column(db.String(20), default='00:00-24:00', comment='营业时间')
    charging_fee = db.Column(db.Float, default=1.5, comment='每度电价格(元)')
    service_fee = db.Column(db.Float, default=0.5, comment='服务费(元/度)')
    is_fast_charging = db.Column(db.Boolean, default=True, comment='是否支持快充')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f'<ChargingStation {self.name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'total_ports': self.total_ports,
            'available_ports': self.available_ports,
            'is_active': self.is_active,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'open_time': self.open_time,
            'charging_fee': self.charging_fee,
            'service_fee': self.service_fee,
            'is_fast_charging': self.is_fast_charging,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        } 