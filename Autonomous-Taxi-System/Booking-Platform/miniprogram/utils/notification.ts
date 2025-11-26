import { CONFIG } from './config';

// 通知类型配置
export const NOTIFY_TYPES = {
  SUCCESS: 'success', ERROR: 'error', WARNING: 'warning', INFO: 'info'
} as const;

// 通知配置
export const NOTIFY_CONFIG = {
  DURATION: CONFIG.NOTIFICATION.DEFAULT_DURATION,
  ICON_MAP: { // 图标映射
    [NOTIFY_TYPES.SUCCESS]: '✓',
    [NOTIFY_TYPES.ERROR]: '✗',
    [NOTIFY_TYPES.WARNING]: '⚠',
    [NOTIFY_TYPES.INFO]: 'ℹ'
  },
  COLOR_MAP: { // 颜色映射
    [NOTIFY_TYPES.SUCCESS]: '#52c41a',
    [NOTIFY_TYPES.ERROR]: '#ff4d4f',
    [NOTIFY_TYPES.WARNING]: '#faad14',
    [NOTIFY_TYPES.INFO]: '#1890ff'
  }
};

type NotifyType = typeof NOTIFY_TYPES[keyof typeof NOTIFY_TYPES];

interface NotifyOptions {
  type?: NotifyType;
  duration?: number;
  mask?: boolean;
  useComponent?: boolean; // 是否使用自定义组件
}

// 通知管理器
class NotificationManager {
  private static instance: NotificationManager;
  
  static getInstance(): NotificationManager {
    return this.instance || (this.instance = new NotificationManager());
  }

  // 获取自定义组件实例
  private getComponent(): any {
    const app = getApp();
    return app.notificationComponent;
  }

  // 显示通知
  show(message: string, options: NotifyOptions = {}): void {
    const { type = NOTIFY_TYPES.INFO, duration = NOTIFY_CONFIG.DURATION, mask = false, useComponent = false } = options;
    
    // 优先使用自定义组件
    const component = this.getComponent();
    if (useComponent && component) {
      component.show(message, type, duration);
    } else {
      // 降级到原生toast
      wx.showToast({
        title: `${NOTIFY_CONFIG.ICON_MAP[type]} ${message}`,
        icon: 'none', duration, mask
      });
    }
  }

  // 成功通知
  success(message: string, duration?: number, useComponent?: boolean): void {
    this.show(message, { type: NOTIFY_TYPES.SUCCESS, duration, useComponent });
  }

  // 错误通知
  error(message: string, duration?: number, useComponent?: boolean): void {
    this.show(message, { type: NOTIFY_TYPES.ERROR, duration, useComponent });
  }

  // 警告通知
  warning(message: string, duration?: number, useComponent?: boolean): void {
    this.show(message, { type: NOTIFY_TYPES.WARNING, duration, useComponent });
  }

  // 信息通知
  info(message: string, duration?: number, useComponent?: boolean): void {
    this.show(message, { type: NOTIFY_TYPES.INFO, duration, useComponent });
  }

  // 加载提示
  loading(message: string = '加载中...'): void {
    wx.showLoading({ title: message, mask: CONFIG.NOTIFICATION.LOADING_MASK });
  }

  // 隐藏加载
  hideLoading(): void {
    wx.hideLoading();
  }

  // 确认对话框
  confirm(content: string, title: string = '提示'): Promise<boolean> {
    return new Promise((resolve) => {
      wx.showModal({
        title, content,
        success: (res) => resolve(res.confirm),
        fail: () => resolve(false)
      });
    });
  }
}

// 导出单例实例
export const notify = NotificationManager.getInstance(); 