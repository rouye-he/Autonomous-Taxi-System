import traceback
from datetime import datetime
import random
from app.dao.base_dao import BaseDAO

class VehicleDAO(BaseDAO):
    """车辆数据访问对象，封装所有车辆相关的数据库操作"""
    
    @staticmethod
    def get_all_vehicles(page=1, per_page=10):
        """获取所有车辆数据"""
        try:
            # 计算总记录数
            count_query = "SELECT COUNT(*) as total FROM vehicles"
            count_result = BaseDAO.execute_query(count_query)
            total_count = count_result[0]['total'] if count_result else 0
            
            # 计算分页参数
            offset = (page - 1) * per_page
            
            # 查询当前页的车辆数据
            vehicles_query = """
            SELECT 
                vehicle_id, plate_number, vin, model, current_status, battery_level,
                mileage, current_location_name, current_city, operating_city, last_maintenance_date, is_available,
                manufacture_date, rating, total_orders
            FROM 
                vehicles
            ORDER BY vehicle_id
            LIMIT %s OFFSET %s
            """
            
            vehicles = BaseDAO.execute_query(vehicles_query, (per_page, offset))
            
            # 处理日期格式和其他格式化
            for vehicle in vehicles:
                VehicleDAO._format_vehicle_data(vehicle)
            
            # 获取状态统计
            status_query = """
            SELECT 
                current_status, COUNT(*) as count
            FROM 
                vehicles
            GROUP BY current_status
            """
            
            status_results = BaseDAO.execute_query(status_query)
            status_counts = {row['current_status']: row['count'] for row in status_results}
            
            idle_count = status_counts.get('空闲中', 0)
            busy_count = status_counts.get('运行中', 0)
            charging_count = status_counts.get('充电中', 0)
            low_battery_count = status_counts.get('电量不足', 0)
            maintenance_count = status_counts.get('维护中', 0)
            
            return {
                'vehicles': vehicles,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page if total_count > 0 else 1,
                'current_page': page,
                'per_page': per_page,
                'status_counts': {
                    'all': total_count,
                    'idle': idle_count,
                    'busy': busy_count,
                    'charging': charging_count,
                    'low_battery': low_battery_count,
                    'maintenance': maintenance_count
                }
            }
        except Exception as e:
            print(f"获取所有车辆数据错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def get_vehicles_by_criteria(search_params, page=1, per_page=10):
        """根据搜索条件获取车辆数据"""
        try:
            # 构建SQL查询条件
            conditions = []
            params = []
            
            # 处理各种搜索条件
            if 'vehicle_id' in search_params and search_params['vehicle_id']:
                conditions.append("vehicle_id = %s")
                params.append(search_params['vehicle_id'])
            
            if 'plate_number' in search_params and search_params['plate_number']:
                conditions.append("plate_number LIKE %s")
                params.append(f"%{search_params['plate_number']}%")
            
            if 'vin' in search_params and search_params['vin']:
                conditions.append("vin LIKE %s")
                params.append(f"%{search_params['vin']}%")
            
            if 'model' in search_params and search_params['model']:
                conditions.append("model = %s")
                params.append(search_params['model'])
            
            if 'current_city' in search_params and search_params['current_city']:
                conditions.append("operating_city = %s")
                params.append(search_params['current_city'])
            
            if 'current_status' in search_params and search_params['current_status']:
                conditions.append("current_status = %s")
                params.append(search_params['current_status'])
            
            if 'battery_level_min' in search_params and search_params['battery_level_min']:
                conditions.append("battery_level >= %s")
                params.append(search_params['battery_level_min'])
            
            if 'battery_level_max' in search_params and search_params['battery_level_max']:
                conditions.append("battery_level <= %s")
                params.append(search_params['battery_level_max'])
            
            if 'mileage_min' in search_params and search_params['mileage_min']:
                conditions.append("mileage >= %s")
                params.append(search_params['mileage_min'])
            
            if 'mileage_max' in search_params and search_params['mileage_max']:
                conditions.append("mileage <= %s")
                params.append(search_params['mileage_max'])
            
            if 'rating_min' in search_params and search_params['rating_min']:
                conditions.append("rating >= %s")
                params.append(search_params['rating_min'])
            
            if 'rating_max' in search_params and search_params['rating_max']:
                conditions.append("rating <= %s")
                params.append(search_params['rating_max'])
            
            if 'total_orders_min' in search_params and search_params['total_orders_min']:
                conditions.append("total_orders >= %s")
                params.append(search_params['total_orders_min'])
            
            if 'total_orders_max' in search_params and search_params['total_orders_max']:
                conditions.append("total_orders <= %s")
                params.append(search_params['total_orders_max'])
            
            if 'is_available' in search_params:
                conditions.append("is_available = %s")
                params.append(int(search_params['is_available']))
            
            if 'manufacture_date_start' in search_params and search_params['manufacture_date_start']:
                conditions.append("manufacture_date >= %s")
                params.append(search_params['manufacture_date_start'])
            
            if 'manufacture_date_end' in search_params and search_params['manufacture_date_end']:
                conditions.append("manufacture_date <= %s")
                params.append(search_params['manufacture_date_end'])
            
            if 'last_maintenance_date_start' in search_params and search_params['last_maintenance_date_start']:
                conditions.append("last_maintenance_date >= %s")
                params.append(search_params['last_maintenance_date_start'])
            
            if 'last_maintenance_date_end' in search_params and search_params['last_maintenance_date_end']:
                conditions.append("last_maintenance_date <= %s")
                params.append(search_params['last_maintenance_date_end'])
            
            # 构建WHERE子句
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            # 计算总记录数
            count_query = f"SELECT COUNT(*) as total FROM vehicles{where_clause}"
            count_result = BaseDAO.execute_query(count_query, params)
            total_count = count_result[0]['total'] if count_result else 0
            
            # 计算分页参数
            offset = (page - 1) * per_page
            
            # 查询当前页的车辆数据
            vehicles_query = f"""
            SELECT 
                vehicle_id, plate_number, vin, model, current_status, battery_level,
                mileage, current_location_name, current_city, operating_city, last_maintenance_date, is_available,
                manufacture_date, rating, total_orders
            FROM 
                vehicles
            {where_clause}
            ORDER BY vehicle_id
            LIMIT %s OFFSET %s
            """
            
            query_params = params.copy()
            query_params.extend([per_page, offset])
            vehicles = BaseDAO.execute_query(vehicles_query, query_params)
            
            # 处理日期格式和其他格式化
            for vehicle in vehicles:
                VehicleDAO._format_vehicle_data(vehicle)
            
            # 获取状态统计
            status_params = params.copy()
            status_query = f"""
            SELECT 
                current_status, COUNT(*) as count
            FROM 
                vehicles
            {where_clause}
            GROUP BY current_status
            """
            
            status_results = BaseDAO.execute_query(status_query, status_params)
            status_counts = {row['current_status']: row['count'] for row in status_results}
            
            idle_count = status_counts.get('空闲中', 0)
            busy_count = status_counts.get('运行中', 0)
            charging_count = status_counts.get('充电中', 0)
            low_battery_count = status_counts.get('电量不足', 0)
            maintenance_count = status_counts.get('维护中', 0)
            
            return {
                'vehicles': vehicles,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page if total_count > 0 else 1,
                'current_page': page,
                'per_page': per_page,
                'status_counts': {
                    'all': total_count,
                    'idle': idle_count,
                    'busy': busy_count,
                    'charging': charging_count,
                    'low_battery': low_battery_count,
                    'maintenance': maintenance_count
                }
            }
        except Exception as e:
            print(f"根据条件获取车辆数据错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def get_vehicle_by_id(vehicle_id):
        """根据ID获取车辆详情"""
        try:
            query = """
            SELECT 
                *
            FROM 
                vehicles
            WHERE 
                vehicle_id = %s
            """
            
            results = BaseDAO.execute_query(query, (vehicle_id,))
            
            if not results:
                return None
            
            vehicle = results[0]
            VehicleDAO._format_vehicle_data(vehicle)
            
            # 手动添加维护次数字段，默认设为0
            vehicle['maintenance_count'] = 0
            
            return vehicle
        except Exception as e:
            print(f"获取车辆详情错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def get_city_vehicles(city):
        """获取指定城市的车辆数据"""
        try:
            query = """
            SELECT 
                vehicle_id, plate_number, model, current_status, battery_level,
                mileage, current_location_x, current_location_y, current_location_name,
                current_city, operating_city, last_maintenance_date
            FROM vehicles 
            WHERE operating_city = %s OR %s = 'all'
            """
            
            vehicles = BaseDAO.execute_query(query, (city, city))
            
            # 处理车辆数据
            for vehicle in vehicles:
                VehicleDAO._format_vehicle_data(vehicle)
                
                # 确保经纬度坐标存在
                if not vehicle.get('current_location_x') or not vehicle.get('current_location_y'):
                    # 为不同城市的车辆分配不同区域的随机坐标
                    vehicle['current_location_x'] = random.randint(400, 600)
                    vehicle['current_location_y'] = random.randint(400, 600)
                
                # 添加模拟评分
                vehicle['rating'] = round(random.uniform(3.5, 5.0), 1)
            
            return vehicles
        except Exception as e:
            print(f"获取城市车辆数据错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def delete_vehicle(vehicle_id):
        """删除车辆"""
        try:
            # 检查车辆是否存在
            check_query = "SELECT vehicle_id FROM vehicles WHERE vehicle_id = %s"
            results = BaseDAO.execute_query(check_query, (vehicle_id,))
            
            if not results:
                return False
            
            # 删除车辆
            delete_query = "DELETE FROM vehicles WHERE vehicle_id = %s"
            affected_rows = BaseDAO.execute_update(delete_query, (vehicle_id,))
            
            return affected_rows > 0
        except Exception as e:
            print(f"删除车辆错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def update_vehicle(vehicle_id, vehicle_data):
        """更新车辆信息"""
        try:
            # 检查车辆是否存在
            check_query = "SELECT vehicle_id FROM vehicles WHERE vehicle_id = %s"
            results = BaseDAO.execute_query(check_query, (vehicle_id,))
            
            if not results:
                return False
            
            # 构建更新SQL语句
            update_query = "UPDATE vehicles SET "
            update_parts = []
            params = []
            
            # 动态添加需要更新的字段
            for key, value in vehicle_data.items():
                if value is not None:
                    update_parts.append(f"{key} = %s")
                    params.append(value)
            
            # 如果没有要更新的字段，直接返回
            if not update_parts:
                return True
            
            # 拼接SQL语句
            update_query += ", ".join(update_parts)
            update_query += " WHERE vehicle_id = %s"
            params.append(vehicle_id)
            
            # 执行更新
            affected_rows = BaseDAO.execute_update(update_query, params)
            
            return affected_rows > 0
        except Exception as e:
            print(f"更新车辆信息错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def update_vehicle_location(vehicle_id, location_data):
        """更新车辆位置信息"""
        try:
            location_name = location_data.get('location_name')
            location_x = location_data.get('location_x')
            location_y = location_data.get('location_y')
            city = location_data.get('city')
            
            # 构建更新语句
            update_query = "UPDATE vehicles SET current_location_name = %s"
            params = [location_name]
            
            # 动态添加其他字段
            if location_x is not None and location_y is not None:
                update_query += ", current_location_x = %s, current_location_y = %s"
                params.extend([location_x, location_y])
            
            if city:
                update_query += ", current_city = %s"
                params.append(city)
            
            update_query += " WHERE vehicle_id = %s"
            params.append(vehicle_id)
            
            # 执行更新
            affected_rows = BaseDAO.execute_update(update_query, params)
            
            return affected_rows > 0
        except Exception as e:
            print(f"更新车辆位置错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def batch_update_vehicle_locations(updates):
        """批量更新车辆位置信息"""
        try:
            if not updates or not isinstance(updates, list):
                return 0
            
            # 构建批量更新查询
            queries_and_params = []
            
            for update in updates:
                vehicle_id = update.get('vehicleId')
                location_name = update.get('locationName')
                x = update.get('x')
                y = update.get('y')
                city = update.get('city')
                battery = update.get('battery')
                
                if not vehicle_id or not location_name:
                    continue
                
                # 构建单个更新查询
                update_query = "UPDATE vehicles SET current_location_name = %s"
                params = [location_name]
                
                if x is not None and y is not None:
                    update_query += ", current_location_x = %s, current_location_y = %s"
                    params.extend([x, y])
                
                if city:
                    update_query += ", current_city = %s"
                    params.append(city)
                
                # 添加电池电量更新
                if battery is not None:
                    update_query += ", battery_level = %s"
                    params.append(battery)
                
                update_query += " WHERE vehicle_id = %s"
                params.append(vehicle_id)
                
                queries_and_params.append((update_query, params))
            
            # 执行批量更新事务
            if queries_and_params:
                results = BaseDAO.execute_transaction(queries_and_params)
                updated_count = sum(1 for count in results if count > 0)
                
                # 对于已更新的车辆检查是否有低电量情况
                for update in updates:
                    vehicle_id = update.get('vehicleId')
                    battery = update.get('battery')
                    if vehicle_id is not None and battery is not None and battery <= 0:
                        VehicleDAO.check_and_update_zero_battery(vehicle_id, battery)
                
                return updated_count
            
            return 0
        except Exception as e:
            print(f"批量更新车辆位置错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def get_charging_stations(city='all', page=1, per_page=10):
        """获取充电站数据"""
        try:
            # 构建WHERE条件
            where_clause = ""
            params = []
            
            if city and city != 'all':
                where_clause = " WHERE city_code = %s"
                params.append(city)
            
            # 计算总记录数
            count_query = f"SELECT COUNT(*) as total FROM charging_stations{where_clause}"
            count_result = BaseDAO.execute_query(count_query, params)
            total_count = count_result[0]['total'] if count_result else 0
            
            # 计算分页参数
            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
            offset = (page - 1) * per_page
            
            # 查询当前页的充电站数据
            stations_query = f"""
            SELECT 
                station_id, station_code, city_code, 
                current_vehicles, max_capacity, 
                location_x, location_y,
                created_at
            FROM 
                charging_stations
            {where_clause}
            ORDER BY city_code, station_id
            LIMIT %s OFFSET %s
            """
            
            query_params = params.copy()
            query_params.extend([per_page, offset])
            stations = BaseDAO.execute_query(stations_query, query_params)
            
            # 处理数据格式
            for station in stations:
                # 处理created_at格式
                if station.get('created_at'):
                    station['created_at'] = station['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                
                # 添加站点名称
                station['station_name'] = f"充电站 #{station['station_id']} ({station.get('station_code', '')})"
                
                # 添加位置名称
                station['location_name'] = f"坐标({station.get('location_x', 0):.2f}, {station.get('location_y', 0):.2f})"
                
                # 计算使用率百分比
                station['usage_percent'] = round((station['current_vehicles'] / station['max_capacity']) * 100) if station['max_capacity'] > 0 else 0
                
                # 确定状态样式
                if station['usage_percent'] < 60:
                    station['status_class'] = 'bg-success'
                elif station['usage_percent'] < 85:
                    station['status_class'] = 'bg-warning'
                else:
                    station['status_class'] = 'bg-danger'
            
            # 获取所有城市列表
            cities_query = "SELECT DISTINCT city_code FROM charging_stations ORDER BY city_code"
            cities_result = BaseDAO.execute_query(cities_query)
            cities = [row['city_code'] for row in cities_result]
            
            return {
                'stations': stations,
                'cities': cities,
                'selected_city': city,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_count': total_count,
                    'per_page': per_page
                }
            }
        except Exception as e:
            print(f"获取充电站数据错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def get_city_charging_stations(city):
        """获取指定城市的充电站数据"""
        try:
            query = """
            SELECT 
                station_id, station_code, city_code, location_x, location_y,
                current_vehicles, max_capacity, 
                last_maintenance_date, next_maintenance_date
            FROM 
                charging_stations
            WHERE 
                city_code = %s
            """
            
            stations = BaseDAO.execute_query(query, (city,))
            
            # 处理日期格式
            for station in stations:
                if station.get('last_maintenance_date'):
                    station['last_maintenance_date'] = station['last_maintenance_date'].strftime('%Y-%m-%d')
                if station.get('next_maintenance_date'):
                    station['next_maintenance_date'] = station['next_maintenance_date'].strftime('%Y-%m-%d')
            
            return stations
        except Exception as e:
            print(f"获取城市充电站数据错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def _format_vehicle_data(vehicle):
        """格式化车辆数据"""
        # 处理日期格式
        if vehicle.get('last_maintenance_date'):
            vehicle['last_maintenance_date'] = vehicle['last_maintenance_date'].strftime('%Y-%m-%d')
        if vehicle.get('manufacture_date'):
            vehicle['manufacture_date'] = vehicle['manufacture_date'].strftime('%Y-%m-%d')
        if vehicle.get('registration_date'):
            vehicle['registration_date'] = vehicle['registration_date'].strftime('%Y-%m-%d')
        
        # 格式化距离
        if vehicle.get('mileage') is not None:
            vehicle['mileage_formatted'] = f"{vehicle['mileage']:,.0f}"
        else:
            vehicle['mileage_formatted'] = "0"
        
        # 确保数值类型是JSON兼容的
        if vehicle.get('battery_level') is not None:
            vehicle['battery_level'] = int(vehicle['battery_level'])
        else:
            vehicle['battery_level'] = 0
            
        if vehicle.get('mileage') is not None:
            vehicle['mileage'] = float(vehicle['mileage'])
        else:
            vehicle['mileage'] = 0
            
        if vehicle.get('is_available') is not None:
            vehicle['is_available'] = bool(vehicle['is_available'])
        else:
            vehicle['is_available'] = False
    
    @staticmethod
    def get_idle_vehicles_by_city(city_code):
        """获取指定城市中空闲状态的车辆"""
        try:
            query = """
            SELECT 
                vehicle_id, plate_number, model, current_status, battery_level,
                mileage, current_location_x, current_location_y, current_location_name,
                current_city, operating_city
            FROM vehicles 
            WHERE operating_city = %s AND current_status = '空闲中'
            ORDER BY battery_level DESC
            """
            
            vehicles = BaseDAO.execute_query(query, (city_code,))
            
            # 处理车辆数据
            for vehicle in vehicles:
                VehicleDAO._format_vehicle_data(vehicle)
            
            return vehicles
        except Exception as e:
            print(f"获取城市空闲车辆错误: {str(e)}")
            traceback.print_exc()
            raise e

    @staticmethod
    def get_low_battery_vehicles_by_city(city_code):
        """获取指定城市中等待充电状态的车辆"""
        try:
            query = """
            SELECT 
                vehicle_id, plate_number, model, current_status, battery_level,
                mileage, current_location_x, current_location_y, current_location_name,
                current_city, operating_city
            FROM vehicles 
            WHERE operating_city = %s AND current_status = '等待充电'
            ORDER BY battery_level ASC
            """
            
            vehicles = BaseDAO.execute_query(query, (city_code,))
            
            # 处理车辆数据
            for vehicle in vehicles:
                VehicleDAO._format_vehicle_data(vehicle)
            
            return vehicles
        except Exception as e:
            print(f"获取城市等待充电车辆错误: {str(e)}")
            traceback.print_exc()
            raise e

    @staticmethod
    def update_vehicle_status(vehicle_id, new_status):
        """更新车辆状态"""
        try:
            # 获取车辆当前信息，用于状态检查和位置信息获取
            vehicle = VehicleDAO.get_vehicle_by_id(vehicle_id)
            if not vehicle:
                print(f"找不到车辆 {vehicle_id}，无法更新状态")
                return False
            
            current_status = vehicle['current_status']
            current_location = vehicle.get('current_location_name', '')
            city_code = vehicle.get('current_city')
            
            # 如果状态没有变化，直接返回成功
            if current_status == new_status:
                return True
            
            # 如果当前状态为"电量不足"，不允许变更为其他状态
            if current_status == '电量不足' and new_status != '电量不足':
                return False
            
            # 特殊情况：从"前往充电"变为"电量不足"，需要释放充电站位置
            if current_status == '前往充电' and new_status == '电量不足' and current_location:
                # 提取充电站编号
                import re
                match = re.search(r'前往充电站\s+(\w+)', current_location)
                if match:
                    station_code = match.group(1)
                    
                    if city_code and station_code:
                        try:
                            from app.dao.charging_station_dao import ChargingStationDAO
                            # 释放充电站位置
                            success, old_count, new_count, max_capacity = ChargingStationDAO.update_station_vehicle_count(
                                station_code, city_code, -1, check_capacity=False
                            )
                            if success:
                                print(f"车辆 {vehicle_id} 从'前往充电'变为'电量不足'，已释放充电站 {station_code} 位置，当前负载: {new_count}/{max_capacity}")
                            else:
                                print(f"车辆 {vehicle_id} 从'前往充电'变为'电量不足'，释放充电站 {station_code} 位置失败")
                        except Exception as e:
                            print(f"释放充电站位置错误: {str(e)}")
                            traceback.print_exc()
            
            # 新增特殊情况：从"运行中"变为"电量不足"，确保不会错误地增加充电站负载
            if current_status == '运行中' and new_status == '电量不足':
                print(f"车辆 {vehicle_id} 从'运行中'变为'电量不足'，确保不与任何充电站关联")
                # 如果当前位置名称包含充电站信息，修改为一个通用的位置名称
                if '充电站' in current_location or '前往充电站' in current_location:
                    # 更新位置名称，移除充电站关联
                    try:
                        generic_location_name = "电量耗尽位置"
                        update_query = """
                        UPDATE vehicles
                        SET current_location_name = %s
                        WHERE vehicle_id = %s
                        """
                        BaseDAO.execute_update(update_query, (generic_location_name, vehicle_id))
                        print(f"已更新车辆 {vehicle_id} 位置名称，移除充电站关联")
                    except Exception as e:
                        print(f"更新位置名称错误: {str(e)}")
                        traceback.print_exc()
            
            # 执行状态更新
            query = """
            UPDATE vehicles
            SET current_status = %s
            WHERE vehicle_id = %s
            """
            
            affected_rows = BaseDAO.execute_update(query, (new_status, vehicle_id))
            return affected_rows > 0
        except Exception as e:
            print(f"更新车辆状态错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def get_nearest_vehicle(city_code, pickup_location_x, pickup_location_y):
        """获取离上车地点最近的空闲车辆"""
        try:
            
            # 如果没有提供坐标，则仅获取空闲车辆
            if pickup_location_x is None or pickup_location_y is None:
                print("未提供上车点坐标，将按电量排序返回车辆")
                query = """
                SELECT 
                    vehicle_id, plate_number, model, current_status, battery_level,
                    mileage, current_location_x, current_location_y, current_location_name,
                    current_city, operating_city
                FROM vehicles 
                WHERE operating_city = %s AND current_status = '空闲中'
                ORDER BY battery_level DESC
                LIMIT 1
                """
                vehicles = BaseDAO.execute_query(query, (city_code,))
            else:
                # 确保坐标是数值类型
                try:
                    pickup_x = float(pickup_location_x)
                    pickup_y = float(pickup_location_y)
      
                    
                    # 计算当前位置与乘客上车点之间的欧几里得距离
                    query = """
                    SELECT 
                        vehicle_id, plate_number, model, current_status, battery_level,
                        mileage, current_location_x, current_location_y, current_location_name,
                        current_city, operating_city, 
                        SQRT(POWER(current_location_x - %s, 2) + POWER(current_location_y - %s, 2)) AS distance
                    FROM vehicles 
                    WHERE operating_city = %s AND current_status = '空闲中'
                    ORDER BY distance ASC, battery_level DESC
                    LIMIT 1
                    """
                    vehicles = BaseDAO.execute_query(query, (pickup_x, pickup_y, city_code))
                except (ValueError, TypeError) as e:
                    print(f"坐标转换错误: {e}, 将按电量排序返回车辆")
                    # 如果坐标转换出错，退回到电量排序
                    query = """
                    SELECT 
                        vehicle_id, plate_number, model, current_status, battery_level,
                        mileage, current_location_x, current_location_y, current_location_name,
                        current_city, operating_city
                    FROM vehicles 
                    WHERE operating_city = %s AND current_status = '空闲中'
                    ORDER BY battery_level DESC
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
            else:
                print(f"找到车辆(按电量排序): ID={vehicle['vehicle_id']}, 电量={vehicle['battery_level']}%")
                
            return vehicle
            
        except Exception as e:
            print(f"获取最近车辆错误: {str(e)}")
            traceback.print_exc()
            raise e 

    @staticmethod
    def update_vehicle_location_coordinates(vehicle_id, location_x, location_y, location_name=None):
        """更新车辆坐标位置"""
        try:
            if location_name:
                query = """
                UPDATE vehicles
                SET current_location_x = %s, current_location_y = %s, current_location_name = %s
                WHERE vehicle_id = %s
                """
                affected_rows = BaseDAO.execute_update(query, (location_x, location_y, location_name, vehicle_id))
            else:
                query = """
                UPDATE vehicles
                SET current_location_x = %s, current_location_y = %s
                WHERE vehicle_id = %s
                """
                affected_rows = BaseDAO.execute_update(query, (location_x, location_y, vehicle_id))
                
            return affected_rows > 0
        except Exception as e:
            print(f"更新车辆坐标位置错误: {str(e)}")
            traceback.print_exc()
            raise e 

    @staticmethod
    def update_vehicle_location_and_battery(vehicle_id, location_x, location_y, location_name, battery_level):
        """更新车辆坐标位置和电量"""
        try:
            query = """
            UPDATE vehicles
            SET current_location_x = %s, current_location_y = %s, current_location_name = %s, battery_level = %s
            WHERE vehicle_id = %s
            """
            affected_rows = BaseDAO.execute_update(query, (location_x, location_y, location_name, battery_level, vehicle_id))
                
            
            # 检查电量是否为0，如果是则将状态更新为"电量不足"
            VehicleDAO.check_and_update_zero_battery(vehicle_id, battery_level)
            
            return affected_rows > 0
        except Exception as e:
            print(f"更新车辆坐标位置和电量错误: {str(e)}")
            traceback.print_exc()
            raise e 

    @staticmethod
    def find_nearest_available_charging_station(vehicle_x, vehicle_y, city_code):
        """查找最近的有空位的充电站
        
        Args:
            vehicle_x: 车辆当前X坐标
            vehicle_y: 车辆当前Y坐标
            city_code: 城市代码
            
        Returns:
            dict: 包含充电站信息的字典，如果找不到则返回None
        """
        try:
            
            # 使用事务和临时表获取更准确的充电站负载情况
            conn = BaseDAO.get_connection()
            try:
                # 开始事务
                conn.start_transaction(isolation_level='READ COMMITTED')
                cursor = conn.cursor(dictionary=True)
                
                # 获取可用的充电站列表，使用更严格的条件筛选
                query = """
                SELECT 
                    station_id, station_code, city_code, location_x, location_y, 
                    current_vehicles, max_capacity,
                    SQRT(POWER(location_x - %s, 2) + POWER(location_y - %s, 2)) AS distance
                FROM 
                    charging_stations
                WHERE 
                    city_code = %s AND
                    current_vehicles < max_capacity  -- 确保当前车辆数量小于最大容量
                ORDER BY 
                    distance ASC
                """
                
                cursor.execute(query, (vehicle_x, vehicle_y, city_code))
                stations = cursor.fetchall()
                
                if not stations:
                    conn.rollback()
                    return None
                
 
                # 获取向充电站移动中的车辆数量统计
                vehicles_to_station_query = """
                SELECT 
                    SUBSTRING_INDEX(current_location_name, ' ', -1) AS station_code,
                    COUNT(*) as vehicles_count
                FROM vehicles
                WHERE 
                    current_status = '前往充电' AND 
                    current_city = %s AND
                    current_location_name LIKE '前往充电站%'
                GROUP BY SUBSTRING_INDEX(current_location_name, ' ', -1)
                """
                
                cursor.execute(vehicles_to_station_query, (city_code,))
                vehicles_to_station = cursor.fetchall()
                
                # 创建充电站ID到前往车辆数量的映射
                station_pending_count = {}
                for item in vehicles_to_station:
                    station_code = item['station_code']
                    station_pending_count[station_code] = item['vehicles_count']
                
             # 找到有足够容量的最近充电站，并确保事务隔离
                for station in stations:
                    station_code = station['station_code']
                    
                    # 再次查询最新状态确保数据一致性
                    verify_query = """
                    SELECT current_vehicles, max_capacity
                    FROM charging_stations 
                    WHERE station_code = %s AND city_code = %s
                    """
                    cursor.execute(verify_query, (station_code, city_code))
                    latest_info = cursor.fetchone()
                    
                    if not latest_info:
                        continue
                    
                    current_vehicles = latest_info['current_vehicles']
                    max_capacity = latest_info['max_capacity']
                    
                    # 获取前往该充电站的车辆数
                    pending_vehicles = station_pending_count.get(station_code, 0)
                    
                    # 为了防止竞态条件，预留一个位置的缓冲
                    safety_buffer = 1
                    
                    # 检查是否有足够的剩余容量
                    if (current_vehicles + pending_vehicles + safety_buffer) <= max_capacity:
                        # 计算距离并格式化
                        station['distance'] = float(station['distance'])
                        station['distance_formatted'] = f"{station['distance']:.2f} 单位"
                        station['available_slots'] = max_capacity - current_vehicles - pending_vehicles
                        
                        
                        # 使用事务中获取的最新值
                        station['current_vehicles'] = current_vehicles
                        station['max_capacity'] = max_capacity
                        conn.commit()
                        return station
                
                conn.rollback()
                return None
                
            except Exception as tx_e:
                try:
                    conn.rollback()
                except:
                    pass
                print(f"查找最近充电站事务错误: {str(tx_e)}")
                traceback.print_exc()
                return None
            finally:
                try:
                    cursor.close()
                    conn.close()
                except:
                    pass
                    
        except Exception as e:
            print(f"查找最近充电站错误: {str(e)}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def update_vehicle_location_name(vehicle_id, location_name):
        """只更新车辆位置名称
        
        Args:
            vehicle_id: 车辆ID
            location_name: 新的位置名称
            
        Returns:
            bool: 更新是否成功
        """
        try:
            query = """
            UPDATE vehicles
            SET current_location_name = %s
            WHERE vehicle_id = %s
            """
            
            affected_rows = BaseDAO.execute_update(query, (location_name, vehicle_id))

            return affected_rows > 0
        except Exception as e:
            print(f"更新车辆位置名称错误: {str(e)}")
            traceback.print_exc()
            raise e 

    @staticmethod
    def update_vehicle_battery(vehicle_id, battery_level):
        """更新车辆电量
        
        Args:
            vehicle_id: 车辆ID
            battery_level: 电量百分比
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 先获取车辆当前状态和电量
            vehicle = VehicleDAO.get_vehicle_by_id(vehicle_id)
            if not vehicle:
                print(f"找不到车辆 {vehicle_id}，无法更新电量")
                return False
                
            current_status = vehicle['current_status']
            current_battery = vehicle['battery_level']
            
            # 如果当前状态是"电量不足"，则不允许电量增加
            if current_status == '电量不足' and battery_level > current_battery:
                print(f"车辆 {vehicle_id} 状态为电量不足，不允许电量增加从 {current_battery}% 到 {battery_level}%")
                return False
            
            query = """
            UPDATE vehicles
            SET battery_level = %s
            WHERE vehicle_id = %s
            """
            
            affected_rows = BaseDAO.execute_update(query, (battery_level, vehicle_id))
            
            # 检查电量是否为0，如果是则将状态更新为"电量不足"
            VehicleDAO.check_and_update_zero_battery(vehicle_id, battery_level)
            
            return affected_rows > 0
        except Exception as e:
            print(f"更新车辆电量错误: {str(e)}")
            traceback.print_exc()
            raise e

    @staticmethod
    def get_charging_capacity_status(city_code):
        """获取指定城市的充电站总剩余容量和前往充电站的车辆总数
        
        Args:
            city_code: 城市代码
            
        Returns:
            tuple: (总剩余容量, 前往充电站的车辆总数)
        """
        try:
            print(f"获取城市 {city_code} 的充电站容量状态")
            
            # 获取所有充电站的总容量和当前车辆数
            stations_query = """
            SELECT 
                SUM(max_capacity) as total_capacity,
                SUM(current_vehicles) as total_current_vehicles
            FROM 
                charging_stations
            WHERE 
                city_code = %s
            """
            
            stations_result = BaseDAO.execute_query(stations_query, (city_code,))
            
            if not stations_result or len(stations_result) == 0:
                print(f"城市 {city_code} 没有充电站数据")
                return 0, 0
                
            total_capacity = stations_result[0]['total_capacity'] or 0
            total_current_vehicles = stations_result[0]['total_current_vehicles'] or 0
            total_remaining_capacity = total_capacity - total_current_vehicles
            
            # 获取前往充电站的车辆总数
            vehicles_to_station_query = """
            SELECT 
                COUNT(*) as total_pending_vehicles
            FROM vehicles
            WHERE 
                current_status IN ('等待充电', '前往充电', '等待充电') AND 
                current_city = %s AND
                current_location_name LIKE '前往充电站%'
            """
            
            pending_result = BaseDAO.execute_query(vehicles_to_station_query, (city_code,))
            total_pending_vehicles = pending_result[0]['total_pending_vehicles'] if pending_result else 0
            
            print(f"城市 {city_code} 充电站总容量: {total_capacity}, 已使用: {total_current_vehicles}, " +
                  f"剩余: {total_remaining_capacity}, 前往中: {total_pending_vehicles}")
                  
            return total_remaining_capacity, total_pending_vehicles
        
        except Exception as e:
            print(f"获取充电站容量状态出错: {str(e)}")
            traceback.print_exc()
            return 0, 0

    @staticmethod
    def check_charging_station_availability(station_code, city_code):
        """检查充电站是否有可用空位
        
        返回值包含：
        - 是否有空位
        - 当前车辆数
        - 最大容量
        - 前往中的车辆数
        """
        from app.dao.charging_station_dao import ChargingStationDAO
        
        # 使用ChargingStationDAO检查充电站可用性
        return ChargingStationDAO.check_station_availability(station_code, city_code)
    
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
                
                # 如果当前状态不是"电量不足"，才更新
                if vehicle['current_status'] != '电量不足':
                    current_status = vehicle['current_status']
                    current_location_name = vehicle.get('current_location_name', '')
                    city_code = vehicle.get('current_city', '')
                    
                    # 记录原始状态用于日志
                    
                    # 特殊处理：如果是"运行中"状态且位置名称包含充电站信息
                    if current_status == '运行中' and ('充电站' in current_location_name or '前往充电站' in current_location_name):
                        # 先更新位置名称，防止与充电站产生关联
                        print(f"车辆 {vehicle_id} 从'运行中'电量耗尽，检测到位置名称包含充电站信息，清除关联")
                        try:
                            update_query = """
                            UPDATE vehicles
                            SET current_location_name = %s
                            WHERE vehicle_id = %s
                            """
                            BaseDAO.execute_update(update_query, ("电量耗尽位置", vehicle_id))
                        except Exception as e:
                            print(f"更新位置名称错误: {str(e)}")
                            traceback.print_exc()
                    
                    # 从位置名称中检查是否有充电站关联
                    if '前往充电站' in current_location_name:
                        import re
                        match = re.search(r'前往充电站\s+(\w+)', current_location_name)
                        if match and city_code:
                            station_code = match.group(1)
                            print(f"检测到车辆 {vehicle_id} 位置名称包含充电站 {station_code} 信息，尝试释放位置")
                            try:
                                from app.dao.charging_station_dao import ChargingStationDAO
                                # 释放充电站位置
                                success, old_count, new_count, max_capacity = ChargingStationDAO.update_station_vehicle_count(
                                    station_code, city_code, -1, check_capacity=False
                                )
                                if success:
                                    print(f"车辆 {vehicle_id} 电量耗尽，已释放充电站 {station_code} 位置，当前负载: {new_count}/{max_capacity}")
                                else:
                                    print(f"车辆 {vehicle_id} 电量耗尽，释放充电站 {station_code} 位置失败")
                            except Exception as e:
                                print(f"释放充电站位置错误: {str(e)}")
                                traceback.print_exc()
                    
                    # 更新车辆状态为电量不足
                    # 注意：update_vehicle_status方法现在已经包含了释放充电站位置的逻辑
                    # 所以这里直接调用即可，不需要额外处理"前往充电"的情况
                    VehicleDAO.update_vehicle_status(vehicle_id, "电量不足")
                    
                    # 发送车辆电量不足通知
                    from app.utils.notification_service import NotificationService
                    plate_number = vehicle.get('plate_number', f'ID-{vehicle_id}')
                    NotificationService.notify_vehicle_low_battery(
                        vehicle_id=vehicle_id, 
                        battery_level=battery_level,
                        plate_number=plate_number
                    )
               
                    
                    # 记录车辆状态变更日志
                    try:
                        log_query = """
                        INSERT INTO vehicle_logs
                        (vehicle_id, plate_number, log_type, log_content, created_at)
                        VALUES (%s, %s, %s, %s, NOW())
                        """
                        
                        log_content = f"电量耗尽，状态从'{current_status}'自动更改为'电量不足'"
                        VehicleDAO.execute_update(log_query, (vehicle_id, plate_number, '状态变更', log_content))
                    except Exception as log_error:
                        print(f"记录状态变更日志失败: {str(log_error)}")
                        print("系统将继续工作，但不会记录此次状态变更历史")
                    
                    return True
            return False
        except Exception as e:
            print(f"检查电量不足状态时出错: {str(e)}")
            traceback.print_exc()
            return False 

    @staticmethod
    def find_nearest_waiting_charging_vehicle(station_x, station_y, city_code):
        """查找最近的等待充电的车辆
        
        Args:
            station_x: 充电站X坐标 - 应该是特定充电站的坐标
            station_y: 充电站Y坐标 - 应该是特定充电站的坐标
            city_code: 城市代码
            
        Returns:
            dict: 包含车辆信息的字典，如果找不到则返回None
        """
        try:
            print(f"查找最近等待充电车辆 - 城市: {city_code}, 充电站坐标: ({station_x}, {station_y})")
            
            # 查询等待充电状态的车辆，按与特定充电站的距离排序（而不是所有充电站）
            query = """
            SELECT 
                vehicle_id, plate_number, model, current_status, battery_level,
                mileage, current_location_x, current_location_y, current_location_name,
                current_city, operating_city,
                SQRT(POWER(current_location_x - %s, 2) + POWER(current_location_y - %s, 2)) AS distance
            FROM vehicles 
            WHERE operating_city = %s AND current_status = '等待充电'
            ORDER BY distance ASC, battery_level ASC
            LIMIT 1
            """
            
            vehicles = BaseDAO.execute_query(query, (station_x, station_y, city_code))
            
            if not vehicles:
                print(f"在城市 {city_code} 没有找到等待充电的车辆")
                return None
            
            vehicle = vehicles[0]
            VehicleDAO._format_vehicle_data(vehicle)
            
            # 添加距离信息
            if 'distance' in vehicle:
                vehicle['distance'] = float(vehicle['distance'])
                vehicle['distance_formatted'] = f"{vehicle['distance']:.2f} 单位"
                print(f"找到最近等待充电车辆: ID={vehicle['vehicle_id']}, 距离充电站{vehicle.get('distance_formatted')}, 电量={vehicle['battery_level']}%")
            
            return vehicle
            
        except Exception as e:
            print(f"查找最近等待充电车辆错误: {str(e)}")
            traceback.print_exc()
            return None 

    @staticmethod
    def check_vehicle_exists(plate_number, vin):
        """检查车牌号或VIN是否已存在
        
        Args:
            plate_number: 车牌号
            vin: 车辆识别号
            
        Returns:
            dict: 如果存在重复，返回{'field': 字段名, 'value': 值}，否则返回None
        """
        try:
            # 检查车牌号
            query = "SELECT vehicle_id FROM vehicles WHERE plate_number = %s"
            result = BaseDAO.execute_query(query, (plate_number,))
            if result:
                return {
                    'field': '车牌号',
                    'value': plate_number
                }
            
            # 检查VIN
            query = "SELECT vehicle_id FROM vehicles WHERE vin = %s"
            result = BaseDAO.execute_query(query, (vin,))
            if result:
                return {
                    'field': '车辆识别号(VIN)',
                    'value': vin
                }
            
            return None
        except Exception as e:
            print(f"检查车辆是否存在出错: {str(e)}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def add_vehicle(vehicle_data):
        """添加新车辆
        
        Args:
            vehicle_data: 车辆数据字典
            
        Returns:
            int: 新创建的车辆ID，如果失败则返回None
        """
        try:
            print("开始添加车辆...")
            
            # 构建插入SQL
            fields = []
            placeholders = []
            values = []
            
            # 基本字段
            required_fields = {
                'plate_number': '车牌号',
                'vin': '车辆识别号',
                'model': '车型',
                'current_status': '状态',
                'battery_level': '电量',
                'mileage': '距离'
            }
            
            # 处理必填字段
            for field, desc in required_fields.items():
                if field in vehicle_data and vehicle_data[field] is not None:
                    fields.append(field)
                    placeholders.append('%s')
                    values.append(vehicle_data[field])
            
            # 处理城市相关字段
            if 'current_city' in vehicle_data and vehicle_data['current_city']:
                city = vehicle_data['current_city']
                fields.append('current_city')
                placeholders.append('%s')
                values.append(city)
                
                # 运营城市默认与当前城市相同
                fields.append('operating_city')
                placeholders.append('%s')
                values.append(city)
                
                # 处理坐标信息
                if 'current_location_x' in vehicle_data and 'current_location_y' in vehicle_data:
                    # 如果提供了坐标
                    fields.append('current_location_x')
                    placeholders.append('%s')
                    values.append(vehicle_data['current_location_x'])
                    
                    fields.append('current_location_y')
                    placeholders.append('%s')
                    values.append(vehicle_data['current_location_y'])
                else:
                    # 未提供坐标，生成随机坐标（城市中心区域400-600范围内）
                    import random
                    location_x = random.randint(400, 600)
                    location_y = random.randint(400, 600)
                    
                    fields.append('current_location_x')
                    placeholders.append('%s')
                    values.append(location_x)
                    
                    fields.append('current_location_y')
                    placeholders.append('%s')
                    values.append(location_y)
                
                # 处理位置名称
                if 'current_location_name' in vehicle_data and vehicle_data['current_location_name']:
                    fields.append('current_location_name')
                    placeholders.append('%s')
                    values.append(vehicle_data['current_location_name'])
                else:
                    # 未提供位置名称，使用默认值
                    default_location = f"{city}市中心区域"
                    fields.append('current_location_name')
                    placeholders.append('%s')
                    values.append(default_location)
            
            # 处理生产日期
            if 'manufacture_date' in vehicle_data and vehicle_data['manufacture_date']:
                fields.append('manufacture_date')
                placeholders.append('%s')
                values.append(vehicle_data['manufacture_date'])
                
                # 默认注册日期为生产日期后20天
                from datetime import datetime, timedelta
                manufacture_date = datetime.strptime(vehicle_data['manufacture_date'], '%Y-%m-%d')
                registration_date = manufacture_date + timedelta(days=20)
                
                fields.append('registration_date')
                placeholders.append('%s')
                values.append(registration_date.strftime('%Y-%m-%d'))
            
            # 添加创建时间和更新时间
            from datetime import datetime
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            fields.append('created_at')
            placeholders.append('%s')
            values.append(now)
            
            fields.append('updated_at')
            placeholders.append('%s')
            values.append(now)
            
            # 构建完整SQL
            sql = f"""
            INSERT INTO vehicles ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
            """
            
            print(f"执行SQL: {sql}")
            print(f"参数值: {values}")
            
            # 使用直接连接执行插入，以便获取最后插入的ID
            conn = BaseDAO.get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute(sql, tuple(values))
                conn.commit()
                
                # 获取最后插入的ID
                new_id = cursor.lastrowid
                print(f"插入成功，获取到新ID: {new_id}")
                
                return new_id
            finally:
                cursor.close()
                conn.close()
            
        except Exception as e:
            print(f"添加车辆错误: {str(e)}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def update_vehicle_statistics(vehicle_id, additional_mileage):
        """
        更新车辆统计信息：增加里程和完成订单数
        
        Args:
            vehicle_id (int): 车辆ID
            additional_mileage (float): 要增加的里程数()
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 首先检查车辆是否存在
            check_query = "SELECT mileage, total_orders FROM vehicles WHERE vehicle_id = %s"
            check_result = BaseDAO.execute_query(check_query, (vehicle_id,))
            
            if not check_result:
                print(f"找不到车辆 {vehicle_id}，无法更新统计信息")
                return False
            
            # 获取当前里程和订单数
            current_mileage = check_result[0]['mileage']
            current_total_orders = check_result[0]['total_orders']
            
            # 转换类型并计算新的里程和订单数
            new_mileage = float(current_mileage) + float(additional_mileage)
            new_total_orders = int(current_total_orders) + 1  # 每次调用增加1个订单
            
            # 限制里程小数位数为2位
            new_mileage = round(new_mileage, 2)
            
            # 更新车辆统计信息
            update_query = """
            UPDATE vehicles
            SET mileage = %s, total_orders = %s
            WHERE vehicle_id = %s
            """
            
            affected_rows = BaseDAO.execute_update(update_query, (new_mileage, new_total_orders, vehicle_id))
            
            if affected_rows > 0:
                return True
            else:
                print(f"更新车辆 {vehicle_id} 的统计信息失败")
                return False
                
        except Exception as e:
            print(f"更新车辆统计信息出错: {str(e)}")
            traceback.print_exc()
            return False 

    @staticmethod
    def add_vehicle_log(vehicle_id, plate_number, log_type, log_content):
        """
        添加车辆操作日志
        
        Args:
            vehicle_id (int): 车辆ID
            plate_number (str): 车牌号
            log_type (str): 日志类型，如'车辆添加'、'车辆删除'等
            log_content (str): 日志内容
            
        Returns:
            int: 新创建的日志ID，如果失败则返回None
        """
        connection = None
        cursor = None
        
        try:
            print(f"开始记录车辆日志: 车辆ID={vehicle_id}, 车牌={plate_number}, 类型={log_type}")
            
            # 确保vehicle_id是整数
            try:
                vehicle_id = int(vehicle_id)
                print(f"车辆ID已转换为整数: {vehicle_id}")
            except (ValueError, TypeError) as e:
                print(f"车辆ID转换失败: {vehicle_id}，错误: {str(e)}")
                return None
            
            # 首先检查车辆是否存在 - 但不阻止添加日志
            check_query = "SELECT vehicle_id FROM vehicles WHERE vehicle_id = %s"
            check_result = BaseDAO.execute_query(check_query, (vehicle_id,))
            
            if not check_result:
                print(f"警告: 找不到ID为{vehicle_id}的车辆，但仍将尝试添加日志")
            else:
                print(f"确认车辆存在，ID: {vehicle_id}")
            
            # 查询当前最大ID
            max_id_query = "SELECT MAX(log_id) as max_id FROM vehicle_logs"
            max_id_result = BaseDAO.execute_query(max_id_query)
            
            # 计算新ID (当前最大ID + 1)，如果表空则使用1
            new_id = 1
            if max_id_result and max_id_result[0]['max_id'] is not None:
                new_id = max_id_result[0]['max_id'] + 1
            
            print(f"将使用的日志ID: {new_id}")
            
            # 使用直接的数据库连接和事务，确保插入成功
            connection = BaseDAO.get_connection()
            cursor = connection.cursor()
            
            # 构建插入SQL，显式指定ID
            log_query = """
            INSERT INTO vehicle_logs
            (log_id, vehicle_id, plate_number, log_type, log_content, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """
            
            print(f"执行日志插入SQL: {log_query}")
            print(f"SQL参数: [{new_id}, {vehicle_id}, {plate_number}, {log_type}, {log_content[:30]}...]")
            
            # 执行插入
            cursor.execute(log_query, (new_id, vehicle_id, plate_number, log_type, log_content))
            connection.commit()
            
            # 验证插入是否成功
            verify_query = "SELECT log_id FROM vehicle_logs WHERE log_id = %s"
            cursor.execute(verify_query, (new_id,))
            verify_result = cursor.fetchone()
            
            if verify_result:
                print(f"成功记录日志，ID: {new_id}，已验证插入成功")
                return new_id
            else:
                print(f"日志似乎已插入但无法验证，将尝试再次查询")
                # 再次尝试验证
                cursor.execute(verify_query, (new_id,))
                verify_result = cursor.fetchone()
                if verify_result:
                    print(f"二次验证成功，日志ID: {new_id}")
                    return new_id
                else:
                    print(f"日志记录似乎未成功插入")
                    return None
                
        except Exception as e:
            print(f"添加车辆日志错误: {str(e)}")
            traceback.print_exc()
            if connection:
                try:
                    connection.rollback()
                except:
                    pass
            return None
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if connection:
                try:
                    connection.close()
                except:
                    pass 

    @staticmethod
    def find_vehicle_by_status_and_city(status, city_code):
        """查找指定状态和城市的车辆
        
        Args:
            status: 车辆状态，例如"等待充电"
            city_code: 城市代码
            
        Returns:
            返回符合条件的第一辆车信息，如果没有找到则返回None
        """
        try:
            # 查询符合条件的车辆
            query = """
            SELECT 
                vehicle_id, plate_number, current_status, battery_level,
                current_location_x, current_location_y, current_location_name, 
                operating_city, model, is_available
            FROM 
                vehicles
            WHERE 
                current_status = %s
                AND operating_city = %s
                AND is_available = 1
            ORDER BY 
                vehicle_id ASC
            LIMIT 1
            """
            
            result = BaseDAO.execute_query(query, (status, city_code))
            
            if result and len(result) > 0:
                # 返回第一个符合条件的车辆
                return result[0]
            else:
                return None
        except Exception as e:
            print(f"查找状态为 {status} 且在 {city_code} 城市的车辆时出错: {str(e)}")
            traceback.print_exc()
            return None 