import { login, sendVerifyCode, loginByCode } from '../../utils/db';

Component({
  data: {
    loginType: 'password', // 登录方式：password-密码登录，code-验证码登录
    email: '',
    password: '',
    verifyCode: '',
    emailError: '',
    passwordError: '',
    verifyCodeError: '',
    loginError: '',
    loading: false,
    codeSending: false,
    countdown: 0,
    timer: null as any
  },
  
  methods: {
    // 切换登录方式
    switchLoginType(e: any) {
      const type = e.currentTarget.dataset.type;
      this.setData({
        loginType: type,
        loginError: ''
      });
    },
    
    // 邮箱输入处理
    onEmailInput(e: any) {
      this.setData({
        email: e.detail.value,
        emailError: '',
        loginError: ''
      });
    },
    
    // 密码输入处理
    onPasswordInput(e: any) {
      this.setData({
        password: e.detail.value,
        passwordError: '',
        loginError: ''
      });
    },
    
    // 验证码输入处理
    onVerifyCodeInput(e: any) {
      this.setData({
        verifyCode: e.detail.value,
        verifyCodeError: '',
        loginError: ''
      });
    },
    
    // 发送验证码
    sendVerifyCode() {
      // 验证邮箱
      if (!this.validateEmail()) return;
      
      this.setData({ codeSending: true });
      
      // 调用发送验证码API
      sendVerifyCode(this.data.email)
        .then(() => {
          // 发送成功，开始倒计时
          this.startCountdown();
          wx.showToast({
            title: '验证码已发送',
            icon: 'success'
          });
        })
        .catch((error) => {
          this.setData({
            codeSending: false,
            loginError: error
          });
        });
    },
    
    // 开始倒计时
    startCountdown() {
      // 设置60秒倒计时
      this.setData({
        countdown: 60,
        codeSending: false
      });
      
      // 清除可能存在的定时器
      if (this.data.timer) {
        clearInterval(this.data.timer);
      }
      
      // 创建新的定时器
      const timer = setInterval(() => {
        if (this.data.countdown <= 1) {
          clearInterval(timer);
          this.setData({ countdown: 0 });
        } else {
          this.setData({ countdown: this.data.countdown - 1 });
        }
      }, 1000);
      
      this.setData({ timer });
    },
    
    // 表单验证
    validateForm(): boolean {
      if (this.data.loginType === 'password') {
        return this.validateEmail() && this.validatePassword();
      } else {
        return this.validateEmail() && this.validateVerifyCode();
      }
    },
    
    // 验证邮箱
    validateEmail(): boolean {
      if (!this.data.email.trim()) {
        this.setData({ emailError: '请输入邮箱' });
        return false;
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.data.email)) {
        this.setData({ emailError: '请输入有效的邮箱地址' });
        return false;
      }
      return true;
    },
    
    // 验证密码
    validatePassword(): boolean {
      if (!this.data.password.trim()) {
        this.setData({ passwordError: '请输入密码' });
        return false;
      }
      return true;
    },
    
    // 验证验证码
    validateVerifyCode(): boolean {
      if (!this.data.verifyCode.trim()) {
        this.setData({ verifyCodeError: '请输入验证码' });
        return false;
      } else if (!/^\d{6}$/.test(this.data.verifyCode)) {
        this.setData({ verifyCodeError: '请输入6位数字验证码' });
        return false;
      }
      return true;
    },
    
    // 登录处理
    handleLogin() {
      // 表单验证
      if (!this.validateForm()) return;
      
      this.setData({ loading: true });
      
      // 根据登录方式调用不同的登录API
      const loginPromise = this.data.loginType === 'password'
        ? login({ email: this.data.email, password: this.data.password })
        : loginByCode({ email: this.data.email, verifyCode: this.data.verifyCode });
      
      loginPromise.then((data) => {
        // 登录成功，跳转到首页
        this.setData({ loading: false });
        wx.showToast({
          title: '登录成功',
          icon: 'success',
          duration: 1500
        });
        
        // 延迟跳转，让用户看到成功提示
        setTimeout(() => {
          wx.reLaunch({
            url: '/pages/index/index'
          });
        }, 1500);
      }).catch((error) => {
        // 登录失败，显示错误信息
        this.setData({
          loading: false,
          loginError: error
        });
      });
    },
    
    // 导航到注册页面
    navigateToRegister() {
      wx.navigateTo({
        url: '/pages/register/register'
      });
    }
  },
  
  // 组件生命周期
  lifetimes: {
    // 组件卸载时清除定时器
    detached() {
      if (this.data.timer) {
        clearInterval(this.data.timer);
      }
    },
    
    // 页面加载时检查是否已登录
    attached() {
      // 检查是否已登录，如已登录则跳转到首页
      const token = wx.getStorageSync('token');
      if (token) {
        wx.reLaunch({
          url: '/pages/index/index'
        });
      }
    }
  }
}); 