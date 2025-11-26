import { fetchUserDetailInfo } from '../../utils/db';
import { request } from '../../utils/util';
import { notify } from '../../utils/notification';

interface CreditLevel {
  level_id: number;
  level_name: string;
  min_score: number;
  max_score: number;
  benefits: string;
  limitations: string;
  icon_url: string;
}

interface CreditRule {
  rule_id: number;
  rule_name: string;
  rule_type: string;
  trigger_event: string;
  score_change: number;
  description: string;
  is_active: boolean;
}

interface CreditLog {
  log_id: number;
  change_type: string;
  reason: string;
  change_amount: number;
  credit_before: number;
  credit_after: number;
  operator: string;
  created_at: string;
}

Page({
  data: {
    creditScore: 0,
    creditLevel: {
      level_id: 0,
      level_name: '',
      min_score: 0,
      max_score: 0,
      benefits: '',
      limitations: '',
      icon_url: ''
    },
    activeTab: 0,
    allLevels: [] as CreditLevel[], // 所有信用等级
    rules: [] as CreditRule[],
    logs: [] as CreditLog[],
    loading: false,
    hasMore: false,
    page: 1,
    per_page: 20
  },

  onLoad() {
    console.log('页面加载，初始数据状态:', {
      activeTab: this.data.activeTab,
      allLevels: this.data.allLevels.length,
      rules: this.data.rules.length,
      logs: this.data.logs.length
    });
    this.loadCreditInfo();
  },

  onPullDownRefresh() {
    this.setData({ page: 1 });
    this.loadCreditInfo();
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading && this.data.activeTab === 2) {
      this.loadMoreLogs();
    }
  },

  // 格式化时间 - 模仿钱包页面
  formatTime(dateStr: string): string {
    if (!dateStr) return '';
    
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diff = now.getTime() - date.getTime();
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      
      if (days === 0) {
        return '今天';
      } else if (days === 1) {
        return '昨天';
      } else if (days < 7) {
        return `${days}天前`;
      } else {
        return date.toLocaleDateString('zh-CN', {
          month: '2-digit',
          day: '2-digit'
        });
      }
    } catch (error) {
      return dateStr.split(' ')[0] || '';
    }
  },

  // 加载信用信息
  async loadCreditInfo() {
    try {
      this.setData({ loading: true });
      
      console.log('开始加载信用信息...');
      
      // 获取用户详细信息（包含信用分）
      const userInfo = await fetchUserDetailInfo();
      const creditScore = userInfo.credit_score || 100;
      console.log('用户信用分:', creditScore);
      
      // 获取所有信用等级
      const allLevels = await this.getAllCreditLevels();
      console.log('信用等级数量:', allLevels.length);
      
      // 根据信用分确定当前信用等级
      const creditLevel = this.getCurrentCreditLevel(creditScore, allLevels);
      console.log('当前信用等级:', creditLevel.level_name);
      
      // 获取信用规则和记录
      const [rules, logs] = await Promise.all([
        this.getCreditRules(),
        this.getCreditLogs(userInfo.user_id, 1)
      ]);
      
      console.log('信用规则数量:', rules.length);
      console.log('信用记录数量:', logs.data ? logs.data.length : 0);

      this.setData({
        creditScore,
        creditLevel,
        allLevels,
        rules,
        logs: logs.data || [],
        hasMore: logs.pagination ? logs.pagination.has_next : false,
        page: 1
      });
      
      console.log('数据设置完成');
      console.log('页面数据状态:', {
        creditScore: this.data.creditScore,
        creditLevel: this.data.creditLevel,
        allLevels: this.data.allLevels.length,
        rules: this.data.rules.length,
        logs: this.data.logs.length,
        activeTab: this.data.activeTab,
        loading: this.data.loading
      });
    } catch (error) {
      console.error('加载信用信息失败:', error);
      notify.error('加载失败，请重试');
      
      // 即使出错也要设置默认数据
      const defaultLevels = this.getDefaultLevels();
      this.setData({
        creditScore: 100,
        creditLevel: defaultLevels[2], // 默认一般信用
        allLevels: defaultLevels,
        rules: this.getDefaultRules(),
        logs: [],
        hasMore: false,
        page: 1
      });
    } finally {
      this.setData({ loading: false });
      wx.stopPullDownRefresh();
    }
  },

  // 加载更多记录
  async loadMoreLogs() {
    if (this.data.loading || !this.data.hasMore) return;
    
    try {
      this.setData({ loading: true });
      
      const userInfo = await fetchUserDetailInfo();
      const nextPage = this.data.page + 1;
      const moreLogsRes = await this.getCreditLogs(userInfo.user_id, nextPage);
      
      this.setData({
        logs: [...this.data.logs, ...(moreLogsRes.data || [])],
        hasMore: moreLogsRes.pagination ? moreLogsRes.pagination.has_next : false,
        page: nextPage
      });
    } catch (error) {
      notify.error('加载更多失败');
      console.error('加载更多记录失败:', error);
    } finally {
      this.setData({ loading: false });
    }
  },

  // 获取默认等级数据
  getDefaultLevels(): CreditLevel[] {
    return [
      {
        level_id: 1,
        level_name: '极低信用',
        min_score: 0,
        max_score: 30,
        benefits: '无特殊权益',
        limitations: '1. 需支付额外押金\n2. 限制预约功能\n3. 无法使用高峰期服务\n4. 部分车型不可用',
        icon_url: ''
      },
      {
        level_id: 2,
        level_name: '低信用',
        min_score: 31,
        max_score: 60,
        benefits: '基础服务访问',
        limitations: '1. 高峰期限制预约\n2. 无优惠折扣\n3. 需要较长预约提前期',
        icon_url: ''
      },
      {
        level_id: 3,
        level_name: '一般信用',
        min_score: 61,
        max_score: 90,
        benefits: '1. 正常使用全部基础功能\n2. 可享受基础会员价格',
        limitations: '无特殊限制',
        icon_url: ''
      },
      {
        level_id: 4,
        level_name: '良好信用',
        min_score: 91,
        max_score: 120,
        benefits: '1. 享受会员折扣\n2. 优先客服支持\n3. 免押金服务',
        limitations: '无特殊限制',
        icon_url: ''
      },
      {
        level_id: 5,
        level_name: '优秀信用',
        min_score: 121,
        max_score: 200,
        benefits: '1. 享受最高折扣\n2. VIP客服通道\n3. 免押金服务\n4. 优先派单权限\n5. 积分奖励翻倍',
        limitations: '无使用限制',
        icon_url: ''
      }
    ];
  },

  // 获取默认规则数据
  getDefaultRules(): CreditRule[] {
    return [
      {
        rule_id: 1,
        rule_name: '完成订单',
        rule_type: '奖励',
        trigger_event: '订单正常完成',
        score_change: 1,
        description: '用户按时完成订单，无任何异常行为',
        is_active: true
      },
      {
        rule_id: 2,
        rule_name: '取消订单',
        rule_type: '惩罚',
        trigger_event: '用户主动取消订单',
        score_change: -2,
        description: '用户在订单确认后主动取消，影响系统调度',
        is_active: true
      },
      {
        rule_id: 3,
        rule_name: '违规行为',
        rule_type: '惩罚',
        trigger_event: '用户存在违规行为',
        score_change: -10,
        description: '用户存在恶意行为或违反平台规定',
        is_active: true
      }
    ];
  },

  // 获取所有信用等级
  async getAllCreditLevels(): Promise<CreditLevel[]> {
    try {
      const app = getApp<IAppOption>();
      const token = app.globalData.token;
      
      console.log('请求信用等级API...');
      console.log('Token:', token);
      
      const res = await request({
        url: '/api/credit/levels',
        method: 'GET',
        header: {
          'Authorization': `Bearer ${token}`
        },
        showLoading: false,
        showError: false // 手动处理错误
      });
      
      console.log('信用等级API响应:', res);
      
      if (res.code === 0 && res.data) {
        return res.data;
      } else {
        console.warn('信用等级API返回错误:', res);
        return this.getDefaultLevels();
      }
    } catch (error) {
      console.error('获取信用等级失败:', error);
      // 返回默认等级数据
      return this.getDefaultLevels();
    }
  },

  // 根据信用分获取当前信用等级
  getCurrentCreditLevel(score: number, allLevels: CreditLevel[]): CreditLevel {
    for (const level of allLevels) {
      if (score >= level.min_score && score <= level.max_score) {
        return level;
      }
    }
    // 如果没有匹配的等级，返回第一个等级
    return allLevels[0] || {
      level_id: 1,
      level_name: '未知等级',
      min_score: 0,
      max_score: 100,
      benefits: '',
      limitations: '',
      icon_url: ''
    };
  },

  // 获取信用规则
  async getCreditRules(): Promise<CreditRule[]> {
    try {
      const app = getApp<IAppOption>();
      const token = app.globalData.token;
      
      console.log('请求信用规则API...');
      console.log('Token:', token);
      
      const res = await request({
        url: '/api/credit/rules',
        method: 'GET',
        header: {
          'Authorization': `Bearer ${token}`
        },
        showLoading: false,
        showError: false // 手动处理错误
      });
      
      console.log('信用规则API响应:', res);
      
      if (res.code === 0 && res.data) {
        return res.data;
      } else {
        console.warn('信用规则API返回错误:', res);
        return this.getDefaultRules();
      }
    } catch (error) {
      console.error('获取信用规则失败:', error);
      return this.getDefaultRules();
    }
  },

  // 获取信用记录
  async getCreditLogs(userId: number, page: number = 1): Promise<any> {
    try {
      const app = getApp<IAppOption>();
      const token = app.globalData.token;
      
      console.log('请求信用记录API...', { userId, page });
      console.log('Token:', token);
      
      const res = await request({
        url: `/api/credit/logs?page=${page}&per_page=${this.data.per_page}`,
        method: 'GET',
        header: {
          'Authorization': `Bearer ${token}`
        },
        showLoading: false,
        showError: false // 手动处理错误
      });
      
      console.log('信用记录API响应:', res);
      
      if (res.code === 0) {
        return {
          data: res.data || [],
          pagination: res.pagination || null
        };
      } else {
        console.warn('信用记录API返回错误:', res);
        return { data: [], pagination: null };
      }
    } catch (error) {
      console.error('获取信用记录失败:', error);
      return { data: [], pagination: null };
    }
  },

  // 切换标签页
  onTabChange(e: any) {
    const index = parseInt(e.currentTarget.dataset.index);
    console.log('切换标签页:', index, '当前activeTab:', this.data.activeTab);
    this.setData({ activeTab: index });
    console.log('标签页切换完成，新的activeTab:', this.data.activeTab);
    
    // 如果切换到记录页面且没有数据，重新加载
    if (index === 2 && this.data.logs.length === 0) {
      console.log('重新加载信用记录数据');
      this.loadCreditInfo();
    }
  },

  // 返回上一页
  onBack() {
    wx.navigateBack();
  }
}); 