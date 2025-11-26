import { getUserCouponsAPI, checkLoginStatus } from '../../utils/db';

// 获取应用实例
const appInst = getApp<IAppOption>()

Page({
  data: {
    currentTab: 0,
    coupons: [] as any[],
    loading: true,
    allCoupons: [] as any[],
    couponStats: {
      available: 0,
      used: 0,
      expired: 0,
      availableByType: {} as any,
      usedByType: {} as any,
      expiredByType: {} as any
    }
  },
  async onLoad() {
    if (!checkLoginStatus()) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
      return;
    }
    
    await this.fetchCoupons();
  },
  async fetchCoupons() {
    try {
      this.setData({ loading: true });
      
      const result = await getUserCouponsAPI();
      const coupons = result.coupons || [];
      
      this.setData({
        allCoupons: coupons,
        loading: false
      });
      
      this.calculateCouponStats(coupons);
      this.filterCoupons(this.data.currentTab);
      
      console.log('获取优惠券成功:', coupons.length);
    } catch (error) {
      console.error('获取优惠券失败:', error);
      this.setData({ loading: false });
      
      wx.showModal({
        title: '加载失败',
        content: typeof error === 'string' ? error : '获取优惠券失败，请稍后重试',
        showCancel: false,
        confirmText: '知道了'
      });
    }
  },
  calculateCouponStats(coupons: any[]) {
    const stats = {
      available: 0,
      used: 0,
      expired: 0,
      availableByType: {} as any,
      usedByType: {} as any,
      expiredByType: {} as any
    };
    
    /* 按种类和过期时间分组统计 */
    const groupedCoupons = {
      available: {} as any,
      used: {} as any,
      expired: {} as any
    };
    
    coupons.forEach(coupon => {
      const typeName = coupon.type_name || '未知类型';
      const expireDate = coupon.expire_time ? coupon.expire_time.split(' ')[0] : '无期限'; /* 只取日期部分 */
      const groupKey = `${typeName}_${expireDate}`; /* 种类+过期时间作为分组键 */
      
      switch(coupon.status) {
        case '未使用':
          stats.available++;
          if (!groupedCoupons.available[groupKey]) {
            groupedCoupons.available[groupKey] = {
              typeName,
              expireDate,
              count: 0
            };
          }
          groupedCoupons.available[groupKey].count++;
          break;
        case '已使用':
          stats.used++;
          if (!groupedCoupons.used[groupKey]) {
            groupedCoupons.used[groupKey] = {
              typeName,
              expireDate,
              count: 0
            };
          }
          groupedCoupons.used[groupKey].count++;
          break;
        case '已过期':
          stats.expired++;
          if (!groupedCoupons.expired[groupKey]) {
            groupedCoupons.expired[groupKey] = {
              typeName,
              expireDate,
              count: 0
            };
          }
          groupedCoupons.expired[groupKey].count++;
          break;
      }
    });
    
    /* 转换为显示格式 */
    stats.availableByType = Object.values(groupedCoupons.available);
    stats.usedByType = Object.values(groupedCoupons.used);
    stats.expiredByType = Object.values(groupedCoupons.expired);
    
    this.setData({ couponStats: stats });
    console.log('优惠券统计(按种类和过期时间分组):', stats);
  },
  switchTab(e: any) {
    const index = parseInt(e.currentTarget.dataset.index);
    this.setData({
      currentTab: index
    });
    
    this.filterCoupons(index);
  },
  filterCoupons(tabIndex: number) {
    const allCoupons = this.data.allCoupons;
    let filteredCoupons;
    
    switch(tabIndex) {
      case 0:
        filteredCoupons = allCoupons.filter(coupon => coupon.status === '未使用');
        break;
      case 1:
        filteredCoupons = allCoupons.filter(coupon => coupon.status === '已使用');
        break;
      case 2:
        filteredCoupons = allCoupons.filter(coupon => coupon.status === '已过期');
        break;
      default:
        filteredCoupons = allCoupons.filter(coupon => coupon.status === '未使用');
    }
    
    this.setData({
      coupons: filteredCoupons
    });
  },
  useCoupon(e: any) {
    const couponId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: '/pages/index/index'
    });
    wx.showToast({
      title: '已选择优惠券，请下单时使用',
      icon: 'none',
      duration: 2000
    });
  },
  
  goToCouponShop() {
    wx.navigateTo({
      url: '/pages/coupon-shop/coupon-shop'
    });
  },
  
  async onPullDownRefresh() {
    await this.fetchCoupons();
    wx.stopPullDownRefresh();
  }
}) 