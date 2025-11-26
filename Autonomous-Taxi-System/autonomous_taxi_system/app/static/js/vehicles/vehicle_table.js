/**
 * 车辆表格AJAX分页处理
 */
class VehicleTable {
    constructor(options = {}) {
        this.options = {
            tableContainerId: 'vehicles-table-container',
            tableBodyId: 'vehicles-table-body',
            paginationId: 'vehicle-pagination',
            baseUrl: '/vehicles',
            ...options
        };
        
        this.tableContainer = document.getElementById(this.options.tableContainerId);
        this.tableBody = document.getElementById(this.options.tableBodyId);
        this.pagination = document.getElementById(this.options.paginationId);
        
        this.initPaginationHandlers();
        this.initRowEvents();
        
        // 保存实例到window对象，以便popstate事件可以访问
        window.vehicleTableInstance = this;
    }
    
    /**
     * 初始化分页处理功能
     */
    initPaginationHandlers() {
        const self = this;
        
        // 为所有页码链接添加点击事件
        document.querySelectorAll('.page-link').forEach(link => {
            // 跳过已经初始化过的链接
            if (link.getAttribute('data-initialized') === 'true') {
                return;
            }
            
            link.addEventListener('click', function(e) {
                e.preventDefault();
                
                // 如果链接被禁用，不执行任何操作
                if (this.parentElement.classList.contains('disabled')) {
                    return;
                }
                
                // 解析链接URL中的页码
                const href = this.getAttribute('href');
                if (href && href !== '#') {
                    const url = new URL(href, window.location.origin);
                    const pageNum = url.searchParams.get('page') || 1;
                    
                    // 保存原始内容
                    const originalContent = this.innerHTML;
                    
                    // 添加加载中样式
                    this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
                    
                    // 禁用所有页码链接，防止重复点击
                    document.querySelectorAll('.page-link').forEach(l => {
                        l.style.pointerEvents = 'none';
                    });
                    
                    // 加载页面数据
                    self.loadPageData(pageNum);
                    
                    // 延迟后恢复所有页码链接
                    setTimeout(() => {
                        document.querySelectorAll('.page-link').forEach(l => {
                            l.style.pointerEvents = '';
                        });
                    }, 500);
                }
            });
            
            // 标记为已初始化
            link.setAttribute('data-initialized', 'true');
        });
        
        // 为页码跳转按钮添加点击事件
        const jumpBtn = document.querySelector('button[onclick="pageTableJump()"]');
        if (jumpBtn) {
            // 移除原有的onclick属性
            jumpBtn.removeAttribute('onclick');
            
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
     * 初始化表格行事件（如查看、编辑、删除等按钮）
     */
    initRowEvents() {
        // 为了保持代码简洁，这里不实现详细的行事件处理
        // 在完整实现中，这里应该重新绑定表格行的所有事件处理器
        
        // 重新初始化查看、编辑、删除按钮事件
        this.initViewButtons();
        this.initEditButtons();
        this.initDeleteButtons();
        this.initRescueButtons();
    }
    
    /**
     * 初始化查看按钮事件
     */
    initViewButtons() {
        document.querySelectorAll('.view-vehicle-btn').forEach(btn => {
            // 跳过已经初始化过的按钮
            if (btn.getAttribute('data-initialized') === 'true') {
                return;
            }
            
            btn.addEventListener('click', function() {
                const vehicleId = this.getAttribute('data-vehicle-id');
                if (vehicleId) {
                    // 调用全局的showVehicleDetails函数或vehicleDetailsViewer函数
                    if (typeof window.showVehicleDetails === 'function') {
                        window.showVehicleDetails(vehicleId);
                    } else if (typeof window.vehicleDetailsViewer === 'function') {
                        window.vehicleDetailsViewer(vehicleId);
                    } else {
                        // Fallback: 直接使用模态框
                        const modal = document.getElementById('vehicleDetailsModal');
                        if (modal) {
                            const modalContent = document.getElementById('vehicleDetailsContent');
                            if (modalContent) {
                                modalContent.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>加载中...</p></div>';
                                const bsModal = new bootstrap.Modal(modal);
                                bsModal.show();
                                
                                // 获取车辆详情
                                fetch(`/vehicles/api/vehicle_details/${vehicleId}`)
                                    .then(response => response.json())
                                    .then(data => {
                                        if (data.status === 'success') {
                                            modalContent.innerHTML = `<div class="alert alert-info">车辆详情加载完成，ID: ${vehicleId}</div>`;
                                        } else {
                                            modalContent.innerHTML = `<div class="alert alert-danger">加载失败: ${data.message || '未知错误'}</div>`;
                                        }
                                    })
                                    .catch(error => {
                                        modalContent.innerHTML = `<div class="alert alert-danger">请求错误: ${error.message}</div>`;
                                    });
                            }
                        }
                    }
                }
            });
            
            // 标记为已初始化
            btn.setAttribute('data-initialized', 'true');
        });
    }
    
    /**
     * 初始化编辑按钮事件
     */
    initEditButtons() {
        document.querySelectorAll('.edit-vehicle-btn').forEach(btn => {
            if (btn.getAttribute('data-initialized') === 'true') {
                return;
            }
            
            btn.addEventListener('click', function() {
                const vehicleId = this.getAttribute('data-vehicle-id');
                if (vehicleId) {
                    // 直接跳转到编辑页面，注意路径必须与后端路由匹配
                    const urlParams = new URLSearchParams(window.location.search);
                    const page = urlParams.get('page') || 1;
                    
                    // 构建编辑URL，并保留所有搜索参数
                    // 修改为正确的路由路径：/vehicles/edit_vehicle/123 -> /vehicles/edit_vehicle/123
                    const editUrl = new URL(`/vehicles/edit_vehicle/${vehicleId}`, window.location.origin);
                    editUrl.searchParams.set('page', page);
                    
                    // 添加其他搜索参数
                    urlParams.forEach((value, key) => {
                        if (key !== 'page' && key !== 'ajax' && key !== 'include_stats') {
                            editUrl.searchParams.set(key, value);
                        }
                    });
                    
                    // 打印URL以便调试
                    console.log('跳转到编辑页面:', editUrl.toString());
                    
                    window.location.href = editUrl.toString();
                }
            });
            
            btn.setAttribute('data-initialized', 'true');
        });
    }
    
    /**
     * 初始化删除按钮事件
     */
    initDeleteButtons() {
        document.querySelectorAll('.delete-vehicle-btn').forEach(btn => {
            if (btn.getAttribute('data-initialized') === 'true') {
                return;
            }
            
            btn.addEventListener('click', function() {
                const vehicleId = this.getAttribute('data-vehicle-id');
                if (vehicleId) {
                    // 调用全局的confirmDeleteVehicle函数
                    if (typeof window.confirmDeleteVehicle === 'function') {
                        window.confirmDeleteVehicle(vehicleId);
                    } else {
                        // Fallback: 使用确认框
                        const deleteModal = document.getElementById('deleteConfirmModal');
                        if (deleteModal) {
                            const deleteForm = document.getElementById('deleteForm');
                            if (deleteForm) {
                                // 构建删除URL，修正URL路径
                                const urlParams = new URLSearchParams(window.location.search);
                                const page = urlParams.get('page') || 1;
                                
                                // 修正URL路径，与后端路由一致
                                let deleteUrl = `/vehicles/delete_vehicle/${vehicleId}?page=${page}`;
                                
                                // 打印URL以便调试
                                console.log('删除车辆URL:', deleteUrl);
                                
                                // 添加其他搜索参数
                                urlParams.forEach((value, key) => {
                                    if (key !== 'page' && key !== 'ajax' && key !== 'include_stats') {
                                        deleteUrl += `&${key}=${value}`;
                                    }
                                });
                                
                                deleteForm.action = deleteUrl;
                                const bsModal = new bootstrap.Modal(deleteModal);
                                bsModal.show();
                            }
                        }
                    }
                }
            });
            
            btn.setAttribute('data-initialized', 'true');
        });
    }
    
    /**
     * 初始化救援按钮事件
     */
    initRescueButtons() {
        document.querySelectorAll('.rescue-vehicle-btn').forEach(btn => {
            if (btn.getAttribute('data-initialized') === 'true') {
                return;
            }
            
            btn.addEventListener('click', function() {
                const vehicleId = this.getAttribute('data-vehicle-id');
                if (vehicleId) {
                    // 调用全局的rescueVehicle函数
                    if (typeof window.rescueVehicle === 'function') {
                        window.rescueVehicle(vehicleId);
                    } else {
                        // Fallback: 直接发送救援请求
                        const confirmMessage = '确定要对该车辆执行救援操作吗？';
                        if (confirm(confirmMessage)) {
                            fetch(`/vehicles/api/rescue_vehicle/${vehicleId}`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-Requested-With': 'XMLHttpRequest'
                                }
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.status === 'success') {
                                    // 可以考虑刷新表格
                                    setTimeout(() => this.loadPageData(window.currentPage || 1), 1000);
                                } 
                            })
                            .catch(error => {
                            });
                        }
                    }
                }
            });
            
            btn.setAttribute('data-initialized', 'true');
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
        
        // 添加AJAX标识
        urlParams.set('ajax', '1');
        
        // 保存当前页码到localStorage
        localStorage.setItem('vehicleCurrentPage', pageNum);
        
        // 构建请求URL
        const url = `${this.options.baseUrl}?${urlParams.toString()}`;
        
        // 创建加载指示器
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div>';
        
        // 确保表格容器有相对定位
        if (!this.tableContainer) {
            console.error('表格容器未找到');
            return;
        }
        
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
                throw new Error('网络响应错误: ' + response.status);
            }
            // 检查Content-Type来决定如何处理响应
            const contentType = response.headers.get('Content-Type');
            if (contentType && contentType.includes('application/json')) {
                return response.json();
            } else {
                return response.text();
            }
        })
        .then(data => {
            // 移除加载指示器
            loadingOverlay.remove();
            
            // 处理JSON或HTML响应
            if (typeof data === 'object' && data.html) {
                // JSON响应中包含HTML片段
                this.tableContainer.innerHTML = data.html;
                
                // 如果JSON中包含其他数据，可以在这里处理
                if (data.current_page) {
                    window.currentPage = data.current_page;
                }
                
                if (data.total_count !== undefined && data.per_page !== undefined && data.offset !== undefined) {
                    this.updateCountInfo(data);
                }
            } else if (typeof data === 'string') {
                // 直接的HTML响应
                this.tableContainer.innerHTML = data;
            } else {
                throw new Error('服务器返回了无效的数据格式');
            }
            
            // 更新URL，不刷新页面（使用History API）
            const stateObj = { page: pageNum };
            const newUrl = window.location.pathname + '?' + urlParams.toString();
            history.pushState(stateObj, '', newUrl);
            
            // 重新初始化分页事件处理程序
            this.initPaginationHandlers();
            
            // 重新初始化行事件（如查看、编辑、删除等按钮）
            this.initRowEvents();
            
            // 高亮显示表格容器，表明内容已更新
            this.highlightTableContainer();
            
            // 如果全局存在bindTableEvents函数，也调用它（确保完全兼容原有代码）
            if (typeof window.bindTableEvents === 'function') {
                window.bindTableEvents();
            }
            
            // 提取并更新统计信息（如果在DOM中有这个元素）
            const countInfo = document.getElementById('vehicle-count-info');
            if (countInfo && typeof data === 'string') {
                this.updateCountInfo(countInfo.textContent);
            }
        })
        .catch(error => {
            console.error('加载页面数据失败:', error);
            
            // 移除加载指示器
            loadingOverlay.remove();
            
            // 显示错误消息
        });
    }
    
    /**
     * 更新计数信息
     */
    updateCountInfo(data) {
        const countInfoEl = document.getElementById('vehicle-count-info');
        if (countInfoEl && data.offset !== undefined && data.per_page !== undefined && data.total_count !== undefined) {
            const start = data.offset + 1;
            const end = Math.min(data.offset + data.per_page, data.total_count);
            countInfoEl.textContent = `显示 ${start} 到 ${end} 条，共 ${data.total_count} 条`;
        }
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
     * 显示提示消息
     */
    showToast(message, type = 'info') {
        // 如果页面有toast组件，则使用它
        if (typeof showToast === 'function') {
            showToast(message, type);
        } else {
            // 简单的alert回退
            alert(message);
        }
    }
    
    /**
     * 使用AJAX跳转到指定页码
     */
    jumpToPageAjax() {
        const input = document.getElementById('pageJumpInput');
        if (!input) return;
        
        const pageNum = parseInt(input.value);
        const maxPage = parseInt(input.getAttribute('max') || input.placeholder.split('/')[1] || 1);
        
        if (pageNum && pageNum >= 1 && pageNum <= maxPage) {
            // 保存页码到localStorage
            localStorage.setItem('vehicleCurrentPage', pageNum);
            
            // 禁用输入框和按钮，显示加载中状态
            input.disabled = true;
            const jumpBtn = document.querySelector('button[onclick="pageTableJump()"]') || 
                           document.querySelector('button:has(+ #pageJumpInput)');
            
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
                    jumpBtn.innerHTML = '跳转';
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

// 监听浏览器的前进/后退按钮事件
window.addEventListener('popstate', function(event) {
    // 从URL获取当前页码
    const urlParams = new URLSearchParams(window.location.search);
    const currentPage = parseInt(urlParams.get('page')) || 1;
    
    // 通过AJAX加载对应页面
    if (window.vehicleTableInstance) {
        window.vehicleTableInstance.loadPageData(currentPage);
    }
});

// 在页面加载完成后初始化表格
document.addEventListener('DOMContentLoaded', function() {
    // 创建并初始化车辆表格
    const vehicleTable = new VehicleTable();
}); 