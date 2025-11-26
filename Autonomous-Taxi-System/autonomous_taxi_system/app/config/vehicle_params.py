"""
车辆相关的全局参数配置文件 - 从数据库中读取参数
"""

import mysql.connector
import os
import json
import logging
from functools import lru_cache
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('vehicle_params')

# 数据库连接配置
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '123456'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME', 'autonomous_taxi_system')
}

class DatabaseConnectionError(Exception):
    """数据库连接失败异常"""
    pass

class ParameterNotFoundError(Exception):
    """参数不存在异常"""
    pass

# 创建一个全局的参数字典
_PARAMS = {}

# 初始化连接状态
_DB_CONNECTION_FAILED = False

# 创建城市距离转换比例字典
CITY_DISTANCE_RATIO = {
    "沈阳市": 0.0,
    "上海市": 0.0,
    "北京市": 0.0,
    "广州市": 0.0,
    "深圳市": 0.0,
    "杭州市": 0.0,
    "南京市": 0.0,
    "成都市": 0.0,
    "重庆市": 0.0,
    "武汉市": 0.0,
    "西安市": 0.0
}

# 创建城市价格系数字典
CITY_PRICE_FACTORS = {}

# 创建城市支付方式偏好系数
CITY_PAYMENT_FACTORS = {}

# 当前城市 - 默认为沈阳市
CURRENT_CITY = "沈阳市"

@lru_cache(maxsize=1)
def get_db_connection():
    """获取数据库连接"""
    global _DB_CONNECTION_FAILED
    
    if _DB_CONNECTION_FAILED:
        # 如果之前已经失败过，不再尝试连接
        logger.error("之前数据库连接失败")
        raise DatabaseConnectionError("数据库连接失败")
        
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Exception as e:
        _DB_CONNECTION_FAILED = True
        logger.error(f"数据库连接失败: {str(e)}")
        raise DatabaseConnectionError(f"数据库连接失败: {str(e)}")

def get_param(param_key, default_value=None):
    """
    从数据库获取参数值
    
    Args:
        param_key: 参数键名
        default_value: 默认值（只有明确传入时才使用）
    
    Returns:
        参数值
    
    Raises:
        DatabaseConnectionError: 数据库连接失败时抛出
        ParameterNotFoundError: 参数不存在时抛出
    """
    # 首先检查全局参数字典中是否已有缓存值
    if param_key in _PARAMS:
        return _PARAMS[param_key]
    
    logger.info(f"开始从数据库获取参数: {param_key}")
    
    try:
        conn = get_db_connection()
        
        cursor = conn.cursor(dictionary=True)
        query = "SELECT param_value, param_type FROM system_parameters WHERE param_key = %s"
        logger.info(f"执行查询: {query} with param: {param_key}")
        
        cursor.execute(query, (param_key,))
        result = cursor.fetchone()
        cursor.close()
        
        if not result:
            if default_value is not None:
                logger.warning(f"参数 {param_key} 在数据库中不存在，使用传入的默认值: {default_value}")
                _PARAMS[param_key] = default_value
                return default_value
            else:
                error_msg = f"参数 {param_key} 在数据库中不存在"
                logger.error(error_msg)
                raise ParameterNotFoundError(error_msg)
        
        # 根据参数类型转换值
        param_value = result['param_value']
        param_type = result['param_type']
        
        
        try:
            if param_type == 'int':
                param_value = int(param_value)
            elif param_type == 'float':
                param_value = float(param_value)
            elif param_type == 'boolean':
                param_value = param_value.lower() in ('true', '1', 'yes')
            elif param_type == 'json' or param_type == 'array':
                param_value = json.loads(param_value)
                
            logger.info(f"参数 {param_key} 转换后的值: {param_value}")
        except (ValueError, json.JSONDecodeError) as e:
            error_msg = f"参数 {param_key} 值转换失败: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 将值存入全局参数字典
        _PARAMS[param_key] = param_value
        return param_value
    except DatabaseConnectionError:
        # 直接向上传递数据库连接异常
        raise
    except Exception as e:
        if isinstance(e, ParameterNotFoundError) or isinstance(e, ValueError):
            # 直接向上传递参数不存在或值转换异常
            raise
        # 其他未预期的异常
        error_msg = f"获取参数 {param_key} 时出错: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    finally:
        if 'conn' in locals() and conn:
            try:
                conn.close()
            except:
                pass

def init_params():
    """
    初始化所有必需的参数
    
    Raises:
        DatabaseConnectionError: 数据库连接失败时抛出
        ParameterNotFoundError: 必需参数不存在时抛出
    """
    global VEHICLE_MOVEMENT_SPEED, BATTERY_CONSUMPTION_RATE, CHARGING_RATE, LOW_BATTERY_THRESHOLD
    global POSITION_MOVEMENT_INTERVAL, BATTERY_UPDATE_INTERVAL, POSITION_UPDATE_INTERVAL
    global RUNNING_BATTERY_UPDATE_INTERVAL, LOW_BATTERY_UPDATE_INTERVAL, CHARGING_BATTERY_UPDATE_INTERVAL
    global PICKUP_WAITING_TIME, CHARGING_SCHEDULER_INTERVAL, MAX_CHARGING_RETRY_COUNT
    global CHARGING_SCHEDULER_LOG_LEVEL, ORDER_BASE_KM, ORDER_BASE_PRICE, ORDER_PRICE_PER_KM, PAYMENT_METHODS
    global Alpha_X1_PRICE, Alpha_Nexus_PRICE, Alpha_Voyager_PRICE, Nova_S1_PRICE
    global Nova_Quantum_PRICE, Nova_Pulse_PRICE, Neon_500_PRICE, Neon_Zero_PRICE
    global CHARGING_PRICE_PER_PERCENT, CHARGING_STATION_BASE_COST, CHARGING_STATION_VARIABLE_COST
    global Alpha_X1_SPEED, Alpha_Nexus_SPEED, Alpha_Voyager_SPEED, Nova_S1_SPEED
    global Nova_Quantum_SPEED, Nova_Pulse_SPEED, Neon_500_SPEED, Neon_Zero_SPEED
    global Alpha_X1_ORDER_PRICE, Alpha_Nexus_ORDER_PRICE, Alpha_Voyager_ORDER_PRICE, Nova_S1_ORDER_PRICE
    global Nova_Quantum_ORDER_PRICE, Nova_Pulse_ORDER_PRICE, Neon_500_ORDER_PRICE, Neon_Zero_ORDER_PRICE
    global Alpha_X1_CAPACITY, Alpha_Nexus_CAPACITY, Alpha_Voyager_CAPACITY, Nova_S1_CAPACITY
    global Nova_Quantum_CAPACITY, Nova_Pulse_CAPACITY, Neon_500_CAPACITY, Neon_Zero_CAPACITY
    global Alpha_X1_CHARGING_SPEED, Alpha_Nexus_CHARGING_SPEED, Alpha_Voyager_CHARGING_SPEED, Nova_S1_CHARGING_SPEED
    global Nova_Quantum_CHARGING_SPEED, Nova_Pulse_CHARGING_SPEED, Neon_500_CHARGING_SPEED, Neon_Zero_CHARGING_SPEED
    global Alpha_X1_MAINTENANCE_COST, Alpha_Nexus_MAINTENANCE_COST, Alpha_Voyager_MAINTENANCE_COST, Nova_S1_MAINTENANCE_COST
    global Nova_Quantum_MAINTENANCE_COST, Nova_Pulse_MAINTENANCE_COST, Neon_500_MAINTENANCE_COST, Neon_Zero_MAINTENANCE_COST
    global Alpha_X1_ENERGY_CONSUMPTION_COEFFICIENT, Alpha_Nexus_ENERGY_CONSUMPTION_COEFFICIENT, Alpha_Voyager_ENERGY_CONSUMPTION_COEFFICIENT, Nova_S1_ENERGY_CONSUMPTION_COEFFICIENT
    global Nova_Quantum_ENERGY_CONSUMPTION_COEFFICIENT, Nova_Pulse_ENERGY_CONSUMPTION_COEFFICIENT, Neon_500_ENERGY_CONSUMPTION_COEFFICIENT, Neon_Zero_ENERGY_CONSUMPTION_COEFFICIENT
    global _DB_CONNECTION_FAILED
    global CITY_DISTANCE_RATIO, CITY_PRICE_FACTORS, CITY_PAYMENT_FACTORS, CURRENT_CITY
    global BASE_MAINTENANCE_COST, MAINTENANCE_INTERVAL

    # 重置数据库连接状态，强制重新连接
    _DB_CONNECTION_FAILED = False
    if hasattr(get_db_connection, 'cache_clear'):
        get_db_connection.cache_clear()
    
    # 清空参数字典
    _PARAMS.clear()
    
    # 读取所有参数
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT param_key, param_value, param_type FROM system_parameters")
        results = cursor.fetchall()
        cursor.close()
        
        if not results:
            logger.error("数据库中没有找到任何参数")
            raise ParameterNotFoundError("数据库中没有找到任何参数")
        
        for result in results:
            param_key = result['param_key']
            param_value = result['param_value']
            param_type = result['param_type']
            
            
            try:
                if param_type == 'int':
                    param_value = int(param_value)
                elif param_type == 'float':
                    param_value = float(param_value)
                elif param_type == 'boolean':
                    param_value = param_value.lower() in ('true', '1', 'yes')
                elif param_type == 'json' or param_type == 'array':
                    param_value = json.loads(param_value)
                    
                _PARAMS[param_key] = param_value
            except Exception as e:
                error_msg = f"参数 {param_key} 值转换失败: {str(e)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        

    except Exception as e:
        error_msg = f"初始化参数时出错: {str(e)}"
        logger.error(error_msg)
        print(f"初始化参数失败: {error_msg}")
        raise
    finally:
        if 'conn' in locals() and conn:
            try:
                conn.close()
            except:
                pass
    
    # 给全局变量赋值，如果参数不存在则会抛出异常
    try:
        VEHICLE_MOVEMENT_SPEED = get_param('VEHICLE_MOVEMENT_SPEED')
        BATTERY_CONSUMPTION_RATE = get_param('BATTERY_CONSUMPTION_RATE')
        CHARGING_RATE = get_param('CHARGING_RATE')
        LOW_BATTERY_THRESHOLD = get_param('LOW_BATTERY_THRESHOLD')
        POSITION_MOVEMENT_INTERVAL = get_param('POSITION_MOVEMENT_INTERVAL')
        BATTERY_UPDATE_INTERVAL = get_param('BATTERY_UPDATE_INTERVAL')
        POSITION_UPDATE_INTERVAL = get_param('POSITION_UPDATE_INTERVAL')
        RUNNING_BATTERY_UPDATE_INTERVAL = get_param('RUNNING_BATTERY_UPDATE_INTERVAL')
        LOW_BATTERY_UPDATE_INTERVAL = get_param('LOW_BATTERY_UPDATE_INTERVAL')
        CHARGING_BATTERY_UPDATE_INTERVAL = get_param('CHARGING_BATTERY_UPDATE_INTERVAL')
        PICKUP_WAITING_TIME = get_param('PICKUP_WAITING_TIME')
        CHARGING_SCHEDULER_INTERVAL = get_param('CHARGING_SCHEDULER_INTERVAL')
        MAX_CHARGING_RETRY_COUNT = get_param('MAX_CHARGING_RETRY_COUNT')
        CHARGING_SCHEDULER_LOG_LEVEL = get_param('CHARGING_SCHEDULER_LOG_LEVEL')
        ORDER_BASE_KM = get_param('ORDER_BASE_KM')
        ORDER_BASE_PRICE = get_param('ORDER_BASE_PRICE')
        ORDER_PRICE_PER_KM = get_param('ORDER_PRICE_PER_KM')
        PAYMENT_METHODS = get_param('PAYMENT_METHODS')
        
        # 车型价格
        Alpha_X1_PRICE = get_param('Alpha_X1_PRICE')
        Alpha_Nexus_PRICE = get_param('Alpha_Nexus_PRICE')
        Alpha_Voyager_PRICE = get_param('Alpha_Voyager_PRICE')
        Nova_S1_PRICE = get_param('Nova_S1_PRICE')
        Nova_Quantum_PRICE = get_param('Nova_Quantum_PRICE')
        Nova_Pulse_PRICE = get_param('Nova_Pulse_PRICE')
        Neon_500_PRICE = get_param('Neon_500_PRICE')
        Neon_Zero_PRICE = get_param('Neon_Zero_PRICE')

        #车型速度
        Alpha_X1_SPEED = get_param('Alpha_X1_SPEED')
        Alpha_Nexus_SPEED = get_param('Alpha_Nexus_SPEED')
        Alpha_Voyager_SPEED = get_param('Alpha_Voyager_SPEED')
        Nova_S1_SPEED = get_param('Nova_S1_SPEED')
        Nova_Quantum_SPEED = get_param('Nova_Quantum_SPEED')
        Nova_Pulse_SPEED = get_param('Nova_Pulse_SPEED')
        Neon_500_SPEED = get_param('Neon_500_SPEED')
        Neon_Zero_SPEED = get_param('Neon_Zero_SPEED')
        
        #车型订单价格
        Alpha_X1_ORDER_PRICE = get_param('Alpha_X1_ORDER_PRICE')
        Alpha_Nexus_ORDER_PRICE = get_param('Alpha_Nexus_ORDER_PRICE')    
        Alpha_Voyager_ORDER_PRICE = get_param('Alpha_Voyager_ORDER_PRICE')
        Nova_S1_ORDER_PRICE = get_param('Nova_S1_ORDER_PRICE')
        Nova_Quantum_ORDER_PRICE = get_param('Nova_Quantum_ORDER_PRICE')
        Nova_Pulse_ORDER_PRICE = get_param('Nova_Pulse_ORDER_PRICE')
        Neon_500_ORDER_PRICE = get_param('Neon_500_ORDER_PRICE')
        Neon_Zero_ORDER_PRICE = get_param('Neon_Zero_ORDER_PRICE')
        
        #车型电量容量
        Alpha_X1_CAPACITY = get_param('Alpha_X1_CAPACITY')
        Alpha_Nexus_CAPACITY = get_param('Alpha_Nexus_CAPACITY')
        Alpha_Voyager_CAPACITY = get_param('Alpha_Voyager_CAPACITY')
        Nova_S1_CAPACITY = get_param('Nova_S1_CAPACITY')
        Nova_Quantum_CAPACITY = get_param('Nova_Quantum_CAPACITY')
        Nova_Pulse_CAPACITY = get_param('Nova_Pulse_CAPACITY')
        Neon_500_CAPACITY = get_param('Neon_500_CAPACITY')
        Neon_Zero_CAPACITY = get_param('Neon_Zero_CAPACITY')
        
        #车型充电速度
        Alpha_X1_CHARGING_SPEED = get_param('Alpha_X1_CHARGING_SPEED')
        Alpha_Nexus_CHARGING_SPEED = get_param('Alpha_Nexus_CHARGING_SPEED')
        Alpha_Voyager_CHARGING_SPEED = get_param('Alpha_Voyager_CHARGING_SPEED')
        Nova_S1_CHARGING_SPEED = get_param('Nova_S1_CHARGING_SPEED')
        Nova_Quantum_CHARGING_SPEED = get_param('Nova_Quantum_CHARGING_SPEED')
        Nova_Pulse_CHARGING_SPEED = get_param('Nova_Pulse_CHARGING_SPEED')
        Neon_500_CHARGING_SPEED = get_param('Neon_500_CHARGING_SPEED')
        Neon_Zero_CHARGING_SPEED = get_param('Neon_Zero_CHARGING_SPEED')

        #车型维护成本
        Alpha_X1_MAINTENANCE_COST = get_param('Alpha_X1_MAINTENANCE_COST')
        Alpha_Nexus_MAINTENANCE_COST = get_param('Alpha_Nexus_MAINTENANCE_COST')
        Alpha_Voyager_MAINTENANCE_COST = get_param('Alpha_Voyager_MAINTENANCE_COST')
        Nova_S1_MAINTENANCE_COST = get_param('Nova_S1_MAINTENANCE_COST')
        Nova_Quantum_MAINTENANCE_COST = get_param('Nova_Quantum_MAINTENANCE_COST')
        Nova_Pulse_MAINTENANCE_COST = get_param('Nova_Pulse_MAINTENANCE_COST')
        Neon_500_MAINTENANCE_COST = get_param('Neon_500_MAINTENANCE_COST')
        Neon_Zero_MAINTENANCE_COST = get_param('Neon_Zero_MAINTENANCE_COST')
        BASE_MAINTENANCE_COST=get_param('BASE_MAINTENANCE_COST')
        MAINTENANCE_INTERVAL = get_param('MAINTENANCE_INTERVAL')
        
        #车型能耗系数
        Alpha_X1_ENERGY_CONSUMPTION_COEFFICIENT = get_param('Alpha_X1_ENERGY_CONSUMPTION_COEFFICIENT')
        Alpha_Nexus_ENERGY_CONSUMPTION_COEFFICIENT = get_param('Alpha_Nexus_ENERGY_CONSUMPTION_COEFFICIENT')
        Alpha_Voyager_ENERGY_CONSUMPTION_COEFFICIENT = get_param('Alpha_Voyager_ENERGY_CONSUMPTION_COEFFICIENT')
        Nova_S1_ENERGY_CONSUMPTION_COEFFICIENT = get_param('Nova_S1_ENERGY_CONSUMPTION_COEFFICIENT')
        Nova_Quantum_ENERGY_CONSUMPTION_COEFFICIENT = get_param('Nova_Quantum_ENERGY_CONSUMPTION_COEFFICIENT')
        Nova_Pulse_ENERGY_CONSUMPTION_COEFFICIENT = get_param('Nova_Pulse_ENERGY_CONSUMPTION_COEFFICIENT')
        Neon_500_ENERGY_CONSUMPTION_COEFFICIENT = get_param('Neon_500_ENERGY_CONSUMPTION_COEFFICIENT')
        Neon_Zero_ENERGY_CONSUMPTION_COEFFICIENT = get_param('Neon_Zero_ENERGY_CONSUMPTION_COEFFICIENT')

        # 充电站价格参数
        CHARGING_PRICE_PER_PERCENT = get_param('CHARGING_PRICE_PER_PERCENT')
        CHARGING_STATION_BASE_COST = get_param('CHARGING_STATION_BASE_COST')
        CHARGING_STATION_VARIABLE_COST = get_param('CHARGING_STATION_VARIABLE_COST')
        
        # 初始化城市距离转换比例
        for city in CITY_DISTANCE_RATIO.keys():
            try:
                # 直接使用城市名称作为参数键名
                CITY_DISTANCE_RATIO[city] = get_param(city)
            except ParameterNotFoundError:
                # 这里不再设置默认值，而是抛出异常
                error_msg = f"未找到城市 {city} 的距离转换比例参数"
                logger.error(error_msg)
                raise ParameterNotFoundError(error_msg)
        
        # 初始化城市价格系数
        try:
            CITY_PRICE_FACTORS = get_param('CITY_PRICE_FACTORS')
        except ParameterNotFoundError:
            # 不再使用默认值，而是抛出异常
            error_msg = "未找到城市价格系数参数"
            logger.error(error_msg)
            raise ParameterNotFoundError(error_msg)
        
        # 初始化城市支付方式偏好系数
        try:
            CITY_PAYMENT_FACTORS = get_param('CITY_PAYMENT_FACTORS')
        except ParameterNotFoundError:
            # 不再使用默认值，而是抛出异常
            error_msg = "未找到城市支付方式偏好系数参数"
            logger.error(error_msg)
            raise ParameterNotFoundError(error_msg)
  
    except Exception as e:
        error_msg = f"系统参数赋值失败: {str(e)}"
        logger.error(error_msg)
        print(f"初始化失败: {error_msg}")
        raise

def refresh_params():
    """
    刷新所有参数值
    
    Raises:
        DatabaseConnectionError: 数据库连接失败时抛出
        ParameterNotFoundError: 必需参数不存在时抛出
    """
    global _DB_CONNECTION_FAILED
    
    # 重置连接状态和缓存
    _DB_CONNECTION_FAILED = False
    get_db_connection.cache_clear()
    _PARAMS.clear()
    
    # 重新初始化所有参数
    init_params()
    
    logger.info("系统参数已刷新")

# 初始化全局变量为None，这些变量值必须通过init_params()来设置
VEHICLE_MOVEMENT_SPEED = None
BATTERY_CONSUMPTION_RATE = None
CHARGING_RATE = None
LOW_BATTERY_THRESHOLD = None
POSITION_MOVEMENT_INTERVAL = None
BATTERY_UPDATE_INTERVAL = None
POSITION_UPDATE_INTERVAL = None
RUNNING_BATTERY_UPDATE_INTERVAL = None
LOW_BATTERY_UPDATE_INTERVAL = None
CHARGING_BATTERY_UPDATE_INTERVAL = None
PICKUP_WAITING_TIME = None
CHARGING_SCHEDULER_INTERVAL = None
MAX_CHARGING_RETRY_COUNT = None
CHARGING_SCHEDULER_LOG_LEVEL = None
ORDER_BASE_KM = None
ORDER_BASE_PRICE = None
ORDER_PRICE_PER_KM = None
PAYMENT_METHODS = None

# 车型价格
Alpha_X1_PRICE = None
Alpha_Nexus_PRICE = None
Alpha_Voyager_PRICE = None
Nova_S1_PRICE = None
Nova_Quantum_PRICE = None
Nova_Pulse_PRICE = None
Neon_500_PRICE = None   
Neon_Zero_PRICE = None     

#车型速度
Alpha_X1_SPEED = None
Alpha_Nexus_SPEED = None
Alpha_Voyager_SPEED = None
Nova_S1_SPEED = None
Nova_Quantum_SPEED = None
Nova_Pulse_SPEED = None
Neon_500_SPEED = None
Neon_Zero_SPEED = None

#车型订单价格
Alpha_X1_ORDER_PRICE = None
Alpha_Nexus_ORDER_PRICE = None
Alpha_Voyager_ORDER_PRICE = None
Nova_S1_ORDER_PRICE = None
Nova_Quantum_ORDER_PRICE = None
Nova_Pulse_ORDER_PRICE = None
Neon_500_ORDER_PRICE = None
Neon_Zero_ORDER_PRICE = None

#车型电量容量
Alpha_X1_CAPACITY = None
Alpha_Nexus_CAPACITY = None
Alpha_Voyager_CAPACITY = None
Nova_S1_CAPACITY = None
Nova_Quantum_CAPACITY = None
Nova_Pulse_CAPACITY = None
Neon_500_CAPACITY = None
Neon_Zero_CAPACITY = None

#车型充电速度
Alpha_X1_CHARGING_SPEED = None
Alpha_Nexus_CHARGING_SPEED = None
Alpha_Voyager_CHARGING_SPEED = None
Nova_S1_CHARGING_SPEED = None
Nova_Quantum_CHARGING_SPEED = None
Nova_Pulse_CHARGING_SPEED = None
Neon_500_CHARGING_SPEED = None
Neon_Zero_CHARGING_SPEED = None

#车型维护成本
Alpha_X1_MAINTENANCE_COST = None
Alpha_Nexus_MAINTENANCE_COST = None
Alpha_Voyager_MAINTENANCE_COST = None
Nova_S1_MAINTENANCE_COST = None
Nova_Quantum_MAINTENANCE_COST = None
Nova_Pulse_MAINTENANCE_COST = None
Neon_500_MAINTENANCE_COST = None
Neon_Zero_MAINTENANCE_COST = None
BASE_MAINTENANCE_COST = None
MAINTENANCE_INTERVAL = None
#车型能耗系数
Alpha_X1_ENERGY_CONSUMPTION_COEFFICIENT = None
Alpha_Nexus_ENERGY_CONSUMPTION_COEFFICIENT = None
Alpha_Voyager_ENERGY_CONSUMPTION_COEFFICIENT = None
Nova_S1_ENERGY_CONSUMPTION_COEFFICIENT = None
Nova_Quantum_ENERGY_CONSUMPTION_COEFFICIENT = None
Nova_Pulse_ENERGY_CONSUMPTION_COEFFICIENT = None
Neon_500_ENERGY_CONSUMPTION_COEFFICIENT = None
Neon_Zero_ENERGY_CONSUMPTION_COEFFICIENT = None

# 充电站价格参数
CHARGING_PRICE_PER_PERCENT = None
CHARGING_STATION_BASE_COST = None
CHARGING_STATION_VARIABLE_COST = None

def set_current_city(city):
    """
    设置当前城市
    
    Args:
        city (str): 城市名称
    
    Returns:
        bool: 设置是否成功
    """
    global CURRENT_CITY
    
    if city in CITY_DISTANCE_RATIO:
        CURRENT_CITY = city
        logger.info(f"当前城市已设置为: {city}")
        return True
    else:
        logger.error(f"无效的城市名称: {city}")
        return False

def get_city_order_price_factor(city=None):
    """
    获取指定城市的订单价格系数
    
    Args:
        city (str, optional): 城市名称，如果不指定则使用当前城市
    
    Returns:
        float: 城市订单价格系数
        
    Raises:
        KeyError: 如果找不到指定城市的价格系数
    """
    if city is None:
        city = CURRENT_CITY
    
    if city not in CITY_PRICE_FACTORS:
        raise KeyError(f"找不到城市 {city} 的价格系数")
        
    return CITY_PRICE_FACTORS[city].get('orderPrice')

def get_city_charging_price_factor(city=None):
    """
    获取指定城市的充电价格系数
    
    Args:
        city (str, optional): 城市名称，如果不指定则使用当前城市
    
    Returns:
        float: 城市充电价格系数
        
    Raises:
        KeyError: 如果找不到指定城市的价格系数
    """
    if city is None:
        city = CURRENT_CITY
    
    if city not in CITY_PRICE_FACTORS:
        raise KeyError(f"找不到城市 {city} 的价格系数")
        
    return CITY_PRICE_FACTORS[city].get('chargingPrice')

def get_city_maintenance_factor(city=None):
    """
    获取指定城市的维护成本系数
    
    Args:
        city (str, optional): 城市名称，如果不指定则使用当前城市
    
    Returns:
        float: 城市维护成本系数
        
    Raises:
        KeyError: 如果找不到指定城市的价格系数
    """
    if city is None:
        city = CURRENT_CITY
    
    if city not in CITY_PRICE_FACTORS:
        raise KeyError(f"找不到城市 {city} 的价格系数")
        
    return CITY_PRICE_FACTORS[city].get('maintenance')

def get_city_vehicle_price_factor(city=None):
    """
    获取指定城市的车辆购置价格系数
    
    Args:
        city (str, optional): 城市名称，如果不指定则使用当前城市
    
    Returns:
        float: 城市车辆购置价格系数
        
    Raises:
        KeyError: 如果找不到指定城市的价格系数
    """
    if city is None:
        city = CURRENT_CITY
    
    if city not in CITY_PRICE_FACTORS:
        raise KeyError(f"找不到城市 {city} 的价格系数")
        
    return CITY_PRICE_FACTORS[city].get('vehiclePrice')

def get_city_charging_station_price_factor(city=None):
    """
    获取指定城市的充电站价格系数
    
    Args:
        city (str, optional): 城市名称，如果不指定则使用当前城市
    
    Returns:
        float: 城市充电站价格系数
        
    Raises:
        KeyError: 如果找不到指定城市的价格系数
    """
    if city is None:
        city = CURRENT_CITY
    
    if city not in CITY_PRICE_FACTORS:
        raise KeyError(f"找不到城市 {city} 的价格系数")
        
    return CITY_PRICE_FACTORS[city].get('chargingStationPrice')

def get_city_distance_ratio(city=None):
    """
    获取指定城市的距离转换比例
    
    Args:
        city (str, optional): 城市名称，如果不指定则使用当前城市
    
    Returns:
        float: 城市距离转换比例
    
    Raises:
        KeyError: 如果找不到指定城市的距离转换比例
    """
    if city is None:
        city = CURRENT_CITY
    
    if city not in CITY_DISTANCE_RATIO:
        raise KeyError(f"找不到城市 {city} 的距离转换比例")
    
    return CITY_DISTANCE_RATIO[city]

def get_weighted_payment_method(city=None):
    """
    强制使用余额支付，不考虑城市支付方式偏好系数
    
    Args:
        city (str, optional): 城市名称（已忽略）
    
    Returns:
        str: 固定返回余额支付
    """
    # 强制返回余额支付，忽略所有权重配置
    return '余额支付'

# 在应用开始时需要调用init_params()加载数据库参数
# 注意: 需要在应用上下文中调用，通常在app/__init__.py中
