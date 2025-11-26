import { getCouponPackagesAPI, purchaseCouponPackageAPI, checkLoginStatus, fetchUserDetailInfo } from '../../utils/db';
import { notify } from '../../utils/notification'; // 导入通知管理器

Page({
  data: {
    packages: [] as any[],
    loading: true,
    showPurchaseModal: false,
    selectedPackage: null as any,
    paymentMethod: '余额支付',
    userBalance: 0,
    purchasing: false
  },
  
  async onLoad() {
    // 检查登录状态
    if (!checkLoginStatus()) {
      notify.error('请先登录');
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
      return;
    }
    
    // 获取用户信息和套餐列表
    await this.loadData();
  },
  
  async loadData() {
    try {
      this.setData({ loading: true });
      
      // 并行获取用户信息和套餐列表
      const [userInfo, packagesData] = await Promise.all([
        fetchUserDetailInfo(),
        getCouponPackagesAPI()
      ]);
      
      this.setData({
        packages: packagesData.packages || [],
        userBalance: userInfo.balance || 0,
        loading: false
      });
      
      console.log('加载数据成功:', { packages: packagesData.packages.length, balance: userInfo.balance });
    } catch (error) {
      console.error('加载数据失败:', error);
      this.setData({ loading: false });
      
      wx.showModal({
        title: '加载失败',
        content: typeof error === 'string' ? error : '获取数据失败，请稍后重试',
        showCancel: false,
        confirmText: '知道了'
      });
    }
  },
  
  // 点击套餐卡片
  onPackageClick(e: any) {
    const packageData = e.currentTarget.dataset.package;
    
    this.setData({
      selectedPackage: packageData,
      showPurchaseModal: true,
      paymentMethod: '余额支付' // 默认选择余额支付
    });
  },
  
  // 关闭弹窗
  onModalClose() {
    this.setData({
      showPurchaseModal: false,
      selectedPackage: null,
      purchasing: false
    });
  },
  
  // 阻止事件冒泡
  stopPropagation() {
    // 空函数，用于阻止事件冒泡
  },
  
  // 切换支付方式
  onPaymentMethodChange(e: any) {
    const method = e.currentTarget.dataset.method;
    this.setData({
      paymentMethod: method
    });
  },
  
  // 确认购买
  async onConfirmPurchase() {
    if (this.data.purchasing) return;
    
    const { selectedPackage, paymentMethod, userBalance } = this.data;
    
    if (!selectedPackage) {
      notify.warning('请选择套餐');
      return;
    }
    
    // 检查余额支付时的余额是否足够
    if (paymentMethod === '余额支付' && userBalance < selectedPackage.price) {
      notify.error(`余额不足，当前余额：¥${userBalance}，需要：¥${selectedPackage.price}`);
      return;
    }
    
    try {
      this.setData({ purchasing: true });
      
      notify.loading('购买中...');
      
      const result = await purchaseCouponPackageAPI({
        package_id: selectedPackage.id,
        payment_method: paymentMethod
      });
      
      notify.hideLoading();
      
      // 关闭弹窗
      this.onModalClose();
      
      // 刷新用户余额
      if (paymentMethod === '余额支付') {
        this.setData({
          userBalance: userBalance - selectedPackage.price
        });
      }
      
      // 购买成功提示
      notify.success(`恭喜您成功购买"${result.package_name}"套餐！优惠券已发放到您的账户。`);
      
      // 延迟跳转，让用户看到成功提示
      setTimeout(() => {
        wx.navigateTo({
          url: '/pages/coupons/coupons'
        });
      }, 1500);
      
      console.log('购买成功:', result);
    } catch (error) {
      notify.hideLoading();
      console.error('购买失败:', error);
      
      notify.error(typeof error === 'string' ? error : '购买失败，请稍后重试');
    } finally {
      this.setData({ purchasing: false });
    }
  },
  
  // 下拉刷新
  async onPullDownRefresh() {
    await this.loadData();
    wx.stopPullDownRefresh();
  }
}) 