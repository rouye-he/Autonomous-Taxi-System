from flask import Blueprint, render_template, jsonify, request, redirect, url_for, current_app
from app.dao.notification_dao import NotificationDAO
import traceback
from datetime import datetime
import json
from app.utils.flash_helper import flash_success, flash_error, flash_warning, flash_info

# 创建蓝图
notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/')
def index():
    """通知管理主页"""
    # 获取搜索参数
    search_params = {}
    for key, value in request.args.items():
        if value and key != 'page' and key != 'ajax' and key != 'include_stats':
            search_params[key] = value

    page = request.args.get('page', 1, type=int)
    
    # 如果有搜索参数，进行高级搜索
    if search_params:
        return advanced_search()
    
    try:
        # 使用NotificationDAO获取通知数据
        result = NotificationDAO.get_all_notifications(page=page, per_page=10)
        
        # 字段中文名映射
        field_names = {
            'type': '类型',
            'priority': '优先级',
            'status': '状态',
            'title': '标题',
            'content': '内容',
            'created_after': '创建时间(开始)',
            'created_before': '创建时间(结束)'
        }
        
        # 检查是否AJAX请求
        is_ajax = request.args.get('ajax') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            # 渲染部分模板（仅表格部分）
            html_content = render_template(
                'notifications/_notification_table.html',
                notifications=result['notifications'],
                current_page=result['current_page'],
                total_pages=result['total_pages'],
                total_count=result['total_count'],
                offset=(result['current_page'] - 1) * result['per_page'],
                per_page=result['per_page'],
                search_params={}
            )
            
            # 返回JSON响应，包含HTML和统计数据
            return jsonify({
                'html': html_content,
                'stats': result['status_counts'],
                'current_page': result['current_page'],
                'total_pages': result['total_pages']
            })
        else:
            # 返回完整页面
            return render_template('notifications/index.html',
                               notifications=result['notifications'],
                               current_page=result['current_page'],
                               total_pages=result['total_pages'],
                               total_count=result['total_count'],
                               offset=(result['current_page'] - 1) * result['per_page'],
                               per_page=result['per_page'],
                               field_names=field_names,
                               status_counts=result['status_counts'])
    
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"通知管理页面加载错误: {error_traceback}")
        
        if is_ajax:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
        else:
            return render_template('notifications/index.html', 
                              error=str(e), 
                              field_names={},
                              current_page=page,
                              total_pages=1,
                              total_count=0,
                              offset=0,
                              per_page=10,
                              notifications=[],
                              status_counts={
                                  'total': 0,
                                  'unread': 0,
                                  'read': 0
                              })

@notifications_bp.route('/advanced_search')
def advanced_search():
    """通知高级搜索"""
    # 获取搜索参数
    search_params = {}
    for key, value in request.args.items():
        if value and key != 'page' and key != 'ajax' and key != 'include_stats':
            search_params[key] = value
    
    page = request.args.get('page', 1, type=int)
    
    # 字段中文名映射
    field_names = {
        'type': '类型',
        'priority': '优先级',
        'status': '状态',
        'title': '标题',
        'content': '内容',
        'created_after': '创建时间(开始)',
        'created_before': '创建时间(结束)'
    }
    
    # 检查是否AJAX请求
    is_ajax = request.args.get('ajax') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    try:
        # 使用NotificationDAO根据条件获取通知数据
        result = NotificationDAO.get_notifications_by_criteria(search_params, page=page, per_page=10)
        
        if is_ajax:
            # 渲染部分模板（仅表格部分）
            html_content = render_template(
                'notifications/_notification_table.html',
                notifications=result['notifications'],
                current_page=result['current_page'],
                total_pages=result['total_pages'],
                total_count=result['total_count'],
                offset=(result['current_page'] - 1) * result['per_page'],
                per_page=result['per_page'],
                search_params=search_params
            )
            
            # 返回JSON响应，包含HTML和统计数据
            return jsonify({
                'html': html_content,
                'stats': result['status_counts'],
                'current_page': result['current_page'],
                'total_pages': result['total_pages']
            })
        else:
            # 返回完整页面
            return render_template('notifications/index.html', 
                               notifications=result['notifications'],
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
        print(f"通知高级搜索错误: {error_traceback}")
        
        if is_ajax:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
        else:
            return render_template('notifications/index.html', 
                              error=str(e), 
                              search_params=search_params,
                              field_names=field_names,
                              current_page=page,
                              total_pages=1, 
                              total_count=0,
                              offset=0,
                              per_page=10,
                              notifications=[],
                              status_counts={
                                  'total': 0,
                                  'unread': 0,
                                  'read': 0
                              })

@notifications_bp.route('/delete/<int:notification_id>', methods=['POST'])
def delete_notification(notification_id):
    """删除通知"""
    try:
        # 删除通知
        NotificationDAO.delete_notification(notification_id)
        
        # 获取最新的统计数据
        status_counts = NotificationDAO.get_notification_status_counts()
        
        # 检查是否AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            # 如果请求包含include_stats参数，则返回HTML和统计数据
            if request.args.get('include_stats') == '1':
                # 获取当前页码
                page = request.args.get('page', 1, type=int)
                
                # 获取最新的通知数据
                result = NotificationDAO.get_all_notifications(page=page, per_page=10)
                
                # 渲染新的HTML表格内容
                html_content = render_template(
                    'notifications/_notification_table.html',
                    notifications=result['notifications'],
                    current_page=result['current_page'],
                    total_pages=result['total_pages'],
                    total_count=result['total_count'],
                    offset=(result['current_page'] - 1) * result['per_page'],
                    per_page=result['per_page']
                )
                
                # 返回HTML和统计数据
                return jsonify({
                    'success': True,
                    'message': '通知已删除',
                    'html': html_content,
                    'stats': {
                        'total': status_counts.get('total', 0),
                        'unread': status_counts.get('unread', 0),
                        'read': status_counts.get('read', 0)
                    }
                })
            
            # 否则仅返回成功状态
            return jsonify({
                'success': True,
                'status': 'success',
                'message': '通知已删除',
                'stats': status_counts
            })
        else:
            # 非AJAX请求，重定向回列表页
            flash_success('通知已删除')
            return redirect(url_for('notifications.index'))
    except Exception as e:
        current_app.logger.error(f'删除通知出错: {str(e)}')
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'删除通知失败: {str(e)}'
        }), 500

@notifications_bp.route('/mark_read/<int:id>', methods=['POST'])
def mark_read(id):
    """将单个通知标记为已读"""
    try:
        # 获取通知记录
        notification = NotificationDAO.get_notification_by_id(id)
        
        if not notification:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': '通知不存在'
            }), 404
        
        # 检查通知状态
        already_read = notification.get('status') == '已读'
        
        # 如果通知已经是已读状态，则直接返回成功
        if already_read:
            status_counts = NotificationDAO.get_notification_status_counts()
            return jsonify({
                'success': True,
                'status': 'success',
                'message': '通知已经是已读状态',
                'already_read': True,
                'stats': status_counts
            })
        
        # 更新通知状态为已读
        result = NotificationDAO.update_notification_status(id, '已读')
        
        # 获取最新的统计数据
        status_counts = NotificationDAO.get_notification_status_counts()
        
        # 检查是否AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            # 如果请求包含include_stats参数，则返回HTML和统计数据
            if request.args.get('include_stats') == '1' and result:
                # 获取当前页码
                page = request.args.get('page', 1, type=int)
                
                # 获取最新的通知数据
                result = NotificationDAO.get_all_notifications(page=page, per_page=10)
                
                # 渲染新的HTML表格内容
                html_content = render_template(
                    'notifications/_notification_table.html',
                    notifications=result['notifications'],
                    current_page=result['current_page'],
                    total_pages=result['total_pages'],
                    total_count=result['total_count'],
                    offset=(result['current_page'] - 1) * result['per_page'],
                    per_page=result['per_page']
                )
                
                # 返回HTML和统计数据
                return jsonify({
                    'success': True,
                    'message': '已将通知标记为已读',
                    'already_read': False,
                    'html': html_content,
                    'stats': {
                        'total': status_counts.get('total', 0),
                        'unread': status_counts.get('unread', 0),
                        'read': status_counts.get('read', 0)
                    }
                })
            
            # 默认返回
            if result:
                return jsonify({
                    'success': True,
                    'status': 'success',
                    'message': '已将通知标记为已读',
                    'already_read': False,
                    'stats': status_counts
                })
            else:
                return jsonify({
                    'success': False,
                    'status': 'error',
                    'message': '标记为已读失败'
                }), 500
                
        else:
            # 非AJAX请求，重定向回列表页
            if result:
                flash_success('通知已标记为已读')
                return redirect(url_for('notifications.index'))
            else:
                flash_error('标记通知为已读失败')
                return redirect(url_for('notifications.index'))
                
    except Exception as e:
        current_app.logger.error(f'标记通知已读出错: {str(e)}')
        traceback.print_exc()
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'操作失败: {str(e)}'
        }), 500

@notifications_bp.route('/mark_all_read', methods=['POST'])
def mark_all_read():
    """标记所有通知为已读"""
    try:
        affected_rows = NotificationDAO.mark_all_as_read()
        
        # 获取最新的统计数据
        status_counts = NotificationDAO.get_notification_status_counts()
        
        # 检查是否AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            # 如果请求包含include_stats参数，则返回HTML和统计数据
            if request.args.get('include_stats') == '1':
                # 获取当前页码
                page = request.args.get('page', 1, type=int)
                
                # 获取最新的通知数据
                result = NotificationDAO.get_all_notifications(page=page, per_page=10)
                
                # 渲染新的HTML表格内容
                html_content = render_template(
                    'notifications/_notification_table.html',
                    notifications=result['notifications'],
                    current_page=result['current_page'],
                    total_pages=result['total_pages'],
                    total_count=result['total_count'],
                    offset=(result['current_page'] - 1) * result['per_page'],
                    per_page=result['per_page']
                )
                
                # 返回HTML和统计数据
                return jsonify({
                    'success': True,
                    'message': f'已将{affected_rows}条通知标记为已读',
                    'html': html_content,
                    'stats': {
                        'total': status_counts.get('total', 0),
                        'unread': status_counts.get('unread', 0),
                        'read': status_counts.get('read', 0)
                    }
                })
            
            # 默认返回
            return jsonify({
                'success': True,
                'status': 'success',
                'message': f'已将{affected_rows}条通知标记为已读',
                'stats': status_counts
            })
        else:
            # 非AJAX请求，重定向回列表页
            flash_success(f'已将{affected_rows}条通知标记为已读')
            return redirect(url_for('notifications.index'))
            
    except Exception as e:
        current_app.logger.error(f'标记所有通知为已读出错: {str(e)}')
        traceback.print_exc()
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'标记所有通知为已读失败: {str(e)}'
        }), 500

@notifications_bp.route('/api/unread_count', methods=['GET'])
def get_unread_count():
    """获取未读通知数量"""
    try:
        count = NotificationDAO.get_unread_count()
        return jsonify({
            'status': 'success',
            'count': count
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取未读通知数量失败: {str(e)}',
            'count': 0
        })

@notifications_bp.route('/api/latest', methods=['GET'])
def get_latest_notifications():
    """获取最新通知"""
    try:
        limit = request.args.get('limit', 5, type=int)
        notifications = NotificationDAO.get_unread_notifications(limit)
        return jsonify({
            'status': 'success',
            'data': notifications
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取最新通知失败: {str(e)}',
            'data': []
        })

@notifications_bp.route('/api/check_new', methods=['GET'])
def check_new_notifications():
    """检查是否有新通知API"""
    try:
        # 获取上次检查时间参数，如果没有则默认使用当前时间30分钟前
        since_time_str = request.args.get('since')
        
        if since_time_str:
            try:
                # 尝试解析ISO格式的时间字符串
                from datetime import datetime
                since_time = datetime.fromisoformat(since_time_str.replace('Z', '+00:00'))
            except ValueError:
                # 如果解析失败，使用默认值
                from datetime import datetime, timedelta
                since_time = datetime.now() - timedelta(minutes=30)
        else:
            # 如果没有提供时间参数，使用默认值
            from datetime import datetime, timedelta
            since_time = datetime.now() - timedelta(minutes=30)
        
        # 查询新通知
        query = """
        SELECT * FROM system_notifications 
        WHERE created_at > %s AND status = '未读'
        ORDER BY created_at DESC
        """
        
        new_notifications = NotificationDAO.execute_query(query, (since_time,))
        
        # 获取未读通知总数
        total_unread = NotificationDAO.get_unread_count()
        
        return jsonify({
            'status': 'success',
            'new_notifications': new_notifications,
            'total_unread': total_unread,
            'since': since_time.isoformat()
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'检查新通知失败: {str(e)}',
            'new_notifications': [],
            'total_unread': 0
        })

@notifications_bp.route('/api/create_test_notification', methods=['GET'])
def create_test_notification():
    """创建测试通知API"""
    try:
        # 导入所需模块
        from datetime import datetime
        import random
        
        # 生成测试标题和内容
        now = datetime.now()
        test_title = f"测试通知 - {now.strftime('%Y-%m-%d %H:%M:%S')}"
        test_content = f"这是一条测试通知，创建于 {now.strftime('%Y-%m-%d %H:%M:%S')}，请忽略此通知。"
        
        # 随机选择通知类型和优先级
        notification_types = ['system', 'vehicle', 'order']
        notification_priorities = ['通知', '警告']
        
        notification_type = random.choice(notification_types)
        notification_priority = random.choice(notification_priorities)
        
        # 创建通知
        notification = NotificationDAO.create_notification(
            title=test_title,
            content=test_content,
            type=notification_type,
            priority=notification_priority
        )
        
        # 网页请求则重定向回通知列表页面
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            flash_success('测试通知已创建')
            return redirect(url_for('notifications.index'))
            
        return jsonify({
            'status': 'success',
            'message': '测试通知已创建',
            'notification': notification
        })
    except Exception as e:
        current_app.logger.error(f'创建测试通知出错: {str(e)}')
        traceback.print_exc()
        
        # 网页请求则重定向回通知列表页面
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            flash_error(f'创建测试通知失败: {str(e)}')
            return redirect(url_for('notifications.index'))
            
        return jsonify({
            'status': 'error',
            'message': f'创建测试通知失败: {str(e)}'
        }), 500

@notifications_bp.route('/delete/batch', methods=['POST'])
def batch_delete_notifications():
    """批量删除通知"""
    try:
        # 从请求体中获取要删除的通知ID列表
        notification_ids = request.json.get('ids', [])
        
        if not notification_ids:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': '未选择要删除的通知'
            }), 400
        
        # 逐个删除通知
        deleted_count = 0
        for notification_id in notification_ids:
            try:
                success = NotificationDAO.delete_notification(notification_id)
                if success:
                    deleted_count += 1
            except Exception as e:
                current_app.logger.error(f'删除通知ID={notification_id}出错: {str(e)}')
        
        # 获取最新的统计数据
        status_counts = NotificationDAO.get_notification_status_counts()
        
        # 检查是否AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            # 如果请求包含include_stats参数，则返回HTML和统计数据
            if request.args.get('include_stats') == '1':
                # 获取当前页码
                page = request.args.get('page', 1, type=int)
                
                # 获取最新的通知数据
                result = NotificationDAO.get_all_notifications(page=page, per_page=10)
                
                # 渲染新的HTML表格内容
                html_content = render_template(
                    'notifications/_notification_table.html',
                    notifications=result['notifications'],
                    current_page=result['current_page'],
                    total_pages=result['total_pages'],
                    total_count=result['total_count'],
                    offset=(result['current_page'] - 1) * result['per_page'],
                    per_page=result['per_page']
                )
                
                # 返回HTML和统计数据
                return jsonify({
                    'success': True,
                    'message': f'已成功删除 {deleted_count} 条通知',
                    'html': html_content,
                    'stats': {
                        'total': status_counts.get('total', 0),
                        'unread': status_counts.get('unread', 0),
                        'read': status_counts.get('read', 0)
                    }
                })
            
            # 否则仅返回成功状态
            return jsonify({
                'success': True,
                'status': 'success',
                'message': f'已成功删除 {deleted_count} 条通知',
                'stats': status_counts
            })
        else:
            # 非AJAX请求，重定向回列表页
            flash_success(f'已成功删除 {deleted_count} 条通知')
            return redirect(url_for('notifications.index'))
            
    except Exception as e:
        current_app.logger.error(f'批量删除通知出错: {str(e)}')
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'批量删除通知失败: {str(e)}'
        }), 500

@notifications_bp.route('/delete/filtered', methods=['POST'])
def delete_filtered_notifications():
    """删除筛选结果的所有通知"""
    try:
        # 从请求中获取筛选条件
        search_params = {}
        for key in ['title', 'content', 'type', 'priority', 'status', 'created_after', 'created_before']:
            value = request.json.get(key, '')
            if value:
                search_params[key] = value
        
        # 如果没有筛选条件，则返回错误
        if not search_params:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': '未提供筛选条件，拒绝删除全部通知'
            }), 400
        
        # 使用筛选条件查询所有匹配的通知
        query = "SELECT id FROM system_notifications"
        where_clauses = []
        params = []
        
        if 'type' in search_params and search_params['type']:
            where_clauses.append("type = %s")
            params.append(search_params['type'])
        
        if 'priority' in search_params and search_params['priority']:
            where_clauses.append("priority = %s")
            params.append(search_params['priority'])
        
        if 'status' in search_params and search_params['status']:
            where_clauses.append("status = %s")
            params.append(search_params['status'])
        
        if 'title' in search_params and search_params['title']:
            where_clauses.append("title LIKE %s")
            params.append(f"%{search_params['title']}%")
        
        if 'content' in search_params and search_params['content']:
            where_clauses.append("content LIKE %s")
            params.append(f"%{search_params['content']}%")
        
        if 'created_after' in search_params and search_params['created_after']:
            where_clauses.append("created_at >= %s")
            params.append(search_params['created_after'])
        
        if 'created_before' in search_params and search_params['created_before']:
            where_clauses.append("created_at <= %s")
            params.append(search_params['created_before'])
            
        # 添加WHERE子句
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        # 执行查询获取所有匹配的通知ID
        matched_notifications = NotificationDAO.execute_query(query, params)
        notification_ids = [n['id'] for n in matched_notifications]
        
        if not notification_ids:
            return jsonify({
                'success': False,
                'status': 'warning',
                'message': '没有找到匹配的通知'
            })
        
        # 逐个删除通知
        deleted_count = 0
        for notification_id in notification_ids:
            try:
                success = NotificationDAO.delete_notification(notification_id)
                if success:
                    deleted_count += 1
            except Exception as e:
                current_app.logger.error(f'删除通知ID={notification_id}出错: {str(e)}')
        
        # 获取最新的统计数据
        status_counts = NotificationDAO.get_notification_status_counts()
        
        # 检查是否AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            # 返回成功状态
            return jsonify({
                'success': True,
                'status': 'success',
                'message': f'已成功删除 {deleted_count} 条通知',
                'stats': status_counts
            })
        else:
            # 非AJAX请求，重定向回列表页
            from flask import flash, redirect, url_for
            flash(f'已成功删除 {deleted_count} 条通知', 'success')
            return redirect(url_for('notifications.index'))
            
    except Exception as e:
        current_app.logger.error(f'删除筛选通知出错: {str(e)}')
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'删除筛选通知失败: {str(e)}'
        }), 500 

@notifications_bp.route('/user_notifications')
def user_notifications():
    """用户通知管理页面"""
    try:
        # 获取所有用户列表用于下拉选择
        from app.dao.base_dao import BaseDAO
        users_query = "SELECT user_id, username, real_name FROM users WHERE status = '正常' ORDER BY user_id"
        users = BaseDAO.execute_query(users_query)
        
        # 获取用户通知列表
        page = request.args.get('page', 1, type=int)
        per_page = 10
        offset = (page - 1) * per_page
        
        # 查询用户通知
        notifications_query = """
        SELECT notification_id, title, content, target_type, userid, 
               is_read, is_deleted, read_time, create_time
        FROM user_notifications 
        WHERE is_deleted = 0 OR is_deleted IS NULL
        ORDER BY create_time DESC 
        LIMIT %s OFFSET %s
        """
        notifications = BaseDAO.execute_query(notifications_query, (per_page, offset))
        
        # 获取总数
        count_query = "SELECT COUNT(*) as total FROM user_notifications WHERE is_deleted = 0 OR is_deleted IS NULL"
        total_count = BaseDAO.execute_query(count_query)[0]['total']
        total_pages = (total_count + per_page - 1) // per_page
        
        # 为通知添加用户信息
        for notification in notifications:
            if notification['userid']:
                user_query = "SELECT username, real_name FROM users WHERE user_id = %s"
                user_result = BaseDAO.execute_query(user_query, (notification['userid'],))
                if user_result:
                    notification['user_info'] = user_result[0]
                else:
                    notification['user_info'] = {'username': '未知用户', 'real_name': '未知用户'}
            else:
                notification['user_info'] = {'username': '所有用户', 'real_name': '所有用户'}
        
        return render_template('notifications/user_notifications.html',
                             notifications=notifications,
                             users=users,
                             current_page=page,
                             total_pages=total_pages,
                             total_count=total_count,
                             offset=offset,
                             per_page=per_page)
    except Exception as e:
        current_app.logger.error(f'用户通知页面加载错误: {str(e)}')
        traceback.print_exc()
        return render_template('notifications/user_notifications.html', 
                             error=str(e),
                             notifications=[],
                             users=[],
                             current_page=1,
                             total_pages=1,
                             total_count=0,
                             offset=0,
                             per_page=10)

@notifications_bp.route('/user_notifications/create', methods=['POST'])
def create_user_notification():
    """创建用户通知"""
    try:
        from app.dao.base_dao import BaseDAO
        from datetime import datetime
        
        title = request.form.get('title')
        content = request.form.get('content')
        target_type = int(request.form.get('target_type'))
        user_id = request.form.get('user_id') if target_type == 1 else None
        
        if not title or not content:
            flash_error('标题和内容不能为空')
            return redirect(url_for('notifications.user_notifications'))
        
        # 插入用户通知
        insert_query = """
        INSERT INTO user_notifications (title, content, target_type, userid, is_read, is_deleted, create_time)
        VALUES (%s, %s, %s, %s, 0, 0, %s)
        """
        BaseDAO.execute_update(insert_query, (title, content, target_type, user_id, datetime.now()))
        
        flash_success('用户通知创建成功')
        return redirect(url_for('notifications.user_notifications'))
        
    except Exception as e:
        current_app.logger.error(f'创建用户通知错误: {str(e)}')
        traceback.print_exc()
        flash_error(f'创建用户通知失败: {str(e)}')
        return redirect(url_for('notifications.user_notifications'))

@notifications_bp.route('/user_notifications/delete/<int:notification_id>', methods=['POST'])
def delete_user_notification(notification_id):
    """删除用户通知"""
    try:
        from app.dao.base_dao import BaseDAO
        
        # 软删除用户通知
        update_query = "UPDATE user_notifications SET is_deleted = 1 WHERE notification_id = %s"
        BaseDAO.execute_update(update_query, (notification_id,))
        
        return jsonify({
            'success': True,
            'message': '用户通知已删除'
        })
        
    except Exception as e:
        current_app.logger.error(f'删除用户通知错误: {str(e)}')
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'删除用户通知失败: {str(e)}'
        }), 500 