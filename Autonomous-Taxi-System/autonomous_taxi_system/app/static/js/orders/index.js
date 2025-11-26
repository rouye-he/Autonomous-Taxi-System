/**
 * 无人驾驶出租车管理平台 - 订单管理页面脚本
 */

// 电池电量颜色类
function getBatteryColorClass(level) {
    if (level >= 70) {
        return 'bg-success';
    } else if (level >= 30) {
        return 'bg-warning';
    } else {
        return 'bg-danger';
    }
}

// 当前正在轮询的车辆ID
let currentPollingVehicleId = null;
let pollingInterval = null;
let currentOrderId = null;
let currentOrderCity = null;

// 查看订单详情
function viewOrderDetails(orderId) {
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('orderDetailModal'));
    modal.show();
    
    // 获取订单详情数据
    fetch(`/orders/api/order_details/${orderId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const order = data.data;
                
                // 构建详情HTML
                let detailsHtml = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>基本信息</h6>
                        <table class="table table-sm">
                            <tr>
                                <th>订单编号</th>
                                <td>${order.order_number}</td>
                            </tr>
                            <tr>
                                <th>下单时间</th>
                                <td>${order.create_time || '未知'}</td>
                            </tr>
                            <tr>
                                <th>订单状态</th>
                                <td>${order.order_status}</td>
                            </tr>
                            <tr>
                                <th>城市</th>
                                <td>${order.city_code || '未知'}</td>
                            </tr>
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h6>行程信息</h6>
                        <table class="table table-sm">
                            <tr>
                                <th>上车地点</th>
                                <td>${order.pickup_location}</td>
                            </tr>
                            <tr>
                                <th>下车地点</th>
                                <td>${order.dropoff_location}</td>
                            </tr>
                            <tr>
                                <th>到达时间</th>
                                <td>${order.arrival_time || '未完成'}</td>
                            </tr>
                        </table>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <h6>用户信息</h6>
                        <table class="table table-sm">
                            <tr>
                                <th>用户ID</th>
                                <td>${order.user_id}</td>
                            </tr>
                            <tr>
                                <th>用户名</th>
                                <td>${order.username || '未知'}</td>
                            </tr>
                            <tr>
                                <th>姓名</th>
                                <td>${order.real_name || '未知'}</td>
                            </tr>
                            <tr>
                                <th>手机号</th>
                                <td>${order.phone || '未知'}</td>
                            </tr>
                            <tr>
                                <th>邮箱</th>
                                <td>${order.email || '未知'}</td>
                            </tr>
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h6>车辆信息</h6>
                        <table class="table table-sm">
                            <tr>
                                <th>车辆ID</th>
                                <td>${order.vehicle_id || '未分配'}</td>
                            </tr>
                            <tr>
                                <th>车牌号</th>
                                <td>${order.plate_number || '未分配'}</td>
                            </tr>
                            <tr>
                                <th>车型</th>
                                <td>${order.model || '未分配'}</td>
                            </tr>
                            <tr>
                                <th>当前位置</th>
                                <td>${order.current_location_name || '未知'}</td>
                            </tr>
                        </table>
                    </div>
                </div>`;
                
                // 更新模态框内容
                document.getElementById('orderDetailContent').innerHTML = detailsHtml;
            } else {
                document.getElementById('orderDetailContent').innerHTML = 
                    `<div class="alert alert-danger">获取订单详情失败: ${data.message}</div>`;
            }
        })
        .catch(error => {
            document.getElementById('orderDetailContent').innerHTML = 
                `<div class="alert alert-danger">获取订单详情出错: ${error}</div>`;
        });
}

// 显示分配车辆模态框
function showAssignVehicleModal(orderId, cityCode) {
    // 先检查订单状态
    fetch(`/orders/api/order_details/${orderId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const order = data.data;
                
                // 只有待分配状态的订单才能分配车辆
                if (order.order_status !== '待分配') {
                    showLocalToast('只能对待分配状态的订单分配车辆', 'error');
                    return;
                }
                
                // 更新变量并显示模态框
                currentOrderId = orderId;
                currentOrderCity = cityCode;
                
                // 更新模态框内容
                document.getElementById('order-id-display').textContent = orderId;
                document.getElementById('order-city').textContent = cityCode;
                
                // 显示模态框
                const modal = new bootstrap.Modal(document.getElementById('assignVehicleModal'));
                modal.show();
                
                // 加载可用车辆
                loadIdleVehicles(cityCode);
            } else {
                showLocalToast('获取订单详情失败: ' + data.message, 'error');
            }
        })
        .catch(error => {
            showLocalToast('获取订单详情出错: ' + error, 'error');
        });
}

// 加载空闲车辆
function loadIdleVehicles(cityCode) {
    // 显示加载中
    document.getElementById('vehiclesLoading').classList.remove('d-none');
    document.getElementById('vehiclesError').classList.add('d-none');
    document.getElementById('vehiclesContainer').classList.add('d-none');
    
    // 获取空闲车辆数据
    fetch(`/orders/api/idle_vehicles?city=${encodeURIComponent(cityCode)}`)
        .then(response => response.json())
        .then(data => {
            // 隐藏加载中
            document.getElementById('vehiclesLoading').classList.add('d-none');
            document.getElementById('vehiclesContainer').classList.remove('d-none');
            
            if (data.status === 'success') {
                const vehicles = data.data;
                
                if (vehicles.length === 0) {
                    document.getElementById('vehicles-list').innerHTML = 
                        `<tr><td colspan="6" class="text-center">城市 ${cityCode} 中没有可用车辆</td></tr>`;
                } else {
                    // 构建车辆列表HTML
                    let vehiclesHtml = '';
                    
                    vehicles.forEach(vehicle => {
                        vehiclesHtml += `
                        <tr>
                            <td>${vehicle.vehicle_id}</td>
                            <td>${vehicle.plate_number || '未知'}</td>
                            <td>${vehicle.model || '未知'}</td>
                            <td>
                                <div class="progress" style="height: 20px;">
                                    <div class="progress-bar ${getBatteryColorClass(vehicle.battery_level)}" 
                                        role="progressbar" 
                                        style="width: ${vehicle.battery_level}%;" 
                                        aria-valuenow="${vehicle.battery_level}" 
                                        aria-valuemin="0" 
                                        aria-valuemax="100">
                                        ${vehicle.battery_level}%
                                    </div>
                                </div>
                            </td>
                            <td>${vehicle.current_location_name || '未知'}</td>
                            <td>
                                <button class="btn btn-sm btn-success" 
                                        onclick="assignVehicle(${currentOrderId}, ${vehicle.vehicle_id})">
                                    <i class="bi bi-check-circle"></i> 分配
                                </button>
                            </td>
                        </tr>
                        `;
                    });
                    
                    document.getElementById('vehicles-list').innerHTML = vehiclesHtml;
                }
            } else {
                document.getElementById('vehiclesError').classList.remove('d-none');
                document.getElementById('vehiclesError').textContent = `获取车辆失败: ${data.message}`;
            }
        })
        .catch(error => {
            document.getElementById('vehiclesLoading').classList.add('d-none');
            document.getElementById('vehiclesError').classList.remove('d-none');
            document.getElementById('vehiclesError').textContent = `获取车辆出错: ${error}`;
        });
}

// 分配车辆函数
function assignVehicle(orderId, vehicleId) {
    fetch('/orders/api/assign_vehicle', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            order_id: orderId,
            vehicle_id: vehicleId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showLocalToast(data.message, 'success');
            // 关闭车辆列表模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('assignVehicleModal'));
            if (modal) {
                modal.hide();
            }
            
            // 获取订单详情以打开跟踪模态框
            getOrderDetails(orderId)
                .then(orderData => {
                    if (orderData) {
                        openVehicleTrackingModal(vehicleId, orderId, orderData);
                    }
                });
        } else {
            showLocalToast('分配车辆失败: ' + data.message, 'error');
        }
    })
    .catch(error => {
        showLocalToast('分配车辆出错: ' + error, 'error');
    });
}

// 获取订单详情
function getOrderDetails(orderId) {
    return fetch(`/orders/api/order_details/${orderId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('获取订单详情失败');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                return data.data;
            } else {
                throw new Error(data.message);
            }
        })
        .catch(error => {
            showLocalToast('获取订单详情出错: ' + error, 'error');
            return null;
        });
}

// 打开车辆跟踪模态框
function openVehicleTrackingModal(vehicleId, orderId, orderData) {
    // 填充订单信息
    $('#trackingOrderId').text(orderId);
    $('#trackingOrderStatus').text(orderData.order_status);
    $('#trackingPickupLocation').text(orderData.pickup_location);
    $('#trackingPickupX').text(orderData.pickup_location_x);
    $('#trackingPickupY').text(orderData.pickup_location_y);
    $('#trackingDropoffLocation').text(orderData.dropoff_location);
    $('#trackingDropoffX').text(orderData.dropoff_location_x);
    $('#trackingDropoffY').text(orderData.dropoff_location_y);
    
    // 开始轮询车辆位置
    startVehiclePositionPolling(vehicleId);
    
    // 显示模态框
    $('#vehicleTrackingModal').modal('show');
}

// 开始轮询车辆位置
function startVehiclePositionPolling(vehicleId) {
    // 如果已经有轮询，先停止
    stopVehiclePositionPolling();
    
    // 设置当前轮询的车辆ID
    currentPollingVehicleId = vehicleId;
    
    // 立即获取一次位置
    updateVehiclePosition(vehicleId);
    
    // 每3秒更新一次位置
    pollingInterval = setInterval(() => {
        updateVehiclePosition(vehicleId);
    }, 3000);
}

// 停止轮询车辆位置
function stopVehiclePositionPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
        currentPollingVehicleId = null;
    }
}

// 更新车辆位置
function updateVehiclePosition(vehicleId) {
    // 获取车辆位置
    fetch(`/orders/api/vehicle_position/${vehicleId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const vehicleData = data.data;
                
                // 更新车辆信息
                $('#trackingVehicleId').text(vehicleData.vehicle_id);
                $('#trackingVehicleStatus').text(vehicleData.status);
                $('#trackingVehicleLocation').text(vehicleData.location_name);
                $('#trackingVehicleX').text(vehicleData.location_x);
                $('#trackingVehicleY').text(vehicleData.location_y);
                
                // 检查车辆是否在移动
                checkVehicleMovement(vehicleId);
                
                // 计算移动进度
                updateMovementProgress(vehicleData);
            } else {
                console.error('获取车辆位置失败:', data.message);
            }
        })
        .catch(error => {
            console.error('获取车辆位置出错:', error);
        });
}

// 检查车辆是否在移动
function checkVehicleMovement(vehicleId) {
    fetch(`/orders/api/vehicle_movement_status/${vehicleId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const isMoving = data.data.is_moving;
                
                // 如果车辆停止移动且轮询仍在进行，将轮询间隔改为10秒
                if (!isMoving && pollingInterval) {
                    clearInterval(pollingInterval);
                    pollingInterval = setInterval(() => {
                        updateVehiclePosition(vehicleId);
                    }, 10000);
                }
            }
        })
        .catch(error => {
            console.error('获取车辆移动状态出错:', error);
        });
}

// 更新移动进度
function updateMovementProgress(vehicleData) {
    const vehicleX = parseFloat(vehicleData.location_x);
    const vehicleY = parseFloat(vehicleData.location_y);
    const pickupX = parseFloat($('#trackingPickupX').text());
    const pickupY = parseFloat($('#trackingPickupY').text());
    const dropoffX = parseFloat($('#trackingDropoffX').text());
    const dropoffY = parseFloat($('#trackingDropoffY').text());
    
    // 计算距离
    const calcDistance = (x1, y1, x2, y2) => Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
    
    const distToPickup = calcDistance(vehicleX, vehicleY, pickupX, pickupY);
    const distToDropoff = calcDistance(vehicleX, vehicleY, dropoffX, dropoffY);
    const totalDist = calcDistance(pickupX, pickupY, dropoffX, dropoffY);
    
    let progress = 0;
    let phase = "";
    
    // 判断阶段
    if (vehicleData.location_name.includes('前往上车点')) {
        // 前往上车点阶段
        const initialDistToPickup = calcDistance(
            parseFloat($('#initialVehicleX').data('value') || vehicleX), 
            parseFloat($('#initialVehicleY').data('value') || vehicleY), 
            pickupX, pickupY
        );
        
        progress = Math.min(100, Math.max(0, (1 - distToPickup / initialDistToPickup) * 50));
        phase = "前往上车点";
        $('#progressPhase').text(phase);
    } else if (vehicleData.location_name.includes('前往下车点')) {
        // 前往下车点阶段
        progress = Math.min(100, Math.max(50, 50 + (1 - distToDropoff / totalDist) * 50));
        phase = "前往下车点";
        $('#progressPhase').text(phase);
    } else if (distToPickup < 5) {
        // 已到达上车点
        progress = 50;
        phase = "已到达上车点";
        $('#progressPhase').text(phase);
    } else if (distToDropoff < 5) {
        // 已到达目的地
        progress = 100;
        phase = "已到达目的地";
        $('#progressPhase').text(phase);
    }
    
    // 更新进度条
    $('#movementProgress').css('width', `${progress}%`).attr('aria-valuenow', progress);
    
    // 第一次获取车辆位置时，存储初始位置用于计算进度
    if (!$('#initialVehicleX').length) {
        $('body').append(`<div id="initialVehicleX" data-value="${vehicleX}" style="display:none;"></div>`);
        $('body').append(`<div id="initialVehicleY" data-value="${vehicleY}" style="display:none;"></div>`);
    }
}

// 一键分配车辆功能
function autoAssignVehicles() {
    // 显示确认对话框
    if (!confirm('确定要为所有待分配订单（包括其他页面的订单）自动分配最近的车辆吗？')) {
        return;
    }
    
    // 显示加载指示器
    showLoadingOverlay('正在为所有搜索结果中的订单分配车辆，请稍候...');
    
    // 获取当前URL和搜索参数
    const url = new URL(window.location.href);
    const searchParams = {};
    
    // 提取所有搜索参数（除了page参数）
    for (const [key, value] of url.searchParams.entries()) {
        if (key !== 'page') {
            searchParams[key] = value;
        }
    }
    
    // 调用后端API获取所有符合条件的待分配订单ID
    fetch('/orders/api/get_waiting_order_ids', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            search_params: searchParams
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const orderIds = data.data.order_ids;
            
            // 如果没有待分配订单，提示用户
            if (orderIds.length === 0) {
                hideLoadingOverlay();
                showLocalToast('没有待分配的订单', 'warning');
                return;
            }
            
            // 显示找到的订单数量
            showLocalToast(`找到 ${orderIds.length} 个待分配订单，开始分配...`, 'info');
            
            // 调用后端API进行一键分配
            return fetch('/orders/api/auto_assign_vehicles', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    order_ids: orderIds
                })
            });
        } else {
            throw new Error(data.message || '获取待分配订单失败');
        }
    })
    .then(response => {
        if (!response) return null; // 处理前一个then可能的空返回
        return response.json();
    })
    .then(data => {
        hideLoadingOverlay();
        
        // 如果前一个then返回null，直接退出处理
        if (!data) return;
        
        if (data.status === 'success') {
            // 构建成功和失败信息
            const successful = data.data.successful;
            const failed = data.data.failed;
            
            let resultMessage = `<div class="text-center mb-3">${data.message}</div>`;
            
            if (successful.length > 0) {
                resultMessage += '<div class="mb-2"><strong>成功分配：</strong></div>';
                resultMessage += '<ul class="list-group mb-3" style="max-height: 200px; overflow-y: auto;">';
                successful.forEach(item => {
                    resultMessage += `<li class="list-group-item list-group-item-success">
                        订单 #${item.order_id} 分配给车辆 ${item.plate_number || item.vehicle_id}
                        ${item.distance ? `（距离：${item.distance}）` : ''}
                    </li>`;
                });
                resultMessage += '</ul>';
            }
            
            if (failed.length > 0) {
                resultMessage += '<div class="mb-2"><strong>分配失败：</strong></div>';
                resultMessage += '<ul class="list-group" style="max-height: 200px; overflow-y: auto;">';
                failed.forEach(item => {
                    resultMessage += `<li class="list-group-item list-group-item-danger">
                        订单 #${item.order_id}：${item.reason}
                    </li>`;
                });
                resultMessage += '</ul>';
            }
            
            // 显示结果模态框
            const resultModal = showResultModal('一键分配结果', resultMessage);
            
            // 如果有成功分配的订单，在用户点击确定按钮时刷新页面
            if (successful.length > 0) {
                const okButton = resultModal.querySelector('.modal-footer .btn-primary');
                if (okButton) {
                    okButton.addEventListener('click', function() {
                        location.reload();
                    });
                }
            }
        } else {
            showLocalToast(`一键分配失败: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        hideLoadingOverlay();
        showLocalToast(`一键分配出错: ${error}`, 'error');
    });
}

// 显示加载覆盖层
function showLoadingOverlay(message = '加载中...') {
    // 如果已存在，先移除
    hideLoadingOverlay();
    
    // 创建加载覆盖层
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div class="loading-content">
            <div class="spinner-border text-light" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
            <div class="mt-2">${message}</div>
        </div>
    `;
    
    // 添加样式
    const style = document.createElement('style');
    style.textContent = `
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }
        .loading-content {
            text-align: center;
            color: white;
        }
    `;
    
    // 添加到文档
    document.head.appendChild(style);
    document.body.appendChild(overlay);
}

// 隐藏加载覆盖层
function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
}

// 显示结果模态框
function showResultModal(title, content) {
    // 检查是否已存在结果模态框
    let resultModal = document.getElementById('resultModal');
    
    if (!resultModal) {
        // 创建模态框
        resultModal = document.createElement('div');
        resultModal.id = 'resultModal';
        resultModal.className = 'modal fade';
        resultModal.tabIndex = -1;
        resultModal.setAttribute('aria-labelledby', 'resultModalLabel');
        resultModal.setAttribute('aria-hidden', 'true');
        
        resultModal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="resultModalLabel">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body" id="resultModalBody">
                        ${content}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal">确定</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(resultModal);
    } else {
        // 更新已存在的模态框内容
        resultModal.querySelector('.modal-title').textContent = title;
        resultModal.querySelector('.modal-body').innerHTML = content;
    }
    
    // 确保模态框不会自动关闭
    const bsModal = new bootstrap.Modal(resultModal, {
        backdrop: 'static', // 点击背景不会关闭
        keyboard: false     // 按ESC键不会关闭
    });
    
    // 显示模态框
    bsModal.show();
    
    // 返回模态框DOM元素，方便调用者添加事件监听器
    return resultModal;
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 查找最近车辆按钮事件
    const findNearestBtn = document.getElementById('findNearestBtn');
    if (findNearestBtn) {
        findNearestBtn.addEventListener('click', function() {
            if (!currentOrderId || !currentOrderCity) {
                showLocalToast('缺少订单信息或城市信息', 'error');
                return;
            }

            // 显示加载中
            document.getElementById('vehiclesLoading').classList.remove('d-none');
            document.getElementById('vehiclesError').classList.add('d-none');
            document.getElementById('vehiclesContainer').classList.add('d-none');
            
            // 首先获取订单详情以获取上车点坐标
            fetch(`/orders/api/order_details/${currentOrderId}`)
                .then(response => response.json())
                .then(orderData => {
                    if (orderData.status === 'success') {
                        const order = orderData.data;
                        // 获取上车点坐标
                        const pickupX = order.pickup_location_x;
                        const pickupY = order.pickup_location_y;
                        
                        console.log(`订单ID: ${currentOrderId}, 上车点坐标: (${pickupX}, ${pickupY})`);
                        
                        // 然后调用查找最近车辆的API，传递上车点坐标
                        return fetch(`/orders/api/find_nearest_vehicle?city=${encodeURIComponent(currentOrderCity)}&pickup_x=${pickupX}&pickup_y=${pickupY}`);
                    } else {
                        throw new Error(`获取订单详情失败: ${orderData.message}`);
                    }
                })
                .then(response => response.json())
                .then(data => {
                    // 隐藏加载中
                    document.getElementById('vehiclesLoading').classList.add('d-none');
                    document.getElementById('vehiclesContainer').classList.remove('d-none');
                    
                    if (data.status === 'success') {
                        const vehicle = data.data;
                        
                        // 构建车辆列表HTML
                        let vehicleHtml = `
                        <tr>
                            <td>${vehicle.vehicle_id}</td>
                            <td>${vehicle.plate_number || '未知'}</td>
                            <td>${vehicle.model || '未知'}</td>
                            <td>
                                <div class="progress" style="height: 20px;">
                                    <div class="progress-bar ${getBatteryColorClass(vehicle.battery_level)}" 
                                        role="progressbar" 
                                        style="width: ${vehicle.battery_level}%;" 
                                        aria-valuenow="${vehicle.battery_level}" 
                                        aria-valuemin="0" 
                                        aria-valuemax="100">
                                        ${vehicle.battery_level}%
                                    </div>
                                </div>
                            </td>
                            <td>${vehicle.current_location_name || '未知'}</td>
                            <td>
                                <button class="btn btn-sm btn-success" 
                                        onclick="assignVehicle(${currentOrderId}, ${vehicle.vehicle_id})">
                                    <i class="bi bi-check-circle"></i> 分配
                                </button>
                            </td>
                        </tr>
                        `;
                        
                        document.getElementById('vehicles-list').innerHTML = vehicleHtml;
                        
                        // 显示推荐消息
                        showLocalToast(`推荐车辆: ${vehicle.plate_number || vehicle.vehicle_id}`, 'success');
                        
                    } else {
                        document.getElementById('vehiclesError').classList.remove('d-none');
                        document.getElementById('vehiclesError').textContent = `获取最近车辆失败: ${data.message}`;
                        
                        // 显示空的车辆列表
                        document.getElementById('vehicles-list').innerHTML = 
                            `<tr><td colspan="6" class="text-center">城市 ${currentOrderCity} 中没有可用车辆</td></tr>`;
                    }
                })
                .catch(error => {
                    document.getElementById('vehiclesLoading').classList.add('d-none');
                    document.getElementById('vehiclesError').classList.remove('d-none');
                    document.getElementById('vehiclesError').textContent = `获取最近车辆出错: ${error}`;
                });
        });
    }
    
    // 刷新车辆位置按钮点击事件
    const refreshTrackingBtn = document.getElementById('refreshTrackingBtn');
    if (refreshTrackingBtn) {
        refreshTrackingBtn.addEventListener('click', function() {
            if (currentPollingVehicleId) {
                updateVehiclePosition(currentPollingVehicleId);
            }
        });
    }
    
    // 模态框关闭时停止轮询
    const vehicleTrackingModal = document.getElementById('vehicleTrackingModal');
    if (vehicleTrackingModal) {
        vehicleTrackingModal.addEventListener('hidden.bs.modal', function() {
            stopVehiclePositionPolling();
        });
    }
    
    // 获取跳转按钮和输入框
    const jumpButton = document.getElementById('jumpButton');
    const jumpToPage = document.getElementById('jumpToPage');
    
    if (jumpButton && jumpToPage) {
        // 为跳转按钮添加点击事件
        jumpButton.addEventListener('click', function() {
            jumpToPageHandler();
        });
        
        // 为输入框添加回车事件
        jumpToPage.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                jumpToPageHandler();
            }
        });
    }
    
    // 跳转到指定页面的处理函数
    function jumpToPageHandler() {
        const pageNum = parseInt(jumpToPage.value);
        const maxPage = parseInt(jumpToPage.getAttribute('max'));
        
        if (pageNum && pageNum > 0 && pageNum <= maxPage) {
            // 获取当前URL
            let url = new URL(window.location.href);
            // 设置page参数
            url.searchParams.set('page', pageNum);
            // 跳转到新页面
            window.location.href = url.toString();
        } else {
            // 输入无效页码时显示提示
            alert('请输入有效的页码（1-' + maxPage + '）');
            jumpToPage.focus();
        }
    }
    
    // 清除搜索参数函数
    window.removeSearchParam = function(field) {
        let url = new URL(window.location.href);
        url.searchParams.delete(field);
        window.location.href = url.toString();
    }
    
    // 清除所有搜索参数函数
    window.clearAllSearchParams = function() {
        let url = new URL(window.location.href);
        // 获取页面基础URL（不包含查询参数）
        window.location.href = url.origin + url.pathname;
    }
    
    // 一键分配按钮事件
    const autoAssignBtn = document.getElementById('autoAssignBtn');
    if (autoAssignBtn) {
        autoAssignBtn.addEventListener('click', function() {
            autoAssignVehicles();
        });
    }
    
    // 获取批量添加订单按钮和相关元素
    const generateOrdersBtn = document.getElementById('generateOrdersBtn');
    const bulkAddOrdersForm = document.getElementById('bulkAddOrdersForm');
    const generateProgress = document.getElementById('generateProgress');
    const generationStatus = document.getElementById('generationStatus');
    
    if (generateOrdersBtn) {
        generateOrdersBtn.addEventListener('click', function() {
            // 检查表单有效性
            const citySelect = document.getElementById('citySelect');
            const orderCount = document.getElementById('orderCount');
            
            if (!citySelect.value) {
                showLocalToast('请选择城市', 'warning');
                citySelect.focus();
                return;
            }
            
            if (!orderCount.value || orderCount.value < 1 || orderCount.value > 1000) {
                showLocalToast('订单数量必须在1-1000之间', 'warning');
                orderCount.focus();
                return;
            }
            
            // 显示进度条和状态
            generateProgress.style.display = 'block';
            generateProgress.querySelector('.progress-bar').style.width = '20%';
            generationStatus.style.display = 'block';
            generationStatus.textContent = '正在生成订单，请稍候...';
            generationStatus.className = 'alert alert-info';
            
            // 禁用提交按钮
            generateOrdersBtn.disabled = true;
            
            // 准备表单数据
            const formData = {
                city: citySelect.value,
                order_count: parseInt(orderCount.value)
            };
            
            // 获取是否更新最后登录时间选项
            const updateLastLoginTime = document.getElementById('updateLastLoginTime');
            if (updateLastLoginTime) {
                formData.update_last_login = updateLastLoginTime.checked;
            }
            
            // 发送API请求
            fetch('/orders/api/bulk_add_orders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })
            .then(response => {
                // 更新进度条
                generateProgress.querySelector('.progress-bar').style.width = '70%';
                return response.json();
            })
            .then(data => {
                // 更新进度条到100%
                generateProgress.querySelector('.progress-bar').style.width = '100%';
                
                if (data.status === 'success') {
                    // 显示成功消息
                    generationStatus.textContent = data.message;
                    generationStatus.className = 'alert alert-success';
                    
                    // 显示Toast消息
                    showLocalToast(data.message, 'success');
                    
                    // 3秒后刷新页面
                    setTimeout(function() {
                        window.location.reload();
                    }, 3000);
                } else {
                    // 显示错误消息
                    generationStatus.textContent = data.message;
                    generationStatus.className = 'alert alert-danger';
                    showLocalToast(data.message, 'error');
                    // 启用提交按钮
                    generateOrdersBtn.disabled = false;
                }
            })
            .catch(error => {
                // 显示错误消息
                generateProgress.querySelector('.progress-bar').style.width = '100%';
                generationStatus.textContent = '生成订单时发生错误: ' + error;
                generationStatus.className = 'alert alert-danger';
                showLocalToast('生成订单时发生错误', 'error');
                // 启用提交按钮
                generateOrdersBtn.disabled = false;
            });
        });
    }
});