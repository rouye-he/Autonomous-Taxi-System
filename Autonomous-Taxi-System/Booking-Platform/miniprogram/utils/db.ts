// db.ts - 数据库连接和操作函数 #数据库工具函数

// 服务器地址配置 - 本地开发服务器
const API_BASE_URL = 'http://localhost:5001'; 

// 登录接口
export const login = (data: {email: string; password: string}) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始登录请求');
    wx.request({
      url: `${API_BASE_URL}/api/login`,
      method: 'POST',
      data,
      success: (res: any) => {
        console.log('登录响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          try {
            // 登录成功，存储token和用户信息到本地存储和全局变量
            const app = getApp<IAppOption>();
            const token = res.data.data.token;
            const userInfo = res.data.data.userInfo;
            
            // 保存到本地存储
            wx.setStorageSync('token', token);
            wx.setStorageSync('userInfo', userInfo);
            
            // 保存到全局变量
            app.globalData.token = token;
            app.globalData.userInfo = userInfo;
            
            resolve(res.data.data);
          } catch (e) {
            console.error('存储用户信息失败:', e);
            reject('存储用户信息失败');
          }
        } else {
          // 登录失败
          reject(res.data.message || '登录失败，请检查邮箱和密码');
        }
      },
      fail: (err) => {
        console.error('登录请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 发送验证码
export const sendVerifyCode = (email: string) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始发送验证码请求');
    wx.request({
      url: `${API_BASE_URL}/api/send_verify_code`,
      method: 'POST',
      data: { email },
      success: (res: any) => {
        console.log('发送验证码响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          resolve(res.data);
        } else {
          reject(res.data.message || '验证码发送失败');
        }
      },
      fail: (err) => {
        console.error('验证码发送请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 验证码登录
export const loginByCode = (data: {email: string; verifyCode: string}) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始验证码登录请求');
    wx.request({
      url: `${API_BASE_URL}/api/login_by_code`,
      method: 'POST',
      data,
      success: (res: any) => {
        console.log('验证码登录响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          try {
            // 登录成功，存储token和用户信息到本地存储和全局变量
            const app = getApp<IAppOption>();
            const token = res.data.data.token;
            const userInfo = res.data.data.userInfo;
            
            // 保存到本地存储
            wx.setStorageSync('token', token);
            wx.setStorageSync('userInfo', userInfo);
            
            // 保存到全局变量
            app.globalData.token = token;
            app.globalData.userInfo = userInfo;
            
            resolve(res.data.data);
          } catch (e) {
            console.error('存储用户信息失败:', e);
            reject('存储用户信息失败');
          }
        } else {
          // 登录失败
          reject(res.data.message || '登录失败，请检查邮箱和验证码');
        }
      },
      fail: (err) => {
        console.error('验证码登录请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 注册接口参数类型
interface RegisterParams {
  username: string;
  password: string;
  email: string;
  registration_city: string;
  verifyCode: string;
}

// 注册接口
export const register = (data: RegisterParams) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始注册请求');
    wx.request({
      url: `${API_BASE_URL}/api/register`,
      method: 'POST',
      data,
      success: (res: any) => {
        console.log('注册响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          // 注册成功
          resolve(res.data.data);
        } else {
          // 注册失败
          reject(res.data.message || '注册失败，请检查输入信息');
        }
      },
      fail: (err) => {
        console.error('注册请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 创建订单接口参数类型
export interface CreateOrderParams {
  pickupLocation: {
    latitude: number;
    longitude: number;
  };
  dropoffLocation: {
    latitude: number;
    longitude: number;
  };
  cityCode: string;
  amount: number;
  distance: number;
}

// 创建订单接口
export const createOrderAPI = (data: CreateOrderParams) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始创建订单请求');
    
    // 获取用户信息和token
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    wx.request({
      url: `${API_BASE_URL}/api/create_order`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data,
      success: (res: any) => {
        console.log('创建订单响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          // 订单创建成功
          resolve(res.data.data);
        } else {
          // 订单创建失败
          reject(res.data.message || '订单创建失败');
        }
      },
      fail: (err) => {
        console.error('创建订单请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 获取用户信息
export const getUserInfo = () => {
  try {
    const app = getApp<IAppOption>();
    return app.globalData.userInfo;
  } catch (e) {
    console.error('获取用户信息失败:', e);
    return null;
  }
};

// 更新用户信息
export const updateUserInfo = () => {
  return new Promise<any>((resolve, reject) => {
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录');
      return;
    }
    wx.request({
      url: `${API_BASE_URL}/api/user/info`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`
      },
      success: (res: any) => {
        if (res.statusCode === 200 && res.data.code === 0) {
          try {
            // 更新全局存储的用户信息
            app.globalData.userInfo = res.data.data;
            resolve(res.data.data);
          } catch (e) {
            console.error('存储用户信息失败:', e);
            reject('存储用户信息失败');
          }
        } else {
          reject(res.data.message || '获取用户信息失败');
        }
      },
      fail: (err) => {
        console.error('获取用户信息失败:', err);
        reject('网络错误，请检查网络连接');
      }
    });
  });
};

// 检查登录状态
export const checkLoginStatus = () => {
  const app = getApp<IAppOption>();
  
  // 优先检查本地存储
  const localToken = wx.getStorageSync('token');
  const localUserInfo = wx.getStorageSync('userInfo');
  
  // 如果本地存储有token但全局变量没有，恢复到全局变量
  if (localToken && !app.globalData.token) {
    app.globalData.token = localToken;
    if (localUserInfo) {
      app.globalData.userInfo = localUserInfo;
    }
  }
  
  return !!app.globalData.token;
};

// 退出登录
export const logout = () => {
  try {
    const app = getApp<IAppOption>();
    
    // 清除全局变量
    app.globalData.token = '';
    app.globalData.userInfo = null;
    
    // 清除本地存储
    wx.removeStorageSync('token');
    wx.removeStorageSync('userInfo');
    
    wx.redirectTo({
      url: '/pages/login/login'
    });
  } catch (e) {
    console.error('退出登录失败:', e);
    wx.showToast({
      title: '退出登录失败',
      icon: 'none'
    });
  }
};

// 模拟用户数据
export const mockUsers = [
  {
    userId: 1,
    username: 'juan71',
    password: 'ee5054f66d770f5b7d3c4562dd03e998',
    realName: '王玉英',
    creditScore: 99
  },
  {
    userId: 2,
    username: 'tianping',
    password: '888642de2ad98f03476df7f5ebbc5147',
    realName: '李建华',
    creditScore: 88
  },
  {
    userId: 3,
    username: 'leicao',
    password: 'ce35d05cb271b969bdf25fcc70c3540d',
    realName: '焦秀荣',
    creditScore: 80
  }
];

// 模拟登录验证
export const mockLoginValidate = (username: string, password: string) => {
  const user = mockUsers.find(u => u.username === username);
  if (!user) return { success: false, message: '用户不存在' };
  
  // 实际项目中应该对密码进行加密比较
  if (user.password === password) {
    return { 
      success: true, 
      user: {
        userId: user.userId,
        username: user.username,
        realName: user.realName,
        creditScore: user.creditScore
      }
    };
  } else {
    return { success: false, message: '密码错误' };
  }
};

// 从服务器获取用户详细信息
export const fetchUserDetailInfo = () => {
  return new Promise<any>((resolve, reject) => {
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录');
      return;
    }
    wx.request({
      url: `${API_BASE_URL}/api/user/detail`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`
      },
      success: (res: any) => {
        console.log('用户详细信息响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          try {
            // 更新全局存储的用户信息，并添加额外的详细信息
            const userDetail = res.data.data || {};
            
            // 确保处理缺失字段
            if (!userDetail.tags) userDetail.tags = '';
            if (!userDetail.total_orders) userDetail.total_orders = 0;
            if (!userDetail.coupon_count) userDetail.coupon_count = 0;
            
            // 创建符合小程序用户信息格式的对象
            const userInfo = {
              ...app.globalData.userInfo,
              user_id: userDetail.user_id,
              username: userDetail.username,
              real_name: userDetail.real_name,
              phone: userDetail.phone,
              email: userDetail.email || '',
              gender: userDetail.gender || '',
              birth_date: userDetail.birth_date || '',
              credit_score: userDetail.credit_score || 100,
              balance: userDetail.balance || 0,
              registration_time: userDetail.registration_time || '',
              last_login_time: userDetail.last_login_time || '',
              registration_city: userDetail.registration_city || '',
              registration_channel: userDetail.registration_channel || '',
              tags: userDetail.tags || '',
              total_orders: userDetail.total_orders || 0,
              coupon_count: userDetail.coupon_count || 0,
              avatar_url: userDetail.avatar_url || app.globalData.userInfo?.avatar_url || ''
            };
            
            // 更新全局状态
            app.globalData.userInfo = userInfo;
            
            resolve(userInfo);
          } catch (e) {
            console.error('处理用户详细信息失败:', e);
            reject('处理用户详细信息失败');
          }
        } else if (res.statusCode === 500) {
          console.error('服务器内部错误:', res.data);
          reject('获取用户详细信息失败: 服务器内部错误');
        } else {
          reject(res.data.message || '获取用户详细信息失败');
        }
      },
      fail: (err) => {
        console.error('获取用户详细信息失败:', err);
        reject('网络错误，请检查网络连接');
      }
    });
  });
};

// 模拟用户详细信息（本地开发测试用）
export const getMockUserDetailInfo = () => {
  return {
    user_id: 1,
    username: 'testuser',
    real_name: '测试用户',
    phone: '13800138000',
    email: 'test@example.com',
    gender: '男',
    birth_date: '1990-01-01',
    credit_score: 92,
    balance: 500.50,
    registration_time: '2023-08-15 14:30:00',
    last_login_time: '2023-10-12 09:15:30',
    registration_city: '沈阳市',
    registration_channel: '微信小程序',
    tags: '新用户,旅游用车,企业认证',
    total_orders: 35,
    coupon_count: 5
  };
};

// 修改密码API
export const changePasswordAPI = (data: {oldPassword: string; newPassword: string}) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始修改密码请求');
    
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    wx.request({
      url: `${API_BASE_URL}/api/user/change_password`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data,
      success: (res: any) => {
        console.log('修改密码响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          // 修改成功
          resolve(res.data.data);
        } else {
          // 修改失败
          reject(res.data.message || '修改密码失败');
        }
      },
      fail: (err) => {
        console.error('修改密码请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 获取用户订单列表API
export const getUserOrdersAPI = (params?: {status?: string; page?: number; per_page?: number}) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始获取用户订单列表请求');
    
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    // 手动构建查询参数
    const queryParts: string[] = [];
    if (params?.status) queryParts.push(`status=${encodeURIComponent(params.status)}`);
    if (params?.page) queryParts.push(`page=${params.page}`);
    if (params?.per_page) queryParts.push(`per_page=${params.per_page}`);
    
    const queryString = queryParts.length > 0 ? '?' + queryParts.join('&') : '';
    const url = `${API_BASE_URL}/api/user/orders${queryString}`;
    
    wx.request({
      url,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      success: (res: any) => {
        console.log('获取订单列表响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          // 获取成功
          resolve(res.data.data);
        } else {
          // 获取失败
          reject(res.data.message || '获取订单列表失败');
        }
      },
      fail: (err) => {
        console.error('获取订单列表请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 取消订单API
export const cancelOrderAPI = (data: {order_number: string; cancel_reason?: string}) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始取消订单请求');
    
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    wx.request({
      url: `${API_BASE_URL}/api/user/cancel_order`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data,
      success: (res: any) => {
        console.log('取消订单响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          // 取消成功
          resolve(res.data.data);
        } else {
          // 取消失败
          reject(res.data.message || '取消订单失败');
        }
      },
      fail: (err) => {
        console.error('取消订单请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 上报异常API
export const reportIssueAPI = (data: {order_number: string; issue_type: string; description?: string}) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始上报异常请求');
    
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    wx.request({
      url: `${API_BASE_URL}/api/user/report_issue`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data,
      success: (res: any) => {
        console.log('上报异常响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          // 上报成功
          resolve(res.data.data);
        } else {
          // 上报失败
          reject(res.data.message || '上报异常失败');
        }
      },
      fail: (err) => {
        console.error('上报异常请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 提交评价API
export const submitEvaluationAPI = (data: {order_number: string; rating: number; comment?: string}) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始提交评价请求');
    
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    wx.request({
      url: `${API_BASE_URL}/api/user/submit_evaluation`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data,
      success: (res: any) => {
        console.log('提交评价响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          // 提交成功
          resolve(res.data.data);
        } else {
          // 提交失败
          reject(res.data.message || '提交评价失败');
        }
      },
      fail: (err) => {
        console.error('提交评价请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 检查订单是否已评价API
export const checkEvaluationAPI = (orderNumber: string) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始检查评价请求');
    
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    wx.request({
      url: `${API_BASE_URL}/api/user/check_evaluation?order_number=${encodeURIComponent(orderNumber)}`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      success: (res: any) => {
        console.log('检查评价响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          // 检查成功
          resolve(res.data.data);
        } else {
          // 检查失败
          reject(res.data.message || '检查评价失败');
        }
      },
      fail: (err) => {
        console.error('检查评价请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 获取用户评价列表API
export const getUserEvaluationsAPI = (params: {page?: number; per_page?: number; status?: string}) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始获取评价列表请求');
    
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    // 构建查询参数
    const queryParts: string[] = [];
    if (params.page) queryParts.push(`page=${params.page}`);
    if (params.per_page) queryParts.push(`per_page=${params.per_page}`);
    if (params.status) queryParts.push(`status=${encodeURIComponent(params.status)}`);
    
    const url = `${API_BASE_URL}/api/user/evaluations${queryParts.length > 0 ? '?' + queryParts.join('&') : ''}`;
    
    wx.request({
      url,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      success: (res: any) => {
        console.log('获取评价列表响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          // 获取成功
          resolve(res.data.data);
        } else {
          // 获取失败
          reject(res.data.message || '获取评价列表失败');
        }
      },
      fail: (err) => {
        console.error('获取评价列表请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 获取优惠券包列表API
export const getCouponPackagesAPI = () => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始获取优惠券包请求');
    
    wx.request({
      url: `${API_BASE_URL}/api/coupon/packages`,
      method: 'GET',
      header: {
        'Content-Type': 'application/json'
      },
      success: (res: any) => {
        console.log('获取优惠券包响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          // 获取成功
          resolve(res.data.data);
        } else {
          // 获取失败
          reject(res.data.message || '获取优惠券包失败');
        }
      },
      fail: (err) => {
        console.error('获取优惠券包请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 购买优惠券包API
export const purchaseCouponPackageAPI = (data: {package_id: number; payment_method?: string}) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始购买优惠券包请求');
    
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    wx.request({
      url: `${API_BASE_URL}/api/coupon/purchase`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data,
      success: (res: any) => {
        console.log('购买优惠券包响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          // 购买成功
          resolve(res.data.data);
        } else {
          // 购买失败
          reject(res.data.message || '购买优惠券包失败');
        }
      },
      fail: (err) => {
        console.error('购买优惠券包请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 获取用户优惠券API
export const getUserCouponsAPI = (params?: {status?: string}) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始获取用户优惠券请求');
    
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    // 构建查询参数
    let queryString = '';
    if (params?.status) {
      queryString = `?status=${encodeURIComponent(params.status)}`;
    }
    
    wx.request({
      url: `${API_BASE_URL}/api/user/coupons${queryString}`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      success: (res: any) => {
        console.log('获取用户优惠券响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          // 获取成功
          resolve(res.data.data);
        } else {
          // 获取失败
          reject(res.data.message || '获取优惠券失败');
        }
      },
      fail: (err) => {
        console.error('获取用户优惠券请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 获取钱包交易记录API
export const getWalletTransactionsAPI = (params: {page?: number; per_page?: number; type?: string}) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始获取钱包交易记录请求');
    
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    // 构建查询参数
    const queryParts: string[] = [];
    if (params.page) queryParts.push(`page=${params.page}`);
    if (params.per_page) queryParts.push(`per_page=${params.per_page}`);
    if (params.type) queryParts.push(`type=${encodeURIComponent(params.type)}`);
    
    const url = `${API_BASE_URL}/api/user/wallet/transactions${queryParts.length > 0 ? '?' + queryParts.join('&') : ''}`;
    
    wx.request({
      url,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      success: (res: any) => {
        console.log('获取钱包交易记录响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          // 获取成功
          resolve(res.data.data);
        } else {
          // 获取失败
          reject(res.data.message || '获取交易记录失败');
        }
      },
      fail: (err) => {
        console.error('获取钱包交易记录请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 充值API
export const rechargeWalletAPI = (data: {amount: number; payment_method?: string}) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始充值请求');
    
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    wx.request({
      url: `${API_BASE_URL}/api/user/wallet/recharge`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data,
      success: (res: any) => {
        console.log('充值响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          // 充值成功
          resolve(res.data.data);
        } else {
          // 充值失败
          reject(res.data.message || '充值失败');
        }
      },
      fail: (err) => {
        console.error('充值请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 提现API
export const withdrawWalletAPI = (data: {amount: number; withdraw_method?: string}) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始提现请求');
    
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    wx.request({
      url: `${API_BASE_URL}/api/user/wallet/withdraw`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data,
      success: (res: any) => {
        console.log('提现响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          // 提现成功
          resolve(res.data.data);
        } else {
          // 提现失败
          reject(res.data.message || '提现失败');
        }
      },
      fail: (err) => {
        console.error('提现请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 获取用户统计数据API
export const getUserStatisticsAPI = () => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始获取用户统计数据请求');
    
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    wx.request({
      url: `${API_BASE_URL}/api/user/statistics`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      success: (res: any) => {
        console.log('获取用户统计数据响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          resolve(res.data.data);
        } else {
          reject(res.data.message || '获取统计数据失败');
        }
      },
      fail: (err) => {
        console.error('获取用户统计数据请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 获取用户订单趋势数据API
export const getUserOrderTrendAPI = (params?: {period?: string; limit?: number}) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始获取用户订单趋势数据请求');
    
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    // 构建查询参数
    const queryParts: string[] = [];
    if (params?.period) queryParts.push(`period=${params.period}`);
    if (params?.limit) queryParts.push(`limit=${params.limit}`);
    
    const url = `${API_BASE_URL}/api/user/statistics/order-trend${queryParts.length > 0 ? '?' + queryParts.join('&') : ''}`;
    
    wx.request({
      url,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      success: (res: any) => {
        console.log('获取用户订单趋势数据响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          resolve(res.data.data);
        } else {
          reject(res.data.message || '获取订单趋势数据失败');
        }
      },
      fail: (err) => {
        console.error('获取用户订单趋势数据请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 获取用户消费分析数据API
export const getUserSpendingAnalysisAPI = (params?: {period?: string}) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始获取用户消费分析数据请求');
    
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    // 构建查询参数
    const queryParts: string[] = [];
    if (params?.period) queryParts.push(`period=${params.period}`);
    
    const url = `${API_BASE_URL}/api/user/statistics/spending-analysis${queryParts.length > 0 ? '?' + queryParts.join('&') : ''}`;
    
    wx.request({
      url,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      success: (res: any) => {
        console.log('获取用户消费分析数据响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          resolve(res.data.data);
        } else {
          reject(res.data.message || '获取消费分析数据失败');
        }
      },
      fail: (err) => {
        console.error('获取用户消费分析数据请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 获取用户出行习惯分析API
export const getUserTravelHabitsAPI = (params?: {status?: string}) => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始获取用户出行习惯分析请求');
    
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    // 构建查询参数
    const queryParts: string[] = [];
    if (params?.status) queryParts.push(`status=${params.status}`);
    
    const url = `${API_BASE_URL}/api/user/statistics/travel-habits${queryParts.length > 0 ? '?' + queryParts.join('&') : ''}`;
    
    wx.request({
      url,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      success: (res: any) => {
        console.log('获取用户出行习惯分析响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          resolve(res.data.data);
        } else {
          reject(res.data.message || '获取出行习惯分析失败');
        }
      },
      fail: (err) => {
        console.error('获取用户出行习惯分析请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

// 获取订单价格预估接口参数类型
export interface OrderPriceEstimateParams {
  pickup_location: {
    latitude: number;
    longitude: number;
  };
  dropoff_location: {
    latitude: number;
    longitude: number;
  };
  city_code: string;
}

// 获取订单价格预估接口响应类型
export interface OrderPriceEstimateResponse {
  distance: number;
  base_amount: number;
  city_price_factor: number;
  min_vehicle_coefficient: number;
  max_vehicle_coefficient: number;
  min_price: number;
  max_price: number;
  price_range: string;
  pickup_coords: {
    x: number;
    y: number;
  };
  dropoff_coords: {
    x: number;
    y: number;
  };
  base_distance: number;  // 起步距离
  adjusted_base_price: number;  // 包含城市系数的起步价
  adjusted_price_per_km: number;  // 包含城市系数的每公里价格
}

// 获取订单价格预估
export const getOrderPriceEstimateAPI = (params: OrderPriceEstimateParams): Promise<OrderPriceEstimateResponse> => {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${API_BASE_URL}/api/order/price-estimate`,
      method: 'POST',
      header: {
        'Content-Type': 'application/json'
      },
      data: params,
      success: (res: any) => {
        if (res.statusCode === 200 && res.data.code === 0) {
          resolve(res.data.data);
        } else {
          reject(res.data.message || '获取价格预估失败');
        }
      },
      fail: (err) => {
        console.error('获取价格预估请求失败:', err);
        reject('网络请求失败');
      }
    });
  });
};

// 获取信用等级规则
export const getCreditLevelRulesAPI = () => {
  return new Promise<any>((resolve, reject) => {
    console.log('开始获取信用等级规则请求');
    
    // 获取token
    const app = getApp<IAppOption>();
    const token = app.globalData.token;
    
    if (!token) {
      reject('未登录，请先登录');
      return;
    }
    
    wx.request({
      url: `${API_BASE_URL}/api/credit_level_rules`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      success: (res: any) => {
        console.log('获取信用等级规则响应:', res.data);
        if (res.statusCode === 200 && res.data.code === 0) {
          resolve(res.data.data);
        } else {
          reject(res.data.message || '获取信用等级规则失败');
        }
      },
      fail: (err) => {
        console.error('获取信用等级规则请求失败:', err);
        reject('网络错误，请检查网络连接或后端服务是否启动');
      }
    });
  });
};

/* 
实际开发注意事项:
1. 小程序正式环境需要配置合法域名，否则无法进行网络请求
2. 可在微信开发者工具中勾选"不校验合法域名"进行本地开发测试
3. 上线前需要将API_BASE_URL更改为正式环境URL，并在小程序管理后台添加为合法域名
4. 微信小程序本地环境无法直接连接MySQL数据库，需要通过服务端API实现
*/