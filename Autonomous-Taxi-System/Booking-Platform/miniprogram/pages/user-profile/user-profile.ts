// 获取应用实例
import { getUserInfo, fetchUserDetailInfo, getMockUserDetailInfo, getCreditLevelRulesAPI } from '../../utils/db';

const appInstance = getApp<IAppOption>()

// 定义用户信息接口
interface UserInfo {
  user_id?: number;
  username?: string;
  real_name?: string;
  phone?: string;
  email?: string;
  gender?: string;
  birth_date?: string;
  credit_score?: number;
  balance?: number;
  registration_time?: string;
  last_login_time?: string;
  registration_city?: string;
  registration_channel?: string;
  tags?: string;
  total_orders?: number;
  coupon_count?: number;
  [key: string]: any;
}

// 定义信用等级规则接口
interface CreditLevelRule {
  level_id: number;
  level_name: string;
  min_score: number;
  max_score: number;
  benefits?: string;
  limitations?: string;
  icon_url?: string;
}

Page({
  data: {
    userInfo: {} as UserInfo,
    tagsArray: [] as string[],
    isLoading: true,
    creditLevel: '' as string, // 用户信用等级
    creditLevelRules: [] as CreditLevelRule[] // 信用等级规则
  },
  onLoad() {
    this.loadCreditLevelRules();
    this.loadUserInfo();
  },
  onShow() {
    // 每次打开页面重新获取用户信息
    this.loadUserInfo();
  },
  
  // 加载信用等级规则
  async loadCreditLevelRules() {
    try {
      // 从API获取信用等级规则
      const rules = await getCreditLevelRulesAPI();
      console.log('获取到的信用等级规则:', rules);
      
      this.setData({
        creditLevelRules: rules
      });
    } catch (error) {
      console.error('获取信用等级规则失败:', error);
      
      // 如果API调用失败，使用默认规则（基于数据库结构）
      const defaultRules: CreditLevelRule[] = [
        { level_id: 1, level_name: '极低信用', min_score: 0, max_score: 30 },
        { level_id: 2, level_name: '低信用', min_score: 31, max_score: 60 },
        { level_id: 3, level_name: '一般信用', min_score: 61, max_score: 90 },
        { level_id: 4, level_name: '良好信用', min_score: 91, max_score: 120 },
        { level_id: 5, level_name: '优秀信用', min_score: 121, max_score: 999 }
      ];
      
      this.setData({
        creditLevelRules: defaultRules
      });
    }
  },
  
  // 根据信用分获取对应的等级名称
  getCreditLevelName(creditScore: number): string {
    const rules = this.data.creditLevelRules;
    for (const rule of rules) {
      if (creditScore >= rule.min_score && creditScore <= rule.max_score) {
        return rule.level_name;
      }
    }
    return '未知等级';
  },
  
  // 根据信用分获取对应的样式类名
  getCreditLevelClass(creditScore: number): string {
    const rules = this.data.creditLevelRules;
    for (const rule of rules) {
      if (creditScore >= rule.min_score && creditScore <= rule.max_score) {
        switch (rule.level_name) {
          case '极低信用':
            return 'badge-danger';
          case '低信用':
            return 'badge-warning';
          case '一般信用':
            return 'badge';
          case '良好信用':
            return 'badge';
          case '优秀信用':
            return 'badge';
          default:
            return 'badge';
        }
      }
    }
    return 'badge';
  },
  
  // 加载用户信息
  loadUserInfo() {
    this.setData({
      isLoading: true
    });
    
    // 先尝试从服务器获取最新的用户详细信息
    fetchUserDetailInfo()
      .then((userDetail: any) => {
        console.log('成功获取用户详细信息:', userDetail);
        this.processUserInfo(userDetail);
      })
      .catch((error) => {
        console.error('获取用户详细信息失败:', error);
        
        // 从全局变量获取基本用户信息
        const baseUserInfo = getUserInfo();
        if (baseUserInfo) {
          console.log('使用全局用户信息:', baseUserInfo);
          this.processUserInfo(baseUserInfo as unknown as UserInfo);
        } else {
          // 使用模拟数据（仅开发测试时使用）
          console.log('使用模拟用户数据');
          const mockUserInfo = getMockUserDetailInfo();
          this.processUserInfo(mockUserInfo);
          
          // 提示用户正在使用模拟数据
          wx.showToast({
            title: '正在使用模拟数据',
            icon: 'none',
            duration: 2000
          });
        }
      })
      .finally(() => {
        this.setData({
          isLoading: false
        });
      });
  },
  
  // 处理用户信息
  processUserInfo(userInfo: UserInfo) {
    // 处理用户标签，转换为数组
    let tagsArray: string[] = [];
    if (userInfo.tags) {
      tagsArray = userInfo.tags.split(',').map((tag: string) => tag.trim());
    }
    
    // 获取信用等级
    const creditScore = userInfo.credit_score || 100;
    const creditLevel = this.getCreditLevelName(creditScore);
    
    // 更新页面数据
    this.setData({
      userInfo,
      tagsArray,
      creditLevel
    });
  },
  
  // 刷新用户信息
  refreshUserInfo() {
    wx.showLoading({
      title: '刷新中...'
    });
    
    this.loadUserInfo();
    
    setTimeout(() => {
      wx.hideLoading();
    }, 1000);
  },
  
  // 编辑个人资料
  handleEditProfile() {
    wx.navigateTo({
      url: '/pages/edit-profile/edit-profile'
    });
  },
  
  // 跳转到修改密码页面
  goToChangePwd() {
    wx.navigateTo({
      url: '/pages/change-password/change-password'
    });
  },
  
  // 退出登录
  handleLogout() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          // 清除全局变量
          appInstance.globalData.token = '';
          appInstance.globalData.userInfo = null;
          
          // 清除本地存储
          wx.removeStorageSync('token');
          wx.removeStorageSync('userInfo');
          
          // 跳转到登录页
          wx.reLaunch({
            url: '/pages/login/login'
          });
        }
      }
    });
  }
}) 