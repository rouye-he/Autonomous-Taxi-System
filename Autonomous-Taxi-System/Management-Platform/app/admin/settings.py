from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.extensions import db
from app.dao.system_parameter_dao import SystemParameterDAO
import json
import traceback

# 创建蓝图
settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/')
def index():
    """系统设置主页"""
    return render_template('settings/index.html')

@settings_bp.route('/vehicle_params')
def vehicle_params():
    """车辆参数设置页面"""
    return render_template('settings/vehicle_params.html')

@settings_bp.route('/city_map_params')
def city_map_params():
    """城市地图参数设置页面"""
    return render_template('settings/city_map_params.html')

@settings_bp.route('/api/city_map_params')
def get_city_map_params():
    """获取城市地图参数API"""
    try:
        # 从数据库获取参数
        params = SystemParameterDAO.get_all_parameters()
        
        # 提取城市地图相关参数
        city_centers = params.get('city_centers')
        city_scale_factors = params.get('city_scale_factors')
        city_zoom_levels = params.get('city_zoom_levels')
        
        return jsonify({
            'status': 'success',
            'message': '成功获取城市地图参数',
            'data': {
                'city_centers': city_centers,
                'city_scale_factors': city_scale_factors,
                'city_zoom_levels': city_zoom_levels
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取城市地图参数失败: {str(e)}'
        }), 500

@settings_bp.route('/api/save_city_centers', methods=['POST'])
def save_city_centers():
    """保存城市中心点设置"""
    try:
        # 获取请求数据
        data = request.get_json()
        city_centers = data.get('city_centers')
        
        if not city_centers:
            return jsonify({
                'status': 'error',
                'message': '未提供城市中心点数据'
            }), 400
        
        # 更新数据库
        success = SystemParameterDAO.update_parameter('city_centers', city_centers)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '城市中心点设置已保存'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '保存城市中心点设置失败'
            }), 500
            
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'保存城市中心点设置失败: {str(e)}'
        }), 500

@settings_bp.route('/api/save_city_scale_factors', methods=['POST'])
def save_city_scale_factors():
    """保存城市缩放比例设置"""
    try:
        # 获取请求数据
        data = request.get_json()
        city_scale_factors = data.get('city_scale_factors')
        
        if not city_scale_factors:
            return jsonify({
                'status': 'error',
                'message': '未提供城市缩放比例数据'
            }), 400
        
        # 更新数据库
        success = SystemParameterDAO.update_parameter('city_scale_factors', city_scale_factors)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '城市缩放比例设置已保存'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '保存城市缩放比例设置失败'
            }), 500
            
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'保存城市缩放比例设置失败: {str(e)}'
        }), 500

@settings_bp.route('/api/save_city_zoom_levels', methods=['POST'])
def save_city_zoom_levels():
    """保存城市缩放级别设置"""
    try:
        # 获取请求数据
        data = request.get_json()
        city_zoom_levels = data.get('city_zoom_levels')
        
        if not city_zoom_levels:
            return jsonify({
                'status': 'error',
                'message': '未提供城市缩放级别数据'
            }), 400
        
        # 更新数据库
        success = SystemParameterDAO.update_parameter('city_zoom_levels', city_zoom_levels)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '城市缩放级别设置已保存'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '保存城市缩放级别设置失败'
            }), 500
            
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'保存城市缩放级别设置失败: {str(e)}'
        }), 500 