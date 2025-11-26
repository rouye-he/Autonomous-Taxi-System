// 城市地图参数设置

// 当页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 显示城市参数设置内容
    showCityParamsContent();
    
    // 注册事件监听器
    registerEventListeners();
    
    // 从服务器获取最新的城市地图参数
    loadCityMapParams();
});

// 显示城市参数设置内容
function showCityParamsContent() {
    document.getElementById('city-params-loading').style.display = 'none';
    document.getElementById('city-params-content').style.display = 'block';
}

// 注册相关事件监听器
function registerEventListeners() {
    // 刷新参数按钮
    const refreshBtn = document.getElementById('refreshCityParams');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            loadCityMapParams();
        });
    }
    
    // 保存中心点设置按钮
    const saveCentersBtn = document.getElementById('saveCityCentersBtn');
    if (saveCentersBtn) {
        saveCentersBtn.addEventListener('click', function() {
            saveCityCenters();
        });
    }
    
    // 保存缩放设置按钮
    const saveScaleBtn = document.getElementById('saveCityScaleBtn');
    if (saveScaleBtn) {
        saveScaleBtn.addEventListener('click', function() {
            saveCityScales();
        });
    }
}

// 从服务器加载最新的城市地图参数
function loadCityMapParams() {
    // 显示加载中提示
    showToast('正在加载城市地图参数...', 'info');
    
    // 向服务器发送请求获取最新参数
    fetch('/settings/api/city_map_params')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // 更新表单数据
                updateCityMapForms(data.data);
                showToast('城市地图参数加载成功', 'success');
            } else {
                showToast('加载城市地图参数失败: ' + data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('加载城市地图参数错误:', error);
            showToast('加载城市地图参数时发生错误: ' + error.message, 'danger');
            
            // 如果是首次加载时发生错误，则使用默认值
            // 这里采用的做法是不更新表单，保留HTML中的默认值
        });
}

// 更新城市地图表单数据
function updateCityMapForms(data) {
    // 更新中心点表单数据
    if (data.city_centers) {
        // 沈阳市
        if (data.city_centers['沈阳市']) {
            document.getElementById('syLng').value = data.city_centers['沈阳市'][0];
            document.getElementById('syLat').value = data.city_centers['沈阳市'][1];
        }
        // 北京市
        if (data.city_centers['北京市']) {
            document.getElementById('bjLng').value = data.city_centers['北京市'][0];
            document.getElementById('bjLat').value = data.city_centers['北京市'][1];
        }
        // 上海市
        if (data.city_centers['上海市']) {
            document.getElementById('shLng').value = data.city_centers['上海市'][0];
            document.getElementById('shLat').value = data.city_centers['上海市'][1];
        }
        // 广州市
        if (data.city_centers['广州市']) {
            document.getElementById('gzLng').value = data.city_centers['广州市'][0];
            document.getElementById('gzLat').value = data.city_centers['广州市'][1];
        }
        // 深圳市
        if (data.city_centers['深圳市']) {
            document.getElementById('szLng').value = data.city_centers['深圳市'][0];
            document.getElementById('szLat').value = data.city_centers['深圳市'][1];
        }
    }
    
    // 更新缩放比例表单数据
    if (data.city_scale_factors) {
        // 沈阳市
        if (data.city_scale_factors['沈阳市'] !== undefined) {
            document.getElementById('syScale').value = data.city_scale_factors['沈阳市'];
        }
        // 北京市
        if (data.city_scale_factors['北京市'] !== undefined) {
            document.getElementById('bjScale').value = data.city_scale_factors['北京市'];
        }
        // 上海市
        if (data.city_scale_factors['上海市'] !== undefined) {
            document.getElementById('shScale').value = data.city_scale_factors['上海市'];
        }
        // 广州市
        if (data.city_scale_factors['广州市'] !== undefined) {
            document.getElementById('gzScale').value = data.city_scale_factors['广州市'];
        }
        // 深圳市
        if (data.city_scale_factors['深圳市'] !== undefined) {
            document.getElementById('szScale').value = data.city_scale_factors['深圳市'];
        }
    }
    
    // 更新缩放级别表单数据
    if (data.city_zoom_levels) {
        // 沈阳市
        if (data.city_zoom_levels['沈阳市'] !== undefined) {
            document.getElementById('syZoom').value = data.city_zoom_levels['沈阳市'];
        }
        // 北京市
        if (data.city_zoom_levels['北京市'] !== undefined) {
            document.getElementById('bjZoom').value = data.city_zoom_levels['北京市'];
        }
        // 上海市
        if (data.city_zoom_levels['上海市'] !== undefined) {
            document.getElementById('shZoom').value = data.city_zoom_levels['上海市'];
        }
        // 广州市
        if (data.city_zoom_levels['广州市'] !== undefined) {
            document.getElementById('gzZoom').value = data.city_zoom_levels['广州市'];
        }
        // 深圳市
        if (data.city_zoom_levels['深圳市'] !== undefined) {
            document.getElementById('szZoom').value = data.city_zoom_levels['深圳市'];
        }
    }
}

// 保存城市中心点设置
function saveCityCenters() {
    // 构建数据
    const cityCenters = {
        '沈阳市': [
            parseFloat(document.getElementById('syLng').value),
            parseFloat(document.getElementById('syLat').value)
        ],
        '北京市': [
            parseFloat(document.getElementById('bjLng').value),
            parseFloat(document.getElementById('bjLat').value)
        ],
        '上海市': [
            parseFloat(document.getElementById('shLng').value),
            parseFloat(document.getElementById('shLat').value)
        ],
        '广州市': [
            parseFloat(document.getElementById('gzLng').value),
            parseFloat(document.getElementById('gzLat').value)
        ],
        '深圳市': [
            parseFloat(document.getElementById('szLng').value),
            parseFloat(document.getElementById('szLat').value)
        ]
    };
    
    // 向服务器发送请求保存设置
    fetch('/settings/api/save_city_centers', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            city_centers: cityCenters
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            showToast('城市中心点设置保存成功', 'success');
        } else {
            showToast('保存城市中心点设置失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('保存城市中心点设置错误:', error);
        showToast('保存城市中心点设置时发生错误: ' + error.message, 'danger');
    });
}

// 保存城市缩放比例设置
function saveCityScales() {
    // 构建数据
    const cityScaleFactors = {
        '沈阳市': parseFloat(document.getElementById('syScale').value),
        '北京市': parseFloat(document.getElementById('bjScale').value),
        '上海市': parseFloat(document.getElementById('shScale').value),
        '广州市': parseFloat(document.getElementById('gzScale').value),
        '深圳市': parseFloat(document.getElementById('szScale').value)
    };
    
    const cityZoomLevels = {
        '沈阳市': parseInt(document.getElementById('syZoom').value),
        '北京市': parseInt(document.getElementById('bjZoom').value),
        '上海市': parseInt(document.getElementById('shZoom').value),
        '广州市': parseInt(document.getElementById('gzZoom').value),
        '深圳市': parseInt(document.getElementById('szZoom').value)
    };
    
    // 向服务器发送请求保存设置
    fetch('/settings/api/save_city_scales', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            city_scale_factors: cityScaleFactors,
            city_zoom_levels: cityZoomLevels
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            showToast('城市缩放设置保存成功', 'success');
        } else {
            showToast('保存城市缩放设置失败: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('保存城市缩放设置错误:', error);
        showToast('保存城市缩放设置时发生错误: ' + error.message, 'danger');
    });
}

// 地图预览功能
function mapPreview(city) {
    let lng, lat;
    
    switch(city) {
        case '沈阳市':
            lng = parseFloat(document.getElementById('syLng').value);
            lat = parseFloat(document.getElementById('syLat').value);
            break;
        case '北京市':
            lng = parseFloat(document.getElementById('bjLng').value);
            lat = parseFloat(document.getElementById('bjLat').value);
            break;
        case '上海市':
            lng = parseFloat(document.getElementById('shLng').value);
            lat = parseFloat(document.getElementById('shLat').value);
            break;
        case '广州市':
            lng = parseFloat(document.getElementById('gzLng').value);
            lat = parseFloat(document.getElementById('gzLat').value);
            break;
        case '深圳市':
            lng = parseFloat(document.getElementById('szLng').value);
            lat = parseFloat(document.getElementById('szLat').value);
            break;
        default:
            showToast('未知的城市', 'danger');
            return;
    }
    
    // 打开新窗口预览地图
    const mapUrl = `https://uri.amap.com/marker?position=${lng},${lat}&name=${city}中心点&callnative=0`;
    window.open(mapUrl, '_blank');
}

// 显示通知消息
function showToast(message, type = 'info', duration = 3000) {
    // 检查是否已有toast容器
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1050';
        document.body.appendChild(toastContainer);
    }
    
    // 创建toast元素
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
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
    
    // 使用Bootstrap的toast初始化
    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: duration
    });
    
    // 显示toast
    toast.show();
    
    // 自动移除元素
    setTimeout(() => {
        toastEl.remove();
    }, duration + 500);
} 