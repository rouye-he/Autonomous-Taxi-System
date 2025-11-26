import { checkLoginStatus, fetchUserDetailInfo, getWalletTransactionsAPI, rechargeWalletAPI, withdrawWalletAPI } from '../../utils/db'; /* 导入API函数 */

/* 获取应用实例 */
const appInstance = getApp<IAppOption>()

/* 定义交易记录接口 */
interface TransactionItem {
  id: number;
  amount: number;
  amount_type: 'income' | 'expense';
  type: string;
  date: string;
  description?: string;
  order_id?: string;
  user_id?: number;
  distance?: number; // 行程距离
  payment_method?: string; // 支付方式
  pickup_coords?: string; // 起点坐标
  dropoff_coords?: string; // 终点坐标
  created_at?: string; // 创建时间
  original_price?: number; // 原价
  final_price?: number; // 实付价格
  coupon_info?: string; // 优惠券信息
}

Page({
  data: {
    currentTab: 2, /* 默认显示全部记录 */
    transactions: [] as TransactionItem[],
    loading: false,
    hasMore: true,
    page: 1,
    userBalance: 0,
    transactionStats: {
      income: 0,
      expense: 0,
      total: 0
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
    
    this.fetchUserBalance();
    this.fetchTransactionStats();
    this.fetchTransactions();
  },
  
  onShow() {
    /* 页面显示时刷新数据 */
    this.refreshData();
  },
  
  /* 获取用户余额 */
  async fetchUserBalance() {
    try {
      const userInfo = await fetchUserDetailInfo();
      this.setData({
        userBalance: userInfo.balance || 0
      });
    } catch (error) {
      console.error('获取用户余额失败:', error);
    }
  },
  
  /* 获取交易统计数据 */
  async fetchTransactionStats() {
    try {
      const result = await getWalletTransactionsAPI({
        page: 1,
        per_page: 1,
        type: 'stats'
      });
      
      const stats = result.stats || {
        income_count: 0,
        expense_count: 0,
        total_count: 0
      };
      
      this.setData({ 
        transactionStats: {
          income: stats.income_count,
          expense: stats.expense_count,
          total: stats.total_count
        }
      });
      console.log('交易统计:', stats);
    } catch (error) {
      console.error('获取交易统计失败:', error);
    }
  },
  
  /* 获取交易记录 */
  async fetchTransactions(loadMore = false) {
    if (this.data.loading) return;
    
    this.setData({ loading: true });
    
    try {
      const currentTab = this.data.currentTab;
      const page = loadMore ? this.data.page + 1 : 1;
      
      /* 根据当前tab确定API类型参数 */
      let apiType = 'all';
      if (currentTab === 0) {
        apiType = 'income';
      } else if (currentTab === 1) {
        apiType = 'expense';
      }
      
      /* 使用钱包交易API获取数据 */
      const result = await getWalletTransactionsAPI({
        page,
        per_page: 10,
        type: apiType
      });
      
      const transactions = result.transactions || [];
      
      /* 处理交易数据，格式化显示 */
      const processedTransactions = transactions.map((transaction: TransactionItem) => {
        return {
          ...transaction,
          amount_type: transaction.amount_type || (transaction.type.includes('收入') ? 'income' : 'expense')
        };
      });
      
      this.setData({
        transactions: loadMore ? [...this.data.transactions, ...processedTransactions] : processedTransactions,
        hasMore: result.pagination?.has_next || false,
        page,
        loading: false
      });
      
      console.log(`获取交易记录成功，当前页：${page}，记录数：${transactions.length}`);
    } catch (error) {
      console.error('获取交易记录失败:', error);
      this.setData({ loading: false });
      wx.showToast({
        title: typeof error === 'string' ? error : '获取交易记录失败',
        icon: 'none'
      });
    }
  },
  
  /* 刷新数据 */
  refreshData() {
    this.setData({
      transactions: [],
      page: 1,
      hasMore: true
    });
    this.fetchUserBalance();
    this.fetchTransactionStats();
    this.fetchTransactions();
  },
  
  /* 切换标签 */
  switchTab(e: any) {
    const index = parseInt(e.currentTarget.dataset.index);
    if (index === this.data.currentTab) return;
    
    this.setData({
      currentTab: index,
      transactions: [],
      page: 1,
      hasMore: true
    });
    
    this.fetchTransactions();
  },
  
  /* 下拉刷新 */
  onPullDownRefresh() {
    this.refreshData();
    wx.stopPullDownRefresh();
  },
  
  /* 上拉加载更多 */
  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.fetchTransactions(true);
    }
  },
  
  /* 格式化时间显示 */
  formatTime(timeStr: string): string {
    if (!timeStr) return '';
    return timeStr.replace(/:\d{2}$/, ''); /* 移除秒数 */
  },
  
  /* 跳转到充值页面 */
  goToRecharge() {
    wx.showModal({
      title: '充值',
      editable: true,
      placeholderText: '请输入金额(10-10000元)',
      success: async (res) => {
        if (res.confirm && res.content) {
          const amount = parseFloat(res.content);
          if (isNaN(amount) || amount <= 0) {
            wx.showToast({
              title: '请输入有效金额',
              icon: 'none'
            });
            return;
          }
          if (amount < 10) {
            wx.showToast({
              title: '充值金额不能少于10元',
              icon: 'none'
            });
            return;
          }
          if (amount > 10000) {
            wx.showToast({
              title: '充值金额不能超过10000元',
              icon: 'none'
            });
            return;
          }
          
          // 选择支付方式
          wx.showActionSheet({
            itemList: ['微信支付', '支付宝', '银行卡'],
            success: async (payRes) => {
              const paymentMethods = ['微信支付', '支付宝', '银行卡'];
              const selectedMethod = paymentMethods[payRes.tapIndex];
              
              wx.showLoading({
                title: '充值中...'
              });
              
              try {
                const result = await rechargeWalletAPI({
                  amount: amount,
                  payment_method: selectedMethod
                });
                
                wx.hideLoading();
                wx.showToast({
                  title: '充值成功',
                  icon: 'success'
                });
                
                // 刷新页面数据
                this.refreshData();
              } catch (error) {
                wx.hideLoading();
                wx.showToast({
                  title: typeof error === 'string' ? error : '充值失败',
                  icon: 'none'
                });
              }
            }
          });
        }
      }
    });
  },
  
  /* 跳转到提现页面 */
  goToWithdraw() {
    wx.showModal({
      title: '提现',
      editable: true,
      placeholderText: '请输入金额(10-5000元)',
      success: async (res) => {
        if (res.confirm && res.content) {
          const amount = parseFloat(res.content);
          if (isNaN(amount) || amount <= 0) {
            wx.showToast({
              title: '请输入有效金额',
              icon: 'none'
            });
            return;
          }
          if (amount < 10) {
            wx.showToast({
              title: '提现金额不能少于10元',
              icon: 'none'
            });
            return;
          }
          if (amount > 5000) {
            wx.showToast({
              title: '提现金额不能超过5000元',
              icon: 'none'
            });
            return;
          }
          if (amount > this.data.userBalance) {
            wx.showToast({
              title: '余额不足',
              icon: 'none'
            });
            return;
          }
          
          // 选择提现方式
          wx.showActionSheet({
            itemList: ['银行卡', '支付宝', '微信'],
            success: async (withdrawRes) => {
              const withdrawMethods = ['银行卡', '支付宝', '微信'];
              const selectedMethod = withdrawMethods[withdrawRes.tapIndex];
              
              wx.showLoading({
                title: '提现中...'
              });
              
              try {
                const result = await withdrawWalletAPI({
                  amount: amount,
                  withdraw_method: selectedMethod
                });
                
                wx.hideLoading();
                wx.showToast({
                  title: '提现申请已提交',
                  icon: 'success'
                });
                
                // 刷新页面数据
                this.refreshData();
              } catch (error) {
                wx.hideLoading();
                wx.showToast({
                  title: typeof error === 'string' ? error : '提现失败',
                  icon: 'none'
                });
              }
            }
          });
        }
      }
    });
  }
}) 