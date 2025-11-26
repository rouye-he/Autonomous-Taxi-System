// 引入API函数
import { changePasswordAPI } from '../../utils/db';

Page({
  data: {
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
    oldPasswordError: '',
    newPasswordError: '',
    confirmPasswordError: '',
    formError: '',
    loading: false
  },
  
  // 原密码输入处理
  onOldPasswordInput(e: any) {
    this.setData({
      oldPassword: e.detail.value,
      oldPasswordError: '',
      formError: ''
    });
  },
  
  // 新密码输入处理
  onNewPasswordInput(e: any) {
    this.setData({
      newPassword: e.detail.value,
      newPasswordError: '',
      formError: ''
    });
  },
  
  // 确认密码输入处理
  onConfirmPasswordInput(e: any) {
    this.setData({
      confirmPassword: e.detail.value,
      confirmPasswordError: '',
      formError: ''
    });
  },
  
  // 验证表单
  validateForm(): boolean {
    let isValid = true;
    
    // 验证原密码
    if (!this.data.oldPassword.trim()) {
      this.setData({ oldPasswordError: '请输入原密码' });
      isValid = false;
    }
    
    // 验证新密码
    if (!this.data.newPassword.trim()) {
      this.setData({ newPasswordError: '请输入新密码' });
      isValid = false;
    } else if (this.data.newPassword.length < 6) {
      this.setData({ newPasswordError: '新密码长度不能少于6位' });
      isValid = false;
    }
    
    // 验证确认密码
    if (!this.data.confirmPassword.trim()) {
      this.setData({ confirmPasswordError: '请再次输入新密码' });
      isValid = false;
    } else if (this.data.newPassword !== this.data.confirmPassword) {
      this.setData({ confirmPasswordError: '两次输入的密码不一致' });
      isValid = false;
    }
    
    return isValid;
  },
  
  // 提交处理
  handleSubmit() {
    // 表单验证
    if (!this.validateForm()) return;
    
    // 防止重复提交
    if (this.data.loading) return;
    
    this.setData({ loading: true });
    
    // 调用修改密码API
    changePasswordAPI({
      oldPassword: this.data.oldPassword,
      newPassword: this.data.newPassword
    }).then(() => {
      // 修改成功
      wx.showToast({
        title: '密码修改成功',
        icon: 'success',
        duration: 2000
      });
      
      // 2秒后返回上一页
      setTimeout(() => {
        wx.navigateBack();
      }, 2000);
    }).catch((error) => {
      // 修改失败
      this.setData({
        formError: error || '修改密码失败，请稍后重试',
        loading: false
      });
    });
  }
}); 