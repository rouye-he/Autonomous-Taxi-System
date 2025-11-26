import { register } from '../../utils/db';
import { sendVerifyCode, verifyCode } from '../../utils/sms';

Component({
  data: {
    username: '',
    password: '',
    email: '',
    verifyCode: '',
    cityList: ['沈阳市', '上海市', '北京市', '广州市', '深圳市', '杭州市', '南京市', '成都市', '重庆市', '武汉市', '西安市'],
    cityIndex: -1,
    selectedCity: '',
    usernameError: '',
    passwordError: '',
    emailError: '',
    verifyCodeError: '',
    cityError: '',
    registerError: '',
    loading: false,
    statusBarHeight: 0,
    codeSending: false,
    codeButtonText: '获取验证码',
    countdown: 60
  },
  
  lifetimes: {
    attached() {
      // 获取状态栏高度
      const systemInfo = wx.getSystemInfoSync();
      this.setData({
        statusBarHeight: systemInfo.statusBarHeight
      });
    }
  },
  
  methods: {
    // 用户名输入处理
    onUsernameInput(e: any) {
      this.setData({
        username: e.detail.value,
        usernameError: '',
        registerError: ''
      });
    },
    
    // 密码输入处理
    onPasswordInput(e: any) {
      this.setData({
        password: e.detail.value,
        passwordError: '',
        registerError: ''
      });
    },
    
    // 邮箱输入处理
    onEmailInput(e: any) {
      this.setData({
        email: e.detail.value,
        emailError: '',
        registerError: ''
      });
    },
    
    // 验证码输入处理
    onVerifyCodeInput(e: any) {
      this.setData({
        verifyCode: e.detail.value,
        verifyCodeError: '',
        registerError: ''
      });
    },
    
    // 城市选择处理
    onCityChange(e: any) {
      const index = e.detail.value;
      this.setData({
        cityIndex: index,
        selectedCity: this.data.cityList[index],
        cityError: '',
        registerError: ''
      });
    },
    
    // 发送验证码
    sendVerifyCode() {
      // 如果正在发送验证码，直接返回
      if (this.data.codeSending) {
        return;
      }
      
      // 验证邮箱
      const email = this.data.email.trim();
      if (!email) {
        this.setData({ emailError: '请输入邮箱' });
        return;
      }
      
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        this.setData({ emailError: '请输入正确的邮箱格式' });
        return;
      }
      
      // 开始发送验证码
      this.setData({ 
        codeSending: true,
        codeButtonText: '发送中...'
      });
      
      sendVerifyCode(email).then((res) => {
        // 发送成功，开始倒计时
        wx.showToast({
          title: '验证码已发送',
          icon: 'success'
        });
        
        this.startCountdown();
      }).catch((err) => {
        // 发送失败
        this.setData({ 
          codeSending: false,
          codeButtonText: '获取验证码',
          verifyCodeError: '验证码发送失败，请重试'
        });
      });
    },
    
    // 开始倒计时
    startCountdown() {
      this.setData({
        countdown: 60,
        codeButtonText: '60秒后重发',
        codeSending: true
      });
      
      const timer = setInterval(() => {
        const countdown = this.data.countdown - 1;
        
        if (countdown <= 0) {
          // 倒计时结束
          clearInterval(timer);
          this.setData({
            codeButtonText: '获取验证码',
            codeSending: false
          });
        } else {
          // 更新倒计时
          this.setData({
            countdown,
            codeButtonText: `${countdown}秒后重发`
          });
        }
      }, 1000);
    },
    
    // 表单验证
    validateForm(): boolean {
      let isValid = true;
      
      // 用户名验证
      if (!this.data.username.trim()) {
        this.setData({ usernameError: '请输入用户名' });
        isValid = false;
      }
      
      // 密码验证
      if (!this.data.password.trim()) {
        this.setData({ passwordError: '请输入密码' });
        isValid = false;
      } else if (this.data.password.length < 6) {
        this.setData({ passwordError: '密码长度不能少于6位' });
        isValid = false;
      }
      
      // 邮箱验证
      if (!this.data.email.trim()) {
        this.setData({ emailError: '请输入邮箱' });
        isValid = false;
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.data.email)) {
        this.setData({ emailError: '请输入正确的邮箱格式' });
        isValid = false;
      }
      
      // 验证码验证
      if (!this.data.verifyCode.trim()) {
        this.setData({ verifyCodeError: '请输入验证码' });
        isValid = false;
      } else if (this.data.verifyCode.length !== 6) {
        this.setData({ verifyCodeError: '验证码应为6位数字' });
        isValid = false;
      }
      
      // 城市验证
      if (this.data.cityIndex === -1) {
        this.setData({ cityError: '请选择注册城市' });
        isValid = false;
      }
      
      return isValid;
    },
    
    // 注册处理
    handleRegister() {
      // 表单验证
      if (!this.validateForm()) return;
      
      this.setData({ loading: true });
      
      // 调用注册API
      register({
        username: this.data.username,
        password: this.data.password,
        email: this.data.email,
        registration_city: this.data.selectedCity,
        verifyCode: this.data.verifyCode
      }).then(() => {
        // 注册成功
        this.setData({ loading: false });
        wx.showToast({
          title: '注册成功',
          icon: 'success',
          duration: 1500
        });
        
        // 延迟跳转到登录页
        setTimeout(() => {
          wx.navigateBack();
        }, 1500);
      }).catch((error) => {
        // 注册失败
        this.setData({
          loading: false,
          registerError: error
        });
      });
    },
    
    // 导航回登录页
    navigateToLogin() {
      wx.navigateBack();
    }
  }
}); 