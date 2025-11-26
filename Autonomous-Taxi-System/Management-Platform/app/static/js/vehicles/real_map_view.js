// 真实地图视图JavaScript文件
document.addEventListener('DOMContentLoaded', function() {
    // 城市中心点映射
    let cityCenters = {
        '沈阳市': [123.427171, 41.790598],  
        '北京市': [116.397428, 39.909190],
        '上海市': [121.458044, 31.190706],
        '广州市': [113.200637, 23.085178],
        '深圳市': [114.045947, 22.617],
        '杭州市': [120.260070, 30.270084], 
        '南京市': [118.806877, 32.050255],  
        '成都市': [104.065901, 30.657372],  
        '重庆市': [106.49724305, 29.53466598],  
        '武汉市': [114.31797981, 30.59307521], 
        '西安市': [108.94349813, 34.28514470]  
    };
    
    // 新增：每个城市的缩放比例配置
    let cityScaleFactors = {
        '沈阳市': 0.18,   // 修改：1000坐标单位=37.88公里 (37.88/111≈0.341度纬度变化)
        '北京市': 0.21,    // 北京更大，所以缩放范围更大
        '上海市': 0.37,    // 上海更集中，缩放范围更小
        '广州市': 0.11,    
        '深圳市': 0.10,    // 深圳更集中，范围更小
        '杭州市': 0.22,    // 新增：杭州市缩放比例
        '南京市': 0.21,    // 新增：南京市缩放比例
        '成都市': 0.12,    // 新增：成都市缩放比例
        '重庆市': 0.10,    // 新增：重庆市缩放比例（地形复杂，范围稍大）
        '武汉市': 0.23,    // 新增：武汉市缩放比例
        '西安市': 0.19     // 新增：西安市缩放比例
    };
    
    // 新增：每个城市的默认缩放级别
    let cityZoomLevels = {
        '沈阳市': 12,
        '北京市': 11,      // 北京更大，默认缩放级别更小以显示更多区域
        '上海市': 13,      // 上海更集中，缩放级别更大
        '广州市': 12,
        '深圳市': 13,      // 深圳更集中
        '杭州市': 12,      // 新增：杭州市缩放级别
        '南京市': 12,      // 新增：南京市缩放级别
        '成都市': 11,      // 新增：成都市缩放级别
        '重庆市': 11,      // 新增：重庆市缩放级别（地形复杂，显示更大区域）
        '武汉市': 12,      // 新增：武汉市缩放级别
        '西安市': 11      // 新增：西安市缩放级别
    };
    
    // 获取选择的城市 - 从localStorage读取上次选择的城市，如果没有则使用默认值
    const citySelector = document.getElementById('citySelector');
    const savedCity = localStorage.getItem('selectedCity');
    
    // 如果有保存的城市选择，则设置为该城市
    if (savedCity && citySelector.querySelector(`option[value="${savedCity}"]`)) {
        console.log(`从localStorage恢复上次选择的城市: ${savedCity}`);
        citySelector.value = savedCity;
    } else {
        console.log('没有找到保存的城市选择，使用默认值');
    }
    
    let selectedCity = citySelector.value;
    console.log('初始城市:', selectedCity);
    let centerCoords = cityCenters[selectedCity] || cityCenters['沈阳市'];
    
    // 自动刷新控制
    const autoRefreshCheckbox = document.getElementById('autoRefresh');
    const refreshIntervalSelect = document.getElementById('refreshInterval');
    
    // 从localStorage恢复自动刷新设置和间隔
    const savedAutoRefresh = localStorage.getItem('autoRefresh');
    if (savedAutoRefresh !== null) {
        console.log(`从localStorage恢复自动刷新设置: ${savedAutoRefresh}`);
        autoRefreshCheckbox.checked = savedAutoRefresh === 'true';
    }
    
    const savedRefreshInterval = localStorage.getItem('refreshInterval');
    if (savedRefreshInterval !== null && refreshIntervalSelect.querySelector(`option[value="${savedRefreshInterval}"]`)) {
        console.log(`从localStorage恢复刷新间隔: ${savedRefreshInterval}秒`);
        refreshIntervalSelect.value = savedRefreshInterval;
    }
    
    let autoRefreshInterval = null;
    
    // 从服务器加载最新的城市地图配置
    let mapInitialized = false;
    let map = null;
    
    // 加载城市地图配置
    loadCityMapConfig();
    
    // 从服务器加载城市地图配置
    function loadCityMapConfig() {
        console.log('加载城市地图配置...');
        
        // 显示加载提示
        showLoadingOverlay('正在加载地图配置...');
        
        // 发送请求获取城市地图配置
        fetch('/settings/api/city_map_params')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    // 更新配置
                    if (data.data.city_centers) {
                        cityCenters = data.data.city_centers;
                        console.log('加载城市中心点配置:', cityCenters);
                    }
                    
                    if (data.data.city_scale_factors) {
                        cityScaleFactors = data.data.city_scale_factors;
                        console.log('加载城市缩放比例配置:', cityScaleFactors);
                    }
                    
                    if (data.data.city_zoom_levels) {
                        cityZoomLevels = data.data.city_zoom_levels;
                        console.log('加载城市缩放级别配置:', cityZoomLevels);
                    }
                    
                    // 更新中心坐标
                    centerCoords = cityCenters[selectedCity] || cityCenters['沈阳市'];
                    console.log('更新后的中心坐标:', centerCoords);
                    
                    // 初始化地图
                    initializeMap();
                } else {
                    console.error('加载城市地图配置失败:', data.message);
                    // 初始化地图（使用默认配置）
                    initializeMap();
                }
            })
            .catch(error => {
                console.error('加载城市地图配置错误:', error);
                // 初始化地图（使用默认配置）
                initializeMap();
            })
            .finally(() => {
                hideLoadingOverlay();
            });
    }
    
    // 显示加载覆盖层
    function showLoadingOverlay(message = '加载中...') {
        // 创建或获取覆盖层
        let overlay = document.getElementById('loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.style.cssText = `
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(255, 255, 255, 0.8);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                z-index: 1000;
            `;
            
            const spinnerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2" id="loading-message">${message}</p>
            `;
            
            overlay.innerHTML = spinnerHTML;
            
            // 添加到地图容器
            const mapContainer = document.getElementById('map-container');
            mapContainer.style.position = 'relative';
            mapContainer.appendChild(overlay);
        } else {
            // 更新消息
            const loadingMessage = document.getElementById('loading-message');
            if (loadingMessage) {
                loadingMessage.textContent = message;
            }
            
            // 显示覆盖层
            overlay.style.display = 'flex';
        }
    }
    
    // 隐藏加载覆盖层
    function hideLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
    
    // 初始化地图
    function initializeMap() {
        if (mapInitialized) {
            console.log('地图已初始化，跳过');
            return;
        }
        
        console.log('初始化地图，中心点:', centerCoords, '缩放级别:', cityZoomLevels[selectedCity] || 12);
        
        // 初始化地图，使用城市特定的缩放级别
        map = new AMap.Map('map-container', {
            zoom: cityZoomLevels[selectedCity] || 12,
            center: centerCoords,
            resizeEnable: true,
            defaultLayer: new AMap.TileLayer(),  // 确保使用标准图层
            viewMode: '2D'  // 使用2D模式可能更容易显示标记
        });
        
        // 在地图初始化后检查是否加载成功
        map.on('complete', function() {
            console.log('地图加载完成');
            
            // 调整地图视图以确保标记可见
            setTimeout(() => {
                console.log('触发地图刷新');
                map.setZoom(map.getZoom() - 0.1);
                setTimeout(() => {
                    map.setZoom(map.getZoom() + 0.1);
                    
                    // 加载初始城市数据
                    loadCityData(selectedCity);
                    
                    // 启动自动刷新（如果已勾选）
                    if (autoRefreshCheckbox.checked) {
                        startAutoRefresh();
                    }
                }, 100);
            }, 200);
        });
        
        // 添加地图控件 - 使用正确的方式添加控件
        map.plugin(['AMap.Scale', 'AMap.ToolBar'], function() {
            // 添加比例尺控件
            const scale = new AMap.Scale({
                position: 'LB'
            });
            map.addControl(scale);
            
            // 添加工具条控件
            const toolBar = new AMap.ToolBar({
                position: 'RB'
            });
            map.addControl(toolBar);
        });
        
        // 标记地图已初始化
        mapInitialized = true;
        
        // 注册事件监听器
        registerEventListeners();
    }
    
    // 车辆标记和充电站标记数组
    let vehicleMarkers = {};  // 改为对象以便通过ID查找
    let chargingStationMarkers = {};  // 改为对象以便通过ID查找
    
    // 注册事件监听器
    function registerEventListeners() {
        // 城市选择器变更事件
        citySelector.addEventListener('change', function() {
            selectedCity = this.value;
            console.log('选择城市:', selectedCity);
            
            // 保存选择的城市到localStorage
            localStorage.setItem('selectedCity', selectedCity);
            console.log(`已保存城市选择到localStorage: ${selectedCity}`);
            
            centerCoords = cityCenters[selectedCity] || cityCenters['沈阳市'];
            console.log('中心坐标:', centerCoords);
            
            // 更新地图中心点和缩放级别
            map.setCenter(centerCoords);
            map.setZoom(cityZoomLevels[selectedCity] || 12);
            
            // 清除现有标记
            clearMarkers();
            
            // 加载新城市的数据
            loadCityData(selectedCity);
            
            showToast(`已切换到${selectedCity}地图`, 'success');
        });
        
        // 自动刷新控制
        autoRefreshCheckbox.addEventListener('change', function() {
            // 保存自动刷新设置到localStorage
            localStorage.setItem('autoRefresh', this.checked);
            
            if (this.checked) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        });
        
        // 刷新间隔变更
        refreshIntervalSelect.addEventListener('change', function() {
            // 保存刷新间隔到localStorage
            localStorage.setItem('refreshInterval', this.value);
            
            if (autoRefreshCheckbox.checked) {
                // 重启自动刷新以应用新间隔
                stopAutoRefresh();
                startAutoRefresh();
            }
        });
        
        // 刷新按钮点击事件
        document.getElementById('refreshMapBtn').addEventListener('click', function() {
            // 使用智能刷新方法替代原来的方法
            smartRefresh(selectedCity);
            showToast('地图已刷新', 'success');
        });
        
        // 显示/隐藏车辆开关
        document.getElementById('showVehicles').addEventListener('change', function() {
            const isShowVehicles = this.checked;
            
            Object.values(vehicleMarkers).forEach(marker => {
                if (isShowVehicles) {
                    marker.show();
                } else {
                    marker.hide();
                }
            });
            
            showToast(isShowVehicles ? '已显示车辆' : '已隐藏车辆', 'info');
        });
        
        // 显示/隐藏充电站开关
        document.getElementById('showChargingStations').addEventListener('change', function() {
            const isShowStations = this.checked;
            
            Object.values(chargingStationMarkers).forEach(marker => {
                if (isShowStations) {
                    marker.show();
                } else {
                    marker.hide();
                }
            });
            
            showToast(isShowStations ? '已显示充电站' : '已隐藏充电站', 'info');
        });
    }
    
    // 开始自动刷新
    function startAutoRefresh() {
        stopAutoRefresh(); // 先停止现有的刷新
        
        const interval = parseInt(refreshIntervalSelect.value) * 1000; // 转换为毫秒
        autoRefreshInterval = setInterval(function() {
            // 使用智能刷新方法
            smartRefresh(selectedCity);
            
            // 记录刷新时间
            const refreshTime = new Date().toLocaleTimeString();
            console.log(`自动刷新完成，时间: ${refreshTime}`);
        }, interval);
        
        showToast(`自动刷新已启动，间隔${refreshIntervalSelect.value}秒`, 'info');
    }
    
    // 智能刷新 - 尽量保留现有标记并平滑更新位置
    function smartRefresh(city) {
        console.log(`智能刷新${city}的数据...`);
        
        // 记录更新时间
        const updateTime = new Date().toLocaleTimeString();
        
        // 加载车辆数据
        fetch(`/vehicles/api/city_vehicles?city=${city}`)
            .then(response => {
                // 检查响应状态码
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}, URL: /vehicles/api/city_vehicles?city=${city}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('车辆数据API返回:', data);  // 记录原始返回数据以排查问题
                
                if (data.status === 'success') {
                    let updatedCount = 0;
                    let newCount = 0;
                    let removedCount = 0;
                    
                    // 记录数据中的车辆ID
                    const vehicleIds = new Set(data.data.map(v => v.vehicle_id));
                    
                    // 1. 先移除不再存在的车辆标记
                    Object.keys(vehicleMarkers).forEach(id => {
                        if (!vehicleIds.has(parseInt(id))) {
                            // 创建标记消失的动画效果
                            const marker = vehicleMarkers[id];
                            
                            // 直接移除标记，避免动画过程中的错误
                            map.remove(marker);
                            delete vehicleMarkers[id];
                            removedCount++;
                        }
                    });

                    // 2. 处理现有车辆和新增车辆
                    data.data.forEach(vehicle => {
                        try {
                            const vehicleId = vehicle.vehicle_id;
                            
                            if (vehicleMarkers[vehicleId]) {
                                // 更新现有标记
                                updateVehicleMarker(vehicleMarkers[vehicleId], vehicle, city);
                                updatedCount++;
                            } else {
                                // 创建新标记
                                const marker = addVehicleMarker(vehicle, city);
                                if (marker) {
                                    newCount++;
                                }
                            }
                        } catch (err) {
                            console.error('处理车辆数据时出错:', err, vehicle);
                        }
                    });

                    // 加载充电站数据（只在首次加载时执行或充电站为空时）
                    if (Object.keys(chargingStationMarkers).length === 0) {
                        loadChargingStations(city);
                    }
                    
                    console.log(`智能刷新完成: 更新 ${updatedCount} 辆车, 新增 ${newCount} 辆车, 移除 ${removedCount} 辆车`);
                    
                    // 如果有变化，显示toast通知
                    if (updatedCount > 0 || newCount > 0 || removedCount > 0) {
                    }
                } else {
                    console.error('更新车辆数据失败:', data.message);
                    showToast('更新车辆数据失败: ' + (data.message || '未知错误'), 'danger');
                }
            })
            .catch(error => {
                console.error('车辆API错误详情:', error);
                showToast('刷新数据时发生错误: ' + error.message, 'danger');
            });
    }
    
    // 加载充电站数据的函数，单独提取以便重用
    function loadChargingStations(city) {
        fetch(`/vehicles/api/city_charging_stations?city=${city}`)
            .then(response => {
                // 检查响应状态码
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}, URL: /vehicles/api/city_charging_stations?city=${city}`);
                }
                return response.json();
            })
            .then(stationData => {
                console.log('充电站数据API返回:', stationData);  // 记录原始返回数据
                
                if (stationData.status === 'success') {
                    console.log(`获取到${stationData.data.length}个充电站数据`);
                    // 添加充电站标记
                    stationData.data.forEach(station => {
                        try {
                            addChargingStationMarker(station, city);
                        } catch (err) {
                            console.error('添加充电站标记时出错:', err, station);
                        }
                    });
                } else {
                    console.error('加载充电站数据失败:', stationData.message);
                    showToast('加载充电站数据失败: ' + (stationData.message || '未知错误'), 'warning');
                }
            })
            .catch(error => {
                console.error('充电站API错误详情:', error);
                showToast('加载充电站数据时发生错误: ' + error.message, 'warning');
            });
    }
    
    // 加载城市数据
    function loadCityData(city) {
        console.log(`开始加载${city}的数据`);
        
        // 加载车辆数据
        fetch(`/vehicles/api/city_vehicles?city=${city}`)
            .then(response => {
                // 检查响应状态码
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}, URL: /vehicles/api/city_vehicles?city=${city}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('车辆数据API返回:', data);  // 记录原始返回数据
                
                if (data.status === 'success') {
                    console.log(`获取到${data.data.length}辆车数据:`, data.data);
                    // 添加车辆标记
                    data.data.forEach(vehicle => {
                        try {
                            addVehicleMarker(vehicle, city);
                        } catch (err) {
                            console.error('添加车辆标记时出错:', err, vehicle);
                        }
                    });
                    console.log(`已加载 ${data.data.length} 辆车的数据`);
                } else {
                    showToast('加载车辆数据失败: ' + (data.message || '未知错误'), 'danger');
                    console.error('加载车辆数据失败:', data.message);
                }
            })
            .catch(error => {
                console.error('API错误详情:', error);
                showToast('加载车辆数据时发生错误: ' + error.message, 'danger');
            });
        
        // 加载充电站数据
        loadChargingStations(city);
    }
    
    // 停止自动刷新
    function stopAutoRefresh() {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
            showToast('自动刷新已停止', 'info');
        }
    }
    
    // 更新车辆数据而不重新创建所有标记
    function updateVehiclesData(city) {
        console.log(`更新${city}的车辆数据...`);
        
        // 获取当前时间，用于显示最后更新时间
        const updateTime = new Date().toLocaleTimeString();
        
        // 加载车辆数据
        fetch(`/vehicles/api/city_vehicles?city=${city}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    let positionChangedCount = 0;
                    let statusChangedCount = 0;
                    
                    // 处理每个车辆数据
                    data.data.forEach(vehicle => {
                        const vehicleId = vehicle.vehicle_id;
                        
                        if (vehicleMarkers[vehicleId]) {
                            // 获取旧数据
                            const oldData = vehicleMarkers[vehicleId].getExtData().vehicleData;
                            
                            // 检查位置或状态是否变化
                            if (oldData.current_location_x !== vehicle.current_location_x || 
                                oldData.current_location_y !== vehicle.current_location_y) {
                                positionChangedCount++;
                            }
                            
                            if (oldData.current_status !== vehicle.current_status) {
                                statusChangedCount++;
                            }
                            
                            // 更新现有标记
                            updateVehicleMarker(vehicleMarkers[vehicleId], vehicle, city);
                        } else {
                            // 创建新标记
                            addVehicleMarker(vehicle, city);
                        }
                    });
                    
                    // 检查并移除不再存在的车辆标记
                    Object.keys(vehicleMarkers).forEach(id => {
                        const exists = data.data.some(v => v.vehicle_id == id);
                        if (!exists) {
                            // 移除不再存在的车辆标记
                            map.remove(vehicleMarkers[id]);
                            delete vehicleMarkers[id];
                        }
                    });
                    
                    console.log(`已更新 ${data.data.length} 辆车的数据，其中 ${positionChangedCount} 辆位置变化，${statusChangedCount} 辆状态变化`);
                    
                    // 如果有变化，显示toast通知
                    if (positionChangedCount > 0 || statusChangedCount > 0) {
                    }
                } else {
                    console.error('更新车辆数据失败:', data.message);
                }
            })
            .catch(error => {
                console.error('车辆API错误:', error);
            });
    }
    
    // 清除所有标记
    function clearMarkers() {
        // 清除车辆标记
        Object.values(vehicleMarkers).forEach(marker => {
            map.remove(marker);
        });
        vehicleMarkers = {};
        
        // 清除充电站标记
        Object.values(chargingStationMarkers).forEach(marker => {
            map.remove(marker);
        });
        chargingStationMarkers = {};
    }
    
    // 将模拟坐标转换为真实经纬度坐标
    function convertCoordinates(x, y, city) {
        // 这里根据实际情况计算，将1000x1000的虚拟坐标映射到各城市的实际经纬度
        console.log(`转换坐标: x=${x}, y=${y}, city=${city}`);
        
        // 确保坐标是数字
        x = parseFloat(x) || 0;
        y = parseFloat(y) || 0;
        
        // 获取城市中心点
        const center = cityCenters[city] || cityCenters['沈阳市'];
        
        // 获取城市特定的缩放比例
        // 每个城市使用不同的缩放比例，以适应各自的地理范围
        // 例如：沈阳市缩放比例0.341表示1000个坐标单位映射到约37.88公里
        // 其他城市根据自身规模和地理特点设置不同的缩放比例
        const scaleFactor = cityScaleFactors[city] || 0.2; // 默认使用0.2作为缩放因子
        
        // 计算偏移量，使用城市特定的缩放比例
        const lonOffset = ((x - 500) / 500) * scaleFactor;  // 使用城市特定的缩放比例
        const latOffset = ((500 - y) / 500) * scaleFactor;  // 使用城市特定的缩放比例，y坐标倒转，因为地图上方是北方
        
        const result = [center[0] + lonOffset, center[1] + latOffset];
        console.log(`转换结果: [${result[0]}, ${result[1]}]`);
        
        return result;
    }
    
    // 更新现有车辆标记
    function updateVehicleMarker(marker, vehicle, city) {
        if (vehicle.current_location_x === undefined || vehicle.current_location_y === undefined) {
            console.warn('车辆缺少位置信息:', vehicle);
            return null;
        }
        
        // 获取旧位置数据（用于对比是否有变化）
        const oldVehicleData = marker.getExtData().vehicleData;
        const positionChanged = 
            oldVehicleData.current_location_x !== vehicle.current_location_x || 
            oldVehicleData.current_location_y !== vehicle.current_location_y;
        
        // 获取新坐标
        const coords = convertCoordinates(vehicle.current_location_x, vehicle.current_location_y, city);
        
        // 更新位置 - 使用平滑移动效果
        if (positionChanged) {
            console.log(`车辆 ${vehicle.vehicle_id} (${vehicle.plate_number}) 位置已更新:`, 
                `从 (${oldVehicleData.current_location_x}, ${oldVehicleData.current_location_y}) 到 ` +
                `(${vehicle.current_location_x}, ${vehicle.current_location_y})`);
            
            try {
                // 使用平滑移动动画，如果位置有变化的话显示更明显的动画
                const oldCoords = convertCoordinates(oldVehicleData.current_location_x, oldVehicleData.current_location_y, city);
                
                // 使用路径规划来移动车辆，而不是直线移动
                planRouteForVehicle(marker, oldCoords, coords, vehicle);
            } catch (e) {
                console.warn('路径规划失败，使用直接设置位置:', e);
                marker.setPosition(coords);
            }
        } else {
            // 没有位置变化时，只更新位置但不使用动画
            marker.setPosition(coords);
        }
        
        // 状态是否变化
        const statusChanged = oldVehicleData.current_status !== vehicle.current_status;
        if (statusChanged) {
            console.log(`车辆 ${vehicle.vehicle_id} (${vehicle.plate_number}) 状态已更新: 从 ${oldVehicleData.current_status} 到 ${vehicle.current_status}`);
        }
        
        // 更新颜色 - 根据车辆状态
        let color = '#28a745'; // 默认绿色（空闲）
        switch (vehicle.current_status) {
            case '运行中':
                color = '#007bff'; // 蓝色
                break;
            case '充电中':
                color = '#17a2b8'; // 青色
                break;
            case '电量不足':
                color = '#6c757d'; // 灰色
                break;
            case '等待充电':
                color = '#dc3545'; // 红色
                break;
            case '前往充电':
                color = '#6f42c1'; // 紫色
                break;
            case '维护中':
                color = '#ffc107'; // 黄色
                break;
        }
        
        // 更新标记样式 - 使用DOM内容方式
        marker.setContent(`<div style="background-color:${color}; width:20px; height:20px; border-radius:50%; border:2px solid white; box-shadow:0 0 5px rgba(0,0,0,0.5);"></div>`);
        
        // 更新标题
        marker.setTitle(`${vehicle.plate_number} - ${vehicle.current_status}`);
        
        // 更新数据属性
        marker.setExtData({
            ...marker.getExtData(),
            vehicleData: vehicle,
            lastUpdated: new Date()
        });
        
        return marker;
    }
    
    // 为车辆规划路径并沿路线移动
    function planRouteForVehicle(marker, startCoords, endCoords, vehicle) {
        // 存储规划中的标记和路线，以便后续清理
        if (!window.planningRoutes) {
            window.planningRoutes = {};
        }
        
        const vehicleId = vehicle.vehicle_id;
        
        // 如果该车辆已有规划中的路线，先清除
        if (window.planningRoutes[vehicleId]) {
            try {
                // 停止之前的动画
                if (window.planningRoutes[vehicleId].moveAnimation) {
                    window.planningRoutes[vehicleId].moveAnimation.stop();
                }
            } catch (e) {
                console.warn('清除旧路线失败:', e);
            }
        }
        
        // 创建路线规划实例
        const driving = new AMap.Driving({
            map: map,
            hideMarkers: true,  // 隐藏原始标记点
            autoFitView: false  // 不自动调整视图
        });
        
        // 规划路线
        driving.search(startCoords, endCoords, function(status, result) {
            if (status === 'complete' && result.routes && result.routes.length > 0) {
                // 获取路线点
                const path = result.routes[0].steps.map(step => step.path).flat();
                
                // 如果路径太短，或者只有起点终点两个点，使用直线过渡
                if (path.length <= 2) {
                    console.log('规划路径过短，使用直线过渡');
                    useLinearPath(marker, startCoords, endCoords);
                    return;
                }
                
                console.log(`为车辆 ${vehicleId} 规划了 ${path.length} 个路径点的行驶路线`);
                
                // 计算合适的动画时间，基于路径长度
                const totalDistance = calculatePathDistance(path);
                const speed = 50;  // 像素/秒
                const duration = Math.max(2000, Math.min(10000, totalDistance * 30));
                
                // 沿路线移动标记
                const moveAnimation = marker.moveAlong(path, {
                    duration: duration,         // 移动总时长
                    autoRotation: false,        // 不自动旋转
                    circlable: false           // 不循环移动
                });
                
                // 保存动画引用，以便后续清理
                window.planningRoutes[vehicleId] = {
                    moveAnimation: moveAnimation
                };
                
                // 添加监听器，移动结束后清理
                moveAnimation.on('stop', () => {
                    setTimeout(() => {
                        try {
                            // 清除引用
                            delete window.planningRoutes[vehicleId];
                        } catch (e) {
                            console.warn('清除路线失败:', e);
                        }
                    }, 1000);
                });
                
                // 开始动画
                moveAnimation.start();
            } else {
                console.warn('路径规划失败，使用线性路径:', status, result);
                useLinearPath(marker, startCoords, endCoords);
            }
        });
    }
    
    // 使用线性路径作为备选
    function useLinearPath(marker, startCoords, endCoords) {
        // 自定义动画实现平滑移动
        const startTime = Date.now();
        const duration = 2000; // 2秒
        const animate = () => {
            const now = Date.now();
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // 线性插值计算当前位置
            const lng = startCoords[0] + (endCoords[0] - startCoords[0]) * progress;
            const lat = startCoords[1] + (endCoords[1] - startCoords[1]) * progress;
            
            marker.setPosition([lng, lat]);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        animate();
    }
    
    // 计算路径总长度
    function calculatePathDistance(path) {
        let distance = 0;
        for (let i = 1; i < path.length; i++) {
            distance += AMap.GeometryUtil.distance(path[i-1], path[i]);
        }
        return distance;
    }
    
    // 添加车辆标记
    function addVehicleMarker(vehicle, city) {
        if (vehicle.current_location_x === undefined || vehicle.current_location_y === undefined) {
            console.warn('车辆缺少位置信息:', vehicle);
            return null;
        }
        
        // 将模拟坐标转换为实际经纬度
        const coords = convertCoordinates(vehicle.current_location_x, vehicle.current_location_y, city);
        
        // 根据车辆状态确定标记颜色
        let color = '#28a745'; // 默认绿色（空闲）
        switch (vehicle.current_status) {
            case '运行中':
                color = '#007bff'; // 蓝色
                break;
            case '充电中':
                color = '#17a2b8'; // 青色
                break;
            case '电量不足':
                color = '#6c757d'; // 灰色
                break;
            case '等待充电':
                color = '#dc3545'; // 红色
                break;
            case '前往充电':
                color = '#6f42c1'; // 紫色
                break;
            case '维护中':
                color = '#ffc107'; // 黄色
                break;
        }
        
        // 创建标记 - 使用HTML内容而不是图标，以确保可见性
        const marker = new AMap.Marker({
            position: coords,
            title: `${vehicle.plate_number} - ${vehicle.current_status}`,
            content: `<div style="background-color:${color}; width:20px; height:20px; border-radius:50%; border:2px solid white; box-shadow:0 0 5px rgba(0,0,0,0.5);"></div>`,
            offset: new AMap.Pixel(-10, -10),
            extData: {
                vehicleData: vehicle,
                lastUpdated: new Date()
            },
            zIndex: 200  // 设置非常高的z-index，确保显示在最上层
        });
        
        // 添加点击事件
        marker.on('click', function() {
            // 获取最新数据
            const vehicleData = marker.getExtData().vehicleData;
            
            // 显示车辆信息窗口
            const infoWindow = new AMap.InfoWindow({
                content: `
                    <div style="padding: 10px;">
                        <h5>${vehicleData.plate_number}</h5>
                        <p>状态: ${vehicleData.current_status}</p>
                        <p>电量: ${vehicleData.battery_level}%</p>
                        <p>型号: ${vehicleData.model || '未知'}</p>
                        <p><small>最后更新: ${new Date(marker.getExtData().lastUpdated).toLocaleTimeString()}</small></p>
                    </div>
                `,
                offset: new AMap.Pixel(0, -30)
            });
            
            infoWindow.open(map, marker.getPosition());
        });
        
        // 添加到地图
        marker.setMap(map);
        console.log(`已添加车辆标记: ${vehicle.plate_number}，位置: ${coords}`);
        
        // 保存到标记数组
        vehicleMarkers[vehicle.vehicle_id] = marker;
        
        return marker;
    }
    
    // 添加充电站标记
    function addChargingStationMarker(station, city) {
        if (station.location_x === undefined || station.location_y === undefined) {
            console.warn('充电站缺少位置信息:', station);
            return null;
        }
        
        // 将模拟坐标转换为实际经纬度
        const coords = convertCoordinates(station.location_x, station.location_y, city);
        
        // 车辆标记尺寸
        const vehicleSize = 20;
        // 充电站尺寸为车辆的1.5倍
        const stationSize = Math.round(vehicleSize * 1.5);
        
        // 创建标记 - 使用更醒目的样式
        const marker = new AMap.Marker({
            position: coords,
            title: `充电站: ${station.station_code}`,
            content: `<div style="background-color:#17a2b8; width:${stationSize}px; height:${stationSize}px; border-radius:50%; display:flex; justify-content:center; align-items:center; color:white; font-weight:bold; font-size:${stationSize/2}px; box-shadow:0 0 8px rgba(0,0,0,0.8);">⚡</div>`,
            offset: new AMap.Pixel(-stationSize/2, -stationSize/2),
            extData: {
                stationData: station
            },
            zIndex: 180  // 设置较高的z-index，但低于车辆
        });
        
        // 点击事件
        marker.on('click', function() {
            // 获取最新数据
            const stationData = marker.getExtData().stationData;
            
            // 显示充电站信息窗口
            const infoWindow = new AMap.InfoWindow({
                content: `
                    <div style="padding: 10px;">
                        <h5>充电站: ${stationData.station_code}</h5>
                        <p>当前充电车辆: ${stationData.current_vehicles}/${stationData.max_capacity}</p>
                        <p>上次维护: ${stationData.last_maintenance_date || '暂无记录'}</p>
                    </div>
                `,
                offset: new AMap.Pixel(0, -30)
            });
            
            infoWindow.open(map, marker.getPosition());
        });
        
        // 添加到地图
        marker.setMap(map);
        console.log(`已添加充电站标记: ${station.station_code}，位置: ${coords}`);
        
        // 保存到标记数组
        chargingStationMarkers[station.station_id] = marker;
        
        return marker;
    }
    
    // 显示通知消息
    function showToast(message, type = 'info', duration = 3000) {
        // 检查是否已有toast容器
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
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
    
    // 路线规划演示
    window.planRoute = function(startX, startY, endX, endY) {
        // 将模拟坐标转换为经纬度
        const startCoords = convertCoordinates(startX, startY, selectedCity);
        const endCoords = convertCoordinates(endX, endY, selectedCity);
        
        // 创建路线规划实例
        const driving = new AMap.Driving({
            map: map,
            panel: "panel", // 可选，路线详情面板
            policy: AMap.DrivingPolicy.LEAST_TIME // 最短时间
        });
        
        // 规划路线
        driving.search(
            startCoords, 
            endCoords, 
            function(status, result) {
                if (status === 'complete') {
                    showToast('路线规划成功', 'success');
                    console.log('路线规划结果:', result);
                    
                    // 创建沿路线移动的车辆标记
                    const vehicleMarker = new AMap.Marker({
                        map: map,
                        position: startCoords,
                        icon: new AMap.Icon({
                            size: new AMap.Size(20, 20),
                            image: 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(`
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20">
                                    <circle cx="10" cy="10" r="8" fill="#007bff" stroke="white" stroke-width="2"/>
                                </svg>
                            `),
                            imageSize: new AMap.Size(20, 20)
                        })
                    });
                    
                    // 获取路线点
                    const path = result.routes[0].steps.map(step => step.path).flat();
                    
                    // 沿路线移动
                    vehicleMarker.moveAlong(path, 100);
                } else {
                    showToast('路线规划失败', 'danger');
                }
            }
        );
    };
    
    // 将函数暴露到全局，方便控制台测试路径规划
    window.testPathPlanning = function() {
        // 测试路径规划
        planRoute(200, 300, 800, 700);
    };
});

