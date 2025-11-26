from app.dao.notification_dao import NotificationDAO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """
    通知服务工具类
    用于系统各部分创建不同类型的通知
    """
    
    @staticmethod
    def create_vehicle_notification(title, content, priority='通知'):
        """
        创建车辆相关通知
        
        参数:
            title (str): 通知标题
            content (str): 通知内容
            priority (str): 优先级，可选值为'通知'或'警告'，默认为'通知'
        
        返回:
            int: 新创建通知的ID
        """
        try:
            notification_id = NotificationDAO.create_notification(
                title=title,
                content=content,
                type='vehicle',
                priority=priority
            )
            logger.info(f"已创建车辆通知: {title}")
            
            # 通过WebSocket发送通知
            NotificationService._emit_notification(
                notification_id=notification_id,
                title=title,
                content=content,
                type='vehicle',
                priority=priority
            )
            
            return notification_id
        except Exception as e:
            logger.error(f"创建车辆通知失败: {str(e)}")
            return None
    
    @staticmethod
    def create_order_notification(title, content, priority='通知'):
        """
        创建订单相关通知
        
        参数:
            title (str): 通知标题
            content (str): 通知内容
            priority (str): 优先级，可选值为'通知'或'警告'，默认为'通知'
        
        返回:
            int: 新创建通知的ID
        """
        try:
            notification_id = NotificationDAO.create_notification(
                title=title,
                content=content,
                type='order',
                priority=priority
            )
            logger.info(f"已创建订单通知: {title}")
            
            # 通过WebSocket发送通知
            NotificationService._emit_notification(
                notification_id=notification_id,
                title=title,
                content=content,
                type='order',
                priority=priority
            )
            
            return notification_id
        except Exception as e:
            logger.error(f"创建订单通知失败: {str(e)}")
            return None
    
    @staticmethod
    def create_system_notification(title, content, priority='通知'):
        """
        创建系统相关通知
        
        参数:
            title (str): 通知标题
            content (str): 通知内容
            priority (str): 优先级，可选值为'通知'或'警告'，默认为'通知'
        
        返回:
            int: 新创建通知的ID
        """
        try:
            notification_id = NotificationDAO.create_notification(
                title=title,
                content=content,
                type='system',
                priority=priority
            )
    
            
            # 通过WebSocket发送通知
            NotificationService._emit_notification(
                notification_id=notification_id,
                title=title,
                content=content,
                type='system',
                priority=priority
            )
            
            return notification_id
        except Exception as e:
            logger.error(f"创建系统通知失败: {str(e)}")
            return None
            
    @staticmethod
    def _emit_notification(notification_id, title, content, type, priority):
        """
        通过WebSocket发送通知
        
        参数:
            notification_id (int): 通知ID
            title (str): 通知标题
            content (str): 通知内容
            type (str): 通知类型
            priority (str): 优先级
        """
        try:
            # 构造通知数据
            notification_data = {
                'id': notification_id,
                'title': title,
                'content': content,
                'type': type,
                'priority': priority,
                'created_at': datetime.now().isoformat(),
                'status': '未读'
            }
            
            # 在函数内部动态导入socketio，避免循环导入
            from app import socketio
            # 发送WebSocket事件
            socketio.emit('new_notification', notification_data)
        except Exception as e:
            logger.error(f"通过WebSocket发送通知失败: {str(e)}")
    
    @staticmethod
    def notify_vehicle_low_battery(vehicle_id, battery_level, plate_number=None):
        """
        通知车辆电量不足
        
        参数:
            vehicle_id (int): 车辆ID
            battery_level (float): 当前电量百分比
            plate_number (str): 车牌号，如果不提供则只显示ID
        
        返回:
            int: 新创建通知的ID
        """
        # 如果未提供车牌号，尝试从数据库获取
        if not plate_number:
            try:
                from app.dao.vehicle_dao import VehicleDAO
                vehicle = VehicleDAO.get_vehicle_by_id(vehicle_id)
                if vehicle and vehicle.get('plate_number'):
                    plate_number = vehicle.get('plate_number')
            except Exception as e:
                logger.error(f"获取车辆信息失败: {str(e)}")
        
        # 构建通知内容
        title = f"车辆电量不足警告"
        vehicle_desc = f"{plate_number} (ID:{vehicle_id})" if plate_number else f"ID:{vehicle_id}"
        content = f"车辆 {vehicle_desc} 当前电量为 {battery_level}%，需要及时救援。"
        
        return NotificationService.create_vehicle_notification(title, content, priority='警告')
    
    @staticmethod
    def notify_vehicle_maintenance_required(vehicle_id, reason):
        """
        通知车辆需要维护
        
        参数:
            vehicle_id (int): 车辆ID
            reason (str): 维护原因
        
        返回:
            int: 新创建通知的ID
        """
        title = f"车辆需要维护"
        content = f"车辆ID-{vehicle_id}需要进行维护，原因: {reason}"
        return NotificationService.create_vehicle_notification(title, content, priority='警告')
    
    @staticmethod
    def notify_vehicle_status_changed(vehicle_id, old_status, new_status):
        """
        通知车辆状态变更
        
        参数:
            vehicle_id (int): 车辆ID
            old_status (str): 原状态
            new_status (str): 新状态
        
        返回:
            int: 新创建通知的ID
        """
        title = f"车辆状态变更"
        content = f'车辆ID-{vehicle_id}状态已从"{old_status}"变更为"{new_status}"'
        return NotificationService.create_vehicle_notification(title, content)
    
    @staticmethod
    def notify_new_order(order_id, origin, destination):
        """
        通知新订单创建
        
        参数:
            order_id (int): 订单ID
            origin (str): 起点
            destination (str): 终点
        
        返回:
            int: 新创建通知的ID
        """
        title = f"新订单创建"
        content = f"订单ID-{order_id}已创建，行程从{origin}到{destination}"
        return NotificationService.create_order_notification(title, content)
    
    @staticmethod
    def notify_order_completed(order_id, duration, distance, amount):
        """
        通知订单完成
        
        参数:
            order_id (int): 订单ID
            duration (int): 行程时长(分钟)
            distance (float): 行程距离(公里)
            amount (float): 订单金额(元)
        
        返回:
            int: 新创建通知的ID
        """
        title = f"订单已完成"
        content = f"订单ID-{order_id}已完成，行程时长{duration}分钟，距离{distance}公里，金额{amount}元"
        return NotificationService.create_order_notification(title, content)
    
    @staticmethod
    def notify_order_cancelled(order_id, reason):
        """
        通知订单取消
        
        参数:
            order_id (int): 订单ID
            reason (str): 取消原因
        
        返回:
            int: 新创建通知的ID
        """
        title = f"订单已取消"
        content = f"订单ID-{order_id}已取消，原因: {reason}"
        return NotificationService.create_order_notification(title, content, priority='警告')
    
    @staticmethod
    def notify_system_startup():
        """
        通知系统启动
        
        返回:
            int: 新创建通知的ID
        """
        title = "系统已启动"
        content = f"无人驾驶出租车管理平台已于{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}成功启动"
        return NotificationService.create_system_notification(title, content)
    
    @staticmethod
    def notify_system_shutdown():
        """
        通知系统关闭
        
        返回:
            int: 新创建通知的ID
        """
        title = "系统已关闭"
        content = f"无人驾驶出租车管理平台已于{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}关闭"
        return NotificationService.create_system_notification(title, content)
    
    @staticmethod
    def notify_system_error(error_message):
        """
        通知系统错误
        
        参数:
            error_message (str): 错误信息
        
        返回:
            int: 新创建通知的ID
        """
        title = "系统错误"
        content = f"系统发生错误: {error_message}"
        return NotificationService.create_system_notification(title, content, priority='警告') 