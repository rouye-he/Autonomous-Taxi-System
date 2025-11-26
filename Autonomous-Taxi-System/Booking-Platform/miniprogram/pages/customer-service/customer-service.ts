interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  time: string;
  date?: string; // 消息日期，用于分组
}

Page({
  data: {
    messages: [] as Message[],
    inputText: '',
    isConnected: true,
    isTyping: false,
    isSending: false,
    scrollTop: 0,
    toView: '',
    userAvatar: '/static/images/user-default.png',
    robotAvatar: '/static/images/robot-avatar.png',
    showRobotImage: true,
    showUserImage: true,
    showQuickQuestions: true,
    quickQuestions: [
      '如何下单？',
      '如何取消订单？',
      '费用如何计算？',
      '当前平台支持哪些城市？',
      '当前平台有哪些车型？各种车型的特点和乘坐价格是什么？',
      '账户余额不足怎么办？',
      '如何查看订单状态？'
    ],
    messageId: 1,
    selectedDate: '', // 选中的日期
    availableDates: [] as string[], // 有对话记录的日期
    showAvailableDates: false, // 是否显示可用日期列表
    isHistoryMode: false, // 是否处于历史记录模式
    historyLoading: false // 历史记录加载状态
  },

  onLoad() {
    this.checkRobotAvatar();
    this.loadUserAvatar();
    this.loadAvailableDates(); // 加载可用的对话日期
    
    // 默认加载今日的聊天记录
    const today = this.formatDateString(new Date());
    this.loadTodayChat(today);
  },

  // 返回上一页
  onBack() {
    wx.navigateBack();
  },

  // 格式化日期为YYYY-MM-DD格式
  formatDateString(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  },

  // 加载今日聊天记录
  async loadTodayChat(today: string) {
    this.setData({ historyLoading: true, isTyping: true });
    
    try {
      const token = wx.getStorageSync('token');
      if (!token) {
        this.initChat(); // 如果未登录，显示默认欢迎消息
        this.setData({ historyLoading: false, isTyping: false });
        return;
      }
      
      const response: any = await this.requestAPI(`http://localhost:5001/api/chat/history?date=${today}&page=1&per_page=100`, 'GET');
      
      if (response.code === 0 && response.data.chat_history && response.data.chat_history.length > 0) {
        // 有今日聊天记录
        const chatHistory = response.data.chat_history;
        
        // 转换为消息格式
        const messages: Message[] = chatHistory.map((item: any) => ({
          id: this.data.messageId++,
          role: item.is_user ? 'user' : 'assistant',
          content: item.message,
          time: item.time,
          date: item.date
        }));
        
        this.setData({
          messages,
          isTyping: false,
          historyLoading: false
        });
      } else {
        // 无今日聊天记录，显示默认欢迎消息
        this.initChat();
        this.setData({ historyLoading: false, isTyping: false });
      }
      
      // 滚动到底部
      setTimeout(() => {
        this.scrollToBottom();
      }, 300);
    } catch (error) {
      console.error('加载今日聊天记录失败:', error);
      this.initChat(); // 出错时显示默认欢迎消息
      this.setData({ historyLoading: false, isTyping: false });
    }
  },

  initChat() {
    const welcomeMessage: Message = {
      id: this.data.messageId++,
      role: 'assistant',
      content: '您好！我是无人驾驶出租车平台的智能客服助手，很高兴为您服务。请问有什么可以帮助您的吗？',
      time: this.formatTime(new Date())
    };
    
    this.setData({
      messages: [welcomeMessage]
    });
  },

  onInput(e: any) {
    this.setData({
      inputText: e.detail.value,
      showQuickQuestions: !e.detail.value
    });
  },

  sendMessage() {
    const content = this.data.inputText.trim();
    if (!content || this.data.isSending) return;

    this.addUserMessage(content);
    this.setData({
      inputText: '',
      isSending: true,
      isTyping: true,
      showQuickQuestions: false
    });

    this.callCozeAPI(content);
  },

  sendQuickQuestion(e: any) {
    const question = e.currentTarget.dataset.question;
    this.setData({ inputText: question });
    this.sendMessage();
  },

  addUserMessage(content: string) {
    const userMessage: Message = {
      id: this.data.messageId++,
      role: 'user',
      content,
      time: this.formatTime(new Date())
    };

    this.setData({
      messages: [...this.data.messages, userMessage]
    });
    this.scrollToBottom();
  },

  addAssistantMessage(content: string) {
    const assistantMessage: Message = {
      id: this.data.messageId++,
      role: 'assistant',
      content,
      time: this.formatTime(new Date())
    };

    this.setData({
      messages: [...this.data.messages, assistantMessage],
      isTyping: false,
      isSending: false
    });
    this.scrollToBottom();
  },

  async callCozeAPI(content: string) {
    try {
      const token = wx.getStorageSync('token');
      const userInfo = wx.getStorageSync('userInfo');
      const userId = (userInfo && userInfo.user_id) ? userInfo.user_id : 'anonymous';

      const response = await this.requestCozeAPI({
        content,
        userId: userId.toString()
      });

      if (response.code === 0) {
        this.addAssistantMessage(response.data.content);
      } else {
        this.addAssistantMessage('抱歉，我暂时无法回答您的问题，请稍后再试或联系人工客服。');
      }
    } catch (error) {
      console.error('调用智能客服API失败:', error);
      this.addAssistantMessage('网络连接异常，请检查网络后重试。');
    }
  },

  requestCozeAPI(data: { content: string; userId: string }): Promise<any> {
    return new Promise((resolve, reject) => {
      const token = wx.getStorageSync('token');
      
      wx.request({
        url: 'http://localhost:5001/api/chat',
        method: 'POST',
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
  },

  // 通用API请求方法
  requestAPI(url: string, method: 'GET' | 'POST' = 'GET', data: any = null): Promise<any> {
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
        success: (res: any) => {
          if (res.statusCode === 200) {
            resolve(res.data);
          } else {
            reject(new Error(`HTTP ${res.statusCode}`));
          }
        },
        fail: reject
      });
    });
  },

  scrollToBottom() {
    const lastMessage = this.data.messages[this.data.messages.length - 1];
    const lastMessageId = lastMessage ? lastMessage.id : null;
    if (lastMessageId) {
      this.setData({
        toView: `msg${lastMessageId}`
      });
      
      // 额外添加延迟确保滚动生效
      setTimeout(() => {
        this.setData({
          toView: `msg${lastMessageId}`
        });
      }, 100);
    }
  },

  formatTime(date: Date): string {
    // 显示详细时间：年-月-日 时:分:秒
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    
    const now = new Date();
    const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    const messageDate = `${year}-${month}-${day}`;
    
    if (messageDate === today) {
      // 今天只显示时间
      return `今天 ${hours}:${minutes}:${seconds}`;
    } else {
      // 其他日期显示完整日期时间
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    }
  },

  onShareAppMessage() {
    return {
      title: '智能客服 - 无人驾驶出租车平台',
      path: '/pages/customer-service/customer-service'
    };
  },

  checkRobotAvatar() {
    // 检查机器人头像文件是否存在 #检查头像文件
    wx.getImageInfo({
      src: this.data.robotAvatar,
      success: () => {
        this.setData({ showRobotImage: true });
      },
      fail: () => {
        this.setData({ showRobotImage: false });
      }
    });
  },

  loadUserAvatar() {
    const userInfo = wx.getStorageSync('userInfo');
    if (userInfo && userInfo.avatar_url) {
      this.setData({ userAvatar: userInfo.avatar_url });
      this.checkUserAvatar();
    } else {
      const app = getApp<IAppOption>();
      if (app.globalData.userInfo && app.globalData.userInfo.avatar_url) {
        this.setData({ userAvatar: app.globalData.userInfo.avatar_url });
        this.checkUserAvatar();
      } else {
        this.setData({ userAvatar: '/static/images/user-default.png', showUserImage: true });
      }
    }
  },

  checkUserAvatar() {
    wx.getImageInfo({
      src: this.data.userAvatar,
      success: () => {
        this.setData({ showUserImage: true });
      },
      fail: () => {
        this.setData({ showUserImage: false, userAvatar: '/static/images/user-default.png' });
      }
    });
  },

  onAvatarError(e: any) {
    const role = e.currentTarget.dataset.role;
    if (role === 'assistant') {
      this.setData({ showRobotImage: false });
    } else if (role === 'user') {
      this.setData({ showUserImage: false, userAvatar: '/static/images/user-default.png' });
    }
  },

  // 加载可用的对话日期
  async loadAvailableDates() {
    try {
      const token = wx.getStorageSync('token');
      if (!token) return;
      
      const userInfo = wx.getStorageSync('userInfo');
      if (!userInfo || !userInfo.user_id) return;
      
      const response: any = await this.requestAPI('http://localhost:5001/api/chat/history?page=1&per_page=1', 'GET');
      
      if (response.code === 0 && response.data.available_dates) {
        this.setData({
          availableDates: response.data.available_dates
        });
      }
    } catch (error) {
      console.error('获取可用日期失败:', error);
    }
  },
  
  // 日期选择器事件
  onDateChange(e: any) {
    const selectedDate = e.detail.value;
    this.setData({ 
      selectedDate,
      isHistoryMode: true,
      showAvailableDates: false,
      showQuickQuestions: false,
      messages: [],
      isTyping: false
    });
    this.loadChatHistory(selectedDate);
  },
  
  // 清除日期筛选
  clearDateFilter() {
    this.setData({ 
      selectedDate: '',
      isHistoryMode: false,
      showAvailableDates: false,
      showQuickQuestions: true
    });
    
    // 加载今日聊天记录，而不是重置为初始对话
    const today = this.formatDateString(new Date());
    this.loadTodayChat(today);
  },
  
  // 快速选择日期
  selectDate(e: any) {
    const date = e.currentTarget.dataset.date;
    this.setData({ 
      selectedDate: date,
      isHistoryMode: true,
      showAvailableDates: false,
      showQuickQuestions: false,
      messages: [],
      isTyping: false
    });
    this.loadChatHistory(date);
  },
  
  // 加载对话历史记录
  async loadChatHistory(date: string) {
    if (this.data.historyLoading) return;
    
    this.setData({ historyLoading: true, isTyping: true });
    
    try {
      const token = wx.getStorageSync('token');
      if (!token) {
        wx.showToast({ title: '请先登录', icon: 'none' });
        return;
      }
      
      const response: any = await this.requestAPI(`http://localhost:5001/api/chat/history?date=${date}&page=1&per_page=100`, 'GET');
      
      if (response.code === 0) {
        const chatHistory = response.data.chat_history;
        
        // 转换为消息格式
        const messages: Message[] = chatHistory.map((item: any) => ({
          id: this.data.messageId++,
          role: item.is_user ? 'user' : 'assistant',
          content: item.message,
          time: item.time,
          date: item.date
        }));
        
        this.setData({
          messages,
          isTyping: false,
          historyLoading: false
        });
        
        // 滚动到底部
        setTimeout(() => {
          this.scrollToBottom();
        }, 300);
      } else {
        wx.showToast({ title: response.message || '加载失败', icon: 'none' });
        this.setData({ isTyping: false, historyLoading: false });
      }
    } catch (error) {
      console.error('加载对话历史失败:', error);
      wx.showToast({ title: '网络异常，请重试', icon: 'none' });
      this.setData({ isTyping: false, historyLoading: false });
    }
  },
  
  // 显示/隐藏可用日期列表
  toggleAvailableDates() {
    this.setData({
      showAvailableDates: !this.data.showAvailableDates
    });
  }
}); 