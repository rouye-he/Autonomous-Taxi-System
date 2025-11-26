#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask_mail import Mail, Message
import random
import time

# 邮箱配置
EMAIL_CONFIG = {
    'MAIL_SERVER': 'smtp.163.com',
    'MAIL_PORT': 465,
    'MAIL_USE_SSL': True,
    'MAIL_USERNAME': '13998252675@163.com',  # 用户的163邮箱
    'MAIL_PASSWORD': 'HNsN3AfgpiJsT5yz',  # 163邮箱授权码
    'MAIL_DEFAULT_SENDER': '13998252675@163.com'  # 用户的163邮箱
}

# 验证码缓存 {邮箱: {'code': 验证码, 'expire_time': 过期时间戳}}
EMAIL_CODE_CACHE = {}

def init_mail(app):
    """初始化邮件服务"""
    app.config.update(EMAIL_CONFIG)
    return Mail(app)

def generate_email_code(length=6):
    """生成邮箱验证码"""
    return ''.join(random.choices('0123456789', k=length))

def send_email_verify_code(mail, email):
    """发送邮箱验证码"""
    code = generate_email_code(6)
    expire_time = int(time.time()) + 5 * 60  # 5分钟有效期
    
    EMAIL_CODE_CACHE[email] = {'code': code, 'expire_time': expire_time}
    
    try:
        msg = Message(
            subject='无人驾驶出租车平台验证码',
            recipients=[email],
            body=f'您的验证码是：{code}，5分钟内有效，请勿泄露给他人。'
        )
        mail.send(msg)
        return {'success': True, 'message': '验证码发送成功'}
    except Exception as e:
        return {'success': False, 'message': f'验证码发送失败: {str(e)}'}

def verify_email_code(email, code):
    """验证邮箱验证码"""
    cache_info = EMAIL_CODE_CACHE.get(email)
    
    if not cache_info:
        return {'success': False, 'message': '验证码不存在或已过期'}
    
    if int(time.time()) > cache_info['expire_time']:
        del EMAIL_CODE_CACHE[email]
        return {'success': False, 'message': '验证码已过期'}
    
    if cache_info['code'] != code:
        return {'success': False, 'message': '验证码错误'}
    
    del EMAIL_CODE_CACHE[email]
    return {'success': True, 'message': '验证码正确'} 