import traceback
from datetime import datetime
from app.dao.base_dao import BaseDAO

class UserCreditLogDAO(BaseDAO):
    """用户信用变动记录数据访问对象，封装所有信用记录相关的数据库操作"""
    
    @staticmethod
    def get_credit_logs(offset=0, limit=10, user_id=None, change_type=None, 
                       date_from=None, date_to=None, sort="created_at", order="DESC", search=None):
        """获取信用变动记录，支持分页和筛选
        
        Args:
            offset: 偏移量（从第几条记录开始）
            limit: 每页记录数（0表示不限制记录数）
            user_id: 筛选特定用户ID（可选）
            change_type: 筛选特定变动类型（可选）
            date_from: 开始日期（可选）
            date_to: 结束日期（可选）
            sort: 排序字段
            order: 排序方向（升序ASC/降序DESC）
            search: 全局搜索关键词（可选）
            
        Returns:
            tuple: (总记录数, 当前页数据列表)
        """
        try:
            # 构建查询条件
            conditions = []
            params = []
            
            if user_id:
                conditions.append("l.user_id = %s")
                params.append(user_id)
            
            if change_type:
                conditions.append("l.change_type = %s")
                params.append(change_type)
            
            if date_from:
                conditions.append("l.created_at >= %s")
                params.append(f"{date_from} 00:00:00")
            
            if date_to:
                conditions.append("l.created_at <= %s")
                params.append(f"{date_to} 23:59:59")
            
            # 添加全局搜索
            if search and search.strip():
                search_term = f"%{search.strip()}%"
                search_conditions = [
                    "l.reason LIKE %s",
                    "l.change_type LIKE %s",
                    "l.related_order_id LIKE %s",
                    "u.username LIKE %s",
                    "l.operator LIKE %s",
                    "CAST(l.user_id AS CHAR) LIKE %s",
                    "CAST(l.log_id AS CHAR) LIKE %s"
                ]
                conditions.append("(" + " OR ".join(search_conditions) + ")")
                # 为每个条件添加相同的搜索词
                params.extend([search_term] * len(search_conditions))
            
            # 构建WHERE子句
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            # 获取总记录数
            count_sql = f"SELECT COUNT(*) as total FROM user_credit_logs l LEFT JOIN users u ON l.user_id = u.user_id {where_clause}"
            count_result = BaseDAO.execute_query(count_sql, params)
            total = count_result[0]["total"] if count_result else 0
            
            print(f"SQL查询条件: {where_clause}")
            print(f"参数: {params}")
            print(f"总记录数: {total}")
            
            # 有效的排序字段
            valid_sort_fields = ["log_id", "change_amount", "credit_before", "credit_after", "created_at"]
            if sort not in valid_sort_fields:
                sort = "created_at"
            
            order_direction = "DESC" if order.lower() == "desc" else "ASC"
            
            # 获取分页数据
            if total > 0:
                # 构建查询SQL
                data_sql = f"""
                    SELECT l.*, u.username
                    FROM user_credit_logs l
                    LEFT JOIN users u ON l.user_id = u.user_id
                    {where_clause}
                    ORDER BY l.{sort} {order_direction}
                """
                
                # 如果limit > 0，添加LIMIT子句
                if limit > 0:
                    data_sql += " LIMIT %s OFFSET %s"
                    params.extend([limit, offset])
                
                logs = BaseDAO.execute_query(data_sql, params)
                
                # 格式化日期
                for log in logs:
                    if 'created_at' in log and log['created_at']:
                        log['created_at'] = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                
                return total, logs
            
            return 0, []
        except Exception as e:
            print(f"获取信用变动记录失败: {str(e)}")
            traceback.print_exc()
            return 0, []
    
    @staticmethod
    def add_credit_log(user_id, change_amount, credit_before, credit_after, change_type, 
                       reason, related_order_id=None, operator=None):
        """添加信用变动记录
        
        Args:
            user_id: 用户ID
            change_amount: 变动分值
            credit_before: 变动前信用分
            credit_after: 变动后信用分
            change_type: 变动类型
            reason: 变动原因
            related_order_id: 关联订单ID（可选）
            operator: 操作人（可选）
            
        Returns:
            int: 新增记录的ID，失败返回0
        """
        try:
            # 准备插入数据
            fields = [
                "user_id", "change_amount", "credit_before", "credit_after", 
                "change_type", "reason", "related_order_id", "operator"
            ]
            
            values = [
                user_id, change_amount, credit_before, credit_after, 
                change_type, reason, related_order_id, operator
            ]
            
            # 构建SQL语句
            placeholders = ', '.join(['%s'] * len(fields))
            fields_str = ', '.join(fields)
            
            query = f"INSERT INTO user_credit_logs ({fields_str}) VALUES ({placeholders})"
            
            # 执行插入操作
            affected_rows = BaseDAO.execute_update(query, values)
            
            if affected_rows > 0:
                # 获取最后插入的ID
                get_id_query = "SELECT LAST_INSERT_ID() as last_id"
                result = BaseDAO.execute_query(get_id_query)
                if result and 'last_id' in result[0]:
                    return result[0]['last_id']
                return 1  # 至少插入成功了
            return 0
        except Exception as e:
            print(f"添加信用变动记录失败: {str(e)}")
            traceback.print_exc()
            return 0
    
    @staticmethod
    def get_user_credit_history(user_id, limit=10):
        """获取指定用户的信用变动历史
        
        Args:
            user_id: 用户ID
            limit: 返回记录数量限制
            
        Returns:
            list: 信用变动历史记录列表
        """
        try:
            query = """
            SELECT *
            FROM user_credit_logs
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """
            
            params = (user_id, limit)
            logs = BaseDAO.execute_query(query, params)
            
            # 格式化日期
            for log in logs:
                if 'created_at' in log and log['created_at']:
                    log['created_at'] = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return logs
        except Exception as e:
            print(f"获取用户信用历史失败: {str(e)}")
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_credit_log_by_id(log_id):
        """根据ID获取信用变动记录详情
        
        Args:
            log_id: 记录ID
            
        Returns:
            dict: 信用变动记录详情，如果不存在返回None
        """
        try:
            query = """
            SELECT l.*, u.username
            FROM user_credit_logs l
            LEFT JOIN users u ON l.user_id = u.user_id
            WHERE l.log_id = %s
            """
            
            logs = BaseDAO.execute_query(query, (log_id,))
            
            if not logs:
                return None
            
            log = logs[0]
            if 'created_at' in log and log['created_at']:
                log['created_at'] = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return log
        except Exception as e:
            print(f"根据ID获取信用变动记录失败: {str(e)}")
            traceback.print_exc()
            return None

    @staticmethod
    def get_statistics_by_change_type(start_date=None, end_date=None):
        """获取信用变动类型统计数据
        
        Args:
            start_date: 开始日期（可选，格式：YYYY-MM-DD）
            end_date: 结束日期（可选，格式：YYYY-MM-DD）
            
        Returns:
            list: 各类型的变动次数和总分值统计
        """
        try:
            conditions = []
            params = []
            
            if start_date:
                conditions.append("created_at >= %s")
                params.append(f"{start_date} 00:00:00")
            
            if end_date:
                conditions.append("created_at <= %s")
                params.append(f"{end_date} 23:59:59")
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
            SELECT 
                change_type,
                COUNT(*) as count,
                SUM(change_amount) as total_amount
            FROM 
                user_credit_logs
            {where_clause}
            GROUP BY 
                change_type
            ORDER BY 
                count DESC
            """
            
            result = BaseDAO.execute_query(query, params)
            return result
        except Exception as e:
            print(f"获取信用变动类型统计失败: {str(e)}")
            traceback.print_exc()
            return []
    
    @staticmethod
    def delete_credit_log(log_id):
        """删除信用变动记录（管理员功能）
        
        Args:
            log_id: 记录ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            query = "DELETE FROM user_credit_logs WHERE log_id = %s"
            affected_rows = BaseDAO.execute_update(query, (log_id,))
            
            return affected_rows > 0
        except Exception as e:
            print(f"删除信用变动记录失败: {str(e)}")
            traceback.print_exc()
            return False 