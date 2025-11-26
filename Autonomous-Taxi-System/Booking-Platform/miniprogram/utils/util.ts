import { notify } from './notification'; // 导入通知管理器
import { CONFIG } from './config'; // 导入配置

export const formatTime = (date: Date) => {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hour = date.getHours()
  const minute = date.getMinutes()
  const second = date.getSeconds()

  return (
    [year, month, day].map(formatNumber).join('/') +
    ' ' +
    [hour, minute, second].map(formatNumber).join(':')
  )
}

const formatNumber = (n: number) => {
  const s = n.toString()
  return s[1] ? s : '0' + s
}

/**
 * 统一网络请求封装
 */
export interface RequestOptions {
  url: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  data?: any;
  header?: Record<string, string>;
  showLoading?: boolean; // 是否显示加载提示
  showError?: boolean; // 是否显示错误提示
  loadingText?: string; // 加载提示文本
  timeout?: number; // 请求超时时间
}

/**
 * 发起网络请求
 * @param options 请求选项
 * @returns Promise
 */
export function request(options: RequestOptions): Promise<any> {
  const { 
    showLoading = CONFIG.REQUEST.SHOW_LOADING, 
    showError = CONFIG.REQUEST.SHOW_ERROR, 
    loadingText = '请求中...',
    timeout = CONFIG.REQUEST.TIMEOUT
  } = options;
  
  return new Promise((resolve, reject) => {
    // 显示加载提示
    if (showLoading) notify.loading(loadingText);
    
    // 拼接完整URL
    const url = options.url.startsWith('http') ? 
      options.url : 
      `${CONFIG.API_BASE_URL}${options.url}`;
    
    // 获取token并构建请求头
    const token = wx.getStorageSync('token');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.header
    };
    
    // 如果有token，自动添加Authorization头
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    // 发起请求
    wx.request({
      url,
      method: options.method || 'GET',
      data: options.data || {},
      timeout,
      header: headers,
      success: (res: any) => {
        if (showLoading) notify.hideLoading(); // 隐藏加载提示
        
        // 服务器返回的数据
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          const error = {
            code: res.statusCode,
            message: res.data.message || '请求失败'
          };
          if (showError) notify.error(error.message); // 显示错误提示
          reject(error);
        }
      },
      fail: (err: any) => {
        if (showLoading) notify.hideLoading(); // 隐藏加载提示
        
        const error = {
          code: -1,
          message: err.errMsg || '网络错误'
        };
        if (showError) notify.error(error.message); // 显示错误提示
        reject(error);
      }
    });
  });
}
