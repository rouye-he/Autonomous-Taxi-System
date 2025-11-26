// 坐标转换工具 #从后端API动态获取城市参数
let CITY_CENTERS = {}; // 动态从后端获取
let CITY_SCALE_FACTORS = {}; // 动态从后端获取
let isInitialized = false; // 是否已初始化

/**
 * 从后端API获取城市参数配置
 * @returns {Promise<boolean>} 是否获取成功
 */
async function loadCityParameters() {
  if (isInitialized) return true; // 已初始化，直接返回
  
  try {
    console.log('开始从后端API获取城市参数...');
    
    // 获取城市中心点坐标
    const centersResponse = await new Promise((resolve, reject) => {
      wx.request({
        url: 'http://localhost:5001/api/system/city-centers',
        method: 'GET',
        success: resolve,
        fail: reject
      });
    });
    
    if (centersResponse.statusCode === 200 && centersResponse.data.code === 0) {
      CITY_CENTERS = centersResponse.data.data;
      console.log('成功获取城市中心点坐标:', Object.keys(CITY_CENTERS).length, '个城市');
    } else {
      throw new Error('获取城市中心点坐标失败');
    }
    
    // 获取城市缩放因子
    const scaleResponse = await new Promise((resolve, reject) => {
      wx.request({
        url: 'http://localhost:5001/api/system/city-scale-factors',
        method: 'GET',
        success: resolve,
        fail: reject
      });
    });
    
    if (scaleResponse.statusCode === 200 && scaleResponse.data.code === 0) {
      CITY_SCALE_FACTORS = scaleResponse.data.data;
      console.log('成功获取城市缩放因子:', Object.keys(CITY_SCALE_FACTORS).length, '个城市');
    } else {
      throw new Error('获取城市缩放因子失败');
    }
    
    isInitialized = true;
    console.log('城市参数初始化完成');
    return true;
    
  } catch (error) {
    console.error('获取城市参数失败:', error);
    return false;
  }
}

/**
 * 将系统内部坐标(0-999整数)转换为经纬度
 * @param {number} x - X坐标 (0-999)
 * @param {number} y - Y坐标 (0-999)
 * @param {string} city - 城市代码(中文)
 * @returns {Promise<object>} 包含longitude和latitude的对象
 */
async function systemToGeoCoordinates(x, y, city) {
  // 确保城市参数已加载
  const loaded = await loadCityParameters();
  if (!loaded) {
    throw new Error('无法获取城市参数配置');
  }
  
  // 检查城市参数是否存在
  if (!CITY_CENTERS[city] || !CITY_SCALE_FACTORS[city]) {
    console.error(`未找到城市信息: ${city}，支持的城市:`, Object.keys(CITY_CENTERS));
    throw new Error(`未找到城市信息: ${city}，请确保配置中包含该城市的参数`);
  }
  
  // 获取对应城市的中心点经纬度和缩放因子
  const [centerLongitude, centerLatitude] = CITY_CENTERS[city];
  const scaleFactor = CITY_SCALE_FACTORS[city];
  
  // 使用高精度浮点数计算 - 修正公式与后端保持一致
  // 转换公式: 经度 = 城市中心经度 + (x坐标 - 500) * 城市缩放因子 / 500
  const longitude = centerLongitude + ((x - 500.0) * scaleFactor / 500.0);
  // 转换公式: 纬度 = 城市中心纬度 - (y坐标 - 500) * 城市缩放因子 / 500
  const latitude = centerLatitude - ((y - 500.0) * scaleFactor / 500.0);
  
  console.log(`坐标转换: ${city} (${x},${y}) => (${longitude.toFixed(6)},${latitude.toFixed(6)})`);
  
  return {
    longitude: longitude,
    latitude: latitude
  };
}

/**
 * 将经纬度转换为系统内部坐标(0-999整数)
 * @param {number} longitude - 经度
 * @param {number} latitude - 纬度
 * @param {string} city - 城市代码(中文)
 * @returns {Promise<object>} 包含x和y的对象
 */
async function geoToSystemCoordinates(longitude, latitude, city) {
  // 确保城市参数已加载
  const loaded = await loadCityParameters();
  if (!loaded) {
    throw new Error('无法获取城市参数配置');
  }
  
  // 检查城市参数是否存在
  if (!CITY_CENTERS[city] || !CITY_SCALE_FACTORS[city]) {
    console.error(`未找到城市信息: ${city}，支持的城市:`, Object.keys(CITY_CENTERS));
    throw new Error(`未找到城市信息: ${city}，请确保配置中包含该城市的参数`);
  }
  
  // 获取对应城市的中心点经纬度和缩放因子
  const [centerLongitude, centerLatitude] = CITY_CENTERS[city];
  const scaleFactor = CITY_SCALE_FACTORS[city];
  
  // 使用高精度浮点数计算 - 修正公式与后端保持一致
  // 转换公式: x坐标 = 500 + (经度 - 城市中心经度) * 500 / 城市缩放因子
  const xFloat = 500.0 + ((longitude - centerLongitude) * 500.0 / scaleFactor);
  // 转换公式: y坐标 = 500 - (纬度 - 城市中心纬度) * 500 / 城市缩放因子
  const yFloat = 500.0 - ((latitude - centerLatitude) * 500.0 / scaleFactor);
  
  // 最终结果转换为整数
  let x = Math.round(xFloat);
  let y = Math.round(yFloat);
  
  // 确保坐标在0-999范围内
  x = Math.max(0, Math.min(999, x));
  y = Math.max(0, Math.min(999, y));
  
  return { x, y };
}

/**
 * 获取城市中心点坐标
 * @param {string} city - 城市代码(中文)
 * @returns {Promise<object>} 包含longitude和latitude的对象
 */
async function getCityCenter(city) {
  // 确保城市参数已加载
  const loaded = await loadCityParameters();
  if (!loaded) {
    throw new Error('无法获取城市参数配置');
  }
  
  if (!CITY_CENTERS[city]) {
    throw new Error(`未找到城市信息: ${city}`);
  }
  
  const [longitude, latitude] = CITY_CENTERS[city];
  return { longitude, latitude };
}

/**
 * 获取所有支持的城市列表
 * @returns {Promise<array>} 城市代码数组
 */
async function getSupportedCities() {
  // 确保城市参数已加载
  const loaded = await loadCityParameters();
  if (!loaded) {
    throw new Error('无法获取城市参数配置');
  }
  
  return Object.keys(CITY_CENTERS);
}

/**
 * 验证坐标是否在有效范围内
 * @param {number} x - X坐标
 * @param {number} y - Y坐标
 * @returns {boolean} 是否有效
 */
function isValidSystemCoordinate(x, y) {
  return x >= 0 && x <= 999 && y >= 0 && y <= 999;
}

/**
 * 计算两个系统坐标点之间的距离
 * @param {number} x1 - 第一个点的X坐标
 * @param {number} y1 - 第一个点的Y坐标
 * @param {number} x2 - 第二个点的X坐标
 * @param {number} y2 - 第二个点的Y坐标
 * @returns {number} 距离（系统坐标单位）
 */
function calculateSystemDistance(x1, y1, x2, y2) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  return Math.sqrt(dx * dx + dy * dy);
}

module.exports = {
  loadCityParameters,
  systemToGeoCoordinates,
  geoToSystemCoordinates,
  getCityCenter,
  getSupportedCities,
  isValidSystemCoordinate,
  calculateSystemDistance
}; 