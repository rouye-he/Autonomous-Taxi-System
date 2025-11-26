import traceback
from app.dao.base_dao import BaseDAO
import threading

class ChargingStationDAO(BaseDAO):
    """充电站数据访问对象，封装所有充电站相关的数据库操作"""
    
    # 使用锁来防止并发问题
    _station_locks = {}
    _lock_mutex = threading.Lock()
    
    @staticmethod
    def get_all_stations():
        """获取所有充电站记录
        
        Returns:
            list: 包含所有充电站信息的列表
        """
        try:
            query = """
            SELECT 
                station_id, station_code, city_code, 
                current_vehicles, max_capacity, 
                location_x, location_y,
                last_maintenance_date, next_maintenance_date
            FROM 
                charging_stations
            ORDER BY city_code, station_id
            """
            
            stations = BaseDAO.execute_query(query)
            
            # 处理数据格式
            for station in stations:
                if station.get('last_maintenance_date'):
                    station['last_maintenance_date'] = station['last_maintenance_date'].strftime('%Y-%m-%d')
                if station.get('next_maintenance_date'):
                    station['next_maintenance_date'] = station['next_maintenance_date'].strftime('%Y-%m-%d')
                
                # 添加站点名称
                station['station_name'] = f"充电站 #{station['station_id']} ({station.get('station_code', '')})"
            
            return stations
        except Exception as e:
            print(f"获取所有充电站数据错误: {str(e)}")
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_station_lock(station_code, city_code):
        """获取指定充电站的锁对象，如果不存在则创建"""
        key = f"{station_code}_{city_code}"
        with ChargingStationDAO._lock_mutex:
            if key not in ChargingStationDAO._station_locks:
                ChargingStationDAO._station_locks[key] = threading.Lock()
            return ChargingStationDAO._station_locks[key]
    
    @staticmethod
    def get_station_info(station_code, city_code):
        """获取充电站信息
        
        Args:
            station_code: 充电站编码
            city_code: 城市编码
            
        Returns:
            dict: 充电站信息，包含current_vehicles和max_capacity
                 如果找不到，返回None
        """
        try:
            query = """
            SELECT current_vehicles, max_capacity
            FROM charging_stations
            WHERE station_code = %s AND city_code = %s
            """
            
            result = BaseDAO.execute_query(query, (station_code, city_code))
            if result and len(result) > 0:
                return result[0]
            return None
        except Exception as e:
            print(f"获取充电站信息出错: {e}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def update_station_vehicle_count(station_code, city_code, increment, check_capacity=True):
        """更新充电站当前车辆数量
        
        Args:
            station_code: 充电站编码
            city_code: 城市编码
            increment: 车辆数变化，正数表示增加，负数表示减少
            check_capacity: 是否检查容量限制，默认检查
            
        Returns:
            tuple: (成功标志, 更新前数量, 更新后数量, 最大容量)
                  如果失败，返回(False, 0, 0, 0)
        """
        # 获取该充电站的锁
        lock = ChargingStationDAO.get_station_lock(station_code, city_code)
        
        # 使用锁确保线程安全
        with lock:
            try:
                # 使用事务确保查询和更新是原子操作
                conn = BaseDAO.get_connection()
                try:
                    # 开始事务
                    conn.start_transaction(isolation_level='SERIALIZABLE')
                    
                    # 先获取当前充电站信息并加锁
                    query = """
                    SELECT current_vehicles, max_capacity
                    FROM charging_stations
                    WHERE station_code = %s AND city_code = %s
                    FOR UPDATE
                    """
                    
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(query, (station_code, city_code))
                    result = cursor.fetchall()
                    cursor.close()
                    
                    if not result or len(result) == 0:
                        print(f"找不到充电站: {station_code}, {city_code}")
                        conn.rollback()
                        return False, 0, 0, 0
                    
                    station_info = result[0]
                    current_count = station_info['current_vehicles']
                    max_capacity = station_info['max_capacity']
                    
                    # 计算新的车辆数量
                    new_count = current_count + increment
                    
                    # 确保不小于0
                    new_count = max(0, new_count)
                    
                    # 再次核实容量
                    if check_capacity and increment > 0:
                        # 严格检查：确保新数量不超过最大容量
                        if new_count > max_capacity:
                            print(f"拒绝更新：充电站 {station_code} 将超过最大容量 {max_capacity}")
                            conn.rollback()
                            return False, current_count, current_count, max_capacity
                        
                        # 二次验证：查询前往该充电站的车辆数量
                        pending_query = """
                        SELECT COUNT(*) as pending_count
                        FROM vehicles
                        WHERE current_status = '前往充电' AND
                              current_city = %s AND
                              current_location_name LIKE %s
                        """
                        
                        location_pattern = f"前往充电站 {station_code}%"
                        cursor = conn.cursor(dictionary=True)
                        cursor.execute(pending_query, (city_code, location_pattern))
                        pending_result = cursor.fetchall()
                        cursor.close()
                        
                        pending_vehicles = pending_result[0]['pending_count'] if pending_result else 0
                        
                        # 考虑前往中的车辆
                        if (current_count + pending_vehicles + 1) > max_capacity:
                            print(f"拒绝更新：充电站 {station_code} 总预计车辆数（当前{current_count}+前往中{pending_vehicles}+新增1）将超过最大容量 {max_capacity}")
                            conn.rollback()
                            return False, current_count, current_count, max_capacity
                    
                    # 更新数据库
                    update_query = """
                    UPDATE charging_stations
                    SET current_vehicles = %s
                    WHERE station_code = %s AND city_code = %s
                    """
                    
                    cursor = conn.cursor()
                    cursor.execute(update_query, (new_count, station_code, city_code))
                    cursor.close()
                    
                    # 提交事务
                    conn.commit()
                    
                    return True, current_count, new_count, max_capacity
                    
                except Exception as inner_e:
                    # 发生异常，回滚事务
                    try:
                        conn.rollback()
                    except:
                        pass
                    print(f"更新充电站车辆数量事务出错: {inner_e}")
                    traceback.print_exc()
                    return False, 0, 0, 0
                finally:
                    # 关闭连接
                    try:
                        conn.close()
                    except:
                        pass
                    
            except Exception as e:
                print(f"获取数据库连接出错: {e}")
                traceback.print_exc()
                return False, 0, 0, 0
    
    @staticmethod
    def check_station_availability(station_code, city_code):
        """检查充电站是否有可用位置，考虑当前车辆和正在前往的车辆
        
        Args:
            station_code: 充电站编码
            city_code: 城市编码
            
        Returns:
            tuple: (是否有可用位置, 当前车辆数, 最大容量, 前往中的车辆数)
        """
        try:
            # 获取充电站信息
            station_info = ChargingStationDAO.get_station_info(station_code, city_code)
            if not station_info:
                return False, 0, 0, 0
            
            current_vehicles = station_info['current_vehicles']
            max_capacity = station_info['max_capacity']
            
            # 获取前往该充电站的车辆数量
            pending_query = """
            SELECT COUNT(*) as pending_count
            FROM vehicles
            WHERE current_status IN ('等待充电', '前往充电') AND
                  current_city = %s AND
                  current_location_name LIKE %s
            """
            
            location_pattern = f"前往充电站 {station_code}%"
            pending_result = BaseDAO.execute_query(pending_query, (city_code, location_pattern))
            pending_vehicles = pending_result[0]['pending_count'] if pending_result else 0
            
            # 判断是否有可用空位
            has_available_slots = (current_vehicles + pending_vehicles) < max_capacity
            
            print(f"充电站 {station_code} 状态: 当前车辆={current_vehicles}, 最大容量={max_capacity}, " +
                  f"前往中={pending_vehicles}, 有空位={has_available_slots}")
            
            return has_available_slots, current_vehicles, max_capacity, pending_vehicles
            
        except Exception as e:
            print(f"检查充电站可用性错误: {str(e)}")
            traceback.print_exc()
            return False, 0, 0, 0
    
    @staticmethod
    def notify_waiting_vehicle(station_code, city_code, station_x, station_y):
        """通知等待充电的车辆前往指定充电站，确保原子操作
        
        Args:
            station_code: 充电站编码
            city_code: 城市编码
            station_x: 充电站X坐标
            station_y: 充电站Y坐标
            
        Returns:
            tuple: (成功标志, 等待车辆ID或None, 错误信息或等待车辆信息)
        """
        # 获取该充电站的锁
        lock = ChargingStationDAO.get_station_lock(station_code, city_code)
        
        # 使用锁确保线程安全
        with lock:
            try:
                from app.dao.vehicle_dao import VehicleDAO  # 导入放在函数内避免循环导入
                
                # 使用事务确保查询和更新是原子操作
                conn = BaseDAO.get_connection()
                try:
                    # 开始事务
                    conn.start_transaction(isolation_level='SERIALIZABLE')
                    
                    # 1. 先检查充电站是否真的有空位
                    query = """
                    SELECT current_vehicles, max_capacity
                    FROM charging_stations
                    WHERE station_code = %s AND city_code = %s
                    FOR UPDATE
                    """
                    
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(query, (station_code, city_code))
                    result = cursor.fetchall()
                    cursor.close()
                    
                    if not result or len(result) == 0:
                        print(f"找不到充电站: {station_code}, {city_code}")
                        conn.rollback()
                        return False, None, "充电站不存在"
                    
                    station_info = result[0]
                    current_count = station_info['current_vehicles']
                    max_capacity = station_info['max_capacity']
                    
                    # 注意: 检查前首先减1，因为调用此方法时，充电完成的车辆会离开充电站
                    # 但调用方不会先更新数据库，而是等待此方法的事务完成
                    adjusted_count = current_count - 1
                    
                    # 确保计数不会小于0
                    if adjusted_count < 0:
                        adjusted_count = 0
                        
                    # 首先更新充电站计数，减去离开的车辆
                    update_count_query = """
                    UPDATE charging_stations
                    SET current_vehicles = %s
                    WHERE station_code = %s AND city_code = %s
                    """
                    
                    cursor = conn.cursor()
                    cursor.execute(update_count_query, (adjusted_count, station_code, city_code))
                    cursor.close()
                    
                    print(f"充电站 {station_code} 负载更新: {current_count} -> {adjusted_count} (车辆离开)")
                    
                    # 2. 查找最近的等待充电车辆
                    waiting_vehicle_query = """
                    SELECT 
                        vehicle_id, current_location_x, current_location_y, battery_level, current_location_name
                    FROM vehicles 
                    WHERE current_status = '等待充电' AND current_city = %s
                    ORDER BY 
                        SQRT(POWER(current_location_x - %s, 2) + POWER(current_location_y - %s, 2)) ASC,
                        battery_level ASC
                    LIMIT 1
                    FOR UPDATE
                    """
                    
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(waiting_vehicle_query, (city_code, station_x, station_y))
                    waiting_vehicles = cursor.fetchall()
                    cursor.close()
                    
                    if not waiting_vehicles:
                        print(f"没有找到等待充电的车辆")
                        # 提交事务 - 即使没有等待车辆，也要保存减少的容量计数
                        conn.commit()
                        return False, None, "没有等待充电的车辆"
                    
                    waiting_vehicle = waiting_vehicles[0]
                    waiting_vehicle_id = waiting_vehicle['vehicle_id']
                    
                    # 3. 更新车辆状态
                    update_vehicle_query = """
                    UPDATE vehicles
                    SET 
                        current_status = '前往充电',
                        current_location_name = %s
                    WHERE 
                        vehicle_id = %s AND current_status = '等待充电'
                    """
                    
                    location_name = f"前往充电站 {station_code}"
                    cursor = conn.cursor()
                    cursor.execute(update_vehicle_query, (location_name, waiting_vehicle_id))
                    updated_rows = cursor.rowcount
                    cursor.close()
                    
                    if updated_rows == 0:
                        print(f"车辆 {waiting_vehicle_id} 状态已变更，无法通知前往充电")
                        # 提交事务 - 即使无法更新车辆状态，也要保存减少的容量计数
                        conn.commit()
                        return False, None, "车辆状态已变更"
                    
                    # 4. 更新充电站容量 - 增加新车辆的计数
                    update_query = """
                    UPDATE charging_stations
                    SET current_vehicles = current_vehicles + 1
                    WHERE station_code = %s AND city_code = %s AND current_vehicles < max_capacity
                    """
                    
                    cursor = conn.cursor()
                    cursor.execute(update_query, (station_code, city_code))
                    capacity_updated = cursor.rowcount
                    cursor.close()
                    
                    if capacity_updated == 0:
                        print(f"充电站 {station_code} 容量已满，无法更新")
                        # 回滚车辆状态更新
                        revert_vehicle_query = """
                        UPDATE vehicles
                        SET 
                            current_status = '等待充电',
                            current_location_name = %s
                        WHERE 
                            vehicle_id = %s
                        """
                        
                        original_location = waiting_vehicle.get('current_location_name', '')
                        cursor = conn.cursor()
                        cursor.execute(revert_vehicle_query, (original_location, waiting_vehicle_id))
                        cursor.close()
                        
                        # 提交事务 - 即使无法增加新车辆的计数，也要保存减少离开车辆的计数
                        conn.commit()
                        return False, None, "充电站容量已满"
                    
                    # 提交事务
                    conn.commit()
                    
                    print(f"成功通知车辆 {waiting_vehicle_id} 前往充电站 {station_code}，充电站容量已更新")
                    return True, waiting_vehicle_id, waiting_vehicle
                    
                except Exception as inner_e:
                    # 发生异常，回滚事务
                    try:
                        conn.rollback()
                    except:
                        pass
                    print(f"通知等待充电车辆事务出错: {inner_e}")
                    traceback.print_exc()
                    return False, None, str(inner_e)
                finally:
                    # 关闭连接
                    try:
                        conn.close()
                    except:
                        pass
                    
            except Exception as e:
                print(f"获取数据库连接出错: {e}")
                traceback.print_exc()
                return False, None, str(e)
    
    @staticmethod
    def add_charging_station(station_data):
        """添加新充电站
        
        Args:
            station_data: 充电站数据字典
            
        Returns:
            int: 新创建的充电站ID，如果失败则返回None
        """
        try:
            # 构建插入SQL
            fields = []
            placeholders = []
            values = []
            
            # 基本字段
            required_fields = {
                'station_code': '充电站编号',
                'city_code': '所在城市',
                'max_capacity': '最大容纳车辆数'
            }
            
            # 处理必填字段
            for field, desc in required_fields.items():
                if field in station_data and station_data[field] is not None:
                    fields.append(field)
                    placeholders.append('%s')
                    values.append(station_data[field])
            
            # 处理坐标信息
            if 'location_x' in station_data and 'location_y' in station_data:
                # 如果提供了坐标
                fields.append('location_x')
                placeholders.append('%s')
                values.append(station_data['location_x'])
                
                fields.append('location_y')
                placeholders.append('%s')
                values.append(station_data['location_y'])
            else:
                # 未提供坐标，生成随机坐标（城市中心区域400-600范围内）
                import random
                location_x = random.randint(400, 600)
                location_y = random.randint(400, 600)
                
                fields.append('location_x')
                placeholders.append('%s')
                values.append(location_x)
                
                fields.append('location_y')
                placeholders.append('%s')
                values.append(location_y)
            
            # 处理当前车辆数
            fields.append('current_vehicles')
            placeholders.append('%s')
            values.append(0)  # 新充电站默认没有车辆
            
            # 处理维护日期
            if 'last_maintenance_date' in station_data and station_data['last_maintenance_date']:
                fields.append('last_maintenance_date')
                placeholders.append('%s')
                values.append(station_data['last_maintenance_date'])
                
            if 'next_maintenance_date' in station_data and station_data['next_maintenance_date']:
                fields.append('next_maintenance_date')
                placeholders.append('%s')
                values.append(station_data['next_maintenance_date'])
            else:
                # 默认下次维护日期为90天后
                from datetime import datetime, timedelta
                next_date = datetime.now() + timedelta(days=90)
                fields.append('next_maintenance_date')
                placeholders.append('%s')
                values.append(next_date.strftime('%Y-%m-%d'))
            
            # 添加创建时间 - 使用参数方式而不是SQL函数
            from datetime import datetime
            fields.append('created_at')
            placeholders.append('%s')
            values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # 构建完整SQL
            sql = f"""
            INSERT INTO charging_stations ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
            """
            
            # 执行插入
            affected_rows = BaseDAO.execute_update(sql, tuple(values))
            
            # 简化判断逻辑：如果有影响的行数，则认为插入成功
            if affected_rows > 0:
                # 直接返回1表示成功，不再尝试获取LAST_INSERT_ID
                return 1
            
            return None
        except Exception as e:
            print(f"添加充电站错误: {str(e)}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def check_station_code_exists(station_code):
        """检查充电站编号是否已存在
        
        Args:
            station_code: 充电站编号
            
        Returns:
            bool: 如果存在则返回True，否则返回False
        """
        try:
            query = "SELECT station_id FROM charging_stations WHERE station_code = %s"
            result = BaseDAO.execute_query(query, (station_code,))
            return bool(result)
        except Exception as e:
            print(f"检查充电站编号是否存在出错: {str(e)}")
            traceback.print_exc()
            return False 