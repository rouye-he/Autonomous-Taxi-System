/**
 * 系统共用JavaScript函数库
 */

// 全局变量定义
let lastNotificationCheck = new Date();
let socket = null; // 添加WebSocket连接变量

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log("系统初始化开始");
    
    // 初始化WebSocket连接
    initSocketIO();
    
    // 加载通知数量
    loadNotifications();
    
    // 初始化通知下拉菜单
    initNotificationDropdown();
    
    console.log("系统初始化完成");
});

/**
 * 初始化Socket.IO连接
 */
function initSocketIO() {
    try {
        // 检查是否存在io对象(Socket.IO)
        if (typeof io !== 'undefined') {
            console.log("初始化WebSocket连接...");
            
            // 创建Socket.IO连接
            socket = io();
            
            // 连接成功事件
            socket.on('connect', function() {
                console.log('WebSocket连接成功');
            });
            
            // 新通知事件
            socket.on('new_notification', function(notification) {
                console.log('收到新通知:', notification);
                
                // 显示通知弹窗
                showNotificationToast(notification);
                
                // 刷新通知数据
                loadNotifications();
                
                // 更新通知下拉菜单
                loadNotificationItems();
            });
            
            // 添加窗口大小变化监听器，更新通知弹窗位置
            window.addEventListener('resize', function() {
                updateNotificationContainerPosition();
            });
        } else {
            console.error("Socket.IO未加载，无法初始化WebSocket连接");
        }
    } catch (error) {
        console.error('初始化WebSocket连接失败:', error);
    }
}

/**
 * 更新通知弹窗容器位置
 */
function updateNotificationContainerPosition() {
    const notificationContainer = document.getElementById('notification-popup-container');
    const bellIcon = document.getElementById('notificationDropdown');
    
    if (notificationContainer && bellIcon) {
        const bellRect = bellIcon.getBoundingClientRect();
        // 将容器定位在铃铛按钮左侧
        notificationContainer.style.top = (bellRect.top) + 'px';
        notificationContainer.style.right = (window.innerWidth - bellRect.left + 10) + 'px';
    }
}

/**
 * 显示通知弹窗
 */
function showNotificationToast(notification) {
    // 创建自定义通知弹窗容器，设置为单例模式
    let notificationContainer = document.getElementById('notification-popup-container');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'notification-popup-container';
        notificationContainer.style.position = 'fixed';
        notificationContainer.style.zIndex = '9999';
        
        // 获取铃铛按钮位置
        const bellIcon = document.getElementById('notificationDropdown');
        if (bellIcon) {
            const bellRect = bellIcon.getBoundingClientRect();
            // 将容器定位在铃铛按钮左侧
            notificationContainer.style.top = (bellRect.top) + 'px';
            notificationContainer.style.right = (window.innerWidth - bellRect.left + 10) + 'px';
        } else {
            // 默认位置
            notificationContainer.style.top = '60px';
            notificationContainer.style.right = '60px';
        }
        
        // 添加一个小三角形，指向铃铛按钮
        const triangle = document.createElement('div');
        triangle.style.position = 'absolute';
        triangle.style.top = '10px'; // 居中对齐
        triangle.style.right = '-10px'; // 放在右侧边缘
        triangle.style.width = '0';
        triangle.style.height = '0';
        triangle.style.borderTop = '10px solid transparent';
        triangle.style.borderBottom = '10px solid transparent';
        triangle.style.borderLeft = '10px solid #fff'; // 使三角形指向右侧
        triangle.style.zIndex = '10000';
        
        notificationContainer.appendChild(triangle);
        document.body.appendChild(notificationContainer);
    }
    
    // 先移除当前的通知弹窗（如果有）
    while (notificationContainer.childNodes.length > 1) { // 保留第一个子元素（三角形）
        notificationContainer.removeChild(notificationContainer.lastChild);
    }
    
    // 创建通知弹窗元素
    const notificationPopup = document.createElement('div');
    notificationPopup.className = 'notification-popup';
    notificationPopup.style.backgroundColor = notification.priority === '警告' ? '#fff3cd' : '#d1ecf1';
    notificationPopup.style.border = `1px solid ${notification.priority === '警告' ? '#ffeeba' : '#bee5eb'}`;
    notificationPopup.style.color = notification.priority === '警告' ? '#856404' : '#0c5460';
    notificationPopup.style.padding = '15px';
    notificationPopup.style.borderRadius = '5px';
    notificationPopup.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
    notificationPopup.style.width = '300px';
    notificationPopup.style.animation = 'slideInLeft 0.5s ease-out';
    notificationPopup.style.position = 'relative';
    notificationPopup.style.cursor = 'pointer';
    
    // 更新三角形颜色以匹配通知弹窗
    const triangle = notificationContainer.firstChild;
    if (triangle) {
        triangle.style.borderLeft = `10px solid ${notification.priority === '警告' ? '#fff3cd' : '#d1ecf1'}`;
    }
    
    // 添加CSS动画
    const styleElement = document.createElement('style');
    styleElement.textContent = `
        @keyframes slideInLeft {
            from { transform: translateX(20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
    `;
    document.head.appendChild(styleElement);
    
    // 添加通知内容
    notificationPopup.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div style="font-weight: bold; margin-bottom: 5px;">${notification.title}</div>
                <div style="font-size: 0.9em;">${notification.content || ''}</div>
            </div>
            <div style="font-size: 16px; cursor: pointer; padding: 0 5px;" onclick="event.stopPropagation();">&times;</div>
        </div>
        <div style="font-size: 0.8em; margin-top: 8px; text-align: right;">
            ${new Date().toLocaleTimeString()}
        </div>
    `;
    
    // 点击关闭按钮移除通知
    notificationPopup.querySelector('div[onclick]').addEventListener('click', function(e) {
        e.stopPropagation();
        notificationPopup.style.animation = 'fadeOut 0.5s';
        setTimeout(() => {
            if (notificationPopup.parentNode) {
                notificationPopup.parentNode.removeChild(notificationPopup);
            }
        }, 500);
    });
    
    // 点击通知标记为已读并跳转到通知页面
    notificationPopup.addEventListener('click', function() {
        if (notification.id) {
            markNotificationAsRead(notification.id);
        }
        window.location.href = '/notifications/';
    });
    
    // 添加到容器
    notificationContainer.appendChild(notificationPopup);
    
    // 设置自动消失
    setTimeout(() => {
        if (notificationPopup.parentNode) {
            notificationPopup.style.animation = 'fadeOut 0.5s';
            setTimeout(() => {
                if (notificationPopup.parentNode) {
                    notificationPopup.parentNode.removeChild(notificationPopup);
                }
            }, 500);
        }
    }, 8000);
}

/**
 * 初始化通知下拉菜单
 */
function initNotificationDropdown() {
    // 获取通知下拉菜单触发器
    const notificationDropdown = document.getElementById('notificationDropdown');
    if (notificationDropdown) {
        // 当点击通知图标时加载最新通知
        notificationDropdown.addEventListener('click', function() {
            loadNotificationItems();
            
            // 关闭通知弹窗
            hideNotificationPopup();
        });
    }
}

/**
 * 隐藏通知弹窗
 */
function hideNotificationPopup() {
    const notificationContainer = document.getElementById('notification-popup-container');
    if (notificationContainer) {
        // 先设置淡出动画
        const notifications = notificationContainer.querySelectorAll('.notification-popup');
        notifications.forEach(notif => {
            notif.style.animation = 'fadeOut 0.5s';
        });
        
        // 然后移除弹窗（保留容器和三角形）
        setTimeout(() => {
            while (notificationContainer.childNodes.length > 1) {
                notificationContainer.removeChild(notificationContainer.lastChild);
            }
        }, 500);
    }
}

/**
 * 加载通知下拉菜单内容
 */
function loadNotificationItems() {
    const notificationItems = document.querySelector('.notification-items');
    if (!notificationItems) return;
    
    // 显示加载中
    notificationItems.innerHTML = `
        <li class="text-center py-2">
            <div class="spinner-border spinner-border-sm text-primary" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
        </li>
    `;
    
    // 获取最新通知
    fetch('/notifications/api/latest?limit=3')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.data && data.data.length > 0) {
                // 清空容器
                notificationItems.innerHTML = '';
                
                // 添加通知项
                data.data.forEach(function(notification) {
                    const item = document.createElement('li');
                    
                    // 格式化创建时间
                    let createdTime = '刚刚';
                    if (notification.created_at) {
                        const date = new Date(notification.created_at);
                        createdTime = date.toLocaleString();
                    }
                    
                    // 设置通知项内容
                    item.innerHTML = `
                        <a class="dropdown-item notification-item" href="#" data-id="${notification.id}">
                            <div class="d-flex align-items-center">
                                <div class="notification-icon me-2">
                                    <i class="bi bi-${notification.priority === '警告' ? 'exclamation-triangle-fill text-warning' : 'info-circle-fill text-primary'}"></i>
                                </div>
                                <div class="notification-content">
                                    <div class="fw-bold text-truncate" style="max-width: 220px;">${notification.title}</div>
                                    <div class="small text-muted">${createdTime}</div>
                                </div>
                            </div>
                        </a>
                    `;
                    
                    // 点击通知项事件
                    item.querySelector('.notification-item').addEventListener('click', function(e) {
                        e.preventDefault();
                        const id = this.getAttribute('data-id');
                        markNotificationAsRead(id);
                        window.location.href = '/notifications/';
                    });
                    
                    notificationItems.appendChild(item);
                });
            } else {
                // 没有通知时显示提示
                notificationItems.innerHTML = `
                    <li class="dropdown-item text-center py-2">暂无未读通知</li>
                `;
            }
        })
        .catch(error => {
            console.error('获取通知失败:', error);
            notificationItems.innerHTML = `
                <li class="dropdown-item text-center py-2 text-danger">加载失败</li>
            `;
        });
}

/**
 * 显示提示消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型 (success/error/warning/info)
 */
function showToast(message, type = 'info', duration = 3000) {
    // 创建toast容器（如果不存在）
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // 创建新的toast元素
    const toast = document.createElement('div');
    toast.className = `custom-toast toast-${type === 'error' ? 'danger' : type}`;
    toast.textContent = message;
    
    // 添加到容器
    toastContainer.appendChild(toast);
    
    // 设置自动消失
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.5s forwards';
        setTimeout(() => {
            toast.remove();
        }, 500);
    }, duration);
}

// 加载通知数量和最新通知
function loadNotifications() {
    // 获取未读通知数量
    fetch('/notifications/api/unread_count')
        .then(response => response.json())
        .then(data => {
            const countElement = document.querySelector('.notification-count');
            if (data.status === 'success') {
                const count = data.count;
                countElement.textContent = count;
                
                // 如果没有未读通知，隐藏badge
                if (count <= 0) {
                    countElement.style.display = 'none';
                } else {
                    countElement.style.display = 'inline-block';
                }
            } else {
                console.error('获取通知数量失败:', data.message);
                countElement.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('获取通知数量出错:', error);
            document.querySelector('.notification-count').style.display = 'none';
        });
}

// 标记通知为已读
function markNotificationAsRead(id) {
    fetch(`/notifications/mark_read/${id}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // 如果不是已经标记为已读，则显示提示
            if (!data.already_read) {
           
                
                // 刷新通知数据
                loadNotifications();
                
                // 更新通知下拉菜单
                loadNotificationItems();
            }
        } 
    })
    .catch(error => {
        console.error('标记通知为已读时出错:', error);

    });
} 