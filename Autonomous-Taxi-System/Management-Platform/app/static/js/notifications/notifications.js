/**
 * 系统通知管理页面脚本
 */

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log("通知页面初始化开始 - 模块化版本 - 2023-05-01");
    
    // 检查DOM元素是否存在
    console.log("DOM元素检查:", {
        "标记已读按钮": document.querySelectorAll('.mark-read-btn').length + " 个",
        "删除按钮": document.querySelectorAll('.delete-notification-btn').length + " 个",
        "查看按钮": document.querySelectorAll('.view-notification-btn').length + " 个"
    });
    
    // 初始化Tooltip
        try {
            initTooltips();
            console.log("Tooltips初始化完成");
        } catch (e) {
            console.error("初始化Tooltips失败:", e);
    }
    
    // 初始化通知详情查看
    try {
        initNotificationView();
        console.log("通知详情查看初始化完成");
    } catch (e) {
        console.error("初始化通知详情查看失败:", e);
    }
    
    // 初始化删除筛选结果按钮
    try {
        initDeleteFilteredBtn();
        console.log("删除筛选结果按钮初始化完成");
    } catch (e) {
        console.error("初始化删除筛选结果按钮失败:", e);
    }
});

/**
 * 初始化Tooltip组件
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover'
        });
    });
}

/**
 * 初始化通知详情查看
 */
function initNotificationView() {
    document.querySelectorAll('.view-notification-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            const title = this.getAttribute('data-title');
            const content = this.getAttribute('data-content');
            const type = this.getAttribute('data-type');
            const priority = this.getAttribute('data-priority');
            const status = this.getAttribute('data-status');
            const createdAt = this.getAttribute('data-created-at');
            const readAt = this.getAttribute('data-read-at');
            
            // 填充模态框
            document.getElementById('notificationTitle').textContent = title;
            document.getElementById('notificationContent').textContent = content;
            document.getElementById('notificationType').textContent = type;
            document.getElementById('notificationPriority').textContent = priority;
            document.getElementById('notificationStatus').textContent = status;
            document.getElementById('notificationCreatedAt').textContent = createdAt;
            document.getElementById('notificationReadAt').textContent = readAt || '未读';
            
            // 设置标记按钮
            const markReadBtn = document.getElementById('markAsReadBtn');
            if (markReadBtn) {
                // 清除之前的事件监听器，防止重复绑定
                const newMarkReadBtn = markReadBtn.cloneNode(true);
                markReadBtn.parentNode.replaceChild(newMarkReadBtn, markReadBtn);
                
                newMarkReadBtn.setAttribute('data-id', id);
                
                // 如果已读，禁用按钮
                if (status === '已读') {
                    newMarkReadBtn.disabled = true;
                    newMarkReadBtn.textContent = '已读';
                } else {
                    newMarkReadBtn.disabled = false;
                    newMarkReadBtn.textContent = '标记为已读';
                    
                    // 设置模态框内标记已读按钮的点击事件
                    newMarkReadBtn.addEventListener('click', function() {
                        const notificationId = this.getAttribute('data-id');
                        
                        // 立即禁用按钮，防止重复点击
                        this.disabled = true;
                        this.textContent = '处理中...';
                        
                        // 通过通知表格组件标记为已读
                        if (window.notificationTable) {
                            window.notificationTable.markAsRead(notificationId);
                            
                            // 不要关闭模态框，只更新模态框内容
                            setTimeout(() => {
                                this.disabled = true;
                                this.textContent = '已读';
                                document.getElementById('notificationStatus').textContent = '已读';
                                const now = new Date().toLocaleString();
                                document.getElementById('notificationReadAt').textContent = now;
                            }, 500);
                        }
                    });
                }
            }
            
            // 显示模态框
            const notificationModal = new bootstrap.Modal(document.getElementById('notificationModal'));
            notificationModal.show();
        });
    });
}

/**
 * 初始化通知详情查看处理程序 - 供NotificationTable调用
 */
function initNotificationDetailViewHandler() {
    // 重用已有的initNotificationView函数
    initNotificationView();
    
    // 重新初始化Tooltip
    initTooltips();
}

/**
 * 初始化删除筛选结果处理程序 - 供NotificationTable调用
 */
function initDeleteFilteredHandler() {
    initDeleteFilteredBtn();
}

/**
 * 显示提示消息 (兼容旧版本 - 使用重定向到后端Flash)
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型 (success/error/warning/info)
 */
function showToast(message, type = 'info') {
    // 日志记录消息，但不做实际操作
    console.log(`[Flash消息] ${type}: ${message}`);
    
    // 通知从后端返回的消息会通过Flash系统显示，无需在前端创建Toast
    // 此函数保留只是为了兼容旧代码
}

/**
 * 初始化删除筛选结果按钮
 */
function initDeleteFilteredBtn() {
    const deleteFilteredBtn = document.getElementById('deleteFilteredBtn');
    if (deleteFilteredBtn) {
        console.log("找到删除筛选结果按钮，添加点击事件");
        deleteFilteredBtn.addEventListener('click', function() {
            // 收集所有搜索参数
            const searchParams = {};
            document.querySelectorAll('[data-search-param]').forEach(element => {
                const key = element.getAttribute('data-param-key');
                const value = element.getAttribute('data-param-value');
                if (key && value) {
                    searchParams[key] = value;
                }
            });
            
            console.log("删除筛选按钮点击，搜索参数:", searchParams);
            
            // 询问用户确认
            if (confirm(`确定要删除所有符合当前筛选条件的通知吗？此操作不可恢复！`)) {
                // 使用fetch API发送请求
                fetch('/notifications/delete/filtered', {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(searchParams)
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('删除筛选结果失败');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        // 不再显示前端Toast，等待后端Flash消息
                        
                        // 更新统计指标
                        if (data.stats) {
                            document.getElementById('totalCount').textContent = data.stats.total;
                            document.getElementById('unreadCount').textContent = data.stats.unread;
                            document.getElementById('readCount').textContent = data.stats.read;
                        }
                        
                        // 如果删除成功并且没有剩余通知，跳转回首页
                        if (data.stats && data.stats.total === 0) {
                            window.location.href = document.getElementById('indexUrl').getAttribute('data-url');
                        } else {
                            // 刷新页面
                            if (window.notificationTable) {
                                window.notificationTable.reloadTable();
                            } else {
                                window.location.reload();
                            }
                        }
                    } else {
                        // 后端会发送Flash消息，此处只需记录错误
                        console.error('删除筛选结果失败:', data.message);
                    }
                })
                .catch(error => {
                    console.error('删除筛选结果出错:', error);
                    // 可能需要页面重载以显示后端Flash消息
                    window.location.reload();
                });
            }
        });
    } else {
        console.log("未找到删除筛选结果按钮");
    }
}

// 暴露全局方法，用于兼容旧代码
window.showToast = showToast;
window.initTooltips = initTooltips;
window.initNotificationView = initNotificationView;
window.initDeleteFilteredBtn = initDeleteFilteredBtn; 