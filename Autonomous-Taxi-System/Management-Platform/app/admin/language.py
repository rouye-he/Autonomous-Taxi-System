"""
语言切换模块
"""
from flask import Blueprint, session, redirect, request, url_for

language_bp = Blueprint('language', __name__, url_prefix='/language')

@language_bp.route('/set/<lang>')
def set_language(lang):
    """设置语言"""
    if lang in ['zh', 'en']:
        session['language'] = lang
    
    # 获取来源页面，如果没有则重定向到首页
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    return redirect(url_for('dashboard.index'))
