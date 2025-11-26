import { fetchUserDetailInfo } from '../../utils/db';
import { request } from '../../utils/util';
import { notify } from '../../utils/notification';

interface Notification {
  notification_id: number;
  title: string;
  content: string;
  target_type: number;
  userid: number | null;
  is_read: number;
  is_deleted: number;
  read_time: string | null;
  create_time: string;
}

Page({
  data: {
    activeTab: 0,
    unreadNotifications: [] as Notification[],
    readNotifications: [] as Notification[],
    unreadCount: 0,
    readCount: 0,
    loading: false,
    hasMore: false,
    unreadPage: 1,
    readPage: 1,
    per_page: 20
  },

  onLoad() {
    console.log('页面加载，初始数据状态:', {
      activeTab: this.data.activeTab,
      unreadNotifications: this.data.unreadNotifications.length,
      readNotifications: this.data.readNotifications.length
    });
    this.loadNotifications();
  },

  onPullDownRefresh() {
    this.resetPagination();
    this.loadNotifications();
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      if (this.data.activeTab === 0) {
        this.loadMoreUnreadNotifications();
      } else {
        this.loadMoreReadNotifications();
      }
    }
  },

  resetPagination() {
    this.setData({
      unreadPage: 1,
      readPage: 1
    });
  },

  // 格式化时间
  formatTime(dateStr: string, isReadTime: boolean = false): string {
    if (!dateStr) return '';
    
    try {
      // 处理创建时间的相对显示
      const date = new Date(dateStr);
      
      // 检查日期是否有效
      if (isNaN(date.getTime())) {
        return dateStr;
      }
      
      // 对于通知创建时间，使用相对时间格式
      const now = new Date();
      const diff = now.getTime() - date.getTime();
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      
      if (days === 0) {
        return '今天';
      } else if (days === 1) {
        return '昨天';
      } else if (days < 7) {
        return `${days}天前`;
      } else {
        return date.toLocaleDateString('zh-CN', {
          month: '2-digit',
          day: '2-digit'
        });
      }
    } catch (error) {
      return dateStr;
    }
  },

  // 加载通知
  async loadNotifications() {
    try {
      this.setData({ loading: true });
      
      console.log('开始加载通知信息...');
      
      // 获取未读通知和已读通知
      const [unreadRes, readRes] = await Promise.all([
        this.getNotifications(0, this.data.unreadPage),
        this.getNotifications(1, this.data.readPage)
      ]);
      
      console.log('未读通知数量:', unreadRes.data ? unreadRes.data.length : 0);
      console.log('已读通知数量:', readRes.data ? readRes.data.length : 0);
      
      // 检查已读通知中的read_time字段
      if (readRes.data && readRes.data.length > 0) {
        console.log('已读通知中的第一条:', readRes.data[0]);
        console.log('已读通知中的read_time字段:', readRes.data[0].read_time);
      }

      this.setData({
        unreadNotifications: unreadRes.data || [],
        readNotifications: readRes.data || [],
        unreadCount: unreadRes.pagination ? unreadRes.pagination.total : 0,
        readCount: readRes.pagination ? readRes.pagination.total : 0,
        hasMore: this.data.activeTab === 0 ? 
          (unreadRes.pagination ? unreadRes.pagination.has_next : false) : 
          (readRes.pagination ? readRes.pagination.has_next : false)
      });
      
      console.log('数据设置完成');
    } catch (error) {
      console.error('加载通知信息失败:', error);
      notify.error('加载失败，请重试');
      
      // 设置默认数据
      this.setData({
        unreadNotifications: [],
        readNotifications: [],
        unreadCount: 0,
        readCount: 0,
        hasMore: false
      });
    } finally {
      this.setData({ loading: false });
      wx.stopPullDownRefresh();
    }
  },

  // 加载更多未读通知
  async loadMoreUnreadNotifications() {
    if (this.data.loading || !this.data.hasMore) return;
    
    try {
      this.setData({ loading: true });
      
      const nextPage = this.data.unreadPage + 1;
      const moreUnreadRes = await this.getNotifications(0, nextPage);
      
      this.setData({
        unreadNotifications: [...this.data.unreadNotifications, ...(moreUnreadRes.data || [])],
        hasMore: moreUnreadRes.pagination ? moreUnreadRes.pagination.has_next : false,
        unreadPage: nextPage
      });
    } catch (error) {
      notify.error('加载更多失败');
      console.error('加载更多未读通知失败:', error);
    } finally {
      this.setData({ loading: false });
    }
  },

  // 加载更多已读通知
  async loadMoreReadNotifications() {
    if (this.data.loading || !this.data.hasMore) return;
    
    try {
      this.setData({ loading: true });
      
      const nextPage = this.data.readPage + 1;
      const moreReadRes = await this.getNotifications(1, nextPage);
      
      this.setData({
        readNotifications: [...this.data.readNotifications, ...(moreReadRes.data || [])],
        hasMore: moreReadRes.pagination ? moreReadRes.pagination.has_next : false,
        readPage: nextPage
      });
    } catch (error) {
      notify.error('加载更多失败');
      console.error('加载更多已读通知失败:', error);
    } finally {
      this.setData({ loading: false });
    }
  },

  // 获取通知列表
  async getNotifications(isRead: number, page: number = 1): Promise<any> {
    try {
      const url = `/api/user/notifications`;
      const res = await request({
        url,
        method: 'GET',
        data: {
          is_read: isRead,
          page,
          per_page: this.data.per_page
        }
      });
      
      return res;
    } catch (error) {
      console.error('获取通知列表失败:', error);
      throw error;
    }
  },

  // 标记通知为已读
  async markAsRead(e: any) {
    const notificationId = e.currentTarget.dataset.id;
    
    try {
      this.setData({ loading: true });
      
      // 调用API标记为已读
      const url = `/api/user/notifications/${notificationId}/read`;
      await request({
        url,
        method: 'PUT'
      });
      
      // 更新本地数据
      const notification = this.data.unreadNotifications.find(item => item.notification_id === notificationId);
      if (notification) {
        notification.is_read = 1;
        const now = new Date();
        notification.read_time = now.toISOString();
        console.log('设置read_time为:', notification.read_time);
        
        this.setData({
          unreadNotifications: this.data.unreadNotifications.filter(item => item.notification_id !== notificationId),
          readNotifications: [notification, ...this.data.readNotifications],
          unreadCount: Math.max(0, this.data.unreadCount - 1),
          readCount: this.data.readCount + 1
        });
        
        // 显示时间作为提示
        notify.success(`已标记为已读: ${this.formatTime(notification.read_time, true)}`);
        console.log('添加到已读列表的通知:', notification);
      }
    } catch (error) {
      console.error('标记通知为已读失败:', error);
      notify.error('操作失败，请重试');
    } finally {
      this.setData({ loading: false });
    }
  },

  // 标记所有为已读
  async markAllAsRead() {
    try {
      this.setData({ loading: true });
      
      // 调用API标记所有为已读
      const url = `/api/user/notifications/read-all`;
      await request({
        url,
        method: 'PUT'
      });
      
      // 重新加载数据
      this.resetPagination();
      this.loadNotifications();
      
      notify.success('已全部标记为已读');
    } catch (error) {
      console.error('标记所有通知为已读失败:', error);
      notify.error('操作失败，请重试');
    } finally {
      this.setData({ loading: false });
    }
  },

  // 切换标签页
  onTabChange(e: any) {
    const index = Number(e.currentTarget.dataset.index);
    if (this.data.activeTab === index) return;
    
    this.setData({ 
      activeTab: index,
      hasMore: index === 0 ? 
        this.data.unreadNotifications.length < this.data.unreadCount : 
        this.data.readNotifications.length < this.data.readCount
    });
  },

  // 返回上一页
  onBack() {
    wx.navigateBack();
  }
}); 