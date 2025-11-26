interface ChatMessage {
  id: number;
  message: string;
  is_user: boolean;
  role: 'user' | 'assistant';
  created_at: string;
  date: string;
  time: string;
}

Page({
  data: {
    chatHistory: [] as ChatMessage[],
    availableDates: [] as string[],
    selectedDate: '',
    loading: false,
    hasMore: false,
    currentPage: 1,
    perPage: 50,
    scrollTop: 0,
    toView: '',
    userAvatar: '/static/images/user-default.png',
    robotAvatar: '/static/images/robot-avatar.png',
    showRobotImage: true,
    showUserImage: true
  },

  onLoad() {
    this.loadChatHistory(); // 加载所有历史记录
    this.loadUserAvatar();
    this.checkRobotAvatar();
  },

  onShow() {
    // 页面显示时刷新数据
    this.loadChatHistory();
  },

  // 加载对话历史记录
  async loadChatHistory(isLoadMore = false) {
    if (this.data.loading) return;
    
    this.setData({ loading: true });
    
    try {
      const token = wx.getStorageSync('token');
      if (!token) {
        wx.showToast({ title: '请先登录', icon: 'none' });
        return;
      }

      const params: any = {
        page: isLoadMore ? this.data.currentPage + 1 : 1,
        per_page: this.data.perPage
      };

      if (this.data.selectedDate) {
        params.date = this.data.selectedDate;
      }

      const queryString = Object.keys(params)
        .map(key => `${key}=${params[key]}`)
        .join('&');

      const response = await this.requestAPI(`http://localhost:5001/api/chat/history?${queryString}`, 'GET');

      if (response.code === 0) {
        const newChatHistory = response.data.chat_history;
        const availableDates = response.data.available_dates;

        if (isLoadMore) {
          this.setData({
            chatHistory: [...this.data.chatHistory, ...newChatHistory],
            currentPage: this.data.currentPage + 1,
            hasMore: response.data.pagination.has_next,
            availableDates
          });
        } else {
          this.setData({
            chatHistory: newChatHistory,
            currentPage: 1,
            hasMore: response.data.pagination.has_next,
            availableDates,
            scrollTop: 0
          });
        }
      } else {
        wx.showToast({ title: response.message || '加载失败', icon: 'none' });
      }
    } catch (error) {
      console.error('加载对话历史失败:', error);
      wx.showToast({ title: '网络异常，请重试', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  // 日期选择器事件
  onDateChange(e: any) {
    const selectedDate = e.detail.value;
    this.setData({ 
      selectedDate,
      currentPage: 1 
    });
    this.loadChatHistory();
  },

  // 清除日期筛选
  clearDateFilter() {
    this.setData({ 
      selectedDate: '',
      currentPage: 1 
    });
    this.loadChatHistory();
  },

  // 快速选择日期
  selectDate(e: any) {
    const date = e.currentTarget.dataset.date;
    this.setData({ 
      selectedDate: date,
      currentPage: 1 
    });
    this.loadChatHistory();
  },

  // 加载更多
  loadMore() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadChatHistory(true);
    }
  },

  // 加载用户头像
  loadUserAvatar() {
    try {
      const userInfo = wx.getStorageSync('userInfo');
      if (userInfo && userInfo.avatar_url) {
        this.setData({ userAvatar: userInfo.avatar_url });
      }
    } catch (error) {
      console.log('加载用户头像失败:', error);
    }
  },

  // 检查机器人头像
  checkRobotAvatar() {
    // 使用网络请求检测图片
    wx.request({
      url: this.data.robotAvatar,
      method: 'HEAD',
      success: () => {
        this.setData({ showRobotImage: true });
      },
      fail: () => {
        this.setData({ showRobotImage: false });
      }
    });
  },

  // 用户头像加载失败
  onUserAvatarError() {
    this.setData({ showUserImage: false });
  },

  // 机器人头像加载失败
  onRobotAvatarError() {
    this.setData({ showRobotImage: false });
  },

  // API请求封装
  requestAPI(url: string, method: 'GET' | 'POST' = 'GET', data?: any): Promise<any> {
    return new Promise((resolve, reject) => {
      const token = wx.getStorageSync('token');
      
      wx.request({
        url,
        method,
        header: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        data,
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(res.data);
          } else {
            reject(new Error(`HTTP ${res.statusCode}`));
          }
        },
        fail: reject
      });
    });
  }
}); 