#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/dao/order_details_dao.py

import traceback
from datetime import datetime
from app.dao.base_dao import BaseDAO
from app.models.order_details import OrderDetails

class OrderDetailsDAO(BaseDAO):
    """订单详情数据访问对象"""
    
    @staticmethod
    def create_order_details(order_details):
        """
        创建新的订单详情记录
        
        Args:
            order_details: 订单详情对象或字典
            
        Returns:
            int: 新创建的订单详情ID，失败返回None
        """
        try:
            # 导入允许的支付方式
            from app.config.vehicle_params import PAYMENT_METHODS
            
            # 检查是否是字典，如果是字典则使用字典访问方式
            is_dict = isinstance(order_details, dict)
            
            # 验证支付方式
            if is_dict:
                payment_method = order_details.get('payment_method')
                if payment_method not in PAYMENT_METHODS:
                    # 如果支付方式不在允许列表中，使用余额支付
                    print(f"支付方式 '{payment_method}' 不允许，使用余额支付")
                    order_details['payment_method'] = '余额支付'  # 强制使用余额支付
            else:
                if order_details.payment_method not in PAYMENT_METHODS:
                    # 如果支付方式不在允许列表中，使用余额支付
                    print(f"支付方式 '{order_details.payment_method}' 不允许，使用余额支付")
                    order_details.payment_method = '余额支付'  # 强制使用余额支付
                
            # 构建插入SQL
            query = """
            INSERT INTO order_details 
            (order_id, vehicle_id, user_id, amount, distance, payment_method)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            # 根据传入参数类型获取参数值
            if is_dict:
                params = (
                    order_details.get('order_id'),
                    order_details.get('vehicle_id'),
                    order_details.get('user_id'),
                    order_details.get('amount'),
                    order_details.get('distance'),
                    order_details.get('payment_method')
                )
            else:
                params = (
                    order_details.order_id,
                    order_details.vehicle_id,
                    order_details.user_id,
                    order_details.amount,
                    order_details.distance,
                    order_details.payment_method
                )
            
            # 执行插入并获取行数
            affected_rows = BaseDAO.execute_update(query, params)
            
            if affected_rows > 0:
                # 获取最后插入的ID
                id_query = "SELECT LAST_INSERT_ID() as id"
                result = BaseDAO.execute_query(id_query)
                
                if result and 'id' in result[0]:
                    insert_id = result[0]['id']
                    return insert_id
                else:
                    print("无法获取新插入记录的ID")
                    return None
            else:
                print("添加订单详情记录失败")
                return None
                
        except Exception as e:
            print(f"创建订单详情记录出错: {str(e)}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_order_details_by_order_id(order_id):
        """
        根据订单ID获取订单详情
        
        Args:
            order_id (str): 订单ID
            
        Returns:
            list: 订单详情对象列表
        """
        try:
            query = """
            SELECT * FROM order_details
            WHERE order_id = %s
            ORDER BY created_at DESC
            """
            
            results = BaseDAO.execute_query(query, (order_id,))
            
            order_details_list = []
            for row in results:
                order_details = OrderDetails(
                    id=row['id'],
                    order_id=row['order_id'],
                    vehicle_id=row['vehicle_id'],
                    user_id=row['user_id'],
                    amount=row['amount'],
                    distance=row['distance'],
                    payment_method=row['payment_method'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                order_details_list.append(order_details)
                
            return order_details_list
            
        except Exception as e:
            print(f"获取订单详情记录出错: {str(e)}")
            traceback.print_exc()
            return []
    
    @staticmethod
    def create_details_for_completed_order(order_id):
        """
        为已完成的订单创建详情记录
        
        Args:
            order_id (str): 订单ID
            
        Returns:
            int: 新创建的订单详情ID，失败返回None
        """
        try:
            # 首先获取订单信息
            from app.dao.order_dao import OrderDAO
            order = OrderDAO.get_order_by_id(order_id)
            
            if not order:
                print(f"无法找到订单ID: {order_id}")
                return None
            
            # 导入车辆参数配置
            from app.config.vehicle_params import ORDER_BASE_PRICE, ORDER_PRICE_PER_KM, ORDER_BASE_KM, PAYMENT_METHODS
            from app.config.vehicle_params import get_city_order_price_factor, get_weighted_payment_method
            
            # 获取城市代码和城市价格系数
            city = order.get('city_code')
            city_price_factor = get_city_order_price_factor(city)
            
            # 尝试获取车辆价格系数
            order_price_coefficient = 1.0  # 默认价格系数为1.0
            vehicle_model = order.get('model')
            vehicle_id = order.get('vehicle_id')
            
            if vehicle_id:
                try:
                    # 获取车辆参数
                    from app.admin.orders import get_vehicle_parameters
                    _, vehicle_params_dict = get_vehicle_parameters(vehicle_id)
                    if vehicle_params_dict and 'order_price_coefficient' in vehicle_params_dict:
                        order_price_coefficient = vehicle_params_dict.get('order_price_coefficient')
                    else:
                        print(f"未能获取车型 {vehicle_model} 的订单价格系数，使用默认值1.0")
                except Exception as e:
                    print(f"获取车辆订单价格系数出错: {e}")
                    traceback.print_exc()
            
            # 计算距离
            dx = order.get('dropoff_location_x', 0) - order.get('pickup_location_x', 0)
            dy = order.get('dropoff_location_y', 0) - order.get('pickup_location_y', 0)
            distance_in_units = ((dx ** 2 + dy ** 2) ** 0.5)
            
            # 计算距离（公里）
            try:
                from app.config.vehicle_params import CITY_DISTANCE_RATIO
                city_ratio = CITY_DISTANCE_RATIO.get(city, 0.1)
                distance = distance_in_units * city_ratio
                distance = round(distance, 2)
            except ImportError:
                distance = distance_in_units * 0.1
                distance = round(distance, 2)
            
            # 计算订单金额，考虑车型系数和城市价格系数
            # 根据距离计算基础金额
            if distance <= ORDER_BASE_KM:
                # 距离在起步范围内，只收起步价
                base_amount = ORDER_BASE_PRICE
            else:
                # 距离超过起步范围，收取起步价加超出部分的里程费
                base_amount = ORDER_BASE_PRICE + ((distance - ORDER_BASE_KM) * ORDER_PRICE_PER_KM)
            
            # 应用车型价格系数和城市价格系数
            amount = base_amount * order_price_coefficient * city_price_factor
            amount = round(amount, 2)  # 保留两位小数
            
            # 使用固定的余额支付，不再使用加权随机选择
            payment_method = '余额支付'
            
            # 创建订单详情字典
            order_details = {
                "order_id": order_id,
                "vehicle_id": vehicle_id,
                "user_id": order.get('user_id'),
                "amount": amount,
                "distance": distance,
                "payment_method": payment_method
            }
            
            # 保存订单详情
            return OrderDetailsDAO.create_order_details(order_details)
            
        except Exception as e:
            print(f"为已完成订单创建详情记录出错: {str(e)}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_order_details_by_id(id):
        """
        根据ID获取订单详情
        
        Args:
            id (int): 订单详情ID
            
        Returns:
            OrderDetails: 订单详情对象，不存在返回None
        """
        try:
            query = "SELECT * FROM order_details WHERE id = %s"
            results = BaseDAO.execute_query(query, (id,))
            
            if results:
                row = results[0]
                return OrderDetails(
                    id=row['id'],
                    order_id=row['order_id'],
                    vehicle_id=row['vehicle_id'],
                    user_id=row['user_id'],
                    amount=row['amount'],
                    distance=row['distance'],
                    payment_method=row['payment_method'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return None
            
        except Exception as e:
            print(f"通过ID获取订单详情出错: {str(e)}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def update_order_details(order_details):
        """
        更新订单详情
        
        Args:
            order_details (OrderDetails): 订单详情对象
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            query = """
            UPDATE order_details
            SET order_id = %s, vehicle_id = %s, user_id = %s,
                amount = %s, distance = %s, payment_method = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            
            params = (
                order_details.order_id,
                order_details.vehicle_id,
                order_details.user_id,
                order_details.amount,
                order_details.distance,
                order_details.payment_method,
                order_details.id
            )
            
            affected_rows = BaseDAO.execute_update(query, params)
            return affected_rows > 0
            
        except Exception as e:
            print(f"更新订单详情出错: {str(e)}")
            traceback.print_exc()
            return False 