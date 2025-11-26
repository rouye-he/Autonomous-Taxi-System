from flask import flash

# 不同类型的flash消息
def flash_success(message):
    """成功类型的Flash消息"""
    flash(message, 'success')

def flash_error(message):
    """错误类型的Flash消息"""
    flash(message, 'danger')  # Bootstrap使用danger表示错误

def flash_warning(message):
    """警告类型的Flash消息"""
    flash(message, 'warning')

def flash_info(message):
    """信息类型的Flash消息"""
    flash(message, 'info')

# 特定操作的Flash消息 - 添加常用操作统一处理
def flash_add_success(item_type, identifier=None):
    """添加操作成功的Flash消息
    
    Args:
        item_type: 添加的项目类型（如车辆、订单等）
        identifier: 可选，项目的标识（如车牌号、订单ID等）
    """
    if identifier:
        flash_success(f'成功添加{item_type}，标识: {identifier}')
    else:
        flash_success(f'成功添加{item_type}')

def flash_update_success(item_type, identifier=None):
    """更新操作成功的Flash消息"""
    if identifier:
        flash_success(f'成功更新{item_type}，标识: {identifier}')
    else:
        flash_success(f'成功更新{item_type}')

def flash_delete_success(item_type, identifier=None):
    """删除操作成功的Flash消息"""
    if identifier:
        flash_success(f'成功删除{item_type}，标识: {identifier}')
    else:
        flash_success(f'成功删除{item_type}')

def flash_operation_success(operation, item_type, identifier=None):
    """通用操作成功的Flash消息"""
    if identifier:
        flash_success(f'成功{operation}{item_type}，标识: {identifier}')
    else:
        flash_success(f'成功{operation}{item_type}')

def flash_operation_failed(operation, item_type, error=None):
    """操作失败的Flash消息"""
    if error:
        flash_error(f'{operation}{item_type}失败: {error}')
    else:
        flash_error(f'{operation}{item_type}失败') 