#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, Response
from app.dao.credit_level_dao import CreditLevelDAO
from app.dao.credit_rule_dao import CreditRuleDAO
import csv
from io import StringIO
import datetime

# 创建蓝图
credit_bp = Blueprint('credit', __name__, url_prefix='/api/credit')

@credit_bp.route('/levels', methods=['GET'])
def get_credit_levels():
    """获取所有信用等级规则"""
    try:
        levels = CreditLevelDAO.get_all_credit_levels()
        
        # 处理空行和换行符
        for level in levels:
            if 'benefits' in level and level['benefits']:
                level['benefits'] = level['benefits'].replace('\n', '<br>')
            if 'limitations' in level and level['limitations']:
                level['limitations'] = level['limitations'].replace('\n', '<br>')
        
        return jsonify({
            'status': 'success',
            'data': levels
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取信用等级规则失败: {str(e)}'
        }), 500

@credit_bp.route('/levels/<int:level_id>', methods=['GET'])
def get_credit_level(level_id):
    """获取单个信用等级规则"""
    try:
        level = CreditLevelDAO.get_credit_level_by_id(level_id)
        
        if not level:
            return jsonify({
                'status': 'error',
                'message': f'未找到ID为{level_id}的信用等级规则'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': level
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取信用等级规则失败: {str(e)}'
        }), 500

@credit_bp.route('/levels', methods=['POST'])
def add_credit_level():
    """添加新的信用等级规则"""
    try:
        data = request.get_json()
        
        # 基本字段验证
        required_fields = ['level_name', 'min_score', 'max_score']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必填字段: {field}'
                }), 400
        
        # 验证分数范围
        if int(data['min_score']) >= int(data['max_score']):
            return jsonify({
                'status': 'error',
                'message': '最低分值必须小于最高分值'
            }), 400
        
        # 处理HTML标签
        if 'benefits' in data and data['benefits']:
            data['benefits'] = data['benefits'].replace('<br>', '\n')
        
        if 'limitations' in data and data['limitations']:
            data['limitations'] = data['limitations'].replace('<br>', '\n')
        
        # 添加到数据库
        new_id = CreditLevelDAO.add_credit_level(data)
        
        if not new_id:
            return jsonify({
                'status': 'error',
                'message': '添加信用等级规则失败'
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': '添加信用等级规则成功',
            'data': {'level_id': new_id}
        }), 201
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'添加信用等级规则失败: {str(e)}'
        }), 500

@credit_bp.route('/levels/<int:level_id>', methods=['PUT'])
def update_credit_level(level_id):
    """更新信用等级规则"""
    try:
        data = request.get_json()
        
        # 检查规则是否存在
        existing_level = CreditLevelDAO.get_credit_level_by_id(level_id)
        if not existing_level:
            return jsonify({
                'status': 'error',
                'message': f'未找到ID为{level_id}的信用等级规则'
            }), 404
        
        # 验证分数范围（如果提供了min_score和max_score）
        if 'min_score' in data and 'max_score' in data:
            if int(data['min_score']) >= int(data['max_score']):
                return jsonify({
                    'status': 'error',
                    'message': '最低分值必须小于最高分值'
                }), 400
        
        # 处理HTML标签
        if 'benefits' in data and data['benefits']:
            data['benefits'] = data['benefits'].replace('<br>', '\n')
        
        if 'limitations' in data and data['limitations']:
            data['limitations'] = data['limitations'].replace('<br>', '\n')
        
        # 更新数据库
        success = CreditLevelDAO.update_credit_level(level_id, data)
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': '更新信用等级规则失败'
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': '更新信用等级规则成功'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'更新信用等级规则失败: {str(e)}'
        }), 500

@credit_bp.route('/levels/<int:level_id>', methods=['DELETE'])
def delete_credit_level(level_id):
    """删除信用等级规则"""
    try:
        # 检查规则是否存在
        existing_level = CreditLevelDAO.get_credit_level_by_id(level_id)
        if not existing_level:
            return jsonify({
                'status': 'error',
                'message': f'未找到ID为{level_id}的信用等级规则'
            }), 404
        
        # 从数据库删除
        success = CreditLevelDAO.delete_credit_level(level_id)
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': '删除信用等级规则失败'
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': '删除信用等级规则成功'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'删除信用等级规则失败: {str(e)}'
        }), 500

# 信用分变动规则相关API
@credit_bp.route('/rules', methods=['GET'])
def get_credit_rules():
    """获取所有信用分变动规则"""
    try:
        # 检查是否按类型筛选
        rule_type = request.args.get('type')
        
        if rule_type and rule_type in ['奖励', '惩罚', '恢复']:
            rules = CreditRuleDAO.get_credit_rules_by_type(rule_type)
        else:
            rules = CreditRuleDAO.get_all_credit_rules()
        
        return jsonify({
            'status': 'success',
            'data': rules
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取信用分变动规则失败: {str(e)}'
        }), 500

@credit_bp.route('/rules/<int:rule_id>', methods=['GET'])
def get_credit_rule(rule_id):
    """获取单个信用分变动规则"""
    try:
        rule = CreditRuleDAO.get_credit_rule_by_id(rule_id)
        
        if not rule:
            return jsonify({
                'status': 'error',
                'message': f'未找到ID为{rule_id}的信用分变动规则'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': rule
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取信用分变动规则失败: {str(e)}'
        }), 500

@credit_bp.route('/rules', methods=['POST'])
def add_credit_rule():
    """添加新的信用分变动规则"""
    try:
        data = request.get_json()
        
        # 基本字段验证
        required_fields = ['rule_name', 'rule_type', 'trigger_event', 'score_change']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'缺少必填字段: {field}'
                }), 400
        
        # 验证规则类型
        if data['rule_type'] not in ['奖励', '惩罚', '恢复']:
            return jsonify({
                'status': 'error',
                'message': '规则类型必须是: 奖励, 惩罚, 恢复'
            }), 400
        
        # 验证分数变动与规则类型的匹配
        score_change = int(data['score_change'])
        rule_type = data['rule_type']
        
        if rule_type == '奖励' or rule_type == '恢复':
            if score_change <= 0:
                return jsonify({
                    'status': 'error',
                    'message': f'{rule_type}类型的规则分值变动必须为正数'
                }), 400
        elif rule_type == '惩罚':
            if score_change >= 0:
                return jsonify({
                    'status': 'error',
                    'message': '惩罚类型的规则分值变动必须为负数'
                }), 400
        
        # 添加到数据库
        new_id = CreditRuleDAO.add_credit_rule(data)
        
        if not new_id:
            return jsonify({
                'status': 'error',
                'message': '添加信用分变动规则失败'
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': '添加信用分变动规则成功',
            'data': {'rule_id': new_id}
        }), 201
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'添加信用分变动规则失败: {str(e)}'
        }), 500

@credit_bp.route('/rules/<int:rule_id>', methods=['PUT'])
def update_credit_rule(rule_id):
    """更新信用分变动规则"""
    try:
        data = request.get_json()
        
        # 检查规则是否存在
        existing_rule = CreditRuleDAO.get_credit_rule_by_id(rule_id)
        if not existing_rule:
            return jsonify({
                'status': 'error',
                'message': f'未找到ID为{rule_id}的信用分变动规则'
            }), 404
        
        # 验证规则类型（如果提供了）
        if 'rule_type' in data and data['rule_type'] not in ['奖励', '惩罚', '恢复']:
            return jsonify({
                'status': 'error',
                'message': '规则类型必须是: 奖励, 惩罚, 恢复'
            }), 400
        
        # 验证分数变动与规则类型的匹配
        if 'score_change' in data:
            score_change = int(data['score_change'])
            rule_type = data.get('rule_type', existing_rule['rule_type'])
            
            if rule_type == '奖励' or rule_type == '恢复':
                if score_change <= 0:
                    return jsonify({
                        'status': 'error',
                        'message': f'{rule_type}类型的规则分值变动必须为正数'
                    }), 400
            elif rule_type == '惩罚':
                if score_change >= 0:
                    return jsonify({
                        'status': 'error',
                        'message': '惩罚类型的规则分值变动必须为负数'
                    }), 400
        
        # 更新数据库
        success = CreditRuleDAO.update_credit_rule(rule_id, data)
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': '更新信用分变动规则失败'
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': '更新信用分变动规则成功'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'更新信用分变动规则失败: {str(e)}'
        }), 500

@credit_bp.route('/rules/<int:rule_id>/status', methods=['PUT'])
def change_rule_status(rule_id):
    """更改规则状态（激活/禁用）"""
    try:
        data = request.get_json()
        
        # 检查规则是否存在
        existing_rule = CreditRuleDAO.get_credit_rule_by_id(rule_id)
        if not existing_rule:
            return jsonify({
                'status': 'error',
                'message': f'未找到ID为{rule_id}的信用分变动规则'
            }), 404
        
        # 检查状态参数
        if 'is_active' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少必填字段: is_active'
            }), 400
        
        # 转换为整数
        is_active = int(data['is_active'])
        if is_active not in [0, 1]:
            return jsonify({
                'status': 'error',
                'message': 'is_active必须是0或1'
            }), 400
        
        # 更新状态
        success = CreditRuleDAO.change_rule_status(rule_id, is_active)
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': '更改规则状态失败'
            }), 500
        
        status_text = '激活' if is_active == 1 else '禁用'
        return jsonify({
            'status': 'success',
            'message': f'信用分变动规则已{status_text}'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'更改规则状态失败: {str(e)}'
        }), 500

@credit_bp.route('/rules/<int:rule_id>', methods=['DELETE'])
def delete_credit_rule(rule_id):
    """删除信用分变动规则"""
    try:
        # 检查规则是否存在
        existing_rule = CreditRuleDAO.get_credit_rule_by_id(rule_id)
        if not existing_rule:
            return jsonify({
                'status': 'error',
                'message': f'未找到ID为{rule_id}的信用分变动规则'
            }), 404
        
        # 从数据库删除
        success = CreditRuleDAO.delete_credit_rule(rule_id)
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': '删除信用分变动规则失败'
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': '删除信用分变动规则成功'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'删除信用分变动规则失败: {str(e)}'
        }), 500

# 信用变动记录相关API
@credit_bp.route('/logs', methods=['GET'])
def get_credit_logs():
    """获取信用变动记录API"""
    try:
        print("开始请求信用变动记录API...")
        
        # 分页参数
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # DataTables 特殊参数
        draw = request.args.get('draw', 1, type=int)  # 获取draw参数
        search = request.args.get('search', '')  # 获取搜索关键词
        
        # 排序参数
        sort = request.args.get('sort', 'created_at')
        order = request.args.get('order', 'desc')
        
        # 筛选参数
        user_id = request.args.get('user_id', '')
        change_type = request.args.get('change_type', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        print(f"API参数: offset={offset}, limit={limit}, search={search}, sort={sort}, order={order}")

        # 直接从DAO层获取数据，不使用测试数据
        from app.dao.user_credit_log_dao import UserCreditLogDAO
        
        total, credit_logs = UserCreditLogDAO.get_credit_logs(
            offset=offset,
            limit=limit,
            user_id=user_id if user_id else None,
            change_type=change_type if change_type else None,
            date_from=date_from if date_from else None,
            date_to=date_to if date_to else None,
            sort=sort,
            order=order,
            search=search  # 传递搜索参数
        )
        
        print(f"从数据库查询到 {len(credit_logs)} 条记录，总记录数: {total}")
        
        # 返回格式化的响应，符合DataTables期望的格式
        return jsonify({
            'draw': draw,  # 返回相同的draw参数
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': credit_logs,
            'status': 'success'
        })
    
    except Exception as e:
        import traceback
        print(f"获取信用记录异常: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'draw': request.args.get('draw', 1, type=int),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'status': 'error',
            'message': f'获取信用记录失败: {str(e)}'
        }), 500

@credit_bp.route('/logs/export', methods=['GET'])
def export_credit_logs():
    """导出信用变动记录"""
    try:
        # 获取请求参数
        user_id = request.args.get('user_id', '')
        change_type = request.args.get('change_type', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # 从DAO层获取全部数据（不分页）
        from app.dao.user_credit_log_dao import UserCreditLogDAO
        
        # 获取全部数据，传递limit=0表示不限制记录数
        total, credit_logs = UserCreditLogDAO.get_credit_logs(
            offset=0,
            limit=0,  # 0表示不限制
            user_id=user_id if user_id else None,
            change_type=change_type if change_type else None,
            date_from=date_from if date_from else None,
            date_to=date_to if date_to else None,
            sort="created_at",
            order="DESC"
        )
        
        print(f"导出数据: 获取到 {len(credit_logs)} 条记录")
        
        # 生成CSV文件
        output = StringIO()
        writer = csv.writer(output)
        
        # 写入标题行
        writer.writerow(['记录ID', '用户ID', '用户名', '变动分值', '变动前分值', '变动后分值', 
                         '变动类型', '变动原因', '关联订单', '操作人', '时间'])
        
        # 写入数据行
        for log in credit_logs:
            # 格式化created_at
            if isinstance(log.get('created_at'), datetime.datetime):
                created_at = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                created_at = log.get('created_at', '')
                
            writer.writerow([
                log.get('log_id', ''),
                log.get('user_id', ''),
                log.get('username', ''),
                log.get('change_amount', ''),
                log.get('credit_before', ''),
                log.get('credit_after', ''),
                log.get('change_type', ''),
                log.get('reason', ''),
                log.get('related_order_id', '') or '-',
                log.get('operator', '') or '系统',
                created_at
            ])
        
        # 设置响应头，返回CSV文件
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=credit_logs_{timestamp}.csv"}
        )
    
    except Exception as e:
        import traceback
        print(f"导出信用记录异常: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f'导出信用记录失败: {str(e)}'
        }) 