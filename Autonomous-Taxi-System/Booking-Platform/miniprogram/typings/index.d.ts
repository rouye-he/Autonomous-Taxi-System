// global.d.ts
interface IAppOption {
  globalData: {
    logs: number[];
    token: string;
    userInfo: UserInfo | null;
    defaultAvatarUrl: string;
  }
  userInfoReadyCallback?: WechatMiniprogram.GetUserInfoSuccessCallback
  restoreLoginState(): void;
}

// 定义用户信息接口 - 使用下划线命名风格与后端保持一致
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
  avatar_url?: string;  // 添加头像URL字段，与后端保持一致
  status?: string;
  [key: string]: any;  // 允许其他属性
} 