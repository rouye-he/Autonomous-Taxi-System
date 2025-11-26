/**
 * 用户表格组件
 * 扩展通用数据表格组件，处理用户管理特有的功能
 */

class UserTable extends DataTable {
    /**
     * 创建用户表格组件
     * @param {Object} options - 配置选项
     */
    constructor(options) {
        // 默认配置
        const defaultOptions = {
            tableContainer: '.user-table-container',
            baseUrl: '/users',
            statsElements: {
                total: 'userTotalCount'
            },
            showToastOnRefresh: true
        };
        
        // 合并默认配置和用户配置
        super(Object.assign({}, defaultOptions, options));
        
        // 初始化用户特有事件
        this.initViewDetailsHandlers();
        this.initDeleteHandlers();
        this.initEditFormHandlers();
    }
    
    /**
     * 初始化查看详情的事件处理
     */
    initViewDetailsHandlers() {
        const self = this;
        
        // 为所有查看详情按钮添加事件监听
        document.querySelectorAll('.view-details-btn').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const userId = this.getAttribute('data-user-id');
                self.loadUserDetails(userId);
            });
        });
    }
    
    /**
     * 初始化删除用户的事件处理
     */
    initDeleteHandlers() {
        const self = this;
        
        // 为所有删除按钮添加事件监听
        document.querySelectorAll('.delete-btn').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const userId = this.getAttribute('data-user-id');
                const page = this.getAttribute('data-page');
                const searchParams = this.getAttribute('data-search-params') || '';
                self.confirmDelete(userId, page, searchParams);
            });
        });
    }
    
    /**
     * 加载用户详情
     * @param {string} userId - 用户ID
     */
    loadUserDetails(userId) {
        if (!userId) return;
        
        // 显示加载中提示
        const modalBody = document.querySelector('#userDetailsModal .modal-body .row');
        if (modalBody) {
            modalBody.innerHTML = '<div class="col-12 text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div></div>';
        }
        
        // 显示模态框
        const userDetailsModal = new bootstrap.Modal(document.getElementById('userDetailsModal'));
        userDetailsModal.show();
        
        // 获取用户详情
        fetch('/users/details/' + userId, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('获取用户详情失败');
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.user) {
                // 填充用户详情
                modalBody.innerHTML = this.formatUserDetails(data.user);
            } else {
                modalBody.innerHTML = '<div class="col-12 text-center text-danger">获取用户详情失败</div>';
            }
        })
        .catch(error => {
            console.error('获取用户详情出错:', error);
            modalBody.innerHTML = '<div class="col-12 text-center text-danger">获取用户详情出错: ' + error.message + '</div>';
        });
    }
    
    /**
     * 格式化用户详情
     * @param {Object} user - 用户数据
     * @returns {string} HTML字符串
     */
    formatUserDetails(user) {
        if (!user) return '<div class="col-12">无数据</div>';
        
        // 日期格式化函数
        const formatDate = (dateString) => {
            if (!dateString) return '-';
            
            try {
                const date = new Date(dateString);
                // 检查日期是否有效
                if (isNaN(date.getTime())) return '-';
                
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                
                return `${year}-${month}-${day}`;
            } catch (e) {
                console.error('日期格式化错误:', e);
                return dateString; // 返回原始字符串
            }
        };
        
        // 处理用户标签
        const formatTags = (tags) => {
            if (!tags) return '';
            
            let tagsList = [];
            
            // 处理不同格式的tags
            if (typeof tags === 'string') {
                tagsList = tags.split(',').filter(tag => tag.trim());
            } else if (Array.isArray(tags)) {
                tagsList = tags.filter(tag => tag && tag.trim());
            }
            
            if (tagsList.length === 0) return '';
            
            let html = '<div class="mt-2">';
            tagsList.forEach(tag => {
                html += `<span class="badge bg-info me-1">${tag.trim()}</span>`;
            });
            html += '</div>';
            
            return html;
        };
        
        // 构建详情HTML - 使用卡片布局
        return `
            <!-- 第一行：基本信息和账户信息 -->
            <div class="col-md-6 mb-3">
                <div class="card h-100">
                    <div class="card-header bg-light">
                        <h5 class="mb-0">基本信息</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <div class="d-flex justify-content-between align-items-center">
                                <h4 class="mb-0">
                                    ${user.username || '-'}
                                    <span class="badge ${this.getStatusBadgeClass(user.status)}">${user.status || '-'}</span>
                                </h4>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-6">
                                <p class="text-muted mb-1">用户ID</p>
                                <p class="fw-bold mb-0">${user.user_id || '-'}</p>
                            </div>
                            <div class="col-6">
                                <p class="text-muted mb-1">真实姓名</p>
                                <p class="fw-bold mb-0">${user.real_name || '-'}</p>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-6">
                                <p class="text-muted mb-1">性别</p>
                                <p class="fw-bold mb-0">${user.gender || '-'}</p>
                            </div>
                            <div class="col-6">
                                <p class="text-muted mb-1">出生日期</p>
                                <p class="fw-bold mb-0">${formatDate(user.birth_date)}</p>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-6">
                                <p class="text-muted mb-1">手机号</p>
                                <p class="fw-bold mb-0">${user.phone || '-'}</p>
                            </div>
                            <div class="col-6">
                                <p class="text-muted mb-1">邮箱</p>
                                <p class="fw-bold mb-0">${user.email || '-'}</p>
                            </div>
                        </div>
                        <div class="row mb-0">
                            <div class="col-12">
                                <p class="text-muted mb-1">身份证号</p>
                                <p class="fw-bold mb-0">${user.id_card || '-'}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6 mb-3">
                <div class="card h-100">
                    <div class="card-header bg-light">
                        <h5 class="mb-0">账户信息</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-4">
                            <p class="text-muted mb-1">信用分</p>
                            <div class="progress" style="height: 25px;position: relative">
                                <div class="progress-bar ${user.credit_score >= 80 ? 'bg-success' : user.credit_score >= 60 ? 'bg-info' : user.credit_score >= 40 ? 'bg-warning' : 'bg-danger'}" 
                                     role="progressbar" 
                                     style="width: ${user.credit_score}%;" 
                                     aria-valuenow="${user.credit_score}" 
                                     aria-valuemin="0" 
                                     aria-valuemax="100">
                                </div>
                                <span style="color: #000; position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center;">${user.credit_score || 0}分</span>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-12">
                                <p class="text-muted mb-1">账户余额</p>
                                <p class="fw-bold mb-0 fs-4">${user.balance !== undefined ? '¥' + user.balance.toFixed(2) : '-'}</p>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-12">
                                <p class="text-muted mb-1">标签</p>
                                <div>${formatTags(user.tags) || '<span class="text-muted">无标签</span>'}</div>
                            </div>
                        </div>
                        
                    </div>
                </div>
            </div>
            
            <!-- 第二行：注册信息和系统信息 -->
            <div class="col-md-6 mb-3">
                <div class="card h-100">
                    <div class="card-header bg-light">
                        <h5 class="mb-0">注册信息</h5>
                    </div>
                    <div class="card-body">
                        <div class="row mb-3">
                            <div class="col-6">
                                <p class="text-muted mb-1">注册时间</p>
                                <p class="fw-bold mb-0">${formatDate(user.registration_time)}</p>
                            </div>
                            <div class="col-6">
                                <p class="text-muted mb-1">最后登录时间</p>
                                <p class="fw-bold mb-0">${formatDate(user.last_login_time)}</p>
                            </div>
                        </div>
                        <div class="row mb-0">
                            <div class="col-6">
                                <p class="text-muted mb-1">注册城市</p>
                                <p class="fw-bold mb-0">${user.registration_city || '-'}</p>
                            </div>
                            <div class="col-6">
                                <p class="text-muted mb-1">注册渠道</p>
                                <p class="fw-bold mb-0">${user.registration_channel || '-'}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6 mb-3">
                <div class="card h-100">
                    <div class="card-header bg-light">
                        <h5 class="mb-0">系统信息</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6 mb-3">
                                <p class="text-muted mb-1">创建时间</p>
                                <p class="fw-bold mb-0">${formatDate(user.created_at)}</p>
                            </div>
                            <div class="col-6 mb-3">
                                <p class="text-muted mb-1">更新时间</p>
                                <p class="fw-bold mb-0">${formatDate(user.updated_at)}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 按钮操作区 -->
            <div class="col-12 mt-3">
                <div class="card">
                    <div class="card-body d-flex justify-content-end">
                        <a href="/orders/advanced_search?user_id=${user.user_id}" class="btn btn-primary" target="_blank">
                            <i class="bi bi-clock-history"></i> 查看历史订单
                        </a>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * 根据状态获取对应的Badge类名
     * @param {string} status - 用户状态
     * @returns {string} Badge类名
     */
    getStatusBadgeClass(status) {
        switch(status) {
            case '正常':
                return 'bg-success';
            case '禁用':
                return 'bg-danger';
            case '注销':
                return 'bg-secondary';
            default:
                return 'bg-info';
        }
    }
    
    /**
     * 删除用户
     * @param {string} userId - 用户ID
     */
    deleteUser(userId) {
        if (!userId) return;
        
        // 请求删除用户
        fetch(`/users/delete/${userId}`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            // 隐藏确认框
            const deleteConfirmModal = bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal'));
            if (deleteConfirmModal) {
                deleteConfirmModal.hide();
            }
            
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || '删除用户失败');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // 显示成功消息
                
                // 立即刷新表格
                this.reloadTable();
            } 
        })
        .catch(error => {
            console.error('删除用户出错:', error);
        });
    }
    
    /**
     * 确认删除用户
     * @param {string} userId - 用户ID
     * @param {string} page - 当前页码
     * @param {string} searchParams - 搜索参数
     */
    confirmDelete(userId, page, searchParams) {
        if (!userId) return;
        
        // 在Modal内设置确认删除的事件
        const confirmBtn = document.querySelector('#deleteConfirmModal .btn-danger');
        if (confirmBtn) {
            // 清除之前的事件监听器（如果有）
            const newConfirmBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
            
            // 添加新的事件监听器
            newConfirmBtn.addEventListener('click', e => {
                e.preventDefault();
                
                // 隐藏确认框
                const deleteConfirmModal = bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal'));
                if (deleteConfirmModal) {
                    deleteConfirmModal.hide();
                }
                
                // 执行删除
                this.deleteUser(userId);
            });
        }
        
        // 显示确认删除模态框
        const deleteConfirmModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
        deleteConfirmModal.show();
    }
    
    /**
     * 重写initRowEvents方法，提供给DataTable使用
     */
    initRowEvents() {
        this.initViewDetailsHandlers();
        this.initDeleteHandlers();
    }
    
    /**
     * 初始化编辑表单处理
     */
    initEditFormHandlers() {
        // 检查当前页面是否是编辑页面
        const editForm = document.querySelector('form[action*="/users/edit/"]');
        if (!editForm) return;
        
        // 监听表单提交事件
        editForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // 获取表单数据
            const formData = new FormData(editForm);
            const userId = window.location.pathname.split('/').pop();
            
            // 发送AJAX请求
            fetch(`/users/edit/${userId}`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // 显示成功消息
                    
                    // 准备返回URL
                    let returnUrl = '';
                    const page = formData.get('page') || '1';
                    
                    // 判断是否有搜索参数
                    const searchParams = {};
                    for (const [key, value] of formData.entries()) {
                        if (key !== 'page' && key !== 'username' && key !== 'real_name' && 
                            key !== 'phone' && key !== 'email' && key !== 'gender' && 
                            key !== 'birth_date' && key !== 'id_card' && key !== 'credit_score' && 
                            key !== 'balance' && key !== 'status' && key !== 'registration_city' && 
                            key !== 'registration_channel' && key !== 'tags') {
                            searchParams[key] = value;
                        }
                    }
                    
                    // 构建URL
                    if (Object.keys(searchParams).length > 0) {
                        returnUrl = `/users/advanced_search?page=${page}`;
                        for (const key in searchParams) {
                            returnUrl += `&${key}=${encodeURIComponent(searchParams[key])}`;
                        }
                    } else {
                        returnUrl = `/users?page=${page}`;
                    }
                    
                    // 显示成功提示和返回按钮
                    this.showSuccessAlert(returnUrl);
                    
                    // 禁用提交按钮，防止重复提交
                    const submitButton = editForm.querySelector('button[type="submit"]');
                    if (submitButton) {
                        submitButton.disabled = true;
                        submitButton.innerHTML = '<i class="bi bi-check-circle"></i> 已保存';
                    }
                } 
            })
            .catch(error => {
                console.error('编辑用户出错:', error);
            });
        });
    }
    
    /**
     * 显示成功提示和返回按钮
     * @param {string} returnUrl - 返回链接
     */
    showSuccessAlert(returnUrl) {
        // 查找表单上方的容器，用于显示提示
        const formCard = document.querySelector('form').closest('.card');
        if (!formCard) return;
        
        // 创建成功提示
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show mt-3';
        alertDiv.innerHTML = `
            <strong><i class="bi bi-check-circle"></i> 保存成功!</strong> 用户信息已成功更新。
            <div class="mt-2">
                <a href="${returnUrl}" class="btn btn-sm btn-outline-success">
                    <i class="bi bi-arrow-left"></i> 返回用户列表
                </a>
                <button type="button" class="btn btn-sm btn-outline-secondary ms-2" id="continueEditBtn">
                    <i class="bi bi-pencil"></i> 继续编辑
                </button>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // 插入到表单之前
        formCard.parentNode.insertBefore(alertDiv, formCard);
        
        // 滚动到提示区域
        alertDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // 为"继续编辑"按钮添加事件
        document.getElementById('continueEditBtn').addEventListener('click', function() {
            // 关闭提示
            const bsAlert = bootstrap.Alert.getInstance(alertDiv);
            if (bsAlert) {
                bsAlert.close();
            } else {
                alertDiv.remove();
            }
            
            // 重新启用提交按钮
            const submitButton = document.querySelector('form button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = '保存修改';
            }
        });
    }
}

// 确保文档加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 创建用户表格实例并存储为全局变量
    window.userTable = new UserTable({
        initRowEvents: function() {
            window.userTable.initRowEvents();
        }
    });
    
    // 初始化编辑表单处理
    window.userTable.initEditFormHandlers();
}); 