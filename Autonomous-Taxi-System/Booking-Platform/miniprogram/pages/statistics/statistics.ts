import { getUserStatisticsAPI, getUserOrderTrendAPI, getUserSpendingAnalysisAPI, getUserTravelHabitsAPI, checkLoginStatus } from '../../utils/db'; // 导入API函数

// 获取应用实例
const appInstance = getApp<IAppOption>()

// 定义数据接口
interface OrderAnalysis {
  statusStats: Array<{
    status: string;
    count: number;
    percentage: string;
  }>;
  trendData: Array<{
    date: string;
    count: number;
  }>;
  totalOrders: number;
  avgDaily: string;
  maxDaily: number;
}

interface SpendingAnalysis {
  avgOrderAmount: string;
  maxOrderAmount: string;
  minOrderAmount: string;
  totalAmount: string;
  trendData: Array<{
    date: string;
    amount: number;
  }>;
  paymentMethods: Array<{
    method: string;
    count: number;
    percentage: string;
  }>;
}

interface TravelHabits {
  peakHour: string;
  avgDistance: string;
  favoriteCity: string;
  totalTrips: number;
  timeDistribution: Array<{
    hour: number;
    count: number;
  }>;
  cityDistribution: Array<{
    city: string;
    count: number;
    percentage: string;
  }>;
}

// 订单状态项接口
interface OrderStatusItem {
  status: string;
  count: number;
  percentage: string;
}

Page({
  data: {
    currentTab: 0,
    loading: false,
    isEmpty: false,
    orderAnalysis: {} as OrderAnalysis,
    spendingAnalysis: {} as SpendingAnalysis,
    travelHabits: {} as TravelHabits
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
    
    this.loadStatisticsData();
  },
  
  onShow() {
    // 页面显示时刷新数据
    this.loadStatisticsData();
  },
  
  // 加载统计数据
  async loadStatisticsData() {
    this.setData({ loading: true });
    
    try {
      // 根据当前标签页加载对应数据
      switch (this.data.currentTab) {
        case 0:
          await this.loadOrderAnalysis();
          break;
        case 1:
          await this.loadSpendingAnalysis();
          break;
        case 2:
          await this.loadTravelHabits();
          break;
      }
    } catch (error) {
      console.error('加载统计数据失败:', error);
      wx.showToast({
        title: typeof error === 'string' ? error : '加载数据失败',
        icon: 'none'
      });
      this.setData({ isEmpty: true });
    } finally {
      this.setData({ loading: false });
    }
  },
  
  // 加载订单分析数据
  async loadOrderAnalysis() {
    try {
      const trendResult = await getUserOrderTrendAPI({ period: 'month', limit: 30 });
      const statsResult = await getUserStatisticsAPI();
      
      let orderAnalysis = {
        statusStats: statsResult.orderStatusStats || [],
        trendData: trendResult.trendData || [],
        totalOrders: 0,
        avgDaily: '0.0',
        maxDaily: 0
      };
      
      if (!orderAnalysis.statusStats.length || !orderAnalysis.trendData.length) {
        this.setData({ isEmpty: true });
        return;
      }
      
      // 计算总订单数：已结束 + 进行中 + 待分配
      const completedCount = orderAnalysis.statusStats.find((item: OrderStatusItem) => item.status === '已结束')?.count || 0;
      const inProgressCount = orderAnalysis.statusStats.find((item: OrderStatusItem) => item.status === '进行中')?.count || 0;
      const pendingCount = orderAnalysis.statusStats.find((item: OrderStatusItem) => item.status === '待分配')?.count || 0;
      
      const totalOrders = completedCount + inProgressCount + pendingCount;
      
      // 计算日均和最高
      const avgDaily = orderAnalysis.trendData.length > 0 ? (totalOrders / orderAnalysis.trendData.length).toFixed(1) : '0.0';
      const maxDaily = Math.max(...orderAnalysis.trendData.map((item: {count: number}) => item.count));
      
      orderAnalysis.totalOrders = totalOrders;
      orderAnalysis.avgDaily = avgDaily;
      orderAnalysis.maxDaily = maxDaily;
      
      this.setData({
        orderAnalysis,
        isEmpty: false
      });
    } catch (error) {
      console.error('获取订单分析数据失败:', error);
      this.setData({ isEmpty: true });
    }
  },
  
  // 加载消费分析数据
  async loadSpendingAnalysis() {
    try {
      const result = await getUserSpendingAnalysisAPI({ period: 'month' });
      
      let spendingAnalysis = result;
      
      if (!spendingAnalysis.trendData || !spendingAnalysis.trendData.length || !spendingAnalysis.paymentMethods || !spendingAnalysis.paymentMethods.length) {
        this.setData({ isEmpty: true });
        return;
      }
      
      // 计算总消费金额
      const totalAmount = spendingAnalysis.trendData.reduce((sum: number, item: {amount: number}) => sum + item.amount, 0).toFixed(2);
      spendingAnalysis.totalAmount = totalAmount;
      
      this.setData({
        spendingAnalysis,
        isEmpty: false
      });
    } catch (error) {
      console.error('获取消费分析数据失败:', error);
      this.setData({ isEmpty: true });
    }
  },
  
  // 加载出行习惯数据
  async loadTravelHabits() {
    try {
      const statsResult = await getUserStatisticsAPI();
      
      // 首先检查是否有已结束订单
      if (!statsResult.orderStatusStats || !statsResult.orderStatusStats.length) {
        this.setData({ isEmpty: true });
        return;
      }
      
      const completedOrderCount = statsResult.orderStatusStats.find((item: OrderStatusItem) => item.status === '已结束')?.count || 0;
      
      // 如果没有已结束订单，显示空状态
      if (completedOrderCount === 0) {
        this.setData({ isEmpty: true });
        return;
      }
      
      // 获取基于已结束订单的出行习惯数据
      const result = await getUserTravelHabitsAPI({ status: '已结束' });
      
      let travelHabits = result;
      
      if (!travelHabits.timeDistribution || !travelHabits.timeDistribution.length || 
          !travelHabits.cityDistribution || !travelHabits.cityDistribution.length) {
        this.setData({ isEmpty: true });
        return;
      }
      
      // 直接使用订单状态分布中的已结束订单数作为总出行次数
      travelHabits.totalTrips = completedOrderCount;
      
      this.setData({
        travelHabits,
        isEmpty: false
      });
    } catch (error) {
      console.error('获取出行习惯数据失败:', error);
      this.setData({ isEmpty: true });
    }
  },
  
  // 切换标签
  switchTab(e: any) {
    const index = parseInt(e.currentTarget.dataset.index);
    if (index === this.data.currentTab) return;
    
    this.setData({ currentTab: index });
    this.loadStatisticsData();
  },
  
  // 下拉刷新
  onPullDownRefresh() {
    this.loadStatisticsData();
    wx.stopPullDownRefresh();
  }
}) 