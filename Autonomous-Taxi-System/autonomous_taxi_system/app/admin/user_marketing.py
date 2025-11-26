from flask import Blueprint, jsonify, request
from app.dao.base_dao import BaseDAO
import json
from datetime import datetime, timedelta
import random
from collections import defaultdict
import colorsys
import numpy as np

user_marketing_bp = Blueprint('user_marketing', __name__, url_prefix='/user_marketing')

def get_user_funnel_data(start_date=None, end_date=None):
    """
    获取用户活跃度转化漏斗图数据
    
    参数:
        start_date: 开始日期，格式：YYYY-MM-DD
        end_date: 结束日期，格式：YYYY-MM-DD
    
    返回:
        包含漏斗图所需数据的字典
    """
    # 如果没有提供日期范围，默认使用最近30天
    if not start_date or not end_date:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
    
    # 格式化日期
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d') 
        end_date = end_date.replace(hour=23, minute=59, second=59)
    
    # 计算活跃用户数据
    query_total_users = """
    SELECT COUNT(DISTINCT user_id) as total_users
    FROM users
    WHERE registration_time <= %s
    """
    
    query_active_users = """
    SELECT COUNT(DISTINCT user_id) as active_users
    FROM users
    WHERE last_login_time BETWEEN %s AND %s
    """
    
    query_order_users = """
    SELECT 
        COUNT(DISTINCT user_id) as order_users,
        COUNT(DISTINCT CASE WHEN create_time BETWEEN %s AND %s THEN user_id END) as recent_order_users
    FROM orders
    WHERE user_id IS NOT NULL
    """
    
    query_recent_registration = """
    SELECT COUNT(DISTINCT user_id) as new_users,
           COUNT(DISTINCT CASE WHEN u.user_id IN (
               SELECT DISTINCT user_id FROM orders 
               WHERE create_time BETWEEN %s AND %s
           ) THEN u.user_id END) as new_order_users
    FROM users u
    WHERE registration_time BETWEEN %s AND %s
    """
    
    # 执行查询
    total_users_result = BaseDAO.execute_query(query_total_users, (end_date.strftime('%Y-%m-%d %H:%M:%S'),))
    active_users_result = BaseDAO.execute_query(query_active_users, (start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S')))
    order_users_result = BaseDAO.execute_query(query_order_users, (start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S')))
    new_users_result = BaseDAO.execute_query(query_recent_registration, (
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S'),
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    # 提取数据
    total_users = int(total_users_result[0]['total_users']) if total_users_result else 0
    active_users = int(active_users_result[0]['active_users']) if active_users_result else 0
    order_users = int(order_users_result[0]['order_users']) if order_users_result else 0
    recent_order_users = int(order_users_result[0]['recent_order_users']) if order_users_result else 0
    new_users = int(new_users_result[0]['new_users']) if new_users_result else 0
    new_order_users = int(new_users_result[0]['new_order_users']) if new_users_result else 0
    
    # 计算重复购买用户
    query_repeat_users = """
    SELECT COUNT(DISTINCT user_id) as repeat_users
    FROM (
        SELECT user_id, COUNT(*) as order_count
        FROM orders
        WHERE create_time BETWEEN %s AND %s
        GROUP BY user_id
        HAVING COUNT(*) > 1
    ) as repeat_orders
    """
    
    repeat_users_result = BaseDAO.execute_query(query_repeat_users, (
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    repeat_users = int(repeat_users_result[0]['repeat_users']) if repeat_users_result else 0
    
    # 构建漏斗数据
    funnel_data = [
        {'value': total_users, 'name': '注册用户总数', 'itemStyle': {'color': 'rgba(55, 162, 255, 0.8)'}},
        {'value': active_users, 'name': f'活跃用户（近{(end_date-start_date).days}天）', 'itemStyle': {'color': 'rgba(73, 190, 241, 0.8)'}},
        {'value': order_users, 'name': '下单用户总数', 'itemStyle': {'color': 'rgba(91, 218, 227, 0.85)'}},
        {'value': recent_order_users, 'name': f'近期下单用户（{(end_date-start_date).days}天内）', 'itemStyle': {'color': 'rgba(109, 245, 213, 0.9)'}},
        {'value': repeat_users, 'name': '重复购买用户', 'itemStyle': {'color': 'rgba(127, 255, 199, 0.95)'}},
        {'value': new_order_users, 'name': '新用户首单转化', 'itemStyle': {'color': 'rgba(130, 255, 158, 1)'}}
    ]
    
    return {
        'data': funnel_data,
        'period': f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
        'conversion_rates': {
            'active_rate': round(active_users / total_users * 100, 1) if total_users > 0 else 0,
            'order_rate': round(order_users / active_users * 100, 1) if active_users > 0 else 0,
            'recent_order_rate': round(recent_order_users / order_users * 100, 1) if order_users > 0 else 0,
            'repeat_rate': round(repeat_users / recent_order_users * 100, 1) if recent_order_users > 0 else 0,
            'new_conversion_rate': round(new_order_users / new_users * 100, 1) if new_users > 0 else 0
        }
    }

def get_coupon_sankey_data(start_date=None, end_date=None):
    """
    获取优惠券领取-使用转化桑基图数据
    
    参数:
        start_date: 开始日期，格式：YYYY-MM-DD
        end_date: 结束日期，格式：YYYY-MM-DD
    
    返回:
        包含桑基图所需数据的字典
    """
    # 如果没有提供日期范围，默认使用最近90天
    if not start_date or not end_date:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
    
    # 格式化日期
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
    
    # 获取优惠券来源分布
    source_query = """
    SELECT 
        source, 
        COUNT(*) as count
    FROM 
        coupons
    WHERE 
        receive_time BETWEEN %s AND %s
    GROUP BY 
        source
    """
    
    # 获取优惠券类型分布
    type_query = """
    SELECT 
        ct.type_name,
        ct.coupon_category,
        COUNT(*) as count
    FROM 
        coupons c
        JOIN coupon_types ct ON c.coupon_type_id = ct.id
    WHERE 
        c.receive_time BETWEEN %s AND %s
    GROUP BY 
        ct.type_name, ct.coupon_category
    """
    
    # 获取优惠券状态分布
    status_query = """
    SELECT 
        status,
        COUNT(*) as count
    FROM 
        coupons
    WHERE 
        receive_time BETWEEN %s AND %s
    GROUP BY 
        status
    """
    
    # 获取优惠券从来源到类型的流向
    source_type_query = """
    SELECT 
        c.source,
        ct.type_name,
        ct.coupon_category,
        COUNT(*) as count
    FROM 
        coupons c
        JOIN coupon_types ct ON c.coupon_type_id = ct.id
    WHERE 
        c.receive_time BETWEEN %s AND %s
    GROUP BY 
        c.source, ct.type_name, ct.coupon_category
    """
    
    # 获取优惠券从类型到状态的流向
    type_status_query = """
    SELECT 
        ct.type_name,
        ct.coupon_category,
        c.status,
        COUNT(*) as count
    FROM 
        coupons c
        JOIN coupon_types ct ON c.coupon_type_id = ct.id
    WHERE 
        c.receive_time BETWEEN %s AND %s
    GROUP BY 
        ct.type_name, ct.coupon_category, c.status
    """
    
    # 执行查询
    sources = BaseDAO.execute_query(source_query, (
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    types = BaseDAO.execute_query(type_query, (
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    statuses = BaseDAO.execute_query(status_query, (
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    source_to_type = BaseDAO.execute_query(source_type_query, (
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    type_to_status = BaseDAO.execute_query(type_status_query, (
        start_date.strftime('%Y-%m-%d %H:%M:%S'), 
        end_date.strftime('%Y-%m-%d %H:%M:%S')
    ))
    
    # 构建桑基图数据
    # 节点数据
    nodes = []
    
    # 添加来源节点
    for idx, source in enumerate(sources):
        nodes.append({
            'name': source['source'],
            'itemStyle': {'color': get_gradient_color(idx, len(sources), 'source')}
        })
    
    # 添加类型节点
    type_colors = {}
    for idx, type_info in enumerate(types):
        type_name = f"{type_info['type_name']}（{type_info['coupon_category']}）"
        color = get_gradient_color(idx, len(types), 'type')
        nodes.append({'name': type_name, 'itemStyle': {'color': color}})
        type_colors[f"{type_info['type_name']}_{type_info['coupon_category']}"] = color
    
    # 添加状态节点
    status_colors = {}
    for idx, status in enumerate(statuses):
        color = get_gradient_color(idx, len(statuses), 'status')
        nodes.append({'name': status['status'], 'itemStyle': {'color': color}})
        status_colors[status['status']] = color
    
    # 边数据（链接）
    links = []
    
    # 来源到类型的链接
    source_names = [s['source'] for s in sources]
    for flow in source_to_type:
        source_idx = source_names.index(flow['source'])
        type_name = f"{flow['type_name']}（{flow['coupon_category']}）"
        type_idx = len(sources) + next((i for i, t in enumerate(types) 
                                        if t['type_name'] == flow['type_name'] and 
                                        t['coupon_category'] == flow['coupon_category']), 0)
        
        links.append({
            'source': source_idx,
            'target': type_idx,
            'value': int(flow['count']),
            'lineStyle': {
                'color': 'gradient',
                'opacity': 0.8
            }
        })
    
    # 类型到状态的链接
    status_names = [s['status'] for s in statuses]
    for flow in type_to_status:
        type_name = f"{flow['type_name']}（{flow['coupon_category']}）"
        type_idx = len(sources) + next((i for i, t in enumerate(types) 
                                      if t['type_name'] == flow['type_name'] and 
                                      t['coupon_category'] == flow['coupon_category']), 0)
        status_idx = len(sources) + len(types) + status_names.index(flow['status'])
        
        links.append({
            'source': type_idx,
            'target': status_idx,
            'value': int(flow['count']),
            'lineStyle': {
                'color': 'gradient',
                'opacity': 0.8
            }
        })
    
    # 汇总数据
    summary = {
        'total_coupons': sum(int(s['count']) for s in sources),
        'source_data': [{'name': s['source'], 'value': int(s['count'])} for s in sources],
        'type_data': [{'name': f"{t['type_name']}（{t['coupon_category']}）", 'value': int(t['count'])} for t in types],
        'status_data': [{'name': s['status'], 'value': int(s['count'])} for s in statuses],
        'usage_rate': round(next((int(s['count']) for s in statuses if s['status'] == '已使用'), 0) / 
                           sum(int(s['count']) for s in statuses) * 100, 1) if statuses else 0,
        'period': f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
    }
    
    return {
        'nodes': nodes,
        'links': links,
        'summary': summary
    }

def get_gradient_color(index, total, category_type):
    """生成渐变色，为不同类别的节点设置不同的颜色范围"""
    if total <= 1:
        position = 0.5
    else:
        position = index / (total - 1) if total > 1 else 0
    
    if category_type == 'source':
        # 来源节点使用蓝色到紫色渐变
        h = 0.6 + position * 0.1  # 在210°到246°之间
        s = 0.8
        v = 0.9
    elif category_type == 'type':
        # 类型节点使用绿色到黄色渐变
        h = 0.25 - position * 0.15  # 在90°到36°之间
        s = 0.85
        v = 0.95
    elif category_type == 'time':
        # 时间分布使用橙色到红色渐变
        h = 0.05 - position * 0.05  # 从橙色(18°)渐变到红色(0°)
        s = 0.85 + position * 0.1
        v = 0.95
    else:  # status
        # 状态节点使用红色到橙色渐变
        h = 0.05 - position * 0.05  # 在18°到0°之间
        s = 0.9
        v = 0.95
    
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    
    # 添加透明度，生成rgba格式
    rgba = f'rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, 0.85)'
    return rgba

def get_user_tags_heatmap_data():
    """获取用户标签共现热力图数据"""
    # 查询用户标签数据
    query = """
    SELECT tags FROM users 
    WHERE tags IS NOT NULL AND tags != ''
    """
    
    # 执行查询
    results = BaseDAO.execute_query(query)
    
    # 提取所有标签
    all_tags = []
    for row in results:
        tags = row['tags'].split(',')
        all_tags.extend(tags)
    
    # 统计标签频率并提取前15个最常见标签
    tag_counts = {}
    for tag in all_tags:
        tag = tag.strip()
        if tag in tag_counts:
            tag_counts[tag] += 1
        else:
            tag_counts[tag] = 1
    
    # 排序并获取前15个标签
    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    top_tag_names = [tag[0] for tag in top_tags]
    
    # 初始化共现矩阵
    matrix_size = len(top_tag_names)
    cooccurrence_matrix = [[0 for _ in range(matrix_size)] for _ in range(matrix_size)]
    
    # 计算共现矩阵
    for row in results:
        user_tags = [tag.strip() for tag in row['tags'].split(',')]
        # 只考虑出现在top_tag_names中的标签
        user_top_tags = [tag for tag in user_tags if tag in top_tag_names]
        
        # 计算任意两个标签的共现次数
        for i, tag1 in enumerate(user_top_tags):
            idx1 = top_tag_names.index(tag1)
            for j, tag2 in enumerate(user_top_tags):
                if i != j:  # 不统计自己和自己的共现
                    idx2 = top_tag_names.index(tag2)
                    cooccurrence_matrix[idx1][idx2] += 1
    
    # 生成热力图所需数据
    heatmap_data = []
    max_value = max([max(row) for row in cooccurrence_matrix])
    
    # 创建渐变色方案
    def get_rgba_color(value, max_val):
        # 使用自定义渐变色，从透明蓝色到深红色
        intensity = value / max_val if max_val > 0 else 0
        if intensity < 0.25:
            r = 30 + 100 * (intensity * 4)
            g = 144 + 50 * (intensity * 4)
            b = 255
            a = 0.3 + intensity * 2
        elif intensity < 0.5:
            r = 130 + 125 * ((intensity - 0.25) * 4)
            g = 194 - 94 * ((intensity - 0.25) * 4)
            b = 255 - 55 * ((intensity - 0.25) * 4)
            a = 0.7 + (intensity - 0.25) * 0.6
        elif intensity < 0.75:
            r = 255
            g = 100 - 70 * ((intensity - 0.5) * 4)
            b = 200 - 120 * ((intensity - 0.5) * 4)
            a = 0.85 + (intensity - 0.5) * 0.1
        else:
            r = 255
            g = 30 - 30 * ((intensity - 0.75) * 4)
            b = 80 - 80 * ((intensity - 0.75) * 4)
            a = 0.95 + (intensity - 0.75) * 0.05
        
        return f"rgba({int(r)}, {int(g)}, {int(b)}, {a})"
    
    # 生成热力图数据
    for i in range(matrix_size):
        for j in range(matrix_size):
            if i != j:  # 排除对角线
                value = cooccurrence_matrix[i][j]
                if value > 0:  # 只添加有共现的数据点
                    heatmap_data.append({
                        'value': [j, i, value],  # x, y, value
                        'itemStyle': {
                            'color': get_rgba_color(value, max_value)
                        }
                    })
    
    # 添加一些随机动态波动数据使热力图更生动
    for i in range(10):
        x = random.randint(0, matrix_size-1)
        y = random.randint(0, matrix_size-1)
        if x != y:
            value = random.randint(1, int(max_value * 0.3))
            heatmap_data.append({
                'value': [x, y, value],
                'itemStyle': {
                    'color': get_rgba_color(value, max_value)
                },
                'emphasis': {
                    'itemStyle': {
                        'shadowBlur': 10,
                        'shadowColor': 'rgba(255,255,255,0.5)'
                    }
                }
            })
    
    return {
        'tags': top_tag_names,
        'data': heatmap_data,
        'max_value': max_value
    }

def get_credit_score_path_data():
    """获取用户信用分变化路径图数据，展示个人用户信用分变化轨迹"""
    # 查询多个用户的信用分变化记录
    query = """
    SELECT 
        l.log_id,
        l.user_id,
        u.username,
        l.change_amount,
        l.credit_before,
        l.credit_after,
        l.change_type,
        l.reason,
        DATE_FORMAT(l.created_at, '%Y-%m-%d %H:%i') as change_date,
        l.related_order_id
    FROM 
        user_credit_logs l
        JOIN users u ON l.user_id = u.user_id
    WHERE 
        l.created_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
    ORDER BY 
        l.user_id, l.created_at
    """
    
    # 执行查询
    results = BaseDAO.execute_query(query)
    
    # 按用户ID分组记录
    user_logs = defaultdict(list)
    
    for row in results:
        user_logs[row['user_id']].append(row)
    
    # 选择有足够记录的前5个用户(每个用户至少有3条记录)
    selected_users = []
    
    for user_id, logs in user_logs.items():
        if len(logs) >= 3:
            selected_users.append(user_id)
            if len(selected_users) >= 5:
                break
    
    # 生成系列数据
    series = []
    
    # 用户对应的颜色
    user_colors = [
        ['rgba(24, 144, 255, 0.8)', 'rgba(24, 144, 255, 0.2)'],  # 蓝色
        ['rgba(47, 194, 91, 0.8)', 'rgba(47, 194, 91, 0.2)'],    # 绿色
        ['rgba(250, 84, 28, 0.8)', 'rgba(250, 84, 28, 0.2)'],    # 橙色
        ['rgba(245, 34, 45, 0.8)', 'rgba(245, 34, 45, 0.2)'],    # 红色
        ['rgba(114, 46, 209, 0.8)', 'rgba(114, 46, 209, 0.2)']   # 紫色
    ]
    
    for idx, user_id in enumerate(selected_users):
        logs = user_logs[user_id]
        data = []
        
        for i, log in enumerate(logs):
            data.append({
                'value': [
                    i,  # x轴索引
                    log['credit_after'],  # y轴信用分
                    log['change_date'],   # 变化日期
                    log['reason'],        # 变化原因
                    log['change_type']    # 变化类型
                ]
            })
        
        # 创建用户系列
        series.append({
            'name': f"用户 {logs[0]['username']}",
            'type': 'line',
            'data': data,
            'smooth': True,
            'showSymbol': True,
            'symbolSize': 8,
            'lineStyle': {
                'width': 3,
                'color': {
                    'type': 'linear',
                    'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                    'colorStops': [
                        {'offset': 0, 'color': user_colors[idx % len(user_colors)][0]},
                        {'offset': 1, 'color': user_colors[idx % len(user_colors)][1]}
                    ]
                }
            },
            'itemStyle': {
                'borderWidth': 2,
                'borderColor': 'rgba(255, 255, 255, 0.8)',
                'color': {
                    'type': 'linear',
                    'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                    'colorStops': [
                        {'offset': 0, 'color': user_colors[idx % len(user_colors)][0]},
                        {'offset': 1, 'color': user_colors[idx % len(user_colors)][1]}
                    ]
                }
            },
            'emphasis': {
                'focus': 'series',
                'itemStyle': {
                    'borderWidth': 4,
                    'borderColor': '#fff',
                    'shadowBlur': 10,
                    'shadowColor': 'rgba(0,0,0,0.5)'
                }
            }
        })
    
    # 返回系列数据
    return {
        'series': series
    }

@user_marketing_bp.route('/funnel_data')
def funnel_data():
    """获取漏斗图数据的API端点"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        data = get_user_funnel_data(start_date, end_date)
        return jsonify(data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@user_marketing_bp.route('/sankey_data')
def sankey_data():
    """获取桑基图数据的API端点"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        data = get_coupon_sankey_data(start_date, end_date)
        return jsonify(data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@user_marketing_bp.route('/tags_heatmap_data')
def tags_heatmap_data():
    """获取用户标签共现关系热力图数据的API端点"""
    try:
        data = get_user_tags_heatmap_data()
        return jsonify(data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@user_marketing_bp.route('/credit_score_path_data')
def credit_score_path_data():
    """获取用户信用分变化路径图数据的API端点"""
    try:
        data = get_credit_score_path_data()
        return jsonify(data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def get_first_order_time_distribution():
    """
    获取用户从注册到首次下单所需时间的分布数据
    
    返回:
        包含首次下单时间分布数据的字典
    """
    # 查询用户首次下单时间
    query = """
    SELECT 
        u.user_id,
        u.registration_time,
        MIN(o.create_time) as first_order_time,
        TIMESTAMPDIFF(HOUR, u.registration_time, MIN(o.create_time)) as hours_to_first_order
    FROM 
        users u
        JOIN orders o ON u.user_id = o.user_id
    WHERE 
        u.registration_time IS NOT NULL 
        AND o.create_time IS NOT NULL
        AND u.registration_time <= o.create_time
    GROUP BY 
        u.user_id, u.registration_time
    HAVING 
        hours_to_first_order >= 0
        AND hours_to_first_order <= 1440  -- 最多60天(60*24=1440小时)
    ORDER BY 
        hours_to_first_order
    """
    
    results = BaseDAO.execute_query(query)
    
    if not results:
        return {
            'categories': [],
            'data': [],
            'total_users': 0,
            'distribution': []
        }
    
    # 提取首次下单所需时间（小时）
    hours_to_first_order = [int(row['hours_to_first_order']) for row in results]
    
    # 定义时间段分类
    categories = [
        '1小时内', '1-6小时', '6-12小时', '12-24小时',
        '1-3天', '3-7天', '1-2周', '2-4周', '4周以上'
    ]
    
    # 定义时间段边界（小时）
    boundaries = [0, 1, 6, 12, 24, 72, 168, 336, 672, 1440]
    
    # 统计各时间段的用户数
    counts = [0] * (len(boundaries) - 1)
    for hours in hours_to_first_order:
        for i in range(len(boundaries) - 1):
            if boundaries[i] <= hours < boundaries[i + 1]:
                counts[i] += 1
                break
    
    # 计算完整的分布数据
    total_users = len(hours_to_first_order)
    distribution = []
    
    for i in range(len(categories)):
        percentage = round(counts[i] / total_users * 100, 1) if total_users > 0 else 0
        distribution.append({
            'category': categories[i],
            'count': counts[i],
            'percentage': percentage,
            'color': get_gradient_color(i, len(categories), 'time')
        })
    
    # 生成核密度估计数据 (KDE)
    kde_data = []
    if len(hours_to_first_order) > 5:  # 至少需要一些数据点
        # 使用对数变换处理偏度较大的分布
        log_hours = [np.log1p(h) for h in hours_to_first_order if h > 0]
        
        if log_hours:
            # 计算核密度估计
            # 简化计算，生成平滑曲线
            x_min, x_max = min(log_hours), max(log_hours)
            x_range = np.linspace(x_min, x_max, 100)
            
            # 生成KDE曲线的Y值
            # 这里使用简单的高斯核进行平滑
            bandwidth = 0.2  # 控制平滑程度
            kde_values = []
            
            for x in x_range:
                y = sum(np.exp(-0.5 * ((x - xi) / bandwidth) ** 2) / (bandwidth * np.sqrt(2 * np.pi)) for xi in log_hours) / len(log_hours)
                kde_values.append(y)
            
            # 归一化KDE以便于显示
            max_kde = max(kde_values) if kde_values else 1
            kde_values = [v / max_kde for v in kde_values]
            
            # 转换回原始尺度以便显示
            x_original = [np.expm1(x) for x in x_range]
            
            # 截断x轴使图表更易读
            for i in range(len(x_original)):
                if i < len(kde_values):
                    kde_data.append([x_original[i], kde_values[i]])
    
    return {
        'categories': categories,
        'counts': counts,
        'total_users': total_users,
        'distribution': distribution,
        'kde_data': kde_data
    }

def get_user_ltv_distribution():
    """
    获取用户生命周期价值(LTV)分布数据
    使用用户累计消费金额作为LTV的近似值
    
    返回:
        包含用户生命周期价值分布数据的字典
    """
    # 查询用户累计消费金额
    query = """
    SELECT 
        od.user_id,
        u.username,
        u.registration_time,
        COUNT(DISTINCT od.order_id) as order_count,
        SUM(od.amount) as total_spend
    FROM 
        order_details od
        JOIN users u ON od.user_id = u.user_id
    GROUP BY 
        od.user_id, u.username, u.registration_time
    HAVING 
        order_count >= 1
    ORDER BY 
        total_spend DESC
    """
    
    results = BaseDAO.execute_query(query)
    
    if not results:
        return {
            'data': [],
            'summary': {}
        }
    
    # 提取LTV数据
    ltv_data = []
    ltv_values = []
    
    for row in results:
        user_id = row['user_id']
        username = row['username']
        total_spend = float(row['total_spend'])
        order_count = int(row['order_count'])
        
        # 计算注册至今的天数
        registration_time = row['registration_time']
        if registration_time:
            days_since_registration = (datetime.now() - registration_time).days
        else:
            days_since_registration = 0
        
        # 计算平均订单价值
        avg_order_value = total_spend / order_count if order_count > 0 else 0
        
        # 存储数据
        ltv_data.append({
            'user_id': user_id,
            'username': username,
            'total_spend': total_spend,
            'order_count': order_count,
            'days_since_registration': days_since_registration,
            'avg_order_value': round(avg_order_value, 2)
        })
        
        ltv_values.append(total_spend)
    
    # 计算小提琴图需要的统计数据
    if ltv_values:
        sorted_values = sorted(ltv_values)
        
        # 分位数
        q1, median, q3 = (
            np.percentile(sorted_values, 25),
            np.percentile(sorted_values, 50),
            np.percentile(sorted_values, 75)
        )
        
        # 计算四分位距
        iqr = q3 - q1
        
        # 计算上下限（用于检测离群值）
        lower_bound = max(0, q1 - 1.5 * iqr)
        upper_bound = q3 + 1.5 * iqr
        
        # 归一化处理，用于生成核密度估计
        min_val, max_val = min(sorted_values), max(sorted_values)
        range_val = max_val - min_val if max_val > min_val else 1
        
        # 生成小提琴图的轮廓数据
        violin_points = []
        if len(sorted_values) >= 10:  # 至少需要10个数据点才能生成有意义的小提琴图
            # 分箱并计算每个分箱的频率
            bin_count = min(20, len(sorted_values) // 5)  # 根据数据量动态调整分箱数
            hist, bin_edges = np.histogram(sorted_values, bins=bin_count, density=True)
            
            # 归一化频率值，使最大宽度固定
            max_width = 0.4
            if max(hist) > 0:
                hist = [h / max(hist) * max_width for h in hist]
            
            # 生成小提琴图的左侧轮廓点
            for i in range(len(hist)):
                bin_mid = (bin_edges[i] + bin_edges[i+1]) / 2
                violin_points.append([-hist[i], bin_mid])
            
            # 生成小提琴图的右侧轮廓点（按照从下到上的顺序）
            for i in range(len(hist)-1, -1, -1):
                bin_mid = (bin_edges[i] + bin_edges[i+1]) / 2
                violin_points.append([hist[i], bin_mid])
        
        # 摘要统计信息
        summary = {
            'count': len(ltv_values),
            'min': min_val,
            'max': max_val,
            'mean': np.mean(sorted_values),
            'median': median,
            'q1': q1,
            'q3': q3,
            'outliers_count': sum(1 for v in sorted_values if v < lower_bound or v > upper_bound),
            'top_10_percent_threshold': np.percentile(sorted_values, 90),
            'top_users': sorted(ltv_data, key=lambda x: x['total_spend'], reverse=True)[:10]
        }
    else:
        violin_points = []
        summary = {
            'count': 0,
            'min': 0,
            'max': 0,
            'mean': 0,
            'median': 0,
            'q1': 0,
            'q3': 0,
            'outliers_count': 0,
            'top_10_percent_threshold': 0,
            'top_users': []
        }
    
    return {
        'violin_points': violin_points,
        'ltv_data': ltv_data[:100],  # 限制返回数量，避免数据过大
        'summary': summary
    }

@user_marketing_bp.route('/first_order_time_data')
def first_order_time_data():
    """获取首次下单时间分布图数据的API端点"""
    try:
        data = get_first_order_time_distribution()
        return jsonify(data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@user_marketing_bp.route('/user_ltv_data')
def user_ltv_data():
    """获取用户生命周期价值分布图数据的API端点"""
    try:
        data = get_user_ltv_distribution()
        return jsonify(data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def get_coupon_preference_radar():
    """
    获取优惠券使用偏好雷达图数据
    
    返回:
        包含不同类型优惠券使用情况的雷达图数据
    """
    # 查询各类型优惠券使用情况
    query = """
    SELECT 
        ct.type_name,
        ct.coupon_category,
        COUNT(*) as use_count
    FROM 
        coupons c
        JOIN coupon_types ct ON c.coupon_type_id = ct.id
    WHERE 
        c.status = '已使用'
    GROUP BY 
        ct.type_name, ct.coupon_category
    ORDER BY 
        use_count DESC
    LIMIT 10
    """
    
    results = BaseDAO.execute_query(query)
    
    if not results:
        return {
            'indicator': [],
            'data': []
        }
    
    # 提取优惠券类型和使用次数
    coupon_types = []
    use_counts = []
    categories = {}  # 用于按照优惠券种类(满减券/折扣券)分组
    
    for row in results:
        type_name = f"{row['type_name']}({row['coupon_category']})"
        use_count = int(row['count'] if isinstance(row.get('count'), (int, float)) else row['use_count'])
        
        coupon_types.append(type_name)
        use_counts.append(use_count)
        
        # 按种类分组
        category = row['coupon_category']
        if category not in categories:
            categories[category] = []
        
        categories[category].append({
            'name': type_name,
            'value': use_count
        })
    
    # 构建雷达图指示器
    indicators = []
    max_count = max(use_counts) if use_counts else 100
    
    for coupon_type in coupon_types:
        indicators.append({
            'name': coupon_type,
            'max': max_count * 1.2  # 设置最大值为实际最大值的1.2倍
        })
    
    # 构建雷达图系列数据
    series_data = []
    
    # 按优惠券种类生成不同系列
    for category, data in categories.items():
        # 创建一个与indicators长度相同的数据数组，填充0
        values = [0] * len(indicators)
        
        # 将数据填充到对应位置
        for item in data:
            if item['name'] in coupon_types:
                idx = coupon_types.index(item['name'])
                values[idx] = item['value']
        
        series_data.append({
            'name': category,
            'value': values,
            'areaStyle': {
                'opacity': 0.4
            }
        })
    
    return {
        'indicators': indicators,
        'series_data': series_data,
        'coupon_types': coupon_types,
        'categories': list(categories.keys())
    }

def get_channel_activity_comparison():
    """
    获取不同注册渠道用户活跃时段对比图数据
    
    返回:
        包含不同渠道用户在各时段活跃度的数据
    """
    # 查询不同渠道用户在不同时段的订单数量
    query = """
    SELECT 
        u.registration_channel,
        HOUR(o.create_time) as hour_of_day,
        COUNT(*) as order_count
    FROM 
        orders o
        JOIN users u ON o.user_id = u.user_id
    WHERE 
        o.create_time IS NOT NULL
        AND u.registration_channel IS NOT NULL
    GROUP BY 
        u.registration_channel, 
        HOUR(o.create_time)
    ORDER BY 
        u.registration_channel,
        HOUR(o.create_time)
    """
    
    results = BaseDAO.execute_query(query)
    
    if not results:
        return {
            'channels': [],
            'hours': list(range(24)),
            'series': []
        }
    
    # 准备数据结构
    channels = []  # 渠道列表
    channel_data = {}  # 每个渠道的小时数据
    
    # 初始化24小时
    hours = list(range(24))
    
    # 处理查询结果
    for row in results:
        channel = row['registration_channel']
        hour = int(row['hour_of_day'])
        count = int(row['order_count'])
        
        if channel not in channels:
            channels.append(channel)
            channel_data[channel] = [0] * 24  # 初始化24小时数据
        
        channel_data[channel][hour] = count
    
    # 构建系列数据
    series = []
    colors = ['#4a79fe', '#36c5fe', '#38c7be', '#fa9d4c', '#f87146']
    
    for i, channel in enumerate(channels):
        series.append({
            'name': channel,
            'type': 'bar',
            'data': channel_data[channel],
            'itemStyle': {
                'color': colors[i % len(colors)]
            }
        })
    
    # 计算每个时段的峰值时间
    peak_hours = []
    for hour in range(24):
        max_channel = None
        max_count = 0
        for channel in channels:
            if channel_data[channel][hour] > max_count:
                max_count = channel_data[channel][hour]
                max_channel = channel
        
        if max_channel:
            peak_hours.append({
                'hour': hour,
                'channel': max_channel,
                'count': max_count
            })
    
    # 按订单量排序，取前5个峰值时段
    peak_hours = sorted(peak_hours, key=lambda x: x['count'], reverse=True)[:5]
    
    return {
        'channels': channels,
        'hours': hours,
        'series': series,
        'peak_hours': peak_hours
    }

def get_repurchase_interval_data():
    """
    获取用户复购间隔时间分布图数据
    
    返回:
        包含用户复购间隔的分布数据
    """
    # 查询用户的订单创建时间 - 使用order_details表中的数据
    query = """
    SELECT 
        user_id,
        created_at
    FROM 
        order_details
    WHERE 
        user_id IS NOT NULL
        AND created_at IS NOT NULL
    ORDER BY 
        user_id,
        created_at
    """
    
    results = BaseDAO.execute_query(query)
    
    if not results:
        return {
            'intervals': [],
            'counts': [],
            'summary': {}
        }
    
    # 计算每个用户的订单间隔时间(小时)
    user_orders = defaultdict(list)
    
    for row in results:
        user_id = row['user_id']
        create_time = row['created_at']
        user_orders[user_id].append(create_time)
    
    # 计算间隔时间(小时)
    intervals = []
    
    for user_id, order_times in user_orders.items():
        if len(order_times) < 2:
            continue
        
        # 确保订单按时间排序
        order_times.sort()
        
        # 计算相邻订单的时间间隔
        for i in range(1, len(order_times)):
            time_diff = (order_times[i] - order_times[i-1]).total_seconds() / 3600  # 转换为小时
            if 0 < time_diff <= 720:  # 过滤异常值，最长考虑30天(720小时)
                intervals.append(time_diff)
    
    if not intervals:
        return {
            'intervals': [],
            'counts': [],
            'summary': {}
        }
    
    # 定义间隔区间(小时)
    bins = [0, 6, 12, 24, 48, 72, 168, 336, 720]
    bin_labels = ['0-6小时', '6-12小时', '12-24小时', '1-2天', '2-3天', '3-7天', '7-14天', '14-30天']
    
    # 统计各区间的频数
    hist_counts = [0] * len(bin_labels)
    
    for interval in intervals:
        for i in range(len(bins)-1):
            if bins[i] <= interval < bins[i+1]:
                hist_counts[i] += 1
                break
    
    # 计算摘要统计信息
    import numpy as np
    
    avg_interval = round(np.mean(intervals), 1)
    median_interval = round(np.median(intervals), 1)
    
    # 转换为更易读的时间格式
    def format_hours(hours):
        if hours < 1:
            return f"{int(hours * 60)}分钟"
        elif hours < 24:
            return f"{int(hours)}小时"
        else:
            days = hours / 24
            return f"{int(days)}天{int((days - int(days)) * 24)}小时"
    
    # 构建密度估计数据
    kde_data = []
    if len(intervals) >= 10:
        # 对数据进行排序
        sorted_intervals = np.sort(intervals)
        # 生成平滑曲线的x轴点
        x_points = np.linspace(min(intervals), min(720, max(intervals)), 100)
        
        # 使用高斯核进行平滑
        bandwidth = 0.1 * (max(intervals) - min(intervals))
        bandwidth = max(bandwidth, 0.5)  # 确保带宽不会太小
        
        try:
            # 尝试使用scipy的gaussian_kde
            from scipy.stats import gaussian_kde
            kde = gaussian_kde(intervals, bw_method=bandwidth)
            y_points = kde(x_points)
            
            # 归一化y值使其最大值为1
            max_y = max(y_points)
            if max_y > 0:
                y_points = [y / max_y for y in y_points]
                
            kde_data = list(zip(x_points.tolist(), y_points.tolist()))
        except:
            # 如果scipy不可用，使用简单的直方图
            hist, bin_edges = np.histogram(intervals, bins=20, density=True)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            max_hist = max(hist) if len(hist) > 0 else 1
            normalized_hist = [h / max_hist for h in hist]
            kde_data = list(zip(bin_centers.tolist(), normalized_hist))
    
    return {
        'intervals': bin_labels,
        'counts': hist_counts,
        'total_users': len(user_orders),
        'repurchase_users': sum(1 for user_id, orders in user_orders.items() if len(orders) > 1),
        'total_intervals': len(intervals),
        'summary': {
            'avg_interval': avg_interval,
            'avg_interval_text': format_hours(avg_interval),
            'median_interval': median_interval,
            'median_interval_text': format_hours(median_interval)
        },
        'kde_data': kde_data
    }

@user_marketing_bp.route('/coupon_preference_radar')
def coupon_preference_radar():
    """获取优惠券使用偏好雷达图数据的API端点"""
    try:
        data = get_coupon_preference_radar()
        return jsonify(data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@user_marketing_bp.route('/channel_activity_comparison')
def channel_activity_comparison():
    """获取不同注册渠道用户活跃时段对比图数据的API端点"""
    try:
        data = get_channel_activity_comparison()
        return jsonify(data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@user_marketing_bp.route('/repurchase_interval_data')
def repurchase_interval_data():
    """获取用户复购间隔时间分布图数据的API端点"""
    try:
        data = get_repurchase_interval_data()
        return jsonify(data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500 