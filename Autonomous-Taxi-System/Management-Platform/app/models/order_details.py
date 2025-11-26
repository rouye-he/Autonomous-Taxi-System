#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/models/order_details.py

from datetime import datetime

class OrderDetails:
    """订单详情模型"""
    
    def __init__(self, order_id=None, vehicle_id=None, user_id=None, amount=0.0, 
                 distance=0.0, payment_method="余额支付", id=None, created_at=None, updated_at=None):
        """
        初始化订单详情对象
        
        Args:
            order_id (str): 订单ID
            vehicle_id (int): 车辆ID
            user_id (int): 用户ID
            amount (float): 订单金额
            distance (float): 行驶距离
            payment_method (str): 支付方式
            id (int, optional): 记录ID
            created_at (datetime, optional): 创建时间
            updated_at (datetime, optional): 更新时间
        """
        self.id = id
        self.order_id = order_id
        self.vehicle_id = vehicle_id
        self.user_id = user_id
        self.amount = amount
        self.distance = distance
        self.payment_method = payment_method
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def to_dict(self):
        """
        将订单详情转换为字典
        
        Returns:
            dict: 订单详情的字典表示
        """
        return {
            'id': self.id,
            'order_id': self.order_id,
            'vehicle_id': self.vehicle_id,
            'user_id': self.user_id,
            'amount': self.amount,
            'distance': self.distance,
            'payment_method': self.payment_method,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        从字典创建订单详情对象
        
        Args:
            data (dict): 订单详情数据字典
            
        Returns:
            OrderDetails: 订单详情对象
        """
        return cls(
            id=data.get('id'),
            order_id=data.get('order_id'),
            vehicle_id=data.get('vehicle_id'),
            user_id=data.get('user_id'),
            amount=data.get('amount'),
            distance=data.get('distance'),
            payment_method=data.get('payment_method'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        ) 