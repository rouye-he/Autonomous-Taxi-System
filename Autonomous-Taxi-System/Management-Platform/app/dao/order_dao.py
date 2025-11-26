import traceback
from datetime import datetime
import random
from app.dao.base_dao import BaseDAO
import os
import re

class OrderDAO(BaseDAO):
    """订单数据访问对象，封装所有订单相关的数据库操作 - 简化版"""
    
    @staticmethod
    def get_all_orders(page=1, per_page=10):
        """获取所有订单数据"""
        try:
            # 计算总记录数
            count_query = "SELECT COUNT(*) as total FROM orders"
            count_result = BaseDAO.execute_query(count_query)
            total_count = count_result[0]['total'] if count_result else 0
            
            # 计算分页参数
            offset = (page - 1) * per_page
            
            # 查询当前页的订单数据
            orders_query = """
            SELECT 
                o.order_id, o.order_number, o.user_id, o.vehicle_id, o.order_status,
                o.create_time, o.arrival_time,
                o.pickup_location, o.dropoff_location, o.city_code,
                u.username, u.real_name,
                v.plate_number, v.model
            FROM 
                orders o
                LEFT JOIN users u ON o.user_id = u.user_id
                LEFT JOIN vehicles v ON o.vehicle_id = v.vehicle_id
            ORDER BY o.create_time DESC
            LIMIT %s OFFSET %s
            """
            
            orders = BaseDAO.execute_query(orders_query, (per_page, offset))
            
            # 处理日期格式和其他格式化
            for order in orders:
                OrderDAO._format_order_data(order)
            
            # 获取订单状态统计
            status_counts = {
                'all': total_count,
                'waiting': 0,
                'in_progress': 0,
                'completed': 0,
                'cancelled': 0
            }
            
            # 统计所有订单的状态分布
            status_query = """
            SELECT order_status, COUNT(*) as count
            FROM orders
            GROUP BY order_status
            """
            
            status_results = BaseDAO.execute_query(status_query)
            
            for status in status_results:
                if status['order_status'] == '待分配':
                    status_counts['waiting'] += status['count']
                elif status['order_status'] == '待支付':
                    status_counts['waiting'] += status['count']
                elif status['order_status'] == '已支付待出行':
                    status_counts['waiting'] += status['count']
                elif status['order_status'] == '进行中':
                    status_counts['in_progress'] = status['count']
                elif status['order_status'] == '已结束':
                    status_counts['completed'] = status['count']
                elif status['order_status'] == '已取消':
                    status_counts['cancelled'] = status['count']
            
            return {
                'orders': orders,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page if total_count > 0 else 1,
                'current_page': page,
                'per_page': per_page,
                'status_counts': status_counts
            }
        except Exception as e:
            print(f"获取所有订单数据错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def get_orders_by_criteria(criteria, offset=0, limit=10):
        """按条件搜索订单"""
        try:
            # 构建SQL查询的WHERE子句
            where_clauses = []
            params = []
            
            # 处理订单ID查询
            if 'order_id' in criteria:
                where_clauses.append("o.order_id = %s")
                params.append(criteria['order_id'])
                
            if 'order_number' in criteria:
                where_clauses.append("o.order_number LIKE %s")
                params.append(f"%{criteria['order_number']}%")
                
            if 'user_id' in criteria:
                where_clauses.append("o.user_id = %s")
                params.append(criteria['user_id'])
                
            if 'vehicle_id' in criteria:
                where_clauses.append("o.vehicle_id = %s")
                params.append(criteria['vehicle_id'])
                
            if 'city_code' in criteria:
                where_clauses.append("o.city_code = %s")
                params.append(criteria['city_code'])
                
            if 'order_status' in criteria:
                where_clauses.append("o.order_status = %s")
                params.append(criteria['order_status'])
                
            # 处理位置查询参数
            if 'pickup_location' in criteria:
                where_clauses.append("o.pickup_location LIKE %s")
                params.append(f"%{criteria['pickup_location']}%")
                
            if 'dropoff_location' in criteria:
                where_clauses.append("o.dropoff_location LIKE %s")
                params.append(f"%{criteria['dropoff_location']}%")
                
            # 处理时间范围查询参数
            if 'create_time_start' in criteria:
                where_clauses.append("o.create_time >= %s")
                params.append(criteria['create_time_start'])
                
            if 'create_time_end' in criteria:
                where_clauses.append("o.create_time <= %s")
                params.append(criteria['create_time_end'])
                
            if 'arrival_time_start' in criteria:
                where_clauses.append("o.arrival_time >= %s")
                params.append(criteria['arrival_time_start'])
                
            if 'arrival_time_end' in criteria:
                where_clauses.append("o.arrival_time <= %s")
                params.append(criteria['arrival_time_end'])
                
            # 构建WHERE子句
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
                
            # 计算总数
            count_query = f"""
            SELECT COUNT(*) as total 
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.user_id
            LEFT JOIN vehicles v ON o.vehicle_id = v.vehicle_id
            {where_clause}
            """
            
            count_result = BaseDAO.execute_query(count_query, params)
            total_count = count_result[0]['total'] if count_result else 0
            
            # 获取分页数据
            query = f"""
            SELECT 
                o.order_id, o.order_number, o.user_id, o.vehicle_id, 
                o.pickup_location, o.dropoff_location, 
                o.create_time, o.arrival_time,
                o.order_status, o.city_code,
                u.username, u.real_name, u.phone, u.email,
                v.plate_number, v.model, v.current_location_name,
                v.current_location_x, v.current_location_y
            FROM 
                orders o
            LEFT JOIN 
                users u ON o.user_id = u.user_id
            LEFT JOIN 
                vehicles v ON o.vehicle_id = v.vehicle_id
            {where_clause}
            ORDER BY 
                o.create_time DESC
            LIMIT %s OFFSET %s
            """
            
            all_params = params + [limit, offset]
            orders = BaseDAO.execute_query(query, all_params)
            
            # 格式化订单数据
            formatted_orders = []
            for order in orders:
                formatted_orders.append(OrderDAO._format_order_data(order))
            
            # 获取状态统计数据
            status_counts = {
                'all': total_count,
                'waiting': 0,
                'in_progress': 0,
                'completed': 0,
                'cancelled': 0
            }
            
            # 统计不同状态的订单数量
            if total_count > 0:
                status_query = f"""
                SELECT order_status, COUNT(*) as count
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.user_id
                LEFT JOIN vehicles v ON o.vehicle_id = v.vehicle_id
                {where_clause}
                GROUP BY order_status
                """
                
                status_results = BaseDAO.execute_query(status_query, params)
                
                for status in status_results:
                    if status['order_status'] == '待分配':
                        status_counts['waiting'] += status['count']
                    elif status['order_status'] == '待支付':
                        status_counts['waiting'] += status['count']
                    elif status['order_status'] == '已支付待出行':
                        status_counts['waiting'] += status['count']
                    elif status['order_status'] == '进行中':
                        status_counts['in_progress'] = status['count']
                    elif status['order_status'] == '已结束':
                        status_counts['completed'] = status['count']
                    elif status['order_status'] == '已取消':
                        status_counts['cancelled'] = status['count']
            
            return total_count, formatted_orders, status_counts
        except Exception as e:
            print(f"按条件搜索订单失败: {str(e)}")
            traceback.print_exc()
            raise e
            
    @staticmethod
    def get_order_by_id(order_id):
        """获取订单详情"""
        try:
            query = """
            SELECT 
                o.order_id, o.order_number, o.user_id, o.vehicle_id, o.order_status,
                o.create_time, o.arrival_time,
                o.pickup_location, o.dropoff_location, o.city_code,
                o.pickup_location_x, o.pickup_location_y, o.dropoff_location_x, o.dropoff_location_y,
                u.username, u.real_name, u.phone, u.email,
                v.plate_number, v.model, v.current_location_name,
                v.current_location_x, v.current_location_y
            FROM orders o
                LEFT JOIN users u ON o.user_id = u.user_id
                LEFT JOIN vehicles v ON o.vehicle_id = v.vehicle_id
            WHERE o.order_id = %s
            """
            
            orders = BaseDAO.execute_query(query, (order_id,))
            
            if orders:
                order = orders[0]
                OrderDAO._format_order_data(order)
                return order
                
            return None
        except Exception as e:
            print(f"获取订单详情错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def get_city_orders(city):
        """获取指定城市的订单数据"""
        try:
            # 城市代码与中文名映射
            city_names = {
                'shanghai': '上海市',
                'beijing': '北京市',
                'guangzhou': '广州市',
                'shenzhen': '深圳市',
                'hangzhou': '杭州市',
                'nanjing': '南京市',
                'chengdu': '成都市',
                'chongqing': '重庆市',
                'wuhan': '武汉市',
                'xian': '西安市',
                'shenyang': '沈阳市'
            }
            
            # 如果传入的是城市代码，转换为中文名
            city_name = city_names.get(city, city)
            
            query = """
            SELECT 
                o.order_id, o.order_number, o.user_id, o.vehicle_id, o.order_status,
                o.create_time, o.arrival_time, 
                o.pickup_location, o.dropoff_location, o.city_code,
                u.username, u.real_name,
                v.plate_number, v.model
            FROM orders o
                LEFT JOIN users u ON o.user_id = u.user_id
                LEFT JOIN vehicles v ON o.vehicle_id = v.vehicle_id
            WHERE o.city_code = %s OR %s = 'all'
            ORDER BY o.create_time DESC
            """
            
            orders = BaseDAO.execute_query(query, (city_name, city_name))
            
            # 处理日期格式和其他格式化
            for order in orders:
                OrderDAO._format_order_data(order)
            
            return orders
        except Exception as e:
            print(f"获取城市订单数据错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def update_order_status(order_id, status):
        """更新订单状态"""
        try:
            query = """
            UPDATE orders
            SET order_status = %s
            WHERE order_id = %s
            """
            
            affected_rows = BaseDAO.execute_update(query, (status, order_id))
            return affected_rows > 0
        except Exception as e:
            print(f"更新订单状态错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def create_order(order_data):
        """创建新订单"""
        try:
            # 生成订单编号（年月日+随机6位数）
            now = datetime.now()
            order_number = f"O{now.strftime('%Y%m%d')}{random.randint(100000, 999999)}"
            
            query = """
            INSERT INTO orders (
                order_number, user_id, vehicle_id, order_status,
                create_time, arrival_time, pickup_location, 
                dropoff_location, city_code
            ) VALUES (
                %s, %s, %s, %s, 
                NOW(), %s, %s, 
                %s, %s
            )
            """
            
            params = (
                order_number,
                order_data.get('user_id'),
                order_data.get('vehicle_id'),
                order_data.get('order_status', '待分配'),
                order_data.get('arrival_time'),
                order_data.get('pickup_location'),
                order_data.get('dropoff_location'),
                order_data.get('city_code')
            )
            
            affected_rows = BaseDAO.execute_update(query, params)
            
            if affected_rows > 0:
                # 获取新创建的订单ID
                order_id_query = "SELECT order_id FROM orders WHERE order_number = %s"
                result = BaseDAO.execute_query(order_id_query, (order_number,))
                if result:
                    return result[0]['order_id']
            
            return None
        except Exception as e:
            print(f"创建订单错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def assign_vehicle(order_id, vehicle_id):
        """分配车辆到订单"""
        try:
            query = """
            UPDATE orders
            SET vehicle_id = %s, order_status = '进行中'
            WHERE order_id = %s
            """
            
            affected_rows = BaseDAO.execute_update(query, (vehicle_id, order_id))
            return affected_rows > 0
        except Exception as e:
            print(f"分配车辆错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def cancel_order(order_id):
        """取消订单"""
        try:
            query = """
            UPDATE orders
            SET order_status = '已取消'
            WHERE order_id = %s
            """
            
            affected_rows = BaseDAO.execute_update(query, (order_id,))
            return affected_rows > 0
        except Exception as e:
            print(f"取消订单错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def get_user_orders(user_id, page=1, per_page=10):
        """获取用户的订单"""
        try:
            # 计算总记录数
            count_query = "SELECT COUNT(*) as total FROM orders WHERE user_id = %s"
            count_result = BaseDAO.execute_query(count_query, (user_id,))
            total_count = count_result[0]['total'] if count_result else 0
            
            # 计算分页参数
            offset = (page - 1) * per_page
            
            # 查询当前页的订单数据
            orders_query = """
            SELECT 
                o.order_id, o.order_number, o.user_id, o.vehicle_id, o.order_status,
                o.create_time, o.arrival_time,
                o.pickup_location, o.dropoff_location, o.city_code,
                v.plate_number, v.model
            FROM 
                orders o
                LEFT JOIN vehicles v ON o.vehicle_id = v.vehicle_id
            WHERE 
                o.user_id = %s
            ORDER BY o.create_time DESC
            LIMIT %s OFFSET %s
            """
            
            orders = BaseDAO.execute_query(orders_query, (user_id, per_page, offset))
            
            # 处理日期格式和其他格式化
            for order in orders:
                OrderDAO._format_order_data(order)
            
            return {
                'orders': orders,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page if total_count > 0 else 1,
                'current_page': page,
                'per_page': per_page
            }
        except Exception as e:
            print(f"获取用户订单错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def get_vehicle_orders(vehicle_id, page=1, per_page=10):
        """获取车辆的订单"""
        try:
            # 计算总记录数
            count_query = "SELECT COUNT(*) as total FROM orders WHERE vehicle_id = %s"
            count_result = BaseDAO.execute_query(count_query, (vehicle_id,))
            total_count = count_result[0]['total'] if count_result else 0
            
            # 计算分页参数
            offset = (page - 1) * per_page
            
            # 查询当前页的订单数据
            orders_query = """
            SELECT 
                o.order_id, o.order_number, o.user_id, o.vehicle_id, o.order_status,
                o.create_time, o.arrival_time,
                o.pickup_location, o.dropoff_location, o.city_code,
                u.username, u.real_name
            FROM 
                orders o
                LEFT JOIN users u ON o.user_id = u.user_id
            WHERE 
                o.vehicle_id = %s
            ORDER BY o.create_time DESC
            LIMIT %s OFFSET %s
            """
            
            orders = BaseDAO.execute_query(orders_query, (vehicle_id, per_page, offset))
            
            # 处理日期格式和其他格式化
            for order in orders:
                OrderDAO._format_order_data(order)
            
            return {
                'orders': orders,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page if total_count > 0 else 1,
                'current_page': page,
                'per_page': per_page
            }
        except Exception as e:
            print(f"获取车辆订单错误: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def _format_order_data(order):
        """格式化订单数据 - 简化版"""
        # 处理日期格式
        date_fields = ['create_time', 'arrival_time']
        for field in date_fields:
            if field in order and order[field]:
                order[field] = order[field].strftime('%Y-%m-%d %H:%M:%S')
        
        return order
    
    @staticmethod
    def get_waiting_order_ids(criteria):
        """获取符合条件的待分配订单ID列表"""
        try:
            # 构建WHERE子句和参数
            where_clauses = []
            params = []
            
            # 处理基本查询参数
            if 'order_number' in criteria:
                where_clauses.append("o.order_number LIKE %s")
                params.append(f"%{criteria['order_number']}%")
                
            if 'user_id' in criteria:
                where_clauses.append("o.user_id = %s")
                params.append(criteria['user_id'])
                
            if 'vehicle_id' in criteria:
                where_clauses.append("o.vehicle_id = %s")
                params.append(criteria['vehicle_id'])
                
            if 'city_code' in criteria:
                where_clauses.append("o.city_code = %s")
                params.append(criteria['city_code'])
                
            # 确保只查询待分配状态的订单
            where_clauses.append("o.order_status = %s")
            params.append('待分配')
                
            # 处理位置查询参数
            if 'pickup_location' in criteria:
                where_clauses.append("o.pickup_location LIKE %s")
                params.append(f"%{criteria['pickup_location']}%")
                
            if 'dropoff_location' in criteria:
                where_clauses.append("o.dropoff_location LIKE %s")
                params.append(f"%{criteria['dropoff_location']}%")
                
            # 处理时间范围查询参数
            if 'create_time_start' in criteria:
                where_clauses.append("o.create_time >= %s")
                params.append(criteria['create_time_start'])
                
            if 'create_time_end' in criteria:
                where_clauses.append("o.create_time <= %s")
                params.append(criteria['create_time_end'])
                
            if 'arrival_time_start' in criteria:
                where_clauses.append("o.arrival_time >= %s")
                params.append(criteria['arrival_time_start'])
                
            if 'arrival_time_end' in criteria:
                where_clauses.append("o.arrival_time <= %s")
                params.append(criteria['arrival_time_end'])
                
            # 构建WHERE子句
            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)
                
            # 查询订单ID
            query = f"""
            SELECT o.order_id
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.user_id
            LEFT JOIN vehicles v ON o.vehicle_id = v.vehicle_id
            {where_clause}
            ORDER BY o.create_time ASC
            """
            
            results = BaseDAO.execute_query(query, params)
            
            # 提取ID列表
            order_ids = [result['order_id'] for result in results]
            
            return order_ids
            
        except Exception as e:
            print(f"获取待分配订单ID失败: {str(e)}")
            traceback.print_exc()
            raise e
    
    @staticmethod
    def calculate_order_distance(pickup_x, pickup_y, dropoff_x, dropoff_y, city_code):
        """计算订单距离（公里）
        
        Args:
            pickup_x: 上车点X坐标
            pickup_y: 上车点Y坐标
            dropoff_x: 下车点X坐标
            dropoff_y: 下车点Y坐标
            city_code: 城市代码
            
        Returns:
            float: 订单距离（公里）
        """
        try:
            # 计算欧氏距离
            dx = dropoff_x - pickup_x
            dy = dropoff_y - pickup_y
            distance_in_units = ((dx ** 2 + dy ** 2) ** 0.5)  # 系统距离单位
            
            # 使用城市距离转换比例将距离单位转换为公里
            try:
                from app.config.vehicle_params import CITY_DISTANCE_RATIO
                
                # 获取城市的距离转换比例
                city_ratio = CITY_DISTANCE_RATIO.get(city_code, 0.1)  # 默认使用0.1如果找不到匹配的城市
                
                # 计算实际公里数
                distance = distance_in_units * city_ratio
                distance = round(distance, 2)  # 保留两位小数
                
            except ImportError:
                # 如果导入失败，使用旧的计算方式
                print("无法导入CITY_DISTANCE_RATIO，使用默认转换比例0.1")
                distance = distance_in_units * 0.1
                distance = round(distance, 2)
                
            return distance
        except Exception as e:
            print(f"计算订单距离错误: {str(e)}")
            traceback.print_exc()
            return 0
    
    @staticmethod
    def calculate_order_amount(distance, vehicle_id, vehicle_model, city_code):
        """计算订单原始金额
        
        Args:
            distance: 行驶距离（公里）
            vehicle_id: 车辆ID
            vehicle_model: 车辆型号
            city_code: 城市代码
            
        Returns:
            float: 订单原始金额
        """
        try:
            from app.config.vehicle_params import ORDER_BASE_PRICE, ORDER_PRICE_PER_KM, ORDER_BASE_KM
            from app.config.vehicle_params import get_city_order_price_factor
            
            # 获取城市和城市价格系数
            city_price_factor = get_city_order_price_factor(city_code)
            
            # 获取车辆订单价格系数
            order_price_coefficient = 1.0  # 默认价格系数为1.0
            
            if vehicle_model:
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
            
            return amount, order_price_coefficient, city_price_factor
        except Exception as e:
            print(f"计算订单金额错误: {str(e)}")
            traceback.print_exc()
            return 0, 1.0, 1.0
    
    @staticmethod
    def find_best_coupon(user_id, original_amount):
        """查找最佳优惠券
        
        Args:
            user_id: 用户ID
            original_amount: 订单原始金额
            
        Returns:
            tuple: (最佳优惠券, 优惠金额, 最终金额)
        """
        try:
            # 查询用户可用的优惠券（未使用且在有效期内）
            coupon_query = """
            SELECT c.coupon_id, c.coupon_type_id, ct.coupon_category, ct.value, ct.min_amount, ct.description
            FROM coupons c
            JOIN coupon_types ct ON c.coupon_type_id = ct.id
            WHERE c.user_id = %s 
              AND c.status = '未使用'
              AND NOW() BETWEEN c.validity_start AND c.validity_end
            """
            coupons = BaseDAO.execute_query(coupon_query, (user_id,))
            
            # 初始化优惠券相关变量
            best_coupon = None
            max_discount = 0
            final_amount = original_amount  # 默认为原价
            discount_amount = 0
            
            # 筛选出满足订单金额条件的优惠券，找出最优惠的一张
            for coupon in coupons:
                # 检查是否满足使用门槛
                if original_amount < coupon['min_amount']:
                    continue
                
                # 计算优惠金额
                if coupon['coupon_category'] == '满减券':
                    # 满减券直接减去指定金额
                    current_discount = float(coupon['value'])
                elif coupon['coupon_category'] == '折扣券':
                    # 折扣券，例如0.8表示8折，优惠为原价的20%
                    current_discount = original_amount * (1 - float(coupon['value']))
                else:
                    continue
                
                # 更新最优惠券
                if current_discount > max_discount:
                    max_discount = current_discount
                    best_coupon = coupon
            
            # 应用优惠券折扣
            if best_coupon:
                discount_amount = max_discount
                final_amount = original_amount - discount_amount
                final_amount = max(final_amount, 0)  # 确保金额不小于0
                final_amount = round(final_amount, 2)  # 保留两位小数
            else:
                # 如果没有可用优惠券，最终金额就是原始金额
                final_amount = original_amount
            
            return best_coupon, discount_amount, final_amount
        except Exception as e:
            print(f"查找最佳优惠券错误: {str(e)}")
            traceback.print_exc()
            return None, 0, original_amount
    
    @staticmethod
    def apply_coupon(order_id, coupon_id, discount_amount):
        """应用优惠券至订单
        
        Args:
            order_id: 订单ID
            coupon_id: 优惠券ID
            discount_amount: 优惠金额
            
        Returns:
            bool: 是否应用成功
        """
        try:
            # 更新优惠券状态为已使用
            update_coupon_query = """
            UPDATE coupons
            SET status = '已使用', use_time = NOW(), order_id = %s
            WHERE coupon_id = %s
            """
            affected_rows = BaseDAO.execute_update(update_coupon_query, (order_id, coupon_id))
            
            if affected_rows > 0:
                return True
            else:
                print(f"订单 {order_id} 应用优惠券 ID:{coupon_id} 失败")
                return False
        except Exception as e:
            print(f"应用优惠券错误: {str(e)}")
            traceback.print_exc()
            return False
    
    @staticmethod
    def process_user_payment(user_id, amount, payment_method):
        """处理用户支付
        
        Args:
            user_id: 用户ID
            amount: 支付金额
            payment_method: 支付方式
            
        Returns:
            bool: 支付是否成功
        """
        try:
            # 如果支付方式是"余额支付"，则扣减用户余额
            if payment_method == '余额支付':
                # 获取用户当前余额
                user_query = "SELECT balance FROM users WHERE user_id = %s"
                user_result = BaseDAO.execute_query(user_query, (user_id,))
                
                if user_result:
                    current_balance = user_result[0]['balance']
                    # 转换类型并计算新的余额
                    current_balance_float = float(current_balance) if current_balance else 0
                    new_balance = current_balance_float - float(amount)
                    new_balance = round(new_balance, 2)  # 保留两位小数
                    
                    # 更新用户余额
                    balance_update_query = """
                    UPDATE users
                    SET balance = %s
                    WHERE user_id = %s
                    """
                    balance_updated = BaseDAO.execute_update(balance_update_query, (new_balance, user_id))
                    
                    if balance_updated <= 0:
                        print(f"更新用户 {user_id} 余额失败")
                        return False
                    return True
                else:
                    print(f"获取用户 {user_id} 余额信息失败")
                    return False
            
            # 其他支付方式不需要处理用户余额
            return True
        except Exception as e:
            print(f"处理用户支付错误: {str(e)}")
            traceback.print_exc()
            return False
    
    @staticmethod
    def create_income_record(order_id, user_id, amount, payment_method, distance, vehicle_info, city_price_factor, price_coefficient, coupon_info=None):
        """创建收入记录
        
        Args:
            order_id: 订单ID
            user_id: 用户ID
            amount: 订单金额（优惠后）
            payment_method: 支付方式
            distance: 行驶距离
            vehicle_info: 车辆信息（型号、车牌等）
            city_price_factor: 城市价格系数
            price_coefficient: 车辆价格系数
            coupon_info: 优惠券信息（可选）
            
        Returns:
            int: 收入记录ID，失败返回None
        """
        try:
            # 如果是余额支付，则不添加收入记录（应该在充值时算作充值收入）
            if payment_method == '余额支付':
                return None
                
            from datetime import datetime
            from app.dao.income_dao import IncomeDAO
            
            # 准备收入记录的数据
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # 添加优惠券信息到描述中
            coupon_desc = ""
            if coupon_info:
                coupon_id, discount = coupon_info
                coupon_desc = f"，使用了优惠券(ID:{coupon_id})，优惠金额:{discount}元"
            
            description = f"订单{order_id}的车费，支付方式：{payment_method}，车辆：{vehicle_info.get('plate_number', '未知')}，车型：{vehicle_info.get('model', '未知')}，距离：{distance}公里，价格系数：{price_coefficient}，城市价格系数：{city_price_factor}{coupon_desc}"
            
            # 调用IncomeDAO添加收入记录
            income_id = IncomeDAO.add_income(
                amount=amount,  # 使用优惠后的金额
                source="车费收入",
                user_id=user_id,
                order_id=str(order_id),  # 确保传递订单ID
                date=current_date,
                description=description
            )
            
            if income_id:
                print(f"为订单 {order_id} 创建收入记录成功")
                return income_id
            else:
                print(f"为订单 {order_id} 创建收入记录失败")
                return None
                
        except Exception as e:
            print(f"创建收入记录错误: {str(e)}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def create_order_detail_record(order_id, vehicle_id, user_id, amount, distance, payment_method):
        """创建订单详情记录
        
        Args:
            order_id: 订单ID
            vehicle_id: 车辆ID
            user_id: 用户ID
            amount: 订单金额（优惠后）
            distance: 行驶距离
            payment_method: 支付方式
            
        Returns:
            int: 订单详情ID，失败返回None
        """
        try:
            from app.dao.order_details_dao import OrderDetailsDAO
            
            # 准备订单详情数据
            order_details_data = {
                "order_id": str(order_id),  # 确保转换为字符串类型
                "vehicle_id": vehicle_id,
                "user_id": user_id,
                "amount": amount,  # 记录优惠后的价格
                "distance": distance,
                "payment_method": payment_method
            }
            
            # 创建订单详情记录
            details_id = OrderDetailsDAO.create_order_details(order_details_data)
            
            if details_id:
                return details_id
            else:
                return None
                
        except Exception as e:
            print(f"创建订单详情记录错误: {str(e)}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def update_order_completion(order_id, arrival_time):
        """
        更新订单为完成状态
        
        Args:
            order_id (int): 订单ID
            arrival_time (str): 到达时间
            
        Returns:
            dict: 包含操作结果的字典，keys: success, message
        """
        try:
            # 获取订单当前信息和车辆ID
            query = """
            SELECT o.order_id, o.order_status, o.vehicle_id, o.user_id, 
                   o.pickup_location, o.dropoff_location,
                   o.pickup_location_x, o.pickup_location_y,
                   o.dropoff_location_x, o.dropoff_location_y,
                   o.city_code, v.plate_number, v.model
            FROM orders o
            LEFT JOIN vehicles v ON o.vehicle_id = v.vehicle_id
            WHERE o.order_id = %s
            """
            result = BaseDAO.execute_query(query, (order_id,))
            
            if not result:
                return {"success": False, "message": f"订单 {order_id} 不存在"}
                
            order_data = result[0]
            
            # 检查当前状态是否允许更新为完成
            current_status = order_data['order_status']
            vehicle_id = order_data['vehicle_id']
            user_id = order_data['user_id']
            city_code = order_data['city_code']  # 获取城市代码
            
            # 使用硬编码的状态值，不再尝试检测枚举
            if current_status in ['已结束', '已完成', 3]:
                return {"success": False, "message": "订单已经是完成状态"}
                
            if current_status in ['已取消', 4]:
                return {"success": False, "message": "订单已取消，无法更新为完成状态"}
                
            if current_status in ['已评价', 5]:
                return {"success": False, "message": "订单已评价，无法再次更新"}
            
            # 直接使用硬编码的状态值
            if isinstance(current_status, str):
                new_status_value = '已结束'
            else:
                new_status_value = 3
                
            # 更新订单状态为完成
            update_query = """
            UPDATE orders
            SET order_status = %s, arrival_time = %s
            WHERE order_id = %s
            """
            
            try:
                affected_rows = BaseDAO.execute_update(update_query, (new_status_value, arrival_time, order_id))
                
                if affected_rows <= 0:
                    # 尝试使用数字状态
                    if isinstance(new_status_value, str):
                        new_status_value = 3
                        affected_rows = BaseDAO.execute_update(update_query, (new_status_value, arrival_time, order_id))
                
                if affected_rows <= 0:
                    return {"success": False, "message": "更新订单状态失败"}
            except Exception as update_error:
                print(f"更新订单状态错误: {str(update_error)}")
                traceback.print_exc()
                return {"success": False, "message": f"更新订单状态错误: {str(update_error)}"}
            
            # 如果是从"进行中"到"已完成"状态，处理后续操作
            if current_status in ['进行中', 2]:
                try:
                    # 1. 计算行驶距离
                    distance = OrderDAO.calculate_order_distance(
                        order_data['pickup_location_x'], 
                        order_data['pickup_location_y'],
                        order_data['dropoff_location_x'], 
                        order_data['dropoff_location_y'],
                        city_code
                    )
                    
                    # 2. 更新车辆统计信息（里程和订单数）
                    from app.dao import VehicleDAO
                    update_success = VehicleDAO.update_vehicle_statistics(vehicle_id, distance)
                    
                    # 3. 计算订单原始金额
                    original_amount, price_coefficient, city_price_factor = OrderDAO.calculate_order_amount(
                        distance, 
                        vehicle_id, 
                        order_data.get('model'), 
                        city_code
                    )
                    
                    # 4. 查找最佳优惠券并计算优惠后金额
                    best_coupon, discount_amount, final_amount = OrderDAO.find_best_coupon(user_id, original_amount)
                    
                    # 5. 应用优惠券（如果有）
                    coupon_info = None
                    if best_coupon:
                        OrderDAO.apply_coupon(order_id, best_coupon['coupon_id'], discount_amount)
                        coupon_info = (best_coupon['coupon_id'], discount_amount)
                    
                    # 6. 获取支付方式
                    from app.config.vehicle_params import get_weighted_payment_method
                    payment_method = get_weighted_payment_method(city_code)
                    
                    # 7. 处理用户支付
                    payment_success = OrderDAO.process_user_payment(user_id, final_amount, payment_method)
                    if not payment_success:
                        print(f"订单 {order_id} 支付处理失败，但继续处理订单完成流程")
                    
                    # 8. 创建收入记录（如果不是余额支付）
                    if payment_method != '余额支付':
                        income_id = OrderDAO.create_income_record(
                            order_id, 
                            user_id, 
                            final_amount, 
                            payment_method, 
                            distance, 
                            order_data, 
                            city_price_factor, 
                            price_coefficient, 
                            coupon_info
                        )
                    
                    # 9. 创建订单详情记录
                    order_detail_id = OrderDAO.create_order_detail_record(
                        order_id, 
                        vehicle_id, 
                        user_id, 
                        final_amount, 
                        distance, 
                        payment_method
                    )
                    
                    
                    # 10. 更新用户信用积分
                    OrderDAO.update_user_credit_score(user_id, order_id)
                    
                except Exception as e:
                    print(f"订单完成后续处理出错: {str(e)}")
                    traceback.print_exc()
                    return {"success": True, "message": "订单状态已更新，但后续处理出现错误"}
                    
            return {"success": True, "message": "订单状态已更新为已结束"}
            
        except Exception as e:
            print(f"更新订单为完成状态出错: {str(e)}")
            traceback.print_exc()
            return {"success": False, "message": f"更新订单为完成状态出错: {str(e)}"}
    
    @staticmethod
    def update_user_credit_score(user_id, order_id=None):
        """
        更新用户信用积分:
        1. 每次下单完成增加1信用积分
        2. 如果是用户当天第一次下单，额外增加1信用积分
        
        Args:
            user_id (int): 用户ID
            order_id (int, optional): 订单ID
            
        Returns:
            bool: 更新是否成功
        """
        try:
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 检查今日是否是用户第一个完成的订单
            check_query = """
            SELECT COUNT(*) as order_count
            FROM orders
            WHERE user_id = %s 
              AND order_status IN ('已结束', '已完成', 3)
              AND DATE(arrival_time) = %s
            """
            result = BaseDAO.execute_query(check_query, (user_id, today))
            
            # 检查是否是当天首单
            is_first_order_today = result[0]['order_count'] <= 1  # 包括当前订单
            
            # 获取用户当前信用分
            query_user = """
            SELECT credit_score FROM users
            WHERE user_id = %s
            """
            user_result = BaseDAO.execute_query(query_user, (user_id,))
            
            if not user_result:
                print(f"未找到用户 {user_id} 的信用积分信息")
                return False
            
            current_credit = user_result[0]['credit_score'] or 0
            
            # 导入用户信用日志DAO
            from app.dao.user_credit_log_dao import UserCreditLogDAO
            success = True
            
            # 首先记录订单完成基础积分（+1分）
            base_new_credit = current_credit + 1
            update_query = """
            UPDATE users
            SET credit_score = %s
            WHERE user_id = %s
            """
            affected_rows = BaseDAO.execute_update(update_query, (base_new_credit, user_id))
            
            if affected_rows > 0:
                
                # 记录基础积分变动
                base_log_id = UserCreditLogDAO.add_credit_log(
                    user_id=user_id,
                    change_amount=1,  # 基础增加1分
                    credit_before=current_credit,
                    credit_after=base_new_credit,
                    change_type="订单完成",
                    reason="订单完成获得基础积分",
                    related_order_id=str(order_id) if order_id else None,
                    operator="system"
                )
                
      
                
                # 如果是当天首单，再额外增加1分
                if is_first_order_today:
                    first_order_credit = base_new_credit + 1
                    update_query = """
                    UPDATE users
                    SET credit_score = %s
                    WHERE user_id = %s
                    """
                    affected_rows = BaseDAO.execute_update(update_query, (first_order_credit, user_id))
                    
                    if affected_rows > 0:
                        
                        # 记录首单额外积分变动
                        first_log_id = UserCreditLogDAO.add_credit_log(
                            user_id=user_id,
                            change_amount=1,  # 首单额外增加1分
                            credit_before=base_new_credit,
                            credit_after=first_order_credit,
                            change_type="系统奖励",  # 使用不同的变动类型
                            reason="当日首单额外奖励",
                            related_order_id=str(order_id) if order_id else None,
                            operator="system"
                        )
                        
                  
                    else:
                        print(f"更新用户 {user_id} 首单额外积分失败")
                        success = False
                
                return success
            else:
                print(f"更新用户 {user_id} 信用积分失败")
                return False
                
        except Exception as e:
            print(f"更新用户信用积分出错: {str(e)}")
            traceback.print_exc()
            return False
    
    @staticmethod
    def bulk_create_orders(city_code, order_count):
        """批量添加订单 - 修改为随机坐标起点/终点

        Args:
            city_code: 城市名称(中文名)
            order_count: 要添加的订单数量

        Returns:
            字典包含：成功添加的订单数量和已创建订单的用户ID列表
        """
        try:
            # 获取指定城市的用户ID列表
            users_query = "SELECT user_id FROM users WHERE registration_city = %s"
            users_result = BaseDAO.execute_query(users_query, (city_code,))
            user_ids = [row['user_id'] for row in users_result] if users_result else []

            if not user_ids:
                raise Exception(f"城市 {city_code} 没有可用的用户，无法创建订单")

            # 准备批量插入的数据
            now = datetime.now()
            order_data_list = []
            GRID_SIZE = 1000 # 定义网格大小
            created_user_ids = []  # 用于存储已创建订单的用户ID

            for i in range(order_count):
                # 随机选择用户ID
                user_id = random.choice(user_ids) if user_ids else random.randint(1, 10)
                created_user_ids.append(user_id)  # 记录用户ID

                # 生成订单编号
                order_number = f"O{now.strftime('%Y%m%d')}{random.randint(100000, 999999)}"

                # 创建时间
                create_time = now.strftime('%Y-%m-%d %H:%M:%S')

                # --- 修改开始：生成随机坐标作为起点和终点 ---
                pickup_location_x = random.randint(0, GRID_SIZE - 1)
                pickup_location_y = random.randint(0, GRID_SIZE - 1)

                dropoff_location_x = random.randint(0, GRID_SIZE - 1)
                dropoff_location_y = random.randint(0, GRID_SIZE - 1)

                # 确保上下车坐标不太近
                min_distance = 50  # 最小距离
                while True:
                    dx = dropoff_location_x - pickup_location_x
                    dy = dropoff_location_y - pickup_location_y
                    # 计算欧氏距离的平方，避免开方运算提高效率
                    if (dx**2 + dy**2) >= min_distance**2:
                        break
                    # 如果太近，重新生成下车点坐标
                    dropoff_location_x = random.randint(0, GRID_SIZE - 1)
                    dropoff_location_y = random.randint(0, GRID_SIZE - 1)

                # 将地点名称格式化为坐标字符串
                pickup_location = f"({pickup_location_x}, {pickup_location_y})"
                dropoff_location = f"({dropoff_location_x}, {dropoff_location_y})"
                # --- 修改结束 ---

                # 添加到批量插入数据列表
                order_data_list.append((
                    order_number, user_id, None, '待分配', create_time, None,
                    pickup_location, pickup_location_x, pickup_location_y,
                    dropoff_location, dropoff_location_x, dropoff_location_y, city_code
                ))

            # 批量插入订单数据
            insert_order_query = """
            INSERT INTO orders
            (order_number, user_id, vehicle_id, order_status, create_time, arrival_time,
            pickup_location, pickup_location_x, pickup_location_y,
            dropoff_location, dropoff_location_x, dropoff_location_y, city_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            batch_size = 100
            success_count = 0
            successful_user_ids = []  # 存储成功创建订单的用户ID

            for i in range(0, len(order_data_list), batch_size):
                batch = order_data_list[i:i + batch_size]
                batch_user_ids = created_user_ids[i:i + batch_size]  # 当前批次的用户ID
                try:
                    BaseDAO.execute_batch(insert_order_query, batch)
                    success_count += len(batch)
                    successful_user_ids.extend(batch_user_ids)  # 添加成功创建订单的用户ID
                except Exception as e:
                    print(f"批量插入订单数据失败: {str(e)}")
                    traceback.print_exc()

            return {
                "success_count": success_count,
                "user_ids": successful_user_ids
            }

        except Exception as e:
            print(f"批量添加订单失败: {str(e)}")
            traceback.print_exc()
            return {
                "success_count": 0,
                "user_ids": []
            } 