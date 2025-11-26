// app.ts
App<IAppOption>({
  globalData: {
    logs: [] as number[],
    token: '',
    userInfo: null,
    defaultAvatarUrl: '/static/images/user-default.png'
  },
  onLaunch() {
    try {
      // 快速启动，异步恢复登录状态
      setTimeout(() => {
        this.restoreLoginState();
      }, 100);
      
      // 记录启动日志
      this.globalData.logs = this.globalData.logs || [];
      this.globalData.logs.unshift(Date.now());
      console.log('日志记录成功');
    } catch (e) {
      console.error('记录日志失败:', e);
    }

    // 登录
    wx.login({
      success: res => {
        console.log(res.code)
        // 发送 res.code 到后台换取 openId, sessionKey, unionId
      },
    })
  },
  
  // 恢复登录状态
  restoreLoginState() {
    try {
      // 使用异步API避免阻塞
      wx.getStorage({
        key: 'token',
        success: (res) => {
          this.globalData.token = res.data;
          console.log('恢复token成功');
        },
        fail: () => {
          console.log('未找到token');
        }
      });

      wx.getStorage({
        key: 'userInfo',
        success: (res) => {
          this.globalData.userInfo = res.data;
          console.log('恢复用户信息成功');
        },
        fail: () => {
          console.log('未找到用户信息');
        }
      });
    } catch (e) {
      console.error('恢复登录状态失败:', e);
    }
  }
})