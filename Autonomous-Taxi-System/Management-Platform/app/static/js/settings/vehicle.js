/**
 * 车辆参数设置页面专用脚本
 */

// 车型参数保存函数
function saveVehicleParams(formId) {
    const parameters = getFormParameters(formId);
    const modalFooter = document.querySelector(`#${formId}`).closest('.modal').querySelector('.modal-footer');
    const submitBtn = modalFooter.querySelector('.btn-primary') || modalFooter.querySelector('.btn-success') || modalFooter.querySelector('.btn-danger');
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
            showToast('车型参数保存成功', 'success');
            // 可选：关闭模态框
            const modalEl = document.querySelector(`#${formId}`).closest('.modal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            modal.hide();
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

// 在页面加载时初始化车辆参数页面
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有模态框
    const vehicleModals = [
        'alphaX1Modal', 'alphaNexusModal', 'alphaVoyagerModal',
        'novaS1Modal', 'novaQuantumModal', 'novaPulseModal',
        'neon500Modal', 'neonZeroModal'
    ];
    
    vehicleModals.forEach(modalId => {
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
            console.log(`初始化模态框: ${modalId}`);
            new bootstrap.Modal(modalElement);
        }
    });
    
    // 如果当前是车辆参数页面，加载数据
    if (document.getElementById('vehicle-params')) {
        const vehicleParamsTab = document.querySelector('a[href="#vehicle-params"]');
        
        // 如果标签页已激活，直接加载数据
        if (vehicleParamsTab.classList.contains('active')) {
            loadSystemParameters('vehicle-params');
        }
        
        // 监听车辆参数标签页的激活事件
        vehicleParamsTab.addEventListener('shown.bs.tab', function() {
            loadSystemParameters('vehicle-params');
        });
        
        // 为刷新按钮添加事件监听器
        if (document.getElementById('refreshParams')) {
            document.getElementById('refreshParams').addEventListener('click', function() {
                loadSystemParameters('vehicle-params');
            });
        }
    }
    
    // 如果当前是充电站参数页面，加载数据
    if (document.getElementById('charging-params')) {
        const chargingParamsTab = document.querySelector('a[href="#charging-params"]');
        
        // 如果标签页已激活，直接加载数据
        if (chargingParamsTab && chargingParamsTab.classList.contains('active')) {
            loadSystemParameters('charging-params');
        }
        
        // 监听充电站参数标签页的激活事件
        chargingParamsTab && chargingParamsTab.addEventListener('shown.bs.tab', function() {
            loadSystemParameters('charging-params');
        });
        
        // 为刷新按钮添加事件监听器
        if (document.getElementById('refreshChargingParams')) {
            document.getElementById('refreshChargingParams').addEventListener('click', function() {
                loadSystemParameters('charging-params');
            });
        }
        
        // 充电站经济参数表单提交事件
        const economicsForm = document.getElementById('chargingEconomicsForm');
        if (economicsForm) {
            economicsForm.addEventListener('submit', function(e) {
                e.preventDefault();
                saveParamsGroup('chargingEconomicsForm');
            });
        }
        
        // 充电站系统参数表单提交事件
        const systemForm = document.getElementById('chargingSystemForm');
        if (systemForm) {
            systemForm.addEventListener('submit', function(e) {
                e.preventDefault();
                saveParamsGroup('chargingSystemForm');
            });
        }
    }
});
