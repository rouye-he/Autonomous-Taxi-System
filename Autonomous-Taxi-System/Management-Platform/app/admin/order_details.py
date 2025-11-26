#!/usr/bin/env python
# -*- coding: utf-8 -*-
# app/admin/order_details.py

import traceback
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from app.dao.order_dao import OrderDAO
from app.dao.order_details_dao import OrderDetailsDAO
from app.models.order_details import OrderDetails
from app.config.vehicle_params import ORDER_BASE_PRICE, ORDER_PRICE_PER_KM, PAYMENT_METHODS

order_details_bp = Blueprint('order_details', __name__)

@order_details_bp.route('/api/order/<int:order_id>/details')
def get_order_details_api(order_id):
    """
    获取订单详情API
    
    Args:
        order_id (int): 订单ID
        
    Returns:
        JSON: 订单详情数据
    """
    try:
        # 获取订单基本信息
        order = OrderDAO.get_order_by_id(order_id)
        if not order:
            return jsonify({"status": "error", "message": f"订单 {order_id} 不存在"}), 404
        
        # 获取订单详情记录
        details = OrderDetailsDAO.get_order_details_by_order_id(order_id)
        details_data = [item.to_dict() for item in details]
        
        # 格式化响应
        response = {
            "status": "success",
            "order": order,
            "details": details_data
        }
        
        return jsonify(response)
    except Exception as e:
        print(f"获取订单详情API出错: {str(e)}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@order_details_bp.route('/order/<int:order_id>/details')
def view_order_details(order_id):
    """
    查看订单详情页面
    
    Args:
        order_id (int): 订单ID
        
    Returns:
        HTML: 订单详情页面
    """
    try:
        # 获取订单基本信息
        order = OrderDAO.get_order_by_id(order_id)
        if not order:
            flash(f"订单 {order_id} 不存在", "danger")
            return redirect(url_for('orders.index'))
        
        # 获取订单详情记录
        details = OrderDetailsDAO.get_order_details_by_order_id(order_id)
        
        return render_template(
            'orders/details.html',
            order=order,
            details=details
        )
    except Exception as e:
        print(f"查看订单详情页面出错: {str(e)}")
        traceback.print_exc()
        flash(f"加载订单详情出错: {str(e)}", "danger")
        return redirect(url_for('orders.index'))

@order_details_bp.route('/api/order_details/create', methods=['POST'])
def create_order_details_api():
    """
    手动创建订单详情API
    
    Request Body:
        order_id (str): 订单ID
        vehicle_id (int): 车辆ID
        user_id (int): 用户ID
        amount (float): 订单金额
        distance (float): 行驶距离
        payment_method (str): 支付方式
    
    Returns:
        JSON: 创建结果
    """
    try:
        data = request.json
        required_fields = ['order_id', 'vehicle_id', 'user_id']
        
        # 检查必填字段
        for field in required_fields:
            if field not in data:
                return jsonify({"status": "error", "message": f"缺少必填字段: {field}"}), 400
        
        # 获取订单信息，用于计算距离和金额
        order_info = OrderDAO.get_order_by_id(data['order_id'])
        if not order_info:
            return jsonify({"status": "error", "message": f"订单 {data['order_id']} 不存在"}), 404
            
        # 计算行驶距离
        dx = order_info['dropoff_location_x'] - order_info['pickup_location_x']
        dy = order_info['dropoff_location_y'] - order_info['pickup_location_y']
        distance = (dx ** 2 + dy ** 2) ** 0.5
        distance = round(distance, 2)  # 保留两位小数
        
        # 计算订单金额
        amount = ORDER_BASE_PRICE + (distance * ORDER_PRICE_PER_KM)
        amount = round(amount, 2)  # 保留两位小数
        
        # 验证支付方式
        payment_method = data.get('payment_method', '余额支付')  # 默认使用余额支付
        if payment_method not in PAYMENT_METHODS:
            return jsonify({
                "status": "error", 
                "message": f"支付方式 '{payment_method}' 无效，允许的支付方式: {', '.join(PAYMENT_METHODS)}"
            }), 400
        
        # 创建订单详情对象
        order_details = OrderDetails(
            order_id=data['order_id'],
            vehicle_id=data['vehicle_id'],
            user_id=data['user_id'],
            amount=amount,
            distance=distance,
            payment_method=payment_method
        )
        
        # 保存订单详情
        details_id = OrderDetailsDAO.create_order_details(order_details)
        
        if details_id:
            return jsonify({
                "status": "success", 
                "message": "订单详情创建成功",
                "details_id": details_id,
                "details": {
                    "amount": amount,
                    "distance": distance,
                    "payment_method": payment_method
                }
            })
        else:
            return jsonify({"status": "error", "message": "订单详情创建失败"}), 500
    except Exception as e:
        print(f"创建订单详情API出错: {str(e)}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@order_details_bp.route('/api/order/<int:order_id>/generate_details', methods=['POST'])
def generate_order_details_api(order_id):
    """
    根据订单信息生成订单详情API
    
    Args:
        order_id (int): 订单ID
    
    Returns:
        JSON: 生成结果
    """
    try:
        # 检查订单是否存在
        order = OrderDAO.get_order_by_id(order_id)
        if not order:
            return jsonify({"status": "error", "message": f"订单 {order_id} 不存在"}), 404
        
        # 生成订单详情
        details_id = OrderDetailsDAO.create_details_for_completed_order(order_id)
        
        if details_id:
            return jsonify({
                "status": "success", 
                "message": "订单详情生成成功",
                "details_id": details_id
            })
        else:
            return jsonify({"status": "error", "message": "订单详情生成失败"}), 500
    except Exception as e:
        print(f"生成订单详情API出错: {str(e)}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500 