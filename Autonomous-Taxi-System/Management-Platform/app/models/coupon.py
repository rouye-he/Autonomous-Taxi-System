from app.extensions import db
from datetime import datetime

class CouponType(db.Model):
    """优惠券种类模型"""
    __tablename__ = 'coupon_types'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type_name = db.Column(db.String(50), nullable=False, comment='优惠券类型名称')
    coupon_category = db.Column(db.Enum('满减券', '折扣券'), nullable=True, comment='优惠券种类')
    value = db.Column(db.Numeric(10, 2), nullable=False, comment='优惠券面值')
    min_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00, comment='使用门槛')
    description = db.Column(db.String(255), nullable=True, comment='优惠券描述')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    
    def __repr__(self):
        return f'<CouponType {self.type_name}>'


class Coupon(db.Model):
    """优惠券模型"""
    __tablename__ = 'coupons'
    
    coupon_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='优惠券ID')
    user_id = db.Column(db.Integer, nullable=False, comment='用户ID')
    coupon_type_id = db.Column(db.Integer, nullable=False, comment='优惠券类型ID')
    source = db.Column(db.String(50), nullable=False, default='平台发放', comment='来源(套餐购买/活动发放/注册赠送等)')
    source_id = db.Column(db.Integer, nullable=True, comment='来源ID(关联套餐ID或活动ID)')
    receive_time = db.Column(db.DateTime, default=datetime.now, comment='获得时间')
    validity_start = db.Column(db.DateTime, nullable=False, comment='有效期开始')
    validity_end = db.Column(db.DateTime, nullable=False, comment='有效期结束')
    use_time = db.Column(db.DateTime, nullable=True, comment='使用时间')
    order_id = db.Column(db.String(50), nullable=True, comment='使用订单ID')
    status = db.Column(db.Enum('未使用', '已使用', '已过期'), default='未使用', comment='优惠券状态')
    
    def __repr__(self):
        return f'<Coupon {self.coupon_id}>'


class CouponPackage(db.Model):
    """优惠券套餐模型"""
    __tablename__ = 'coupon_packages'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='套餐名称')
    description = db.Column(db.Text, nullable=True, comment='套餐简介')
    price = db.Column(db.Numeric(10, 2), nullable=False, comment='套餐价格')
    original_price = db.Column(db.Numeric(10, 2), nullable=False, comment='原价/折扣前价格')
    status = db.Column(db.Integer, nullable=False, default=1, comment='状态(1:上架, 0:下架)')
    validity_days = db.Column(db.Integer, nullable=False, default=30, comment='有效期(天)')
    coupon_details = db.Column(db.JSON, nullable=False, comment='包含的优惠券详情')
    sale_count = db.Column(db.Integer, nullable=False, default=0, comment='已售数量')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    
    def __repr__(self):
        return f'<CouponPackage {self.name}>' 