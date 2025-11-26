import mysql.connector
from app.config.database import db_config

class BaseDAO:
    """数据访问基类，提供基础数据库连接和操作方法"""
    
    @staticmethod
    def get_connection():
        """获取数据库连接"""
        try:
            conn = mysql.connector.connect(**db_config)
            return conn
        except Exception as e:
            print(f"数据库连接错误: {str(e)}")
            raise e
    
    @staticmethod
    def execute_query(query, params=None):
        """执行查询语句并返回结果"""
        conn = None
        cursor = None
        try:
            conn = BaseDAO.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Exception as e:
            print(f"查询执行错误: {str(e)}")
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @staticmethod
    def execute_update(query, params=None):
        """执行更新/插入/删除操作并返回影响的行数"""
        conn = None
        cursor = None
        try:
            conn = BaseDAO.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"更新执行错误: {str(e)}")
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @staticmethod
    def execute_transaction(queries_and_params):
        """执行事务操作
        
        Args:
            queries_and_params: 包含(query, params)元组的列表
        
        Returns:
            执行结果列表
        """
        conn = None
        cursor = None
        results = []
        
        try:
            conn = BaseDAO.get_connection()
            cursor = conn.cursor()
            conn.start_transaction()
            
            for query, params in queries_and_params:
                cursor.execute(query, params or ())
                results.append(cursor.rowcount)
            
            conn.commit()
            return results
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"事务执行错误: {str(e)}")
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @staticmethod
    def execute_transaction_with_results(queries_and_params):
        """执行事务操作并返回每个查询的结果
        
        Args:
            queries_and_params: 包含(query, params)元组的列表
        
        Returns:
            每个查询的结果列表，SELECT语句返回查询结果集，其他语句返回受影响的行数
        """
        conn = None
        cursor = None
        results = []
        
        try:
            conn = BaseDAO.get_connection()
            conn.start_transaction()
            
            for query, params in queries_and_params:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params or ())
                
                # 判断查询类型
                if query.strip().upper().startswith("SELECT"):
                    # 查询操作，获取结果集
                    results.append(cursor.fetchall())
                else:
                    # 非查询操作，获取影响的行数
                    results.append(cursor.rowcount)
                    
                cursor.close()
                cursor = None
            
            conn.commit()
            return results
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"事务执行错误: {str(e)}")
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @staticmethod
    def execute_batch(query, params_list):
        """批量执行SQL语句
        
        Args:
            query: SQL语句
            params_list: 参数列表，每个元素是一个元组，包含SQL语句的参数
            
        Returns:
            影响的行数
        """
        conn = None
        cursor = None
        try:
            conn = BaseDAO.get_connection()
            cursor = conn.cursor()
            
            # 执行批量插入
            cursor.executemany(query, params_list)
            conn.commit()
            
            return cursor.rowcount
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"批量执行SQL错误: {str(e)}")
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close() 