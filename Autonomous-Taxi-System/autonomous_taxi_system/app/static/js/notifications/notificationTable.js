/**
 * 通知表格组件
 * 扩展通用数据表格组件，处理通知特有的功能
 */

class NotificationTable extends DataTable {
    /**
     * 创建通知表格组件
     * @param {Object} options - 配置选项
     */
    constructor(options) {
        // 默认配置
        const defaultOptions = {
            tableContainer: '.notification-table-container',
            baseUrl: '/notifications',
            statsElements: {
                total: 'totalCount',
                unread: 'unreadCount',
                read: 'readCount'
            },
            showToastOnRefresh: true
        };
        
        // 合并默认配置和用户配置
        super(Object.assign({}, defaultOptions, options));
        
        // 初始化通知特有事件
        this.initDeleteHandlers();
        this.initMarkAsReadHandlers();
        this.initMarkAllAsReadHandler();
        this.initBatchSelection();
        this.initRowEvents();
        this.initPaginationHandlers(); // 添加分页处理
    }
    
    /**
     * 初始化删除通知的事件处理
     */
    initDeleteHandlers() {
        const self = this;
        
        // 为所有删除按钮添加事件监听
        document.querySelectorAll('.delete-notification-btn').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const notificationId = this.getAttribute('data-id');
                self.deleteNotification(notificationId);
            });
        });
    }
    
    /**
     * 初始化标记已读的事件处理
     */
    initMarkAsReadHandlers() {
        const self = this;
        
        // 为所有标记已读按钮添加事件监听
        document.querySelectorAll('.mark-read-btn').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const notificationId = this.getAttribute('data-id');
                self.markAsRead(notificationId);
            });
        });
    }
    
    /**
     * 初始化全部标记已读的事件处理
     */
    initMarkAllAsReadHandler() {
        const self = this;
        const markAllBtn = document.getElementById('markAllReadBtn');
        
        if (markAllBtn) {
            markAllBtn.addEventListener('click', function(e) {
                e.preventDefault();
                self.markAllAsRead();
            });
        }
    }
    
    /**
     * 初始化批量选择功能
     */
    initBatchSelection() {
        const self = this;
        
        // 获取全选复选框和批量删除按钮
        const selectAllCheckbox = document.getElementById('selectAllCheckbox');
        const batchDeleteBtn = document.getElementById('batchDeleteBtn');
        
        if (selectAllCheckbox) {
            // 全选/取消全选
            selectAllCheckbox.addEventListener('change', function() {
                const isChecked = this.checked;
                const checkboxes = document.querySelectorAll('.notification-checkbox');
                
                checkboxes.forEach(checkbox => {
                    checkbox.checked = isChecked;
                });
                
                // 更新批量删除按钮状态
                self.updateBatchDeleteButtonState();
            });
        }
        
        // 单个复选框变化事件
        document.querySelectorAll('.notification-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                // 更新批量删除按钮状态
                self.updateBatchDeleteButtonState();
                
                // 更新全选复选框状态
                if (selectAllCheckbox) {
                    const allCheckboxes = document.querySelectorAll('.notification-checkbox');
                    const checkedCheckboxes = document.querySelectorAll('.notification-checkbox:checked');
                    
                    selectAllCheckbox.checked = allCheckboxes.length === checkedCheckboxes.length;
                    selectAllCheckbox.indeterminate = checkedCheckboxes.length > 0 && allCheckboxes.length !== checkedCheckboxes.length;
                }
            });
        });
        
        // 批量删除按钮点击事件
        if (batchDeleteBtn) {
            batchDeleteBtn.addEventListener('click', function(e) {
                e.preventDefault();
                const selectedIds = self.getSelectedNotificationIds();
                
                if (selectedIds.length > 0) {
                    // 确认删除提示
                    if (confirm(`确定要删除选中的 ${selectedIds.length} 条通知吗？此操作不可恢复。`)) {
                        self.batchDeleteNotifications(selectedIds);
                    }
                }
            });
        }
    }
    
    /**
     * 更新批量删除按钮状态
     */
    updateBatchDeleteButtonState() {
        const batchDeleteBtn = document.getElementById('batchDeleteBtn');
        const selectedIds = this.getSelectedNotificationIds();
        
        if (batchDeleteBtn) {
            batchDeleteBtn.disabled = selectedIds.length === 0;
        }
    }
    
    /**
     * 获取选中的通知ID列表
     * @returns {Array} 通知ID数组
     */
    getSelectedNotificationIds() {
        const selectedIds = [];
        document.querySelectorAll('.notification-checkbox:checked').forEach(checkbox => {
            selectedIds.push(checkbox.value);
        });
        return selectedIds;
    }
    
    /**
     * 批量删除通知
     * @param {Array} notificationIds - 通知ID数组
     */
    batchDeleteNotifications(notificationIds) {
        if (!notificationIds || notificationIds.length === 0) return;
        
        fetch('/notifications/delete/batch', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ids: notificationIds
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('批量删除通知失败');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // 立即刷新表格
                this.reloadTable();
            } 
        })
        .catch(error => {
            console.error('批量删除通知出错:', error);
        });
    }
    
    /**
     * 删除指定ID的通知
     * @param {string} notificationId - 通知ID
     */
    deleteNotification(notificationId) {
        if (!notificationId) return;
        
        fetch('/notifications/delete/' + notificationId, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('删除通知失败');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // 立即刷新表格
                this.reloadTable();
            } 
        })
        .catch(error => {
            console.error('删除通知出错:', error);
        });
    }
    
    /**
     * 将指定ID的通知标记为已读
     * @param {string} notificationId - 通知ID
     */
    markAsRead(notificationId) {
        if (!notificationId) return;
        
        fetch('/notifications/mark_read/' + notificationId, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('标记通知为已读失败');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // 立即刷新表格
                this.reloadTable();
            } 
        })
        .catch(error => {
            console.error('标记通知为已读出错:', error);
        });
    }
    
    /**
     * 将所有通知标记为已读
     */
    markAllAsRead() {
        fetch('/notifications/mark_all_read', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('标记所有通知为已读失败');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // 立即刷新表格
                this.reloadTable();
            } 
        })
        .catch(error => {
            console.error('标记所有通知为已读出错:', error);
        });
    }
    
    /**
     * 重写initRowEvents方法，提供给DataTable使用
     */
    initRowEvents() {
        this.initDeleteHandlers();
        this.initMarkAsReadHandlers();
        this.initBatchSelection();
        this.initFilteredDeleteHandler();
    }
    
    /**
     * 初始化删除筛选结果按钮事件
     */
    initFilteredDeleteHandler() {
        const deleteFilteredBtn = document.getElementById('deleteFilteredBtn');
        if (deleteFilteredBtn) {
            deleteFilteredBtn.addEventListener('click', () => {
                // 收集所有搜索参数
                const searchParams = {};
                document.querySelectorAll('[data-search-param]').forEach(element => {
                    const key = element.getAttribute('data-param-key');
                    const value = element.getAttribute('data-param-value');
                    if (key && value) {
                        searchParams[key] = value;
                    }
                });
                
                // 询问用户确认
                if (confirm(`确定要删除所有符合当前筛选条件的通知吗？此操作不可恢复！`)) {
                    this.deleteFilteredNotifications(searchParams);
                }
            });
        }
    }
    
    /**
     * 删除符合筛选条件的所有通知
     * @param {Object} searchParams - 筛选条件
     */
    deleteFilteredNotifications(searchParams) {
        if (!searchParams || Object.keys(searchParams).length === 0) {
            return;
        }
        
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
                    // 立即刷新表格
                    this.reloadTable();
                }
            } 
        })
        .catch(error => {
            console.error('删除筛选结果出错:', error);
        });
    }
    
    /**
     * 初始化分页处理功能
     */
    initPaginationHandlers() {
        const self = this;
        
        // 为所有页码链接添加点击事件
        document.querySelectorAll('.page-nav-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                
                // 如果链接被禁用，不执行任何操作
                if (this.hasAttribute('disabled')) {
                    return;
                }
                
                const pageNum = this.getAttribute('data-page');
                if (pageNum) {
                    // 保存当前链接的原始内容
                    const originalContent = this.innerHTML;
                    
                    // 添加加载中样式
                    this.classList.add('loading');
                    this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
                    
                    // 禁用所有页码链接，防止重复点击
                    document.querySelectorAll('.page-nav-link').forEach(l => {
                        l.classList.add('temp-disabled');
                        l.style.pointerEvents = 'none';
                    });
                    
                    // 加载页面数据
                    self.loadPageData(pageNum);
                    
                    // 延迟后移除加载样式，恢复所有页码链接
                    setTimeout(() => {
                        document.querySelectorAll('.page-nav-link').forEach(l => {
                            l.classList.remove('temp-disabled');
                            l.style.pointerEvents = '';
                        });
                    }, 500);
                }
            });
        });
        
        // 为页码跳转按钮添加点击事件
        const jumpBtn = document.getElementById('pageJumpBtn');
        if (jumpBtn) {
            jumpBtn.addEventListener('click', function() {
                self.jumpToPageAjax();
            });
            
            // 为跳转输入框添加回车键支持
            const input = document.getElementById('pageJumpInput');
            if (input) {
                input.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        self.jumpToPageAjax();
                    }
                });
            }
        }
    }
    
    /**
     * 使用AJAX加载指定页码的数据
     * @param {number} pageNum - 页码
     */
    loadPageData(pageNum) {
        if (!pageNum) return;
        
        // 获取当前URL中的所有查询参数
        const urlParams = new URLSearchParams(window.location.search);
        
        // 更新页码参数
        urlParams.set('page', pageNum);
        
        // 添加AJAX和统计标识
        urlParams.set('ajax', '1');
        urlParams.set('include_stats', '1');
        
        // 构建请求URL
        const url = this.options.baseUrl + (window.location.search.includes('advanced_search') ? '/advanced_search' : '') + '?' + urlParams.toString();
        
        // 在表格内部创建加载指示器，而不是替换整个内容
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.style.position = 'absolute';
        loadingOverlay.style.top = '0';
        loadingOverlay.style.left = '0';
        loadingOverlay.style.width = '100%';
        loadingOverlay.style.height = '100%';
        loadingOverlay.style.backgroundColor = 'rgba(255, 255, 255, 0.7)';
        loadingOverlay.style.display = 'flex';
        loadingOverlay.style.alignItems = 'center';
        loadingOverlay.style.justifyContent = 'center';
        loadingOverlay.style.zIndex = '1000';
        loadingOverlay.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div>';
        
        // 确保表格容器有相对定位，以便绝对定位的加载指示器正确显示
        const currentPosition = getComputedStyle(this.tableContainer).position;
        if (currentPosition === 'static') {
            this.tableContainer.style.position = 'relative';
        }
        
        // 添加加载指示器到表格容器
        this.tableContainer.appendChild(loadingOverlay);
        
        // 发送AJAX请求
        fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('加载数据失败');
            }
            return response.json();
        })
        .then(data => {
            if (data.html) {
                // 替换表格内容
                this.tableContainer.innerHTML = data.html;
                
                // 更新浏览器历史记录和URL，但不刷新页面
                const newUrl = new URL(window.location.href);
                newUrl.searchParams.set('page', pageNum);
                window.history.pushState({ page: pageNum }, '', newUrl.toString());
                
                // 更新统计数据
                if (data.stats) {
                    this.updateStats(data.stats);
                }
                
                // 重新初始化所有事件处理
                this.initDeleteHandlers();
                this.initMarkAsReadHandlers();
                this.initBatchSelection();
                this.initRowEvents();
                this.initPaginationHandlers();
                
                // 可选：高亮显示表格容器
                this.highlightTableContainer();
            } 
        })
        .catch(error => {
            console.error('AJAX分页请求失败:', error);
            
            // 移除加载指示器
            const existingOverlay = this.tableContainer.querySelector('.loading-overlay');
            if (existingOverlay) {
                existingOverlay.remove();
            }
            
            // 出错时回退到传统刷新
            const url = new URL(window.location.href);
            url.searchParams.set('page', pageNum);
            window.location.href = url.toString();
        });
    }
    
    /**
     * 高亮显示表格容器，提供视觉反馈
     */
    highlightTableContainer() {
        // 添加高亮动画类
        this.tableContainer.classList.add('highlight-table');
        
        // 动画结束后移除类
        setTimeout(() => {
            this.tableContainer.classList.remove('highlight-table');
        }, 1000);
    }
    
    /**
     * 使用AJAX跳转到指定页码
     */
    jumpToPageAjax() {
        const input = document.getElementById('pageJumpInput');
        const pageNum = parseInt(input.value);
        const maxPage = parseInt(input.getAttribute('max'));
        
        if (pageNum && pageNum >= 1 && pageNum <= maxPage) {
            // 禁用输入框和按钮，显示加载中状态
            input.disabled = true;
            const jumpBtn = document.getElementById('pageJumpBtn');
            if (jumpBtn) {
                jumpBtn.disabled = true;
                jumpBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
            }
            
            // 调用加载页面数据
            this.loadPageData(pageNum);
            
            // 加载完成后恢复输入框和按钮状态
            setTimeout(() => {
                input.disabled = false;
                input.value = '';
                input.placeholder = `${pageNum}/${maxPage}`;
                input.focus();
                
                if (jumpBtn) {
                    jumpBtn.disabled = false;
                    jumpBtn.innerHTML = '<i class="bi bi-arrow-right-circle"></i>';
                }
            }, 500);
        } else {
            // 显示错误信息，并聚焦到输入框
            input.classList.add('is-invalid');
            input.focus();
            
            // 移除错误样式
            setTimeout(() => {
                input.classList.remove('is-invalid');
            }, 2000);
        }
    }
}

// 页面加载完成后初始化通知表格组件
document.addEventListener('DOMContentLoaded', function() {
    // 创建通知表格实例
    window.notificationTable = new NotificationTable({
        initRowEvents: function() {
            // 初始化通知行点击事件等
            initNotificationDetailViewHandler();
            initDeleteFilteredHandler();
        }
    });
    
    // 如果存在过滤结果删除按钮，添加事件处理
    const deleteFilteredBtn = document.getElementById('deleteFilteredBtn');
    if (deleteFilteredBtn) {
        deleteFilteredBtn.addEventListener('click', function() {
            if (confirm('确定要删除所有筛选结果吗？此操作不可恢复。')) {
                const searchParams = {};
                
                // 收集当前的搜索参数
                document.querySelectorAll('[data-search-param]').forEach(el => {
                    const key = el.getAttribute('data-param-key');
                    const value = el.getAttribute('data-param-value');
                    if (key && value) {
                        searchParams[key] = value;
                    }
                });
                
                window.notificationTable.deleteFilteredNotifications(searchParams);
            }
        });
    }
    
    // 监听浏览器的前进/后退按钮事件
    window.addEventListener('popstate', function(event) {
        if (event.state && event.state.page) {
            // 从URL获取当前页码
            const urlParams = new URLSearchParams(window.location.search);
            const currentPage = parseInt(urlParams.get('page')) || 1;
            
            // 通过AJAX加载对应页面
            if (window.notificationTable) {
                window.notificationTable.loadPageData(currentPage);
            }
        }
    });
}); 