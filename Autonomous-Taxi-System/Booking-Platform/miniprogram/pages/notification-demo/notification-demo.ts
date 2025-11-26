import { notify } from '../../utils/notification';
import { request } from '../../utils/util';

Page({
  data: {},
  
  // 基础通知演示
  showSuccess() { notify.success('操作成功！'); },
  showError() { notify.error('操作失败！'); },
  showWarning() { notify.warning('请注意！'); },
  showInfo() { notify.info('提示信息'); },
  
  // 自定义组件通知演示
  showComponentSuccess() { notify.success('组件成功提示', 3000, true); },
  showComponentError() { notify.error('组件错误提示', 3000, true); },
  
  // 加载提示演示
  showLoading() {
    notify.loading('处理中...');
    setTimeout(() => {
      notify.hideLoading();
      notify.success('处理完成');
    }, 2000);
  },
  
  // 确认对话框演示
  async showConfirm() {
    const result = await notify.confirm('确定要执行此操作吗？', '确认');
    notify.info(result ? '用户确认' : '用户取消');
  },
  
  // 请求演示
  async testRequest() {
    try {
      await request({
        url: '/api/test',
        method: 'GET',
        showLoading: true,
        showError: true,
        loadingText: '测试请求中...'
      });
      notify.success('请求成功');
    } catch (error) {
      console.log('请求失败:', error);
    }
  }
}); 