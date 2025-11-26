from app.extensions import db
from datetime import datetime

class SystemNotification:
    """系统通知模型类"""
    
    def __init__(self, id=None, title=None, content=None, type=None, 
                 priority='通知', status='未读', created_at=None, read_at=None):
        """初始化通知对象"""
        self.id = id
        self.title = title
        self.content = content
        self.type = type
        self.priority = priority
        self.status = status
        self.created_at = created_at or datetime.now()
        self.read_at = read_at
        
    @staticmethod
    def from_dict(data):
        """从字典创建对象"""
        notification = SystemNotification()
        for key, value in data.items():
            if hasattr(notification, key):
                setattr(notification, key, value)
        return notification
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'type': self.type,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at,
            'read_at': self.read_at
        } 