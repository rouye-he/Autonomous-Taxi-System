from app.dao.base_dao import BaseDAO
import math
import traceback

class MapObstacleDAO(BaseDAO):
    """地图障碍物数据访问对象类，用于操作map_obstacles表"""
    
    @staticmethod
    def get_all_obstacles(page=1, per_page=10, city_code=None):
        """获取所有障碍物，支持分页和城市筛选"""
        try:
            # 计算分页偏移量
            offset = (page - 1) * per_page
            
            # 构建基础查询
            query = "SELECT * FROM map_obstacles"
            count_query = "SELECT COUNT(*) as count FROM map_obstacles"
            
            # 添加城市和激活状态筛选
            where_clauses = ["is_active = 1"]
            params = []
            
            if city_code:
                where_clauses.append("city_code = %s")
                params.append(city_code)
            
            # 拼接WHERE子句
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
                count_query += " WHERE " + " AND ".join(where_clauses)
            
            # 添加排序和分页
            query += " ORDER BY city_code, obstacle_type, id LIMIT %s, %s"
            params.extend([offset, per_page])
            
            # 执行查询
            obstacles = BaseDAO.execute_query(query, params)
            
            # 获取总数
            count_params = params[:-2] if params else []
            count_result = BaseDAO.execute_query(count_query, count_params)
            total_count = count_result[0]['count'] if count_result else 0
            
            # 计算总页数
            total_pages = math.ceil(total_count / per_page)
            
            return {
                'obstacles': obstacles,
                'current_page': page,
                'total_pages': total_pages,
                'total_count': total_count,
                'per_page': per_page
            }
        except Exception as e:
            print(f"获取障碍物列表错误: {str(e)}")
            traceback.print_exc()
            return {
                'obstacles': [],
                'current_page': page,
                'total_pages': 0,
                'total_count': 0,
                'per_page': per_page
            }
            
    @staticmethod
    def get_obstacle_by_id(obstacle_id):
        """根据ID获取单个障碍物详情"""
        try:
            query = "SELECT * FROM map_obstacles WHERE id = %s"
            params = (obstacle_id,)
            
            results = BaseDAO.execute_query(query, params)
            return results[0] if results else None
        except Exception as e:
            print(f"获取障碍物详情错误: {str(e)}")
            traceback.print_exc()
            return None
            
    @staticmethod
    def get_obstacles_by_city(city_code):
        """获取指定城市的所有激活障碍物"""
        try:
            query = """
            SELECT * FROM map_obstacles 
            WHERE city_code = %s AND is_active = 1
            ORDER BY obstacle_type, id
            """
            params = (city_code,)
            
            return BaseDAO.execute_query(query, params)
        except Exception as e:
            print(f"获取城市障碍物错误: {str(e)}")
            traceback.print_exc()
            return []
            
    @staticmethod
    def create_obstacle(data):
        """创建新障碍物"""
        try:
            query = """
            INSERT INTO map_obstacles 
            (city_code, obstacle_type, geometry_type, name, polygon_points, color, width, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                data.get('city_code'),
                data.get('obstacle_type'),
                data.get('geometry_type', 'polygon'),
                data.get('name'),
                data.get('polygon_points'),
                data.get('color'),
                data.get('width', 2),
                data.get('is_active', 1)
            )
            
            return BaseDAO.execute_update(query, params)
        except Exception as e:
            print(f"创建障碍物错误: {str(e)}")
            traceback.print_exc()
            return 0
            
    @staticmethod
    def update_obstacle(obstacle_id, data):
        """更新障碍物"""
        try:
            # 构建更新字段和参数
            update_fields = []
            params = []
            
            # 动态构建更新字段
            if 'city_code' in data:
                update_fields.append("city_code = %s")
                params.append(data['city_code'])
                
            if 'obstacle_type' in data:
                update_fields.append("obstacle_type = %s")
                params.append(data['obstacle_type'])
                
            if 'geometry_type' in data:
                update_fields.append("geometry_type = %s")
                params.append(data['geometry_type'])
                
            if 'name' in data:
                update_fields.append("name = %s")
                params.append(data['name'])
                
            if 'polygon_points' in data:
                update_fields.append("polygon_points = %s")
                params.append(data['polygon_points'])
                
            if 'color' in data:
                update_fields.append("color = %s")
                params.append(data['color'])
                
            if 'width' in data:
                update_fields.append("width = %s")
                params.append(data['width'])
                
            if 'is_active' in data:
                update_fields.append("is_active = %s")
                params.append(data['is_active'])
            
            # 如果没有要更新的字段，直接返回
            if not update_fields:
                return 0
                
            # 构建完整SQL
            query = f"UPDATE map_obstacles SET {', '.join(update_fields)} WHERE id = %s"
            params.append(obstacle_id)
            
            return BaseDAO.execute_update(query, params)
        except Exception as e:
            print(f"更新障碍物错误: {str(e)}")
            traceback.print_exc()
            return 0
            
    @staticmethod
    def delete_obstacle(obstacle_id):
        """删除障碍物"""
        try:
            query = "DELETE FROM map_obstacles WHERE id = %s"
            params = (obstacle_id,)
            
            return BaseDAO.execute_update(query, params)
        except Exception as e:
            print(f"删除障碍物错误: {str(e)}")
            traceback.print_exc()
            return 0
            
    @staticmethod
    def toggle_obstacle_active(obstacle_id, active_status):
        """切换障碍物激活状态"""
        try:
            query = "UPDATE map_obstacles SET is_active = %s WHERE id = %s"
            params = (1 if active_status else 0, obstacle_id)
            
            return BaseDAO.execute_update(query, params)
        except Exception as e:
            print(f"切换障碍物状态错误: {str(e)}")
            traceback.print_exc()
            return 0
            
    @staticmethod
    def is_point_in_any_obstacle(x, y, city_code):
        """检测点是否在任何障碍物内
        
        Args:
            x: 点的X坐标
            y: 点的Y坐标
            city_code: 城市代码
            
        Returns:
            bool: 是否在障碍物内
        """
        try:
            obstacles = MapObstacleDAO.get_obstacles_by_city(city_code)
            
            for obstacle in obstacles:
                # 线段类型不考虑点是否在内部
                if obstacle['geometry_type'] == 'line':
                    continue
                
                if MapObstacleDAO.is_point_in_polygon(x, y, obstacle['polygon_points']):
                    return True
                    
            return False
        except Exception as e:
            print(f"检测点是否在障碍物内错误: {str(e)}")
            traceback.print_exc()
            return False
            
    @staticmethod
    def is_point_in_polygon(x, y, polygon_points_str):
        """检测点是否在多边形内，使用射线法
        
        Args:
            x: 点的X坐标
            y: 点的Y坐标
            polygon_points_str: 多边形点集字符串 "x1,y1;x2,y2;..."
            
        Returns:
            bool: 点是否在多边形内
        """
        try:
            # 解析多边形点集
            points = []
            for point_str in polygon_points_str.split(';'):
                if ',' in point_str:
                    x_str, y_str = point_str.split(',')
                    points.append((float(x_str), float(y_str)))
                    
            if len(points) < 3:
                return False
                
            # 射线法判断点是否在多边形内
            inside = False
            j = len(points) - 1
            
            for i in range(len(points)):
                xi, yi = points[i]
                xj, yj = points[j]
                
                # 射线法核心判断
                intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi)
                if intersect:
                    inside = not inside
                    
                j = i
                
            return inside
        except Exception as e:
            print(f"多边形点检测错误: {str(e)}")
            traceback.print_exc()
            return False
            
    @staticmethod
    def does_line_intersect_any_obstacle(x1, y1, x2, y2, city_code):
        """检测线段是否与任何障碍物相交
        
        Args:
            x1, y1: 线段起点坐标
            x2, y2: 线段终点坐标
            city_code: 城市代码
            
        Returns:
            bool: 是否相交
        """
        try:
            obstacles = MapObstacleDAO.get_obstacles_by_city(city_code)
            
            for obstacle in obstacles:
                if MapObstacleDAO.does_line_intersect_polygon(
                    x1, y1, x2, y2, 
                    obstacle['polygon_points'], 
                    obstacle.get('geometry_type', 'polygon')
                ):
                    return True
                    
            return False
        except Exception as e:
            print(f"检测线段是否与障碍物相交错误: {str(e)}")
            traceback.print_exc()
            return False
            
    @staticmethod
    def does_line_intersect_polygon(x1, y1, x2, y2, polygon_points_str, geometry_type='polygon'):
        """检测线段是否与多边形边界相交
        
        Args:
            x1, y1: 线段起点坐标
            x2, y2: 线段终点坐标
            polygon_points_str: 多边形点集字符串
            geometry_type: 几何类型，'polygon'或'line'
            
        Returns:
            bool: 是否相交
        """
        try:
            # 解析多边形点集
            points = []
            for point_str in polygon_points_str.split(';'):
                if ',' in point_str:
                    px_str, py_str = point_str.split(',')
                    points.append((float(px_str), float(py_str)))
                    
            # 线段类型特殊处理
            if geometry_type == 'line':
                if len(points) == 2:
                    # 直接检查两条线段是否相交
                    x3, y3 = points[0]
                    x4, y4 = points[1]
                    return MapObstacleDAO.do_line_segments_intersect(x1, y1, x2, y2, x3, y3, x4, y4)
                return False
                    
            # 多边形类型处理
            if len(points) < 3:
                return False
                
            # 检查线段起点和终点是否在多边形内
            point1_in_polygon = MapObstacleDAO.is_point_in_polygon(x1, y1, polygon_points_str)
            point2_in_polygon = MapObstacleDAO.is_point_in_polygon(x2, y2, polygon_points_str)
            
            # 如果起点和终点都在多边形内，则线段在多边形内
            if point1_in_polygon and point2_in_polygon:
                return True
                
            # 如果只有一个点在多边形内，则线段与多边形相交
            if point1_in_polygon or point2_in_polygon:
                return True
                
            # 检查线段是否与多边形的任何边相交
            j = len(points) - 1
            
            for i in range(len(points)):
                x3, y3 = points[i]
                x4, y4 = points[j]
                
                # 检查两线段是否相交
                if MapObstacleDAO.do_line_segments_intersect(x1, y1, x2, y2, x3, y3, x4, y4):
                    return True
                    
                j = i
                
            return False
        except Exception as e:
            print(f"检测线段与多边形相交错误: {str(e)}")
            traceback.print_exc()
            return False
            
    @staticmethod
    def do_line_segments_intersect(x1, y1, x2, y2, x3, y3, x4, y4):
        """判断两条线段是否相交
        
        Args:
            x1, y1, x2, y2: 第一条线段的端点
            x3, y3, x4, y4: 第二条线段的端点
            
        Returns:
            bool: 线段是否相交
        """
        # 计算方向
        def direction(xi, yi, xj, yj, xk, yk):
            return (xk - xi) * (yj - yi) - (xj - xi) * (yk - yi)
            
        # 判断点是否在线段上
        def on_segment(xi, yi, xj, yj, xk, yk):
            return (min(xi, xj) <= xk <= max(xi, xj) and 
                    min(yi, yj) <= yk <= max(yi, yj))
        
        # 计算四个方向值
        d1 = direction(x3, y3, x4, y4, x1, y1)
        d2 = direction(x3, y3, x4, y4, x2, y2)
        d3 = direction(x1, y1, x2, y2, x3, y3)
        d4 = direction(x1, y1, x2, y2, x4, y4)
        
        # 判断线段是否相交
        if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
           ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
            return True
            
        # 特殊情况：线段共线且重叠
        if d1 == 0 and on_segment(x3, y3, x4, y4, x1, y1):
            return True
        if d2 == 0 and on_segment(x3, y3, x4, y4, x2, y2):
            return True
        if d3 == 0 and on_segment(x1, y1, x2, y2, x3, y3):
            return True
        if d4 == 0 and on_segment(x1, y1, x2, y2, x4, y4):
            return True
            
        return False 