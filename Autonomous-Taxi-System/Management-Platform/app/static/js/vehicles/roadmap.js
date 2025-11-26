// roadmap.js - 城市道路地图数据和工具函数

/**
 * 生成沈阳市路网地图
 * 0 - 不可通行区域
 * 1 - 道路
 * 2 - 地标/充电站
 * @returns {Array} 1000x1000的路网二维数组
 */
function generateShenyangRoadMap() {
    // 初始化1000x1000的地图，全部设为0（不可通行）
    const roadMap = Array(1000).fill().map(() => Array(1000).fill(0));
    
    // 抛弃路网，返回空白地图
    return roadMap;
}

/**
 * 生成北京市路网地图
 * @returns {Array} 1000x1000的路网二维数组
 */
function generateBeijingRoadMap() {
    // 初始化1000x1000的地图，全部设为0（不可通行）
    const roadMap = Array(1000).fill().map(() => Array(1000).fill(0));
    
    // 抛弃路网，返回空白地图
    return roadMap;
}

/**
 * 生成上海市路网地图
 * @returns {Array} 1000x1000的路网二维数组
 */
function generateShanghaiRoadMap() {
    // 初始化1000x1000的地图，全部设为0（不可通行）
    const roadMap = Array(1000).fill().map(() => Array(1000).fill(0));
    
    // 抛弃路网，返回空白地图
    return roadMap;
}

/**
 * 添加地标和充电站
 * @param {Array} roadMap 道路地图数组
 * @param {string} cityCode 城市代码
 */
function addLandmarks(roadMap, cityCode) {
    // 从landmarks.js文件中获取指定城市的地标数据
    const cityLandmarksData = cityLandmarks[cityCode] || [];
    
    // 将地标位置设为2（地标/充电站）
    cityLandmarksData.forEach(landmark => {
        const x = landmark.x;
        const y = landmark.y;
        
        if (x >= 0 && x < 1000 && y >= 0 && y < 1000) {
            // 为地标创建一个小区域
            for (let dx = -2; dx <= 2; dx++) {
                for (let dy = -2; dy <= 2; dy++) {
                    const nx = x + dx;
                    const ny = y + dy;
                    if (nx >= 0 && nx < 1000 && ny >= 0 && ny < 1000) {
                        roadMap[ny][nx] = 2;
                    }
                }
            }
        }
    });
    
    // 添加一些额外的充电站
    // 每个城市都有10个默认充电站位置
    const defaultChargingStations = [
        { x: 450, y: 450 },
        { x: 550, y: 550 },
        { x: 450, y: 550 },
        { x: 550, y: 450 },
        { x: 600, y: 500 },
        { x: 400, y: 500 },
        { x: 500, y: 600 },
        { x: 500, y: 400 },
        { x: 350, y: 350 },
        { x: 650, y: 650 }
    ];
    
    defaultChargingStations.forEach(station => {
        const x = station.x;
        const y = station.y;
        
        if (x >= 0 && x < 1000 && y >= 0 && y < 1000) {
            // 为充电站创建一个小区域
            for (let dx = -2; dx <= 2; dx++) {
                for (let dy = -2; dy <= 2; dy++) {
                    const nx = x + dx;
                    const ny = y + dy;
                    if (nx >= 0 && nx < 1000 && ny >= 0 && ny < 1000) {
                        roadMap[ny][nx] = 2;
                    }
                }
            }
        }
    });
}

/**
 * 将道路地图绘制到网格上
 * @param {HTMLElement} gridElement 地图网格DOM元素
 * @param {Array} roadMap 道路地图数组
 */
function drawRoadMapToGrid(gridElement, roadMap) {
    // 不需要绘制所有像素，可以降低密度提高性能
    const resolution = 2; // 每2个像素绘制一个点
    
    // 创建一个文档片段，减少DOM操作次数，提高性能
    const fragment = document.createDocumentFragment();
    
    for (let y = 0; y < 1000; y += resolution) {
        for (let x = 0; x < 1000; x += resolution) {
            // 不再绘制道路点 (value === 1)
            if (roadMap[y][x] === 2) { // 只保留地标/充电站
                const landmarkCell = document.createElement('div');
                landmarkCell.className = 'landmark-cell';
                landmarkCell.style.left = `${x}px`;
                landmarkCell.style.top = `${y}px`;
                landmarkCell.style.width = `${resolution}px`;
                landmarkCell.style.height = `${resolution}px`;
                fragment.appendChild(landmarkCell);
            }
        }
    }
    
    gridElement.appendChild(fragment);
}

/**
 * 判断指定位置是否可通行（默认所有位置均可通行）
 * @param {number} x X坐标
 * @param {number} y Y坐标
 * @returns {boolean} 是否可通行
 */
function isValidPosition(x, y) {
    // 地图边界检查
    if (x < 0 || x >= 1000 || y < 0 || y >= 1000) {
        return false;
    }
    
    // 所有位置均可通行
    return true;
}

/**
 * 找到最近的道路点（不再需要，直接返回原始坐标）
 * @param {number} x X坐标
 * @param {number} y Y坐标
 * @param {number} searchRadius 搜索半径
 * @returns {object|null} 最近道路点坐标或null
 */
function findNearestRoadPoint(x, y, searchRadius) {
    // 直接返回原始坐标
    return { x, y };
} 