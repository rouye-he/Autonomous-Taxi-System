/**
 * 订单表格AJAX分页功能
 */
class OrderAjaxPagination {
    /**
     * 初始化订单表格AJAX分页
     * @param {Object} options - 配置选项
     */
    constructor(options = {}) {
        this.options = Object.assign({
            tableContainer: '.order-table-container',
            baseUrl: document.getElementById('indexUrl')?.dataset.url || '/orders',
            searchUrl: document.getElementById('searchUrl')?.dataset.url || '/orders/advanced_search'
        }, options);
        
        this.tableContainer = document.querySelector(this.options.tableContainer);
        
        if (!this.tableContainer) {
            console.error('找不到表格容器:', this.options.tableContainer);
            return;
        }
        
        this.init();
    }
    
    /**
     * 初始化分页处理功能
     */
    init() {
        this.initPaginationHandlers();
        this.initSearchFunctions();
        
        // 监听浏览器的前进/后退按钮事件
        window.addEventListener('popstate', (event) => {
            if (event.state && event.state.page) {
                // 从URL获取当前页码
                const urlParams = new URLSearchParams(window.location.search);
                const currentPage = parseInt(urlParams.get('page')) || 1;
                
                // 通过AJAX加载对应页面
                this.loadPageData(currentPage);
            }
        });
    }
    
    /**
     * 初始化分页处理程序
     */
    initPaginationHandlers() {
        const self = this;
        
        // 为所有页码链接添加点击事件
        document.querySelectorAll('.pagination .page-link').forEach(link => {
            // 排除已禁用的链接
            if (link.parentElement.classList.contains('disabled')) {
                return;
            }
            
            // 原始href值
            const originalHref = link.getAttribute('href');
            
            // 提取页码 - 从URL中的page参数
            const pageMatch = originalHref.match(/[?&]page=(\d+)/);
            const pageNum = pageMatch ? pageMatch[1] : null;
            
            // 如果找到页码,修改链接行为
            if (pageNum) {
                // 存储原始href以便需要时使用
                link.setAttribute('data-original-href', originalHref);
                // 修改链接为JavaScript触发
                link.setAttribute('href', 'javascript:void(0);');
                link.setAttribute('data-page', pageNum);
                
                // 添加点击事件处理程序
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    
                    // 如果链接被禁用,不执行任何操作
                    if (this.parentElement.classList.contains('disabled') || 
                        this.hasAttribute('disabled')) {
                        return;
                    }
                    
                    // 保存当前链接的原始内容
                    const originalContent = this.innerHTML;
                    
                    // 添加加载中样式
                    this.classList.add('loading');
                    this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
                    
                    // 禁用所有页码链接,防止重复点击
                    document.querySelectorAll('.pagination .page-link').forEach(l => {
                        l.classList.add('temp-disabled');
                        l.style.pointerEvents = 'none';
                    });
                    
                    // 加载页面数据
                    self.loadPageData(pageNum);
                    
                    // 延迟后移除加载样式,恢复所有页码链接
                    setTimeout(() => {
                        document.querySelectorAll('.pagination .page-link').forEach(l => {
                            l.classList.remove('temp-disabled');
                            l.style.pointerEvents = '';
                        });
                    }, 500);
                });
            }
        });
        
        // 为页码跳转按钮添加点击事件
        const jumpBtn = document.getElementById('jumpToPageBtn');
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
        
        // 构建请求URL - 根据当前页面是否是高级搜索页面
        const isAdvancedSearch = window.location.href.includes('advanced_search');
        const url = (isAdvancedSearch ? this.options.searchUrl : this.options.baseUrl) + '?' + urlParams.toString();
        
        // 在表格内部创建加载指示器,而不是替换整个内容
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div>';
        
        // 确保表格容器有相对定位,以便绝对定位的加载指示器正确显示
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
                
                // 更新浏览器历史记录和URL,但不刷新页面
                const newUrl = new URL(window.location.href);
                newUrl.searchParams.set('page', pageNum);
                window.history.pushState({ page: pageNum }, '', newUrl.toString());
                
                // 更新状态统计数据(如果有)
                if (data.stats) {
                    this.updateStats(data.stats);
                }
                
                // 重新初始化所有事件处理
                this.initPaginationHandlers();
                this.initSearchFunctions();
                if (window.orderTable && typeof window.orderTable.initRowEvents === 'function') {
                    window.orderTable.initRowEvents();
                }
                
                // 高亮显示表格容器提供视觉反馈
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
     * 高亮显示表格容器,提供视觉反馈
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
            // 禁用输入框和按钮,显示加载中状态
            input.disabled = true;
            const jumpBtn = document.getElementById('jumpToPageBtn');
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
                
                if (jumpBtn) {
                    jumpBtn.disabled = false;
                    jumpBtn.innerHTML = '<i class="bi bi-arrow-right-circle"></i>';
                }
            }, 500);
        } else {
            // 显示错误信息,并聚焦到输入框
            input.classList.add('is-invalid');
            
            // 移除错误样式
            setTimeout(() => {
                input.classList.remove('is-invalid');
            }, 2000);
        }
    }
    
    /**
     * 更新状态统计
     * @param {Object} stats - 状态统计数据
     */
    updateStats(stats) {
        if (!stats) return;
        
        // 更新待分配订单数量
        if (stats.waiting !== undefined) {
            const waitingElement = document.querySelector('.stat-card:nth-child(1) .card-title');
            if (waitingElement) {
                waitingElement.textContent = stats.waiting;
            }
        }
        
        // 更新进行中订单数量
        if (stats.in_progress !== undefined) {
            const inProgressElement = document.querySelector('.stat-card:nth-child(2) .card-title');
            if (inProgressElement) {
                inProgressElement.textContent = stats.in_progress;
            }
        }
        
        // 更新已完成订单数量
        if (stats.completed !== undefined) {
            const completedElement = document.querySelector('.stat-card:nth-child(3) .card-title');
            if (completedElement) {
                completedElement.textContent = stats.completed;
            }
        }
        
        // 更新总记录数
        if (stats.total !== undefined) {
            const totalElement = document.querySelector('.card-header h5 .text-muted');
            if (totalElement) {
                totalElement.textContent = `(共${stats.total}条记录)`;
            }
        }
    }
    
    /**
     * 显示Toast消息提示
     * @param {string} message - 消息内容
     * @param {string} type - 消息类型
     */
    showToast(message, type = 'info') {
        // 检查是否有showLocalToast函数
        if (typeof showLocalToast === 'function') {
            showLocalToast(message, type);
            return;
        }
        
        // 创建一个新的Toast元素
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
        }, 3000);
    }
    
    /**
     * 初始化搜索功能
     */
    initSearchFunctions() {
        // 重新绑定移除搜索参数的功能
        const self = this;
        
        // 为所有搜索标签的删除按钮添加点击事件
        document.querySelectorAll('.search-tag .badge').forEach(badge => {
            badge.onclick = null; // 移除旧的事件处理程序
            badge.addEventListener('click', function() {
                const tag = this.closest('.search-tag');
                if (tag) {
                    const paramKey = tag.getAttribute('data-param-key');
                    if (paramKey) {
                        // 创建构建URL,排除要删除的参数
                        const url = new URL(window.location.href);
                        url.searchParams.delete(paramKey);
                        url.searchParams.delete('page'); // 重置页码
                        
                        // 检查是否是使用AJAX还是传统方式
                        if (typeof window.removeSearchParam === 'function') {
                            // 使用已定义的removeSearchParam函数
                            window.removeSearchParam(paramKey);
                        } else {
                            // 直接导航
                            window.location.href = url.toString();
                        }
                    }
                }
            });
        });
        
        // 为清除所有筛选按钮添加点击事件
        document.querySelectorAll('button[onclick*="clearAllSearchParams"]').forEach(button => {
            button.onclick = null; // 移除旧的事件处理程序
            button.addEventListener('click', function() {
                if (typeof window.clearAllSearchParams === 'function') {
                    // 使用已定义的clearAllSearchParams函数
                    window.clearAllSearchParams();
                } else {
                    // 手动清除所有参数
                    const indexUrl = document.getElementById('indexUrl');
                    const url = indexUrl && indexUrl.dataset.url ? indexUrl.dataset.url : '/orders';
                    window.location.href = url;
                }
            });
        });
        
        // 为搜索表单添加提交事件
        const searchForm = document.getElementById('orderSearchForm');
        if (searchForm) {
            searchForm.removeEventListener('submit', this.handleSearchSubmit);
            searchForm.addEventListener('submit', this.handleSearchSubmit.bind(this));
        }
        
        // 重置搜索按钮
        const resetSearchBtn = document.getElementById('resetSearchBtn');
        if (resetSearchBtn) {
            resetSearchBtn.removeEventListener('click', this.handleResetSearch);
            resetSearchBtn.addEventListener('click', this.handleResetSearch.bind(this));
        }
    }
    
    /**
     * 处理搜索表单提交
     * @param {Event} e - 表单提交事件
     */
    handleSearchSubmit(e) {
        e.preventDefault();
        
        // 获取表单元素
        const form = e.target;
        
        // 创建FormData对象
        const formData = new FormData(form);
        
        // 将FormData转换为URLSearchParams
        const params = new URLSearchParams();
        for (const [key, value] of formData.entries()) {
            if (value) { // 只添加有值的参数
                params.append(key, value);
            }
        }
        
        // 添加AJAX标识
        params.append('ajax', '1');
        params.append('include_stats', '1');
        
        // 构建URL
        const url = form.getAttribute('action') || this.options.searchUrl;
        const fullUrl = `${url}?${params.toString()}`;
        
        // 添加加载指示器
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">搜索中...</span></div>';
        
        // 确保表格容器有相对定位
        const currentPosition = getComputedStyle(this.tableContainer).position;
        if (currentPosition === 'static') {
            this.tableContainer.style.position = 'relative';
        }
        
        // 添加加载指示器到表格容器
        this.tableContainer.appendChild(loadingOverlay);
        
        // 发送AJAX请求
        fetch(fullUrl, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('搜索失败');
            }
            return response.json();
        })
        .then(data => {
            if (data.html) {
                // 替换表格内容
                this.tableContainer.innerHTML = data.html;
                
                // 更新浏览器历史记录和URL
                const newUrl = `${url}?${params.toString().replace(/&?ajax=1&?/g, '').replace(/&?include_stats=1&?/g, '')}`;
                window.history.pushState({ search: true }, '', newUrl);
                
                // 更新状态统计数据
                if (data.stats) {
                    this.updateStats(data.stats);
                }
                
                // 重新初始化事件处理
                this.initPaginationHandlers();
                this.initSearchFunctions();
                if (window.orderTable && typeof window.orderTable.initRowEvents === 'function') {
                    window.orderTable.initRowEvents();
                }
                
                // 高亮表格容器
                this.highlightTableContainer();
                
                // 关闭搜索表单折叠面板
                const searchToggle = document.getElementById('searchToggle');
                if (searchToggle) {
                    const searchForm = document.getElementById('searchForm');
                    if (searchForm && searchForm.classList.contains('show')) {
                        new bootstrap.Collapse(searchForm).hide();
                    }
                }
                
                // 显示成功提示
            } 
        })
        .catch(error => {
            console.error('搜索失败:', error);
            
            // 移除加载指示器
            const existingOverlay = this.tableContainer.querySelector('.loading-overlay');
            if (existingOverlay) {
                existingOverlay.remove();
            }
            
            // 回退到传统方式
            form.submit();
        });
    }
    
    /**
     * 处理重置搜索表单
     */
    handleResetSearch() {
        const form = document.getElementById('orderSearchForm');
        if (form) {
            form.reset();
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 创建全局实例供其他脚本使用
    window.orderPagination = new OrderAjaxPagination();
}); 