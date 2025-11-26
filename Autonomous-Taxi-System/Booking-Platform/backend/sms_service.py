#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
import time
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

# 阿里云短信服务配置
# 请在环境变量中设置以下值:
# ALIBABA_CLOUD_ACCESS_KEY_ID
# ALIBABA_CLOUD_ACCESS_KEY_SECRET
import os

SMS_CONFIG = {
    'access_key_id': os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID', 'your-access-key-id'),
    'access_key_secret': os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET', 'your-access-key-secret'),
    'sign_name': '无人驾驶出租车平台',  # 短信签名名称
    'template_code': 'SMS_123456789',  # 短信模板CODE，需替换为实际的模板CODE
    'region_id': 'cn-hangzhou'
}

# 验证码缓存，实际项目中应该使用Redis等缓存服务
# 格式: {手机号: {'code': 验证码, 'expire_time': 过期时间戳}}
VERIFY_CODE_CACHE = {}

def generate_code(length=6):
    """生成指定长度的随机验证码"""
    return ''.join(random.choices('0123456789', k=length))

def send_verify_code(phone_number):
    """发送验证码到指定手机号"""
    # 生成6位验证码
    code = generate_code(6)
    
    # 设置验证码5分钟有效
    expire_time = int(time.time()) + 5 * 60
    
    # 缓存验证码
    VERIFY_CODE_CACHE[phone_number] = {
        'code': code,
        'expire_time': expire_time
    }
    
    try:
        # 创建ACS客户端
        client = AcsClient(
            SMS_CONFIG['access_key_id'],
            SMS_CONFIG['access_key_secret'],
            SMS_CONFIG['region_id']
        )
        
        # 创建短信发送请求
        request = CommonRequest()
        request.set_accept_format('json')
        request.set_domain('dysmsapi.aliyuncs.com')
        request.set_method('POST')
        request.set_protocol_type('https')
        request.set_version('2017-05-25')
        request.set_action_name('SendSms')
        
        # 设置请求参数
        request.add_query_param('PhoneNumbers', phone_number)
        request.add_query_param('SignName', SMS_CONFIG['sign_name'])
        request.add_query_param('TemplateCode', SMS_CONFIG['template_code'])
        request.add_query_param('TemplateParam', json.dumps({'code': code}))
        
        # 发送短信
        response = client.do_action_with_exception(request)
        response_data = json.loads(response)
        
        # 检查发送结果
        if response_data.get('Code') == 'OK':
            return {'success': True, 'message': '验证码发送成功'}
        else:
            return {'success': False, 'message': f"验证码发送失败: {response_data.get('Message')}"}
    
    except Exception as e:
        return {'success': False, 'message': f"验证码发送失败: {str(e)}"}

def verify_code(phone_number, code):
    """验证手机验证码是否正确"""
    # 获取缓存的验证码信息
    cache_info = VERIFY_CODE_CACHE.get(phone_number)
    
    # 验证码不存在
    if not cache_info:
        return {'success': False, 'message': '验证码不存在或已过期'}
    
    # 验证码已过期
    if int(time.time()) > cache_info['expire_time']:
        # 删除过期验证码
        del VERIFY_CODE_CACHE[phone_number]
        return {'success': False, 'message': '验证码已过期'}
    
    # 验证码不匹配
    if cache_info['code'] != code:
        return {'success': False, 'message': '验证码错误'}
    
    # 验证通过，删除已使用的验证码
    del VERIFY_CODE_CACHE[phone_number]
    return {'success': True, 'message': '验证码正确'}

# 测试代码
if __name__ == '__main__':
    # 测试发送验证码
    test_phone = '13800138000'
    result = send_verify_code(test_phone)
    print(result)
    
    if result['success']:
        # 获取缓存中的验证码（实际使用中不应这样操作）
        print(f"缓存的验证码: {VERIFY_CODE_CACHE[test_phone]['code']}")
        
        # 测试验证码验证
        test_code = VERIFY_CODE_CACHE[test_phone]['code']
        verify_result = verify_code(test_phone, test_code)
        print(verify_result) 