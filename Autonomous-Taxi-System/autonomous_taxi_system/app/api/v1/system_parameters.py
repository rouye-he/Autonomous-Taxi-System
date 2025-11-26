from flask import jsonify, request
from app.api.v1 import api_v1
from app.dao.system_parameter_dao import SystemParameterDAO
import traceback

@api_v1.route('/system_parameters', methods=['GET'])
def get_system_parameters():
    """获取系统参数"""
    try:
        all_params = SystemParameterDAO.get_all_parameters()
        
        return jsonify({
            'success': True,
            'message': '成功获取系统参数',
            'parameters': all_params
        })
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"获取系统参数错误: {e}")
        print(error_traceback)
        
        return jsonify({
            'success': False,
            'message': f'获取系统参数失败: {str(e)}',
            'error': error_traceback
        }), 500

@api_v1.route('/city_price_factors', methods=['GET'])
def get_city_price_factors():
    """获取所有城市价格系数"""
    try:
        from app.config.vehicle_params import CITY_PRICE_FACTORS
        
        return jsonify({
            'success': True,
            'message': '成功获取城市价格系数',
            'price_factors': CITY_PRICE_FACTORS
        })
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"获取城市价格系数错误: {e}")
        print(error_traceback)
        
        return jsonify({
            'success': False,
            'message': f'获取城市价格系数失败: {str(e)}',
            'error': error_traceback
        }), 500

@api_v1.route('/system_parameters', methods=['POST'])
def update_system_parameters():
    """更新系统参数"""
    try:
        data = request.get_json()
        if not data or 'parameters' not in data:
            return jsonify({
                'success': False,
                'message': '请求格式错误，需要包含parameters字段'
            }), 400
        
        parameters = data['parameters']
        
        # 确保表存在
        if not SystemParameterDAO.create_parameters_table_if_not_exists():
            logger.error("系统参数表不存在或创建失败")
            return jsonify({
                'success': False,
                'message': '系统参数表不存在或创建失败'
            }), 500
        
        # 批量更新参数
        success_count, total_count = SystemParameterDAO.batch_update_parameters(parameters)
        
        if success_count == 0:
            logger.warning("没有成功更新任何参数")
            return jsonify({
                'success': False,
                'message': '更新系统参数失败，没有成功更新任何参数',
                'updated_count': 0,
                'total_count': total_count
            }), 500
        
        return jsonify({
            'success': True,
            'message': f'更新系统参数成功，更新了{success_count}/{total_count}个参数',
            'updated_count': success_count,
            'total_count': total_count
        })
    except Exception as e:
        logger.error(f"更新系统参数时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新系统参数失败: {str(e)}'
        }), 500 