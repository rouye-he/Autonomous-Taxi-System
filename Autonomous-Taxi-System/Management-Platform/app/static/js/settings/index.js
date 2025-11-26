/**
 * 设置页面通用脚本
 */

// Toast通知函数
function showToast(message, type = 'info') {
    const toastHTML = `
        <div class="toast align-items-center text-white bg-${type} border-0 mb-3" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    // Create container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Add toast to container
    toastContainer.innerHTML += toastHTML;
    
    // Initialize and show toast
    const toastElList = [].slice.call(document.querySelectorAll('.toast'));
    const toastList = toastElList.map(function(toastEl) {
        return new bootstrap.Toast(toastEl, {delay: 3000});
    });
    toastList.forEach(toast => toast.show());
}

// 辅助函数：从表单中收集参数数据
function getFormParameters(formId) {
    const form = document.getElementById(formId);
    if (!form) return {};
    
    const formData = {};
    const elements = form.elements;
    
    for (let i = 0; i < elements.length; i++) {
        const element = elements[i];
        // 跳过按钮元素
        if (element.tagName === 'BUTTON') continue;
        
        if (element.name) {
            if (element.type === 'checkbox') {
                formData[element.name] = element.checked;
            } else if (element.type === 'select-one') {
                formData[element.name] = element.value;
            } else if (element.type === 'number') {
                formData[element.name] = parseFloat(element.value);
            } else {
                formData[element.name] = element.value;
            }
        }
    }
    
    return formData;
}

// 加载系统参数并填充表单
function loadSystemParameters(formId) {
    console.log(`开始加载系统参数: ${formId}`);
    
    // 获取加载指示器和内容元素
    const loadingElement = document.getElementById(`${formId}-loading`);
    const contentElement = document.getElementById(`${formId}-content`);
    
    // 检查元素是否存在
    if (!loadingElement) {
        console.error(`加载系统参数错误: 找不到 ${formId}-loading 元素`);
        showToast(`界面元素错误: 找不到 ${formId}-loading 元素`, 'danger');
        return;
    }
    
    if (!contentElement) {
        console.error(`加载系统参数错误: 找不到 ${formId}-content 元素`);
        showToast(`界面元素错误: 找不到 ${formId}-content 元素`, 'danger');
        return;
    }
    
    console.log(`显示${formId}加载状态`);
    // 显示加载指示器
    loadingElement.style.display = 'block';
    contentElement.style.display = 'none';
    
    console.log('发送系统参数请求...');
    // 发送请求获取系统参数
    fetch('/api/v1/system_parameters')
        .then(response => {
            if (!response.ok) {
                throw new Error('网络请求错误，状态码: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log('收到系统参数响应:', data.success);
            if (data.success) {
                // 填充表单字段
                let filledCount = 0;
                Object.keys(data.parameters).forEach(key => {
                    const element = document.getElementById(key);
                    if (element) {
                        if (element.type === 'checkbox') {
                            element.checked = data.parameters[key];
                        } else if (element.type === 'select-one') {
                            element.value = data.parameters[key];
                        } else {
                            element.value = data.parameters[key];
                        }
                        filledCount++;
                    }
                });
                console.log(`填充了${filledCount}个表单元素`);
                
                // 隐藏加载指示器，显示内容
                loadingElement.style.display = 'none';
                contentElement.style.display = 'block';
                console.log(`${formId}加载完成，显示内容`);
                
            } else {
                console.error('加载系统参数失败:', data.message);
                showToast(data.message || '加载系统参数失败', 'danger');
                // 出错时也显示内容，避免界面卡在加载状态
                loadingElement.style.display = 'none';
                contentElement.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('加载系统参数时出错:', error);
            showToast('加载系统参数时发生错误: ' + error.message, 'danger');
            // 隐藏加载指示器，显示内容（即使出错）
            if (loadingElement) loadingElement.style.display = 'none';
            if (contentElement) contentElement.style.display = 'block';
        });
}

// 保存表单参数组
function saveParamsGroup(formId) {
    const parameters = getFormParameters(formId);
    const submitBtn = document.querySelector(`#${formId} button[type="button"]`);
    const originalText = submitBtn.innerHTML;
    
    // 禁用按钮，显示加载状态
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 保存中...';
    
    // 发送请求保存参数
    fetch('/api/v1/system_parameters', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ parameters })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('网络请求错误');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showToast('参数保存成功', 'success');
        } else {
            showToast(data.message || '保存失败', 'danger');
        }
    })
    .catch(error => {
        console.error('保存参数时出错:', error);
        showToast('保存参数时发生错误', 'danger');
    })
    .finally(() => {
        // 恢复按钮状态
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    });
}

// 获取CSRF令牌
function getCsrfToken() {
    // 从cookie中获取CSRF令牌
    const name = 'csrf_token=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookieArray = decodedCookie.split(';');
    for (let i = 0; i < cookieArray.length; i++) {
        let cookie = cookieArray[i].trim();
        if (cookie.indexOf(name) === 0) {
            return cookie.substring(name.length, cookie.length);
        }
    }
    return '';
}

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('设置页面JS初始化...');
    
    // 绑定刷新按钮事件
    const refreshButtons = {
        'refreshGeneralSettings': 'general-settings',
        'refreshVehicleSettings': 'vehicle-settings',
        'refreshChargingSettings': 'charging-settings',
        'refreshOrderSettings': 'order-settings'
    };
    
    Object.keys(refreshButtons).forEach(buttonId => {
        const button = document.getElementById(buttonId);
        if (button) {
            console.log('绑定刷新按钮:', buttonId);
            button.addEventListener('click', function() {
                console.log('点击刷新按钮:', buttonId);
                loadSystemParameters(refreshButtons[buttonId]);
            });
        }
    });
    
    // 为充电站经济参数和充电站系统参数表单绑定提交事件
    document.getElementById('chargingEconomicsForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        saveParamsGroup('chargingEconomicsForm');
    });
    
    document.getElementById('chargingSystemForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        saveParamsGroup('chargingSystemForm');
    });
});
