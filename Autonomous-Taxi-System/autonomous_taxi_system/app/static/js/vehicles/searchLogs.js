/**
 * 车辆操作日志高级搜索功能
 */
document.addEventListener('DOMContentLoaded', function() {
    // 搜索框折叠/展开功能
    const searchToggle = document.getElementById('searchToggle');
    if (searchToggle) {
        searchToggle.addEventListener('click', function() {
            // 切换搜索图标方向
            const icon = this.querySelector('i');
            icon.classList.toggle('bi-chevron-down');
            icon.classList.toggle('bi-chevron-right');
            
            // 切换展开状态类
            this.classList.toggle('collapsed');
        });
    }
    
    // 初始化日期选择器
    initDatepickers();
    
    // 提交搜索表单
    const searchForm = document.getElementById('logsSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // 移除空参数
            const formData = new FormData(this);
            const searchParams = new URLSearchParams();
            
            for (const [key, value] of formData.entries()) {
                if (value && value.trim() !== '') {
                    searchParams.append(key, value);
                }
            }
            
            // 设置分页为第一页
            searchParams.append('page', '1');
            
            // 构建URL并跳转
            const searchUrl = document.getElementById('searchUrl').getAttribute('data-url');
            window.location.href = `${searchUrl}?${searchParams.toString()}`;
        });
    }
    
    // 重置搜索表单
    const resetSearchBtn = document.getElementById('resetSearchBtn');
    if (resetSearchBtn) {
        resetSearchBtn.addEventListener('click', function() {
            // 重置表单字段
            const form = document.getElementById('logsSearchForm');
            if (form) {
                form.reset();
            }
        });
    }
    
    // 清除搜索参数全局函数
    window.clearAllSearchParams = function() {
        // 获取基础URL（不包含查询参数）
        const searchUrl = document.getElementById('searchUrl').getAttribute('data-url');
        window.location.href = searchUrl;
    };
    
    // 移除单个搜索参数全局函数
    window.removeSearchParam = function(field) {
        let url = new URL(window.location.href);
        url.searchParams.delete(field);
        window.location.href = url.toString();
    };
    
    // 视图切换按钮
    const viewToggleBtns = document.querySelectorAll('.view-toggle-btn');
    if (viewToggleBtns.length > 0) {
        viewToggleBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                // 移除所有按钮的激活状态
                viewToggleBtns.forEach(b => b.classList.remove('active'));
                
                // 添加当前按钮的激活状态
                this.classList.add('active');
                
                // 获取视图类型并存储在本地
                const viewType = this.getAttribute('data-view');
                localStorage.setItem('logViewType', viewType);
                
                // 切换视图
                toggleView(viewType);
            });
        });
        
        // 初始化视图模式
        const savedViewType = localStorage.getItem('logViewType') || 'table';
        const activeBtn = document.querySelector(`.view-toggle-btn[data-view="${savedViewType}"]`);
        if (activeBtn) {
            activeBtn.click();
        } else {
            // 默认表格视图
            document.querySelector('.view-toggle-btn[data-view="table"]')?.click();
        }
    }
});

/**
 * 初始化日期选择器
 */
function initDatepickers() {
    // 如果你使用的是Bootstrap Datepicker或其他需要初始化的日期选择器
    // 在这里添加初始化代码
    // 例如：$('.datepicker').datepicker();
    
    // 如果使用HTML5原生datetime-local，则不需要额外初始化
}

/**
 * 切换视图模式（表格/卡片）
 * @param {string} viewType - 视图类型（table/card）
 */
function toggleView(viewType) {
    const tableView = document.getElementById('tableView');
    const cardView = document.getElementById('cardView');
    
    if (viewType === 'table') {
        if (tableView) tableView.style.display = 'block';
        if (cardView) cardView.style.display = 'none';
    } else if (viewType === 'card') {
        if (tableView) tableView.style.display = 'none';
        if (cardView) cardView.style.display = 'block';
    }
}

/**
 * 显示本地Toast消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型（success/error/warning/info）
 * @param {number} duration - 持续时间（毫秒）
 */
function showLocalToast(message, type = 'info', duration = 3000) {
    const toastContainer = document.getElementById('toast-container');
    
    if (!toastContainer) {
        console.error('Toast container not found');
        return;
    }
    
    // 创建Toast元素
    const toast = document.createElement('div');
    toast.className = `custom-toast toast-${type}`;
    toast.textContent = message;
    
    // 添加到容器
    toastContainer.appendChild(toast);
    
    // 自动移除
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.5s';
        setTimeout(() => {
            toast.remove();
        }, 500);
    }, duration);
} 