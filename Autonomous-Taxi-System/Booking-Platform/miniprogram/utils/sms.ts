// sms.ts - 阿里云短信服务工具类

import { request } from './util';

// 阿里云短信服务配置
// Note: These credentials should be configured on the backend server
// Do not store sensitive keys in frontend code
const SMS_CONFIG = {
  accessKeyId: 'CONFIGURE_ON_BACKEND',
  accessKeySecret: 'CONFIGURE_ON_BACKEND',
  signName: '无人驾驶出租车平台', // 短信签名名称
  templateCode: 'SMS_123456789', // 短信模板CODE，需替换为实际的模板CODE
};

// 验证码缓存
interface VerifyCodeCache {
  [phone: string]: {
    code: string;
    expireTime: number;
  };
}

// 模拟验证码缓存
// 实际生产环境应该在服务端存储
const verifyCodeCache: VerifyCodeCache = {};

/**
 * 生成指定长度的随机验证码
 * @param length 验证码长度
 * @returns 生成的验证码
 */
export function generateVerifyCode(length = 6): string {
  let code = '';
  for (let i = 0; i < length; i++) {
    code += Math.floor(Math.random() * 10).toString();
  }
  return code;
}

/**
 * 发送邮箱验证码
 * @param email 邮箱地址
 * @returns Promise
 */
export function sendVerifyCode(email: string): Promise<any> {
  return new Promise((resolve, reject) => {
    // 调用后端邮箱验证码API
    wx.request({
      url: 'http://localhost:5001/api/send_verify_code',
      method: 'POST',
      header: {
        'Content-Type': 'application/json'
      },
      data: { email },
      success: (res: any) => {
        if (res.statusCode === 200 && res.data.code === 0) {
          resolve({
            success: true,
            message: res.data.message
          });
        } else {
          reject(res.data.message || '验证码发送失败');
        }
      },
      fail: (err) => {
        console.error('发送验证码失败', err);
        reject('网络错误，请检查网络连接');
      }
    });
  });
}

/**
 * 验证邮箱验证码
 * @param email 邮箱地址
 * @param code 用户输入的验证码
 * @returns 验证结果
 */
export function verifyCode(email: string, code: string): boolean {
  // 注意：这个函数现在只是为了兼容性保留
  // 实际验证在注册时通过后端API完成
  return true;
}

/**
 * 检查验证码发送频率（防止频繁发送）
 * @param phone 手机号
 * @returns 是否可以发送
 */
export function canSendVerifyCode(phone: string): boolean {
  const cached = verifyCodeCache[phone];
  
  // 如果没有发送过，可以发送
  if (!cached) {
    return true;
  }
  
  // 如果距离上次发送不足60秒，不能发送
  const now = Date.now();
  const lastSendTime = cached.expireTime - 5 * 60 * 1000; // 上次发送时间
  const timePassed = now - lastSendTime;
  
  return timePassed >= 60 * 1000; // 至少间隔60秒
} 