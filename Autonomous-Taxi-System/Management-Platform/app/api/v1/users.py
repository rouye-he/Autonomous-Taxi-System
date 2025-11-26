from flask import jsonify, request
from app.models import User
from app.api.v1 import api_v1
from app import db

# 获取用户列表API
@api_v1.route('/users', methods=['GET'])
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('limit', 10, type=int)
    status = request.args.get('status')
    
    query = User.query
    
    # 应用筛选条件
    if status:
        query = query.filter_by(status=status)
    
    # 分页
    paginated_users = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # 格式化响应
    response = {
        'code': 200,
        'message': 'success',
        'data': {
            'total': paginated_users.total,
            'pages': paginated_users.pages,
            'current_page': paginated_users.page,
            'users': [user.to_dict() for user in paginated_users.items]
        }
    }
    
    return jsonify(response)

# 获取用户详情API
@api_v1.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': user.to_dict()
    })

# 创建用户API
@api_v1.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['username', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'code': 400,
                'message': f'Missing required field: {field}'
            }), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({
            'code': 400,
            'message': 'Username already exists'
        }), 400
    
    try:
        from datetime import datetime
        # 创建用户
        user = User(
            username=data['username'],
            password=data['password'],
            real_name=data.get('real_name'),
            phone=data.get('phone'),
            email=data.get('email'),
            gender=data.get('gender'),
            birth_date=datetime.strptime(data['birth_date'], '%Y-%m-%d') if 'birth_date' in data and data['birth_date'] else None,
            id_card=data.get('id_card'),
            credit_score=data.get('credit_score', 100),
            balance=data.get('balance', 0.00),
            status=data.get('status', '正常')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'code': 201,
            'message': 'User created successfully',
            'data': user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'Failed to create user: {str(e)}'
        }), 500

# 更新用户API
@api_v1.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    try:
        # 更新用户属性
        if 'username' in data:
            # 检查新用户名是否已存在（且不是当前用户）
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.user_id != user_id:
                return jsonify({
                    'code': 400,
                    'message': 'Username already exists'
                }), 400
            user.username = data['username']
        
        # 更新其他字段
        if 'password' in data:
            user.password = data['password']
        if 'real_name' in data:
            user.real_name = data['real_name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'email' in data:
            user.email = data['email']
        if 'gender' in data:
            user.gender = data['gender']
        if 'birth_date' in data and data['birth_date']:
            from datetime import datetime
            user.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d')
        if 'id_card' in data:
            user.id_card = data['id_card']
        if 'credit_score' in data:
            user.credit_score = data['credit_score']
        if 'balance' in data:
            user.balance = data['balance']
        if 'status' in data:
            user.status = data['status']
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': 'User updated successfully',
            'data': user.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'Failed to update user: {str(e)}'
        }), 500

# 删除用户API
@api_v1.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': 'User deleted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'Failed to delete user: {str(e)}'
        }), 500 