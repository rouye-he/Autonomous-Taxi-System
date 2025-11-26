import { NOTIFY_CONFIG, NOTIFY_TYPES } from '../../utils/notification';

Component({
  properties: {},
  data: { message: '', type: 'info', icon: '', visible: false },
  
  lifetimes: {
    attached() { this.initEventBus(); }
  },
  
  methods: {
    // 初始化事件总线
    initEventBus() {
      const app = getApp();
      app.notificationComponent = this; // 注册到全局
    },
    
    // 显示通知
    show(message: string, type: string = NOTIFY_TYPES.INFO, duration: number = NOTIFY_CONFIG.DURATION) {
      this.setData({
        message, type,
        icon: NOTIFY_CONFIG.ICON_MAP[type as keyof typeof NOTIFY_CONFIG.ICON_MAP],
        visible: true
      });
      
      setTimeout(() => this.hide(), duration);
    },
    
    // 隐藏通知
    hide() { this.setData({ visible: false, message: '' }); }
  }
}); 