from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from app.dao.map_obstacle_dao import MapObstacleDAO
import traceback
import time

# 创建蓝图
map_obstacles_bp = Blueprint('map_obstacles', __name__, url_prefix='/map_obstacles')

@map_obstacles_bp.route('/')
def index():
    """障碍物管理页面"""
    page = request.args.get('page', 1, type=int)
    city_code = request.args.get('city_code')
    
    try:
        result = MapObstacleDAO.get_all_obstacles(page=page, per_page=10, city_code=city_code)
        return render_template('map_obstacles/index.html',
                              obstacles=result['obstacles'],
                              current_page=result['current_page'],
                              total_pages=result['total_pages'],
                              total_count=result['total_count'],
                              city_code=city_code)
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"障碍物管理页面加载错误: {error_traceback}")
        return render_template('map_obstacles/index.html',
                              error=str(e),
                              obstacles=[],
                              current_page=1,
                              total_pages=1,
                              total_count=0,
                              city_code=city_code)

@map_obstacles_bp.route('/create', methods=['GET', 'POST'])
def create():
    """创建障碍物页面"""
    if request.method == 'POST':
        try:
            data = {
                'city_code': request.form.get('city_code'),
                'obstacle_type': request.form.get('obstacle_type'),
                'geometry_type': request.form.get('geometry_type'),
                'name': request.form.get('name'),
                'polygon_points': request.form.get('polygon_points'),
                'color': request.form.get('color'),
                'width': request.form.get('width', type=float, default=2.0),
                'is_active': request.form.get('is_active', type=int, default=1)
            }
            
            # 验证必填字段
            if not data['city_code'] or not data['obstacle_type'] or not data['polygon_points']:
                return render_template('map_obstacles/create.html',
                                     error="城市代码、障碍物类型和点坐标是必填项",
                                     data=data)
            
            # 创建障碍物
            obstacle_id = MapObstacleDAO.create_obstacle(data)
            
            if obstacle_id:
                return redirect(url_for('map_obstacles.index'))
            else:
                return render_template('map_obstacles/create.html',
                                     error="创建障碍物失败",
                                     data=data)
        except Exception as e:
            error_traceback = traceback.format_exc()
            print(f"创建障碍物错误: {error_traceback}")
            return render_template('map_obstacles/create.html',
                                 error=str(e),
                                 data=request.form)
    
    # GET请求，显示创建表单
    return render_template('map_obstacles/create.html')

@map_obstacles_bp.route('/edit/<int:obstacle_id>', methods=['GET', 'POST'])
def edit(obstacle_id):
    """编辑障碍物页面"""
    # 获取障碍物详情
    obstacle = MapObstacleDAO.get_obstacle_by_id(obstacle_id)
    
    if not obstacle:
        return redirect(url_for('map_obstacles.index'))
    
    if request.method == 'POST':
        try:
            data = {
                'city_code': request.form.get('city_code'),
                'obstacle_type': request.form.get('obstacle_type'),
                'geometry_type': request.form.get('geometry_type'),
                'name': request.form.get('name'),
                'polygon_points': request.form.get('polygon_points'),
                'color': request.form.get('color'),
                'width': request.form.get('width', type=float, default=2.0),
                'is_active': request.form.get('is_active', type=int, default=1)
            }
            
            # 验证必填字段
            if not data['city_code'] or not data['obstacle_type'] or not data['polygon_points']:
                return render_template('map_obstacles/edit.html',
                                     error="城市代码、障碍物类型和点坐标是必填项",
                                     obstacle=obstacle,
                                     data=data)
            
            # 更新障碍物
            success = MapObstacleDAO.update_obstacle(obstacle_id, data)
            
            if success:
                return redirect(url_for('map_obstacles.index'))
            else:
                return render_template('map_obstacles/edit.html',
                                     error="更新障碍物失败",
                                     obstacle=obstacle,
                                     data=data)
        except Exception as e:
            error_traceback = traceback.format_exc()
            print(f"更新障碍物错误: {error_traceback}")
            return render_template('map_obstacles/edit.html',
                                 error=str(e),
                                 obstacle=obstacle,
                                 data=request.form)
    
    # GET请求，显示编辑表单
    return render_template('map_obstacles/edit.html', obstacle=obstacle)

@map_obstacles_bp.route('/delete/<int:obstacle_id>', methods=['POST'])
def delete(obstacle_id):
    """删除障碍物"""
    try:
        success = MapObstacleDAO.delete_obstacle(obstacle_id)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': bool(success), 'message': '删除成功' if success else '删除失败'})
        else:
            return redirect(url_for('map_obstacles.index'))
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"删除障碍物错误: {error_traceback}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': str(e)}), 500
        else:
            return redirect(url_for('map_obstacles.index'))

@map_obstacles_bp.route('/toggle_active/<int:obstacle_id>', methods=['POST'])
def toggle_active(obstacle_id):
    """切换障碍物激活状态"""
    try:
        is_active = request.form.get('is_active', type=int)
        success = MapObstacleDAO.toggle_obstacle_active(obstacle_id, is_active)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': bool(success), 'active': bool(is_active)})
        else:
            return redirect(url_for('map_obstacles.index'))
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"切换障碍物状态错误: {error_traceback}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': str(e)}), 500
        else:
            return redirect(url_for('map_obstacles.index'))

# API接口
@map_obstacles_bp.route('/api/get_by_city/<city_code>', methods=['GET'])
def api_get_by_city(city_code):
    """API: 获取指定城市的所有障碍物"""
    try:
        obstacles = MapObstacleDAO.get_obstacles_by_city(city_code)
        return jsonify({
            'success': True,
            'data': obstacles
        })
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"获取城市障碍物API错误: {error_traceback}")
        return jsonify({
            'success': False,
            'message': str(e),
            'traceback': error_traceback
        }), 500

@map_obstacles_bp.route('/api/create', methods=['POST'])
def api_create():
    """API: 创建新障碍物"""
    try:
        data = request.json
        
        # 验证必填字段
        if not data.get('city_code') or not data.get('polygon_points'):
            return jsonify({
                'success': False,
                'message': "城市代码和点坐标是必填项"
            }), 400
        
        # 设置默认值
        if not data.get('obstacle_type'):
            data['obstacle_type'] = 'barrier'
            
        if not data.get('geometry_type'):
            data['geometry_type'] = 'line'  # 默认为线段类型
            
        if not data.get('name'):
            data['name'] = f"障碍物_{int(time.time())}"
            
        if not data.get('color'):
            data['color'] = '#cc0000'  # 默认红色
        
        # 创建障碍物
        obstacle_id = MapObstacleDAO.create_obstacle(data)
        
        if obstacle_id:
            # 获取创建的障碍物
            new_obstacle = MapObstacleDAO.get_obstacle_by_id(obstacle_id)
            return jsonify({
                'success': True,
                'message': "障碍物创建成功",
                'data': new_obstacle
            })
        else:
            return jsonify({
                'success': False,
                'message': "创建障碍物失败"
            }), 500
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"创建障碍物API错误: {error_traceback}")
        return jsonify({
            'success': False,
            'message': str(e),
            'traceback': error_traceback
        }), 500

@map_obstacles_bp.route('/api/delete', methods=['POST'])
def api_delete():
    """API: 删除障碍物"""
    try:
        data = request.json
        obstacle_id = data.get('obstacle_id')
        
        if not obstacle_id:
            return jsonify({
                'success': False,
                'message': "缺少障碍物ID"
            }), 400
        
        success = MapObstacleDAO.delete_obstacle(obstacle_id)
        
        return jsonify({
            'success': bool(success),
            'message': "障碍物删除成功" if success else "障碍物删除失败"
        })
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"删除障碍物API错误: {error_traceback}")
        return jsonify({
            'success': False,
            'message': str(e),
            'traceback': error_traceback
        }), 500 