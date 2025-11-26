import { fetchUserDetailInfo } from '../../utils/db';

interface FormData {
  username: string;
  real_name: string;
  email: string;
  gender: string;
  birth_date: string;
}

Page({
  data: {
    formData: {
      username: '',
      real_name: '',
      email: '',
      gender: '',
      birth_date: ''
    } as FormData,
    genderOptions: ['男', '女', '其他'],
    genderIndex: -1,
    isSubmitting: false
  },

  onLoad() {
    this.loadUserInfo();
  },

  // 加载用户信息
  loadUserInfo() {
    fetchUserDetailInfo()
      .then((userInfo: any) => {
        const genderIndex = this.data.genderOptions.indexOf(userInfo.gender || '');
        this.setData({
          formData: {
            username: userInfo.username || '',
            real_name: userInfo.real_name || '',
            email: userInfo.email || '',
            gender: userInfo.gender || '',
            birth_date: userInfo.birth_date || ''
          },
          genderIndex: genderIndex >= 0 ? genderIndex : -1
        });
      })
      .catch((error) => {
        console.error('获取用户信息失败:', error);
        wx.showToast({
          title: '获取用户信息失败',
          icon: 'none'
        });
      });
  },

  // 输入框变化
  onInputChange(e: any) {
    const field = e.currentTarget.dataset.field;
    const value = e.detail.value;
    this.setData({
      [`formData.${field}`]: value
    });
  },

  // 性别选择
  onGenderChange(e: any) {
    const index = e.detail.value;
    this.setData({
      genderIndex: index,
      'formData.gender': this.data.genderOptions[index]
    });
  },

  // 日期选择
  onDateChange(e: any) {
    this.setData({
      'formData.birth_date': e.detail.value
    });
  },

  // 提交表单
  handleSubmit() {
    if (this.data.isSubmitting) return;

    // 验证表单
    if (!this.validateForm()) return;

    this.setData({ isSubmitting: true });

    // 调用更新用户信息API
    this.updateUserProfile()
      .then(() => {
        wx.showToast({
          title: '保存成功',
          icon: 'success'
        });
        setTimeout(() => {
          wx.navigateBack();
        }, 1500);
      })
      .catch((error) => {
        console.error('保存失败:', error);
        wx.showToast({
          title: error || '保存失败',
          icon: 'none'
        });
      })
      .finally(() => {
        this.setData({ isSubmitting: false });
      });
  },

  // 验证表单
  validateForm(): boolean {
    const { username, email } = this.data.formData;

    if (!username.trim()) {
      wx.showToast({
        title: '请输入用户名',
        icon: 'none'
      });
      return false;
    }

    if (email && !this.isValidEmail(email)) {
      wx.showToast({
        title: '请输入正确的邮箱格式',
        icon: 'none'
      });
      return false;
    }

    return true;
  },

  // 验证邮箱格式
  isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  },

  // 更新用户信息
  updateUserProfile(): Promise<any> {
    return new Promise((resolve, reject) => {
      const app = getApp<IAppOption>();
      const token = app.globalData.token;
      
      if (!token) {
        reject('未登录，请先登录');
        return;
      }

      wx.request({
        url: 'http://localhost:5001/api/user/update_profile',
        method: 'POST',
        header: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        data: this.data.formData,
        success: (res: any) => {
          console.log('更新用户信息响应:', res.data);
          if (res.statusCode === 200 && res.data.code === 0) {
            resolve(res.data.data);
          } else {
            reject(res.data.message || '更新失败');
          }
        },
        fail: (err) => {
          console.error('更新用户信息请求失败:', err);
          reject('网络错误，请检查网络连接');
        }
      });
    });
  }
}); 