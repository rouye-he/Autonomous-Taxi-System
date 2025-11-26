/**
 * 车辆操作日志管理主脚本
 */

document.addEventListener('DOMContentLoaded', function() {
    // 初始化日志详情按钮
    initLogDetailsButtons();
    
    // 初始化日志删除按钮
    initDeleteLogButtons();
    
    // 初始化跳转页按钮
    initJumpToPageButton();
    
    // 初始化模态框关闭处理
    initModalCloseHandler();
    
    // 初始化AJAX分页链接
    initAjaxPaginationLinks();
});

/**
 * 初始化日志详情按钮点击事件
 */
function initLogDetailsButtons() {
    document.querySelectorAll('.view-log-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const logId = this.getAttribute('data-log-id');
            
            // 如果使用全局表格组件，可以直接调用组件方法
            if (window.logTable && typeof window.logTable.viewLogDetails === 'function') {
                window.logTable.viewLogDetails(logId);
                return;
            }
            
            // 否则使用原生fetch获取日志详情
            fetchLogDetails(logId);
        });
    });
}

/**
 * 初始化删除日志按钮点击事件
 */
function initDeleteLogButtons() {
    document.querySelectorAll('.delete-log-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const logId = this.getAttribute('data-log-id');
            
            // 确认删除
            if (confirm('确定要删除这条日志记录吗？此操作不可恢复。')) {
                deleteLog(logId);
            }
        });
    });
}

/**
 * 删除日志记录
 * @param {string} logId - 日志ID
 */
function deleteLog(logId) {
    fetch(`/vehicles/api/delete_log/${logId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`请求失败: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            showToast('日志记录已成功删除', 'success');
            // 刷新页面以显示更新后的数据
            window.location.reload();
        } else {
            showToast(data.message || '删除日志记录失败', 'error');
        }
    })
    .catch(error => {
        console.error('删除日志记录出错:', error);
        showToast('删除日志记录失败: ' + error.message, 'error');
    });
}

/**
 * 初始化模态框关闭事件处理
 */
function initModalCloseHandler() {
    const logDetailModal = document.getElementById('logDetailModal');
    if (logDetailModal) {
        logDetailModal.addEventListener('hidden.bs.modal', function () {
            // 移除所有modal-backdrop元素
            const backdrops = document.getElementsByClassName('modal-backdrop');
            while (backdrops.length > 0) {
                backdrops[0].parentNode.removeChild(backdrops[0]);
            }
            // 移除body上的modal-open类
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        });
        
        // 添加点击关闭按钮的事件
        const closeButtons = logDetailModal.querySelectorAll('[data-bs-dismiss="modal"]');
        closeButtons.forEach(button => {
            button.addEventListener('click', function() {
                // 手动清理模态框背景
                setTimeout(() => {
                    const backdrops = document.getElementsByClassName('modal-backdrop');
                    while (backdrops.length > 0) {
                        backdrops[0].parentNode.removeChild(backdrops[0]);
                    }
                    document.body.classList.remove('modal-open');
                    document.body.style.overflow = '';
                    document.body.style.paddingRight = '';
                }, 150);
            });
        });
    }
}

/**
 * 从服务器获取日志详情
 * @param {string} logId - 日志ID
 */
function fetchLogDetails(logId) {
    fetch(`/vehicles/api/log_details/${logId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`请求失败: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                const log = data.data;
                
                // 填充模态框信息
                document.getElementById('modal-vehicle-id').textContent = log.vehicle_id;
                document.getElementById('modal-plate-number').textContent = log.plate_number;
                document.getElementById('modal-log-type').textContent = log.log_type;
                document.getElementById('modal-created-at').textContent = log.created_at;
                document.getElementById('modal-log-content').textContent = log.log_content;
                
                // 显示模态框前清理可能存在的遮罩
                const existingBackdrops = document.getElementsByClassName('modal-backdrop');
                while (existingBackdrops.length > 0) {
                    existingBackdrops[0].parentNode.removeChild(existingBackdrops[0]);
                }
                
                // 确保body没有modal-open类和内联样式
                document.body.classList.remove('modal-open');
                document.body.style.overflow = '';
                document.body.style.paddingRight = '';
                
                // 显示模态框
                const modalElement = document.getElementById('logDetailModal');
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
                
                // 为ESC键添加事件监听
                document.addEventListener('keydown', function escKeyHandler(e) {
                    if (e.key === 'Escape') {
                        modal.hide();
                        // 手动清理模态框背景
                        setTimeout(() => {
                            const backdrops = document.getElementsByClassName('modal-backdrop');
                            while (backdrops.length > 0) {
                                backdrops[0].parentNode.removeChild(backdrops[0]);
                            }
                            document.body.classList.remove('modal-open');
                            document.body.style.overflow = '';
                            document.body.style.paddingRight = '';
                        }, 150);
                        document.removeEventListener('keydown', escKeyHandler);
                    }
                });
            } else {
                showToast(data.message || '获取日志详情失败', 'error');
            }
        })
        .catch(error => {
            console.error('获取日志详情出错:', error);
            showToast('获取日志详情失败: ' + error.message, 'error');
        });
}

/**
 * 初始化分页跳转按钮
 */
function initJumpToPageButton() {
    const jumpButton = document.getElementById('jumpToPageBtn') || document.getElementById('jumpButton');
    if (jumpButton) {
        jumpButton.addEventListener('click', function() {
            const jumpInput = document.getElementById('pageJumpInput') || document.getElementById('jumpToPage');
            const page = parseInt(jumpInput.value);
            const maxPage = parseInt(jumpInput.getAttribute('max') || jumpInput.placeholder.split('/')[1]);
            
            if (isNaN(page) || page < 1 || page > maxPage) {
                showToast(`请输入有效的页码 (1-${maxPage})`, 'warning');
                return;
            }
            
            // 通过AJAX加载页面数据
            if (window.logTable && typeof window.logTable.loadPageData === 'function') {
                window.logTable.loadPageData(page);
            } else {
                // 构建URL
                let url = new URL(window.location.href);
                url.searchParams.set('page', page);
                url.searchParams.set('ajax', '1');  // 添加AJAX标记
                url.searchParams.set('include_stats', '1');  // 请求包含统计数据
                
                // 显示加载状态
                const tableContainer = document.querySelector('.log-table-container');
                if (tableContainer) {
                    const loadingOverlay = document.createElement('div');
                    loadingOverlay.className = 'loading-overlay';
                    loadingOverlay.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div>';
                    tableContainer.style.position = 'relative';
                    tableContainer.appendChild(loadingOverlay);
                }
                
                // 发送AJAX请求
                fetch(url.toString(), {
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
                        tableContainer.innerHTML = data.html;
                        
                        // 更新URL，不刷新页面
                        const newUrl = new URL(window.location.href);
                        newUrl.searchParams.set('page', page);
                        window.history.pushState({ page: page }, '', newUrl.toString());
                        
                        // 重新初始化事件
                        initLogDetailsButtons();
                        initDeleteLogButtons();
                        initJumpToPageButton();
                        
                        // 显示成功消息
                        showToast('页面数据已更新', 'success');
                    } else {
                        showToast('加载数据失败', 'error');
                    }
                })
                .catch(error => {
                    console.error('AJAX页面请求失败:', error);
                    showToast('加载数据失败: ' + error.message, 'error');
                    
                    // 移除加载指示器
                    const existingOverlay = tableContainer.querySelector('.loading-overlay');
                    if (existingOverlay) {
                        existingOverlay.remove();
                    }
                    
                    // 出错时回退到传统刷新
                    const url = new URL(window.location.href);
                    url.searchParams.set('page', page);
                    window.location.href = url.toString();
                });
            }
        });
        
        // 为输入框添加回车键支持
        const jumpInput = document.getElementById('pageJumpInput') || document.getElementById('jumpToPage');
        if (jumpInput) {
            jumpInput.addEventListener('keyup', function(e) {
                if (e.key === 'Enter') {
                    jumpButton.click();
                }
            });
        }
    }
}

/**
 * 显示Toast消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型（success/error/warning/info）
 * @param {number} duration - 持续时间（毫秒）
 */
function showToast(message, type = 'info', duration = 3000) {
    if (typeof showLocalToast === 'function') {
        showLocalToast(message, type, duration);
        return;
    }
    
    const toast = document.createElement('div');
    toast.className = `toast-message toast-${type}`;
    toast.innerHTML = message;
    document.body.appendChild(toast);
    
    // 自动移除
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.5s';
        setTimeout(() => {
            toast.remove();
        }, 500);
    }, duration);
}

/**
 * 初始化AJAX分页链接
 */
function initAjaxPaginationLinks() {
    document.querySelectorAll('.page-link[data-ajax="true"]').forEach(link => {
        if (link.closest('.disabled')) {
            return; // 跳过禁用的页码链接
        }
        
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 解析URL获取页码
            const url = new URL(this.href);
            const page = url.searchParams.get('page') || '1';
            
            // 添加AJAX参数
            url.searchParams.set('ajax', '1');
            url.searchParams.set('include_stats', '1');
            
            // 显示加载状态
            const tableContainer = document.querySelector('.log-table-container');
            if (tableContainer) {
                const loadingOverlay = document.createElement('div');
                loadingOverlay.className = 'loading-overlay';
                loadingOverlay.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div>';
                tableContainer.style.position = 'relative';
                tableContainer.appendChild(loadingOverlay);
                
                // 禁用所有分页链接，防止重复点击
                document.querySelectorAll('.page-link').forEach(link => {
                    link.style.pointerEvents = 'none';
                });
            }
            
            // 发送AJAX请求
            fetch(url.toString(), {
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
                    tableContainer.innerHTML = data.html;
                    
                    // 更新浏览器URL，但不刷新页面
                    const newUrl = new URL(window.location.href);
                    newUrl.searchParams.set('page', page);
                    window.history.pushState({ page: page }, '', newUrl.toString());
                    
                    // 重新初始化事件处理
                    initLogDetailsButtons();
                    initDeleteLogButtons();
                    initJumpToPageButton();
                    initAjaxPaginationLinks();
                    
                    // 显示成功消息
                    showToast('页面数据已更新', 'success');
                } else {
                    showToast('加载数据失败', 'error');
                }
            })
            .catch(error => {
                console.error('AJAX页面请求失败:', error);
                showToast('加载数据失败: ' + error.message, 'error');
                
                // 移除加载指示器
                const existingOverlay = tableContainer.querySelector('.loading-overlay');
                if (existingOverlay) {
                    existingOverlay.remove();
                }
                
                // 恢复分页链接可点击状态
                document.querySelectorAll('.page-link').forEach(link => {
                    link.style.pointerEvents = '';
                });
                
                // 出错时回退到传统刷新
                window.location.href = this.href;
            });
        });
    });
}
