from app.extensions import db
from datetime import datetime

class VehicleLog(db.Model):
    """车辆操作日志模型"""
    __tablename__ = 'vehicle_logs'
    
    # 根据数据库表结构定义字段
    log_id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.vehicle_id'), nullable=False, comment='车辆ID')
    plate_number = db.Column(db.String(20), nullable=False, comment='车牌号')
    log_type = db.Column(db.String(50), nullable=False, comment='日志类型')
    log_content = db.Column(db.Text, nullable=False, comment='日志内容')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    # 关联关系 - 只保留vehicle关系
    vehicle = db.relationship('Vehicle', backref=db.backref('logs', lazy='dynamic'))
    
    def __repr__(self):
        return f'<VehicleLog {self.log_id} {self.log_type}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'log_id': self.log_id,
            'vehicle_id': self.vehicle_id,
            'plate_number': self.plate_number,
            'log_type': self.log_type,
            'log_content': self.log_content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        } 