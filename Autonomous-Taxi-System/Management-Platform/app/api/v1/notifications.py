from flask import jsonify, request
from app.api.v1 import api_v1
from app.dao.notification_dao import NotificationDAO
import traceback

@api_v1.route('/notifications/unread_count', methods=['GET'])
def get_unread_notifications_count():
    """获取未读通知数量API"""
    try:
        count = NotificationDAO.get_unread_count()
        return jsonify({
            'status': 'success',
            'count': count
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取未读通知数量失败: {str(e)}',
            'count': 0
        })

@api_v1.route('/notifications/latest', methods=['GET'])
def get_latest_notifications():
    """获取最新通知API"""
    try:
        limit = request.args.get('limit', 5, type=int)
        notifications = NotificationDAO.get_unread_notifications(limit)
        return jsonify({
            'status': 'success',
            'data': notifications
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取最新通知失败: {str(e)}',
            'data': []
        })

@api_v1.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    """标记通知为已读API"""
    try:
        NotificationDAO.mark_as_read(notification_id)
        return jsonify({
            'status': 'success',
            'message': '已将通知标记为已读'
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'标记通知为已读失败: {str(e)}'
        })

@api_v1.route('/notifications/mark_all_read', methods=['POST'])
def mark_all_notifications_read():
    """标记所有通知为已读API"""
    try:
        affected_rows = NotificationDAO.mark_all_as_read()
        return jsonify({
            'status': 'success',
            'message': f'已将{affected_rows}条通知标记为已读'
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'标记所有通知为已读失败: {str(e)}'
        })

@api_v1.route('/notifications/create', methods=['POST'])
def create_notification():
    """创建新通知API"""
    try:
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': '请求数据为空'
            })
        
        title = data.get('title')
        content = data.get('content')
        type = data.get('type')
        priority = data.get('priority', '通知')
        
        if not title or not content or not type:
            return jsonify({
                'status': 'error',
                'message': '标题、内容和类型不能为空'
            })
        
        NotificationDAO.create_notification(title, content, type, priority)
        
        return jsonify({
            'status': 'success',
            'message': '通知创建成功'
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'创建通知失败: {str(e)}'
        }) 