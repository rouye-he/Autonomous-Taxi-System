/**
 * 收入表格组件
 * 扩展通用数据表格组件，处理收入特有的功能
 */

class IncomeTable extends DataTable {
    /**
     * 创建收入表格组件
     * @param {Object} options - 配置选项
     */
    constructor(options) {
        // 默认配置
        const defaultOptions = {
            tableContainer: '.income-table-container',
            baseUrl: '/finance/income',
            statsElements: {
                total: 'totalIncomeAmount',
                recharge: 'rechargeIncomeAmount',
                other: 'otherIncomeAmount',
                count: 'totalIncomeCount'
            }
        };
        
        // 合并默认配置和用户配置
        super(Object.assign({}, defaultOptions, options));
        
        // 初始化收入特有事件
        this.initViewIncomeHandlers();
        this.initViewToggle();
        
        // 初始化分页处理
        this.initPaginationHandlers();
    }
    
    /**
     * 初始化查看收入详情事件处理
     */
    initViewIncomeHandlers() {
        const self = this;
        
        // 为所有查看详情按钮添加事件监听（同时处理表格和卡片视图）
        document.querySelectorAll('.view-income-btn').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const incomeId = this.getAttribute('data-income-id');
                self.viewIncomeDetails(incomeId);
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
                localStorage.setItem('incomeViewPreference', viewType);
            });
        });
        
        // 初始化时根据用户偏好设置视图
        const savedView = localStorage.getItem('incomeViewPreference');
        if (savedView) {
            document.querySelector(`.view-toggle-btn[data-view="${savedView}"]`).click();
        }
    }
    
    /**
     * 查看收入详情
     * @param {string} incomeId - 收入ID
     */
    viewIncomeDetails(incomeId) {
        if (!incomeId) return;
        
        // 获取收入信息，填充模态框
        fetch(`/finance/api/income_details/${incomeId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`请求失败: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    const income = data.data;
                    
                    // 填充模态框信息
                    document.getElementById('modal-income-id').textContent = income.id;
                    document.getElementById('modal-amount').textContent = income.amount;
                    document.getElementById('modal-source').textContent = income.source;
                    document.getElementById('modal-date').textContent = income.date;
                    document.getElementById('modal-user-id').textContent = income.user_id || 'N/A';
                    document.getElementById('modal-username').textContent = income.username || 'N/A';
                    document.getElementById('modal-description').textContent = income.description || '无描述';
                    document.getElementById('modal-created-at').textContent = income.created_at;
                    document.getElementById('modal-updated-at').textContent = income.updated_at;
                    
                    // 设置编辑链接
                    document.getElementById('edit-income-link').href = `/finance/income/edit/${income.id}`;
                    
                    // 显示模态框
                    const modal = new bootstrap.Modal(document.getElementById('incomeDetailModal'));
                    modal.show();
                    
                    // 确保关闭按钮正常工作
                    document.querySelector('#incomeDetailModal .btn-close').addEventListener('click', function() {
                        modal.hide();
                        // 确保模态框完全隐藏后移除背景遮罩
                        document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                    });
                    
                    // 确保"关闭"按钮正常工作
                    document.querySelector('#incomeDetailModal .btn-secondary').addEventListener('click', function() {
                        modal.hide();
                        // 确保模态框完全隐藏后移除背景遮罩
                        document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                    });
                } 
            })
            .catch(error => {
                console.error('获取收入详情出错:', error);
            });
    }
    
    /**
     * 初始化分页处理器
     */
    initPaginationHandlers() {
        const self = this;
        
        // 为所有页码链接添加点击事件
        document.querySelectorAll('.page-link').forEach(link => {
            // 避免重复绑定
            if (link.getAttribute('data-ajax-bound')) return;
            
            link.addEventListener('click', function(e) {
                // 阻止默认行为
                e.preventDefault();
                
                // 如果链接被禁用，不执行任何操作
                if (this.hasAttribute('aria-disabled') || this.parentElement.classList.contains('disabled')) {
                    return;
                }
                
                // 获取页码
                let pageNum = null;
                const href = this.getAttribute('href');
                
                if (href && href !== '#') {
                    // 从URL中提取页码
                    const url = new URL(href, window.location.origin);
                    pageNum = url.searchParams.get('page');
                }
                
                if (pageNum) {
                    // 保存当前链接的原始内容
                    const originalContent = this.innerHTML;
                    
                    // 添加加载中样式
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
                }
            });
            
            // 标记为已绑定
            link.setAttribute('data-ajax-bound', 'true');
        });
        
        // 为页码跳转按钮添加点击事件
        const jumpBtn = document.getElementById('jumpToPageBtn');
        if (jumpBtn) {
            // 避免重复绑定
            if (!jumpBtn.getAttribute('data-ajax-bound')) {
                jumpBtn.addEventListener('click', function() {
                    self.jumpToPageAjax();
                });
                jumpBtn.setAttribute('data-ajax-bound', 'true');
            }
            
            // 为跳转输入框添加回车键支持
            const input = document.getElementById('pageJumpInput');
            if (input && !input.getAttribute('data-ajax-bound')) {
                input.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        self.jumpToPageAjax();
                    }
                });
                input.setAttribute('data-ajax-bound', 'true');
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
        const url = this.options.baseUrl + '?' + urlParams.toString();
        
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
                this.initViewIncomeHandlers();
                this.initPaginationHandlers();
                this.initRowEvents();
                
                // 高亮显示表格容器
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
    
    /**
     * 重写initRowEvents方法，提供给DataTable使用
     */
    initRowEvents() {
        this.initViewIncomeHandlers();
        
        // 初始化删除收入按钮
        document.querySelectorAll('.delete-income-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const incomeId = button.getAttribute('data-income-id');
                if (!incomeId) return;

                if (confirm('确定要删除此收入记录吗？此操作不可撤销。')) {
                    // 发送AJAX请求删除收入
                    fetch(`/finance/income/delete/${incomeId}`, {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
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
                      
                            // 重新加载表格
                            this.reloadTable();
                        } 
                    })
                    .catch(error => {
                        console.error('删除收入记录出错:', error);
                    });
                }
            });
        });
    }
}

// 确保文档加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 创建收入表格实例并存储为全局变量
    window.incomeTable = new IncomeTable({
        initRowEvents: function() {
            window.incomeTable.initRowEvents();
        }
    });
    
    // 监听浏览器的前进/后退按钮事件
    window.addEventListener('popstate', function(event) {
        if (event.state && event.state.page) {
            // 从URL获取当前页码
            const urlParams = new URLSearchParams(window.location.search);
            const currentPage = parseInt(urlParams.get('page')) || 1;
            
            // 通过AJAX加载对应页面
            if (window.incomeTable) {
                window.incomeTable.loadPageData(currentPage);
            }
        }
    });
}); 