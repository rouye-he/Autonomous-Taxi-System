import { submitEvaluationAPI, checkLoginStatus, checkEvaluationAPI } from '../../utils/db'; // 导入API函数

Page({
  data: {
    orderNumber: '',
    rating: 0,
    comment: '',
    submitting: false,
    hasEvaluated: false,
    existingEvaluation: null as any
  },
  
  async onLoad(options: any) {
    // 检查登录状态
    if (!checkLoginStatus()) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
      return;
    }
    
    // 获取订单号
    const orderNumber = options.orderNumber;
    if (!orderNumber) {
      wx.showToast({
        title: '订单号不能为空',
        icon: 'none'
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
      return;
    }
    
    this.setData({
      orderNumber
    });
    
    // 检查是否已经评价过
    await this.checkExistingEvaluation(orderNumber);
  },
  
  // 检查是否已经评价过
  async checkExistingEvaluation(orderNumber: string) {
    try {
      const result = await checkEvaluationAPI(orderNumber);
      
      if (result.has_evaluated) {
        this.setData({
          hasEvaluated: true,
          existingEvaluation: result.evaluation
        });
        
        wx.showModal({
          title: '已评价',
          content: `您已经对此订单评价过了（${result.evaluation.rating}星）。每个订单只能评价一次。`,
          showCancel: true,
          cancelText: '返回',
          confirmText: '查看评价',
          success: (res) => {
            if (res.cancel) {
              wx.navigateBack();
            } else {
              // 显示已有评价
              this.setData({
                rating: result.evaluation.rating,
                comment: result.evaluation.comment || ''
              });
            }
          }
        });
      }
    } catch (error) {
      console.error('检查评价失败:', error);
      // 检查失败不阻止用户继续，可能是网络问题
    }
  },
  
  // 点击星星评分
  onStarTap(e: any) {
    if (this.data.hasEvaluated) {
      wx.showToast({
        title: '该订单已评价过',
        icon: 'none'
      });
      return;
    }
    
    const rating = parseInt(e.currentTarget.dataset.rating);
    this.setData({
      rating
    });
  },
  
  // 输入评价内容
  onCommentInput(e: any) {
    if (this.data.hasEvaluated) {
      wx.showToast({
        title: '该订单已评价过',
        icon: 'none'
      });
      return;
    }
    
    this.setData({
      comment: e.detail.value
    });
  },
  
  // 提交评价
  async onSubmit() {
    if (this.data.submitting || this.data.hasEvaluated) return;
    
    // 验证评分
    if (this.data.rating === 0) {
      wx.showToast({
        title: '请选择评分',
        icon: 'none'
      });
      return;
    }
    
    try {
      this.setData({ submitting: true });
      
      wx.showLoading({
        title: '提交中...',
        mask: true
      });
      
      const result = await submitEvaluationAPI({
        order_number: this.data.orderNumber,
        rating: this.data.rating,
        comment: this.data.comment.trim()
      });
      
      wx.hideLoading();
      
      wx.showModal({
        title: '评价成功',
        content: '感谢您的评价！您的反馈对我们很重要。',
        showCancel: false,
        confirmText: '确定',
        success: () => {
          // 提交成功后返回上一页
          wx.navigateBack();
        }
      });
      
      console.log('评价提交成功:', result);
    } catch (error) {
      wx.hideLoading();
      console.error('提交评价失败:', error);
      
      wx.showModal({
        title: '提交失败',
        content: typeof error === 'string' ? error : '提交评价失败，请稍后重试',
        showCancel: false,
        confirmText: '知道了'
      });
    } finally {
      this.setData({ submitting: false });
    }
  }
}) 