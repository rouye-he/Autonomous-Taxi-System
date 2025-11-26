/**
 * 通用数据表格组件
 * 提供高级搜索、分页、AJAX刷新等功能
 */

class DataTable {
    /**
     * 创建数据表格组件
     * @param {Object} options - 配置选项
     * @param {string} options.tableContainer - 表格容器选择器
     * @param {string} options.baseUrl - 数据请求基础URL
     * @param {Function} options.initRowEvents - 行事件初始化函数
     * @param {Object} options.statsElements - 统计元素ID映射 {total: 'totalCount', unread: 'unreadCount', ...}
     * @param {boolean} options.showToastOnRefresh - 刷新后是否显示提示
     */
    constructor(options) {
        this.options = Object.assign({
            tableContainer: '.table-responsive',
            baseUrl: window.location.pathname,
            initRowEvents: null,
            statsElements: {},
            showToastOnRefresh: true
        }, options);
        
        this.tableContainer = document.querySelector(this.options.tableContainer);
        this.initSearchToggle();
        this.initJumpToPage();
        this.initPaginationHandlers();
    }
    
    /**
     * 初始化搜索表单切换功能
     */
    initSearchToggle() {
        const searchToggle = document.getElementById('searchToggle');
        if (searchToggle) {
            searchToggle.addEventListener('click', function() {
                const icon = this.querySelector('i');
                if (icon) {
                    icon.classList.toggle('bi-chevron-down');
                    icon.classList.toggle('bi-chevron-right');
                }
            });
        }
    }
    
    /**
     * 初始化页码跳转功能
     */
    initJumpToPage() {
        const self = this;
        const jumpBtn = document.querySelector('.page-jump button');
        if (jumpBtn) {
            jumpBtn.addEventListener('click', function() {
                self.jumpToPageAjax();
            });
            
            // 添加回车键支持
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
     * AJAX分页跳转到指定页码
     */
    jumpToPageAjax() {
        const input = document.getElementById('pageJumpInput');
        const pageNum = parseInt(input.value);
        const maxPage = parseInt(input.getAttribute('max'));
        
        if (pageNum && pageNum >= 1 && pageNum <= maxPage) {
            // 禁用输入框和按钮，显示加载中状态
            input.disabled = true;
            const jumpBtn = document.querySelector('.page-jump button');
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
            // 显示错误信息，并聚焦到输入框
        
            input.classList.add('is-invalid');
            input.focus();
            
            // 移除错误样式
            setTimeout(() => {
                input.classList.remove('is-invalid');
            }, 2000);
        }
    }
    
    /**
     * 初始化分页处理功能
     */
    initPaginationHandlers() {
        const self = this;
        
        // 为所有页码链接添加点击事件
        document.querySelectorAll('.page-link').forEach(link => {
            // 跳过已经有click事件的元素和带有禁用属性的元素
            if (link.getAttribute('data-ajax-bound') === 'true' || link.parentElement.classList.contains('disabled')) {
                return;
            }
            
            link.addEventListener('click', function(e) {
                // 如果链接是跳转控件或不包含页码信息，则不处理
                if (this.closest('.page-jump') || !this.getAttribute('href')) {
                    return;
                }
                
                e.preventDefault();
                
                // 尝试从URL中提取页码
                let pageNum;
                try {
                    const url = new URL(this.getAttribute('href'), window.location.origin);
                    pageNum = url.searchParams.get('page') || '1';
                } catch (error) {
                    // 如果URL解析失败，尝试直接从href属性中获取页码
                    const match = this.getAttribute('href').match(/page=(\d+)/);
                    pageNum = match ? match[1] : '1';
                }
                
                // 添加加载中样式
                const originalContent = this.innerHTML;
                this.classList.add('loading');
                this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
                
                // 禁用所有页码链接，防止重复点击
                document.querySelectorAll('.page-link').forEach(l => {
                    l.classList.add('temp-disabled');
                    l.style.pointerEvents = 'none';
                });
                
                // 加载页面数据
                self.loadPageData(pageNum);
                
                // 延迟后移除加载样式，恢复所有页码链接
                setTimeout(() => {
                    document.querySelectorAll('.page-link').forEach(l => {
                        l.classList.remove('temp-disabled');
                        l.style.pointerEvents = '';
                    });
                }, 500);
            });
            
            // 标记该元素已绑定事件
            link.setAttribute('data-ajax-bound', 'true');
        });
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
        
        // 检查当前是否在搜索页面
        // 方法1: 检查URL是否包含advanced_search
        const isSearchPage = window.location.pathname.includes('/advanced_search');
        
        // 方法2: 检查是否有任何搜索参数
        const hasSearchParams = Array.from(urlParams.keys()).some(key => 
            key !== 'page' && key !== 'ajax' && key !== 'include_stats' && key !== 'per_page'
        );
        
        // 方法3: 检查页面上是否有搜索参数标记
        const searchParamElements = document.querySelectorAll('[data-search-param]');
        const hasSearchParamElements = searchParamElements.length > 0;
        
        // 方法4: 检查分页元素上的数据属性
        const paginationElement = document.querySelector('.pagination');
        const paginationHasSearch = paginationElement && paginationElement.getAttribute('data-has-search') === 'true';
        
        // 如果以上任一条件为true，则使用advanced_search路由
        const useSearchRoute = isSearchPage || hasSearchParams || hasSearchParamElements || paginationHasSearch;
        
        // 构建请求URL
        let url = this.options.baseUrl;
        
        // 如果是搜索页面，使用advanced_search路由
        if (useSearchRoute) {
            url = this.options.baseUrl + '/advanced_search';
        }
        
        // 添加查询参数
        url = url + '?' + urlParams.toString();
        
        // 在表格内部创建加载指示器
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
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
                
                // 重新初始化事件处理
                if (typeof this.options.initRowEvents === 'function') {
                    this.options.initRowEvents();
                }
                this.initPaginationHandlers();
                this.initJumpToPage();
                
                // 高亮显示表格容器
                this.highlightTableContainer();
            } 
        })
        .catch(error => {
            console.error('加载数据出错:', error);
    
        })
        .finally(() => {
            // 移除加载指示器
            if (loadingOverlay.parentNode === this.tableContainer) {
                this.tableContainer.removeChild(loadingOverlay);
            }
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
     * 更新统计数据
     * @param {Object} stats - 统计数据对象
     */
    updateStats(stats) {
        if (!stats) return;
        
        Object.keys(this.options.statsElements).forEach(key => {
            if (stats[key] !== undefined) {
                const element = document.getElementById(this.options.statsElements[key]);
                if (element) {
                    element.textContent = stats[key];
                }
            }
        });
    }
    
    /**
     * 显示提示消息
     * @param {string} message - 消息内容
     * @param {string} type - 消息类型 (success/error/warning/info)
     */
    showToast(message, type = 'info') {
        // 防止无限递归
        if (window._showingToast) {
            return;
        }
        
        // 设置标记，防止循环调用
        window._showingToast = true;
        
        try {
            // 如果存在全局showToast函数并且不是自己，则使用它
            if (window.showToast && window.showToast !== this.showToast) {
                window.showToast(message, type);
                return;
            }
            
            // 创建toast容器（如果不存在）
            let toastContainer = document.getElementById('toast-container');
            if (!toastContainer) {
                toastContainer = document.createElement('div');
                toastContainer.id = 'toast-container';
                toastContainer.style.position = 'fixed';
                toastContainer.style.top = '20px';
                toastContainer.style.left = '50%';
                toastContainer.style.transform = 'translateX(-50%)';
                toastContainer.style.zIndex = '9999';
                document.body.appendChild(toastContainer);
            }
            
            // 创建新的toast元素
            const toast = document.createElement('div');
            toast.className = `custom-toast toast-${type === 'error' ? 'danger' : type}`;
            toast.style.padding = '10px 20px';
            toast.style.marginBottom = '10px';
            toast.style.borderRadius = '4px';
            toast.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            toast.style.fontWeight = 'bold';
            
            // 设置背景颜色
            switch(type) {
                case 'success':
                    toast.style.backgroundColor = '#28a745';
                    toast.style.color = '#fff';
                    break;
                case 'error':
                case 'danger':
                    toast.style.backgroundColor = '#dc3545';
                    toast.style.color = '#fff';
                    break;
                case 'warning':
                    toast.style.backgroundColor = '#ffc107';
                    toast.style.color = '#000';
                    break;
                default:
                    toast.style.backgroundColor = '#17a2b8';
                    toast.style.color = '#fff';
            }
            
            toast.textContent = message;
            
            // 添加到容器
            toastContainer.appendChild(toast);
            
            // 设置自动消失
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transition = 'opacity 0.5s';
                setTimeout(() => {
                    toast.remove();
                }, 500);
            }, 3000);
        } finally {
            // 清除标记
            window._showingToast = false;
        }
    }

    /**
     * 使用AJAX重新加载表格内容
     * @param {number} delay - 延迟时间(毫秒)，默认为0（立即刷新）
     */
    reloadTable(delay = 0) {
        if (!this.tableContainer) {
            console.error('找不到表格容器');
            return;
        }
        
        const reload = () => {
            // 获取当前页码和其他查询参数
            const urlParams = new URLSearchParams(window.location.search);
            const currentPage = urlParams.get('page') || '1';
            
            // 创建加载指示器
            const loadingOverlay = document.createElement('div');
            loadingOverlay.className = 'loading-overlay';
            loadingOverlay.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div>';
            
            // 确保表格容器有相对定位
            const currentPosition = getComputedStyle(this.tableContainer).position;
            if (currentPosition === 'static') {
                this.tableContainer.style.position = 'relative';
            }
            
            // 添加加载指示器
            this.tableContainer.appendChild(loadingOverlay);
            
            // 构建请求URL
            const url = this.options.baseUrl + (window.location.search.includes('advanced_search') ? '/advanced_search' : '') + '?' + urlParams.toString() + '&ajax=1&include_stats=1';
            
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
                // 处理返回的JSON数据
                if (data.html) {
                    // 替换表格内容
                    this.tableContainer.innerHTML = data.html;
                    
                    // 更新统计数据
                    if (data.stats) {
                        this.updateStats(data.stats);
                    }
                    
                    // 重新初始化事件处理
                    if (typeof this.options.initRowEvents === 'function') {
                        this.options.initRowEvents();
                    }
                    this.initPaginationHandlers();
                    this.initJumpToPage();
                    
                    // 高亮显示表格容器
                    this.highlightTableContainer();
                    
                    // 显示成功消息
                    
                } 
            })
            .catch(error => {
                console.error('AJAX刷新失败:', error);
                
                
                // 移除加载指示器
                const existingOverlay = this.tableContainer.querySelector('.loading-overlay');
                if (existingOverlay) {
                    existingOverlay.remove();
                }
            });
        };
        
        // 使用指定的延迟
        if (delay > 0) {
            setTimeout(reload, delay);
        } else {
            reload();
        }
    }
}

// 监听浏览器的前进/后退按钮事件
window.addEventListener('popstate', function(event) {
    if (event.state && event.state.page) {
        // 从URL获取当前页码
        const urlParams = new URLSearchParams(window.location.search);
        const currentPage = parseInt(urlParams.get('page')) || 1;
        
        // 获取当前页面上所有DataTable实例
        const tables = document.querySelectorAll('[class*="table-container"]');
        tables.forEach(table => {
            const tableId = table.id || table.className;
            // 找到表格对应的DataTable实例
            if (window[tableId + 'Table']) {
                window[tableId + 'Table'].loadPageData(currentPage);
            } else if (window.dataTable) {
                window.dataTable.loadPageData(currentPage);
            }
        });
    }
});

// 导出供其他模块使用
window.DataTable = DataTable; 