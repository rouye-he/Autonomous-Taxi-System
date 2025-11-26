from flask import Blueprint, render_template, jsonify, request, Response
from app.dao.order_dao import OrderDAO
import traceback
from app.dao.vehicle_dao import VehicleDAO
from app.dao.base_dao import BaseDAO
import threading
import time
import math
from datetime import datetime
from app.config.vehicle_params import (
    VEHICLE_MOVEMENT_SPEED,
    BATTERY_CONSUMPTION_RATE,
    LOW_BATTERY_THRESHOLD,
    POSITION_UPDATE_INTERVAL,
    CHARGING_RATE,
    RUNNING_BATTERY_UPDATE_INTERVAL,
    LOW_BATTERY_UPDATE_INTERVAL,
    CHARGING_BATTERY_UPDATE_INTERVAL,
    POSITION_MOVEMENT_INTERVAL,
    BATTERY_UPDATE_INTERVAL,
    PICKUP_WAITING_TIME,
    # 车型速度系数
    Alpha_X1_SPEED,
    Alpha_Nexus_SPEED,
    Alpha_Voyager_SPEED,
    Nova_S1_SPEED,
    Nova_Quantum_SPEED,
    Nova_Pulse_SPEED,
    Neon_500_SPEED,
    Neon_Zero_SPEED,
    # 车型电池容量系数
    Alpha_X1_CAPACITY,
    Alpha_Nexus_CAPACITY,
    Alpha_Voyager_CAPACITY,
    Nova_S1_CAPACITY,
    Nova_Quantum_CAPACITY,
    Nova_Pulse_CAPACITY,
    Neon_500_CAPACITY,
    Neon_Zero_CAPACITY,
    # 车型充电速度系数
    Alpha_X1_CHARGING_SPEED,
    Alpha_Nexus_CHARGING_SPEED,
    Alpha_Voyager_CHARGING_SPEED,
    Nova_S1_CHARGING_SPEED,
    Nova_Quantum_CHARGING_SPEED,
    Nova_Pulse_CHARGING_SPEED,
    Neon_500_CHARGING_SPEED,
    Neon_Zero_CHARGING_SPEED,
    # 车型能耗系数
    Alpha_X1_ENERGY_CONSUMPTION_COEFFICIENT,
    Alpha_Nexus_ENERGY_CONSUMPTION_COEFFICIENT,
    Alpha_Voyager_ENERGY_CONSUMPTION_COEFFICIENT,
    Nova_S1_ENERGY_CONSUMPTION_COEFFICIENT,
    Nova_Quantum_ENERGY_CONSUMPTION_COEFFICIENT,
    Nova_Pulse_ENERGY_CONSUMPTION_COEFFICIENT,
    Neon_500_ENERGY_CONSUMPTION_COEFFICIENT,
    Neon_Zero_ENERGY_CONSUMPTION_COEFFICIENT,
    # 车型维护成本系数
    Alpha_X1_MAINTENANCE_COST,
    Alpha_Nexus_MAINTENANCE_COST,
    Alpha_Voyager_MAINTENANCE_COST,
    Nova_S1_MAINTENANCE_COST,
    Nova_Quantum_MAINTENANCE_COST,
    Nova_Pulse_MAINTENANCE_COST,
    Neon_500_MAINTENANCE_COST,
    Neon_Zero_MAINTENANCE_COST,
    # 车型订单价格系数
    Alpha_X1_ORDER_PRICE,
    Alpha_Nexus_ORDER_PRICE,
    Alpha_Voyager_ORDER_PRICE,
    Nova_S1_ORDER_PRICE,
    Nova_Quantum_ORDER_PRICE,
    Nova_Pulse_ORDER_PRICE,
    Neon_500_ORDER_PRICE,
    Neon_Zero_ORDER_PRICE,
    # 参数获取函数
    get_param,
    get_city_charging_price_factor
)
import uuid
import json
from app.dao.charging_station_dao import ChargingStationDAO
from app.admin.algorithm import OrderAssignmentAlgorithm



# 创建线程字典，用于跟踪车辆移动线程
vehicle_movement_threads = {}

# 创建全局字典用于跟踪自动分配任务
auto_assign_tasks = {}
auto_assign_stop_signals = {}

# 创建蓝图
orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

# 添加辅助函数计算车辆速度
def calculate_vehicle_speed(vehicle_id):
    """根据车辆型号计算实际速度
    
    Args:
        vehicle_id: 车辆ID
        
    Returns:
        tuple: (实际速度, 车辆型号, 速度系数)
    """
    # 获取车辆所有特性参数
    vehicle_model, vehicle_params = get_vehicle_parameters(vehicle_id)
    
    # 获取基础速度（直接从数据库获取）
    base_speed = get_param('VEHICLE_MOVEMENT_SPEED')
    if base_speed is None:
        print("警告：未能从数据库获取基础速度 VEHICLE_MOVEMENT_SPEED，请检查数据库")
        return 0, vehicle_model, 0
    
    # 如果速度系数为None，使用1.0作为备用
    speed_coefficient = vehicle_params['speed_coefficient']
    if speed_coefficient is None:
        print(f"警告：车型 {vehicle_model} 的速度系数为None，使用1.0作为备用")
        speed_coefficient = 1.0
    
    # 计算实际速度 = 基础速度 * 速度系数
    actual_speed = base_speed * speed_coefficient
    
    return actual_speed, vehicle_model, speed_coefficient

def get_vehicle_parameters(vehicle_id):
    """获取车辆所有特性参数
    
    Args:
        vehicle_id: 车辆ID
        
    Returns:
        tuple: (车辆型号, 包含所有特性参数的字典)
    """
    # 获取车辆型号
    vehicle = VehicleDAO.get_vehicle_by_id(vehicle_id)
    vehicle_model = vehicle.get('model') if vehicle else None
    
    
    # 初始化参数字典
    vehicle_params = {
        'speed_coefficient': None,        # 速度系数
        'capacity_coefficient': None,     # 电池容量系数
        'charging_speed_coefficient': None, # 充电速度系数
        'energy_consumption_coefficient': None, # 能耗系数
        'maintenance_cost_coefficient': None, # 维护成本系数
        'order_price_coefficient': None   # 订单价格系数
    }
    
    # 根据车型设置对应参数 - 直接从数据库获取参数
    if vehicle_model:
        # 替换连字符为下划线，生成参数键名
        model_key = vehicle_model.replace('-', '_')
        
        # 构建各参数的键名
        speed_param = f"{model_key}_SPEED"
        capacity_param = f"{model_key}_CAPACITY"
        charging_param = f"{model_key}_CHARGING_SPEED"
        energy_param = f"{model_key}_ENERGY_CONSUMPTION_COEFFICIENT"
        maintenance_param = f"{model_key}_MAINTENANCE_COST"
        order_price_param = f"{model_key}_ORDER_PRICE"
        
        
        # 从数据库获取参数（不使用默认值）
        vehicle_params['speed_coefficient'] = get_param(speed_param)
        vehicle_params['capacity_coefficient'] = get_param(capacity_param)
        vehicle_params['charging_speed_coefficient'] = get_param(charging_param)
        vehicle_params['energy_consumption_coefficient'] = get_param(energy_param)
        vehicle_params['maintenance_cost_coefficient'] = get_param(maintenance_param)
        vehicle_params['order_price_coefficient'] = get_param(order_price_param)
        
    else:
        print(f"警告：车辆ID {vehicle_id} 无法获取车型信息，系统将尝试从数据库读取默认参数")
        
        # 无车型信息时，尝试从数据库获取默认参数
        vehicle_params['speed_coefficient'] = get_param('DEFAULT_SPEED_COEFFICIENT')
        vehicle_params['capacity_coefficient'] = get_param('DEFAULT_CAPACITY_COEFFICIENT')
        vehicle_params['charging_speed_coefficient'] = get_param('DEFAULT_CHARGING_SPEED_COEFFICIENT')
        vehicle_params['energy_consumption_coefficient'] = get_param('DEFAULT_ENERGY_CONSUMPTION_COEFFICIENT')
        vehicle_params['maintenance_cost_coefficient'] = get_param('DEFAULT_MAINTENANCE_COST_COEFFICIENT')
        vehicle_params['order_price_coefficient'] = get_param('DEFAULT_ORDER_PRICE_COEFFICIENT')
    
    # 检查是否获取到了有效的参数值，若为None则发出警告
    for param_name, param_value in vehicle_params.items():
        if param_value is None:
            print(f"警告：未能从数据库获取车型 {vehicle_model} 的 {param_name} 参数，请检查数据库")
    
    return vehicle_model, vehicle_params

@orders_bp.route('/')
def index():
    """订单管理主页"""
    # 获取搜索参数
    search_params = {}
    for key, value in request.args.items():
        if value and key != 'page' and key != 'ajax' and key != 'include_stats':
            search_params[key] = value

    page = request.args.get('page', 1, type=int)
    
    # 如果有搜索参数，进行高级搜索
    if search_params:
        return advanced_search()
    
    try:
        # 使用OrderDAO获取订单数据
        result = OrderDAO.get_all_orders(page=page, per_page=10)
        
        # 字段中文名映射
        field_names = {
            'order_id': '订单ID',
            'order_number': '订单编号',
            'user_id': '用户ID',
            'vehicle_id': '车辆ID',
            'username': '用户名',
            'real_name': '用户姓名',
            'plate_number': '车牌号',
            'order_status': '订单状态',
            'payment_status': '支付状态',
            'payment_method': '支付方式',
            'city_code': '城市',
            'trip_type': '行程类型',
            'create_time_start': '下单时间(开始)',
            'create_time_end': '下单时间(结束)',
            'distance_min': '最短距离',
            'distance_max': '最长距离',
            'total_fare_min': '最低金额',
            'total_fare_max': '最高金额',
            'user_rating_min': '最低评分',
            'user_rating_max': '最高评分'
        }
        
        # 获取状态统计
        # 如果订单结果中不包含状态统计，手动计算
        if 'status_counts' not in result:
            # 这种情况不应该发生，因为我们已经在DAO层添加了状态统计
            print("警告: DAO层未返回状态统计，将使用默认值")
            status_counts = {'all': result['total_count'], 'completed': 0, 'in_progress': 0, 'waiting': 0, 'cancelled': 0}
        else:
            status_counts = result['status_counts']
        
        # 检查是否是AJAX请求
        is_ajax = request.args.get('ajax') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        include_stats = request.args.get('include_stats') == '1'
        
        if is_ajax:
            # 准备AJAX响应
            html_content = render_template('orders/_order_table.html', 
                                      orders=result['orders'],
                                      current_page=result['current_page'],
                                      total_pages=result['total_pages'],
                                      total_count=result['total_count'],
                                      offset=(result['current_page'] - 1) * 10,
                                      per_page=10,
                                      search_params=search_params)
            
            # 构建响应数据
            response_data = {
                'html': html_content,
                'current_page': result['current_page'],
                'total_pages': result['total_pages']
            }
            
            # 如果需要包含统计数据
            if include_stats:
                response_data['stats'] = {
                    'waiting': status_counts.get('waiting', 0),
                    'in_progress': status_counts.get('in_progress', 0),
                    'completed': status_counts.get('completed', 0),
                    'total': result['total_count']
                }
            
            return jsonify(response_data)
            
        # 普通请求返回完整页面
        return render_template('orders/index.html', 
                           orders=result['orders'],
                           current_page=result['current_page'],
                           total_pages=result['total_pages'],
                           total_count=result['total_count'],
                           offset=(result['current_page'] - 1) * 10,
                           per_page=10,
                           search_params=search_params,
                           status_counts=status_counts,
                           field_names=field_names)
    except Exception as e:
        print(f"订单列表加载错误: {str(e)}")
        traceback.print_exc()
        
        # 检查是否是AJAX请求
        is_ajax = request.args.get('ajax') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
        
        # 返回错误页面
        return render_template('orders/index.html', 
                           orders=[],
                           current_page=1,
                           total_pages=1,
                           total_count=0,
                           offset=0,
                           per_page=10,
                           search_params={},
                           status_counts={'waiting': 0, 'in_progress': 0, 'completed': 0, 'cancelled': 0},
                           field_names=field_names,
                           error=str(e))

@orders_bp.route('/advanced_search')
def advanced_search():
    """订单高级搜索"""
    # 获取查询参数
    search_params = {}
    for key, value in request.args.items():
        if value and key != 'page' and key != 'ajax' and key != 'include_stats':
            search_params[key] = value
    
    page = request.args.get('page', 1, type=int)
    
    # 字段中文名映射
    field_names = {
        'order_id': '订单ID',
        'order_number': '订单编号',
        'user_id': '用户ID',
        'vehicle_id': '车辆ID',
        'username': '用户名',
        'real_name': '用户姓名',
        'plate_number': '车牌号',
        'order_status': '订单状态',
        'payment_status': '支付状态',
        'payment_method': '支付方式',
        'city_code': '城市',
        'trip_type': '行程类型',
        'create_time_start': '下单时间(开始)',
        'create_time_end': '下单时间(结束)',
        'arrival_time_start': '到达时间(开始)',
        'arrival_time_end': '到达时间(结束)',
        'pickup_location': '上车地点',
        'dropoff_location': '下车地点',
        'distance_min': '最短距离',
        'distance_max': '最长距离',
        'total_fare_min': '最低金额',
        'total_fare_max': '最高金额',
        'user_rating_min': '最低评分',
        'user_rating_max': '最高评分'
    }
    
    try:
        # 使用OrderDAO进行高级搜索 - 使用get_orders_by_criteria方法替代search_orders
        per_page = 10
        offset = (page - 1) * per_page
        
        # 调用get_orders_by_criteria方法获取数据
        total_count, orders, status_counts = OrderDAO.get_orders_by_criteria(
            criteria=search_params,
            offset=offset,
            limit=per_page
        )
        
        # 构建结果字典，以兼容原代码
        result = {
            'orders': orders,
            'total_count': total_count,
            'total_pages': (total_count + per_page - 1) // per_page if total_count > 0 else 1,
            'current_page': page,
            'per_page': per_page,
            'status_counts': status_counts
        }
        
        # 检查是否是AJAX请求
        is_ajax = request.args.get('ajax') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        include_stats = request.args.get('include_stats') == '1'
        
        if is_ajax:
            # 准备AJAX响应
            html_content = render_template('orders/_order_table.html', 
                                      orders=result['orders'],
                                      current_page=result['current_page'],
                                      total_pages=result['total_pages'],
                                      total_count=result['total_count'],
                                      offset=(result['current_page'] - 1) * 10,
                                      per_page=10,
                                      search_params=search_params,
                                      field_names=field_names)
            
            # 构建响应数据
            response_data = {
                'html': html_content,
                'current_page': result['current_page'],
                'total_pages': result['total_pages']
            }
            
            # 如果需要包含统计数据
            if include_stats:
                response_data['stats'] = {
                    'waiting': status_counts.get('waiting', 0),
                    'in_progress': status_counts.get('in_progress', 0),
                    'completed': status_counts.get('completed', 0),
                    'total': result['total_count']
                }
            
            return jsonify(response_data)
        
        # 普通请求返回完整页面
        return render_template('orders/index.html', 
                           orders=result['orders'],
                           current_page=result['current_page'],
                           total_pages=result['total_pages'],
                           total_count=result['total_count'],
                           offset=(result['current_page'] - 1) * 10,
                           per_page=10,
                           search_params=search_params,
                           status_counts=status_counts,
                           field_names=field_names)
    except Exception as e:
        print(f"订单高级搜索错误: {str(e)}")
        traceback.print_exc()
        
        # 检查是否是AJAX请求
        is_ajax = request.args.get('ajax') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
        
        # 返回错误页面
        return render_template('orders/index.html', 
                           orders=[],
                           current_page=1,
                           total_pages=1,
                           total_count=0,
                           offset=0,
                           per_page=10,
                           search_params=search_params,
                           status_counts={'waiting': 0, 'in_progress': 0, 'completed': 0, 'cancelled': 0},
                           field_names=field_names,
                           error=str(e))

@orders_bp.route('/map')
def map_view():
    """订单地图视图"""
    return render_template('orders/map_view.html')

@orders_bp.route('/api/city_orders', methods=['GET'])
def get_city_orders():
    """获取指定城市的订单数据"""
    try:
        city = request.args.get('city', 'all')
        
        # 使用OrderDAO获取城市订单数据
        orders = OrderDAO.get_city_orders(city)
        
        return jsonify({
            'status': 'success',
            'message': f'获取到 {len(orders)} 个订单',
            'data': orders
        })
        
    except Exception as e:
        print(f"获取城市订单数据错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取订单数据失败: {str(e)}'
        }), 500

@orders_bp.route('/api/debug')
def api_debug():
    """简单的调试接口，返回纯文本"""
    return "订单API正常工作中"

@orders_bp.route('/api/all_orders')
def get_all_orders():
    """获取所有订单数据"""
    try:
        # 获取所有订单，不分页
        result = OrderDAO.get_all_orders(page=1, per_page=1000)
        
        # 检查数据是否正确
        if not result['orders']:
            return jsonify({"status": "success", "data": [], "message": "无订单数据"})
            
        return jsonify({"status": "success", "data": result['orders']})
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"错误详情: {error_traceback}")
        return jsonify({"status": "error", "message": str(e), "traceback": error_traceback}), 500

@orders_bp.route('/api/order_details/<int:order_id>')
def get_order_details(order_id):
    """获取单个订单的详细信息"""
    try:
        # 使用OrderDAO获取订单详情
        order = OrderDAO.get_order_by_id(order_id)
        
        if not order:
            return jsonify({"status": "error", "message": "订单不存在"}), 404
        
        return jsonify({"status": "success", "data": order})
    
    except AttributeError as e:
        # 处理方法不存在的情况
        error_message = str(e)
        print(f"方法调用错误: {error_message}")
        return jsonify({"status": "error", "message": "数据访问方法不存在或已更新", "error": error_message}), 500
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"订单详情获取错误: {error_traceback}")
        return jsonify({"status": "error", "message": str(e), "traceback": error_traceback}), 500

@orders_bp.route('/api/update_order_status', methods=['POST'])
def update_order_status():
    """更新订单状态"""
    try:
        data = request.json
        order_id = data.get('order_id')
        new_status = data.get('status')
        
        if not order_id or not new_status:
            return jsonify({"status": "error", "message": "缺少必要的参数"}), 400
        
        success = OrderDAO.update_order_status(order_id, new_status)
        
        if success:
            return jsonify({"status": "success", "message": f"订单状态已更新为 {new_status}"})
        else:
            return jsonify({"status": "error", "message": "订单状态更新失败"}), 500
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@orders_bp.route('/api/update_payment_status', methods=['POST'])
def update_payment_status():
    """更新订单支付状态"""
    try:
        # 注意: 简化版订单系统已移除payment_status
        return jsonify({"status": "error", "message": "此功能已在简化版中移除"}), 404
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@orders_bp.route('/api/add_rating', methods=['POST'])
def add_order_rating():
    """添加订单评价"""
    try:
        # 注意: 简化版订单系统已移除评价功能
        return jsonify({"status": "error", "message": "此功能已在简化版中移除"}), 404
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@orders_bp.route('/api/assign_vehicle', methods=['POST'])
def assign_vehicle():
    """分配车辆到订单"""
    try:
        data = request.json
        order_id = data.get('order_id')
        vehicle_id = data.get('vehicle_id')
        
        if not order_id or not vehicle_id:
            return jsonify({"status": "error", "message": "缺少必要的参数"}), 400
        
        # 1. 获取车辆信息，检查状态是否为空闲
        vehicle = VehicleDAO.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            return jsonify({"status": "error", "message": "车辆不存在"}), 404
        
        if vehicle['current_status'] != '空闲中':
            return jsonify({"status": "error", "message": f"车辆状态为 '{vehicle['current_status']}'，无法分配"}), 400
            
        # 获取订单详情，包括上车点和下车点坐标
        order = OrderDAO.get_order_by_id(order_id)
        if not order:
            return jsonify({"status": "error", "message": "订单不存在"}), 404
        
        # 检查订单状态是否为待分配
        if order['order_status'] != '待分配':
            return jsonify({"status": "error", "message": f"订单状态为 '{order['order_status']}'，只能对待分配状态的订单分配车辆"}), 400
            
        # 检查订单是否有坐标
        if not order.get('pickup_location_x') or not order.get('pickup_location_y') or not order.get('dropoff_location_x') or not order.get('dropoff_location_y'):
            return jsonify({"status": "error", "message": "订单缺少上车或下车坐标"}), 400
        
        # 2. 分配车辆到订单并更新订单状态
        order_updated = OrderDAO.assign_vehicle(order_id, vehicle_id)
        if not order_updated:
            return jsonify({"status": "error", "message": "订单更新失败"}), 500
        
        # 3. 更新车辆状态为运行中
        vehicle_updated = VehicleDAO.update_vehicle_status(vehicle_id, "运行中")
        if not vehicle_updated:
            return jsonify({"status": "error", "message": "车辆状态更新失败"}), 500
            
        # 4. 启动车辆移动模拟线程
        start_vehicle_movement(
            vehicle_id=vehicle['vehicle_id'],
            order_id=order['order_id'],
            vehicle_x=float(vehicle['current_location_x']),
            vehicle_y=float(vehicle['current_location_y']),
            pickup_x=float(order['pickup_location_x']),
            pickup_y=float(order['pickup_location_y']),
            dropoff_x=float(order['dropoff_location_x']),
            dropoff_y=float(order['dropoff_location_y']),
            pickup_name=order['pickup_location'],
            dropoff_name=order['dropoff_location']
        )
        
        return jsonify({
            "status": "success", 
            "message": f"车辆 {vehicle['plate_number']} 已分配到订单，正在前往上车点"
        })
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"分配车辆错误: {error_traceback}")
        return jsonify({"status": "error", "message": str(e), "traceback": error_traceback}), 500

@orders_bp.route('/api/vehicle_position/<int:vehicle_id>', methods=['GET'])
def get_vehicle_position(vehicle_id):
    """获取车辆当前位置"""
    try:
        vehicle = VehicleDAO.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            return jsonify({"status": "error", "message": "车辆不存在"}), 404
            
        # 返回车辆位置信息
        return jsonify({
            "status": "success",
            "data": {
                "vehicle_id": vehicle['vehicle_id'],
                "location_x": vehicle['current_location_x'],
                "location_y": vehicle['current_location_y'],
                "location_name": vehicle['current_location_name'],
                "status": vehicle['current_status']
            }
        })
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"获取车辆位置错误: {error_traceback}")
        return jsonify({"status": "error", "message": str(e), "traceback": error_traceback}), 500

@orders_bp.route('/api/vehicle_movement_status/<int:vehicle_id>', methods=['GET'])
def get_vehicle_movement_status(vehicle_id):
    """获取车辆移动状态"""
    vehicle_id_str = str(vehicle_id)
    
    is_moving = vehicle_id_str in vehicle_movement_threads and vehicle_movement_threads[vehicle_id_str].is_alive()
    
    return jsonify({
        "status": "success",
        "data": {
            "vehicle_id": vehicle_id,
            "is_moving": is_moving
        }
    })

def start_vehicle_movement(vehicle_id, order_id, vehicle_x, vehicle_y, pickup_x, pickup_y, 
                           dropoff_x, dropoff_y, pickup_name, dropoff_name):
    """启动车辆移动模拟线程"""
    # 停止之前的线程（如果存在）
    vehicle_id_str = str(vehicle_id)
    if vehicle_id_str in vehicle_movement_threads and vehicle_movement_threads[vehicle_id_str].is_alive():
        # 设置线程停止标志
        print(f"停止车辆 {vehicle_id} 的之前运行的线程")
        vehicle_movement_threads[vehicle_id_str].stop = True
        # 等待线程结束
        vehicle_movement_threads[vehicle_id_str].join(2)
        
        # 如果线程还在运行或异常结束，确保将车辆状态重置
        if vehicle_movement_threads[vehicle_id_str].is_alive():
            print(f"线程未能在规定时间内结束，将强制结束并重置车辆状态")
            try:
                # 获取车辆当前电量
                vehicle = VehicleDAO.get_vehicle_by_id(vehicle_id)
                if vehicle:
                    current_battery = vehicle['battery_level']
                    new_status = "等待充电" if current_battery < 40 else "空闲中"
                    VehicleDAO.update_vehicle_status(vehicle_id, new_status)
                    print(f"线程重置：已将车辆 {vehicle_id} 状态设为 {new_status} (电量: {current_battery}%)")
                else:
                    # 如果无法获取车辆信息，默认设为空闲
                    VehicleDAO.update_vehicle_status(vehicle_id, "空闲中")
                    print(f"线程重置：无法获取车辆电量，已将车辆 {vehicle_id} 状态设为空闲")
            except Exception as e:
                print(f"重置车辆状态时出错: {e}")
    
    # 创建并启动新线程
    thread = VehicleMovementThread(
        vehicle_id=vehicle_id,
        order_id=order_id,
        vehicle_x=vehicle_x,
        vehicle_y=vehicle_y,
        pickup_x=pickup_x,
        pickup_y=pickup_y,
        dropoff_x=dropoff_x,
        dropoff_y=dropoff_y,
        pickup_name=pickup_name,
        dropoff_name=dropoff_name
    )
    thread.daemon = True  # 设置为守护线程，主线程结束时此线程也会结束
    thread.start()
    
    # 保存线程引用
    vehicle_movement_threads[vehicle_id_str] = thread


class VehicleMovementThread(threading.Thread):
    """车辆移动模拟线程"""
    def __init__(self, vehicle_id, order_id, vehicle_x, vehicle_y, pickup_x, pickup_y, 
                 dropoff_x, dropoff_y, pickup_name, dropoff_name):
        """初始化车辆移动线程"""
        super().__init__()
        self.daemon = True
        
        self.vehicle_id = vehicle_id
        self.order_id = order_id
        self.vehicle_x = float(vehicle_x)
        self.vehicle_y = float(vehicle_y)
        self.pickup_x = float(pickup_x)
        self.pickup_y = float(pickup_y)
        self.dropoff_x = float(dropoff_x)
        self.dropoff_y = float(dropoff_y)
        self.pickup_name = pickup_name
        self.dropoff_name = dropoff_name
        
        # 获取车辆所有参数和计算速度
        actual_speed, self.vehicle_model, speed_coefficient = calculate_vehicle_speed(vehicle_id)
        self.vehicle_params = get_vehicle_parameters(vehicle_id)[1]
        
        # 设置车辆速度
        self.speed = actual_speed
        
        # 输出原始车型名称和修正后的名称
        if self.vehicle_model:
            model_key = self.vehicle_model.replace('-', '_')
        
        
        self.stop = False
        self.phase = "TO_PICKUP"  # 初始阶段：前往上车点
        
        # 检查必要的全局参数是否已从数据库加载
        required_params = [
            "POSITION_MOVEMENT_INTERVAL", "BATTERY_UPDATE_INTERVAL", 
            "POSITION_UPDATE_INTERVAL", "RUNNING_BATTERY_UPDATE_INTERVAL",
            "BATTERY_CONSUMPTION_RATE", "PICKUP_WAITING_TIME"
        ]
        
        # 检查全局参数
        from app.config.vehicle_params import _PARAMS
        missing_params = []
        for param in required_params:
            if param not in _PARAMS:
                missing_params.append(param)
                
        if missing_params:
            # 如果有缺失参数，尝试重新加载所有参数
            print(f"警告: 车辆移动线程缺少必要参数: {', '.join(missing_params)}，尝试重新加载参数...")
            from app.config.vehicle_params import refresh_params
            try:
                refresh_params()
                print("参数已刷新")
            except Exception as e:
                error_msg = f"无法从数据库加载必要的全局参数: {str(e)}"
                print(f"错误: {error_msg}")
                raise ValueError(error_msg)
            
            # 再次检查
            for param in missing_params:
                from app.config import vehicle_params
                if getattr(vehicle_params, param) is None:
                    error_msg = f"参数 {param} 在数据库中不存在或无法加载"
                    print(f"错误: {error_msg}")
                    raise ValueError(error_msg)

    def run(self):
        """线程运行方法"""
        try:
            # 解决参数为None的问题：在每个线程中重新获取最新参数
            # 直接使用get_param而不是导入全局变量，避免受到模块重新加载的影响
            from app.config.vehicle_params import get_param
            
            # 创建一个局部参数字典，避免使用可能为None的全局变量
            params = {
                'PICKUP_WAITING_TIME': None,
                'LOW_BATTERY_THRESHOLD': None,
                'BATTERY_CONSUMPTION_RATE': None,
                'CHARGING_RATE': None,
                'POSITION_MOVEMENT_INTERVAL': None,
                'BATTERY_UPDATE_INTERVAL': None,
                'POSITION_UPDATE_INTERVAL': None,
                'RUNNING_BATTERY_UPDATE_INTERVAL': None
            }
            
            # 从数据库获取所有需要的参数
            for param_name in params.keys():
                try:
                    params[param_name] = get_param(param_name)
                except Exception as e:
                    print(f"车辆 {self.vehicle_id} 加载参数 {param_name} 失败: {e}")
                    if param_name == 'PICKUP_WAITING_TIME':
                        params[param_name] = 1  # 等待上车时间默认1秒
                    elif param_name == 'LOW_BATTERY_THRESHOLD':
                        params[param_name] = 20  # 低电量默认20%
                    else:
                        # 其他参数使用合适的默认值
                        default_values = {
                            'BATTERY_CONSUMPTION_RATE': 0.1,
                            'CHARGING_RATE': 0.5,
                            'POSITION_MOVEMENT_INTERVAL': 0.2,
                            'BATTERY_UPDATE_INTERVAL': 10,
                            'POSITION_UPDATE_INTERVAL': 5,
                            'RUNNING_BATTERY_UPDATE_INTERVAL': 15
                        }
                        params[param_name] = default_values.get(param_name, 1)
                    
                    print(f"车辆 {self.vehicle_id} 使用默认值 {param_name}: {params[param_name]}")

            # 获取车辆当前电量
            vehicle = VehicleDAO.get_vehicle_by_id(self.vehicle_id)
            if not vehicle:
                print(f"找不到车辆 {self.vehicle_id}，无法模拟移动")
                return
                
            current_battery = vehicle['battery_level']
    
            
            # 第一阶段：前往上车点
            self.move_to_target(
                target_x=self.pickup_x,
                target_y=self.pickup_y,
                target_name=self.pickup_name,
                current_battery=current_battery
            )
            
            if self.stop:
                return
            
            # 完成上车，更新订单状态
            # 模拟上车等待时间
 
            time.sleep(params['PICKUP_WAITING_TIME'])
            
            # 获取最新电量
            vehicle = VehicleDAO.get_vehicle_by_id(self.vehicle_id)
            current_battery = vehicle['battery_level']
            
            if self.stop:
                return
            
            # 第二阶段：前往下车点
            self.phase = "TO_DROPOFF"

            
            self.move_to_target(
                target_x=self.dropoff_x,
                target_y=self.dropoff_y,
                target_name=self.dropoff_name,
                current_battery=current_battery
            )
            
            if self.stop:
                return
            

            
            try:
                # 确保最终位置更新为终点
                self.vehicle_x = self.dropoff_x
                self.vehicle_y = self.dropoff_y
                VehicleDAO.update_vehicle_location_coordinates(
                    self.vehicle_id, self.dropoff_x, self.dropoff_y, self.dropoff_name
                )
                
                # 更新订单状态为已结束，并记录到达时间
                now = datetime.now()
                update_success = OrderDAO.update_order_completion(self.order_id, now)
                
                # 获取车辆当前电量
                vehicle = VehicleDAO.get_vehicle_by_id(self.vehicle_id)
                if not vehicle:
                    print(f"找不到车辆 {self.vehicle_id}，无法更新状态")
                    return
                
                current_battery = vehicle['battery_level']
                
                # 根据电量决定车辆状态，使用全局配置的电量阈值
                new_status = "空闲中"  # 默认设置为空闲中
                if current_battery < params['LOW_BATTERY_THRESHOLD']:
                    # 尝试查找合适的充电站
                    try:
                        nearest_station = VehicleDAO.find_nearest_available_charging_station(
                            self.vehicle_x, self.vehicle_y, vehicle['current_city']
                        )
                        
                        if nearest_station:
                            # 找到合适的充电站，状态设为"前往充电"
                            new_status = "前往充电"
                        
                            # 修改车辆位置名称，表示正在前往充电站
                            station_location_name = f"前往充电站 {nearest_station['station_code']}"
                            VehicleDAO.update_vehicle_location_name(self.vehicle_id, station_location_name)
                            
                            # 更新充电站当前车辆数量（在车辆前往充电时就计入充电站负荷）
                            try:
                                # 使用ChargingStationDAO更新充电站车辆数量
                                success, old_count, new_count, max_capacity = ChargingStationDAO.update_station_vehicle_count(
                                    nearest_station['station_code'], vehicle['current_city'], 1
                                )
                                
                                if success:
                                   
                                    # 只有成功预分配充电站容量后才启动移动线程
                                    # 创建前往充电站的任务
                                    charging_thread = ChargingStationMovementThread(
                                        vehicle_id=self.vehicle_id,
                                        current_x=self.vehicle_x,
                                        current_y=self.vehicle_y,
                                        station_x=nearest_station['location_x'],
                                        station_y=nearest_station['location_y'],
                                        station_code=nearest_station['station_code'],
                                        current_battery=current_battery,
                                        city_code=vehicle['current_city']
                                    )
                                    charging_thread.daemon = True
                                    charging_thread.start()
                                    
                                else:
                                    # 容量不足，状态设为"等待充电"
                                    new_status = "等待充电"
                                    print(f"充电站 {nearest_station['station_code']} 无法容纳更多车辆，当前容量: {old_count}/{max_capacity}")
                                    print(f"车辆 {self.vehicle_id} 将保持等待充电状态")
                            except Exception as e:
                                # 更新容量失败，状态设为"等待充电"
                                new_status = "等待充电"
                                print(f"更新充电站车辆预分配数量出错: {e}")
                        else:
                            # 没有找到合适的充电站，状态设为"等待充电"
                            new_status = "等待充电"
                    except Exception as station_error:
                        # 查找充电站出错，状态设为"等待充电"
                        new_status = "等待充电"
                        print(f"查找充电站出错，设置为等待充电状态")
                        print(f"错误详情: {station_error}")
                
                # 更新车辆状态
                status_update = VehicleDAO.update_vehicle_status(self.vehicle_id, new_status)

                
            except Exception as inner_e:
                print(f"订单完成阶段出错: {inner_e}")
                traceback.print_exc()
                # 发生异常时，尝试检查电量并设置合适的状态
                try:
                    vehicle = VehicleDAO.get_vehicle_by_id(self.vehicle_id)
                    if vehicle:
                        current_battery = vehicle['battery_level']
                        if current_battery < params['LOW_BATTERY_THRESHOLD']:
                            # 尝试查找合适的充电站
                            try:
                                nearest_station = VehicleDAO.find_nearest_available_charging_station(
                                    self.vehicle_x, self.vehicle_y, vehicle['current_city']
                                )
                                
                                if nearest_station:
                                    # 找到合适的充电站，状态设为"前往充电"
                                    new_status = "前往充电"
                                    print(f"异常处理：车辆等待充电，找到可用充电站，状态设为前往充电")
                                    
                                    # 修改车辆位置名称，表示正在前往充电站
                                    station_location_name = f"前往充电站 {nearest_station['station_code']}"
                                    VehicleDAO.update_vehicle_location_name(self.vehicle_id, station_location_name)
                                    
                                    # 更新充电站当前车辆数量（在车辆前往充电时就计入充电站负荷）
                                    try:
                                        # 使用ChargingStationDAO更新充电站车辆数量
                                        success, old_count, new_count, max_capacity = ChargingStationDAO.update_station_vehicle_count(
                                            nearest_station['station_code'], vehicle['current_city'], 1
                                        )
                                        
                                        if success:
                                          
                                            # 只有成功预分配充电站容量后才启动移动线程
                                            # 创建前往充电站的任务
                                            charging_thread = ChargingStationMovementThread(
                                                vehicle_id=self.vehicle_id,
                                                current_x=self.vehicle_x,
                                                current_y=self.vehicle_y,
                                                station_x=nearest_station['location_x'],
                                                station_y=nearest_station['location_y'],
                                                station_code=nearest_station['station_code'],
                                                current_battery=current_battery,
                                                city_code=vehicle['current_city']
                                            )
                                            charging_thread.daemon = True
                                            charging_thread.start()
                                            
                                        else:
                                            # 容量不足，状态设为"等待充电"
                                            new_status = "等待充电"
                                            print(f"充电站 {nearest_station['station_code']} 无法容纳更多车辆，当前容量: {old_count}/{max_capacity}")
                                            print(f"车辆 {self.vehicle_id} 将保持等待充电状态")
                                    except Exception as e:
                                        # 更新容量失败，状态设为"等待充电"
                                        new_status = "等待充电"
                                        print(f"更新充电站车辆预分配数量出错: {e}")
                                else:
                                    # 没有找到合适的充电站，状态设为"等待充电"
                                    new_status = "等待充电"
                            except Exception as station_error:
                                # 查找充电站出错，状态设为"等待充电"
                                new_status = "等待充电"
                                print(f"异常处理：查找充电站出错，设置为等待充电状态")
                                print(f"错误详情: {station_error}")
                            VehicleDAO.update_vehicle_status(self.vehicle_id, new_status)
                            print(f"异常处理：已将车辆 {self.vehicle_id} 状态设为 {new_status} (电量: {current_battery}%)")
                        else:
                            new_status = "空闲中"
                            VehicleDAO.update_vehicle_status(self.vehicle_id, new_status)
                            print(f"异常处理：已将车辆 {self.vehicle_id} 状态设为 {new_status} (电量: {current_battery}%)")
                    else:
                        # 如果无法获取车辆信息，默认设为空闲
                        VehicleDAO.update_vehicle_status(self.vehicle_id, "空闲中")
                        print(f"异常处理：无法获取车辆电量，已将车辆 {self.vehicle_id} 状态设为空闲")
                except Exception as status_error:
                    print(f"设置车辆状态出错: {status_error}")
            
        except Exception as e:
            print(f"车辆 {self.vehicle_id} 移动过程中出错: {e}")
            traceback.print_exc()
    
    def move_to_target(self, target_x, target_y, target_name, current_battery):
        """移动到目标位置"""
        # 从run方法继承参数字典，如果不存在则创建一个新的
        if not hasattr(self, 'params'):
            from app.config.vehicle_params import get_param
            self.params = {
                'POSITION_MOVEMENT_INTERVAL': get_param('POSITION_MOVEMENT_INTERVAL', 0.2),
                'BATTERY_UPDATE_INTERVAL': get_param('BATTERY_UPDATE_INTERVAL', 10),
                'POSITION_UPDATE_INTERVAL': get_param('POSITION_UPDATE_INTERVAL', 5),
                'RUNNING_BATTERY_UPDATE_INTERVAL': get_param('RUNNING_BATTERY_UPDATE_INTERVAL', 15),
                'BATTERY_CONSUMPTION_RATE': get_param('BATTERY_CONSUMPTION_RATE', 0.1)
            }

        # 如果初始电量已为0，直接返回并更新状态
        if current_battery <= 0:
            try:
                # 更新车辆电量为0并让系统自动处理状态转换为电量不足
                VehicleDAO.update_vehicle_battery(self.vehicle_id, 0)
                print(f"车辆 {self.vehicle_id} 初始电量已为0，无法开始移动")
                return
            except Exception as e:
                print(f"更新零电量车辆状态出错: {e}")
                return
                
        # 计算总距离
        dx = target_x - self.vehicle_x
        dy = target_y - self.vehicle_y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < 1:
            # 已经非常接近目标，直接到达
            self.vehicle_x = target_x
            self.vehicle_y = target_y
            # 同时更新位置和电量
            try:
                VehicleDAO.update_vehicle_location_and_battery(
                    self.vehicle_id, target_x, target_y, target_name, current_battery
                )
                print(f"车辆 {self.vehicle_id} 已接近目标点，已直接到达")
            except Exception as e:
                print(f"更新车辆位置时出错: {e}")
                # 如果更新电量和位置同时失败，尝试只更新位置
                try:
                    VehicleDAO.update_vehicle_location_coordinates(
                        self.vehicle_id, target_x, target_y, target_name
                    )
                except:
                    pass
            return
        
        # 计算移动所需总时间（秒）
        total_time = distance / self.speed
        
        # 分解为多个步骤移动
        position_movement_interval = self.params['POSITION_MOVEMENT_INTERVAL']  # 使用局部参数
        movement_steps = max(int(total_time / position_movement_interval), 1)  # 使用位置移动频率
        movement_step_x = dx / movement_steps
        movement_step_y = dy / movement_steps
        
        # 用于追踪数据库更新
        position_update_counter = 0
        battery_update_counter = 0
        
        for i in range(movement_steps):
            if self.stop:
                break
                
            # 更新车辆位置
            self.vehicle_x += movement_step_x
            self.vehicle_y += movement_step_y
            
            # 计算当前位置名称
            if i < movement_steps - 1:
                # 移动中
                if self.phase == "TO_PICKUP":
                    location_name = f"前往上车点: {target_name}"
                else:
                    location_name = f"前往下车点: {target_name}"
            else:
                # 到达目标
                location_name = target_name
            
            # 更新车辆电量 - 使用车型特定的能耗系数
            energy_consumption = self.params['BATTERY_CONSUMPTION_RATE'] * self.params['BATTERY_UPDATE_INTERVAL'] * self.vehicle_params['energy_consumption_coefficient']
            current_battery = max(0, current_battery - energy_consumption)
            
            # 检查电量是否为0，如果是，则直接转为电量不足状态并停止移动
            if current_battery <= 0:
                try:
                    # 更新车辆位置、电量和状态
                    VehicleDAO.update_vehicle_location_and_battery(
                        self.vehicle_id, self.vehicle_x, self.vehicle_y, location_name, 0
                    )
                    # 状态已在update_vehicle_location_and_battery中通过check_and_update_zero_battery更新
                    print(f"车辆 {self.vehicle_id} 电量耗尽，停止移动")
                    return  # 直接返回，不再继续移动
                except Exception as e:
                    print(f"车辆电量耗尽更新状态时出错: {e}")
            
            # 检查是否需要更新数据库中的位置和电量
            position_update_counter += position_movement_interval
            battery_update_counter += position_movement_interval
            
            if position_update_counter >= self.params['POSITION_UPDATE_INTERVAL']:
                position_update_counter = 0
                # 需要更新位置
                
                if battery_update_counter >= self.params['RUNNING_BATTERY_UPDATE_INTERVAL']:
                    battery_update_counter = 0
                    # 需要同时更新位置和电量
                    try:
                        # 更新数据库中的车辆位置和电量
                        VehicleDAO.update_vehicle_location_and_battery(
                            self.vehicle_id, 
                            self.vehicle_x, 
                            self.vehicle_y, 
                            location_name, 
                            current_battery
                        )
                    except Exception as e:
                        print(f"更新车辆位置和电量时出错: {e}")
                else:
                    # 只需要更新位置
                    try:
                        VehicleDAO.update_vehicle_location_coordinates(
                            self.vehicle_id, 
                            self.vehicle_x, 
                            self.vehicle_y, 
                            location_name
                        )
                    except Exception as e:
                        print(f"更新车辆位置时出错: {e}")
            
            # 等待
            time.sleep(position_movement_interval)
        
        # 确保最后一步到达目标位置
        if not self.stop and (abs(self.vehicle_x - target_x) > 0.1 or abs(self.vehicle_y - target_y) > 0.1):
            self.vehicle_x = target_x
            self.vehicle_y = target_y
            try:
                VehicleDAO.update_vehicle_location_and_battery(
                    self.vehicle_id, target_x, target_y, target_name, current_battery
                )
            except Exception as e:
                print(f"最终更新车辆位置和电量时出错: {e}")
                # 如果更新电量和位置同时失败，尝试只更新位置
                try:
                    VehicleDAO.update_vehicle_location_coordinates(
                        self.vehicle_id, target_x, target_y, target_name
                    )
                except:
                    pass

@orders_bp.route('/api/bulk_add_orders', methods=['POST'])
def bulk_add_orders():
    """
    批量添加随机订单API
    参数:
        city_code: 城市代码
        order_count: 订单数量
    返回:
        成功: {"status": "success", "message": "成功添加n个订单", "count": n}
        失败: {"status": "error", "message": "错误信息"}
    """
    try:
        # 获取请求数据
        data = request.json
        city_code = data.get('city')
        order_count = int(data.get('order_count', 10))
        update_last_login = data.get('update_last_login', False)  # 获取是否需要更新最后登录时间

        # 验证参数
        if not city_code:
            return jsonify({"status": "error", "message": "请选择城市"})

        if not order_count or order_count < 1:
            return jsonify({"status": "error", "message": "订单数量必须大于0"})

        if order_count > 1000:
            return jsonify({"status": "error", "message": "一次最多添加1000条订单"})

        # 调用OrderDAO创建批量订单
        try:
            # 调用OrderDAO创建批量订单
            result = OrderDAO.bulk_create_orders(city_code, order_count)
            success_count = result["success_count"]
            user_ids = result["user_ids"]
            
            # 如果需要更新最后登录时间，并且有用户ID列表
            if update_last_login and user_ids:
                from app.dao.user_dao import UserDAO
                # 更新所有关联用户的最后登录时间
                updated_users = 0
                for user_id in user_ids:
                    if UserDAO.update_last_login(user_id):
                        updated_users += 1
                
                # 返回成功信息，包括更新的用户数量
                return jsonify({
                    "status": "success",
                    "message": f"成功添加{success_count}个订单，并更新{updated_users}个用户的最后登录时间", 
                    "count": success_count,
                    "updated_users": updated_users
                })
            else:
                # 返回成功信息
                return jsonify({
                    "status": "success",
                    "message": f"成功添加{success_count}个订单", 
                    "count": success_count
                })
        except Exception as e:
            # 捕获特定的错误并提供友好的错误消息
            if "没有可用的用户" in str(e):
                return jsonify({"status": "error", "message": str(e)})
            else:
                print(f"批量添加订单失败: {str(e)}")
                traceback.print_exc()
                return jsonify({"status": "error", "message": f"添加订单失败: {str(e)}"})
    
    except Exception as e:
        print(f"批量添加订单失败: {str(e)}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"添加订单失败: {str(e)}"})

@orders_bp.route('/api/auto_assign_vehicles', methods=['POST'])
def auto_assign_vehicles():
    """一键分配车辆到订单 - 使用算法模块的实现"""
    try:
        data = request.json
        order_ids = data.get('order_ids', [])
        
        if not order_ids:
            return jsonify({"status": "error", "message": "未提供订单ID列表"}), 400
        
        # 调用算法模块的分配算法
        result = OrderAssignmentAlgorithm.assign_orders(order_ids)
        
        # 如果分配成功并有成功分配的订单，则启动车辆移动模拟
        if result['status'] == 'success' and result['data']['successful']:
            for assignment in result['data']['successful']:
                # 启动对应的车辆移动线程
                # 获取车辆当前位置和订单详情
                try:
                    vehicle_id = assignment['vehicle_id']
                    order_id = assignment['order_id']
                    
                    # 获取详细订单信息和车辆信息
                    order_detail = OrderDAO.get_order_by_id(order_id)
                    vehicle = VehicleDAO.get_vehicle_by_id(vehicle_id)
                    
                    if order_detail and vehicle:
                        # 启动车辆移动模拟线程
                        start_vehicle_movement(
                            vehicle_id=vehicle_id,
                            order_id=order_id,
                            vehicle_x=float(vehicle['current_location_x']),
                            vehicle_y=float(vehicle['current_location_y']),
                            pickup_x=float(order_detail['pickup_location_x']),
                            pickup_y=float(order_detail['pickup_location_y']),
                            dropoff_x=float(order_detail['dropoff_location_x']),
                            dropoff_y=float(order_detail['dropoff_location_y']),
                            pickup_name=order_detail['pickup_location'],
                            dropoff_name=order_detail['dropoff_location']
                        )
                except Exception as e:
                    print(f"启动车辆移动线程失败: {str(e)}")
                    traceback.print_exc()
        
        return jsonify(result)
        
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"一键分配车辆错误: {error_traceback}")
        return jsonify({"status": "error", "message": str(e), "traceback": error_traceback}), 500

@orders_bp.route('/api/get_waiting_order_ids', methods=['POST'])
def get_waiting_order_ids():
    """获取所有符合搜索条件的待分配订单ID"""
    try:
        data = request.json
        search_params = data.get('search_params', {})
        
        # 构建查询条件
        criteria = {}
        
        # 将前端传来的搜索参数转换为数据库查询条件
        for key, value in search_params.items():
            if value:  # 只保留有值的参数
                criteria[key] = value
        
        # 强制设置订单状态为待分配
        criteria['order_status'] = '待分配'
        
        # 调用DAO获取所有符合条件的订单ID
        order_ids = OrderDAO.get_waiting_order_ids(criteria)
        
        return jsonify({
            "status": "success",
            "message": f"找到 {len(order_ids)} 个待分配订单",
            "data": {
                "order_ids": order_ids
            }
        })
        
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"获取待分配订单ID错误: {error_traceback}")
        return jsonify({"status": "error", "message": str(e), "traceback": error_traceback}), 500 

class ChargingStationMovementThread(threading.Thread):
    """模拟车辆前往充电站的线程"""
    
    def __init__(self, vehicle_id, current_x, current_y, station_x, station_y, 
                 station_code, current_battery, city_code, speed=None):
        """初始化充电站移动线程"""
        super().__init__()
        self.daemon = True
        
        self.vehicle_id = vehicle_id
        # 设置当前位置坐标为实例属性
        self.current_x = float(current_x)
        self.current_y = float(current_y)
        self.station_x = float(station_x)
        self.station_y = float(station_y)
        self.station_code = station_code
        self.current_battery = float(current_battery)
        self.city_code = city_code
        self.speed = speed
        self.stop = False
        
        # 获取车辆所有参数和计算速度
        actual_speed, self.vehicle_model, speed_coefficient = calculate_vehicle_speed(vehicle_id)
        # 注意：此处只获取到了车辆的基本信息
        # capacity_coefficient 需要在run方法中加载
        _, self.vehicle_params = get_vehicle_parameters(vehicle_id)
        
        # 如果没有传入速度，则使用计算得到的实际速度
        if self.speed is None:
            self.speed = actual_speed
        
        # 确保self.vehicle_x和self.vehicle_y也可用（兼容性）
        self.vehicle_x = self.current_x
        self.vehicle_y = self.current_y
    
    def run(self):
        """线程运行方法"""
        try:
            # 类似VehicleMovementThread，创建本地参数字典
            from app.config.vehicle_params import get_param
            
            # 为充电站移动线程创建局部参数字典
            params = {
                'POSITION_MOVEMENT_INTERVAL': None,
                'BATTERY_UPDATE_INTERVAL': None,
                'POSITION_UPDATE_INTERVAL': None,
                'LOW_BATTERY_THRESHOLD': None,
                'CHARGING_RATE': None
            }
            
            # 从数据库获取所有需要的参数
            for param_name in params.keys():
                try:
                    params[param_name] = get_param(param_name)
                except Exception as e:
                     # 使用合适的默认值
                    default_values = {
                        'POSITION_MOVEMENT_INTERVAL': 0.2,
                        'BATTERY_UPDATE_INTERVAL': 10,
                        'POSITION_UPDATE_INTERVAL': 5,
                        'LOW_BATTERY_THRESHOLD': 20,
                        'CHARGING_RATE': 0.5
                    }
                    params[param_name] = default_values.get(param_name, 1)
            
            # 加载车辆电池容量系数
            vehicle_info = VehicleDAO.get_vehicle_by_id(self.vehicle_id)
            if vehicle_info and 'model' in vehicle_info:
                # 重新获取车辆参数，确保获取到完整的数据
                model_key = vehicle_info['model'].replace('-', '_')
                capacity_param = f"{model_key}_CAPACITY"
                try:
                    self.capacity_coefficient = get_param(capacity_param)
                except Exception as e:
                    print(f"无法加载车辆 {self.vehicle_id} ({self.vehicle_model}) 的电池容量系数: {e}")
                    # 不设置默认值，而是抛出异常
                    raise ValueError(f"无法加载电池容量系数: {e}")
            else:
                print(f"无法获取车辆 {self.vehicle_id} 的型号信息")
                raise ValueError(f"无法获取车辆 {self.vehicle_id} 的型号信息")
                
            # 将参数字典保存到实例中，以便后续方法使用
            self.params = params
                    
            # 设置线程名称以便调试
            thread_name = f"充电站线程-{self.vehicle_id}-{self.station_code}"
            
            # 获取车辆当前电量
            if not vehicle_info:
                print(f"{thread_name} 找不到车辆 {self.vehicle_id} 的信息，终止移动线程")
                return
            
            # 设置车辆状态为前往充电
            try:
                VehicleDAO.update_vehicle_status(self.vehicle_id, "前往充电")
            except Exception as e:
                print(f"{thread_name} 更新车辆状态时出错: {e}")

            # 计算总距离
            dx = self.station_x - self.current_x
            dy = self.station_y - self.current_y
            distance = math.sqrt(dx**2 + dy**2)
            
            # 使用传入的速度或者默认速度
            if self.speed is None:
                vehicle_info = VehicleDAO.get_vehicle_by_id(self.vehicle_id)
                if vehicle_info and 'model' in vehicle_info:
                    # 使用车型特定的速度
                    vehicle_model = vehicle_info['model']
                    _, vehicle_params_dict = get_vehicle_parameters(self.vehicle_id)
                    self.speed = get_param('VEHICLE_MOVEMENT_SPEED', 5) * vehicle_params_dict['speed_coefficient']
                    print(f"{thread_name} 使用车型 {vehicle_model} 的速度: {self.speed}")
                else:
                    # 使用默认速度
                    self.speed = get_param('VEHICLE_MOVEMENT_SPEED', 5)
                    print(f"{thread_name} 使用默认速度: {self.speed}")
            
            # 计算移动所需总时间（秒）
            if self.speed <= 0:
                print(f"{thread_name} 速度为0或负值，无法移动")
                VehicleDAO.update_vehicle_status(self.vehicle_id, "等待充电")
                return
                
            total_time = distance / self.speed
            
            # 分解为多个步骤移动
            position_movement_interval = params['POSITION_MOVEMENT_INTERVAL']
            movement_steps = max(int(total_time / position_movement_interval), 1)
            movement_step_x = dx / movement_steps
            movement_step_y = dy / movement_steps
            
            # 用于追踪数据库更新
            position_update_counter = 0
            battery_update_counter = 0
            
            # 初始化位置名称
            location_name = f"前往充电站 {self.station_code}"
            
            # 车辆从当前位置移动到充电站
            for i in range(movement_steps):
                if self.stop:
                    # 如果收到停止信号，释放充电站预分配的容量
                    print(f"{thread_name} 收到停止信号，释放充电站预分配容量")
                    self.update_charging_station_count(-1)
                    VehicleDAO.update_vehicle_status(self.vehicle_id, "等待充电")
                    return
                
                # 更新位置
                self.current_x += movement_step_x
                self.current_y += movement_step_y
                
                # 同时更新vehicle_x和vehicle_y以保持兼容性
                self.vehicle_x = self.current_x
                self.vehicle_y = self.current_y
                
                # 更新电量 - 消耗电量
                self.current_battery = max(0, self.current_battery - params['BATTERY_UPDATE_INTERVAL'] * 0.1)
                
                # 检查电量是否为0
                if self.current_battery <= 0:
                    # 电量耗尽，更新状态后通知下一个等待车辆
                    try:
                        # 更新车辆电量为0并标记为电量耗尽状态
                        VehicleDAO.update_vehicle_battery(self.vehicle_id, 0)
                        VehicleDAO.update_vehicle_status(self.vehicle_id, "电量耗尽")
                        
                        # 更新车辆当前位置
                        location_name = f"前往充电站 {self.station_code} (电量耗尽)"
                        VehicleDAO.update_vehicle_location_coordinates(
                            self.vehicle_id, self.current_x, self.current_y, location_name
                        )
                        
                        # 释放充电站预分配容量
                        self.update_charging_station_count(-1)
                        
                        print(f"{thread_name} 车辆电量耗尽，无法到达充电站")
                        
                        # 通知下一个等待充电的车辆
                        if self.city_code:
                            waiting_vehicle = VehicleDAO.find_vehicle_by_status_and_city("等待充电", self.city_code)
                            waiting_vehicle_id = waiting_vehicle.get('vehicle_id') if waiting_vehicle else None
                            
                            if waiting_vehicle_id:
                                waiting_vehicle_info = VehicleDAO.get_vehicle_by_id(waiting_vehicle_id)
                                if waiting_vehicle_info:
                                    print(f"通知等待充电的车辆 {waiting_vehicle_id} 前往充电站")
                                    
                                    # 更新等待车辆状态
                                    VehicleDAO.update_vehicle_status(waiting_vehicle_id, "前往充电")
                                    
                                    # 创建新的充电站移动线程
                                    movement_thread = ChargingStationMovementThread(
                                        vehicle_id=waiting_vehicle_id,
                                        current_x=waiting_vehicle_info.get('current_location_x'),
                                        current_y=waiting_vehicle_info.get('current_location_y'),
                                        station_x=self.station_x,
                                        station_y=self.station_y,
                                        station_code=self.station_code,
                                        current_battery=waiting_vehicle_info.get('battery_level'),
                                        city_code=self.city_code
                                        # 不要传递speed参数，让线程自己计算基于车型的速度
                                    )
                                    movement_thread.daemon = True
                                    movement_thread.start()
                                    print(f"已成功通知车辆 {waiting_vehicle_id} 前往充电站 {self.station_code}")
                                else:
                                    print(f"无法获取等待充电车辆 {waiting_vehicle_id} 的详细信息")
                            else:
                                print(f"没有找到等待充电的车辆")
                        else:
                            print("缺少城市代码，无法通知等待充电的车辆")
                    except Exception as e:
                        print(f"{thread_name} 更新电量耗尽状态或通知等待充电车辆出错: {e}")
                        traceback.print_exc()
                        # 确保意外情况下也减少充电站计数
                        try:
                            self.update_charging_station_count(-1)
                        except:
                            pass
                    return
                
                # 更新位置
                position_update_counter += 1
                if position_update_counter >= params['POSITION_UPDATE_INTERVAL']:
                    position_update_counter = 0
                    try:
                        VehicleDAO.update_vehicle_location_and_battery(
                            self.vehicle_id, 
                            self.current_x, 
                            self.current_y, 
                            location_name, 
                            self.current_battery
                        )
                    except Exception as e:
                        print(f"更新车辆位置和电量时出错: {e}")
                
                # 更新电量
                battery_update_counter += 1
                if battery_update_counter >= params['BATTERY_UPDATE_INTERVAL']:
                    battery_update_counter = 0
                    try:
                        VehicleDAO.update_vehicle_battery(self.vehicle_id, self.current_battery)
                    except Exception as e:
                        print(f"更新充电中的车辆电量时出错: {e}")
                
                time.sleep(position_movement_interval)
            
          
            # 更新位置为充电站
            try:
                station_name = f"充电站 {self.station_code}"
                VehicleDAO.update_vehicle_location_coordinates(
                    self.vehicle_id, self.station_x, self.station_y, station_name
                )
                
                # 更新车辆状态为充电中
                VehicleDAO.update_vehicle_status(self.vehicle_id, "充电中")
                
                # 模拟充电过程
                self.simulate_charging()
            except Exception as e:
                print(f"{thread_name} 到达充电站更新状态出错: {e}")
                traceback.print_exc()
                
        except Exception as e:
            print(f"{thread_name} 前往充电站过程中出错: {e}")
            traceback.print_exc()
    
    def update_charging_station_count(self, increment):
        """更新充电站当前车辆数量
        
        Args:
            increment: 增加/减少的数量(正数增加，负数减少)
        """
        # 使用新的ChargingStationDAO类进行充电站车辆数量更新
        
        success, old_count, new_count, max_capacity = ChargingStationDAO.update_station_vehicle_count(
            self.station_code, self.city_code, increment
        )
        
        if success:
            return True
        else:
            print(f"更新充电站 {self.station_code} 车辆数量失败")
            return False
    
    def simulate_charging(self):
        """模拟充电过程"""
        try:
            # 获取车辆当前电量
            vehicle_info = VehicleDAO.get_vehicle_by_id(self.vehicle_id)
            if not vehicle_info:
                print(f"找不到车辆 {self.vehicle_id} 的信息，无法模拟充电")
                self.update_charging_station_count(-1)  # 释放充电站位置
                return
                
            # 获取车型和充电速度系数
            vehicle_model = vehicle_info.get('model')
            if vehicle_model:
                try:
                    # 获取车辆参数
                    _, vehicle_params_dict = get_vehicle_parameters(self.vehicle_id)
                    charging_speed_coefficient = vehicle_params_dict.get('charging_speed_coefficient', 1.0)
                    
                    # 如果系数为None，使用默认值
                    if charging_speed_coefficient is None:
                        charging_speed_coefficient = 1.0
                
                except Exception as e:
                    charging_speed_coefficient = 1.0
                    print(f"获取车型充电系数出错: {e}，使用默认值1.0")
            else:
                charging_speed_coefficient = 1.0
                print(f"车辆没有型号信息，使用默认充电速度系数1.0")
                
    
            # 获取当前电量和目标电量
            current_battery = vehicle_info.get('battery_level', 0)
            target_battery = 100
            
            # 保存初始电量，用于计算充电费用
            initial_battery = current_battery
            
            if current_battery >= target_battery:
                print(f"车辆 {self.vehicle_id} 电量已满({current_battery}%)，无需充电")
                # 更新车辆状态为空闲
                VehicleDAO.update_vehicle_status(self.vehicle_id, "空闲中")
                self.update_charging_station_count(-1)  # 释放充电站位置
                return
            
            # 计算充电所需时间
            # 充电速率 = 基础充电速率 * 车型充电速度系数
            # 使用params字典获取CHARGING_RATE，而不是全局变量
            charging_rate_base = self.params.get('CHARGING_RATE', 0.5)
            charging_rate = charging_rate_base * charging_speed_coefficient
            
            # 防止充电速率为0或负数
            if charging_rate <= 0:
                charging_rate = 0.5  # 使用默认值
                print(f"充电速率计算错误，使用默认值0.5")
                
            # 计算充电所需时间(秒)，每个时间单位充电charging_rate%
            remaining_battery = target_battery - current_battery
            total_charging_time = remaining_battery / charging_rate
            
            # 充电时间太长时进行限制，避免无限等待
            max_charging_time = 600  # 最多10分钟
            if total_charging_time > max_charging_time:
                print(f"充电时间过长 ({total_charging_time:.2f}秒)，限制为{max_charging_time}秒")
                total_charging_time = max_charging_time
                
            # 分解为多个步骤充电
            charging_step_interval = 5  # 每5秒更新一次充电状态
            charging_steps = max(int(total_charging_time / charging_step_interval), 1)
            battery_step = remaining_battery / charging_steps
            
         
            # 模拟充电过程
            for i in range(charging_steps):
                if self.stop:
                    print(f"充电过程被中断")
                    # 更新最终电量状态
                    try:
                        # 计算当前已充电电量
                        charged_amount = battery_step * i
                        final_battery = min(current_battery + charged_amount, 100)
                        VehicleDAO.update_vehicle_battery(self.vehicle_id, final_battery)
                        
                        # 更新车辆状态
                        VehicleDAO.update_vehicle_status(self.vehicle_id, "空闲中")
                        
                        # 释放充电站位置
                        self.update_charging_station_count(-1)
                        
                        print(f"充电中断，最终电量: {final_battery:.2f}%")
                        
                        # 计算中断充电的费用
                        charged_percentage = final_battery - initial_battery
                        if charged_percentage > 0:
                            try:
                                self.record_charging_expense(initial_battery, final_battery)
                            except Exception as e:
                                print(f"记录中断充电费用时出错: {e}")
                    except Exception as e:
                        print(f"中断充电更新状态出错: {e}")
                    return
                    
                # 计算充电后电量
                current_battery += battery_step
                if current_battery > 100:
                    current_battery = 100
                    
                # 更新电量
                try:
                    VehicleDAO.update_vehicle_battery(self.vehicle_id, current_battery)
                    # 不更新车辆状态，保持"充电中"
                except Exception as e:
                    print(f"更新充电中的车辆电量时出错: {e}")
                    
        
                # 等待一段时间
                time.sleep(charging_step_interval)
                
            # 充电完成，更新最终状态
            try:
                # 确保电量为100%
                VehicleDAO.update_vehicle_battery(self.vehicle_id, 100)
                
                # 更新车辆状态为空闲
                VehicleDAO.update_vehicle_status(self.vehicle_id, "空闲中")
                
                # 记录充电费用
                try:
                    self.record_charging_expense(initial_battery, 100)
                except Exception as e:
                    print(f"记录充电费用时出错: {e}")
                    traceback.print_exc()
                
                # 释放充电站位置
                self.update_charging_station_count(-1)
                
            
                
                # 通知下一个等待充电的车辆
                if self.city_code:
                    waiting_vehicle = VehicleDAO.find_vehicle_by_status_and_city("等待充电", self.city_code)
                    waiting_vehicle_id = waiting_vehicle.get('vehicle_id') if waiting_vehicle else None
                    waiting_vehicle_info = VehicleDAO.get_vehicle_by_id(waiting_vehicle_id) if waiting_vehicle_id else None
                    
                    if waiting_vehicle_id and waiting_vehicle_info:
                        print(f"通知等待充电的车辆 {waiting_vehicle_id} 前往充电站")
                        
                        # 更新等待车辆状态
                        VehicleDAO.update_vehicle_status(waiting_vehicle_id, "前往充电")
                        
                        # 创建新的充电站移动线程
                        movement_thread = ChargingStationMovementThread(
                            vehicle_id=waiting_vehicle_id,
                            current_x=waiting_vehicle_info.get('current_location_x'),
                            current_y=waiting_vehicle_info.get('current_location_y'),
                            station_x=self.station_x,
                            station_y=self.station_y,
                            station_code=self.station_code,
                            current_battery=waiting_vehicle_info.get('battery_level'),
                            city_code=self.city_code
                            # 不要传递speed参数，让线程自己计算基于车型的速度
                        )
                        movement_thread.daemon = True
                        movement_thread.start()
                else:
                    print("缺少城市代码，无法通知等待充电的车辆")
            except Exception as e:
                print(f"更新充电完成状态出错: {e}")
                traceback.print_exc()
        except Exception as e:
            print(f"充电过程出错: {e}")
            traceback.print_exc()
            # 确保释放充电站位置
            try:
                self.update_charging_station_count(-1)
            except:
                pass
                
    def record_charging_expense(self, start_battery, end_battery):
        """记录充电费用
        
        参数:
            start_battery: 充电开始时的电量百分比
            end_battery: 充电结束时的电量百分比
        """
        from app.config.vehicle_params import get_param, get_city_charging_price_factor
        from app.dao.expense_dao import ExpenseDAO
        from datetime import date
        
        try:
            # 获取充电站ID
            station_query = "SELECT station_id FROM charging_stations WHERE station_code = %s"
            from app.dao.base_dao import BaseDAO
            station_result = BaseDAO.execute_query(station_query, (self.station_code,))
            if not station_result:
                print(f"找不到充电站 {self.station_code} 的ID，无法记录充电费用")
                return
            
            station_id = station_result[0]['station_id']
            
            # 获取充电价格参数
            try:
                charging_price_per_percent = get_param('CHARGING_PRICE_PER_PERCENT')
            except Exception as e:
                error_msg = f"获取充电价格参数失败: {e}"
                print(error_msg)
                raise ValueError(error_msg)
            
            # 计算充电量和费用
            charged_percentage = end_battery - start_battery
            if charged_percentage <= 0:
                print(f"充电量为零或负值，不记录费用")
                return
                
            # 获取车辆型号
            vehicle_info = VehicleDAO.get_vehicle_by_id(self.vehicle_id)
            vehicle_model = vehicle_info.get('model', '未知') if vehicle_info else '未知'
            
            # 计算费用 = 充电百分比 * 每百分比价格 * 电池容量系数
            # 应确保capacity_coefficient在run方法中已被初始化
            if not hasattr(self, 'capacity_coefficient'):
                error_msg = f"车辆 {self.vehicle_id} ({vehicle_model}) 的电池容量系数未初始化"
                print(error_msg)
                raise ValueError(error_msg)
            

            try:
                city_charging_price_factor = get_city_charging_price_factor(self.city_code)

            except Exception as e:
                print(f"获取城市 {self.city_code} 充电价格系数失败: {e}")
                traceback.print_exc()
            
            # 使用电池容量系数和城市价格系数计算充电费用
            total_cost = charged_percentage * charging_price_per_percent * self.capacity_coefficient * city_charging_price_factor
            
            # 创建费用描述
            description = (f"车辆 {self.vehicle_id} ({vehicle_model}) 在充电站 {self.station_code} "
                          f"充电 {charged_percentage:.2f}%，从 {start_battery:.2f}% 到 {end_battery:.2f}%，"
                          f"电池容量系数: {self.capacity_coefficient:.2f}, 城市充电价格系数: {city_charging_price_factor:.2f}")
            
            # 添加费用记录
            expense_id = ExpenseDAO.add_expense(
                amount=total_cost,
                expense_type='充电站支出',
                vehicle_id=self.vehicle_id,
                charging_station_id=station_id,
                date=date.today().strftime('%Y-%m-%d'),
                description=description
            )
            
            if not expense_id:
                print(f"记录充电费用失败")
        except Exception as e:
            print(f"记录充电费用出错: {e}")
            traceback.print_exc()
    
@orders_bp.route('/api/idle_vehicles', methods=['GET'])
def get_idle_vehicles():
    """获取指定城市中所有空闲状态的车辆"""
    try:
        city = request.args.get('city', 'all')
        
        if not city or city == 'all':
            return jsonify({"status": "error", "message": "必须指定城市参数"}), 400
            
        # 调用VehicleDAO获取空闲车辆
        vehicles = VehicleDAO.get_idle_vehicles_by_city(city)
        
        return jsonify({
            "status": "success",
            "message": f"获取到 {len(vehicles)} 辆空闲车辆",
            "data": vehicles
        })
        
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"获取空闲车辆错误: {error_traceback}")
        return jsonify({"status": "error", "message": str(e), "traceback": error_traceback}), 500

@orders_bp.route('/api/auto_assign_pending_orders', methods=['POST'])
def auto_assign_pending_orders():
    """自动分配待处理订单功能 - 使用算法模块的实现
    
    循环执行"一键分配"功能，直到没有更多待分配的订单或者收到终止信号
    
    参数:
        batch_size: 每批处理的订单数量 (可选，默认为10)
        city_code: 城市代码 (可选，默认处理所有城市)
        
    返回:
        成功: {"status": "success", "message": "分配结果", "data": {...}}
        失败: {"status": "error", "message": "错误信息"}
    """
    try:
        data = request.json
        batch_size = int(data.get('batch_size', 10))
        city_code = data.get('city_code', None)
        
        # 验证参数
        if batch_size < 1:
            return jsonify({"status": "error", "message": "批次大小必须大于0"}), 400
            
        # 创建任务ID用于前端查询状态
        task_id = str(uuid.uuid4())
        
        # 获取待分配订单总数，用于进度计算
        total_orders = 0
        try:
            orders_query = """
            SELECT COUNT(*) as count
            FROM orders
            WHERE order_status = '待分配'
            """
            
            # 如果指定了城市，添加过滤条件
            params = []
            if city_code:
                orders_query += " AND city_code = %s"
                params.append(city_code)
                
            result = BaseDAO.execute_query(orders_query, tuple(params) if params else ())
            if result and len(result) > 0:
                total_orders = result[0]['count']
                print(f"找到总共 {total_orders} 个待分配订单")
        except Exception as e:
            print(f"获取订单总数时出错: {str(e)}")
            traceback.print_exc()
        
        # 将任务状态保存在全局字典中
        global auto_assign_tasks, auto_assign_stop_signals
        auto_assign_tasks[task_id] = {
            "status": "running",
            "successful_count": 0,
            "failed_count": 0,
            "total_processed": 0,
            "start_time": datetime.now(),
            "last_update": datetime.now(),
            "total_orders": total_orders,
            "iteration": 0,
            "estimated_total": total_orders or 0
        }
        
        # 确保停止信号初始化为False
        auto_assign_stop_signals[task_id] = False
        
        # 启动一个新线程来实际执行分配任务
        threading.Thread(target=run_auto_assign, args=(task_id, batch_size, city_code), daemon=True).start()
        
        # 立即返回任务ID，让前端可以开始跟踪状态
        return jsonify({
            "status": "success",
            "message": "自动分配任务已启动",
            "data": {
                "task_id": task_id,
                "total_orders": total_orders
            }
        })
        
    except Exception as e:
        print(f"启动自动分配订单失败: {str(e)}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"自动分配订单失败: {str(e)}"}), 500

def run_auto_assign(task_id, batch_size, city_code):
    """在独立线程中执行自动分配任务 - 使用算法模块的实现"""
    try:
        total_successful = 0
        total_failed = 0
        all_successful = []
        all_failed = []
        
        # 循环执行分配，直到没有更多订单或接收到停止信号
        iteration = 0
        stopped = False  # 新增变量，用于标记是否收到停止信号
        
        while True:
            # 首先检查是否收到终止信号
            if task_id in auto_assign_stop_signals and auto_assign_stop_signals[task_id]:
                print(f"收到任务 {task_id} 的终止信号，立即停止分配")
                stopped = True
                break
                
            iteration += 1
            print(f"开始第 {iteration} 轮订单分配，每批 {batch_size} 个")
            
            # 每轮开始时更新待分配订单总数，确保进度计算准确
            try:
                orders_query = """
                SELECT COUNT(*) as count
                FROM orders
                WHERE order_status = '待分配'
                """
                
                # 如果指定了城市，添加过滤条件
                params = []
                if city_code:
                    orders_query += " AND city_code = %s"
                    params.append(city_code)
                    
                result = BaseDAO.execute_query(orders_query, tuple(params) if params else ())
                if result and len(result) > 0:
                    total_orders = result[0]['count']
               
                    
                    # 更新任务状态中的总订单数
                    if task_id in auto_assign_tasks:
                        auto_assign_tasks[task_id]["total_orders"] = total_orders
                        
                        # 如果已经没有订单，标记任务完成并退出
                        if total_orders == 0:
                            print(f"已完成所有待分配订单，任务结束")
                            auto_assign_tasks[task_id].update({
                                "status": "completed",
                                "end_time": datetime.now(),
                                "total_successful": total_successful,
                                "total_failed": total_failed,
                                "total_processed": total_successful + total_failed
                            })
                            break
            except Exception as e:
                print(f"更新订单总数时出错: {str(e)}")
                traceback.print_exc()

            # 更新迭代次数
            if task_id in auto_assign_tasks:
                auto_assign_tasks[task_id]["iteration"] = iteration
            
            # 再次检查是否收到终止信号
            if task_id in auto_assign_stop_signals and auto_assign_stop_signals[task_id]:
                print(f"收到任务 {task_id} 的终止信号，立即停止分配")
                stopped = True
                break
                    
            # 更新最后活动时间，避免自动超时
            if task_id in auto_assign_tasks:
                auto_assign_tasks[task_id]["last_update"] = datetime.now()
            
            # 获取待分配的订单
            try:
                # 检查最近是否有更新，如果前端停止请求状态超过30秒，也终止任务
                if task_id in auto_assign_tasks:
                    last_update_time = auto_assign_tasks[task_id]["last_update"]
                    current_time = datetime.now()
                    if (current_time - last_update_time).total_seconds() > 30:
                        print(f"任务 {task_id} 超过30秒未更新状态，自动终止")
                        break

                orders_query = """
                SELECT order_id
                FROM orders
                WHERE order_status = '待分配'
                """
                
                # 如果指定了城市，添加过滤条件
                params = []
                if city_code:
                    orders_query += " AND city_code = %s"
                    params.append(city_code)
                    
                orders_query += " ORDER BY create_time ASC LIMIT %s"
                params.append(batch_size)
                
                pending_orders = BaseDAO.execute_query(orders_query, tuple(params))
                
                if not pending_orders:
                    print("没有更多待分配的订单，自动分配结束")
                    break
                    
                # 提取订单ID列表
                order_ids = [order['order_id'] for order in pending_orders]
             
                
                # 再次检查是否收到终止信号
                if task_id in auto_assign_stop_signals and auto_assign_stop_signals[task_id]:
                    print(f"在处理前收到任务 {task_id} 的终止信号，立即停止分配")
                    stopped = True
                    break
                
                # 调用算法模块的分配功能
                result = OrderAssignmentAlgorithm.assign_orders(order_ids, task_id, auto_assign_stop_signals)
                
                # 检查是否收到了停止信号
                if result.get('should_stop', False):
                    print(f"算法处理过程中收到了停止信号，即将结束任务")
                    stopped = True
                    
                    # 更新统计信息
                    if 'data' in result:
                        if 'successful' in result['data']:
                            successful_in_batch = len(result['data']['successful'])
                            total_successful += successful_in_batch
                            all_successful.extend(result['data']['successful'])
                        
                        if 'failed' in result['data']:
                            failed_in_batch = len(result['data']['failed'])
                            total_failed += failed_in_batch
                            all_failed.extend(result['data']['failed'])
                    
                    # 更新任务状态
                    if task_id in auto_assign_tasks:
                        auto_assign_tasks[task_id].update({
                            "successful_count": total_successful,
                            "failed_count": total_failed,
                            "total_processed": total_successful + total_failed,
                            "last_update": datetime.now()
                        })
                    
                    break
                
                # 处理返回的结果
                if result['status'] in ['success', 'warning']:
                    # 获取成功和失败的分配数
                    successful_in_batch = len(result['data']['successful'])
                    failed_in_batch = len(result['data']['failed'])
                    
                    # 更新全局计数
                    total_successful += successful_in_batch
                    total_failed += failed_in_batch
                    
                    # 保存分配结果
                    all_successful.extend(result['data']['successful'])
                    all_failed.extend(result['data']['failed'])
                    
                    # 更新任务状态
                    if task_id in auto_assign_tasks:
                        auto_assign_tasks[task_id].update({
                            "successful_count": total_successful,
                            "failed_count": total_failed,
                            "total_processed": total_successful + total_failed,
                            "last_update": datetime.now()
                        })
                    
                    # 启动车辆移动模拟
                    for assignment in result['data']['successful']:
                        try:
                            vehicle_id = assignment['vehicle_id']
                            order_id = assignment['order_id']
                            
                            # 获取详细订单信息和车辆信息
                            order_detail = OrderDAO.get_order_by_id(order_id)
                            vehicle = VehicleDAO.get_vehicle_by_id(vehicle_id)
                            
                            if order_detail and vehicle:
                                # 启动车辆移动模拟线程
                                start_vehicle_movement(
                                    vehicle_id=vehicle_id,
                                    order_id=order_id,
                                    vehicle_x=float(vehicle['current_location_x']),
                                    vehicle_y=float(vehicle['current_location_y']),
                                    pickup_x=float(order_detail['pickup_location_x']),
                                    pickup_y=float(order_detail['pickup_location_y']),
                                    dropoff_x=float(order_detail['dropoff_location_x']),
                                    dropoff_y=float(order_detail['dropoff_location_y']),
                                    pickup_name=order_detail['pickup_location'],
                                    dropoff_name=order_detail['dropoff_location']
                                )
                        except Exception as e:
                            print(f"启动车辆移动线程失败: {str(e)}")
                            traceback.print_exc()
                    
                    print(f"第 {iteration} 轮处理完成。成功: {successful_in_batch}, 失败: {failed_in_batch}, 总进度: {total_successful + total_failed} / {auto_assign_tasks[task_id]['total_orders'] if task_id in auto_assign_tasks else '未知'}")
                    
                else:
                    # 处理中出现错误
                    print(f"第 {iteration} 轮处理出错: {result.get('message', '未知错误')}")
                    
                    # 更新任务状态
                    if task_id in auto_assign_tasks:
                        auto_assign_tasks[task_id].update({
                            "last_update": datetime.now()
                        })
                
            except Exception as e:
                print(f"获取或处理待分配订单出错: {str(e)}")
                traceback.print_exc()
                
                # 出错后稍作等待，避免进入错误循环
                time.sleep(2)
                
                # 尝试更新任务状态
                if task_id in auto_assign_tasks:
                    auto_assign_tasks[task_id].update({
                        "last_update": datetime.now()
                    })
                
            # 每轮分配之间稍微暂停，避免系统负载过高
            time.sleep(0.5)
        
        # 任务结束，标记完成状态
        if task_id in auto_assign_tasks:
            status_message = "任务完成" if not stopped else "任务被中止"
            auto_assign_tasks[task_id].update({
                "status": "completed",
                "end_time": datetime.now(),
                "total_successful": total_successful,
                "total_failed": total_failed,
                "total_processed": total_successful + total_failed,
                "message": status_message
            })
            
            print(f"自动分配任务 {task_id} 已结束: {status_message}, 共处理 {total_successful + total_failed} 个订单, 成功 {total_successful} 个, 失败 {total_failed} 个")
    
    except Exception as e:
        print(f"自动分配主线程出错: {str(e)}")
        traceback.print_exc()
        
        # 发生异常时也将任务标记为完成
        if task_id in auto_assign_tasks:
            auto_assign_tasks[task_id].update({
                "status": "completed",
                "end_time": datetime.now(),
                "total_successful": total_successful,
                "total_failed": total_failed,
                "total_processed": total_successful + total_failed,
                "message": f"任务出错: {str(e)}"
            })

@orders_bp.route('/api/stop_auto_assign', methods=['POST'])
def stop_auto_assign():
    """发送停止自动分配的信号"""
    try:
        data = request.json
        task_id = data.get('task_id')
        
        if not task_id:
            return jsonify({"status": "error", "message": "未提供任务ID"}), 400
            
        # 设置终止信号
        global auto_assign_stop_signals, auto_assign_tasks
        auto_assign_stop_signals[task_id] = True
        
        # 立即更新任务状态为"正在停止"
        if task_id in auto_assign_tasks:
            # 如果任务状态都为零，直接标记为已完成
            if auto_assign_tasks[task_id].get("successful_count", 0) == 0 and auto_assign_tasks[task_id].get("failed_count", 0) == 0:
                auto_assign_tasks[task_id]["status"] = "completed"
                auto_assign_tasks[task_id]["end_time"] = datetime.now()
             
            else:
                auto_assign_tasks[task_id]["status_message"] = "正在停止中..."
               
                # 给进程一点时间来处理停止信号
                def mark_as_completed():
                    time.sleep(3)  # 等待3秒，让进程有时间处理停止信号
                    if task_id in auto_assign_tasks and auto_assign_tasks[task_id]["status"] != "completed":
                        auto_assign_tasks[task_id]["status"] = "completed"
                        auto_assign_tasks[task_id]["end_time"] = datetime.now()
                        print(f"任务 {task_id} 等待超时，强制标记为已完成")
                
                # 启动一个线程在几秒后标记任务为已完成
                threading.Thread(target=mark_as_completed, daemon=True).start()
        
        return jsonify({
            "status": "success",
            "message": "已发送终止信号，分配任务将立即停止"
        })
        
    except Exception as e:
        print(f"发送停止信号失败: {str(e)}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"发送停止信号失败: {str(e)}"}), 500

@orders_bp.route('/api/auto_assign_status/<task_id>', methods=['GET'])
def get_auto_assign_status(task_id):
    """获取自动分配任务的状态"""
    try:
        if not task_id or task_id not in auto_assign_tasks:
            return jsonify({"status": "error", "message": "任务不存在"}), 404
            
        task_status = auto_assign_tasks[task_id]
        
        return jsonify({
            "status": "success", 
        "data": task_status
        })
        
    except Exception as e:
        print(f"获取任务状态失败: {str(e)}")
        return jsonify({"status": "error", "message": f"获取任务状态失败: {str(e)}"}), 500

@orders_bp.route('/api/find_nearest_vehicle', methods=['GET'])
def find_nearest_vehicle():
    """查找最近的空闲车辆 - 使用算法模块的实现"""
    try:
        city = request.args.get('city')
        pickup_x = request.args.get('pickup_x')
        pickup_y = request.args.get('pickup_y')
        
        if not city:
            return jsonify({"status": "error", "message": "缺少城市参数"}), 400
        
        # 将坐标转换为浮点数
        try:
            if pickup_x is not None and pickup_y is not None:
                pickup_x = float(pickup_x)
                pickup_y = float(pickup_y)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "坐标格式无效"}), 400
        
        # 使用算法模块查找最近的车辆
        result = OrderAssignmentAlgorithm.find_nearest_vehicle(city, pickup_x, pickup_y)
        return jsonify(result)
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"获取最近车辆出错: {error_traceback}")
        return jsonify({"status": "error", "message": str(e), "traceback": error_traceback}), 500

# 取消订单API端点
@orders_bp.route('/api/cancel_order', methods=['POST'])
def api_cancel_order():
    """取消订单的API端点，直接从数据库删除订单"""
    try:
        # 获取请求数据
        data = request.json
        order_id = data.get('order_id')
        
        if not order_id:
            return jsonify({
                'status': 'error',
                'message': '订单ID不能为空'
            }), 400
        
        # 获取订单详情，确认是否存在
        order = OrderDAO.get_order_by_id(order_id)
        if not order:
            return jsonify({
                'status': 'error',
                'message': f'找不到订单 ID: {order_id}'
            }), 404
        
        # 删除订单，任何状态的订单都可以删除
        try:
            # 构建SQL删除语句
            delete_query = "DELETE FROM orders WHERE order_id = %s"
            result = BaseDAO.execute_update(delete_query, (order_id,))
            
            if result > 0:
                return jsonify({
                    'status': 'success',
                    'message': '订单已成功删除',
                    'data': {
                        'order_id': order_id
                    }
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': '删除订单失败'
                }), 500
        except Exception as e:
            print(f"删除订单错误: {str(e)}")
            traceback.print_exc()
            return jsonify({
                'status': 'error',
                'message': f'删除订单失败: {str(e)}'
            }), 500
            
    except Exception as e:
        print(f"取消订单错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'发生错误: {str(e)}'
        }), 500

@orders_bp.route('/api/pending_orders_locations', methods=['GET'])
def get_pending_orders_locations():
    """获取所有待分配订单的位置信息
    
    查询参数:
        city: 城市代码(可选，默认为所有城市)
        
    返回:
        JSON格式的待分配订单位置信息，包括订单ID、上车位置坐标
    """
    try:
        # 获取请求参数
        city = request.args.get('city', None)
        
        # 构建查询条件
        query = """
        SELECT 
            order_id, 
            pickup_location_x, 
            pickup_location_y, 
            pickup_location,
            city_code,
            create_time
        FROM 
            orders
        WHERE 
            order_status = '待分配'
        """
        
        params = []
        
        # 如果指定了城市，添加过滤条件
        if city and city != 'all':
            query += " AND city_code = %s"
            params.append(city)
            
        # 获取最近创建的订单，最多100个
        query += " ORDER BY create_time DESC LIMIT 100"
        
        # 执行查询
        from app.dao.base_dao import BaseDAO
        results = BaseDAO.execute_query(query, tuple(params) if params else ())
        
        # 格式化日期
        for result in results:
            if 'create_time' in result and result['create_time']:
                result['create_time'] = result['create_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        # 返回结果
        return jsonify({
            "status": "success",
            "message": f"找到 {len(results)} 个待分配订单",
            "data": results
        })
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"获取待分配订单位置错误: {error_traceback}")
        return jsonify({"status": "error", "message": str(e), "traceback": error_traceback}), 500