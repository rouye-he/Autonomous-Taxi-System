from flask import Blueprint, render_template, jsonify, request, url_for, redirect
from app.dao.vehicle_dao import VehicleDAO
import traceback
import threading
import time
from app.dao.base_dao import BaseDAO
from app.models.vehicle import Vehicle
from app.models.charging_station import ChargingStation
from app.models.vehicle_log import VehicleLog
import json
import random
from datetime import datetime, timedelta
from app.config.vehicle_params import CHARGING_STATION_BASE_COST, CHARGING_STATION_VARIABLE_COST, BASE_MAINTENANCE_COST
from app.dao.expense_dao import ExpenseDAO  # 添加ExpenseDAO导入
from app.utils.flash_helper import flash_success, flash_error, flash_warning, flash_info, flash_add_success, flash_update_success, flash_delete_success, flash_operation_success, flash_operation_failed

# 创建蓝图
vehicles_bp = Blueprint('vehicles', __name__, url_prefix='/vehicles')

@vehicles_bp.route('/')
def index():
    """车辆管理主页"""
    # 获取搜索参数
    search_params = {}
    for key, value in request.args.items():
        if value and key != 'page' and key != 'ajax' and key != 'include_stats':
            search_params[key] = value

    page = request.args.get('page', 1, type=int)
    
    # 检查是否是AJAX请求
    is_ajax = request.args.get('ajax') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    include_stats = request.args.get('include_stats') == '1'
    
    # 如果有搜索参数，进行高级搜索
    if search_params:
        return advanced_search()
    
    try:
        # 使用VehicleDAO获取车辆数据
        result = VehicleDAO.get_all_vehicles(page=page, per_page=10)
        
        # 字段中文名映射
        field_names = {
            'vehicle_id': '车辆ID',
            'plate_number': '车牌号',
            'vin': '车辆识别号',
            'model': '车辆型号',
            'battery_level_min': '最低电量',
            'battery_level_max': '最高电量',
            'mileage_min': '最低距离',
            'mileage_max': '最高距离',
            'rating_min': '最低评分',
            'rating_max': '最高评分',
            'total_orders_min': '最少订单数',
            'total_orders_max': '最多订单数',
            'is_available': '可用状态',
            'manufacture_date_start': '生产日期(开始)',
            'manufacture_date_end': '生产日期(结束)',
            'last_maintenance_date_start': '上次维护日期(开始)',
            'last_maintenance_date_end': '上次维护日期(结束)'
        }
        
        # 获取状态统计
        status_query = """
        SELECT 
            current_status, COUNT(*) as count
        FROM 
            vehicles
        GROUP BY current_status
        """
        
        status_counts = {}
        try:
            status_results = VehicleDAO.execute_query(status_query)
            status_counts = {row['current_status']: row['count'] for row in status_results}
        except:
            pass
        
        idle_count = status_counts.get('空闲中', 0)
        busy_count = status_counts.get('运行中', 0)
        charging_count = status_counts.get('充电中', 0)
        low_battery_count = status_counts.get('电量不足', 0)
        maintenance_count = status_counts.get('维护中', 0)
        
        status_stats = {
            'all': result['total_count'],
            'idle': idle_count,
            'busy': busy_count,
            'charging': charging_count,
            'low_battery': low_battery_count,
            'maintenance': maintenance_count
        }
        
        # 如果是AJAX请求，返回JSON数据
        if is_ajax:
            response_data = {
                'html': render_template('vehicles/_table.html',
                                       vehicles=result['vehicles'],
                                       current_page=result['current_page'],
                                       total_pages=result['total_pages'],
                                       total_count=result['total_count'],
                                       offset=(result['current_page'] - 1) * result['per_page'],
                                       per_page=result['per_page'],
                                       search_params=search_params),
                'total_count': result['total_count'],
                'current_page': result['current_page'],
                'total_pages': result['total_pages'],
                'offset': (result['current_page'] - 1) * result['per_page'],
                'per_page': result['per_page']
            }
            
            # 如果请求包含统计数据
            if include_stats:
                response_data['stats'] = status_stats
                
            return jsonify(response_data)
        
        # 正常页面请求
        return render_template('vehicles/index.html',
                           vehicles=result['vehicles'],
                           current_page=result['current_page'],
                           total_pages=result['total_pages'],
                           total_count=result['total_count'],
                           offset=(result['current_page'] - 1) * result['per_page'],
                           per_page=result['per_page'],
                           field_names=field_names,
                           status_counts=status_stats)
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"车辆管理页面加载错误: {error_traceback}")
        
        status_stats = {
            'all': 0,
            'idle': 0,
            'busy': 0,
            'charging': 0,
            'low_battery': 0,
            'maintenance': 0
        }
        
        # 如果是AJAX请求，返回错误信息
        if is_ajax:
            return jsonify({
                'html': f'<div class="alert alert-danger">加载数据出错: {str(e)}</div>',
                'stats': status_stats if include_stats else {},
                'success': False,
                'message': str(e)
            }), 500
        
        return render_template('vehicles/index.html', 
                          error=str(e), 
                          field_names=field_names,
                          current_page=page,
                          total_pages=1,
                          total_count=0,
                          offset=0,
                          per_page=10,
                          vehicles=[],
                          status_counts=status_stats)

@vehicles_bp.route('/advanced_search')
def advanced_search():
    """车辆高级搜索"""
    # 获取搜索参数
    search_params = {}
    for key, value in request.args.items():
        if value and key != 'page' and key != 'ajax' and key != 'include_stats':
            search_params[key] = value
    
    page = request.args.get('page', 1, type=int)
    
    # 检查是否是AJAX请求
    is_ajax = request.args.get('ajax') == '1'
    include_stats = request.args.get('include_stats') == '1'
    
    # 字段中文名映射
    field_names = {
        'vehicle_id': '车辆ID',
        'plate_number': '车牌号',
        'vin': '车辆识别号',
        'model': '车辆型号',
        'current_city': '城市',
        'current_status': '状态',
        'battery_level_min': '最低电量',
        'battery_level_max': '最高电量',
        'mileage_min': '最低距离',
        'mileage_max': '最高距离',
        'rating_min': '最低评分',
        'rating_max': '最高评分',
        'total_orders_min': '最少订单数',
        'total_orders_max': '最多订单数',
        'is_available': '可用状态',
        'manufacture_date_start': '生产日期(开始)',
        'manufacture_date_end': '生产日期(结束)',
        'last_maintenance_date_start': '上次维护日期(开始)',
        'last_maintenance_date_end': '上次维护日期(结束)'
    }
    
    try:
        # 使用VehicleDAO根据条件获取车辆数据
        result = VehicleDAO.get_vehicles_by_criteria(search_params, page=page, per_page=10)
        
        # 如果是AJAX请求，返回JSON数据
        if is_ajax:
            response_data = {
                'html': render_template('vehicles/_table.html',
                                      vehicles=result['vehicles'],
                                      current_page=result['current_page'],
                                      total_pages=result['total_pages'],
                                      total_count=result['total_count'],
                                      offset=(result['current_page'] - 1) * result['per_page'],
                                      per_page=result['per_page'],
                                      search_params=search_params)
            }
            
            # 如果请求包含统计数据
            if include_stats:
                response_data['stats'] = result['status_counts']
                
            return jsonify(response_data)
        
        # 正常页面请求
        return render_template('vehicles/index.html', 
                          vehicles=result['vehicles'],
                          current_page=result['current_page'],
                          total_pages=result['total_pages'],
                          total_count=result['total_count'],
                          offset=(result['current_page'] - 1) * result['per_page'],
                          per_page=result['per_page'],
                          search_params=search_params, 
                          field_names=field_names,
                          status_counts=result['status_counts'])
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"高级搜索错误: {error_traceback}")
        
        status_stats = {
            'all': 0,
            'idle': 0,
            'busy': 0,
            'charging': 0,
            'low_battery': 0,
            'maintenance': 0
        }
        
        # 如果是AJAX请求，返回错误信息
        if is_ajax:
            return jsonify({
                'html': f'<div class="alert alert-danger">高级搜索出错: {str(e)}</div>',
                'stats': status_stats if include_stats else {}
            })
        
        return render_template('vehicles/index.html', 
                          error=str(e), 
                          search_params=search_params,
                          field_names=field_names,
                          current_page=page,
                          total_pages=1, 
                          total_count=0,
                          offset=0,
                          per_page=10,
                          vehicles=[],
                          status_counts=status_stats)

@vehicles_bp.route('/map')
def map_view():
    """车辆地图视图"""
    return render_template('vehicles/map_view.html')
    
@vehicles_bp.route('/real_map')
def real_map_view():
    """真实地图API视图"""
    return render_template('vehicles/real_map_view.html')

@vehicles_bp.route('/api/city_vehicles', methods=['GET'])
def get_city_vehicles():
    """获取指定城市的车辆数据"""
    try:
        city = request.args.get('city', 'default')
        
        # 使用VehicleDAO获取城市车辆数据
        vehicles = VehicleDAO.get_city_vehicles(city)
        
        return jsonify({
            'status': 'success',
            'message': f'获取到 {len(vehicles)} 辆车',
            'data': vehicles
        })
        
    except Exception as e:
        print(f"获取城市车辆数据错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取车辆数据失败: {str(e)}'
        }), 500

@vehicles_bp.route('/api/city_charging_stations')
def get_city_charging_stations():
    """获取指定城市的充电站数据"""
    city_code = request.args.get('city', 'shenyang')
    
    try:
        # 使用VehicleDAO获取城市充电站数据
        stations = VehicleDAO.get_city_charging_stations(city_code)
        
        return jsonify({"status": "success", "data": stations})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500 

@vehicles_bp.route('/api/debug')
def api_debug():
    """简单的调试接口，返回纯文本"""
    return "API正常工作中"

@vehicles_bp.route('/api/all_vehicles')
def get_all_vehicles():
    """获取所有车辆数据"""
    try:
        # 获取所有车辆，不分页
        result = VehicleDAO.get_all_vehicles(page=1, per_page=1000)
        
        # 检查数据是否正确
        if not result['vehicles']:
            return jsonify({"status": "success", "data": [], "message": "无车辆数据"})
            
        return jsonify({"status": "success", "data": result['vehicles']})
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"错误详情: {error_traceback}")
        return jsonify({"status": "error", "message": str(e), "traceback": error_traceback}), 500

@vehicles_bp.route('/api/vehicle_details/<int:vehicle_id>')
def get_vehicle_details(vehicle_id):
    """获取单个车辆的详细信息"""
    try:
        # 使用VehicleDAO获取车辆详情
        vehicle = VehicleDAO.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            return jsonify({"status": "error", "message": "车辆不存在"}), 404
        
        return jsonify({"status": "success", "data": vehicle})
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"获取车辆详情错误: {error_traceback}")
        return jsonify({"status": "error", "message": str(e)}), 500

@vehicles_bp.route('/delete_vehicle/<int:vehicle_id>', methods=['POST'])
def delete_vehicle(vehicle_id):
    """删除车辆"""
    page = request.args.get('page', 1, type=int)
    
    try:
        print(f"开始处理删除车辆，ID: {vehicle_id}")
        
        # 获取车辆信息用于日志记录
        vehicle = VehicleDAO.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            print(f"车辆不存在，ID: {vehicle_id}")
            return jsonify({"status": "error", "message": "车辆不存在"}), 404
        
        # 记录车辆删除日志
        plate_number = vehicle['plate_number']
        model = vehicle.get('model', '未知')
        log_content = f"删除了车辆，车型：{model}，最后状态：{vehicle.get('current_status', '未知')}，所在城市：{vehicle.get('current_city', '未知')}"
        
        try:
            log_id = VehicleDAO.add_vehicle_log(vehicle_id, plate_number, '车辆删除', log_content)
            print(f"记录车辆删除日志成功，日志ID: {log_id}")
            
            # 保存日志ID，以便在删除车辆后保留该日志
            deletion_log_id = log_id
        except Exception as log_error:
            print(f"记录车辆删除日志失败: {str(log_error)}")
            traceback.print_exc()
            deletion_log_id = None
        
        # 不再删除任何日志记录，保留所有历史日志
        print(f"保留车辆ID为{vehicle_id}的所有日志记录")
        
        # 使用VehicleDAO删除车辆
        success = VehicleDAO.delete_vehicle(vehicle_id)
        
        if not success:
            print(f"删除车辆失败，ID: {vehicle_id}")
            return jsonify({"status": "error", "message": "车辆不存在"}), 404
        
        print(f"成功删除ID为{vehicle_id}的车辆")
        
        # 如果有搜索参数，拼接参数
        search_params = {}
        for key, value in request.args.items():
            if value and key != 'page':
                search_params[key] = value
        
        if search_params:
            # 构建带有搜索参数的重定向URL
            redirect_url = "/vehicles/advanced_search?page=" + str(page)
            for key, value in search_params.items():
                redirect_url += f"&{key}={value}"
        else:
            redirect_url = "/vehicles?page=" + str(page)
        
        return jsonify({"status": "success", "message": "车辆已成功删除", "redirect": redirect_url})
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"删除车辆错误: {error_traceback}")
        return jsonify({"status": "error", "message": str(e)}), 500

@vehicles_bp.route('/api/charging_stations')
def get_charging_stations():
    """获取充电站数据，可按城市筛选"""
    city_code = request.args.get('city', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    try:
        # 使用VehicleDAO获取充电站数据
        result = VehicleDAO.get_charging_stations(city=city_code, page=page, per_page=per_page)
        
        # 确保返回格式正确
        return jsonify({
            "status": "success", 
            "data": result['stations'],
            "cities": result['cities'],
            "selected_city": result['selected_city'],
            "pagination": result['pagination']
        })
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"获取充电站数据错误: {error_traceback}")
        return jsonify({"status": "error", "message": str(e)}), 500

@vehicles_bp.route('/api/update_vehicle_location', methods=['POST'])
def update_vehicle_location():
    """更新车辆的当前位置信息"""
    try:
        data = request.json
        vehicle_id = data.get('vehicle_id')
        location_name = data.get('location_name')
        location_x = data.get('location_x')
        location_y = data.get('location_y')
        city = data.get('city')
        
        if not vehicle_id or not location_name:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数：vehicle_id或location_name'
            }), 400
        
        # 构建位置数据
        location_data = {
            'location_name': location_name,
            'location_x': location_x,
            'location_y': location_y,
            'city': city
        }
        
        # 使用VehicleDAO更新车辆位置
        success = VehicleDAO.update_vehicle_location(vehicle_id, location_data)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '车辆位置更新成功'
            })
        else:
            return jsonify({
                'status': 'warning',
                'message': '没有找到车辆或位置未发生变化'
            }), 404
            
    except Exception as e:
        print(f"更新车辆位置错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'更新车辆位置失败: {str(e)}'
        }), 500

@vehicles_bp.route('/api/batch_update_locations', methods=['POST'])
def batch_update_vehicle_locations():
    """批量更新车辆的当前位置信息"""
    try:
        data = request.json
        updates = data.get('updates', [])
        
        if not updates or not isinstance(updates, list):
            return jsonify({
                'status': 'error',
                'message': '缺少有效的位置更新数据'
            }), 400
        
        # 使用VehicleDAO批量更新位置
        updated_count = VehicleDAO.batch_update_vehicle_locations(updates)
        
        return jsonify({
            'status': 'success',
            'message': f'批量更新车辆位置成功',
            'updated_count': updated_count,
            'total_updates': len(updates)
        })
        
    except Exception as e:
        print(f"批量更新车辆位置错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'批量更新车辆位置失败: {str(e)}'
        }), 500

@vehicles_bp.route('/edit_vehicle/<int:vehicle_id>', methods=['GET', 'POST'])
def edit_vehicle(vehicle_id):
    """编辑车辆信息"""
    page = request.args.get('page', 1, type=int)
    
    # 如果是GET请求，返回编辑页面
    if request.method == 'GET':
        try:
            # 获取车辆信息
            vehicle = VehicleDAO.get_vehicle_by_id(vehicle_id)
            
            if not vehicle:
                return render_template('error.html', 
                                      message="车辆不存在", 
                                      back_url=url_for('vehicles.index'))
            
            # 获取搜索参数
            search_params = {}
            for key, value in request.args.items():
                if value and key != 'page':
                    search_params[key] = value
            
            return render_template('vehicles/edit.html', 
                                 vehicle=vehicle,
                                 page=page,
                                 search_params=search_params)
        
        except Exception as e:
            error_traceback = traceback.format_exc()
            print(f"加载车辆编辑页面错误: {error_traceback}")
            return render_template('error.html', 
                                 message=f"加载车辆编辑页面失败: {str(e)}", 
                                 back_url=url_for('vehicles.index'))
    
    # 如果是POST请求，处理车辆更新
    elif request.method == 'POST':
        try:
            # 获取表单数据
            plate_number = request.form.get('plate_number')
            vin = request.form.get('vin')
            model = request.form.get('model')
            manufacture_date = request.form.get('manufacture_date')
            current_status = request.form.get('current_status')
            battery_level = request.form.get('battery_level', type=int)
            mileage = request.form.get('mileage', type=float)
            
            # 构建更新数据
            vehicle_data = {
                'plate_number': plate_number,
                'vin': vin,
                'model': model,
                'manufacture_date': manufacture_date,
                'current_status': current_status,
                'battery_level': battery_level,
                'mileage': mileage
            }
            
            # 更新车辆信息
            success = VehicleDAO.update_vehicle(vehicle_id, vehicle_data)
            
            if not success:
                return jsonify({
                    'status': 'error',
                    'message': '车辆不存在或更新失败'
                }), 404
            
            # 如果有搜索参数，拼接参数
            search_params = {}
            for key, value in request.args.items():
                if value and key != 'page':
                    search_params[key] = value
            
            if search_params:
                # 构建带有搜索参数的重定向URL
                redirect_url = "/vehicles/advanced_search?page=" + str(page)
                for key, value in search_params.items():
                    redirect_url += f"&{key}={value}"
            else:
                redirect_url = "/vehicles?page=" + str(page)
            
            return jsonify({
                'status': 'success',
                'message': '车辆信息已成功更新',
                'redirect': redirect_url
            })
        
        except Exception as e:
            error_traceback = traceback.format_exc()
            print(f"更新车辆信息错误: {error_traceback}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

@vehicles_bp.route('/api/check_zero_battery_vehicles', methods=['POST'])
def check_zero_battery_vehicles():
    """检测所有电量为0但状态不正确的车辆，将其状态更新为"电量不足"
    
    这个API用于处理因为某些原因电量为0但状态未更新的车辆
    """
    try:
        # 查找所有电量为0但状态不是"电量不足"的车辆
        query = """
        SELECT vehicle_id, plate_number, current_status, battery_level
        FROM vehicles
        WHERE battery_level <= 0 AND current_status != '电量不足'
        """
        
        vehicles = VehicleDAO.execute_query(query)
        
        if not vehicles:
            return jsonify({
                'status': 'success',
                'message': '没有发现电量为0但状态不正确的车辆',
                'affected_vehicles': []
            })
        
        # 更新所有找到的车辆状态
        fixed_vehicles = []
        for vehicle in vehicles:
            vehicle_id = vehicle['vehicle_id']
            old_status = vehicle['current_status']
            
            # 更新为电量不足状态
            success = VehicleDAO.update_vehicle_status(vehicle_id, "电量不足")
            
            if success:
                fixed_vehicles.append({
                    'vehicle_id': vehicle_id,
                    'plate_number': vehicle['plate_number'],
                    'old_status': old_status,
                    'new_status': '电量不足',
                    'battery_level': vehicle['battery_level']
                })
                
                # 发送车辆电量不足通知
                try:
                    from app.utils.notification_service import NotificationService
                    plate_number = vehicle.get('plate_number', '')
                    battery_level = vehicle.get('battery_level', 0)
                    NotificationService.notify_vehicle_low_battery(
                        vehicle_id=vehicle_id,
                        battery_level=battery_level,
                        plate_number=plate_number
                    )
                 
                except Exception as e:
                    print(f"发送电量不足通知失败: {str(e)}")
                    traceback.print_exc()
        
        return jsonify({
            'status': 'success',
            'message': f'已修复 {len(fixed_vehicles)} 辆电量为0的车辆状态',
            'affected_vehicles': fixed_vehicles
        })
        
    except Exception as e:
        print(f"检测电量为0的车辆出错: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'检测电量为0的车辆时出错: {str(e)}'
        }), 500

class ZeroBatteryCheckerThread(threading.Thread):
    """定期检查电量为0的车辆并将其状态更新为"电量不足" """
    
    def __init__(self, check_interval=300):  # 默认5分钟检查一次
        super().__init__()
        self.daemon = True  # 设置为守护线程，随主线程退出而退出
        self.check_interval = check_interval
        self.stop = False
    
    def run(self):
        """线程主循环"""
        while not self.stop:
            try:
                # 查找所有电量为0但状态不是"电量不足"的车辆
                query = """
                SELECT vehicle_id, plate_number, current_status, battery_level
                FROM vehicles
                WHERE battery_level <= 0 AND current_status != '电量不足'
                """
                
                vehicles = VehicleDAO.execute_query(query)
                
                if vehicles:
                    print(f"【自动检查】发现 {len(vehicles)} 辆电量为0但状态不正确的车辆")
                    
                    # 更新所有找到的车辆状态
                    for vehicle in vehicles:
                        vehicle_id = vehicle['vehicle_id']
                        old_status = vehicle['current_status']
                        
                        # 更新为电量不足状态
                        success = VehicleDAO.update_vehicle_status(vehicle_id, "电量不足")
                        
                        if success:                            
                            # 发送车辆电量不足通知
                            try:
                                from app.utils.notification_service import NotificationService
                                plate_number = vehicle.get('plate_number', '')
                                battery_level = vehicle.get('battery_level', 0)
                                NotificationService.notify_vehicle_low_battery(
                                    vehicle_id=vehicle_id,
                                    battery_level=battery_level,
                                    plate_number=plate_number
                                )
                            except Exception as e:
                                print(f"发送电量不足通知失败: {str(e)}")
                                traceback.print_exc()
                
            except Exception as e:
                print(f"自动检查电量为0的车辆时出错: {str(e)}")
                traceback.print_exc()
            
            # 等待下一次检查
            for _ in range(self.check_interval):
                if self.stop:
                    break
                time.sleep(1)

@vehicles_bp.route('/api/rescue_vehicle/<int:vehicle_id>', methods=['POST'])
def rescue_vehicle(vehicle_id):
    """救援电量不足的车辆，充满电量并更改状态为空闲中
    
    用于管理员手动恢复电量不足的车辆，使其能够立即恢复运营
    """
    try:
        # 首先获取车辆信息
        vehicle = VehicleDAO.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            return jsonify({
                'status': 'error',
                'message': f'找不到ID为 {vehicle_id} 的车辆'
            }), 404
        
        # 检查车辆是否处于电量不足状态
        if vehicle['current_status'] != '电量不足':
            return jsonify({
                'status': 'error',
                'message': f'该车辆当前状态为 "{vehicle["current_status"]}"，而不是"电量不足"'
            }), 400
        
        # 给车辆100%的电量，更新状态为空闲中
        update_query = """
        UPDATE vehicles
        SET battery_level = 100, current_status = '空闲中'
        WHERE vehicle_id = %s
        """
        
        VehicleDAO.execute_update(update_query, (vehicle_id,))
        
        # 尝试记录日志，如果日志表不存在，捕获异常但不影响主要功能
        try:
            log_query = """
            INSERT INTO vehicle_logs
            (vehicle_id, plate_number, log_type, log_content, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            """
            
            log_content = f"管理员救援电量不足车辆，充满电量至100%，状态从'电量不足'更改为'空闲中'"
            VehicleDAO.execute_update(log_query, (vehicle_id, vehicle['plate_number'], '车辆救援', log_content))
        except Exception as log_error:
            print(f"记录车辆救援日志失败: {str(log_error)}")
            print("系统将继续工作，但不会记录此次操作历史")
        
        return jsonify({
            'status': 'success',
            'message': f'成功救援车辆 {vehicle_id} ({vehicle["plate_number"]})，已充满电量并更改状态为"空闲中"'
        })
        
    except Exception as e:
        print(f"救援电量不足车辆错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'救援电量不足车辆时出错: {str(e)}'
        }), 500

@staticmethod
def check_and_update_zero_battery(vehicle_id, battery_level):
    """检查电量是否为0或负数，如果是则更新车辆状态为电量不足
    
    Args:
        vehicle_id: 车辆ID
        battery_level: 电量百分比
        
    Returns:
        bool: 是否更新了状态
    """
    try:
        if battery_level <= 0:
            # 先获取当前车辆状态
            vehicle = VehicleDAO.get_vehicle_by_id(vehicle_id)
            if not vehicle:
                print(f"无法找到车辆 {vehicle_id}，无法检查电量状态")
                return False
            
            # 更新车辆状态为电量不足
            VehicleDAO.update_vehicle_status(vehicle_id, '电量不足')
            print(f"车辆 {vehicle_id} 电量为 {battery_level}%，已更新状态为电量不足")
            return True
        return False
    except Exception as e:
        print(f"检查电量状态错误: {str(e)}")
        traceback.print_exc()
        return False

@vehicles_bp.route('/api/charging_station_info')
def get_charging_station_info():
    """获取特定充电站的最新信息
    
    请求参数:
    - station_code: 充电站编码
    - city_code: 城市编码
    
    返回:
    - JSON格式的充电站信息
    """
    try:
        station_code = request.args.get('station_code')
        city_code = request.args.get('city_code')
        
        if not station_code or not city_code:
            return jsonify({
                'status': 'error',
                'message': '缺少必要参数: station_code 和 city_code'
            })
        
        # 获取指定充电站的最新数据
        station_query = """
        SELECT 
            station_id, station_code, city_code, 
            location_x, location_y,
            current_vehicles, max_capacity,
            last_maintenance_date, next_maintenance_date,
            DATE_FORMAT(last_maintenance_date, '%Y-%m-%d') as last_maintenance_date_formatted,
            DATE_FORMAT(next_maintenance_date, '%Y-%m-%d') as next_maintenance_date_formatted
        FROM 
            charging_stations
        WHERE 
            station_code = %s AND city_code = %s
        """
        
        station_result = BaseDAO.execute_query(station_query, (station_code, city_code))
        
        if not station_result:
            return jsonify({
                'status': 'error',
                'message': f'找不到充电站: {station_code}'
            })
        
        station_info = station_result[0]
        
        # 格式化日期字段
        if 'last_maintenance_date_formatted' in station_info and station_info['last_maintenance_date_formatted']:
            station_info['last_maintenance_date'] = station_info['last_maintenance_date_formatted']
        if 'next_maintenance_date_formatted' in station_info and station_info['next_maintenance_date_formatted']:
            station_info['next_maintenance_date'] = station_info['next_maintenance_date_formatted']
        
        # 移除格式化字段，避免重复
        if 'last_maintenance_date_formatted' in station_info:
            del station_info['last_maintenance_date_formatted']
        if 'next_maintenance_date_formatted' in station_info:
            del station_info['next_maintenance_date_formatted']
            
        return jsonify({
            'status': 'success',
            'data': station_info
        })
    except Exception as e:
        print(f"获取充电站信息错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'系统错误: {str(e)}'
        })

@vehicles_bp.route('/logs')
def vehicle_logs():
    """车辆操作记录页面"""
    try:
        # 获取搜索参数
        search_params = {}
        for key, value in request.args.items():
            if value and key != 'page' and key != 'ajax' and key != 'include_stats':
                search_params[key] = value
                
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # 检查是否是AJAX请求
        is_ajax = request.args.get('ajax') == '1'
        include_stats = request.args.get('include_stats') == '1'
        
        # 构建查询条件
        query_conditions = []
        params = []
        
        if 'vehicle_id' in search_params:
            query_conditions.append("vehicle_id = %s")
            params.append(search_params['vehicle_id'])
            
        if 'plate_number' in search_params:
            query_conditions.append("plate_number LIKE %s")
            params.append(f"%{search_params['plate_number']}%")
            
        if 'log_type' in search_params:
            query_conditions.append("log_type = %s")
            params.append(search_params['log_type'])
            
        if 'created_at_start' in search_params:
            query_conditions.append("created_at >= %s")
            params.append(search_params['created_at_start'])
            
        if 'created_at_end' in search_params:
            query_conditions.append("created_at <= %s")
            params.append(search_params['created_at_end'])
        
        # 构建WHERE子句
        where_clause = ""
        if query_conditions:
            where_clause = "WHERE " + " AND ".join(query_conditions)
            
        # 获取总记录数
        count_query = f"""
        SELECT COUNT(*) AS count
        FROM vehicle_logs
        {where_clause}
        """
        
        count_result = BaseDAO.execute_query(count_query, tuple(params))
        total_count = count_result[0]['count'] if count_result else 0
        
        # 分页处理
        offset = (page - 1) * per_page
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        
        # 获取日志数据
        logs_query = f"""
        SELECT log_id, vehicle_id, plate_number, log_type, log_content, created_at
        FROM vehicle_logs
        {where_clause}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """
        
        query_params = params + [per_page, offset]
        logs = BaseDAO.execute_query(logs_query, tuple(query_params))
        
        # 获取各类型日志数量
        type_counts_query = """
        SELECT 
            log_type,
            COUNT(*) AS count
        FROM vehicle_logs
        GROUP BY log_type
        """
        
        type_counts_result = BaseDAO.execute_query(type_counts_query)
        
        # 整理日志类型统计
        log_type_counts = {
            'status_change': 0,  # 车辆救援
            'location_update': 0,  # 车辆添加 (原位置更新)
            'battery_change': 0,  # 车辆删除 (原电量变化)
            'maintenance': 0,
            'system_operation': 0
        }
        
        for item in type_counts_result:
            if item['log_type'] == '车辆救援':
                log_type_counts['status_change'] = item['count']
            elif item['log_type'] == '位置更新' or item['log_type'] == '车辆添加':
                log_type_counts['location_update'] += item['count']
            elif item['log_type'] == '电量变化' or item['log_type'] == '车辆删除':
                log_type_counts['battery_change'] += item['count']
            elif item['log_type'] == '维护记录':
                log_type_counts['maintenance'] = item['count']
            elif item['log_type'] == '系统操作':
                log_type_counts['system_operation'] = item['count']
        
        # 如果是AJAX请求，返回JSON数据
        if is_ajax:
            response_data = {
                'html': render_template('vehicles/_logs_table.html',
                                      logs=logs,
                                      current_page=page,
                                      total_pages=total_pages,
                                      total_count=total_count,
                                      offset=offset,
                                      per_page=per_page,
                                      search_params=search_params)
            }
            
            # 如果请求包含统计数据
            if include_stats:
                response_data['stats'] = log_type_counts
                
            return jsonify(response_data)
        
        # 正常页面请求
        return render_template('vehicles/logs.html',
                              logs=logs,
                              log_type_counts=log_type_counts,
                              search_params=search_params,
                              current_page=page,
                              total_pages=total_pages,
                              total_count=total_count,
                              offset=offset,
                              per_page=per_page)
    except Exception as e:
        print(f"加载车辆操作记录页面错误: {str(e)}")
        traceback.print_exc()
        
        # 如果是AJAX请求，返回错误信息
        if is_ajax:
            return jsonify({
                'html': f'<div class="alert alert-danger">加载数据出错: {str(e)}</div>',
                'stats': {} if include_stats else {}
            })
        
        # 直接返回500错误，避免使用不存在的error.html模板
        return render_template('vehicles/logs.html', 
                              logs=[],
                              log_type_counts={'status_change': 0, 'location_update': 0, 
                                              'battery_change': 0, 'maintenance': 0, 
                                              'system_operation': 0},
                              search_params={},
                              current_page=1,
                              total_pages=1,
                              total_count=0,
                              offset=0,
                              per_page=10,
                              error_message=f"加载车辆操作记录页面时出错: {str(e)}")

@vehicles_bp.route('/add', methods=['GET'])
def add_vehicle():
    """添加车辆页面"""
    try:
        return render_template('vehicles/add_vehicle.html')
    except Exception as e:
        print(f"加载添加车辆页面错误: {str(e)}")
        traceback.print_exc()
        return render_template('error.html', error_message=f"加载添加车辆页面时出错: {str(e)}")

@vehicles_bp.route('/add_vehicle_submit', methods=['POST'])
def add_vehicle_submit():
    """处理添加车辆表单提交"""
    try:
        # 从表单获取数据
        plate_number = request.form.get('plate_number')
        vin = request.form.get('vin')
        model = request.form.get('model')
        current_city = request.form.get('current_city')
        manufacture_date = request.form.get('manufacture_date')
        current_status = request.form.get('current_status')
        battery_level = request.form.get('battery_level')
        mileage = request.form.get('mileage')
        
        # 检查车牌号是否已存在
        check_query = "SELECT vehicle_id FROM vehicles WHERE plate_number = %s"
        result = BaseDAO.execute_query(check_query, (plate_number,))
        if result:
            flash_error(f"车牌号 {plate_number} 已存在")
            return redirect(url_for('vehicles.add_vehicle'))
            
        # 生成随机初始位置（在城市中心区域）
        import random
        location_x = random.randint(10, 20)  # 默认在左上角区域
        location_y = random.randint(10, 20)
        
        # 使用当前时间作为创建和更新时间
        from datetime import datetime
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建插入SQL语句 - 使用正确的字段名
        insert_query = """
        INSERT INTO vehicles (plate_number, vin, model, current_city, manufacture_date, current_status, 
                             battery_level, mileage, current_location_x, current_location_y, 
                             current_location_name, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # 执行插入操作
        params = (
            plate_number, vin, model, current_city, manufacture_date, current_status,
            battery_level, mileage, location_x, location_y,
            f"{current_city}市区", current_time, current_time
        )
        
        result = BaseDAO.execute_update(insert_query, params)
        
        if result:
            # 获取新插入车辆的ID
            get_id_query = "SELECT vehicle_id FROM vehicles WHERE plate_number = %s"
            id_result = BaseDAO.execute_query(get_id_query, (plate_number,))
            
            if id_result:
                vehicle_id = id_result[0]['vehicle_id']
                
                # 添加车辆操作日志
                try:
                    # 使用当前日期作为日志日期
                    from datetime import date
                    today = date.today().strftime('%Y-%m-%d')
                    
                    log_query = """
                    INSERT INTO vehicle_logs (vehicle_id, plate_number, log_type, log_content, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    
                    log_params = (
                        vehicle_id, plate_number, '添加车辆',
                        f"添加车辆: {plate_number}, 型号: {model}, 城市: {current_city}",
                        current_time
                    )
                    
                    BaseDAO.execute_update(log_query, log_params)
                    
                    # 添加车辆支出记录
                    try:
                        # 获取车型价格
                        from app.config.vehicle_params import get_param, get_city_vehicle_price_factor
                        
                        # 根据型号获取价格参数
                        model_key = model.replace('-', '_')
                        price_key = f"{model_key}_PRICE"
                        
                        try:
                            vehicle_price = get_param(price_key)
                            
                            # 获取城市车辆购置价格系数
                            city_factor = 1.0  # 默认系数为1.0
                            try:
                                city_factor = get_city_vehicle_price_factor(current_city)
                                print(f"城市 {current_city} 车辆购置价格系数: {city_factor}")
                            except Exception as e:
                                print(f"获取城市车辆购置价格系数失败: {e}，使用默认值1.0")
                                traceback.print_exc()
                            
                            # 应用城市价格系数
                            vehicle_price = float(vehicle_price) * city_factor
                            
                            # 导入ExpenseDAO
                            from app.dao.expense_dao import ExpenseDAO
                            
                            # 创建费用描述
                            expense_description = f"购置车辆 {plate_number}，型号: {model}，城市: {current_city}, 城市价格系数: {city_factor:.2f}"
                            
                            expense_id = ExpenseDAO.add_expense(
                                amount=float(vehicle_price),
                                expense_type='车辆支出',
                                vehicle_id=vehicle_id,
                                date=today,
                                description=expense_description
                            )
                            print(f"添加车辆支出记录成功，支出ID: {expense_id}")
                        except Exception as e:
                            print(f"未找到车型 {model} 的价格信息，跳过添加支出记录: {e}")
                            flash_warning(f"车辆添加成功，但未能记录车辆购置费用：未找到车型价格信息")
                    except Exception as expense_error:
                        print(f"添加车辆支出记录失败: {str(expense_error)}")
                        traceback.print_exc()
                        flash_warning(f"车辆添加成功，但记录支出失败: {str(expense_error)}")
                        
                except Exception as log_error:
                    print(f"记录车辆添加日志失败: {str(log_error)}")
                    traceback.print_exc()
                    flash_warning(f"车辆添加成功，但记录日志失败: {str(log_error)}")
            else:
                print("车辆添加失败，未能获取车辆ID")
                flash_warning("车辆信息已提交，但获取车辆ID失败")
        
        # 添加成功，使用flash_add_success显示成功消息
        flash_add_success("车辆", plate_number)
        return redirect(url_for('vehicles.index'))
        
    except Exception as e:
        print(f"添加车辆错误: {str(e)}")
        traceback.print_exc()
        flash_error(f'添加车辆失败: {str(e)}')
        return redirect(url_for('vehicles.add_vehicle'))

@vehicles_bp.route('/add_charging_station', methods=['GET'])
def add_charging_station():
    """添加充电站页面"""
    try:
        # 直接从数据库获取充电站基础成本和可变成本参数
        from app.dao.base_dao import BaseDAO
        
        # 获取充电站基础成本
        base_cost_query = "SELECT param_value FROM system_parameters WHERE param_key = 'CHARGING_STATION_BASE_COST'"
        base_cost_result = BaseDAO.execute_query(base_cost_query)
        base_cost = float(base_cost_result[0]['param_value']) if base_cost_result else 250000.0
        
        # 获取充电站可变成本
        variable_cost_query = "SELECT param_value FROM system_parameters WHERE param_key = 'CHARGING_STATION_VARIABLE_COST'"
        variable_cost_result = BaseDAO.execute_query(variable_cost_query)
        variable_cost = float(variable_cost_result[0]['param_value']) if variable_cost_result else 35000.0
        
        
        return render_template(
            'vehicles/add_charging_station.html',
            base_cost=base_cost,
            variable_cost=variable_cost
        )
    except Exception as e:
        print(f"加载添加充电站页面错误: {str(e)}")
        traceback.print_exc()
        return render_template('error.html', error_message=f"加载添加充电站页面时出错: {str(e)}")

@vehicles_bp.route('/add_charging_station_submit', methods=['POST'])
def add_charging_station_submit():
    """处理添加充电站表单提交"""
    try:
        # 获取表单数据
        station_code = request.form['station_code']
        city_code = request.form['city_code']
        max_capacity = request.form['max_capacity']
        last_maintenance_date = request.form.get('last_maintenance_date', '')
        location_x = request.form.get('location_x', '')
        location_y = request.form.get('location_y', '')
        
        # 验证必填字段
        if not all([station_code, city_code, max_capacity]):
            flash_error('请填写所有必填字段')
            return redirect(url_for('vehicles.add_charging_station'))
        
        # 检查充电站编号是否已存在
        from app.dao.charging_station_dao import ChargingStationDAO
        if ChargingStationDAO.check_station_code_exists(station_code):
            flash_error(f"充电站编号 '{station_code}' 已存在")
            return redirect(url_for('vehicles.add_charging_station'))
        
        # 准备充电站数据
        station_data = {
            'station_code': station_code,
            'city_code': city_code,
            'max_capacity': int(max_capacity)
        }
        
        # 添加可选字段
        if last_maintenance_date:
            station_data['last_maintenance_date'] = last_maintenance_date
        if location_x and location_y:
            station_data['location_x'] = float(location_x)
            station_data['location_y'] = float(location_y)
        
        # 设置初始值
        station_data['available_ports'] = int(max_capacity)  # 初始可用端口等于最大容量
        station_data['charging_count'] = 0  # 初始充电车辆数为0
        
        # 添加充电站
        station_id = ChargingStationDAO.add_charging_station(station_data)
        
        if not station_id:
            flash_error('添加充电站失败')
            return redirect(url_for('vehicles.add_charging_station'))
        
        # 如果充电站添加成功但无法获取ID，发出警告
        if station_id == -1:
            flash_warning(f'充电站已添加，但无法获取ID')
            return redirect(url_for('vehicles.index'))
        
        # 计算并添加充电站建设支出
        try:
            from datetime import date
            current_date = date.today().strftime('%Y-%m-%d')
            
            # 从参数配置获取成本数据
            from app.config.vehicle_params import get_param
            
            # 获取城市充电站成本系数
            from app.config.vehicle_params import get_city_charging_price_factor
            city_factor = get_city_charging_price_factor(city_code)
            
            # 计算充电站基础成本
            base_cost = float(get_param('CHARGING_STATION_BASE_COST', 250000.0))
            
            # 计算容量相关成本
            variable_cost = float(get_param('CHARGING_STATION_VARIABLE_COST', 35000.0))
            capacity_cost = int(max_capacity) * variable_cost
            
            # 应用城市系数
            total_cost = (base_cost + capacity_cost) * city_factor
            
            # 添加支出记录
            from app.dao.expense_dao import ExpenseDAO
            expense_description = f"建设充电站 {station_code}，城市: {city_code}, 容量: {max_capacity}，城市成本系数: {city_factor:.2f}"
            expense_id = ExpenseDAO.add_expense(
                amount=total_cost,
                expense_type='充电站支出',
                charging_station_id=station_id,
                date=current_date,
                description=expense_description
            )
            
            if expense_id:
                flash_success(f'成功添加充电站，编号: {station_code}，并记录支出金额: {total_cost:.2f}元')
            else:
                flash_warning(f'充电站已添加，但记录支出失败')
                
            return redirect(url_for('vehicles.index'))
            
        except Exception as e:
            print(f"添加充电站支出记录错误: {str(e)}")
            traceback.print_exc()
            flash_warning(f'充电站已添加，但添加支出记录失败: {str(e)}')
            return redirect(url_for('vehicles.index'))
        
    except Exception as e:
        print(f"添加充电站错误: {str(e)}")
        traceback.print_exc()
        flash_error(f'添加充电站时出错: {str(e)}')
        return redirect(url_for('vehicles.add_charging_station'))

@vehicles_bp.route('/api/log_details/<int:log_id>')
def get_log_details(log_id):
    """获取日志详情"""
    try:
        # 获取日志详情
        query = """
        SELECT log_id, vehicle_id, plate_number, log_type, log_content, created_at
        FROM vehicle_logs
        WHERE log_id = %s
        """
        
        result = BaseDAO.execute_query(query, (log_id,))
        
        if not result:
            return jsonify({
                'status': 'error',
                'message': f'找不到ID为{log_id}的日志记录'
            }), 404
        
        log = result[0]
        
        # 格式化日期时间
        if 'created_at' in log and log['created_at']:
            if isinstance(log['created_at'], str):
                log['created_at'] = log['created_at']
            else:
                log['created_at'] = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'status': 'success',
            'data': log
        })
    except Exception as e:
        print(f"获取日志详情错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取日志详情失败: {str(e)}'
        }), 500 

@vehicles_bp.route('/api/delete_log/<int:log_id>', methods=['POST'])
def delete_log(log_id):
    """删除指定ID的日志记录"""
    try:
        # 验证日志是否存在
        check_query = "SELECT log_id FROM vehicle_logs WHERE log_id = %s"
        log = BaseDAO.execute_query(check_query, (log_id,))
        
        if not log:
            return jsonify({
                'status': 'error',
                'message': f'找不到ID为{log_id}的日志记录'
            }), 404
        
        # 执行删除操作
        delete_query = "DELETE FROM vehicle_logs WHERE log_id = %s"
        result = BaseDAO.execute_update(delete_query, (log_id,))
        
        if result > 0:
            return jsonify({
                'status': 'success',
                'message': '日志记录已成功删除',
                'data': {
                    'log_id': log_id
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '删除日志记录失败'
            }), 500
            
    except Exception as e:
        print(f"删除日志记录错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'删除日志记录时发生错误: {str(e)}'
        }), 500 

@vehicles_bp.route('/data_analysis')
def data_analysis():
    """车辆数据分析页面"""
    try:
        # 查询总车辆数
        total_count_query = "SELECT COUNT(*) as count FROM vehicles"
        total_count_result = VehicleDAO.execute_query(total_count_query)
        total_vehicles = total_count_result[0]['count'] if total_count_result else 0
        
        # 获取状态统计
        status_query = """
        SELECT 
            current_status, COUNT(*) as count
        FROM 
            vehicles
        GROUP BY current_status
        """
        
        status_counts = {}
        status_results = VehicleDAO.execute_query(status_query)
        status_counts = {row['current_status']: row['count'] for row in status_results}
        
        idle_vehicles = status_counts.get('空闲中', 0)
        busy_vehicles = status_counts.get('运行中', 0)
        charging_vehicles = status_counts.get('充电中', 0)
        low_battery_vehicles = status_counts.get('电量不足', 0)
        maintenance_vehicles = status_counts.get('维护中', 0)

        # 获取车辆地理分布数据
        vehicle_geo_query = """
        SELECT 
            operating_city as name, 
            COUNT(*) as value 
        FROM 
            vehicles 
        GROUP BY 
            operating_city
        """
        vehicle_geo_data = VehicleDAO.execute_query(vehicle_geo_query)

        # 获取充电站地理分布数据
        station_geo_query = """
        SELECT 
            city_code as name, 
            COUNT(*) as value 
        FROM 
            charging_stations 
        GROUP BY 
            city_code
        """
        station_geo_data = VehicleDAO.execute_query(station_geo_query)

        # 获取各城市车辆数量随时间变化数据
        city_vehicle_trend_data = get_city_vehicle_trend_data()
        
        # 获取各车型数量随时间变化数据
        model_trend_data = get_model_trend_data()
        
        # 生成车辆状态分布数据
        status_data = {
            'labels': ['空闲中', '运行中', '充电中', '电量不足', '维护中', '其他'],
            'datasets': [{
                'data': [idle_vehicles, busy_vehicles, charging_vehicles, low_battery_vehicles, maintenance_vehicles, 
                        total_vehicles - (idle_vehicles + busy_vehicles + charging_vehicles + low_battery_vehicles + maintenance_vehicles)],
                'backgroundColor': ['#28a745', '#007bff', '#17a2b8', '#dc3545', '#ffc107', '#6c757d']
            }]
        }
        
        # 省份名称映射（简称到全称）
        province_name_map = {
            '北京': '北京市',
            '天津': '天津市',
            '上海': '上海市',
            '重庆': '重庆市',
            '河北': '河北省',
            '山西': '山西省',
            '辽宁': '辽宁省',
            '吉林': '吉林省',
            '黑龙江': '黑龙江省',
            '江苏': '江苏省',
            '浙江': '浙江省',
            '安徽': '安徽省',
            '福建': '福建省',
            '江西': '江西省',
            '山东': '山东省',
            '河南': '河南省',
            '湖北': '湖北省',
            '湖南': '湖南省',
            '广东': '广东省',
            '海南': '海南省',
            '四川': '四川省',
            '贵州': '贵州省',
            '云南': '云南省',
            '陕西': '陕西省',
            '甘肃': '甘肃省',
            '青海': '青海省',
            '台湾': '台湾省',
            '内蒙古': '内蒙古自治区',
            '广西': '广西壮族自治区',
            '西藏': '西藏自治区',
            '宁夏': '宁夏回族自治区',
            '新疆': '新疆维吾尔自治区',
            '香港': '香港特别行政区',
            '澳门': '澳门特别行政区',
            # 添加城市映射
            '上海市': '上海市',
            '北京市': '北京市',
            '广州市': '广东省',
            '深圳市': '广东省',
            '杭州市': '浙江省',
            '南京市': '江苏省',
            '成都市': '四川省',
            '重庆市': '重庆市',
            '武汉市': '湖北省',
            '西安市': '陕西省',
            '沈阳市': '辽宁省'
        }
        
        # 处理车辆地理分布数据
        vehicle_geo_formatted = []
        for item in vehicle_geo_data:
            province_name = item.get('name', '')
            mapped_name = province_name_map.get(province_name, province_name)
            vehicle_geo_formatted.append({
                'name': mapped_name,
                'value': int(item.get('value', 0))
            })
        
        # 处理充电站地理分布数据
        station_geo_formatted = []
        for item in station_geo_data:
            province_name = item.get('name', '')
            mapped_name = province_name_map.get(province_name, province_name)
            station_geo_formatted.append({
                'name': mapped_name,
                'value': int(item.get('value', 0))
            })
        
        # 查询真实的车型分布数据
        model_query = """
        SELECT 
            model, COUNT(*) as count 
        FROM 
            vehicles 
        GROUP BY 
            model 
        ORDER BY 
            count DESC
        """
        model_results = VehicleDAO.execute_query(model_query)
        
        models = [row['model'] for row in model_results]
        model_counts = [int(row['count']) for row in model_results]
        
        model_data = {
            'labels': models,
            'datasets': [{
                'data': model_counts,
                'backgroundColor': [
                    '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', 
                    '#fd7e14', '#6f42c1', '#20c997', '#6610f2', '#e83e8c', '#28a745'
                ]
            }]
        }
        
        # 查询不同订单数量范围的车辆数量
        orders_query = """
        SELECT 
            CASE 
                WHEN total_orders BETWEEN 0 AND 10 THEN '0-10单'
                WHEN total_orders BETWEEN 11 AND 50 THEN '11-50单'
                WHEN total_orders BETWEEN 51 AND 100 THEN '51-100单'
                WHEN total_orders BETWEEN 101 AND 200 THEN '101-200单'
                ELSE '200单以上'
            END AS order_range,
            COUNT(*) AS vehicle_count
        FROM 
            vehicles
        GROUP BY 
            order_range
        ORDER BY 
            CASE order_range
                WHEN '0-10单' THEN 1
                WHEN '11-50单' THEN 2
                WHEN '51-100单' THEN 3
                WHEN '101-200单' THEN 4
                WHEN '200单以上' THEN 5
            END
        """
        orders_results = VehicleDAO.execute_query(orders_query)
        
        # 处理订单范围数据
        order_ranges = ['0-10单', '11-50单', '51-100单', '101-200单', '200单以上']
        vehicle_counts = []
        
        # 确保所有范围都存在
        for order_range in order_ranges:
            found = False
            for row in orders_results:
                if row['order_range'] == order_range:
                    vehicle_counts.append(int(row['vehicle_count']))
                    found = True
                    break
            if not found:
                vehicle_counts.append(0)  # 该范围没有车辆
        
        completed_orders_data = {
            'labels': order_ranges,
            'datasets': [{
                'label': '车辆数量',
                'data': vehicle_counts,
                'backgroundColor': [
                    '#4e73df', '#36b9cc', '#1cc88a', '#f6c23e', '#e74a3b'
                ]
            }]
        }
        
        # 查询真实的车辆评价分布数据，处理小数位评分
        rating_query = """
        SELECT 
            CASE 
                WHEN rating >= 5 THEN '5星'
                WHEN rating >= 4 AND rating < 5 THEN '4-4.9星'
                WHEN rating >= 3 AND rating < 4 THEN '3-3.9星'
                WHEN rating >= 2 AND rating < 3 THEN '2-2.9星'
                WHEN rating >= 1 AND rating < 2 THEN '1-1.9星'
                ELSE '未评价'
            END AS rating_range,
            COUNT(*) AS vehicle_count
        FROM 
            vehicles
        WHERE 
            rating IS NOT NULL
        GROUP BY 
            rating_range
        ORDER BY 
            CASE rating_range
                WHEN '5星' THEN 1
                WHEN '4-4.9星' THEN 2
                WHEN '3-3.9星' THEN 3
                WHEN '2-2.9星' THEN 4
                WHEN '1-1.9星' THEN 5
                ELSE 6
            END
        """
        rating_results = VehicleDAO.execute_query(rating_query)
        
        # 处理评分范围数据
        rating_ranges = ['5星', '4-4.9星', '3-3.9星', '2-2.9星', '1-1.9星']
        rating_counts = []
        
        # 确保所有范围都存在
        for rating_range in rating_ranges:
            found = False
            for row in rating_results:
                if row['rating_range'] == rating_range:
                    rating_counts.append(int(row['vehicle_count']))
                    found = True
                    break
            if not found:
                rating_counts.append(0)  # 该范围没有车辆
        
        rating_distribution_data = {
            'labels': rating_ranges,
            'datasets': [{
                'label': '车辆数量',
                'data': rating_counts,
                'backgroundColor': [
                    '#28a745', '#20c997', '#ffc107', '#fd7e14', '#dc3545'
                ]
            }]
        }
        
        # 查询真实的累计距离分布数据
        mileage_query = """
        SELECT 
            CASE 
                WHEN mileage < 10000 THEN '0-1万km'
                WHEN mileage BETWEEN 10000 AND 19999 THEN '1-2万km'
                WHEN mileage BETWEEN 20000 AND 49999 THEN '2-5万km'
                WHEN mileage BETWEEN 50000 AND 99999 THEN '5-10万km'
                ELSE '10万km以上'
            END AS mileage_range,
            COUNT(*) AS vehicle_count
        FROM 
            vehicles
        WHERE 
            mileage IS NOT NULL
        GROUP BY 
            mileage_range
        ORDER BY 
            CASE mileage_range
                WHEN '0-1万km' THEN 1
                WHEN '1-2万km' THEN 2
                WHEN '2-5万km' THEN 3
                WHEN '5-10万km' THEN 4
                WHEN '10万km以上' THEN 5
            END
        """
        mileage_results = VehicleDAO.execute_query(mileage_query)
        
        # 处理里程范围数据
        mileage_ranges = ['0-1万km', '1-2万km', '2-5万km', '5-10万km', '10万km以上']
        mileage_counts = []
        
        # 确保所有范围都存在
        for mileage_range in mileage_ranges:
            found = False
            for row in mileage_results:
                if row['mileage_range'] == mileage_range:
                    mileage_counts.append(int(row['vehicle_count']))
                    found = True
                    break
            if not found:
                mileage_counts.append(0)  # 该范围没有车辆
        
        mileage_distribution_data = {
            'labels': mileage_ranges,
            'datasets': [{
                'label': '车辆数量',
                'data': mileage_counts,
                'backgroundColor': [
                    '#4e73df', '#36b9cc', '#1cc88a', '#f6c23e', '#e74a3b'
                ]
            }]
        }
        
        # 将所有图表数据封装成JSON字符串传递给前端
        charts_data = {
            'status_data': status_data,
            'vehicle_geo_data': vehicle_geo_formatted,
            'station_geo_data': station_geo_formatted,
            'model_data': model_data,
            'completed_orders_data': completed_orders_data,
            'rating_distribution_data': rating_distribution_data,
            'mileage_distribution_data': mileage_distribution_data,
            'city_vehicle_trend_data': city_vehicle_trend_data,
            'model_trend_data': model_trend_data
        }
        
        charts_json = json.dumps(charts_data)
        
        return render_template('vehicles/data_analysis.html', 
                            charts_json=charts_json,
                            total_vehicles=total_vehicles,
                            idle_vehicles=idle_vehicles,
                            busy_vehicles=busy_vehicles,
                            charging_vehicles=charging_vehicles,
                            low_battery_vehicles=low_battery_vehicles,
                            maintenance_vehicles=maintenance_vehicles)
    except Exception as e:
        # 记录错误详情而不是使用模拟数据
        print(f"数据分析页面出错: {e}")
        traceback.print_exc()
        # 直接向用户显示错误信息
        flash(f"数据查询出错: {str(e)}", "danger")
        return redirect(url_for('vehicles.index'))

def get_city_vehicle_trend_data():
    """获取各城市车辆数量随时间变化的数据（累计总量）"""
    # 查询数据库获取所有车辆数据
    vehicle_query = """
    SELECT 
        operating_city,
        IFNULL(registration_date, created_at) as valid_date
    FROM 
        vehicles
    ORDER BY 
        IFNULL(registration_date, created_at)
    """
    
    vehicle_results = VehicleDAO.execute_query(vehicle_query)
    
    # 所有支持的城市列表
    main_cities = ['沈阳市','上海市','北京市','广州市','深圳市','杭州市','南京市','成都市','重庆市','武汉市','西安市']
    
    # 将日期转换为月份格式
    for row in vehicle_results:
        if row['valid_date']:
            # 将datetime转为字符串格式YYYY-MM
            date_obj = row['valid_date']
            if isinstance(date_obj, str):
                # 如果已经是字符串，尝试解析为datetime
                try:
                    date_obj = datetime.strptime(date_obj, '%Y-%m-%d')
                except ValueError:
                    try:
                        date_obj = datetime.strptime(date_obj, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        # 如果无法解析，使用当前日期
                        date_obj = datetime.now()
            row['month'] = date_obj.strftime('%Y-%m')
    
    # 获取所有月份
    all_months = []
    for row in vehicle_results:
        if 'month' in row and row['month'] not in all_months:
            all_months.append(row['month'])
    
    # 按时间排序
    all_months.sort()
    
    # 使用所有月份，不限制只显示最近12个月
    # if len(all_months) > 12:
    #     all_months = all_months[-12:]  # 这行已被注释掉，显示所有月份
    
    # 初始化城市计数器
    city_counts = {city: [0] * len(all_months) for city in main_cities}
    
    # 计算累计总量
    # 首先建立月份到索引的映射
    month_to_idx = {month: idx for idx, month in enumerate(all_months)}
    
    # 按时间顺序遍历每辆车
    for row in vehicle_results:
        if 'month' not in row:
            continue
        
        month = row['month']
        city = row.get('operating_city')
        
        # 如果不在我们关注的月份范围内或者城市为空，跳过
        if month not in month_to_idx or not city:
            continue
            
        # 如果城市不在主要城市列表中，但有值，添加到"其他"类别
        if city not in main_cities:
            continue
            
        idx = month_to_idx[month]
        
        # 更新当前月份及以后所有月份的计数
        for i in range(idx, len(all_months)):
            city_counts[city][i] += 1
    
    # 格式化月份标签
    month_labels = []
    for month in all_months:
        year, month_num = month.split('-')
        month_labels.append(f"{year[-2:]}年{month_num}月")  # 例如：23年01月
    
    # 生成数据集
    datasets = []
    colors = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#fd7e14', '#6f42c1', '#20c997', '#6610f2', '#e83e8c', '#28a745']
    
    for i, city in enumerate(main_cities):
        if any(count > 0 for count in city_counts[city]):  # 只添加有数据的城市
            datasets.append({
                'label': city,
                'data': city_counts[city],
                'borderColor': colors[i % len(colors)],
                'backgroundColor': 'transparent',
                'tension': 0.4  # 曲线平滑度
            })
    
    # 打印最早和最晚的月份，以及总车辆数量，用于调试
    if all_months:
        earliest_month = all_months[0]
        latest_month = all_months[-1]
        total_vehicles = sum(city_counts[city][-1] for city in main_cities if city_counts[city])
        print(f"城市车辆趋势图：从 {earliest_month} 到 {latest_month}，共 {len(all_months)} 个月，总计 {total_vehicles} 辆车")
    
    return {
        'labels': month_labels,
        'datasets': datasets
    }

def get_model_trend_data():
    """获取各车型数量随时间变化的数据（累计总量）"""
    # 查询数据库获取所有车辆数据
    vehicle_query = """
    SELECT 
        model,
        IFNULL(registration_date, created_at) as valid_date
    FROM 
        vehicles
    ORDER BY 
        IFNULL(registration_date, created_at)
    """
    
    vehicle_results = VehicleDAO.execute_query(vehicle_query)
    
    # 将日期转换为月份格式
    for row in vehicle_results:
        if row['valid_date']:
            # 将datetime转为字符串格式YYYY-MM
            date_obj = row['valid_date']
            if isinstance(date_obj, str):
                # 如果已经是字符串，尝试解析为datetime
                try:
                    date_obj = datetime.strptime(date_obj, '%Y-%m-%d')
                except ValueError:
                    try:
                        date_obj = datetime.strptime(date_obj, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        # 如果无法解析，使用当前日期
                        date_obj = datetime.now()
            row['month'] = date_obj.strftime('%Y-%m')
    
    # 获取所有月份和车型
    all_months = []
    all_models = set()
    
    for row in vehicle_results:
        if 'month' in row and row['month'] not in all_months:
            all_months.append(row['month'])
        if row.get('model'):
            all_models.add(row['model'])
    
    # 按时间排序
    all_months.sort()
    
    # 使用所有月份，不限制只显示最近12个月
    # if len(all_months) > 12:
    #     all_months = all_months[-12:]  # 这行已被注释掉，显示所有月份
    
    # 将模型列表转换为列表并排序
    all_models = list(all_models)
    
    # 初始化车型计数器
    model_counts = {model: [0] * len(all_months) for model in all_models}
    
    # 计算累计总量
    # 首先建立月份到索引的映射
    month_to_idx = {month: idx for idx, month in enumerate(all_months)}
    
    # 按时间顺序遍历每辆车
    for row in vehicle_results:
        if 'month' not in row:
            continue
        
        month = row['month']
        model = row.get('model')
        
        # 如果月份不在范围内或模型为空，跳过
        if month not in month_to_idx or not model:
            continue
            
        idx = month_to_idx[month]
        
        # 更新当前月份及以后所有月份的计数
        for i in range(idx, len(all_months)):
            model_counts[model][i] += 1
    
    # 格式化月份标签
    month_labels = []
    for month in all_months:
        year, month_num = month.split('-')
        month_labels.append(f"{year[-2:]}年{month_num}月")  # 例如：23年01月
    
    # 生成数据集
    datasets = []
    colors = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#fd7e14', '#6f42c1', '#20c997', '#6610f2', '#e83e8c', '#28a745']
    
    # 计算每种车型的最终累计总数并按数量排序
    model_totals = {model: counts[-1] if counts else 0 for model, counts in model_counts.items()}
    sorted_models = sorted(all_models, key=lambda x: model_totals.get(x, 0), reverse=True)
    
    # 限制最多显示前10个车型
    display_models = sorted_models[:10] if len(sorted_models) > 10 else sorted_models
    
    # 打印最早和最晚的月份，以及总车辆数量，用于调试
    if all_months:
        earliest_month = all_months[0]
        latest_month = all_months[-1]
        total_vehicles = sum(model_counts[model][-1] for model in display_models if model_counts[model])
        print(f"车型趋势图：从 {earliest_month} 到 {latest_month}，共 {len(all_months)} 个月，展示了 {len(display_models)} 种车型，总计 {total_vehicles} 辆车")
    
    for i, model in enumerate(display_models):
        datasets.append({
            'label': model,
            'data': model_counts[model],
            'borderColor': colors[i % len(colors)],
            'backgroundColor': 'transparent',
            'tension': 0.4  # 曲线平滑度
        })
    
    return {
        'labels': month_labels,
        'datasets': datasets
    }

@vehicles_bp.route('/api/start_maintenance/<int:vehicle_id>', methods=['POST'])
def start_maintenance(vehicle_id):
    """
    开始车辆维护，将车辆状态设为'维护中'，添加日志记录
    """
    try:
        # 获取车辆信息
        vehicle = VehicleDAO.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            return jsonify({
                'status': 'error',
                'message': f'未找到ID为{vehicle_id}的车辆'
            }), 404
        
        # 如果当前状态已经是维护中，无需操作
        if vehicle['current_status'] == '维护中':
            return jsonify({
                'status': 'info',
                'message': f'车辆 {vehicle["plate_number"]} 已经处于维护中状态'
            })
        
        # 更新车辆状态为"维护中"
        success = VehicleDAO.update_vehicle_status(vehicle_id, '维护中')
        if not success:
            return jsonify({
                'status': 'error',
                'message': f'更新车辆状态失败'
            }), 500
        
        # 添加车辆操作日志
        log_content = f'车辆开始维护。变更前状态：{vehicle["current_status"]}，当前电量：{vehicle["battery_level"]}%'
        log_id = VehicleDAO.add_vehicle_log(
            vehicle_id, 
            vehicle['plate_number'], 
            '维护记录', 
            log_content
        )
        
        # 计算维护费用
        from app.config.vehicle_params import BASE_MAINTENANCE_COST, get_city_maintenance_factor
        
        # 获取车型维护费用系数
        vehicle_model = vehicle['model']
        model_maintenance_cost_factor = 1.0  # 默认值
        
        # 根据车型获取对应的维护费用系数
        if vehicle_model == 'Alpha X1':
            from app.config.vehicle_params import Alpha_X1_MAINTENANCE_COST
            model_maintenance_cost_factor = Alpha_X1_MAINTENANCE_COST
        elif vehicle_model == 'Alpha Nexus':
            from app.config.vehicle_params import Alpha_Nexus_MAINTENANCE_COST
            model_maintenance_cost_factor = Alpha_Nexus_MAINTENANCE_COST
        elif vehicle_model == 'Alpha Voyager':
            from app.config.vehicle_params import Alpha_Voyager_MAINTENANCE_COST
            model_maintenance_cost_factor = Alpha_Voyager_MAINTENANCE_COST
        elif vehicle_model == 'Nova S1':
            from app.config.vehicle_params import Nova_S1_MAINTENANCE_COST
            model_maintenance_cost_factor = Nova_S1_MAINTENANCE_COST
        elif vehicle_model == 'Nova Quantum':
            from app.config.vehicle_params import Nova_Quantum_MAINTENANCE_COST
            model_maintenance_cost_factor = Nova_Quantum_MAINTENANCE_COST
        elif vehicle_model == 'Nova Pulse':
            from app.config.vehicle_params import Nova_Pulse_MAINTENANCE_COST
            model_maintenance_cost_factor = Nova_Pulse_MAINTENANCE_COST
        elif vehicle_model == 'Neon 500':
            from app.config.vehicle_params import Neon_500_MAINTENANCE_COST
            model_maintenance_cost_factor = Neon_500_MAINTENANCE_COST
        elif vehicle_model == 'Neon Zero':
            from app.config.vehicle_params import Neon_Zero_MAINTENANCE_COST
            model_maintenance_cost_factor = Neon_Zero_MAINTENANCE_COST
        
        # 获取城市维护系数
        city_maintenance_factor = get_city_maintenance_factor(vehicle.get('current_city'))
        
        # 计算最终维护费用 = 基础维护费用 * 车型维护系数 * 城市维护系数
        maintenance_cost = BASE_MAINTENANCE_COST * model_maintenance_cost_factor * city_maintenance_factor
        maintenance_cost = round(maintenance_cost, 2)  # 四舍五入保留两位小数
        
        # 记录维护支出
        today = datetime.now().strftime('%Y-%m-%d')
        expense_description = f'车辆维护费用 - ID:{vehicle_id}, 车牌:{vehicle["plate_number"]}, 型号:{vehicle_model}, 基础费用:{BASE_MAINTENANCE_COST}, 车型系数:{model_maintenance_cost_factor}, 城市系数:{city_maintenance_factor}, 城市:{vehicle.get("current_city", "未知")}, 总金额:{maintenance_cost}'
        expense_id = ExpenseDAO.add_expense(
            amount=maintenance_cost,  # 按公式计算的维护费用
            expense_type='车辆支出',
            vehicle_id=vehicle_id,
            date=today,
            description=expense_description
        )
        
        return jsonify({
            'status': 'success',
            'message': f'车辆 {vehicle["plate_number"]} 已开始维护',
            'log_id': log_id,
            'expense_id': expense_id
        })
    except Exception as e:
        print(f"开始维护车辆错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'服务器错误: {str(e)}'
        }), 500

@vehicles_bp.route('/api/end_maintenance/<int:vehicle_id>', methods=['POST'])
def end_maintenance(vehicle_id):
    """
    结束车辆维护，将车辆状态设为'空闲中'，电量设为100%，添加日志记录
    """
    try:
        # 获取车辆信息
        vehicle = VehicleDAO.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            return jsonify({
                'status': 'error',
                'message': f'未找到ID为{vehicle_id}的车辆'
            }), 404
        
        # 如果当前状态不是维护中，返回错误
        if vehicle['current_status'] != '维护中':
            return jsonify({
                'status': 'error',
                'message': f'车辆 {vehicle["plate_number"]} 不在维护状态，无法结束维护'
            }), 400
        
        # 更新车辆状态为"空闲中"
        success = VehicleDAO.update_vehicle_status(vehicle_id, '空闲中')
        if not success:
            return jsonify({
                'status': 'error',
                'message': f'更新车辆状态失败'
            }), 500
        
        # 更新车辆电量为100%
        battery_success = VehicleDAO.update_vehicle_battery(vehicle_id, 100)
        if not battery_success:
            print(f"警告: 车辆 {vehicle_id} 电量更新失败")
        
        # 更新车辆最后维护日期
        today = datetime.now().date()
        vehicle_data = {
            'last_maintenance_date': today.strftime('%Y-%m-%d')
        }
        VehicleDAO.update_vehicle(vehicle_id, vehicle_data)
        
        # 添加车辆操作日志
        log_content = f'车辆完成维护。维护后状态：空闲中，电量已充满至100%，维护日期已更新为{today}'
        log_id = VehicleDAO.add_vehicle_log(
            vehicle_id, 
            vehicle['plate_number'], 
            '维护记录', 
            log_content
        )
        
        return jsonify({
            'status': 'success',
            'message': f'车辆 {vehicle["plate_number"]} 已完成维护，状态已设为空闲，电量已充满',
            'log_id': log_id
        })
    except Exception as e:
        print(f"结束维护车辆错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'服务器错误: {str(e)}'
        }), 500