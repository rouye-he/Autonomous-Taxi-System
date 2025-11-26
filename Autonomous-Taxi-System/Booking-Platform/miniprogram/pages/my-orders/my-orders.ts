import { getUserOrdersAPI, checkLoginStatus, reportIssueAPI, cancelOrderAPI } from '../../utils/db'; // 导入API函数

// 获取应用实例
const appInstance = getApp<IAppOption>()

// 定义订单接口
interface OrderItem {
  order_id: number;
  order_number: string;
  status: string;
  create_time: string;
  arrival_time: string;
  pickup_location: string;
  pickup_location_x: number;  // 起点系统坐标X
  pickup_location_y: number;  // 起点系统坐标Y
  dropoff_location: string;
  dropoff_location_x: number;  // 终点系统坐标X
  dropoff_location_y: number;  // 终点系统坐标Y
  city_code: string;
  vehicle_id?: number;
  amount: number;
  distance: number;
  payment_method: string;
}

Page({
  data: {
    currentTab: 0,
    orders: [] as OrderItem[],
    loading: false,
    hasMore: true,
    page: 1,
    statusMap: ['all', '待分配', '进行中', '已结束', '已取消'], // 对应tab索引的状态
    orderStats: {
      all: 0,
      pending: 0,
      ongoing: 0,
      completed: 0,
      cancelled: 0
    }
  },
  
  onLoad() {
    // 检查登录状态
    if (!checkLoginStatus()) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      });
      setTimeout(() => {
        wx.navigateTo({
          url: '/pages/login/login'
        });
      }, 1500);
      return;
    }
    
    this.fetchOrderStats();
    this.fetchOrders();
  },
  
  onShow() {
    // 页面显示时刷新数据
    this.refreshOrders();
  },
  
  // 获取订单统计数据
  async fetchOrderStats() {
    try {
      const allOrdersResult = await getUserOrdersAPI({
        page: 1,
        per_page: 1000
      });
      
      const allOrders = allOrdersResult.orders || [];
      const stats = {
        all: allOrders.length,
        pending: 0,
        ongoing: 0,
        completed: 0,
        cancelled: 0
      };
      
      allOrders.forEach((order: OrderItem) => {
        switch(order.status) {
          case '待分配':
            stats.pending++;
            break;
          case '进行中':
            stats.ongoing++;
            break;
          case '已结束':
            stats.completed++;
            break;
          case '已取消':
            stats.cancelled++;
            break;
        }
      });
      
      this.setData({ orderStats: stats });
      console.log('订单统计:', stats);
    } catch (error) {
      console.error('获取订单统计失败:', error);
    }
  },
  
  // 获取订单数据
  async fetchOrders(loadMore = false) {
    if (this.data.loading) return;
    
    this.setData({ loading: true });
    
    try {
      const currentStatus = this.data.statusMap[this.data.currentTab];
      const page = loadMore ? this.data.page + 1 : 1;
      
      const result = await getUserOrdersAPI({
        status: currentStatus === 'all' ? undefined : currentStatus,
        page,
        per_page: 10
      });
      
      const newOrders = result.orders || [];
      
      /* 调试：打印原始订单数据 */
      console.log('原始订单数据:', newOrders);
      if (newOrders.length > 0) {
        console.log('第一个订单的地址数据:', {
          pickup_location: newOrders[0].pickup_location,
          dropoff_location: newOrders[0].dropoff_location
        });
      }
      
      // 处理订单数据，格式化地址显示
      const processedOrders = newOrders.map((order: OrderItem) => {
        // 不再格式化地址，直接使用原始数据，让WXML显示系统坐标
        return {
          ...order
        };
      });
      
      this.setData({
        orders: loadMore ? [...this.data.orders, ...processedOrders] : processedOrders,
        hasMore: result.has_more || false,
        page,
        loading: false
      });
      
      console.log(`获取订单成功，当前页：${page}，订单数：${newOrders.length}`);
    } catch (error) {
      console.error('获取订单失败:', error);
      this.setData({ loading: false });
      wx.showToast({
        title: typeof error === 'string' ? error : '获取订单失败',
        icon: 'none'
      });
    }
  },
  
  // 刷新订单
  refreshOrders() {
    this.setData({
      orders: [],
      page: 1,
      hasMore: true
    });
    this.fetchOrderStats();
    this.fetchOrders();
  },
  
  // 切换标签
  switchTab(e: any) {
    const index = parseInt(e.currentTarget.dataset.index);
    if (index === this.data.currentTab) return;
    
    this.setData({
      currentTab: index,
      orders: [],
      page: 1,
      hasMore: true
    });
    
    this.fetchOrders();
  },
  
  // 下拉刷新
  onPullDownRefresh() {
    this.refreshOrders();
    wx.stopPullDownRefresh();
  },
  
  // 上拉加载更多
  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.fetchOrders(true);
    }
  },
  
  // 格式化地址显示
  formatAddress(location: string): string {
    /* 调试：打印输入的地址数据 */
    console.log('formatAddress输入:', location, '类型:', typeof location);
    
    if (!location || location === null || location === undefined) {
      console.log('地址为空，返回未知地址');
      return '未知地址';
    }
    
    // 转换为字符串
    const locationStr = String(location).trim();
    
    if (locationStr === '' || locationStr === 'null' || locationStr === 'undefined') {
      console.log('地址字符串为空或无效，返回未知地址');
      return '未知地址';
    }
    
    // 检查是否为纯坐标格式 (x, y)
    const coordMatch = locationStr.match(/^\((\d+),\s*(\d+)\)$/);
    if (coordMatch) {
      const x = coordMatch[1];
      const y = coordMatch[2];
      console.log('检测到纯坐标格式:', x, y);
      return `坐标位置 (${x}, ${y})`;
    }
    
    // 移除坐标格式，只显示地址文本
    // 匹配格式如：(123.456,78.901) 地址文本
    const result = locationStr.replace(/^\([^)]+\)\s*/, '').trim();
    
    /* 调试：打印格式化结果 */
    console.log('地址格式化结果:', result);
    
    // 如果移除坐标后没有文本，返回坐标信息
    if (!result) {
      const coordMatch2 = locationStr.match(/^\(([^)]+)\)/);
      if (coordMatch2) {
        return `坐标位置 ${coordMatch2[1]}`;
      }
    }
    
    return result || '未知地址';
  },
  
  // 格式化时间
  formatTime(timeStr: string): string {
    return timeStr ? timeStr.split(' ')[0] : '';
  },
  
  // 获取标签页名称
  getTabName(index: number): string {
    const tabNames = ['', '待分配', '进行中', '已结束', '已取消'];
    return tabNames[index] || '';
  },
  
  // 订单操作按钮事件
  onOrderAction(e: any) {
    const { action, orderNumber } = e.currentTarget.dataset;
    
    switch (action) {
      case 'cancel':
        this.cancelOrder(orderNumber);
        break;
      case 'report':
        this.reportIssue(orderNumber);
        break;
      case 'evaluate':
        this.goToEvaluation(orderNumber);
        break;
    }
  },
  
  // 取消订单
  cancelOrder(orderNumber: string) {
    wx.showModal({
      title: '确认取消',
      content: '确定要取消这个订单吗？',
      success: (res) => {
        if (res.confirm) {
          this.submitCancelOrder(orderNumber);
        }
      }
    });
  },
  
  // 提交取消订单
  async submitCancelOrder(orderNumber: string) {
    try {
      wx.showLoading({
        title: '取消中...',
        mask: true
      });
      
      const result = await cancelOrderAPI({
        order_number: orderNumber,
        cancel_reason: '用户主动取消'
      });
      
      wx.hideLoading();
      
      wx.showToast({
        title: '订单已取消',
        icon: 'success'
      });
      
      // 刷新订单列表
      this.refreshOrders();
      
      console.log('订单取消成功:', result);
    } catch (error) {
      wx.hideLoading();
      console.error('取消订单失败:', error);
      
      wx.showToast({
        title: typeof error === 'string' ? error : '取消订单失败',
        icon: 'none'
      });
    }
  },
  
  // 上报异常
  reportIssue(orderNumber: string) {
    wx.showActionSheet({
      itemList: ['车辆故障', '路线异常', '安全问题', '其他异常'],
      success: (res) => {
        const issueTypes = ['车辆故障', '路线异常', '安全问题', '其他异常'];
        const selectedIssue = issueTypes[res.tapIndex];
        
        // 显示输入框让用户编辑异常描述
        wx.showModal({
          title: '异常描述',
          editable: true,
          placeholderText: `请描述${selectedIssue}的具体情况...`,
          success: (modalRes) => {
            if (modalRes.confirm) {
              const userDescription = modalRes.content?.trim() || '';
              
              // 确认上报
              wx.showModal({
                title: '确认上报',
                content: `异常类型：${selectedIssue}\n描述：${userDescription || '无详细描述'}\n\n确认上报此异常？我们会立即通知管理员处理。`,
                confirmText: '确认上报',
                success: (confirmRes) => {
                  if (confirmRes.confirm) {
                    this.submitIssueReport(orderNumber, selectedIssue, userDescription);
                  }
                }
              });
            }
          }
        });
      }
    });
  },
  
  // 提交异常上报
  async submitIssueReport(orderNumber: string, issueType: string, userDescription: string = '') {
    try {
      wx.showLoading({
        title: '上报中...',
        mask: true
      });
      
      const description = userDescription || `用户通过小程序上报${issueType}异常`;
      
      const result = await reportIssueAPI({
        order_number: orderNumber,
        issue_type: issueType,
        description: description
      });
      
      wx.hideLoading();
      
      wx.showModal({
        title: '上报成功',
        content: '异常已成功上报给管理员，我们会尽快处理。请注意安全，如有紧急情况请立即联系客服。',
        showCancel: false,
        confirmText: '知道了'
      });
      
      console.log('异常上报成功:', result);
    } catch (error) {
      wx.hideLoading();
      console.error('异常上报失败:', error);
      
      wx.showModal({
        title: '上报失败',
        content: typeof error === 'string' ? error : '上报异常失败，请稍后重试',
        showCancel: false,
        confirmText: '知道了'
      });
    }
  },
  
  // 跳转到评价页面
  goToEvaluation(orderNumber: string) {
    wx.navigateTo({
      url: `/pages/evaluation/evaluation?orderNumber=${orderNumber}`
    });
  }
}) 