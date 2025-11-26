// index.ts
// 获取应用实例
import { checkLoginStatus, getUserInfo, logout, createOrderAPI, fetchUserDetailInfo, getOrderPriceEstimateAPI } from '../../utils/db';
import { loadCityParameters, geoToSystemCoordinates, systemToGeoCoordinates } from '../../utils/coordinate';

const app = getApp<IAppOption>()
const defaultAvatarUrl = 'https://mmbiz.qpic.cn/mmbiz/icTdbqWNOwNRna42FI242Lcia07jQodd2FJGIYQfG0LAJGFxM4FbnQP6yfMxBgJ0F3YRqJCJ1aPAK2dQagdusBZg/0'

// 高德地图API密钥
const amapKey = '6aa281df2f8c41f2644c648d3d17b1af';

// 定义坐标类型
interface Coordinate {
  latitude: number;
  longitude: number;
}

// 定义点位信息类型
interface PointInfo extends Coordinate {
  address?: string;
}

// 定义地图标记类型
interface MapMarker {
  id: number;
  latitude: number;
  longitude: number;
  title: string;
  iconPath: string;
  width: number;
  height: number;
  callout?: {
    content: string;
    color: string;
    fontSize: number;
    borderRadius: number;
    bgColor: string;
    padding: number;
    display: string;
  };
}

// 定义城市坐标映射类型
interface CityCoordinates {
  [key: string]: Coordinate;
}

// 定义自定义用户信息类型
interface CustomUserInfo {
  avatarUrl: string;
  nickName: string;
  creditScore: number;
  userId: number;
  realName?: string;
  username?: string;
}

// 定义车辆位置数据类型
interface VehicleLocationData {
  vehicleId: number;
  plateNumber: string;
  model: string;
  currentStatus: string;
  batteryLevel: number;
  rating: number;
  location: {
    longitude: number;
    latitude: number;
    systemX: number;
    systemY: number;
    locationName: string;
    city: string;
  };
  orderInfo: {
    orderId: number;
    orderNumber: string;
    orderStatus: string;
    createTime: string;
    arrivalTime?: string;
    pickupLocation: string;
    pickupLocationX: number;  // 起点系统坐标X
    pickupLocationY: number;  // 起点系统坐标Y
    dropoffLocation: string;
    dropoffLocationX: number;  // 终点系统坐标X
    dropoffLocationY: number;  // 终点系统坐标Y
    cityCode: string;
  };
  lastUpdate: string;
}

// 城市坐标映射
const cityCoordinates: CityCoordinates = {
  '沈阳市': { latitude: 41.805699, longitude: 123.431406 },
  '上海市': { latitude: 31.230416, longitude: 121.473701 },
  '北京市': { latitude: 39.904989, longitude: 116.405285 },
  '广州市': { latitude: 23.129163, longitude: 113.264435 },
  '深圳市': { latitude: 22.543096, longitude: 114.057865 },
  '杭州市': { latitude: 30.274085, longitude: 120.155070 },
  '南京市': { latitude: 32.041544, longitude: 118.767413 },
  '成都市': { latitude: 30.572816, longitude: 104.066801 },
  '重庆市': { latitude: 29.563010, longitude: 106.551557 },
  '武汉市': { latitude: 30.593099, longitude: 114.305393 },
  '西安市': { latitude: 34.341576, longitude: 108.940175 }
};

Page({
  data: {
    userInfo: {
      avatarUrl: defaultAvatarUrl,
      nickName: '',
      creditScore: 0,
      userId: 0,
      realName: ''
    } as CustomUserInfo,
    hasUserInfo: false,
    canIUseGetUserProfile: wx.canIUse('getUserProfile'),
    canIUseNicknameComp: wx.canIUse('input.type.nickname'),
    isLogged: false,
    
    // 侧边栏相关
    showSidebar: false,
    
    // 地图相关数据
    cities: ['沈阳市', '上海市', '北京市', '广州市', '深圳市', '杭州市', '南京市', '成都市', '重庆市', '武汉市', '西安市'],
    cityIndex: 0, // 默认选择沈阳市
    latitude: 41.805699,
    longitude: 123.431406,
    scale: 12,
    markers: [] as MapMarker[],
    polygons: [] as any[], // #运营范围多边形数据
    // 起终点相关
    showPopup: false,
    clickPosition: null as PointInfo | null,
    startPoint: null as PointInfo | null,
    endPoint: null as PointInfo | null,
    hasSetStart: false,
    hasSetEnd: false,
    // 车辆位置相关
    vehicleLocation: null as VehicleLocationData | null,
    vehicleLocationTimer: null as any,
    hasActiveOrder: false, // 是否有进行中的订单
    hasOrderInProgress: false, // 是否有订单正在进行（包括待分配状态）
    // 车辆详情弹窗相关
    showVehicleDetail: false, // 是否显示车辆详情弹窗
    selectedVehicle: null as VehicleLocationData | null, // 选中的车辆信息
    // 订单确认弹窗相关
    showOrderConfirm: false, // 是否显示订单确认弹窗
    orderConfirmData: null as any // 订单确认数据
  },
  
  // 页面加载
  async onLoad() {
    // 预加载城市参数
    try {
      console.log('开始预加载城市参数...');
      await loadCityParameters();
      console.log('城市参数预加载完成');
    } catch (error) {
      console.error('城市参数预加载失败:', error);
    }
    
    // 检查登录状态
    const isLogged = checkLoginStatus();
    if (isLogged) {
      try {
        // 获取用户详细信息，包括注册城市
        const userDetail = await fetchUserDetailInfo();
        
        // 根据用户注册城市设置初始城市选择
        let initialCityIndex = 0; // 默认沈阳市
        let initialLatitude = 41.805699;
        let initialLongitude = 123.431406;
        
        if (userDetail.registration_city && this.data.cities.includes(userDetail.registration_city)) {
          initialCityIndex = this.data.cities.indexOf(userDetail.registration_city);
          const cityCoord = cityCoordinates[userDetail.registration_city];
          if (cityCoord) {
            initialLatitude = cityCoord.latitude;
            initialLongitude = cityCoord.longitude;
          }
          console.log(`根据用户注册城市设置初始城市: ${userDetail.registration_city}`);
        } else {
          console.log('用户注册城市不在支持列表中或未设置，使用默认城市');
        }
        
        // #使用Promise确保setData完成后再执行后续操作
        await new Promise<void>((resolve) => {
          this.setData({
            isLogged: true,
            hasUserInfo: true,
            userInfo: {
              ...this.data.userInfo,
              nickName: userDetail.username || '用户',
            },
            cityIndex: initialCityIndex,
            latitude: initialLatitude,
            longitude: initialLongitude
          }, () => {
            console.log(`页面数据设置完成，当前城市索引: ${initialCityIndex}, 城市: ${this.data.cities[initialCityIndex]}`);
            resolve();
          });
        });
        
      } catch (error) {
        console.error('获取用户详细信息失败:', error);
        // 使用基本用户信息作为备选
        const userInfoFromDB = getUserInfo() as unknown;
        const dbUserInfo = userInfoFromDB as { username?: string, [key: string]: any };
        
        // #确保默认数据也正确设置
        await new Promise<void>((resolve) => {
          this.setData({
            isLogged: true,
            hasUserInfo: true,
            userInfo: {
              ...this.data.userInfo,
              nickName: dbUserInfo.username || '用户',
            }
          }, () => {
            console.log(`使用默认数据设置完成，当前城市索引: ${this.data.cityIndex}, 城市: ${this.data.cities[this.data.cityIndex]}`);
            resolve();
          });
        });
      }
      
      // 初始化地图标记
      this.updateMapMarkers();
      
      // 获取用户当前位置
      wx.getLocation({
        type: 'gcj02',
        success: (res) => {
          this.setData({
            latitude: res.latitude,
            longitude: res.longitude
          });
        },
        fail: () => {
          // 如果获取位置失败，使用已设置的城市位置
          console.log('获取位置信息失败，使用注册城市位置');
        }
      });
      
      // 立即获取一次车辆位置
      this.loadVehicleLocation();
      
      // 设置定时器定期更新车辆位置 - 根据是否有订单调整频率
      this.startVehicleLocationTimer();
      
      // #使用setTimeout确保运营范围生成在下一个事件循环执行
      setTimeout(() => {
        console.log('页面加载完成，开始生成运营范围...');
        this.generateOperatingAreaWithRetry();
      }, 100);
    } else {
      // #未登录用户也显示运营范围
      setTimeout(() => {
        console.log('未登录用户，生成默认城市运营范围...');
        this.generateOperatingAreaWithRetry();
      }, 100);
    }
  },
  
  // 页面显示
  onShow() {
    if (this.data.isLogged) {
      this.updateMapMarkers();
      this.loadVehicleLocation(); // 页面显示时也更新车辆位置
      
      // 延迟检查订单状态，确保车辆位置检查完成后再判断
      setTimeout(() => {
        this.checkOrderStatus();
      }, 1000);
      
      // #延迟加载运营范围，确保页面完全显示后再执行
      setTimeout(() => {
        console.log('页面显示完成，重新加载运营范围...');
        this.generateOperatingAreaWithRetry();
      }, 200);
    }
  },
  
  // 页面隐藏时清除定时器
  onHide() {
    if (this.data.vehicleLocationTimer) {
      clearInterval(this.data.vehicleLocationTimer);
    }
  },
  
  // 页面卸载时清除定时器
  onUnload() {
    if (this.data.vehicleLocationTimer) {
      clearInterval(this.data.vehicleLocationTimer);
    }
  },
  
  // 获取进行中订单的车辆位置
  async loadVehicleLocation() {
    if (!this.data.isLogged) return;
    
    try {
      const token = wx.getStorageSync('token');
      if (!token) return;
      
      const response = await new Promise<any>((resolve, reject) => {
        wx.request({
          url: 'http://localhost:5001/api/user/active-order/vehicle-location',
          method: 'GET',
          header: {
            'Authorization': `Bearer ${token}`
          },
          success: resolve,
          fail: reject
        });
      });
      
      if (response.statusCode === 200 && response.data.code === 0) {
        const hadActiveOrder = this.data.hasActiveOrder;
        const vehicleData = response.data.data;
        
        this.setData({
          vehicleLocation: vehicleData,
          hasActiveOrder: true,
          hasOrderInProgress: true // 有车辆位置说明订单正在进行
        });
        
        // 检查订单状态，如果订单已结束则清除起终点标记
        if (vehicleData.orderInfo && vehicleData.orderInfo.orderStatus === '已结束') {
          console.log('订单已结束，清除起终点标记');
          this.setData({ hasOrderInProgress: false });
          this.clearRoutePoints();
        }
        
        // 如果之前没有进行中订单，现在有了，需要调整定时器频率
        if (!hadActiveOrder) {
          this.startVehicleLocationTimer();
        }
        
        // 更新地图标记以包含车辆位置
        this.updateMapMarkers();
        console.log('车辆位置更新成功:', vehicleData.plateNumber);
      } else if (response.statusCode === 404) {
        const hadActiveOrder = this.data.hasActiveOrder;
        // 没有进行中的订单，清除车辆位置
        this.setData({
          vehicleLocation: null,
          hasActiveOrder: false
        });
        
        // 检查是否有待分配订单
        await this.checkOrderStatus();
        
        // 如果之前有进行中订单，现在没有了，需要调整定时器频率
        if (hadActiveOrder) {
          this.startVehicleLocationTimer();
        }
        
        this.updateMapMarkers();
      }
    } catch (error) {
      console.log('获取车辆位置失败:', error);
      // 静默失败，不显示错误提示
    }
  },
  
  // 检查是否有待分配或进行中的订单
  async checkOrderStatus() {
    if (!this.data.isLogged) return;
    
    try {
      const token = wx.getStorageSync('token');
      if (!token) return;
      
      const response = await new Promise<any>((resolve, reject) => {
        wx.request({
          url: 'http://localhost:5001/api/user/orders',
          method: 'GET',
          header: {
            'Authorization': `Bearer ${token}`
          },
          data: {
            status: '待分配',
            page: 1,
            per_page: 1
          },
          success: resolve,
          fail: reject
        });
      });
      
      if (response.statusCode === 200 && response.data.code === 0) {
        const orders = response.data.data.orders || [];
        const hasPendingOrder = orders.length > 0;
        
        // 如果有待分配订单，设置hasOrderInProgress为true
        if (hasPendingOrder) {
          this.setData({ hasOrderInProgress: true });
          console.log('检测到待分配订单，保持起终点标记');
        } else if (!this.data.hasActiveOrder) {
          // 如果没有待分配订单且没有进行中订单，则可以清除标记
          this.setData({ hasOrderInProgress: false });
          if (this.data.hasSetStart || this.data.hasSetEnd) {
            console.log('没有任何订单，清除起终点标记');
            this.clearRoutePoints();
          }
        }
      }
    } catch (error) {
      console.log('检查订单状态失败:', error);
    }
  },
  
  // 手动刷新车辆位置
  refreshVehicleLocation() {
    wx.showToast({
      title: '正在刷新车辆位置...',
      icon: 'loading',
      duration: 1000
    });
    
    this.loadVehicleLocation().then(() => {
      wx.showToast({
        title: '车辆位置已更新',
        icon: 'success',
        duration: 1500
      });
    }).catch(() => {
      wx.showToast({
        title: '刷新失败',
        icon: 'none',
        duration: 1500
      });
    });
  },
  
  // 侧边栏相关方法
  toggleSidebar() {
    this.setData({
      showSidebar: true
    });
  },
  
  closeSidebar() {
    this.setData({
      showSidebar: false
    });
  },
  
  // 事件处理函数
  bindViewTap() {
    wx.navigateTo({
      url: '../logs/logs',
    })
  },
  
  onChooseAvatar(e: any) {
    const { avatarUrl } = e.detail
    const { nickName } = this.data.userInfo
    this.setData({
      "userInfo.avatarUrl": avatarUrl,
      hasUserInfo: nickName && avatarUrl && avatarUrl !== defaultAvatarUrl,
    })
  },
  
  onInputChange(e: any) {
    const nickName = e.detail.value
    const { avatarUrl } = this.data.userInfo
    this.setData({
      "userInfo.nickName": nickName,
      hasUserInfo: nickName && avatarUrl && avatarUrl !== defaultAvatarUrl,
    })
  },
  
  getUserProfile() {
    // 推荐使用wx.getUserProfile获取用户信息，开发者每次通过该接口获取用户个人信息均需用户确认，开发者妥善保管用户快速填写的头像昵称，避免重复弹窗
    wx.getUserProfile({
      desc: '展示用户信息', // 声明获取用户个人信息后的用途，后续会展示在弹窗中，请谨慎填写
      success: (res) => {
        console.log(res)
        this.setData({
          userInfo: {
            ...this.data.userInfo,
            avatarUrl: res.userInfo.avatarUrl,
            nickName: res.userInfo.nickName
          },
          hasUserInfo: true
        })
      }
    })
  },
  
  // 城市选择器改变事件
  cityChange(e: any) {
    const cityIndex = e.detail.value;
    const selectedCity = this.data.cities[cityIndex];
    const { latitude, longitude } = cityCoordinates[selectedCity];
    
    this.setData({
      cityIndex,
      latitude,
      longitude
    });
    
    // 更新地图标记
    this.updateMapMarkers();
    
    // #使用重试机制生成运营范围多边形
    this.generateOperatingAreaWithRetry();
  },
  
  // #生成运营范围多边形
  async generateOperatingArea() {
    const currentCity = this.data.cities[this.data.cityIndex];
    console.log(`开始为城市 ${currentCity} 生成运营范围...`);
    
    try {
      // #确保城市参数已加载
      const loaded = await loadCityParameters();
      if (!loaded) {
        throw new Error('城市参数加载失败');
      }
      
      // #定义运营范围的四个角点(系统坐标0-999)
      const corners = [
        { x: 0, y: 0 },     // #左上角
        { x: 999, y: 0 },   // #右上角  
        { x: 999, y: 999 }, // #右下角
        { x: 0, y: 999 }    // #左下角
      ];
      
      console.log(`正在转换 ${corners.length} 个角点坐标...`);
      
      // #将系统坐标转换为经纬度
      const geoPoints = [];
      for (let i = 0; i < corners.length; i++) {
        const corner = corners[i];
        console.log(`转换角点 ${i + 1}: (${corner.x}, ${corner.y})`);
        
        const geoCoord = await systemToGeoCoordinates(corner.x, corner.y, currentCity) as {latitude: number, longitude: number};
        
        if (!geoCoord || typeof geoCoord.latitude !== 'number' || typeof geoCoord.longitude !== 'number') {
          throw new Error(`角点 ${i + 1} 坐标转换失败`);
        }
        
        geoPoints.push({
          latitude: geoCoord.latitude,
          longitude: geoCoord.longitude
        });
        
        console.log(`角点 ${i + 1} 转换完成: (${geoCoord.longitude.toFixed(6)}, ${geoCoord.latitude.toFixed(6)})`);
      }
      
      // #创建运营范围多边形
      const operatingPolygon = {
        points: geoPoints,
        strokeWidth: 3,
        strokeColor: '#667eea',
        fillColor: 'rgba(102, 126, 234, 0.1)',
        zIndex: 1
      };
      
      this.setData({
        polygons: [operatingPolygon]
      });
      
      console.log(`✅ 已为${currentCity}成功生成运营范围多边形，包含 ${geoPoints.length} 个坐标点`);
      
    } catch (error) {
      console.error(`❌ 生成${currentCity}运营范围失败:`, error);
      throw error; // #重新抛出错误供重试机制处理
    }
  },
  
  // 地图点击事件处理
  onMapTap(e: any) {
    const { latitude, longitude } = e.detail;
    
    // 设置点击位置信息，不再使用屏幕坐标
    this.setData({
      showPopup: true,
      clickPosition: { latitude, longitude }
    });
    
    // 移动地图中心到点击位置
    this.setData({
      latitude,
      longitude
    });
  },
  
  // 显示车辆详情弹窗
  showVehicleDetail() {
    if (this.data.vehicleLocation) {
      this.setData({
        showVehicleDetail: true,
        selectedVehicle: this.data.vehicleLocation
      });
    }
  },
  
  // 关闭车辆详情弹窗
  closeVehicleDetail() {
    this.setData({
      showVehicleDetail: false,
      selectedVehicle: null
    });
  },
  
  // 关闭弹窗
  closePopup() {
    this.setData({
      showPopup: false,
      clickPosition: null
    });
  },
  
  // 设置为起点
  setAsStart() {
    if (!this.data.clickPosition) return;
    
    const startMarker = {
      id: 2,
      latitude: this.data.clickPosition.latitude,
      longitude: this.data.clickPosition.longitude,
      title: '起点',
      iconPath: '/static/images/起点.svg',
      width: 30,
      height: 30,
      callout: {
        content: '起点',
        color: '#ffffff',
        fontSize: 12,
        borderRadius: 4,
        bgColor: '#3a7afe',
        padding: 5,
        display: 'ALWAYS'
      }
    };
    
    // 更新标记和起点数据
    let markers = [...this.data.markers];
    // 移除之前的起点标记（如果有）
    markers = markers.filter(m => m.id !== 2);
    markers.push(startMarker);
    
    this.setData({
      markers,
      startPoint: this.data.clickPosition,
      hasSetStart: true,
      showPopup: false
    });
    
    // 提示设置成功
    wx.showToast({
      title: '起点设置成功',
      icon: 'success',
      duration: 1500
    });
  },
  
  // 设置为终点
  setAsEnd() {
    if (!this.data.clickPosition || !this.data.hasSetStart) return;
    
    const endMarker = {
      id: 3,
      latitude: this.data.clickPosition.latitude,
      longitude: this.data.clickPosition.longitude,
      title: '终点',
      iconPath: '/static/images/终点.svg',
      width: 30,
      height: 30,
      callout: {
        content: '终点',
        color: '#ffffff',
        fontSize: 12,
        borderRadius: 4,
        bgColor: '#ff5252',
        padding: 5,
        display: 'ALWAYS'
      }
    };
    
    // 更新标记和终点数据
    let markers = [...this.data.markers];
    // 移除之前的终点标记（如果有）
    markers = markers.filter(m => m.id !== 3);
    markers.push(endMarker);
    
    this.setData({
      markers,
      endPoint: this.data.clickPosition,
      hasSetEnd: true,
      showPopup: false
    });
    
    // 提示设置成功
    wx.showToast({
      title: '终点设置成功',
      icon: 'success',
      duration: 1500
    });
  },
  
  // 重置起终点
  resetPoints() {
    // 移除起终点标记
    let markers = [...this.data.markers];
    markers = markers.filter(m => m.id !== 2 && m.id !== 3);
    
    this.setData({
      markers,
      startPoint: null,
      endPoint: null,
      hasSetStart: false,
      hasSetEnd: false,
      showPopup: false
    });
    
    // 提示重置成功
    wx.showToast({
      title: '已重置起终点',
      icon: 'success',
      duration: 1500
    });
  },
  
  // 更新地图标记点
  updateMapMarkers() {
    // 创建标记数组，不再添加城市中心点标记
    const markers: MapMarker[] = [];
    
    // 添加已设置的起点和终点标记
    if (this.data.startPoint) {
      markers.push({
        id: 2,
        latitude: this.data.startPoint.latitude,
        longitude: this.data.startPoint.longitude,
        title: '起点',
        iconPath: '/static/images/起点.svg',
        width: 30,
        height: 30,
        callout: {
          content: '起点',
          color: '#ffffff',
          fontSize: 12,
          borderRadius: 4,
          bgColor: '#3a7afe',
          padding: 5,
          display: 'ALWAYS'
        }
      });
    }

    if (this.data.endPoint) {
      markers.push({
        id: 3,
        latitude: this.data.endPoint.latitude,
        longitude: this.data.endPoint.longitude,
        title: '终点',
        iconPath: '/static/images/终点.svg',
        width: 30,
        height: 30,
        callout: {
          content: '终点',
          color: '#ffffff',
          fontSize: 12,
          borderRadius: 4,
          bgColor: '#ff5252',
          padding: 5,
          display: 'ALWAYS'
        }
      });
    }

    // 添加车辆位置标记
    if (this.data.vehicleLocation) {
      const vehicle = this.data.vehicleLocation;
      markers.push({
        id: 4,
        latitude: vehicle.location.latitude,
        longitude: vehicle.location.longitude,
        title: `车辆 ${vehicle.plateNumber}`,
        iconPath: '/static/images/车辆.svg',
        width: 40,
        height: 40,
        callout: {
          content: vehicle.plateNumber, // 只显示车牌号
          color: '#ffffff',
          fontSize: 14,
          borderRadius: 6,
          bgColor: '#00c853',
          padding: 8,
          display: 'ALWAYS'
        }
      });
    }

    this.setData({ markers });
  },
  
  // 发起订单
  async createOrder() {
    if (!this.data.startPoint || !this.data.endPoint) {
      wx.showToast({
        title: '请先设置起点和终点',
        icon: 'none',
        duration: 2000
      });
      return;
    }
    
    // #检查起点和终点是否在运营范围内
    try {
      const currentCity = this.data.cities[this.data.cityIndex];
      
      // #将起点经纬度转换为系统坐标
      const startSystemCoords = await geoToSystemCoordinates(
        this.data.startPoint.longitude, 
        this.data.startPoint.latitude, 
        currentCity
      ) as {x: number, y: number};
      
      // #将终点经纬度转换为系统坐标
      const endSystemCoords = await geoToSystemCoordinates(
        this.data.endPoint.longitude, 
        this.data.endPoint.latitude, 
        currentCity
      ) as {x: number, y: number};
      
      console.log(`起点系统坐标: (${startSystemCoords.x}, ${startSystemCoords.y})`);
      console.log(`终点系统坐标: (${endSystemCoords.x}, ${endSystemCoords.y})`);
      
      // #检查起点坐标是否在运营范围内 (0 < x < 999 且 0 < y < 999)
      if (startSystemCoords.x <= 0 || startSystemCoords.x >= 999 || 
          startSystemCoords.y <= 0 || startSystemCoords.y >= 999) {
        wx.showModal({
          title: '超出运营范围',
          content: `起点坐标(${startSystemCoords.x}, ${startSystemCoords.y})超出运营范围，无法发起订单，请重新选择起点`,
          showCancel: false,
          confirmText: '确定'
        });
        return;
      }
      
      // #检查终点坐标是否在运营范围内 (0 < x < 999 且 0 < y < 999)
      if (endSystemCoords.x <= 0 || endSystemCoords.x >= 999 || 
          endSystemCoords.y <= 0 || endSystemCoords.y >= 999) {
        wx.showModal({
          title: '超出运营范围',
          content: `终点坐标(${endSystemCoords.x}, ${endSystemCoords.y})超出运营范围，无法发起订单，请重新选择终点`,
          showCancel: false,
          confirmText: '确定'
        });
        return;
      }
      
      console.log('✅ 起点和终点均在运营范围内，可以发起订单');
      
    } catch (error) {
      console.error('坐标转换失败:', error);
      wx.showToast({
        title: '坐标转换失败，请重试',
        icon: 'none',
        duration: 2000
      });
      return;
    }
    
    // 显示加载提示
    wx.showLoading({
      title: '正在计算价格...',
    });
    
    try {
      // 调用价格预估API获取价格区间
      const priceEstimate = await getOrderPriceEstimateAPI({
        pickup_location: {
          latitude: this.data.startPoint.latitude,
          longitude: this.data.startPoint.longitude
        },
        dropoff_location: {
          latitude: this.data.endPoint.latitude,
          longitude: this.data.endPoint.longitude
        },
        city_code: this.data.cities[this.data.cityIndex]
      });
      
      wx.hideLoading();
      
      // 将经纬度转换为系统坐标用于显示
      const pickupSystemCoords = await geoToSystemCoordinates(this.data.startPoint.longitude, this.data.startPoint.latitude, this.data.cities[this.data.cityIndex]) as {x: number, y: number};
      const dropoffSystemCoords = await geoToSystemCoordinates(this.data.endPoint.longitude, this.data.endPoint.latitude, this.data.cities[this.data.cityIndex]) as {x: number, y: number};
      
      // 使用自定义弹窗展示订单信息，显示价格区间和系统计算的距离
      this.setData({
        showOrderConfirm: true,
        orderConfirmData: {
          priceEstimate,
          pickupSystemCoords,
          dropoffSystemCoords
        }
      });
      
    } catch (error) {
      wx.hideLoading();
      console.error('获取价格预估失败:', error);
      
      // 如果API调用失败，重新计算距离并使用原有的简单价格计算作为备选
      const distance = this.calculateDistance(
        this.data.startPoint.latitude,
        this.data.startPoint.longitude,
        this.data.endPoint.latitude,
        this.data.endPoint.longitude
      );
      
      const basePrice = 10; // 基础价10元
      const distancePrice = Math.round(distance * 2.5) / 10; // 每公里2.5元，四舍五入到角
      const totalPrice = (basePrice + distancePrice).toFixed(1);
      
      // 将经纬度转换为系统坐标用于显示
      const pickupSystemCoords = await geoToSystemCoordinates(this.data.startPoint.longitude, this.data.startPoint.latitude, this.data.cities[this.data.cityIndex]) as {x: number, y: number};
      const dropoffSystemCoords = await geoToSystemCoordinates(this.data.endPoint.longitude, this.data.endPoint.latitude, this.data.cities[this.data.cityIndex]) as {x: number, y: number};
      
      this.setData({
        showOrderConfirm: true,
        orderConfirmData: {
          distance,
          basePrice,
          distancePrice,
          totalPrice,
          pickupSystemCoords,
          dropoffSystemCoords
        }
      });
    }
  },
  
  // 提交订单
  submitOrder(distance: number, amount: number) {
    // 确认下单
    wx.showLoading({
      title: '正在为您呼叫车辆...',
    });
    
    // 检查登录状态
    if (!checkLoginStatus()) {
      wx.hideLoading();
      wx.showToast({
        title: '请先登录',
        icon: 'none',
        duration: 2000
      });
      
      // 跳转到登录页面
      setTimeout(() => {
        wx.navigateTo({
          url: '/pages/login/login'
        });
      }, 1500);
      return;
    }
    
    // 准备订单数据
    const orderData = {
      pickupLocation: {
        latitude: this.data.startPoint!.latitude,
        longitude: this.data.startPoint!.longitude
      },
      dropoffLocation: {
        latitude: this.data.endPoint!.latitude,
        longitude: this.data.endPoint!.longitude
      },
      cityCode: this.data.cities[this.data.cityIndex],
      amount: amount,
      distance: parseFloat(distance.toFixed(1))
    };
    
    // 调用创建订单API
    createOrderAPI(orderData)
      .then(res => {
        wx.hideLoading();
        wx.showToast({
          title: '下单成功！车辆正在赶来',
          icon: 'success',
          duration: 2000
        });
        
        // 下单成功后设置订单进行状态，保留起终点标记
        this.setData({ hasOrderInProgress: true });
        console.log('订单创建成功，保留起终点标记');
      })
      .catch(err => {
        wx.hideLoading();
        wx.showToast({
          title: err || '下单失败，请重试',
          icon: 'none',
          duration: 2000
        });
      });
  },
  
  // 计算两点之间的距离（公里）
  calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const R = 6371; // 地球半径，单位km
    const dLat = this.deg2rad(lat2 - lat1);
    const dLon = this.deg2rad(lon2 - lon1);
    
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(this.deg2rad(lat1)) * Math.cos(this.deg2rad(lat2)) * 
      Math.sin(dLon/2) * Math.sin(dLon/2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c; // 距离，单位km
  },
  
  // 角度转弧度
  deg2rad(deg: number): number {
    return deg * (Math.PI/180);
  },
  
  // 启动车辆位置定时器
  startVehicleLocationTimer() {
    // 清除现有定时器
    if (this.data.vehicleLocationTimer) {
      clearInterval(this.data.vehicleLocationTimer);
    }
    
    // 根据是否有进行中订单设置不同的更新频率
    const updateInterval = this.data.hasActiveOrder ? 3000 : 100000000; // #修复超大数值错误，改为30秒
    
    this.setData({
      vehicleLocationTimer: setInterval(() => {
        this.loadVehicleLocation();
      }, updateInterval)
    });
    
  },
  
  // 清除起终点标记
  clearRoutePoints() {
    // 移除起终点标记
    let markers = [...this.data.markers];
    markers = markers.filter(m => m.id !== 2 && m.id !== 3);
    
    this.setData({
      markers,
      startPoint: null,
      endPoint: null,
      hasSetStart: false,
      hasSetEnd: false,
      showPopup: false
    });
    
    console.log('起终点标记已清除');
  },
  
  // 关闭订单确认弹窗
  closeOrderConfirm() {
    this.setData({
      showOrderConfirm: false,
      orderConfirmData: null
    });
  },
  
  // 确认下单
  async confirmOrder() {
    const data = this.data.orderConfirmData;
    if (!data) return;
    
    // #检查用户余额是否足够支付最低金额
    try {
      wx.showLoading({ title: '检查余额中...' });
      
      // 获取最新用户信息（包含余额）
      const userDetail = await fetchUserDetailInfo();
      const userBalance = userDetail.balance || 0;
      
      // 计算订单最低金额
      let minAmount = 0;
      if (data.priceEstimate) {
        minAmount = data.priceEstimate.min_price;
      } else {
        minAmount = parseFloat(data.totalPrice);
      }
      
      wx.hideLoading();
      
      // 检查余额是否足够
      if (userBalance < minAmount) {
        wx.showModal({
          title: '余额不足',
          content: `当前余额：¥${userBalance.toFixed(2)}\n订单最低金额：¥${minAmount.toFixed(2)}\n\n余额不足支付最低金额，请先充值`,
          showCancel: true,
          cancelText: '取消',
         
        
        });
        return;
      }
      
    } catch (error) {
      wx.hideLoading();
      console.error('获取用户余额失败:', error);
      wx.showToast({
        title: '获取余额信息失败，请重试',
        icon: 'none',
        duration: 2000
      });
      return;
    }
    
    // 关闭弹窗
    this.closeOrderConfirm();
    
    // 提交订单
    if (data.priceEstimate) {
      // 使用价格预估数据
      this.submitOrder(data.priceEstimate.distance, data.priceEstimate.max_price);
    } else {
      // 使用基础价格计算数据
      this.submitOrder(data.distance, parseFloat(data.totalPrice));
    }
  },
  
  // #添加重试机制的运营范围生成
  async generateOperatingAreaWithRetry() {
    console.log('=== 开始运营范围生成流程 ===');
    console.log(`当前城市索引: ${this.data.cityIndex}`);
    console.log(`当前城市: ${this.data.cities[this.data.cityIndex]}`);
    console.log(`城市列表: ${this.data.cities.join(', ')}`);
    
    let retries = 0;
    const maxRetries = 3;
    
    while (retries < maxRetries) {
      try {
        console.log(`🔄 第 ${retries + 1} 次尝试生成运营范围...`);
        await this.generateOperatingArea();
        console.log('✅ 运营范围生成成功');
        return;
      } catch (error) {
        console.error(`❌ 生成运营范围重试 ${retries + 1} 失败:`, error);
        retries++;
        
        if (retries < maxRetries) {
          // #等待1秒后重试
          console.log(`⏳ 等待1秒后进行第 ${retries + 1} 次重试...`);
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
    }
    
    console.error('💥 所有重试失败，无法生成运营范围');
    wx.showToast({
      title: '运营范围加载失败',
      icon: 'none',
      duration: 2000
    });
  }
})
