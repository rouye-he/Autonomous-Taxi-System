Component({
  properties: {
    show: {
      type: Boolean,
      value: false
    },
    userInfo: {
      type: Object,
      value: {}
    },
    isLogged: {
      type: Boolean,
      value: false
    }
  },
  data: {
    
  },
  methods: {
    closeSidebar() {
      this.triggerEvent('close');
    },
    navigateTo(e: any) {
      const url = e.currentTarget.dataset.url;
      // 关闭侧边栏
      this.triggerEvent('close');
      // 导航到指定页面
      wx.navigateTo({
        url,
        fail: () => {
          // 如果页面不存在，给出提示
          wx.showToast({
            title: '功能开发中',
            icon: 'none'
          });
        }
      });
    }
  }
}) 