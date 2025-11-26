/**
 * 车辆管理页面的JavaScript功能
 */

// 确保能够使用showToast函数
window.showToast = function(message, type = 'info', duration = 3000) {
    // 检查是否已有toast容器，没有则创建
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // 创建toast元素
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type}`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    // 设置toast内容
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // 添加到容器
    toastContainer.appendChild(toastEl);
    
    // 初始化toast
    const toast = new bootstrap.Toast(toastEl, { 
        autohide: true,
        delay: duration
    });
    
    // 显示toast
    toast.show();
    
    // toast隐藏后移除DOM元素
    toastEl.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
};

// 兼容旧代码
function showLocalToast(message, type = 'info', duration = 3000) {
    window.showToast(message, type, duration);
}

// 获取状态徽章样式
function getStatusBadgeClass(status) {
    switch (status) {
        case '空闲中':
            return 'bg-success';
        case '运行中':
            return 'bg-primary';
        case '充电中':
            return 'bg-info';
        case '前往充电':
            return 'bg-purple';
        case '等待充电':
            return 'bg-danger';
        case '电量不足':
            return 'bg-danger';
        case '维护中':
            return 'bg-warning';
        default:
            return 'bg-secondary';
    }
}

// 获取电量进度条样式
function getBatteryBarClass(level) {
    if (level < 20) {
        return 'bg-danger';
    } else if (level < 50) {
        return 'bg-warning';
    } else {
        return 'bg-success';
    }
}

// 显示车辆详情 - 确保全局可用
window.vehicleDetailsViewer = function(vehicleId) {
    console.log('调用vehicleDetailsViewer:', vehicleId);
    const modal = document.getElementById('vehicleDetailsModal');
    const modalContent = document.getElementById('vehicleDetailsContent');
    
    if (!modal || !modalContent) {
        console.error('找不到车辆详情模态框元素');
        return;
    }
    
    // 显示加载中
    modalContent.innerHTML = `
        <div class="col-12 text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
        </div>
    `;
    
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
    const vehicleDetailsModal = new bootstrap.Modal(modal);
    vehicleDetailsModal.show();
    
    // 获取车辆详情
    fetch(`/vehicles/api/vehicle_details/${vehicleId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // 构建详情HTML
                const vehicle = data.data;
                console.log('加载到车辆详情数据:', vehicle); // 调试日志
                modalContent.innerHTML = createVehicleDetailsHtml(vehicle);
            } else {
                modalContent.innerHTML = `
                    <div class="col-12">
                        <div class="alert alert-danger">
                            加载车辆详情失败: ${data.message}
                        </div>
                    </div>
                `;
            }
        })
        .catch(error => {
            modalContent.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        加载车辆详情发生错误: ${error}
                    </div>
                </div>
            `;
        });
    
    // 初始化模态框关闭处理
    initVehicleModalCloseHandler();
};

// 初始化车辆详情模态框关闭事件处理
function initVehicleModalCloseHandler() {
    const modal = document.getElementById('vehicleDetailsModal');
    if (modal) {
        // 添加hidden.bs.modal事件监听
        modal.addEventListener('hidden.bs.modal', function() {
            // 移除所有modal-backdrop元素
            const backdrops = document.getElementsByClassName('modal-backdrop');
            while (backdrops.length > 0) {
                backdrops[0].parentNode.removeChild(backdrops[0]);
            }
            // 移除body上的modal-open类
            document.body.classList.remove('modal-open');
            // 移除添加到body的style属性
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        });
        
        // 为关闭按钮添加点击事件
        const closeButtons = modal.querySelectorAll('[data-bs-dismiss="modal"]');
        closeButtons.forEach(button => {
            button.addEventListener('click', function() {
                // 延迟一点时间手动清理背景
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

// 编辑车辆 - 确保全局可用
window.editVehicle = function(vehicleId) {
    console.log('调用editVehicle:', vehicleId);
    // 跳转到编辑页面
    const url = `/vehicles/edit_vehicle/${vehicleId}?page=${window.currentPage || 1}`;
    
    // 添加当前URL的查询参数
    const currentUrl = new URL(window.location.href);
    const searchParams = currentUrl.searchParams;
    let hasParams = false;
    
    searchParams.forEach((value, key) => {
        if (key !== 'page' && key !== 'ajax' && key !== 'include_stats') {
            url += `&${key}=${value}`;
            hasParams = true;
        }
    });
    
    window.location.href = url;
};

// 确认删除车辆 - 确保全局可用
window.confirmDeleteVehicle = function(vehicleId) {
    console.log('调用confirmDeleteVehicle:', vehicleId);
    const deleteModal = document.getElementById('deleteConfirmModal');
    const deleteForm = document.getElementById('deleteForm');
    
    if (!deleteModal || !deleteForm) {
        console.error('找不到删除确认模态框元素');
        return;
    }
    
    // 设置表单的action属性
    deleteForm.action = `/vehicles/delete_vehicle/${vehicleId}?page=${window.currentPage || 1}`;
    
    // 添加当前URL的查询参数
    const currentUrl = new URL(window.location.href);
    const searchParams = currentUrl.searchParams;
    
    searchParams.forEach((value, key) => {
        if (key !== 'page' && key !== 'ajax' && key !== 'include_stats') {
            deleteForm.action += `&${key}=${value}`;
        }
    });
    
    // 移除之前的事件监听器
    const newDeleteForm = deleteForm.cloneNode(true);
    deleteForm.parentNode.replaceChild(newDeleteForm, deleteForm);
    
    // 为新表单添加提交事件
    newDeleteForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        fetch(this.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            // 隐藏确认框
            const modal = bootstrap.Modal.getInstance(deleteModal);
            if (modal) {
                modal.hide();
                
                // 手动清理背景
                setTimeout(() => {
                    const backdrops = document.getElementsByClassName('modal-backdrop');
                    while (backdrops.length > 0) {
                        backdrops[0].parentNode.removeChild(backdrops[0]);
                    }
                    document.body.classList.remove('modal-open');
                    document.body.style.overflow = '';
                    document.body.style.paddingRight = '';
                }, 150);
            }
            
            if (data.status === 'success') {
                showLocalToast(data.message, 'success');
                
                // 如果返回了重定向URL，执行重定向
                if (data.redirect) {
                    setTimeout(() => {
                        window.location.href = data.redirect;
                    }, 1000);
                }
            } else {
                showLocalToast(`删除失败: ${data.message}`, 'error');
            }
        })
        .catch(error => {
            showLocalToast(`删除操作出错: ${error}`, 'error');
        });
    });
    
    // 确保移除旧的modal-backdrop元素
    const existingBackdrops = document.getElementsByClassName('modal-backdrop');
    while (existingBackdrops.length > 0) {
        existingBackdrops[0].parentNode.removeChild(existingBackdrops[0]);
    }
    
    // 移除body上的modal-open类和内联样式
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
    
    // 为取消按钮添加点击事件
    const cancelButtons = deleteModal.querySelectorAll('button[data-bs-dismiss="modal"]');
    cancelButtons.forEach(button => {
        // 移除旧的事件监听器
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        
        // 添加新的事件监听器
        newButton.addEventListener('click', function() {
            // 获取并隐藏模态框
            const modal = bootstrap.Modal.getInstance(deleteModal);
            if (modal) {
                modal.hide();
            }
            
            // 手动清理背景
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
    
    // 添加hidden.bs.modal事件监听
    deleteModal.addEventListener('hidden.bs.modal', function() {
        // 移除所有modal-backdrop元素
        const backdrops = document.getElementsByClassName('modal-backdrop');
        while (backdrops.length > 0) {
            backdrops[0].parentNode.removeChild(backdrops[0]);
        }
        // 移除body上的modal-open类
        document.body.classList.remove('modal-open');
        // 移除添加到body的style属性
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    });
    
    // 显示确认模态框
    const modal = new bootstrap.Modal(deleteModal);
    modal.show();
};

// 救援车辆 - 确保全局可用
window.rescueVehicle = function(vehicleId) {
    console.log('调用rescueVehicle:', vehicleId);
    
    if (!confirm('确定要救援这辆车辆吗？车辆电量将恢复到100%。')) {
        return;
    }
    
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
            showToast(data.message, 'success');
            // 刷新表格数据
            reloadTableData();
        } else {
            showToast(data.message || '救援操作失败', 'danger');
        }
    })
    .catch(error => {
        console.error('救援操作失败:', error);
        showToast('操作失败，请稍后重试', 'danger');
    });
};

// 创建车辆详情HTML
function createVehicleDetailsHtml(vehicle) {
    console.log('正在生成车辆详情HTML，车辆ID:', vehicle.vehicle_id);
    
    // 状态标签样式
    const statusClass = getStatusBadgeClass(vehicle.current_status);
    // 电量进度条样式
    const batteryClass = getBatteryBarClass(vehicle.battery_level);
    
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
    
    // 计算使用时间（从生产日期到现在）
    let usedMonths = '-';
    if (vehicle.manufacture_date) {
        const manufactureDate = new Date(vehicle.manufacture_date);
        const now = new Date();
        usedMonths = (now.getFullYear() - manufactureDate.getFullYear()) * 12 + now.getMonth() - manufactureDate.getMonth();
        usedMonths = `${usedMonths}个月`;
    }
    
    // 格式化货币
    const formatCurrency = (value) => {
        if (value === null || value === undefined) return '-';
        return `¥${parseFloat(value).toFixed(2)}`;
    };
    
    // 可用状态
    const availableStatus = vehicle.is_available ? 
        '<span class="badge bg-success">可用</span>' : 
        '<span class="badge bg-danger">不可用</span>';
    
    return `
        <!-- 第一行：基本信息和状态 -->
        <div class="col-md-6 mb-3">
            <div class="card h-100">
                <div class="card-header bg-light">
                    <h5 class="mb-0">基本信息</h5>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <div class="d-flex justify-content-between align-items-center">
                            <h4 class="mb-0">
                                ${vehicle.plate_number}
                                <span class="badge ${statusClass}">${vehicle.current_status}</span>
                            </h4>
                            <div>
                                <a href="javascript:void(0)" onclick="editVehicle(${vehicle.vehicle_id})" class="btn btn-sm btn-outline-primary me-1">
                                    <i class="bi bi-pencil"></i> 编辑
                                </a>
                                <a href="javascript:void(0)" onclick="confirmDeleteVehicle(${vehicle.vehicle_id})" class="btn btn-sm btn-outline-danger">
                                    <i class="bi bi-trash"></i> 删除
                                </a>
                            </div>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-6">
                            <p class="text-muted mb-1">车辆ID</p>
                            <p class="fw-bold mb-0">${vehicle.vehicle_id}</p>
                        </div>
                        <div class="col-6">
                            <p class="text-muted mb-1">车辆型号</p>
                            <p class="fw-bold mb-0">${vehicle.model || '-'}</p>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-6">
                            <p class="text-muted mb-1">车辆VIN码</p>
                            <p class="fw-bold mb-0">${vehicle.vin || '-'}</p>
                        </div>
                        <div class="col-6">
                            <p class="text-muted mb-1">运营城市</p>
                            <p class="fw-bold mb-0">${vehicle.operating_city || '-'}</p>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-6">
                            <p class="text-muted mb-1">当前城市</p>
                            <p class="fw-bold mb-0">${vehicle.current_city || '-'}</p>
                        </div>
                        <div class="col-6">
                            <p class="text-muted mb-1">车辆状态</p>
                            <p class="fw-bold mb-0">${availableStatus}</p>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-6">
                            <p class="text-muted mb-1">注册日期</p>
                            <p class="fw-bold mb-0">${formatDate(vehicle.registration_date)}</p>
                        </div>
                        <div class="col-6">
                            <p class="text-muted mb-1">生产日期</p>
                            <p class="fw-bold mb-0">${formatDate(vehicle.manufacture_date)}</p>
                        </div>
                    </div>
                    <div class="row mb-0">
                        <div class="col-6">
                            <p class="text-muted mb-1">使用时间</p>
                            <p class="fw-bold mb-0">${usedMonths}</p>
                        </div>
                        <div class="col-6">
                            <p class="text-muted mb-1">车辆评分</p>
                            <p class="fw-bold mb-0">${vehicle.rating || '-'} / 5.0</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-6 mb-3">
            <div class="card h-100">
                <div class="card-header bg-light">
                    <h5 class="mb-0">运行状态</h5>
                </div>
                <div class="card-body">
                    <div class="mb-4">
                        <p class="text-muted mb-1">当前电量</p>
                        <div class="progress" style="height: 25px;position: relative">
                            <div class="progress-bar ${batteryClass}" role="progressbar" style="width: ${vehicle.battery_level}%;" aria-valuenow="${vehicle.battery_level}" aria-valuemin="0" aria-valuemax="100">
                            </div>
                            <span style="color: #000; position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center;">${vehicle.battery_level}%</span>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-6">
                            <p class="text-muted mb-1">累计里程</p>
                            <p class="fw-bold mb-0">${vehicle.mileage_formatted || `${vehicle.mileage} km` || '-'}</p>
                        </div>
                        <div class="col-6">
                            <p class="text-muted mb-1">总订单数</p>
                            <p class="fw-bold mb-0">${vehicle.total_orders || '0'}</p>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-6">
                            <p class="text-muted mb-1">当前位置名称</p>
                            <p class="fw-bold mb-0">${vehicle.current_location_name || '-'}</p>
                        </div>
                        <div class="col-6">
                            <p class="text-muted mb-1">当前任务</p>
                            <p class="fw-bold mb-0">${vehicle.current_status === '运行中' ? '执行订单中' : '无任务'}</p>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-6">
                            <p class="text-muted mb-1">X坐标</p>
                            <p class="fw-bold mb-0">${vehicle.current_location_x || '-'}</p>
                        </div>
                        <div class="col-6">
                            <p class="text-muted mb-1">Y坐标</p>
                            <p class="fw-bold mb-0">${vehicle.current_location_y || '-'}</p>
                        </div>
                    </div>
                    
                    <div class="actions mt-4">
                        <div class="d-flex justify-content-between">
                            <div>
                                ${vehicle.current_status === '电量不足' ? `
                                    <button class="btn btn-warning" onclick="rescueVehicle(${vehicle.vehicle_id})">
                                        <i class="bi bi-lightning-charge"></i> 救援车辆
                                    </button>
                                ` : ''}
                            </div>
                            <div>
                                <a href="/orders/advanced_search?vehicle_id=${vehicle.vehicle_id}" class="btn btn-primary">
                                    <i class="bi bi-list-ul"></i> 查看历史订单
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 第二行：维护信息和财务信息 -->
        <div class="col-md-6 mb-3">
            <div class="card h-100">
                <div class="card-header bg-light">
                    <h5 class="mb-0">维护信息</h5>
                </div>
                <div class="card-body">
                    <div class="row mb-3">
                        <div class="col-6">
                            <p class="text-muted mb-1">上次维护日期</p>
                            <p class="fw-bold mb-0">${formatDate(vehicle.last_maintenance_date)}</p>
                        </div>
                        <div class="col-6">
                            <p class="text-muted mb-1">下次维护日期</p>
                            <p class="fw-bold mb-0">${formatDate(vehicle.next_maintenance_date)}</p>
                        </div>
                    </div>
                    
                    <div class="actions mt-4">
                        <div class="d-flex justify-content-center">
                            ${vehicle.current_status === '维护中' 
                            ? `<button class="btn btn-success" onclick="endMaintenanceHandler('${vehicle.vehicle_id}')">
                                <i class="bi bi-check-circle"></i> 结束维护
                              </button>` 
                            : `<button class="btn btn-secondary" onclick="startMaintenanceHandler('${vehicle.vehicle_id}')">
                                <i class="bi bi-wrench"></i> 开始维护
                              </button>`}
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
                    <div class="row mb-3">
                        <div class="col-6">
                            <p class="text-muted mb-1">创建时间</p>
                            <p class="fw-bold mb-0">${formatDate(vehicle.created_at)}</p>
                        </div>
                        <div class="col-6">
                            <p class="text-muted mb-1">最后更新时间</p>
                            <p class="fw-bold mb-0">${formatDate(vehicle.updated_at)}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

    `;
}

// 显示错误消息
function showError(message) {
    const tableBody = document.getElementById('vehicles-table-body');
    if (tableBody) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center text-danger">
                    <i class="bi bi-exclamation-triangle-fill"></i> ${message}
                </td>
            </tr>
        `;
    }
    showLocalToast(message, 'danger');
}

// 设置标签页切换事件
function setupTabEvents() {
    // 获取所有标签页链接
    const tabLinks = document.querySelectorAll('.nav-link[data-bs-toggle="tab"]');
    
    // 如果没有找到任何标签页链接，直接返回
    if (!tabLinks || tabLinks.length === 0) {
        console.log('未找到标签页链接，跳过setupTabEvents');
        return;
    }
    
    // 为每个标签页添加事件监听
    tabLinks.forEach(link => {
        link.addEventListener('shown.bs.tab', function(e) {
            // 获取当前激活的标签页ID
            const activeTabId = e.target.getAttribute('href');
            
            // 控制页码跳转的显示/隐藏
            const pageJumpContainers = document.querySelectorAll('.input-group[class*="-page-jump"]');
            
            // 默认隐藏所有页码跳转控件
            if (pageJumpContainers && pageJumpContainers.length > 0) {
                pageJumpContainers.forEach(container => {
                    container.style.display = 'none';
                });
            }
            
            // 根据活动标签页显示对应页码跳转控件
            try {
                if (activeTabId === '#all') {
                    const pagination = document.querySelector('.pagination');
                    if (pagination && pagination.nextElementSibling) {
                        pagination.nextElementSibling.style.display = 'flex';
                    }
                } else if (activeTabId === '#online') {
                    const onlineJump = document.querySelector('.online-page-jump');
                    if (onlineJump) {
                        onlineJump.style.display = 'flex';
                    }
                } else if (activeTabId === '#busy') {
                    const busyJump = document.querySelector('.busy-page-jump');
                    if (busyJump) {
                        busyJump.style.display = 'flex';
                    }
                } else if (activeTabId === '#charging') {
                    const chargingJump = document.querySelector('.charging-page-jump');
                    if (chargingJump) {
                        chargingJump.style.display = 'flex';
                    }
                } else if (activeTabId === '#maintenance') {
                    const maintenanceJump = document.querySelector('.maintenance-page-jump');
                    if (maintenanceJump) {
                        maintenanceJump.style.display = 'flex';
                    }
                }
            } catch (error) {
                console.log('标签页切换处理错误:', error);
            }
        });
    });
    
    // 初始状态 - 只显示"全部车辆"的页码跳转
    const pageJumpContainers = document.querySelectorAll('.input-group[class*="-page-jump"]');
    if (pageJumpContainers && pageJumpContainers.length > 0) {
        pageJumpContainers.forEach(container => {
            container.style.display = 'none';
        });
    }
    
    const allTab = document.querySelector('.nav-link[href="#all"]');
    if (allTab && allTab.classList && allTab.classList.contains('active')) {
        const pagination = document.querySelector('.pagination');
        if (pagination && pagination.nextElementSibling) {
            pagination.nextElementSibling.style.display = 'flex';
        }
    }
}

// 加载车辆数据
function loadVehiclesData() {
    console.log('开始加载车辆数据...');
    
    // 显示加载状态
    const tableBody = document.getElementById('vehicles-table-body');
    if (!tableBody) {
        console.error('找不到vehicles-table-body元素，无法加载车辆数据');
        showLocalToast('页面元素缺失，请刷新页面后重试', 'danger');
        return;
    }
    
    tableBody.innerHTML = `
        <tr>
            <td colspan="9" class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2">正在加载车辆数据...</p>
            </td>
        </tr>
    `;
    
    fetch('/vehicles/api/all_vehicles')
        .then(response => {
            console.log('收到响应:', response.status, response.statusText);
            if (!response.ok) {
                throw new Error(`HTTP错误，状态码: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('接收到数据:', data);
            
            try {
                if (data.status === 'success') {
                    if (Array.isArray(data.data)) {
                        console.log(`成功获取到 ${data.data.length} 条车辆数据`);
                        // 调试：检查数据格式
                        if (data.data.length > 0) {
                            console.log('示例车辆数据格式:', JSON.stringify(data.data[0]));
                            console.log('所有车辆的位置信息:');
                            data.data.forEach(vehicle => {
                                console.log(`车辆ID: ${vehicle.vehicle_id}, 位置: ${vehicle.current_location_name || '未知'}`);
                            });
                        }
                        
                        // 全局存储车辆数据
                        window.currentVehiclesData = data.data;
                        
                        // 渲染表格和状态统计
                        try {
                            renderVehiclesTable(data.data);
                            // 按状态分组车辆并填充其他标签页
                            fillStatusTabs(data.data);
                            // 确保正确设置分页控件显示/隐藏状态
                            setupTabEvents();
                            // 动态填充城市筛选选项
                            populateCityOptions(data.data);
                        } catch (renderError) {
                            console.error('渲染车辆数据时出错:', renderError);
                            showLocalToast('渲染车辆数据时出错: ' + renderError.message, 'danger');
                            showError('渲染车辆数据时出错: ' + renderError.message);
                        }
                    } else {
                        console.error('数据格式不正确，期望是数组:', data.data);
                        showLocalToast('数据格式不正确', 'danger');
                        showError('数据格式不正确，无法显示车辆列表');
                    }
                } else {
                    showLocalToast('获取车辆数据失败: ' + data.message, 'danger');
                    console.error('API返回错误:', data.message);
                    showError('获取车辆数据失败: ' + data.message);
                }
            } catch (processError) {
                console.error('处理车辆数据时出错:', processError);
                showLocalToast('处理车辆数据时出错: ' + processError.message, 'danger');
                showError('处理车辆数据时出错: ' + processError.message);
            }
        })
        .catch(error => {
            showLocalToast('获取车辆数据时发生错误: ' + error.message, 'danger');
            console.error('加载车辆数据错误:', error);
            showError('获取车辆数据时发生错误: ' + error.message);
        });
}

// 从车辆数据中提取所有不同的城市并填充下拉框
function populateCityOptions(vehicles) {
    const cityFilter = document.getElementById('cityFilter');
    if (!cityFilter) {
        console.error('找不到cityFilter元素');
        return;
    }
    
    // 记住当前选中的值
    const currentValue = cityFilter.value;
    
    // 使用固定的城市列表
    const cityList = [
        '沈阳市','上海市', '北京市', '广州市', '深圳市', '杭州市', 
        '南京市', '成都市', '重庆市', '武汉市', '西安市' 
    ];
    
    // 清空现有选项（保留第一个"全部城市"）
    while (cityFilter.options.length > 1) {
        cityFilter.remove(1);
    }
    
    // 添加城市选项
    cityList.forEach(city => {
        const option = document.createElement('option');
        option.value = city;
        option.textContent = city;
        cityFilter.appendChild(option);
    });
    
    // 恢复之前选中的值
    if (currentValue && Array.from(cityFilter.options).some(opt => opt.value === currentValue)) {
        cityFilter.value = currentValue;
    }
    
    console.log(`已填充 ${cityList.length} 个城市选项`);
}

// 渲染车辆表格
function renderVehiclesTable(vehicles) {
    console.log('渲染车辆表格，数据:', vehicles.length + ' 条');
    
    const tableBody = document.getElementById('vehicles-table-body');
    const countInfo = document.getElementById('vehicle-count-info');
    
    if (!tableBody) {
        console.error('找不到vehicles-table-body元素');
        return;
    }
    
    // 清空表格
    tableBody.innerHTML = '';
    
    // 更新计数信息
    if (countInfo) {
        countInfo.textContent = `显示 1 到 ${Math.min(vehicles.length, 10)} 条，共 ${vehicles.length} 条`;
    } else {
        console.warn('找不到vehicle-count-info元素，跳过更新计数信息');
    }
    
    // 计算状态数量
    const statusCounts = {
        '空闲中': 0,
        '运行中': 0,
        '充电中': 0,
        '电量不足': 0,
        '等待充电': 0,
        '维护中': 0
    };
    
    // 更新状态数量统计
    vehicles.forEach(vehicle => {
        if (statusCounts[vehicle.current_status] !== undefined) {
            statusCounts[vehicle.current_status]++;
        }
    });
    
    // 更新状态标签显示的数量，同时保留信息图标
    const allTab = document.querySelector('.nav-link[href="#all"]');
    const onlineTab = document.querySelector('.nav-link[href="#online"]');
    const busyTab = document.querySelector('.nav-link[href="#busy"]');
    const chargingTab = document.querySelector('.nav-link[href="#charging"]');
    const maintenanceTab = document.querySelector('.nav-link[href="#maintenance"]');
    
    // 检查是否存在相应的标签元素，然后再更新内容
    if (allTab) {
        allTab.textContent = `全部车辆 (${vehicles.length})`;
    }
    
    // 更新其他标签，保留信息图标，只显示一个表示总数的括号
    if (onlineTab) {
        onlineTab.innerHTML = `空闲中 (${statusCounts['空闲中']}) <i class="bi bi-info-circle-fill text-info" data-bs-toggle="tooltip" title="显示所有空闲中的车辆数据"></i>`;
    }
    
    if (busyTab) {
        busyTab.innerHTML = `运行中 (${statusCounts['运行中']}) <i class="bi bi-info-circle-fill text-info" data-bs-toggle="tooltip" title="显示所有运行中的车辆数据"></i>`;
    }
    
    if (chargingTab) {
        chargingTab.innerHTML = `充电中 (${statusCounts['充电中']}) <i class="bi bi-info-circle-fill text-info" data-bs-toggle="tooltip" title="显示所有充电中的车辆数据"></i>`;
    }
    
    // 电量不足标签显示电量不足+维护中的总数
    const maintenanceCount = statusCounts['电量不足'] + statusCounts['维护中'];
    if (maintenanceTab) {
        maintenanceTab.innerHTML = `电量不足 (${maintenanceCount}) <i class="bi bi-info-circle-fill text-info" data-bs-toggle="tooltip" title="显示所有电量不足或维护中的车辆数据"></i>`;
    }
    
    // 初始化tooltip
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });
    
    // 每页显示10条记录
    const itemsPerPage = 10;
    const totalPages = Math.ceil(vehicles.length / itemsPerPage);
    
    // 当前页（默认第一页）
    let currentPage = 1;
    // 保存当前页码到全局变量
    window.currentPage = currentPage;
    
    // 生成分页
    updatePagination(currentPage, totalPages);
    
    // 显示当前页数据
    showPageData(vehicles, currentPage, itemsPerPage);
    
    // 分页点击事件
    const pagination = document.getElementById('vehicle-pagination');
    if (pagination) {
        pagination.addEventListener('click', function(e) {
            if (e.target.tagName === 'A' && e.target.getAttribute('data-page')) {
                e.preventDefault();
                const targetPage = parseInt(e.target.getAttribute('data-page'));
                if (targetPage !== currentPage && targetPage > 0 && targetPage <= totalPages) {
                    currentPage = targetPage;
                    // 更新全局当前页码
                    window.currentPage = currentPage;
                    updatePagination(currentPage, totalPages);
                    showPageData(vehicles, currentPage, itemsPerPage);
                }
            }
        });
    } else {
        console.warn('找不到vehicle-pagination元素，跳过绑定分页事件');
    }
    
    // 确保页码跳转器存在
    ensurePageJumper(totalPages, currentPage);
}

// 确保页码跳转器存在并正确初始化
function ensurePageJumper(totalPages, currentPage) {
    // 查找分页容器
    const paginationContainer = document.querySelector('.vehicles-table-container nav .d-flex.align-items-center');
    if (!paginationContainer) {
        console.warn('找不到分页容器，无法添加页码跳转器');
        return;
    }
    
    // 查找现有页码跳转器
    let pageJumper = paginationContainer.querySelector('.input-group');
    
    // 如果不存在，创建一个新的
    if (!pageJumper) {
        console.log('创建新的页码跳转器');
        pageJumper = document.createElement('div');
        pageJumper.className = 'input-group input-group-sm ms-2';
        pageJumper.style.width = '120px';
        
        pageJumper.innerHTML = `
            <input type="number" class="form-control" id="pageJumpInput" min="1" max="${totalPages}" placeholder="${currentPage}/${totalPages}">
            <button class="btn btn-outline-secondary" type="button" id="jumpButton">跳转</button>
        `;
        
        // 添加到分页容器
        paginationContainer.appendChild(pageJumper);
        
        // 绑定跳转按钮事件
        const jumpButton = document.getElementById('jumpButton');
        if (jumpButton) {
            jumpButton.addEventListener('click', jumpToPage);
        }
        
        // 绑定输入框回车事件
        const pageJumpInput = document.getElementById('pageJumpInput');
        if (pageJumpInput) {
            pageJumpInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    jumpToPage();
                }
            });
        }
    } else {
        // 更新现有页码跳转器的属性
        const pageJumpInput = pageJumper.querySelector('input');
        if (pageJumpInput) {
            pageJumpInput.setAttribute('min', '1');
            pageJumpInput.setAttribute('max', totalPages.toString());
            pageJumpInput.setAttribute('placeholder', `${currentPage}/${totalPages}`);
        }
    }
}

/**
 * 分页器更新函数 - 使用服务器端分页的版本
 * @param {number} currentPage - 当前页码
 * @param {number} totalPages - 总页数
 */
function updatePagination(currentPage, totalPages) {
    // 找到分页容器
    const pagination = document.getElementById('vehicle-pagination');
    if (!pagination) {
        console.warn('找不到vehicle-pagination元素，跳过分页更新');
        return;
    }
    
    // 清空现有的分页内容
    pagination.innerHTML = '';
    
    // 首页
    const firstLi = document.createElement('li');
    firstLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    const firstLink = document.createElement('a');
    firstLink.className = 'page-link';
    firstLink.href = 'javascript:void(0)';
    firstLink.setAttribute('data-page', '1');
    firstLink.innerHTML = '&laquo;&laquo;';
    firstLink.setAttribute('aria-label', '首页');
    firstLi.appendChild(firstLink);
    pagination.appendChild(firstLi);
    
    // 上一页
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    const prevLink = document.createElement('a');
    prevLink.className = 'page-link';
    prevLink.href = 'javascript:void(0)';
    prevLink.setAttribute('data-page', currentPage - 1);
    prevLink.innerHTML = '&laquo;';
    prevLink.setAttribute('aria-label', '上一页');
    prevLi.appendChild(prevLink);
    pagination.appendChild(prevLi);
    
    // 页码按钮
    const left_edge = 1;
    const right_edge = 1;
    const left_current = 1;
    const right_current = 1;
    
    if (totalPages <= 7) {
        // 如果总页数较少，显示所有页码
        for (let i = 1; i <= totalPages; i++) {
            addPageItem(i, currentPage);
        }
    } else {
        // 显示左边缘页码
        for (let i = 1; i <= left_edge; i++) {
            addPageItem(i, currentPage);
        }
        
        // 计算当前页附近要显示的页码范围
        let start = Math.max(left_edge + 1, currentPage - left_current);
        let end = Math.min(currentPage + right_current, totalPages - right_edge);
        
        // 调整范围确保显示足够的页码
        if (start <= left_edge + 1) {
            end = Math.min(left_edge + left_current + right_current + 1, totalPages - right_edge);
        }
        if (end >= totalPages - right_edge) {
            start = Math.max(totalPages - right_edge - right_current - left_current, left_edge + 1);
        }
        
        // 添加左省略号
        if (start > left_edge + 1) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.className = 'page-item disabled';
            const ellipsisLink = document.createElement('a');
            ellipsisLink.className = 'page-link';
            ellipsisLink.href = 'javascript:void(0)';
            ellipsisLink.textContent = '...';
            ellipsisLi.appendChild(ellipsisLink);
            pagination.appendChild(ellipsisLi);
        }
        
        // 添加当前页附近的页码
        for (let i = start; i <= end; i++) {
            addPageItem(i, currentPage);
        }
        
        // 添加右省略号
        if (end < totalPages - right_edge) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.className = 'page-item disabled';
            const ellipsisLink = document.createElement('a');
            ellipsisLink.className = 'page-link';
            ellipsisLink.href = 'javascript:void(0)';
            ellipsisLink.textContent = '...';
            ellipsisLi.appendChild(ellipsisLink);
            pagination.appendChild(ellipsisLi);
        }
        
        // 显示右边缘页码
        for (let i = totalPages - right_edge + 1; i <= totalPages; i++) {
            addPageItem(i, currentPage);
        }
    }
    
    // 下一页
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    const nextLink = document.createElement('a');
    nextLink.className = 'page-link';
    nextLink.href = 'javascript:void(0)';
    nextLink.setAttribute('data-page', currentPage + 1);
    nextLink.innerHTML = '&raquo;';
    nextLink.setAttribute('aria-label', '下一页');
    nextLi.appendChild(nextLink);
    pagination.appendChild(nextLi);
    
    // 末页
    const lastLi = document.createElement('li');
    lastLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    const lastLink = document.createElement('a');
    lastLink.className = 'page-link';
    lastLink.href = 'javascript:void(0)';
    lastLink.setAttribute('data-page', totalPages);
    lastLink.innerHTML = '&raquo;&raquo;';
    lastLink.setAttribute('aria-label', '末页');
    lastLi.appendChild(lastLink);
    pagination.appendChild(lastLi);
    
    // 添加页码辅助函数
    function addPageItem(pageNum, currentPage) {
        const pageLi = document.createElement('li');
        pageLi.className = `page-item ${pageNum === currentPage ? 'active' : ''}`;
        const pageLink = document.createElement('a');
        pageLink.className = 'page-link';
        pageLink.href = 'javascript:void(0)';
        pageLink.textContent = pageNum;
        pageLink.setAttribute('data-page', pageNum);
        pageLi.appendChild(pageLink);
        pagination.appendChild(pageLi);
    }
    
    // 更新跳转输入框
    const pageJumpInput = document.getElementById('pageJumpInput');
    if (pageJumpInput) {
        pageJumpInput.setAttribute('max', totalPages);
        pageJumpInput.placeholder = `${currentPage}/${totalPages}`;
    }
}

// 显示当前页数据
function showPageData(vehicles, page, itemsPerPage) {
    // 更新全局当前页码
    window.currentPage = page;
    
    const tableBody = document.getElementById('vehicles-table-body');
    if (!tableBody) {
        console.error('找不到vehicles-table-body元素');
        return;
    }
    
    tableBody.innerHTML = '';
    
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, vehicles.length);

    // 更新统计卡片数据
    updateVehicleStats(vehicles);
    
    // 更新计数信息
    const countInfo = document.getElementById('vehicle-count-info');
    if (countInfo) {
        countInfo.textContent = `显示 ${startIndex + 1} 到 ${endIndex} 条，共 ${vehicles.length} 条`;
    }
    
    for (let i = startIndex; i < endIndex; i++) {
        const vehicle = vehicles[i];
        
        // 创建表格行
        const row = document.createElement('tr');
        
        // 状态徽章样式
        const statusBadgeClass = getStatusBadgeClass(vehicle.current_status);
        
        // 电量进度条样式
        const batteryBarClass = getBatteryBarClass(vehicle.battery_level);
        
        // 设置行内容
        row.innerHTML = `
            <td>${vehicle.vehicle_id}</td>
            <td>${vehicle.plate_number || '-'}</td>
            <td>${vehicle.model || '-'}</td>
            <td><span class="badge ${statusBadgeClass}">${vehicle.current_status || '未知'}</span></td>
            <td>${vehicle.current_location_name || '未知位置'}</td>
            <td>
                <div class="progress" style="height: 15px;">
                    <div class="progress-bar ${batteryBarClass}" role="progressbar" 
                         style="width: ${vehicle.battery_level}%;" 
                         aria-valuenow="${vehicle.battery_level}" 
                         aria-valuemin="0" 
                         aria-valuemax="100">${vehicle.battery_level}%</div>
                </div>
            </td>
            <td>${vehicle.last_maintenance_date || '暂无记录'}</td>
            <td>${vehicle.mileage_formatted || (vehicle.mileage ? vehicle.mileage + ' km' : '0 km')}</td>
            <td>
                <div class="action-buttons">
                    <button class="btn btn-info btn-sm view-vehicle-btn" data-vehicle-id="${vehicle.vehicle_id}">
                        <i class="bi bi-info-circle"></i>
                    </button>
                    <button class="btn btn-warning btn-sm edit-vehicle-btn" data-vehicle-id="${vehicle.vehicle_id}">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-danger btn-sm delete-vehicle-btn" data-vehicle-id="${vehicle.vehicle_id}">
                        <i class="bi bi-trash"></i>
                    </button>
                    ${vehicle.current_status === '电量不足' ? `
                    <button class="btn btn-primary btn-sm rescue-vehicle-btn" data-vehicle-id="${vehicle.vehicle_id}">
                        <i class="bi bi-lightning-charge"></i>
                    </button>` : ''}
                </div>
            </td>
        `;
        
        tableBody.appendChild(row);
    }
    
    // 更新页码跳转器
    ensurePageJumper(Math.ceil(vehicles.length / itemsPerPage), page);
    
    // 重新绑定表格按钮事件
    initVehicleDetailButtons();
}

// 更新车辆状态统计卡片
function updateVehicleStats(vehicles) {
    // 计算各种状态的车辆数量
    const statusCounts = {
        '空闲中': 0,
        '运行中': 0,
        '充电中': 0,
        '电量不足': 0,
        '等待充电': 0,
        '维护中': 0
    };
    
    // 统计各状态数量
    vehicles.forEach(vehicle => {
        if (statusCounts[vehicle.current_status] !== undefined) {
            statusCounts[vehicle.current_status]++;
        }
    });
    
    // 更新统计卡片显示
    document.getElementById('totalVehicleCount').textContent = vehicles.length;
    document.getElementById('idleVehicleCount').textContent = statusCounts['空闲中'];
    document.getElementById('busyVehicleCount').textContent = statusCounts['运行中'];
    document.getElementById('chargingVehicleCount').textContent = statusCounts['充电中'];
    document.getElementById('lowBatteryVehicleCount').textContent = statusCounts['电量不足'];
    document.getElementById('maintenanceVehicleCount').textContent = statusCounts['维护中'];
}

// 页码跳转功能
function jumpToPage() {
    try {
        const input = document.getElementById('pageJumpInput');
        if (!input) {
            console.error('找不到pageJumpInput元素');
            showLocalToast('页码跳转元素不存在', 'danger');
            return;
        }
        
        const pageNum = parseInt(input.value);
        const maxPage = parseInt(input.getAttribute('max') || '1');
        
        console.log('跳转到页码:', pageNum, '最大页码:', maxPage);
        
        if (isNaN(pageNum)) {
            showLocalToast('请输入有效的页码', 'warning');
            return;
        }
        
        if (pageNum && pageNum >= 1 && pageNum <= maxPage) {
            // 获取全局存储的车辆数据
            if (window.currentVehiclesData && window.currentVehiclesData.length > 0) {
                console.log('使用前端分页跳转，数据长度:', window.currentVehiclesData.length);
                
                // 每页显示的记录数
                const itemsPerPage = 10;
                const totalPages = Math.ceil(window.currentVehiclesData.length / itemsPerPage);
                
                try {
                    // 1. 先更新分页控件，确保其可见
                    if (typeof updatePagination === 'function') {
                        updatePagination(pageNum, totalPages);
                    } else {
                        console.error('updatePagination 函数不存在');
                        showLocalToast('分页功能不完整', 'danger');
                        return;
                    }
                    
                    // 2. 显示当前页数据
                    if (typeof showPageData === 'function') {
                        showPageData(window.currentVehiclesData, pageNum, itemsPerPage);
                    } else {
                        console.error('showPageData 函数不存在');
                        showLocalToast('分页数据显示功能不完整', 'danger');
                        return;
                    }
                    
                    // 3. 确保页码跳转器存在
                    if (typeof ensurePageJumper === 'function') {
                        ensurePageJumper(totalPages, pageNum);
                    } else {
                        console.error('ensurePageJumper 函数不存在');
                    }
                    
                    // 4. 更新全局当前页码
                    window.currentPage = pageNum;
                } catch (error) {
                    console.error('分页跳转错误:', error);
                    showLocalToast('分页跳转出错: ' + error.message, 'danger');
                    return;
                }
                
                // 清空输入框
                input.value = '';
                
                // 滚动到表格顶部
                const tableElement = document.querySelector('.vehicles-table-container');
                if (tableElement) {
                    tableElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            } else {
                console.log('没有车辆数据或使用服务器端分页');
                // 如果没有加载车辆数据，使用传统跳转方式
                let url = new URL(window.location.href);
                url.searchParams.set('page', pageNum);
                window.location.href = url.toString();
            }
        } else {
            showLocalToast('请输入有效的页码 (1-' + maxPage + ')', 'warning');
        }
    } catch (error) {
        console.error('页码跳转发生未知错误:', error);
        showLocalToast('页码跳转失败: ' + (error.message || '未知错误'), 'danger');
    }
}

// 按状态分组车辆并填充其他标签页
function fillStatusTabs(vehicles) {
    console.log('开始填充状态标签页数据...');
    
    // 按状态分组车辆
    const idleVehicles = vehicles.filter(v => v.current_status === '空闲中');
    const busyVehicles = vehicles.filter(v => v.current_status === '运行中');
    const chargingVehicles = vehicles.filter(v => v.current_status === '充电中');
    const maintenanceVehicles = vehicles.filter(v => 
        v.current_status === '电量不足' || v.current_status === '维护中');
    
    console.log(`分组结果: 空闲中=${idleVehicles.length}, 运行中=${busyVehicles.length}, 充电中=${chargingVehicles.length}, 电量不足=${maintenanceVehicles.length}`);
    
    // 保存分组数据到全局变量，用于分页
    window.statusVehicles = {
        'online': idleVehicles,
        'busy': busyVehicles,
        'charging': chargingVehicles,
        'maintenance': maintenanceVehicles
    };
    
    // 初始化各标签页的当前页码
    window.statusCurrentPage = {
        'online': 1,
        'busy': 1,
        'charging': 1,
        'maintenance': 1
    };
    
    // 填充空闲中车辆表格
    fillStatusTable('online', idleVehicles, false);
    
    // 填充运行中车辆表格
    fillStatusTable('busy', busyVehicles, false);
    
    // 填充充电中车辆表格
    fillStatusTable('charging', chargingVehicles, false);
    
    // 填充电量不足车辆表格
    fillStatusTable('maintenance', maintenanceVehicles, true);
}

// 状态标签页的页码跳转功能
function jumpToStatusPage(statusType) {
    const input = document.getElementById(`${statusType}PageJumpInput`);
    const pageNum = parseInt(input.value);
    const maxPage = parseInt(input.getAttribute('max'));
    
    if (pageNum && pageNum >= 1 && pageNum <= maxPage) {
        // 更新全局存储的当前页码
        window.statusCurrentPage[statusType] = pageNum;
        
        // 重新加载表格数据
        fillStatusTable(statusType, window.statusVehicles[statusType], statusType === 'maintenance');
        
        // 清空输入框
        input.value = '';
        
        // 滚动到表格顶部（修复可能的空指针问题）
        const tableElement = document.querySelector(`#${statusType} table`);
        if (tableElement) {
            tableElement.scrollIntoView({ behavior: 'smooth' });
        }
    } else {
        showLocalToast('请输入有效的页码 (1-' + maxPage + ')', 'warning');
    }
}

// 全局变量存储筛选条件
window.filterOptions = {
    city: ""
};

// 筛选车辆数据
function filterVehicles() {
    const cityFilter = document.getElementById('cityFilter').value;
    
    // 保存筛选条件
    window.filterOptions.city = cityFilter;
    
    console.log(`开始筛选车辆，城市条件: ${cityFilter || '全部'}`);
    
    // 如果没有加载车辆数据，先提示用户
    if (!window.currentVehiclesData || window.currentVehiclesData.length === 0) {
        showLocalToast('请先加载车辆数据', 'warning');
        return;
    }
    
    // 获取原始车辆数据
    const originalVehicles = window.currentVehiclesData;
    
    // 应用筛选条件
    let filteredVehicles = originalVehicles;
    
    // 根据控制台输出，我们发现数据中current_city为空，但current_location_name包含区域名称
    if (cityFilter) {
        filteredVehicles = filteredVehicles.filter(vehicle => {
            // 匹配城市的通用函数
            const matchesCity = (locationName, cityName) => {
                if (!locationName) return false;
                
                // 根据城市名和对应的区名进行匹配
                const cityDistricts = {
                    '上海市': ['浦东新区', '徐汇区', '静安区', '黄浦区'],
                    '北京市': ['朝阳区', '海淀区', '东城区', '西城区'],
                    '广州市': ['天河区', '越秀区', '海珠区', '荔湾区'],
                    '深圳市': ['南山区', '福田区', '罗湖区', '宝安区'],
                    '杭州市': ['西湖区', '余杭区', '滨江区', '拱墅区'],
                    '南京市': ['鼓楼区', '玄武区', '江宁区', '秦淮区'],
                    '成都市': ['武侯区', '锦江区', '成华区', '青羊区'],
                    '重庆市': ['渝中区', '江北区', '南岸区', '渝北区'],
                    '武汉市': ['武昌区', '江汉区', '洪山区', '汉阳区'],
                    '西安市': ['新城区', '碑林区', '雁塔区', '莲湖区'],
                    '沈阳市': ['沈河区', '和平区', '铁西区', '皇姑区']
                };
                
                // 获取城市对应的区名列表
                const districts = cityDistricts[cityName] || [];
                
                // 检查位置名称是否包含任一区名
                return districts.some(district => locationName.includes(district));
            };
            
            // 检查位置名称是否匹配选中的城市
            return matchesCity(vehicle.current_location_name, cityFilter);
        });
    }
    
    // 渲染筛选后的表格
    renderVehiclesTable(filteredVehicles);
    
    // 按状态分组车辆并填充其他标签页
    fillStatusTabs(filteredVehicles);
    
    // 如果筛选后没有数据，显示提示
    if (filteredVehicles.length === 0) {
        showLocalToast(`未找到符合条件的车辆：${cityFilter || '全部城市'}`, 'info');
        document.getElementById('vehicles-table-body').innerHTML = `
            <tr>
                <td colspan="9" class="text-center text-muted">
                    <i class="bi bi-info-circle"></i> 未找到符合条件的车辆
                </td>
            </tr>
        `;
    } else {
        showLocalToast(`筛选成功，共找到 ${filteredVehicles.length} 辆车`, 'success');
    }
}

// 重置筛选条件
function resetFilters() {
    // 清空所有筛选输入
    document.querySelectorAll('#vehicleSearchForm input, #vehicleSearchForm select').forEach(element => {
        element.value = element.type === 'checkbox' ? false : '';
    });
    
    // 清空全局筛选条件
    window.filterOptions = {
        city: ""
    };
    
    // 刷新表格
    if (window.currentVehiclesData && window.currentVehiclesData.length > 0) {
        // 如果已经加载了车辆数据，则重新渲染
        renderVehiclesTable(window.currentVehiclesData);
        fillStatusTabs(window.currentVehiclesData);
    } else {
        // 否则通过页面刷新重置
        let baseUrl = window.location.href.split('?')[0];
        window.location.href = baseUrl;
    }
}

// 在页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    try {
        console.log('车辆管理页面初始化...');
        
        // 不自动加载车辆数据，避免覆盖服务器端分页
        // loadVehiclesData();
        
        // 加载充电站数据
        loadChargingStations();
        
        // 初始化模态框关闭处理
        initVehicleModalCloseHandler();
        
        // 初始化过滤事件
        const cityFilter = document.getElementById('cityFilter');
        if (cityFilter) {
            cityFilter.addEventListener('change', function() {
                updateStatusCounts();
            });
        } else {
            console.log('找不到cityFilter元素，可能是正常现象');
        }
        
        // 设置充电站城市筛选事件
        const chargingStationCityFilter = document.getElementById('chargingStationCityFilter');
        if (chargingStationCityFilter) {
            chargingStationCityFilter.addEventListener('change', function() {
                loadChargingStations(this.value);
            });
        }
        
        // 设置分页点击事件的全局处理函数，阻止页面刷新
        document.addEventListener('click', function(e) {
            // 查找点击的是否是分页链接
            const link = e.target.closest('.page-link');
            if (link && link.getAttribute('data-page')) {
                e.preventDefault(); // 阻止默认的页面跳转
                
                const targetPage = parseInt(link.getAttribute('data-page'));
                // 如果当前已加载车辆数据，使用JavaScript分页
                if (window.currentVehiclesData) {
                    const itemsPerPage = 10;
                    const totalPages = Math.ceil(window.currentVehiclesData.length / itemsPerPage);
                    
                    if (targetPage > 0 && targetPage <= totalPages) {
                        // 更新页码和分页显示
                        updatePagination(targetPage, totalPages);
                        // 显示当前页数据
                        showPageData(window.currentVehiclesData, targetPage, itemsPerPage);
                        
                        // 滚动到表格顶部
                        const tableElement = document.querySelector('.vehicles-table-container');
                        if (tableElement) {
                            tableElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }
                } else {
                    // 如果没有加载数据，则传统页面跳转
                    window.location.href = link.href;
                }
            }
        });
        
        // 设置页码跳转按钮事件
        const jumpButton = document.getElementById('jumpButton');
        if (jumpButton) {
            jumpButton.addEventListener('click', jumpToPage);
        }
        
        // 设置页码跳转输入框回车事件
        const pageJumpInput = document.getElementById('pageJumpInput');
        if (pageJumpInput) {
            pageJumpInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    jumpToPage();
                }
            });
        }
        
        // 初始化标签页事件 - 确保DOM元素存在
        if (document.querySelector('.nav-link[data-bs-toggle="tab"]')) {
            setupTabEvents();
        }
        
        // 初始化车辆详情按钮事件
        initVehicleDetailButtons();
        
    } catch (error) {
        console.error('初始化车辆管理页面时出错:', error);
        showLocalToast('初始化页面出错: ' + error.message, 'danger');
    }
});

// 加载充电站数据
function loadChargingStations(city = null, page = 1) {
    // 如果没有指定城市，尝试从会话存储中获取
    if (city === null) {
        city = sessionStorage.getItem('chargingStationCity') || 'all';
    } else {
        // 保存选择的城市到会话存储
        sessionStorage.setItem('chargingStationCity', city);
    }
    
    console.log('开始加载充电站数据，城市:', city, '页码:', page);
    const container = document.getElementById('chargingStationsContainer');
    const cityFilter = document.getElementById('chargingStationCityFilter');
    const paginationSection = document.getElementById('chargingStationPagination');
    
    if (!container) {
        console.error('找不到chargingStationsContainer元素');
        return;
    }
    
    // 显示加载状态
    container.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
            <p class="mt-2">正在加载充电站数据...</p>
        </div>
    `;
    
    // 隐藏分页部分
    if (paginationSection) {
        paginationSection.style.display = 'none';
    }
    
    // 从API获取数据
    return fetch(`/vehicles/api/charging_stations?city=${city}&page=${page}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP错误，状态码: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('接收到充电站数据:', data);
            
            // 确认数据格式是否正确
            if (data.status === 'success') {
                const stationsData = data.data;
                const paginationData = data.pagination || {
                    current_page: page,
                    per_page: 10,
                    total_count: 0,
                    total_pages: 1
                };
                
                // 处理数据为空的情况
                if (!stationsData || stationsData.length === 0) {
                    container.innerHTML = `
                        <div class="alert alert-info" role="alert">
                            <i class="bi bi-info-circle-fill"></i> 未找到充电站数据
                        </div>
                    `;
                    
                    // 隐藏分页
                    if (paginationSection) {
                        paginationSection.style.display = 'none';
                    }
                    
                    return;
                }
                
                // 填充城市筛选下拉框
                if (data.cities && Array.isArray(data.cities)) {
                    populateChargingStationCities(data.cities, city);
                }
                
                // 更新记录统计显示
                updateChargingStationStats(paginationData);
                
                // 渲染充电站数据
                renderChargingStations(stationsData, paginationData, city);
                
                // 更新分页跳转控件
                if (paginationSection) {
                    updateChargingStationPagination(paginationData, city);
                    paginationSection.style.display = 'flex';
                }
            } else {
                throw new Error('数据格式不正确');
            }
        })
        .catch(error => {
            console.error('加载充电站数据错误:', error);
            container.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="bi bi-exclamation-triangle-fill"></i> 加载充电站数据出错: ${error.message}
                </div>
            `;
            showLocalToast('加载充电站数据失败: ' + error.message, 'danger');
        });
}

// 更新充电站记录统计信息
function updateChargingStationStats(pagination) {
    const offsetSpan = document.getElementById('csOffset');
    const limitSpan = document.getElementById('csLimit');
    const totalCountSpan = document.getElementById('csTotalCount');
    
    if (!offsetSpan || !limitSpan || !totalCountSpan) {
        console.error('找不到充电站统计DOM元素', {offsetSpan, limitSpan, totalCountSpan});
        return;
    }
    
    if (!pagination) {
        // 如果没有分页信息，显示默认的0条记录
        offsetSpan.textContent = '0';
        limitSpan.textContent = '0';
        totalCountSpan.textContent = '0';
        return;
    }
    
    const totalCount = pagination.total_count || 0;
    
    if (totalCount === 0) {
        // 数据为空，显示0条记录
        offsetSpan.textContent = '0';
        limitSpan.textContent = '0';
        totalCountSpan.textContent = '0';
    } else {
        // 计算当前页的记录范围
        const offset = (pagination.current_page - 1) * pagination.per_page;
        const limit = Math.min(offset + pagination.per_page, totalCount);
        
        // 更新DOM显示
        offsetSpan.textContent = offset + 1;
        limitSpan.textContent = limit;
        totalCountSpan.textContent = totalCount;
    }
    
    console.log('已更新充电站统计信息:', {
        offset: offsetSpan.textContent,
        limit: limitSpan.textContent,
        total: totalCountSpan.textContent
    });
}

// 更新充电站分页控件
function updateChargingStationPagination(pagination, city) {
    const paginationList = document.getElementById('csPaginationList');
    const jumpInput = document.getElementById('csJumpToPage');
    
    if (!paginationList || !jumpInput) return;
    
    // 清空现有分页按钮
    paginationList.innerHTML = '';
    
    const currentPage = pagination.current_page;
    const totalPages = pagination.total_pages;
    
    // 设置跳转输入框的属性
    jumpInput.setAttribute('min', '1');
    jumpInput.setAttribute('max', totalPages);
    jumpInput.setAttribute('placeholder', `${currentPage}/${totalPages}`);
    
    // 添加上一页按钮
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage <= 1 ? 'disabled' : ''}`;
    const prevLink = document.createElement('a');
    prevLink.className = 'page-link';
    prevLink.href = '#';
    prevLink.textContent = '上一页';
    prevLink.setAttribute('data-page', currentPage - 1);
    prevLi.appendChild(prevLink);
    paginationList.appendChild(prevLi);
    
    // 添加页码按钮
    const left_edge = 1;
    const right_edge = 1;
    const left_current = 2;
    const right_current = 2;
    
    if (totalPages <= 7) {
        // 页数较少，显示所有页码
        for (let i = 1; i <= totalPages; i++) {
            addPageItem(i, currentPage);
        }
    } else {
        // 页数较多，智能显示页码
        // 显示左边缘页码
        for (let i = 1; i <= left_edge; i++) {
            addPageItem(i, currentPage);
        }
        
        // 计算当前页附近要显示的页码范围
        let start = Math.max(left_edge + 1, currentPage - left_current);
        let end = Math.min(currentPage + right_current, totalPages - right_edge);
        
        // 调整范围确保显示足够的页码
        if (start <= left_edge + 1) {
            end = Math.min(left_edge + left_current + right_current + 1, totalPages - right_edge);
        }
        if (end >= totalPages - right_edge) {
            start = Math.max(totalPages - right_edge - right_current - left_current, left_edge + 1);
        }
        
        // 添加左省略号
        if (start > left_edge + 1) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.className = 'page-item disabled';
            const ellipsisLink = document.createElement('a');
            ellipsisLink.className = 'page-link';
            ellipsisLink.href = '#';
            ellipsisLink.textContent = '...';
            ellipsisLi.appendChild(ellipsisLink);
            paginationList.appendChild(ellipsisLi);
        }
        
        // 添加当前页附近的页码
        for (let i = start; i <= end; i++) {
            addPageItem(i, currentPage);
        }
        
        // 添加右省略号
        if (end < totalPages - right_edge) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.className = 'page-item disabled';
            const ellipsisLink = document.createElement('a');
            ellipsisLink.className = 'page-link';
            ellipsisLink.href = '#';
            ellipsisLink.textContent = '...';
            ellipsisLi.appendChild(ellipsisLink);
            paginationList.appendChild(ellipsisLi);
        }
        
        // 显示右边缘页码
        for (let i = totalPages - right_edge + 1; i <= totalPages; i++) {
            addPageItem(i, currentPage);
        }
    }
    
    // 添加下一页按钮
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage >= totalPages ? 'disabled' : ''}`;
    const nextLink = document.createElement('a');
    nextLink.className = 'page-link';
    nextLink.href = '#';
    nextLink.textContent = '下一页';
    nextLink.setAttribute('data-page', currentPage + 1);
    nextLi.appendChild(nextLink);
    paginationList.appendChild(nextLi);
    
    // 为分页按钮添加点击事件
    paginationList.querySelectorAll('.page-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            if (this.parentElement.classList.contains('disabled')) return;
            const page = parseInt(this.getAttribute('data-page'));
            if (page) {
                loadChargingStations(city, page);
            }
        });
    });
    
    // 辅助函数：添加页码按钮
    function addPageItem(pageNum, currentPage) {
        const pageLi = document.createElement('li');
        pageLi.className = `page-item ${pageNum === currentPage ? 'active' : ''}`;
        const pageLink = document.createElement('a');
        pageLink.className = 'page-link';
        pageLink.href = '#';
        pageLink.textContent = pageNum;
        pageLink.setAttribute('data-page', pageNum);
        pageLi.appendChild(pageLink);
        paginationList.appendChild(pageLi);
    }
}

// 填充充电站城市下拉框
function populateChargingStationCities(cities, selectedCity) {
    const cityFilter = document.getElementById('chargingStationCityFilter');
    if (!cityFilter) return;
    
    // 如果没有指定选中的城市，尝试从会话存储中获取
    if (!selectedCity) {
        selectedCity = sessionStorage.getItem('chargingStationCity');
    }
    
    // 记住当前选中值
    const currentValue = selectedCity || cityFilter.value || 'all';
    
    // 清空除了"全部城市"之外的选项
    while (cityFilter.options.length > 1) {
        cityFilter.remove(1);
    }
    
    // 添加来自API的城市选项
    cities.forEach(city => {
        const option = document.createElement('option');
        option.value = city;
        option.textContent = city;
        cityFilter.appendChild(option);
    });
    
    // 设置选中的城市
    if (currentValue && Array.from(cityFilter.options).some(opt => opt.value === currentValue)) {
        cityFilter.value = currentValue;
    }
}

// 渲染充电站数据
function renderChargingStations(stations, pagination, currentCity) {
    const container = document.getElementById('chargingStationsContainer');
    
    // 如果没有数据，显示无数据消息
    if (!stations || stations.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info" role="alert">
                <i class="bi bi-info-circle-fill"></i> 未找到充电站数据
            </div>
        `;
        return;
    }
    
    // 构建表格HTML
    let html = `
        <div class="table-responsive">
            <table class="table table-striped table-hover align-middle">
                <thead class="table-light">
                    <tr>
                        <th class="text-center">ID</th>
                        <th class="text-center">编号</th>
                        <th class="text-center">所在城市</th>
                        <th class="text-center">位置信息</th>
                        <th class="text-center">容量情况</th>
                        <th class="text-center">创建时间</th>
                        <th class="text-center">操作</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // 填充充电站数据行
    stations.forEach(station => {
        // 使用率进度条样式
        let usageClass = 'bg-success';
        if (station.usage_percent >= 85) {
            usageClass = 'bg-danger';
        } else if (station.usage_percent >= 60) {
            usageClass = 'bg-warning';
        }
        
        html += `
            <tr>
                <td class="text-center">${station.station_id}</td>
                <td class="text-center">${station.station_code || '-'}</td>
                <td class="text-center">${station.city_code || '-'}</td>
                <td class="text-center">${station.location_name || '未知位置'}</td>
                <td class="text-center">
                    <div class="d-flex align-items-center justify-content-center">
                        <div class="progress flex-grow-1" style="height: 15px; max-width: 100px;">
                            <div class="progress-bar ${usageClass}" role="progressbar" 
                                style="width: ${station.usage_percent}%;" 
                                aria-valuenow="${station.usage_percent}" 
                                aria-valuemin="0" 
                                aria-valuemax="100">${station.usage_percent}%</div>
                        </div>
                        <span class="ms-2">${station.current_vehicles}/${station.max_capacity}</span>
                    </div>
                </td>
                <td class="text-center">${station.created_at || '无记录'}</td>
                <td class="text-center">
                    <div class="d-flex justify-content-center">
                        
                        <a href="/finance/expense?charging_station_id=${station.station_id}" class="btn btn-sm btn-primary view-station-history-btn">
                            <i class="bi bi-clock-history"></i> 费用记录
                        </a>
                    </div>
                </td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    // 设置HTML到容器
    container.innerHTML = html;
}

// 填充状态标签页的表格数据
function fillStatusTable(statusType, vehicles, isMaintenanceTab) {
    console.log(`开始填充${statusType}标签页数据，共${vehicles.length}条记录`);
    
    // 查找对应的表格元素
    const tableBody = document.querySelector(`#${statusType}-vehicles-table tbody`);
    const pagination = document.querySelector(`#${statusType}-pagination`);
    const countInfo = document.querySelector(`#${statusType}-count-info`);
    
    // 如果找不到DOM元素，记录错误并返回
    if (!tableBody || !pagination) {
        console.log(`找不到 ${statusType} 标签页所需DOM元素: tableBody=${tableBody}, pagination=${pagination}`);
        // 这是正常现象，因为当前页面可能不包含这些标签页
        return;
    }
    
    // 清空现有内容
    tableBody.innerHTML = '';
    
    // 如果没有数据，显示提示信息
    if (!vehicles || vehicles.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="8" class="text-center">暂无${getStatusDisplayName(statusType)}车辆数据</td></tr>`;
        pagination.innerHTML = '';
        return;
    }
    
    // 每页显示10条记录
    const itemsPerPage = 10;
    const totalPages = Math.ceil(vehicles.length / itemsPerPage);
    
    // 当前页
    let currentPage = window.statusCurrentPage[statusType] || 1;
    
    // 确保当前页在有效范围内
    if (currentPage > totalPages) {
        currentPage = totalPages;
        window.statusCurrentPage[statusType] = currentPage;
    }
    
    // 生成分页
    updateStatusPagination(statusType, currentPage, totalPages);
    
    // 显示当前页数据
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, vehicles.length);
    
    for (let i = startIndex; i < endIndex; i++) {
        const vehicle = vehicles[i];
        
        // 创建表格行
        const row = document.createElement('tr');
        
        // 状态徽章样式
        const statusBadgeClass = getStatusBadgeClass(vehicle.current_status);
        
        // 电量进度条样式
        const batteryBarClass = getBatteryBarClass(vehicle.battery_level);
        
        // 根据标签页不同设置不同的行内容
        if (isMaintenanceTab) {
            // 电量不足标签页包含状态列
            row.innerHTML = `
                <td>${vehicle.vehicle_id}</td>
                <td>${vehicle.plate_number}</td>
                <td>${vehicle.model}</td>
                <td><span class="badge ${statusBadgeClass}">${vehicle.current_status}</span></td>
                <td>${vehicle.current_location_name || '未知位置'}</td>
                <td>
                    <div class="progress" style="height: 15px;">
                        <div class="progress-bar ${batteryBarClass}" role="progressbar" 
                             style="width: ${vehicle.battery_level}%;" 
                             aria-valuenow="${vehicle.battery_level}" 
                             aria-valuemin="0" 
                             aria-valuemax="100">${vehicle.battery_level}%</div>
                    </div>
                </td>
                <td>${vehicle.last_maintenance_date || '暂无记录'}</td>
                <td>${vehicle.mileage_formatted}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-info btn-sm view-vehicle-btn" data-vehicle-id="${vehicle.vehicle_id}">
                            <i class="bi bi-info-circle"></i>
                        </button>
                        <button class="btn btn-warning btn-sm edit-vehicle-btn" data-vehicle-id="${vehicle.vehicle_id}">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-danger btn-sm delete-vehicle-btn" data-vehicle-id="${vehicle.vehicle_id}">
                            <i class="bi bi-trash"></i>
                        </button>
                        ${vehicle.current_status === '电量不足' ? `
                        <button class="btn btn-primary btn-sm rescue-vehicle-btn" data-vehicle-id="${vehicle.vehicle_id}">
                            <i class="bi bi-lightning-charge"></i>
                        </button>` : ''}
                    </div>
                </td>
            `;
        } else {
            // 其他标签页不显示状态列，因为状态都相同
            row.innerHTML = `
                <td>${vehicle.vehicle_id}</td>
                <td>${vehicle.plate_number}</td>
                <td>${vehicle.model}</td>
                <td>${vehicle.current_location_name || '未知位置'}</td>
                <td>
                    <div class="progress" style="height: 15px;">
                        <div class="progress-bar ${batteryBarClass}" role="progressbar" 
                             style="width: ${vehicle.battery_level}%;" 
                             aria-valuenow="${vehicle.battery_level}" 
                             aria-valuemin="0" 
                             aria-valuemax="100">${vehicle.battery_level}%</div>
                    </div>
                </td>
                <td>${vehicle.last_maintenance_date || '暂无记录'}</td>
                <td>${vehicle.mileage_formatted}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-info btn-sm view-vehicle-btn" data-vehicle-id="${vehicle.vehicle_id}">
                            <i class="bi bi-info-circle"></i>
                        </button>
                        <button class="btn btn-warning btn-sm edit-vehicle-btn" data-vehicle-id="${vehicle.vehicle_id}">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-danger btn-sm delete-vehicle-btn" data-vehicle-id="${vehicle.vehicle_id}">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            `;
        }
        
        tableBody.appendChild(row);
    }
    
    // 更新计数信息
    if (countInfo) {
        const startCount = vehicles.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0;
        const endCount = Math.min(startIndex + itemsPerPage, vehicles.length);
        countInfo.textContent = `显示 ${startCount} 到 ${endCount} 条，共 ${vehicles.length} 条`;
    }
    
    // 重新绑定按钮事件
    initVehicleDetailButtons();
}

// 更新状态标签页的分页控件
function updateStatusPagination(statusType, currentPage, totalPages) {
    const pagination = document.getElementById(`${statusType}-pagination`);
    pagination.innerHTML = '';
    
    // 上一页
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    const prevLink = document.createElement('a');
    prevLink.className = 'page-link';
    prevLink.href = '#';
    prevLink.textContent = '上一页';
    prevLink.setAttribute('data-page', currentPage - 1);
    prevLi.appendChild(prevLink);
    pagination.appendChild(prevLi);
    
    // 页码
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 1 && i <= currentPage + 1)) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${i === currentPage ? 'active' : ''}`;
            const pageLink = document.createElement('a');
            pageLink.className = 'page-link';
            pageLink.href = '#';
            pageLink.textContent = i;
            pageLink.setAttribute('data-page', i);
            pageLi.appendChild(pageLink);
            pagination.appendChild(pageLi);
        } else if ((i === currentPage - 2 && i > 1) || (i === currentPage + 2 && i < totalPages)) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.className = 'page-item disabled';
            const ellipsisSpan = document.createElement('a');
            ellipsisSpan.className = 'page-link';
            ellipsisSpan.textContent = '...';
            ellipsisLi.appendChild(ellipsisSpan);
            pagination.appendChild(ellipsisLi);
        }
    }
    
    // 下一页
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    const nextLink = document.createElement('a');
    nextLink.className = 'page-link';
    nextLink.href = '#';
    nextLink.textContent = '下一页';
    nextLink.setAttribute('data-page', currentPage + 1);
    nextLi.appendChild(nextLink);
    pagination.appendChild(nextLi);
    
    // 更新页码跳转输入框
    const pageJumpInput = document.getElementById(`${statusType}PageJumpInput`);
    if (pageJumpInput) {
        pageJumpInput.max = totalPages;
        pageJumpInput.placeholder = `${currentPage}/${totalPages}`;
        
        // 添加回车键跳转
        pageJumpInput.onkeypress = function(e) {
            if (e.key === 'Enter') {
                jumpToStatusPage(statusType);
            }
        };
    }
    
    // 为分页添加点击事件
    pagination.addEventListener('click', function(e) {
        if (e.target.tagName === 'A' && e.target.getAttribute('data-page')) {
            e.preventDefault();
            const targetPage = parseInt(e.target.getAttribute('data-page'));
            if (targetPage !== currentPage && targetPage > 0 && targetPage <= totalPages) {
                // 更新全局状态页码
                window.statusCurrentPage[statusType] = targetPage;
                // 重新填充表格
                fillStatusTable(statusType, window.statusVehicles[statusType], statusType === 'maintenance');
            }
        }
    });
}

// 初始化车辆详情按钮事件
function initVehicleDetailButtons() {
    // 为所有查看详情按钮添加点击事件
    document.querySelectorAll('.view-vehicle-btn').forEach(button => {
        // 清除旧事件
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        
        newButton.addEventListener('click', function() {
            const vehicleId = this.getAttribute('data-vehicle-id');
            if (vehicleId) {
                vehicleDetailsViewer(vehicleId);
            }
        });
    });
    
    // 为所有编辑按钮添加点击事件
    document.querySelectorAll('.edit-vehicle-btn').forEach(button => {
        // 清除旧事件
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        
        newButton.addEventListener('click', function() {
            const vehicleId = this.getAttribute('data-vehicle-id');
            if (vehicleId) {
                editVehicle(vehicleId);
            }
        });
    });
    
    // 为所有删除按钮添加点击事件
    document.querySelectorAll('.delete-vehicle-btn').forEach(button => {
        // 清除旧事件
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        
        newButton.addEventListener('click', function() {
            const vehicleId = this.getAttribute('data-vehicle-id');
            if (vehicleId) {
                confirmDeleteVehicle(vehicleId);
            }
        });
    });
    
    // 为救援按钮添加点击事件
    document.querySelectorAll('.rescue-vehicle-btn').forEach(button => {
        // 清除旧事件
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        
        newButton.addEventListener('click', function() {
            const vehicleId = this.getAttribute('data-vehicle-id');
            if (vehicleId) {
                window.rescueVehicle(vehicleId);
            }
        });
    });
    
    console.log('车辆操作按钮事件初始化完成');
}

// 绑定表格相关事件
window.bindTableEvents = function() {
    console.log('重新绑定表格事件...');
    
    // 绑定查看详情按钮事件
    const viewButtons = document.querySelectorAll('.view-vehicle-btn');
    viewButtons.forEach(btn => {
        btn.removeEventListener('click', viewButtonHandler);
        btn.addEventListener('click', viewButtonHandler);
    });
    
    // 绑定删除按钮事件
    const deleteButtons = document.querySelectorAll('.delete-vehicle-btn');
    deleteButtons.forEach(btn => {
        btn.removeEventListener('click', deleteButtonHandler);
        btn.addEventListener('click', deleteButtonHandler);
    });
    
    // 绑定救援按钮事件 - 先移除所有已有的事件监听器
    const rescueButtons = document.querySelectorAll('.rescue-vehicle-btn');
    rescueButtons.forEach(btn => {
        // 清除所有可能的点击事件处理程序
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        
        // 添加新的事件处理程序
        newBtn.addEventListener('click', function() {
            const vehicleId = this.getAttribute('data-vehicle-id');
            if (vehicleId) {
                window.rescueVehicle(vehicleId);
            }
        });
    });
    
    // 绑定编辑按钮事件
    const editButtons = document.querySelectorAll('.edit-vehicle-btn');
    editButtons.forEach(btn => {
        btn.removeEventListener('click', editButtonHandler);
        btn.addEventListener('click', editButtonHandler);
    });
    
    // 绑定开始维护按钮事件
    const startMaintenanceButtons = document.querySelectorAll('.start-maintenance-btn');
    startMaintenanceButtons.forEach(btn => {
        btn.removeEventListener('click', startMaintenanceHandler);
        btn.addEventListener('click', startMaintenanceHandler);
    });
    
    // 绑定结束维护按钮事件
    const endMaintenanceButtons = document.querySelectorAll('.end-maintenance-btn');
    endMaintenanceButtons.forEach(btn => {
        btn.removeEventListener('click', endMaintenanceHandler);
        btn.addEventListener('click', endMaintenanceHandler);
    });
}

// 定义按钮事件处理程序
function viewButtonHandler() {
    const vehicleId = this.getAttribute('data-vehicle-id');
    showVehicleDetails(vehicleId);
}

function deleteButtonHandler() {
    const vehicleId = this.getAttribute('data-vehicle-id');
    if (typeof window.confirmDeleteVehicle === 'function') {
        window.confirmDeleteVehicle(vehicleId);
    } else {
        const deleteForm = document.getElementById('deleteForm');
        if (deleteForm) {
            deleteForm.action = `/vehicles/delete/${vehicleId}`;
            const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
            deleteModal.show();
        }
    }
}

function editButtonHandler() {
    const vehicleId = this.getAttribute('data-vehicle-id');
    window.location.href = `/vehicles/edit/${vehicleId}`;
}

// 显示车辆详情函数
function showVehicleDetails(vehicleId) {
    console.log('显示车辆详情:', vehicleId);
    if (typeof window.vehicleDetailsViewer === 'function') {
        window.vehicleDetailsViewer(vehicleId);
    } else {
        // 兼容旧代码
        const modal = document.getElementById('vehicleDetailsModal');
        const modalContent = document.getElementById('vehicleDetailsContent');
        
        if (!modal || !modalContent) {
            console.error('找不到车辆详情模态框元素');
            return;
        }
        
        // 显示加载中
        modalContent.innerHTML = `
            <div class="col-12 text-center">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
            </div>
        `;
        
        // 显示模态框
        const vehicleDetailsModal = new bootstrap.Modal(modal);
        vehicleDetailsModal.show();
        
        // 获取车辆详情
        fetch(`/vehicles/api/vehicle_details/${vehicleId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // 构建详情HTML
                    if (typeof createVehicleDetailsHtml === 'function') {
                        modalContent.innerHTML = createVehicleDetailsHtml(data.data);
                    } else {
                        // 简单展示
                        const vehicle = data.data;
                        modalContent.innerHTML = `
                            <div class="col-md-6">
                                <h5>基本信息</h5>
                                <p><strong>车辆ID:</strong> ${vehicle.vehicle_id}</p>
                                <p><strong>车牌号:</strong> ${vehicle.plate_number}</p>
                                <p><strong>型号:</strong> ${vehicle.model}</p>
                                <p><strong>状态:</strong> ${vehicle.current_status}</p>
                            </div>
                            <div class="col-md-6">
                                <h5>运行信息</h5>
                                <p><strong>当前位置:</strong> ${vehicle.current_location_name || '未知'}</p>
                                <p><strong>电量:</strong> ${vehicle.battery_level}%</p>
                                <p><strong>累计里程:</strong> ${vehicle.mileage} 公里</p>
                            </div>
                        `;
                    }
                } else {
                    modalContent.innerHTML = `
                        <div class="col-12">
                            <div class="alert alert-danger">
                                加载车辆详情失败: ${data.message}
                            </div>
                        </div>
                    `;
                }
            })
            .catch(error => {
                modalContent.innerHTML = `
                    <div class="col-12">
                        <div class="alert alert-danger">
                            加载车辆详情发生错误: ${error}
                        </div>
                    </div>
                `;
            });
    }
}

// 开始车辆维护 - 确保全局可用
window.startVehicleMaintenance = function(vehicleId) {
    console.log('调用startVehicleMaintenance:', vehicleId);
    
    if (!confirm('确定要将车辆设置为维护状态吗？')) {
        return;
    }
    
    fetch(`/api/start_maintenance/${vehicleId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(data.message, 'success');
            // 刷新表格数据
            reloadTableData();
        } else if (data.status === 'info') {
            showToast(data.message, 'info');
        } else {
            showToast(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('开始维护操作失败:', error);
        showToast('操作失败，请稍后重试', 'danger');
    });
};

// 结束车辆维护 - 确保全局可用
window.endVehicleMaintenance = function(vehicleId) {
    console.log('调用endVehicleMaintenance:', vehicleId);
    
    if (!confirm('确定要结束车辆维护吗？车辆电量将恢复到100%。')) {
        return;
    }
    
    fetch(`/api/end_maintenance/${vehicleId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(data.message, 'success');
            // 刷新表格数据
            reloadTableData();
        } else {
            showToast(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('结束维护操作失败:', error);
        showToast('操作失败，请稍后重试', 'danger');
    });
};

// 定义维护按钮事件处理程序
function startMaintenanceHandler() {
    const vehicleId = this.getAttribute('data-vehicle-id');
    console.log('点击了开始维护按钮，车辆ID:', vehicleId);
    window.startVehicleMaintenance(vehicleId);
}

function endMaintenanceHandler() {
    const vehicleId = this.getAttribute('data-vehicle-id');
    console.log('点击了结束维护按钮，车辆ID:', vehicleId);
    window.endVehicleMaintenance(vehicleId);
}

// 刷新表格数据
function reloadTableData() {
    // 从当前URL中获取参数
    const url = new URL(window.location.href);
    // 添加ajax参数，表示这是AJAX请求
    url.searchParams.set('ajax', '1');
    
    // 发送AJAX请求获取表格数据
    fetch(url.toString(), {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.text())
    .then(html => {
        // 更新表格容器内容
        const tableContainer = document.querySelector('.vehicles-table-container');
        if (tableContainer) {
            tableContainer.innerHTML = html;
            
            // 重新绑定表格事件
            if (typeof window.bindTableEvents === 'function') {
                window.bindTableEvents();
            }
            
            // 高亮表格容器
            tableContainer.classList.add('highlight-update');
            setTimeout(() => {
                tableContainer.classList.remove('highlight-update');
            }, 1000);
        }
    })
    .catch(error => {
        console.error('刷新表格数据失败:', error);
        showToast('刷新表格数据失败，请稍后重试', 'danger');
    });
}

// ... existing code ... 