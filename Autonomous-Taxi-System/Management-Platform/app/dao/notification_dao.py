from app.dao.base_dao import BaseDAO
from app.models.notification import SystemNotification
import math
from datetime import datetime
import traceback

class NotificationDAO(BaseDAO):
    """系统通知数据访问对象"""
    
    @staticmethod
    def get_all_notifications(page=1, per_page=10, status=None):
        """获取所有通知，支持分页和状态筛选"""
        offset = (page - 1) * per_page
        
        # 构建基础查询
        query = "SELECT * FROM system_notifications"
        count_query = "SELECT COUNT(*) as count FROM system_notifications"
        
        # 状态筛选
        where_clauses = []
        params = []
        
        if status:
            where_clauses.append("status = %s")
            params.append(status)
        
        # 添加WHERE子句
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            count_query += " WHERE " + " AND ".join(where_clauses)
        
        # 添加排序和分页
        query += " ORDER BY created_at DESC LIMIT %s, %s"
        params.extend([offset, per_page])
        
        # 执行查询
        notifications = NotificationDAO.execute_query(query, params)
        
        # 获取总数
        count_result = NotificationDAO.execute_query(count_query, params[:-2] if params else None)
        total_count = count_result[0]['count'] if count_result else 0
        
        # 计算总页数
        total_pages = math.ceil(total_count / per_page)
        
        # 获取状态统计
        status_counts = NotificationDAO.get_notification_status_counts()
        
        return {
            'notifications': notifications,
            'current_page': page,
            'total_pages': total_pages,
            'total_count': total_count,
            'per_page': per_page,
            'status_counts': status_counts
        }
    
    @staticmethod
    def get_notifications_by_criteria(criteria, page=1, per_page=10):
        """根据条件查询通知"""
        offset = (page - 1) * per_page
        
        # 构建基础查询
        query = "SELECT * FROM system_notifications"
        count_query = "SELECT COUNT(*) as count FROM system_notifications"
        
        # 处理搜索条件
        where_clauses = []
        params = []
        
        if 'type' in criteria and criteria['type']:
            where_clauses.append("type = %s")
            params.append(criteria['type'])
        
        if 'priority' in criteria and criteria['priority']:
            where_clauses.append("priority = %s")
            params.append(criteria['priority'])
        
        if 'status' in criteria and criteria['status']:
            where_clauses.append("status = %s")
            params.append(criteria['status'])
        
        if 'title' in criteria and criteria['title']:
            where_clauses.append("title LIKE %s")
            params.append(f"%{criteria['title']}%")
        
        if 'content' in criteria and criteria['content']:
            where_clauses.append("content LIKE %s")
            params.append(f"%{criteria['content']}%")
        
        if 'created_after' in criteria and criteria['created_after']:
            where_clauses.append("created_at >= %s")
            params.append(criteria['created_after'])
        
        if 'created_before' in criteria and criteria['created_before']:
            where_clauses.append("created_at <= %s")
            params.append(criteria['created_before'])
            
        # 添加WHERE子句
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            count_query += " WHERE " + " AND ".join(where_clauses)
        
        # 添加排序和分页
        query += " ORDER BY created_at DESC LIMIT %s, %s"
        params.extend([offset, per_page])
        
        # 执行查询
        notifications = NotificationDAO.execute_query(query, params)
        
        # 获取总数
        count_result = NotificationDAO.execute_query(count_query, params[:-2] if params else None)
        total_count = count_result[0]['count'] if count_result else 0
        
        # 计算总页数
        total_pages = math.ceil(total_count / per_page)
        
        # 获取状态统计
        status_counts = NotificationDAO.get_notification_status_counts()
        
        return {
            'notifications': notifications,
            'current_page': page,
            'total_pages': total_pages,
            'total_count': total_count,
            'per_page': per_page,
            'status_counts': status_counts
        }
    
    @staticmethod
    def get_notification_by_id(notification_id):
        """根据ID获取通知"""
        query = "SELECT * FROM system_notifications WHERE id = %s"
        params = (notification_id,)
        
        results = NotificationDAO.execute_query(query, params)
        
        return results[0] if results else None
    
    @staticmethod
    def get_unread_notifications(limit=5):
        """获取未读通知"""
        query = "SELECT * FROM system_notifications WHERE status = '未读' ORDER BY created_at DESC LIMIT %s"
        params = (limit,)
        
        return NotificationDAO.execute_query(query, params)
    
    @staticmethod
    def get_unread_count():
        """获取未读通知数量"""
        query = "SELECT COUNT(*) as count FROM system_notifications WHERE status = '未读'"
        
        result = NotificationDAO.execute_query(query)
        
        return result[0]['count'] if result else 0
    
    @staticmethod
    def mark_as_read(notification_id):
        """将通知标记为已读"""
        query = "UPDATE system_notifications SET status = '已读', read_at = %s WHERE id = %s"
        params = (datetime.now(), notification_id)
        
        return NotificationDAO.execute_update(query, params)
    
    @staticmethod
    def mark_all_as_read():
        """将所有通知标记为已读"""
        query = "UPDATE system_notifications SET status = '已读', read_at = %s WHERE status = '未读'"
        params = (datetime.now(),)
        
        return NotificationDAO.execute_update(query, params)
    
    @staticmethod
    def create_notification(title, content, type, priority='通知'):
        """创建新通知"""
        try:
            # 检查表结构是否有content列
            check_query = "SHOW COLUMNS FROM system_notifications LIKE 'content'"
            check_result = BaseDAO.execute_query(check_query)
            
            if check_result and len(check_result) > 0:
                # 存在content列，正常插入
                query = """
                INSERT INTO system_notifications 
                (title, content, type, priority, status, created_at) 
                VALUES (%s, %s, %s, %s, '未读', %s)
                """
                params = (title, content, type, priority, datetime.now())
            else:
                # 不存在content列，将内容附加到标题中
                # 将内容添加到标题上，以便在没有content列的情况下也能显示完整信息
                combined_title = f"{title} - {content}"
                if len(combined_title) > 100:  # 标题字段最大长度限制
                    combined_title = combined_title[:97] + "..."
                
                query = """
                INSERT INTO system_notifications 
                (title, type, priority, status, created_at) 
                VALUES (%s, %s, %s, '未读', %s)
                """
                params = (combined_title, type, priority, datetime.now())
                
                print(f"警告: system_notifications表缺少content列，将内容与标题合并")
            
            return BaseDAO.execute_update(query, params)
        except Exception as e:
            print(f"创建通知失败: {str(e)}")
            traceback.print_exc()
            return 0
    
    @staticmethod
    def delete_notification(notification_id):
        """删除通知"""
        query = "DELETE FROM system_notifications WHERE id = %s"
        params = (notification_id,)
        
        return NotificationDAO.execute_update(query, params)
    
    @staticmethod
    def get_notification_status_counts():
        """获取各状态通知数量"""
        query = """
        SELECT 
            SUM(CASE WHEN status = '未读' THEN 1 ELSE 0 END) as unread,
            SUM(CASE WHEN status = '已读' THEN 1 ELSE 0 END) as `read`,
            COUNT(*) as total
        FROM 
            system_notifications
        """
        
        result = NotificationDAO.execute_query(query)
        
        if result:
            return {
                'unread': result[0]['unread'] or 0,
                'read': result[0]['read'] or 0,
                'total': result[0]['total'] or 0
            }
        
        return {
            'unread': 0,
            'read': 0,
            'total': 0
        }
    
    @staticmethod
    def update_notification_status(notification_id, status):
        """更新通知状态"""
        try:
            query = "UPDATE system_notifications SET status = %s, read_at = %s WHERE id = %s"
            params = (status, datetime.now() if status == '已读' else None, notification_id)
            
            affected_rows = NotificationDAO.execute_update(query, params)
            return affected_rows > 0
        except Exception as e:
            print(f"更新通知状态失败: {str(e)}")
            traceback.print_exc()
            return False 