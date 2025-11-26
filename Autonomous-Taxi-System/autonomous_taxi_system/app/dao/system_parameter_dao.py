from app.dao.base_dao import BaseDAO
import logging
import json

logger = logging.getLogger(__name__)

class SystemParameterDAO(BaseDAO):
    """系统参数数据访问对象类"""

    @classmethod
    def get_all_parameters(cls):
        """获取所有系统参数"""
        try:
            query = "SELECT param_key, param_value, param_type FROM system_parameters"
            parameters = cls.execute_query(query)
            
            result = {}
            for param in parameters:
                param_key = param['param_key']
                param_value = param['param_value']
                param_type = param['param_type']
                
                # 根据参数类型转换值
                try:
                    if param_type == 'int':
                        param_value = int(param_value)
                    elif param_type == 'float':
                        param_value = float(param_value)
                    elif param_type == 'boolean':
                        param_value = param_value.lower() in ('true', '1', 'yes')
                    elif param_type == 'json' or param_type == 'array':
                        param_value = json.loads(param_value)
                except Exception as e:
                    logger.warning(f"参数 {param_key} 值转换失败: {str(e)}")
                
                result[param_key] = param_value
                
            return result
        except Exception as e:
            logger.error(f"获取系统参数时出错: {str(e)}")
            return {}

    @classmethod
    def update_parameter(cls, param_key, param_value):
        """
        更新系统参数
        
        Args:
            param_key: 参数键名
            param_value: 参数值
        
        Returns:
            bool: 操作是否成功
        """
        try:
            # 处理不同类型的参数值
            param_type = cls.get_parameter_type(param_value)
            
            # 对于复杂类型，转换为JSON字符串
            if param_type in ('json', 'array'):
                param_value = json.dumps(param_value)
            elif param_type == 'boolean':
                param_value = 'true' if param_value else 'false'
            else:
                param_value = str(param_value)
            
            # 检查参数是否存在
            check_query = "SELECT COUNT(*) as count FROM system_parameters WHERE param_key = %s"
            result = cls.execute_query(check_query, (param_key,))
            
            if result and result[0]['count'] > 0:
                # 更新已存在的参数
                update_query = """
                UPDATE system_parameters 
                SET param_value = %s, param_type = %s, updated_at = NOW() 
                WHERE param_key = %s
                """
                cls.execute_update(update_query, (param_value, param_type, param_key))
            else:
                # 插入新参数
                insert_query = """
                INSERT INTO system_parameters 
                (param_key, param_value, param_type, created_at, updated_at) 
                VALUES (%s, %s, %s, NOW(), NOW())
                """
                cls.execute_update(insert_query, (param_key, param_value, param_type))
                
            return True
        except Exception as e:
            logger.error(f"更新参数 {param_key} 时出错: {str(e)}")
            return False
    
    @classmethod
    def batch_update_parameters(cls, parameters):
        """
        批量更新系统参数
        
        Args:
            parameters: 参数字典 {param_key: param_value, ...}
        
        Returns:
            tuple: (成功数量, 总数量)
        """
        success_count = 0
        total_count = len(parameters)
        
        try:
            for param_key, param_value in parameters.items():
                if cls.update_parameter(param_key, param_value):
                    success_count += 1
            
            # 刷新系统参数缓存
            from app.config.vehicle_params import refresh_params
            refresh_params()
            
            return success_count, total_count
        except Exception as e:
            logger.error(f"批量更新参数时出错: {str(e)}")
            return success_count, total_count
    
    @staticmethod
    def get_parameter_type(value):
        """
        根据值确定参数类型
        
        Args:
            value: 参数值
        
        Returns:
            str: 参数类型（int, float, boolean, array, json, string）
        """
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'int'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, list):
            return 'array'
        elif isinstance(value, dict):
            return 'json'
        else:
            return 'string'
    
    @classmethod
    def create_parameters_table_if_not_exists(cls):
        """创建系统参数表（如果不存在）"""
        try:
            # 检查表是否存在
            check_query = """
            SELECT COUNT(*) as count
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'system_parameters'
            """
            result = cls.execute_query(check_query)
            
            if result and result[0]['count'] == 0:
                # 创建表
                create_table_query = """
                CREATE TABLE system_parameters (
                    param_id INT AUTO_INCREMENT PRIMARY KEY,
                    param_key VARCHAR(100) NOT NULL UNIQUE,
                    param_value TEXT NOT NULL,
                    param_type VARCHAR(20) NOT NULL DEFAULT 'string',
                    description VARCHAR(255),
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    INDEX idx_param_key (param_key)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统参数表';
                """
                cls.execute_update(create_table_query)
                logger.info("已创建系统参数表")
            
            return True
        except Exception as e:
            logger.error(f"创建系统参数表时出错: {str(e)}")
            return False
            
    @classmethod
    def init_default_parameters(cls, default_params):
        """初始化默认系统参数"""
        try:
            # 获取当前所有参数
            query = "SELECT param_key FROM system_parameters"
            existing_params = cls.execute_query(query)
            existing_keys = set(param['param_key'] for param in existing_params)
            
            # 添加缺失的默认参数
            for param_key, param_value in default_params.items():
                if param_key not in existing_keys:
                    cls.update_parameter(param_key, param_value)
            
            return True
        except Exception as e:
            logger.error(f"初始化默认系统参数时出错: {str(e)}")
            return False 