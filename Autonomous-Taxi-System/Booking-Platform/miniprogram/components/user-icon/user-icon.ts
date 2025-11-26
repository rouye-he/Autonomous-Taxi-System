import { checkLoginStatus } from '../../utils/db';

Component({
  properties: {
    userInfo: {
      type: Object,
      value: {}
    }
  },
  data: {
    
  },
  methods: {
    toggleSidebar() {
      // 检查登录状态（会自动恢复本地存储的登录信息）
      if (!checkLoginStatus()) {
        wx.navigateTo({
          url: '/pages/login/login',
        });
        return;
      }
      
      this.triggerEvent('toggle');
    }
  }
}) 