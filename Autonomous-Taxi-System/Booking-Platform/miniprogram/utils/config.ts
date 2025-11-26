// 全局配置文件
export const CONFIG = {
  // API配置
  API_BASE_URL: 'http://localhost:5001',
  
  // 通知配置
  NOTIFICATION: {
    DEFAULT_DURATION: 3000, // 默认显示时长
    LOADING_MASK: true,     // 加载遮罩
    AUTO_HIDE_LOADING: true // 自动隐藏加载
  },
  
  // 请求配置
  REQUEST: {
    TIMEOUT: 10000,         // 请求超时时间
    RETRY_COUNT: 3,         // 重试次数
    SHOW_LOADING: false,    // 默认不显示加载
    SHOW_ERROR: true        // 默认显示错误
  },
  
  // 页面配置
  PAGE: {
    PAGE_SIZE: 20,          // 分页大小
    MAX_HISTORY: 100        // 最大历史记录
  }
} as const; 