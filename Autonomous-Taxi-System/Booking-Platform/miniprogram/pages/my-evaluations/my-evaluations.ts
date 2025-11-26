import { getUserOrdersAPI, checkLoginStatus, submitEvaluationAPI, getUserEvaluationsAPI } from '../../utils/db'; /* 导入API函数 */

/* 获取应用实例 */
const appInstance = getApp<IAppOption>()

/* 定义评价项接口 */
interface EvaluationItem {
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
  rating?: number;
  comment?: string;
  evaluation_time?: string;
}

Page({
  data: {
    currentTab: 0,
    evaluations: [] as EvaluationItem[],
    loading: false,
    hasMore: true,
    page: 1,
    statusMap: ['待评价', '已评价'], /* 对应tab索引的状态 */
    evaluationStats: {
      pending: 0,
      completed: 0
    }
  },
  
  onLoad() {
    /* 检查登录状态 */
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
    
    this.fetchEvaluationStats();
    this.fetchEvaluations();
  },
  
  onShow() {
    /* 页面显示时刷新数据 */
    this.refreshEvaluations();
  },
  
  /* 获取评价统计数据 */
  async fetchEvaluationStats() {
    try {
      // 使用新的评价API获取统计数据
      const result = await getUserEvaluationsAPI({
        page: 1,
        per_page: 1,
        status: 'all'
      });
      
      const stats = result.stats || {
        pending_evaluations: 0,
        total_evaluations: 0
      };
      
      this.setData({ 
        evaluationStats: {
          pending: stats.pending_evaluations,
          completed: stats.total_evaluations
        }
      });
      console.log('评价统计:', stats);
    } catch (error) {
      console.error('获取评价统计失败:', error);
    }
  },
  
  /* 获取评价数据 */
  async fetchEvaluations(loadMore = false) {
    if (this.data.loading) return;
    
    this.setData({ loading: true });
    
    try {
      const currentStatus = this.data.statusMap[this.data.currentTab];
      const page = loadMore ? this.data.page + 1 : 1;
      
      // 根据当前tab确定API状态参数
      let apiStatus = 'all';
      if (currentStatus === '待评价') {
        apiStatus = 'pending';
      } else if (currentStatus === '已评价') {
        apiStatus = 'completed';
      }
      
      // 使用新的评价API获取数据
      const result = await getUserEvaluationsAPI({
        page,
        per_page: 10,
        status: apiStatus
      });
      
      const evaluations = result.evaluations || [];
      
      /* 处理评价数据，不再格式化地址，直接使用原始数据 */
      const processedEvaluations = evaluations.map((evaluation: EvaluationItem) => {
        return {
          ...evaluation
        };
      });
      
      this.setData({
        evaluations: loadMore ? [...this.data.evaluations, ...processedEvaluations] : processedEvaluations,
        hasMore: result.pagination?.has_next || false,
        page,
        loading: false
      });
      
      console.log(`获取评价成功，当前页：${page}，评价数：${evaluations.length}`);
    } catch (error) {
      console.error('获取评价失败:', error);
      this.setData({ loading: false });
      wx.showToast({
        title: typeof error === 'string' ? error : '获取评价失败',
        icon: 'none'
      });
    }
  },
  
  /* 刷新评价 */
  refreshEvaluations() {
    this.setData({
      evaluations: [],
      page: 1,
      hasMore: true
    });
    this.fetchEvaluationStats();
    this.fetchEvaluations();
  },
  
  /* 切换标签 */
  switchTab(e: any) {
    const index = parseInt(e.currentTarget.dataset.index);
    if (index === this.data.currentTab) return;
    
    this.setData({
      currentTab: index,
      evaluations: [],
      page: 1,
      hasMore: true
    });
    
    this.fetchEvaluations();
  },
  
  /* 下拉刷新 */
  onPullDownRefresh() {
    this.refreshEvaluations();
    wx.stopPullDownRefresh();
  },
  
  /* 上拉加载更多 */
  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.fetchEvaluations(true);
    }
  },
  
  /* 格式化地址显示 */
  formatAddress(location: string, cityCode?: string): string {
    if (!location || location === null || location === undefined) {
      return '未知地址';
    }
    
    const locationStr = String(location).trim();
    
    if (locationStr === '' || locationStr === 'null' || locationStr === 'undefined') {
      return '未知地址';
    }
    
    /* 检查是否为纯坐标格式 (x, y) */
    const coordMatch = locationStr.match(/^\((\d+),\s*(\d+)\)$/);
    if (coordMatch) {
      const x = parseInt(coordMatch[1]);
      const y = parseInt(coordMatch[2]);
      const areaInfo = this.getAreaByCoordinates(x, y, cityCode);
      return areaInfo;
    }
    
    /* 移除坐标格式，只显示地址文本 */
    const result = locationStr.replace(/^\([^)]+\)\s*/, '').trim();
    
    /* 如果移除坐标后没有文本，返回坐标信息 */
    if (!result) {
      const coordMatch2 = locationStr.match(/^\(([^)]+)\)/);
      if (coordMatch2) {
        const coords = coordMatch2[1];
        const [x, y] = coords.split(',').map(s => parseInt(s.trim()));
        if (!isNaN(x) && !isNaN(y)) {
          const areaInfo = this.getAreaByCoordinates(x, y, cityCode);
          return areaInfo;
        }
        return `坐标位置 ${coords}`;
      }
    }
    
    return result || '未知地址';
  },
  
  /* 根据坐标和城市获取区域信息 */
  getAreaByCoordinates(x: number, y: number, cityCode?: string): string {
    const city = cityCode || '未知城市';
    
    /* 根据坐标范围判断大致区域 */
    let area = '';
    
    if (x < 200) {
      area = '西部';
    } else if (x < 400) {
      area = '西南部';
    } else if (x < 600) {
      area = '中部';
    } else if (x < 800) {
      area = '东部';
    } else {
      area = '东北部';
    }
    
    if (y < 200) {
      area += '南区';
    } else if (y < 400) {
      area += '中南区';
    } else if (y < 600) {
      area += '中区';
    } else {
      area += '北区';
    }
    
    return `${city}${area} (${x}, ${y})`;
  },
  
  /* 格式化时间显示 */
  formatTime(timeStr: string): string {
    if (!timeStr) return '';
    return timeStr.replace(/:\d{2}$/, ''); /* 移除秒数 */
  },
  
  /* 跳转到评价页面 */
  goToEvaluation(e: any) {
    const orderNumber = e.currentTarget.dataset.orderNumber;
    wx.navigateTo({
      url: `/pages/evaluation/evaluation?orderNumber=${orderNumber}`
    });
  },
  
  /* 查看评价详情 */
  viewEvaluationDetail(e: any) {
    const evaluation = e.currentTarget.dataset.evaluation;
    
    wx.showModal({
      title: '评价详情',
      content: `订单：${evaluation.order_number}\n评分：${evaluation.rating}星\n评价：${evaluation.comment || '无评价内容'}\n评价时间：${this.formatTime(evaluation.evaluation_time || '')}`,
      showCancel: false,
      confirmText: '知道了'
    });
  }
}) 