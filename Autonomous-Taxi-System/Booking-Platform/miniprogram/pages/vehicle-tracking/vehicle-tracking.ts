// 车辆位置追踪页面逻辑
const { loadCityParameters } = require('../../utils/coordinate'); // 引入坐标转换工具

interface VehicleData {
  vehicleId: number;
  plateNumber: string;
  model: string;
  currentStatus: string;
  batteryLevel: number;
  rating: number;
  location: {
    longitude: number;
    latitude: number;
    locationName: string;
  };
}

Page({
  data: {
    vehicleData: null as VehicleData | null, // 车辆数据
    mapCenter: { longitude: 116.397428, latitude: 39.90923 }, // 地图中心点
    mapScale: 16, // 地图缩放级别
    markers: [] as any[], // 地图标记
    isLoading: true, // 加载状态
    errorMessage: '' // 错误信息
  },

  async onLoad() {
    // 预先加载城市参数
    try {
      console.log('预加载城市参数...');
      await loadCityParameters();
      console.log('城市参数预加载完成');
    } catch (error) {
      console.error('城市参数预加载失败:', error);
    }
    
    this.loadVehicleLocation(); // 加载车辆位置
  },

  onShow() {
    this.loadVehicleLocation(); // 页面显示时刷新数据
  },

  // 加载车辆位置数据
  async loadVehicleLocation() {
    try {
      this.setData({ isLoading: true, errorMessage: '' });
      
      const token = wx.getStorageSync('token');
      if (!token) {
        wx.showToast({ title: '请先登录', icon: 'none' });
        wx.navigateTo({ url: '/pages/login/login' });
        return;
      }

      wx.request({
        url: 'http://localhost:5001/api/user/active-order/vehicle-location',
        method: 'GET',
        header: { 'Authorization': `Bearer ${token}` },
        success: (res: any) => {
          if (res.data.code === 0) {
            const vehicleData = res.data.data;
            this.setData({ vehicleData, isLoading: false });
            this.updateMapData(vehicleData); // 更新地图数据
          } else {
            this.setData({ 
              errorMessage: res.data.message || '获取车辆位置失败',
              isLoading: false 
            });
          }
        },
        fail: (error: any) => {
          console.error('加载车辆位置失败:', error);
          this.setData({ 
            errorMessage: '网络连接失败，请检查网络设置',
            isLoading: false 
          });
        }
      });
    } catch (error) {
      console.error('加载车辆位置失败:', error);
      this.setData({ 
        errorMessage: '网络连接失败，请检查网络设置',
        isLoading: false 
      });
    }
  },

  // 更新地图数据
  updateMapData(vehicleData: VehicleData) {
    const { longitude, latitude } = vehicleData.location;
    
    // 更新地图中心点和标记
    this.setData({
      mapCenter: { longitude, latitude },
      markers: [{
        id: 1,
        longitude,
        latitude,
        iconPath: '/static/images/vehicle-marker.png',
        width: 40,
        height: 40,
        title: `${vehicleData.plateNumber} - ${vehicleData.currentStatus}`
      }]
    });
  },

  // 刷新位置
  refreshLocation() {
    this.loadVehicleLocation();
  },

  // 重试加载
  retryLoad() {
    this.loadVehicleLocation();
  },

  // 返回首页
  goHome() {
    wx.switchTab({ url: '/pages/index/index' });
  }
}); 