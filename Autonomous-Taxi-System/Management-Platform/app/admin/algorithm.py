from flask import Blueprint, render_template, jsonify, request
from app.dao.order_dao import OrderDAO
from app.dao.vehicle_dao import VehicleDAO
from app.dao.base_dao import BaseDAO
import traceback
import math
from datetime import datetime
from app.config import vehicle_params as vp

# 尝试导入scipy进行匈牙利算法计算
try:
    from scipy.optimize import linear_sum_assignment
    import numpy as np
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("警告：未安装scipy，将使用贪心算法进行订单分配")

# 创建蓝图
algorithm_bp = Blueprint('algorithm', __name__, url_prefix='/algorithm')

@algorithm_bp.route('/')
def index():
    """算法测试主页"""
    return render_template('algorithm/index.html') 

# 订单分配算法模块
class OrderAssignmentAlgorithm:
    """订单分配算法类,处理所有订单分配相关的计算"""
    
    @staticmethod
    def assign_orders(order_ids, task_id=None, stop_signals=None):
        """核心订单分配算法
        
        Args:
            order_ids: 订单ID列表
            task_id: 任务ID，用于检查停止信号
            stop_signals: 停止信号字典
            
        Returns:
            dict: 包含处理结果的字典
        """
        try:
            successful_assignments = []
            failed_assignments = []
            
            # 步骤1: 获取所有订单并按城市分组
            all_orders = OrderAssignmentAlgorithm._get_orders_by_ids(order_ids)
            
            if not all_orders:
                return {
                    "status": "warning", 
                    "message": "没有找到待分配状态的订单",
                    "data": {
                        "successful": [],
                        "failed": []
                    }
                }
            
            # 检查是否收到停止信号
            if OrderAssignmentAlgorithm._should_stop(task_id, stop_signals):
                print(f"订单加载后收到停止信号，中断处理")
                return {
                    "status": "warning",
                    "message": "收到停止信号，分配已中断",
                    "data": {
                        "successful": [],
                        "failed": []
                    },
                    "should_stop": True
                }
            
            # 按城市分组订单
            city_orders = OrderAssignmentAlgorithm._group_orders_by_city(all_orders)
            
            # 检查停止信号
            if OrderAssignmentAlgorithm._should_stop(task_id, stop_signals):
                print(f"分组城市后收到停止信号，中断处理")
                return {
                    "status": "warning",
                    "message": "收到停止信号，分配已中断",
                    "data": {
                        "successful": successful_assignments,
                        "failed": failed_assignments
                    },
                    "should_stop": True
                }
                
            # 处理每个城市的订单
            for city, orders in city_orders.items():
                # 检查停止信号
                if OrderAssignmentAlgorithm._should_stop(task_id, stop_signals):
                    return {
                        "status": "warning",
                        "message": "收到停止信号，分配已中断",
                        "data": {
                            "successful": successful_assignments,
                            "failed": failed_assignments
                        },
                        "should_stop": True
                    }
                
                # 获取该城市可用车辆数量
                available_vehicles = OrderAssignmentAlgorithm._get_available_vehicles_count(city)
                
                # 如果没有可用车辆，直接标记所有订单为失败
                if available_vehicles == 0:
                    for order in orders:
                        failed_assignments.append({
                            "order_id": order['order_id'],
                            "reason": f"城市 {city} 中没有可用车辆"
                        })
                    continue
                
                # 如果车辆不足，只处理前N个订单（N=可用车辆数）
                processable_orders = orders[:available_vehicles]
                skipped_orders = orders[available_vehicles:]
                
                # 标记跳过的订单为失败
                for order in skipped_orders:
                    failed_assignments.append({
                        "order_id": order['order_id'],
                        "reason": f"城市 {city} 可用车辆不足，该订单已跳过处理"
                    })
                
                # 处理可以分配的订单
                result = OrderAssignmentAlgorithm._process_city_orders(
                    city, processable_orders, task_id, stop_signals
                )
                
                # 合并处理结果
                successful_assignments.extend(result['successful'])
                failed_assignments.extend(result['failed'])
                
                # 检查是否需要停止
                if result.get('should_stop', False):
                    return {
                        "status": "warning",
                        "message": "收到停止信号，分配已中断",
                        "data": {
                            "successful": successful_assignments,
                            "failed": failed_assignments
                        },
                        "should_stop": True
                    }
            
            # 返回结果
            return {
                "status": "success",
                "message": f"共处理 {len(order_ids)} 个订单，成功 {len(successful_assignments)} 个，失败 {len(failed_assignments)} 个",
                "data": {
                    "successful": successful_assignments,
                    "failed": failed_assignments
                }
            }
            
        except Exception as e:
            print(f"处理自动分配时出错: {str(e)}")
            traceback.print_exc()
            return {
                "status": "error", 
                "message": str(e)
            }
    
    @staticmethod
    def _get_orders_by_ids(order_ids):
        """获取指定ID的待分配订单"""
        if len(order_ids) == 1:
            # 处理只有一个ID的情况
            orders_query = """
            SELECT order_id, city_code, create_time 
            FROM orders
            WHERE order_id = %s AND order_status = '待分配'
            ORDER BY create_time ASC
            """
            return BaseDAO.execute_query(orders_query, (order_ids[0],))
        else:
            # 处理多个ID的情况
            placeholders = ', '.join(['%s'] * len(order_ids))
            orders_query = f"""
            SELECT order_id, city_code, create_time 
            FROM orders
            WHERE order_id IN ({placeholders}) AND order_status = '待分配'
            ORDER BY create_time ASC
            """
            return BaseDAO.execute_query(orders_query, order_ids)
    
    @staticmethod
    def _group_orders_by_city(orders):
        """将订单按城市分组"""
        city_orders = {}
        for order in orders:
            city = order['city_code']
            if city not in city_orders:
                city_orders[city] = []
            city_orders[city].append(order)
        return city_orders
    
    @staticmethod
    def _get_available_vehicles_count(city):
        """获取城市可用车辆数量"""
        vehicle_count_query = """
        SELECT COUNT(*) as count 
        FROM vehicles
        WHERE operating_city = %s AND current_status = '空闲中'
        """
        result = BaseDAO.execute_query(vehicle_count_query, (city,))
        return result[0]['count'] if result else 0
    
    @staticmethod
    def _should_stop(task_id, stop_signals):
        """检查是否收到停止信号"""
        if task_id and stop_signals and task_id in stop_signals and stop_signals[task_id]:
            return True
        return False
    
    @staticmethod
    def _process_city_orders(city, orders, task_id, stop_signals):
        """处理指定城市的订单分配 - 使用批量全局优化"""
        successful = []
        failed = []
        
        # 检查停止信号
        if OrderAssignmentAlgorithm._should_stop(task_id, stop_signals):
            for order in orders:
                failed.append({"order_id": order['order_id'], "reason": "收到停止信号，分配已中断"})
            return {"successful": successful, "failed": failed, "should_stop": True}
        
        # 获取所有待分配订单的详细信息
        valid_orders = []
        for order in orders:
            try:
                order_detail = OrderDAO.get_order_by_id(order['order_id'])
                if not order_detail:
                    failed.append({"order_id": order['order_id'], "reason": "订单不存在"})
                    continue
                    
                if order_detail.get('order_status') != '待分配':
                    failed.append({"order_id": order['order_id'], "reason": f"订单状态为 '{order_detail.get('order_status')}'"})
                    continue
                    
                if not order_detail.get('pickup_location_x') or not order_detail.get('pickup_location_y'):
                    failed.append({"order_id": order['order_id'], "reason": "订单缺少上车点坐标"})
                    continue
                    
                valid_orders.append(order_detail)
            except Exception as e:
                failed.append({"order_id": order['order_id'], "reason": f"处理异常: {str(e)}"})
        
        if not valid_orders:
            return {"successful": successful, "failed": failed}
        
        # 批量全局优化分配
        batch_result = OrderAssignmentAlgorithm._batch_assign_vehicles(city, valid_orders)
        successful.extend(batch_result['successful'])
        failed.extend(batch_result['failed'])
        
        return {"successful": successful, "failed": failed}
    
    @staticmethod
    def _batch_assign_vehicles(city, orders):
        """批量分配车辆 - 真正的全局优化"""
        successful = []
        failed = []
        
        try:
            # 获取所有空闲车辆
            idle_vehicles_query = """
            SELECT v.vehicle_id, v.plate_number, v.model, v.current_location_x, v.current_location_y, 
                   v.battery_level, v.operating_city
            FROM vehicles v
            WHERE v.operating_city = %s AND v.current_status = '空闲中'
            """
            idle_vehicles = BaseDAO.execute_query(idle_vehicles_query, (city,))
            
            if not idle_vehicles:
                for order in orders:
                    failed.append({"order_id": order['order_id'], "reason": "城市中没有空闲车辆"})
                return {"successful": successful, "failed": failed}
            
            # 设置车辆速度参数
            for vehicle in idle_vehicles:
                model = vehicle.get('model')
                if model:
                    try:
                        speed_var_name = f"{model.replace('-', '_')}_SPEED"
                        vehicle['max_speed'] = getattr(vp, speed_var_name, 60)
                    except:
                        vehicle['max_speed'] = 60
                else:
                    vehicle['max_speed'] = 60
            
            print(f"批量优化: {len(orders)}个订单 vs {len(idle_vehicles)}辆车辆")
            
            # 构建成本矩阵
            cost_matrix = []
            for vehicle in idle_vehicles:
                veh_x, veh_y = float(vehicle['current_location_x']), float(vehicle['current_location_y'])
                speed_factor = vehicle['max_speed'] / 60
                
                vehicle_costs = []
                for order in orders:
                    order_x = float(order['pickup_location_x'])
                    order_y = float(order['pickup_location_y'])
                    distance = math.sqrt((veh_x - order_x)**2 + (veh_y - order_y)**2)
                    eta = distance / speed_factor if speed_factor > 0 else float('inf')
                    vehicle_costs.append(eta)
                cost_matrix.append(vehicle_costs)
            
            # 使用匈牙利算法或贪心算法进行分配
            assignments = []
            if SCIPY_AVAILABLE and len(orders) > 1:
                try:
                    print("使用匈牙利算法进行批量全局优化")
                    cost_array = np.array(cost_matrix)
                    
                    # 处理矩阵尺寸不匹配
                    if len(idle_vehicles) != len(orders):
                        if len(idle_vehicles) > len(orders):
                            diff = len(idle_vehicles) - len(orders)
                            virtual_costs = np.full((len(idle_vehicles), diff), 0)
                            cost_array = np.hstack([cost_array, virtual_costs])
                        else:
                            diff = len(orders) - len(idle_vehicles)
                            virtual_costs = np.full((diff, len(orders)), 1000)
                            cost_array = np.vstack([cost_array, virtual_costs])
                    
                    row_indices, col_indices = linear_sum_assignment(cost_array)
                    
                    for row_idx, col_idx in zip(row_indices, col_indices):
                        if row_idx < len(idle_vehicles) and col_idx < len(orders):
                            assignments.append((row_idx, col_idx))
                            
                except Exception as e:
                    print(f"匈牙利算法失败: {str(e)}, 使用贪心算法")
                    assignments = OrderAssignmentAlgorithm._greedy_assign(cost_matrix, len(orders), len(idle_vehicles))
            else:
                print("使用贪心算法进行批量分配")
                assignments = OrderAssignmentAlgorithm._greedy_assign(cost_matrix, len(orders), len(idle_vehicles))
            
            # 执行分配
            for vehicle_idx, order_idx in assignments:
                try:
                    order = orders[order_idx]
                    vehicle = idle_vehicles[vehicle_idx]
                    
                    # 分配车辆到订单
                    if OrderDAO.assign_vehicle(order['order_id'], vehicle['vehicle_id']):
                        if VehicleDAO.update_vehicle_status(vehicle['vehicle_id'], "运行中"):
                            successful.append({
                                "order_id": order['order_id'],
                                "vehicle_id": vehicle['vehicle_id'],
                                "plate_number": vehicle.get('plate_number', '未知'),
                                "distance": f"{cost_matrix[vehicle_idx][order_idx]:.2f} 单位",
                                "rating_score": 100 / (cost_matrix[vehicle_idx][order_idx] + 1)
                            })
                        else:
                            OrderDAO.update_order_status(order['order_id'], "待分配")  # 回滚
                            failed.append({"order_id": order['order_id'], "reason": "车辆状态更新失败"})
                    else:
                        failed.append({"order_id": order['order_id'], "reason": "订单更新失败"})
                        
                except Exception as e:
                    failed.append({"order_id": orders[order_idx]['order_id'], "reason": f"分配异常: {str(e)}"})
            
            # 处理未分配的订单
            assigned_orders = {assignment[1] for assignment in assignments}
            for i, order in enumerate(orders):
                if i not in assigned_orders:
                    failed.append({"order_id": order['order_id'], "reason": "车辆资源不足"})
            
        except Exception as e:
            for order in orders:
                failed.append({"order_id": order['order_id'], "reason": f"批量分配异常: {str(e)}"})
        
        return {"successful": successful, "failed": failed}
    
    @staticmethod
    def _greedy_assign(cost_matrix, num_orders, num_vehicles):
        """贪心算法分配"""
        assignments = []
        used_vehicles = set()
        used_orders = set()
        
        max_assignments = min(num_orders, num_vehicles)
        
        for _ in range(max_assignments):
            best_cost = float('inf')
            best_assignment = None
            
            for v_idx in range(num_vehicles):
                if v_idx in used_vehicles:
                    continue
                for o_idx in range(num_orders):
                    if o_idx in used_orders:
                        continue
                    if cost_matrix[v_idx][o_idx] < best_cost:
                        best_cost = cost_matrix[v_idx][o_idx]
                        best_assignment = (v_idx, o_idx)
            
            if best_assignment:
                assignments.append(best_assignment)
                used_vehicles.add(best_assignment[0])
                used_orders.add(best_assignment[1])
            else:
                break
                
        return assignments
    
    @staticmethod
    def find_nearest_vehicle(city, pickup_x, pickup_y):
        """查找距离上车点最近的车辆"""
        try:
            vehicle = VehicleDAO.get_nearest_vehicle(city, pickup_x, pickup_y)
            if not vehicle:
                return {
                    "status": "error",
                    "message": f"在城市 {city} 中没有找到空闲车辆"
                }
            
            return {
                "status": "success",
                "data": vehicle
            }
        except Exception as e:
            print(f"查找最近车辆时出错: {str(e)}")
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"查找最近车辆时发生异常: {str(e)}"
            }
    
    @staticmethod
    def get_nearest_vehicle_with_rating(city_code, pickup_location_x, pickup_location_y, use_rating=True):
        """获取最优车辆以最小化整体订单等待时间
        
        基于车辆距离、速度和全局订单分布进行优化分配，最小化总体订单等待时间
        
        Args:
            city_code: 城市代码
            pickup_location_x: 上车点X坐标
            pickup_location_y: 上车点Y坐标
            use_rating: 是否使用评分机制，默认为True
            
        Returns:
            dict: 包含车辆信息的字典，如果找不到则返回None
        """
        # 初始化vehicles变量为None，确保在所有执行路径中都有定义
        vehicles = None
        
        try:
            # 如果不使用评分机制，直接调用原方法
            if not use_rating:
                return VehicleDAO.get_nearest_vehicle(city_code, pickup_location_x, pickup_location_y)
            
            # 如果没有提供坐标，则使用基础方法
            if pickup_location_x is None or pickup_location_y is None:
                print("未提供上车点坐标，将使用基础方法")
                query = """
                SELECT 
                    v.vehicle_id, v.plate_number, v.model, v.current_status, v.battery_level,
                    v.mileage, v.current_location_x, v.current_location_y, v.current_location_name,
                    v.current_city, v.operating_city
                FROM vehicles v
                WHERE v.operating_city = %s AND v.current_status = '空闲中'
                ORDER BY v.battery_level DESC
                LIMIT 1
                """
                vehicles = BaseDAO.execute_query(query, (city_code,))
            else:
                # 确保坐标是数值类型
                try:
                    pickup_x = float(pickup_location_x)
                    pickup_y = float(pickup_location_y)
                    
                    # 获取当前城市所有待分配订单
                    pending_orders_query = """
                    SELECT order_id, pickup_location_x, pickup_location_y, create_time,
                           TIMESTAMPDIFF(MINUTE, create_time, NOW()) as wait_time
                    FROM orders 
                    WHERE city_code = %s AND order_status = '待分配'
                    ORDER BY create_time ASC
                    """
                    
                    # 获取所有空闲车辆信息
                    idle_vehicles_query = """
                    SELECT 
                        v.vehicle_id, v.plate_number, v.model, v.current_location_x, v.current_location_y, 
                        v.battery_level, v.operating_city
                    FROM vehicles v
                    WHERE v.operating_city = %s AND v.current_status = '空闲中'
                    """
                    
                    # 执行查询
                    pending_orders = BaseDAO.execute_query(pending_orders_query, (city_code,))
                    idle_vehicles = BaseDAO.execute_query(idle_vehicles_query, (city_code,))
                    
                    # 检查是否有空闲车辆
                    if not idle_vehicles:
                        print(f"在城市 {city_code} 没有找到空闲车辆")
                        return None
                    
                    # 确定当前订单在待分配订单中的索引，初始化为-1
                    current_order_index = -1
                    for i, order in enumerate(pending_orders):
                        if (abs(float(order['pickup_location_x']) - pickup_x) < 0.001 and 
                            abs(float(order['pickup_location_y']) - pickup_y) < 0.001):
                            current_order_index = i
                            break
                    
                    # 为每辆车设置最大速度(从vehicle_params.py中获取)
                    for vehicle in idle_vehicles:
                        model = vehicle.get('model')
                        if model:
                            # 根据车型获取对应的速度
                            try:
                                # 使用动态属性访问
                                speed_var_name = f"{model.replace('-', '_')}_SPEED"
                                vehicle['max_speed'] = getattr(vp, speed_var_name, None)
                                
                                # 如果找不到对应的速度变量，尝试转换格式
                                if vehicle['max_speed'] is None:
                                    alt_var_name = f"{model.split('-')[0]}_{model.split('-')[1]}_SPEED"
                                    vehicle['max_speed'] = getattr(vp, alt_var_name, None)
                                    
                                # 最后的兜底方案
                                if vehicle['max_speed'] is None:
                                    # 尝试从常量对照表中找
                                    model_map = {
                                        "Alpha-X1": "Alpha_X1_SPEED",
                                        "Alpha-Nexus": "Alpha_Nexus_SPEED",
                                        "Nova-S1": "Nova_S1_SPEED",
                                        "Nova-Quantum": "Nova_Quantum_SPEED",
                                        "Nova-Pulse": "Nova_Pulse_SPEED",
                                        "Neon-500": "Neon_500_SPEED",
                                        "Neon-Zero": "Neon_Zero_SPEED"
                                    }
                                    if model in model_map:
                                        vehicle['max_speed'] = getattr(vp, model_map[model], 60)
                                    else:
                                        # 依然没找到，使用默认速度60
                                        vehicle['max_speed'] = 60
                                
                                if vehicle['max_speed'] is None:
                                    vehicle['max_speed'] = 60
                                    print(f"未找到车型 {model} 的速度配置，使用默认速度60km/h")
                                
                            except (AttributeError, Exception) as e:
                                # 出错使用默认值
                                vehicle['max_speed'] = 60
                                print(f"获取车型 {model} 速度出错: {str(e)}，使用默认速度60km/h")
                        else:
                            # 无车型信息使用默认值
                            vehicle['max_speed'] = 60
                            print(f"车辆 {vehicle['vehicle_id']} 无车型信息，使用默认速度60km/h")
                    
                    # 如果仅有当前这一个订单，直接选最近的车辆
                    if len(pending_orders) == 1:
                        # 找到最近且速度最快的车辆
                        best_vehicle = None
                        best_eta = float('inf')  # 最佳到达时间(ETA)
                        
                        for vehicle in idle_vehicles:
                            veh_x = float(vehicle['current_location_x'])
                            veh_y = float(vehicle['current_location_y'])
                            
                            # 计算欧几里得距离
                            distance = math.sqrt((veh_x - pickup_x)**2 + (veh_y - pickup_y)**2)
                            
                            # 考虑车辆速度，计算预计到达时间(分钟)
                            # 假设每单位距离相当于1公里，速度单位为km/h
                            speed_factor = vehicle['max_speed'] / 60  # 转换为km/min
                            eta = distance / speed_factor if speed_factor > 0 else float('inf')
                            
                            if eta < best_eta:
                                best_eta = eta
                                best_vehicle = vehicle
                                best_vehicle['distance'] = distance
                                best_vehicle['eta'] = eta
                                best_vehicle['rating_score'] = 100 / (eta + 1)  # ETA越短评分越高
                        
                        if best_vehicle:
                            VehicleDAO._format_vehicle_data(best_vehicle)
                            best_vehicle['distance_formatted'] = f"{best_vehicle['distance']:.2f} 单位"
                            best_vehicle['eta_formatted'] = f"{best_vehicle['eta']:.2f} 分钟"
                            best_vehicle['rating_score_formatted'] = f"{best_vehicle['rating_score']:.2f}"
                            print(f"选择最快到达车辆: ID={best_vehicle['vehicle_id']}, ETA={best_vehicle['eta']:.2f}分钟")
                            return best_vehicle
                    
                    # ==== 全局优化算法：最小化平均等待时间 ====
                    print(f"采用全局优化算法，当前共有{len(pending_orders)}个待分配订单和{len(idle_vehicles)}辆空闲车辆")
                    
                    # 创建距离/时间矩阵: 每辆车到每个订单的距离和预计到达时间
                    distance_matrix = []
                    eta_matrix = []
                    
                    for vehicle in idle_vehicles:
                        veh_x = float(vehicle['current_location_x'])
                        veh_y = float(vehicle['current_location_y'])
                        speed_factor = vehicle['max_speed'] / 60  # 转换为km/min
                        
                        vehicle_distances = []
                        vehicle_etas = []
                        
                        for order in pending_orders:
                            if order['pickup_location_x'] and order['pickup_location_y']:
                                order_x = float(order['pickup_location_x'])
                                order_y = float(order['pickup_location_y'])
                                
                                # 计算欧几里得距离
                                distance = math.sqrt((veh_x - order_x)**2 + (veh_y - order_y)**2)
                                
                                # 计算预计到达时间
                                eta = distance / speed_factor if speed_factor > 0 else float('inf')
                                
                                vehicle_distances.append(distance)
                                vehicle_etas.append(eta)
                            else:
                                vehicle_distances.append(float('inf'))
                                vehicle_etas.append(float('inf'))
                        
                        distance_matrix.append(vehicle_distances)
                        eta_matrix.append(vehicle_etas)
                    
                    if current_order_index == -1:
                        print("当前订单不在待分配订单列表中，将只考虑当前订单")
                        # 直接寻找对当前订单最优的车辆
                        best_vehicle = None
                        best_eta = float('inf')
                        
                        for i, vehicle in enumerate(idle_vehicles):
                            veh_x = float(vehicle['current_location_x'])
                            veh_y = float(vehicle['current_location_y'])
                            
                            # 计算欧几里得距离和ETA
                            distance = math.sqrt((veh_x - pickup_x)**2 + (veh_y - pickup_y)**2)
                            speed_factor = vehicle['max_speed'] / 60
                            eta = distance / speed_factor if speed_factor > 0 else float('inf')
                            
                            if eta < best_eta:
                                best_eta = eta
                                best_vehicle = vehicle
                                best_vehicle['distance'] = distance
                                best_vehicle['eta'] = eta
                                best_vehicle['rating_score'] = 100 / (eta + 1)
                        
                        if best_vehicle:
                            VehicleDAO._format_vehicle_data(best_vehicle)
                            best_vehicle['distance_formatted'] = f"{best_vehicle['distance']:.2f} 单位"
                            best_vehicle['eta_formatted'] = f"{best_vehicle['eta']:.2f} 分钟"
                            best_vehicle['rating_score_formatted'] = f"{best_vehicle['rating_score']:.2f}"
                            return best_vehicle
                    
                    # ==== 使用匈牙利算法或贪心算法进行全局优化分配 ====
                    best_vehicle_for_current = None
                    
                    if SCIPY_AVAILABLE and len(pending_orders) > 1:
                        try:
                            print(f"使用匈牙利算法进行全局优化")
                            # 创建成本矩阵
                            cost_matrix = np.array(eta_matrix)
                            
                            # 处理矩阵尺寸不匹配的情况
                            if len(idle_vehicles) != len(pending_orders):
                                if len(idle_vehicles) > len(pending_orders):
                                    # 车辆多于订单，添加虚拟订单
                                    diff = len(idle_vehicles) - len(pending_orders)
                                    virtual_costs = np.full((len(idle_vehicles), diff), 0)  # 虚拟订单成本为0
                                    cost_matrix = np.hstack([cost_matrix, virtual_costs])
                                else:
                                    # 订单多于车辆，添加虚拟车辆
                                    diff = len(pending_orders) - len(idle_vehicles)
                                    virtual_costs = np.full((diff, len(pending_orders)), 1000)  # 虚拟车辆成本很高
                                    cost_matrix = np.vstack([cost_matrix, virtual_costs])
                            
                            # 使用匈牙利算法求解
                            row_indices, col_indices = linear_sum_assignment(cost_matrix)
                            
                            # 找到当前订单对应的车辆
                            for row_idx, col_idx in zip(row_indices, col_indices):
                                if col_idx == current_order_index and row_idx < len(idle_vehicles):
                                    best_vehicle_for_current = idle_vehicles[row_idx]
                                    best_vehicle_for_current['distance'] = distance_matrix[row_idx][col_idx]
                                    best_vehicle_for_current['eta'] = eta_matrix[row_idx][col_idx]
                                    best_vehicle_for_current['rating_score'] = 100 / (eta_matrix[row_idx][col_idx] + 1)
                                    print(f"匈牙利算法选择车辆: ID={best_vehicle_for_current['vehicle_id']}")
                                    break
                                    
                        except Exception as e:
                            print(f"使用匈牙利算法时出错: {str(e)}，回退到贪心算法")
                            best_vehicle_for_current = None
                    
                    # 如果没有scipy或匈牙利算法失败，使用贪心算法
                    if best_vehicle_for_current is None:
                        print("使用贪心算法进行分配")
                    min_avg_waiting_time = float('inf')
                    
                    # 确定最大分配数量(取车辆数和订单数的较小值)
                    max_assignments = min(len(idle_vehicles), len(pending_orders))
                    
                    # 对每辆车，计算如果分配给当前订单，对整体等待时间的影响
                    for current_vehicle_idx, vehicle in enumerate(idle_vehicles):
                        # 先假设这辆车分配给当前订单
                        remaining_vehicles = list(range(len(idle_vehicles)))
                        remaining_vehicles.remove(current_vehicle_idx)
                        remaining_orders = list(range(len(pending_orders)))
                        remaining_orders.remove(current_order_index)
                        
                        # 记录已分配的车辆和订单
                        assignments = [(current_vehicle_idx, current_order_index)]
                        
                        # 贪心算法：为剩余订单分配最近的车辆
                        while len(assignments) < max_assignments and remaining_vehicles and remaining_orders:
                            best_pair = (None, None)
                            best_eta = float('inf')
                            
                            for v_idx in remaining_vehicles:
                                for o_idx in remaining_orders:
                                    if eta_matrix[v_idx][o_idx] < best_eta:
                                        best_eta = eta_matrix[v_idx][o_idx]
                                        best_pair = (v_idx, o_idx)
                            
                            if best_pair[0] is not None:
                                assignments.append(best_pair)
                                remaining_vehicles.remove(best_pair[0])
                                remaining_orders.remove(best_pair[1])
                            else:
                                break
                        
                            # 计算已分配订单的平均等待时间
                        total_waiting_time = 0
                        for v_idx, o_idx in assignments:
                            total_waiting_time += eta_matrix[v_idx][o_idx]
                        
                            avg_waiting_time = total_waiting_time / len(assignments)
                        
                        # 更新最优分配方案
                        if avg_waiting_time < min_avg_waiting_time:
                            min_avg_waiting_time = avg_waiting_time
                            current_vehicle_eta = eta_matrix[current_vehicle_idx][current_order_index]
                            best_vehicle_for_current = vehicle
                            best_vehicle_for_current['distance'] = distance_matrix[current_vehicle_idx][current_order_index]
                            best_vehicle_for_current['eta'] = current_vehicle_eta
                            best_vehicle_for_current['rating_score'] = 100 / (current_vehicle_eta + 1)
                            best_vehicle_for_current['global_avg_waiting'] = avg_waiting_time
                    
                    # 使用最优车辆
                    if best_vehicle_for_current:
                        VehicleDAO._format_vehicle_data(best_vehicle_for_current)
                        best_vehicle_for_current['distance_formatted'] = f"{best_vehicle_for_current['distance']:.2f} 单位"
                        best_vehicle_for_current['eta_formatted'] = f"{best_vehicle_for_current['eta']:.2f} 分钟"
                        best_vehicle_for_current['rating_score_formatted'] = f"{best_vehicle_for_current['rating_score']:.2f}"
                        return best_vehicle_for_current
                    
                except (ValueError, TypeError) as e:
                    print(f"坐标或计算错误: {e}, 将使用基本方法")
                    
                # 如果全局优化算法没有找到车辆，使用基本方法作为降级
                if 'best_vehicle_for_current' in locals() and best_vehicle_for_current:
                    return best_vehicle_for_current
                    
                # 降级到基本查询方法
                print("全局优化未找到合适车辆，使用基本查询方法")
                query = """
                SELECT 
                    v.vehicle_id, v.plate_number, v.model, v.current_status, v.battery_level,
                    v.mileage, v.current_location_x, v.current_location_y, v.current_location_name,
                    v.current_city, v.operating_city
                FROM vehicles v
                WHERE v.operating_city = %s AND v.current_status = '空闲中'
                ORDER BY v.battery_level DESC
                LIMIT 1
                """
                vehicles = BaseDAO.execute_query(query, (city_code,))
            
            if not vehicles:
                print(f"在城市 {city_code} 没有找到空闲车辆")
                return None
            
            vehicle = vehicles[0]
            VehicleDAO._format_vehicle_data(vehicle)
            
            # 如果存在距离计算结果，添加到返回数据中
            if 'distance' in vehicle:
                vehicle['distance'] = float(vehicle['distance'])
                vehicle['distance_formatted'] = f"{vehicle['distance']:.2f} 单位"
                
                # 计算ETA
                if 'model' in vehicle:
                    # 从vehicle_params.py获取车辆速度
                    model = vehicle.get('model')
                    try:
                        # 使用动态属性访问
                        speed_var_name = f"{model.replace('-', '_')}_SPEED"
                        max_speed = getattr(vp, speed_var_name, None)
                        
                        # 如果找不到对应的速度变量，尝试转换格式
                        if max_speed is None:
                            alt_var_name = f"{model.split('-')[0]}_{model.split('-')[1]}_SPEED"
                            max_speed = getattr(vp, alt_var_name, None)
                            
                        # 最后的兜底方案
                        if max_speed is None:
                            # 尝试从常量对照表中找
                            model_map = {
                                "Alpha-X1": "Alpha_X1_SPEED",
                                "Alpha-Nexus": "Alpha_Nexus_SPEED",
                                "Nova-S1": "Nova_S1_SPEED",
                                "Nova-Quantum": "Nova_Quantum_SPEED",
                                "Nova-Pulse": "Nova_Pulse_SPEED",
                                "Neon-500": "Neon_500_SPEED",
                                "Neon-Zero": "Neon_Zero_SPEED"
                            }
                            if model in model_map:
                                max_speed = getattr(vp, model_map[model], 60)
                            else:
                                # 依然没找到，使用默认速度60
                                max_speed = 60
                        
                        if max_speed is None:
                            max_speed = 60
                            print(f"未找到车型 {model} 的速度配置，使用默认速度60km/h")
                        
                    except (AttributeError, Exception) as e:
                        # 出错使用默认值
                        max_speed = 60
                        print(f"获取车型 {model} 速度出错: {str(e)}，使用默认速度60km/h")
                        
                    # 计算ETA
                    speed_factor = max_speed / 60  # 转换为km/min
                    eta = vehicle['distance'] / speed_factor
                    
                    vehicle['eta'] = eta
                    vehicle['eta_formatted'] = f"{eta:.2f} 分钟"
                    vehicle['rating_score'] = 100 / (eta + 1)
                    vehicle['rating_score_formatted'] = f"{vehicle['rating_score']:.2f}"
                
                else:
                    # 仍然设置一个基于距离的评分
                    vehicle['rating_score'] = 100 / (vehicle['distance'] + 1)
                    vehicle['rating_score_formatted'] = f"{vehicle['rating_score']:.2f}"
            
            print(f"找到车辆: ID={vehicle['vehicle_id']}, 距离={vehicle.get('distance_formatted', '未知')}")
            return vehicle
            
        except Exception as e:
            print(f"获取最优车辆错误: {str(e)}")
            traceback.print_exc()
            # 出错时尝试使用原始方法作为降级策略
            try:
                print("尝试使用基本的最近车辆策略作为降级")
                return VehicleDAO.get_nearest_vehicle(city_code, pickup_location_x, pickup_location_y)
            except:
                return None

# 添加API接口用于算法测试
@algorithm_bp.route('/api/assign_test', methods=['POST'])
def test_assignment_algorithm():
    """测试订单分配算法API"""
    try:
        data = request.json
        order_ids = data.get('order_ids', [])
        
        if not order_ids:
            return jsonify({"status": "error", "message": "未提供订单ID列表"}), 400
            
        # 调用分配算法
        result = OrderAssignmentAlgorithm.assign_orders(order_ids)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@algorithm_bp.route('/api/nearest_vehicle_test', methods=['GET'])
def test_nearest_vehicle():
    """测试查找最近车辆算法API"""
    try:
        city = request.args.get('city')
        pickup_x = request.args.get('pickup_x')
        pickup_y = request.args.get('pickup_y')
        use_rating = request.args.get('use_rating', 'true').lower() == 'true'
        
        if not city:
            return jsonify({"status": "error", "message": "缺少城市参数"}), 400
        
        # 将坐标转换为浮点数
        try:
            if pickup_x is not None and pickup_y is not None:
                pickup_x = float(pickup_x)
                pickup_y = float(pickup_y)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "坐标格式无效"}), 400
        
        # 调用查找最近车辆算法(根据参数决定是否使用评分机制)
        if use_rating:
            # 使用带评分的方法
            vehicle = OrderAssignmentAlgorithm.get_nearest_vehicle_with_rating(city, pickup_x, pickup_y)
            if not vehicle:
                return jsonify({
                    "status": "error",
                    "message": f"在城市 {city} 中没有找到空闲车辆"
                })
            
            return jsonify({
                "status": "success",
                "data": vehicle,
                "message": "使用了评分机制分配车辆"
            })
        else:
            # 使用原始的方法
            result = OrderAssignmentAlgorithm.find_nearest_vehicle(city, pickup_x, pickup_y)
            result["message"] = "使用了基于距离的原始分配方法"
            return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@algorithm_bp.route('/api/create_vehicle_params_table', methods=['POST'])
def create_vehicle_params_table():
    """创建车型参数配置表并从vehicle_params模块中获取数据填充"""
    try:
        # 创建vehicle_params表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS vehicle_params (
            id INT AUTO_INCREMENT PRIMARY KEY,
            model_name VARCHAR(50) NOT NULL UNIQUE COMMENT '车型名称',
            max_speed INT NOT NULL COMMENT '最大速度(km/h)',
            acceleration DECIMAL(5,2) DEFAULT 2.5 COMMENT '加速度(m/s²)',
            max_range INT DEFAULT 400 COMMENT '最大续航里程(km)',
            charging_time INT DEFAULT 60 COMMENT '充电时间(分钟)',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_model_name (model_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='车型参数配置表';
        """
        BaseDAO.execute_update(create_table_sql, ())
        
        # 检查表是否为空
        check_sql = "SELECT COUNT(*) as count FROM vehicle_params"
        result = BaseDAO.execute_query(check_sql, ())
        
        if result[0]['count'] == 0:
            # 从vehicle_params模块中获取车型速度数据
            vehicle_models = []
            try:
                # Alpha系列
                vehicle_models.append(("Alpha-X1", vp.Alpha_X1_SPEED))
                vehicle_models.append(("Alpha-Nexus", vp.Alpha_Nexus_SPEED))
                # 尝试添加可能存在的Alpha-Voyager
                try:
                    vehicle_models.append(("Alpha-Voyager", vp.Alpha_Voyager_SPEED))
                except AttributeError:
                    pass
                
                # Nova系列
                vehicle_models.append(("Nova-S1", vp.Nova_S1_SPEED))
                vehicle_models.append(("Nova-Quantum", vp.Nova_Quantum_SPEED))
                vehicle_models.append(("Nova-Pulse", vp.Nova_Pulse_SPEED))
                
                # Neon系列
                vehicle_models.append(("Neon-500", vp.Neon_500_SPEED))
                vehicle_models.append(("Neon-Zero", vp.Neon_Zero_SPEED))
                
                # 过滤掉速度为None的车型
                vehicle_models = [(model, speed) for model, speed in vehicle_models if speed is not None]
                
            except AttributeError as e:
                # 如果访问变量失败，使用一组默认数据
                print(f"从vehicle_params模块获取数据失败: {str(e)}，使用默认值")
                vehicle_models = [
                    ("Alpha-X1", 120),
                    ("Alpha-Nexus", 110),
                    ("Nova-S1", 95),
                    ("Nova-Quantum", 90),
                    ("Nova-Pulse", 80),
                    ("Neon-500", 100),
                    ("Neon-Zero", 85)
                ]
            
            # 批量插入数据
            if vehicle_models:
                insert_sql = """
                INSERT INTO vehicle_params (model_name, max_speed)
                VALUES (%s, %s)
                """
                
                for model_data in vehicle_models:
                    BaseDAO.execute_update(insert_sql, model_data)
                    
                return jsonify({
                    "status": "success",
                    "message": f"车型参数表创建成功并添加了{len(vehicle_models)}条数据",
                    "data": {
                        "models": vehicle_models
                    }
                })
            else:
                return jsonify({
                    "status": "warning",
                    "message": "车型参数表创建成功，但未能添加任何数据",
                    "data": {
                        "models": []
                    }
                })
        
        return jsonify({
            "status": "success",
            "message": "车型参数表已存在",
            "data": {
                "table_exists": True
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"创建车型参数表失败: {str(e)}"
        }), 500

@algorithm_bp.route('/api/install_scipy', methods=['POST'])
def install_scipy():
    """安装scipy依赖的说明API"""
    try:
        return jsonify({
            "status": "info",
            "message": "要使用匈牙利算法，需要安装scipy依赖",
            "instructions": [
                "1. 打开命令提示符或PowerShell",
                "2. 运行命令: pip install scipy numpy", 
                "3. 重启Flask应用程序",
                "4. 安装完成后，系统将自动使用匈牙利算法进行全局最优分配"
            ],
            "current_status": "已安装scipy" if SCIPY_AVAILABLE else "未安装scipy",
            "benefits": [
                "使用匈牙利算法可以找到全局最优解",
                "相比贪心算法，能更有效地降低平均等待时间",
                "特别适合车辆资源紧张的高峰期场景"
            ]
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"获取安装信息失败: {str(e)}"
        }), 500

@algorithm_bp.route('/api/algorithm_status', methods=['GET'])
def algorithm_status():
    """查看当前算法状态"""
    try:
        return jsonify({
            "status": "success",
            "data": {
                "scipy_available": SCIPY_AVAILABLE,
                "current_algorithm": "匈牙利算法 (全局最优)" if SCIPY_AVAILABLE else "贪心算法 (局部最优)",
                "performance": {
                    "hungarian_algorithm": {
                        "name": "匈牙利算法",
                        "complexity": "O(n³)",
                        "optimality": "全局最优",
                        "available": SCIPY_AVAILABLE
                    },
                    "greedy_algorithm": {
                        "name": "贪心算法",
                        "complexity": "O(n²)",
                        "optimality": "局部最优",
                        "available": True
                    }
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"获取算法状态失败: {str(e)}"
        }), 500 