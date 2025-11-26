/**
 * 订单表格组件
 * 扩展通用数据表格组件，处理订单特有的功能
 */

class OrderTable extends DataTable {
    /**
     * 创建订单表格组件
     * @param {Object} options - 配置选项
     */
    constructor(options) {
        // 默认配置
        const defaultOptions = {
            tableContainer: '.order-table-container',
            baseUrl: '/orders',
            statsElements: {
                total: 'totalOrderCount',
                waiting: 'waitingOrderCount',
                in_progress: 'inProgressOrderCount',
                completed: 'completedOrderCount',
                cancelled: 'cancelledOrderCount'
            }
        };
        
        // 合并默认配置和用户配置
        super(Object.assign({}, defaultOptions, options));
        
        // 初始化订单特有事件
        this.initViewOrderHandlers();
        this.initAssignVehicleHandlers();
        this.initCancelOrderHandlers();
        this.initEditOrderHandlers();
        this.initViewRatingHandlers();
        this.initViewToggle();
    }
    
    /**
     * 初始化查看订单详情事件处理
     */
    initViewOrderHandlers() {
        const self = this;
        
        // 为所有查看详情按钮添加事件监听（同时处理表格和卡片视图）
        document.querySelectorAll('.view-order-btn').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const orderId = this.getAttribute('data-order-id');
                self.viewOrderDetails(orderId);
            });
        });
    }
    
    /**
     * 初始化分配车辆事件处理
     */
    initAssignVehicleHandlers() {
        const self = this;
        
        // 为所有分配车辆按钮添加事件监听（同时处理表格和卡片视图）
        document.querySelectorAll('.assign-vehicle-btn').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const orderId = this.getAttribute('data-order-id');
                const cityCode = this.getAttribute('data-city-code');
                self.showAssignVehicleModal(orderId, cityCode);
            });
        });
    }
    
    /**
     * 初始化取消订单事件处理
     */
    initCancelOrderHandlers() {
        const self = this;
        
        // 为所有取消订单按钮添加事件监听
        document.querySelectorAll('.cancel-order-btn').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const orderId = this.getAttribute('data-order-id');
                self.showCancelOrderModal(orderId);
            });
        });
    }
    
    /**
     * 初始化编辑订单事件处理
     */
    initEditOrderHandlers() {
        const self = this;
        
        // 为所有编辑订单按钮添加事件监听
        document.querySelectorAll('.edit-order-btn').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const orderId = this.getAttribute('data-order-id');
                self.showEditOrderModal(orderId);
            });
        });
    }
    
    /**
     * 初始化查看评价事件处理
     */
    initViewRatingHandlers() {
        const self = this;
        
        // 为所有查看评价按钮添加事件监听
        document.querySelectorAll('.view-rating-btn, .view-cancel-reason-btn').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const orderId = this.getAttribute('data-order-id');
                if (this.classList.contains('view-rating-btn')) {
                    self.viewOrderRating(orderId);
                } else {
                    self.viewCancelReason(orderId);
                }
            });
        });
    }
    
    /**
     * 初始化视图切换功能
     */
    initViewToggle() {
        // 处理视图切换按钮点击事件
        document.querySelectorAll('.view-toggle-btn').forEach(button => {
            button.addEventListener('click', function() {
                const viewType = this.getAttribute('data-view');
                this.classList.add('active');
                
                if (viewType === 'table') {
                    document.getElementById('tableView').style.display = 'block';
                    document.getElementById('cardView').style.display = 'none';
                    document.querySelector('.view-toggle-btn[data-view="card"]').classList.remove('active');
                } else {
                    document.getElementById('tableView').style.display = 'none';
                    document.getElementById('cardView').style.display = 'block';
                    document.querySelector('.view-toggle-btn[data-view="table"]').classList.remove('active');
                }
                
                // 保存用户偏好到本地存储
                localStorage.setItem('orderViewPreference', viewType);
            });
        });
        
        // 初始化时根据用户偏好设置视图
        const savedView = localStorage.getItem('orderViewPreference');
        if (savedView) {
            document.querySelector(`.view-toggle-btn[data-view="${savedView}"]`).click();
        }
    }
    
    /**
     * 查看订单详情
     * @param {string} orderId - 订单ID
     */
    viewOrderDetails(orderId) {
        if (!orderId) return;
        
        // 调用原有的查看订单详情函数
        if (typeof window.viewOrderDetails === 'function') {
            window.viewOrderDetails(orderId);
        } 
    }
    
    /**
     * 显示分配车辆模态框
     * @param {string} orderId - 订单ID
     * @param {string} cityCode - 城市代码
     */
    showAssignVehicleModal(orderId, cityCode) {
        if (!orderId) return;
        
        // 调用原有的分配车辆函数
        if (typeof window.showAssignVehicleModal === 'function') {
            window.showAssignVehicleModal(orderId, cityCode);
        }
    }
    
    /**
     * 显示取消订单模态框
     * @param {string} orderId - 订单ID
     */
    showCancelOrderModal(orderId) {
        if (!orderId) return;
        
        // 获取订单信息，填充模态框
        fetch(`/orders/api/order_details/${orderId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`请求失败: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    const order = data.data;
                    
                    // 将订单ID存储在隐藏字段中
                    document.getElementById('cancelOrderId').value = orderId;
                    
                    // 显示订单号
                    document.getElementById('cancelOrderNumber').textContent = order.order_number;
                    
                    // 显示模态框
                    const modal = new bootstrap.Modal(document.getElementById('cancelOrderModal'));
                    modal.show();
                    
                    // 初始化确认删除按钮点击事件（仅初始化一次）
                    if (!this._cancelOrderListenersInitialized) {
                        document.getElementById('confirmCancelOrderBtn').addEventListener('click', () => {
                            this._submitCancelOrder();
                        });
                        
                        this._cancelOrderListenersInitialized = true;
                    }
                } 
            })
            .catch(error => {
                console.error('获取订单详情出错:', error);
            });
    }
    
    /**
     * 提交取消订单请求
     * @private
     */
    _submitCancelOrder() {
        // 获取订单ID
        const orderId = document.getElementById('cancelOrderId').value;
        
        // 禁用确认按钮，防止重复提交
        const confirmBtn = document.getElementById('confirmCancelOrderBtn');
        const originalBtnHtml = confirmBtn.innerHTML;
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i> 处理中...';
        
        // 发送取消订单请求
        fetch('/orders/api/cancel_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                order_id: orderId
            })
        })
        .then(response => response.json())
        .then(data => {
            // 隐藏模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('cancelOrderModal'));
            modal.hide();
            
            if (data.status === 'success') {
                // 显示成功消息
                
                // 重新加载表格数据
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                // 显示错误消息
               
                // 重置按钮状态
                confirmBtn.disabled = false;
                confirmBtn.innerHTML = originalBtnHtml;
            }
        })
        .catch(error => {
            console.error('删除订单出错:', error);
            
            // 重置按钮状态
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = originalBtnHtml;
        });
    }
    
    /**
     * 显示编辑订单模态框
     * @param {string} orderId - 订单ID
     */
    showEditOrderModal(orderId) {
        // 功能预留
    }
    
    /**
     * 查看订单评价
     * @param {string} orderId - 订单ID
     */
    viewOrderRating(orderId) {
        // 功能预留
    }
    
    /**
     * 查看取消原因
     * @param {string} orderId - 订单ID
     */
    viewCancelReason(orderId) {
        // 功能预留

    }
    
    /**
     * 重写initRowEvents方法，提供给DataTable使用
     */
    initRowEvents() {
        this.initViewOrderHandlers();
        this.initAssignVehicleHandlers();
        this.initCancelOrderHandlers();
        this.initEditOrderHandlers();
        this.initViewRatingHandlers();
    }
}

// 确保文档加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 创建订单表格实例并存储为全局变量
    window.orderTable = new OrderTable({
        initRowEvents: function() {
            window.orderTable.initRowEvents();
        }
    });
}); 