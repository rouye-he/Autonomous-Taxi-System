#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.dao.base_dao import BaseDAO
import traceback

class CreditLevelDAO(BaseDAO):
    """信用等级规则数据访问对象，封装所有信用等级相关的数据库操作"""
    
    @staticmethod
    def get_all_credit_levels():
        """获取所有信用等级规则"""
        try:
            query = """
            SELECT 
                level_id, level_name, min_score, max_score, 
                benefits, limitations, icon_url, 
                created_at, updated_at
            FROM 
                credit_level_rules
            ORDER BY 
                min_score ASC
            """
            
            levels = BaseDAO.execute_query(query)
            return levels
        except Exception as e:
            print(f"获取信用等级规则错误: {str(e)}")
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_credit_level_by_id(level_id):
        """根据ID获取信用等级规则"""
        try:
            query = """
            SELECT 
                level_id, level_name, min_score, max_score, 
                benefits, limitations, icon_url, 
                created_at, updated_at
            FROM 
                credit_level_rules
            WHERE 
                level_id = %s
            """
            
            results = BaseDAO.execute_query(query, (level_id,))
            
            if not results:
                return None
            
            return results[0]
        except Exception as e:
            print(f"获取信用等级规则详情错误: {str(e)}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def add_credit_level(level_data):
        """添加新的信用等级规则
        
        Args:
            level_data: 包含level_name, min_score, max_score, benefits, limitations, icon_url的字典
            
        Returns:
            新创建的规则ID，如果失败则返回None
        """
        try:
            query = """
            INSERT INTO credit_level_rules 
            (level_name, min_score, max_score, benefits, limitations, icon_url) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            params = (
                level_data.get('level_name'),
                level_data.get('min_score'),
                level_data.get('max_score'),
                level_data.get('benefits'),
                level_data.get('limitations'),
                level_data.get('icon_url')
            )
            
            # 直接连接以获取lastrowid
            conn = BaseDAO.get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute(query, params)
                conn.commit()
                new_id = cursor.lastrowid
                return new_id
            finally:
                cursor.close()
                conn.close()
        except Exception as e:
            print(f"添加信用等级规则错误: {str(e)}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def update_credit_level(level_id, level_data):
        """更新信用等级规则
        
        Args:
            level_id: 规则ID
            level_data: 包含level_name, min_score, max_score, benefits, limitations, icon_url的字典
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 构建更新语句
            update_parts = []
            params = []
            
            # 检查每个字段是否需要更新
            if 'level_name' in level_data:
                update_parts.append("level_name = %s")
                params.append(level_data['level_name'])
                
            if 'min_score' in level_data:
                update_parts.append("min_score = %s")
                params.append(level_data['min_score'])
                
            if 'max_score' in level_data:
                update_parts.append("max_score = %s")
                params.append(level_data['max_score'])
                
            if 'benefits' in level_data:
                update_parts.append("benefits = %s")
                params.append(level_data['benefits'])
                
            if 'limitations' in level_data:
                update_parts.append("limitations = %s")
                params.append(level_data['limitations'])
                
            if 'icon_url' in level_data:
                update_parts.append("icon_url = %s")
                params.append(level_data['icon_url'])
            
            # 如果没有需要更新的字段，直接返回成功
            if not update_parts:
                return True
            
            # 构建完整的更新语句
            query = """
            UPDATE credit_level_rules 
            SET {} 
            WHERE level_id = %s
            """.format(", ".join(update_parts))
            
            # 添加规则ID到参数列表
            params.append(level_id)
            
            # 执行更新操作
            affected_rows = BaseDAO.execute_update(query, tuple(params))
            
            return affected_rows > 0
        except Exception as e:
            print(f"更新信用等级规则错误: {str(e)}")
            traceback.print_exc()
            return False
    
    @staticmethod
    def delete_credit_level(level_id):
        """删除信用等级规则
        
        Args:
            level_id: 规则ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            query = "DELETE FROM credit_level_rules WHERE level_id = %s"
            affected_rows = BaseDAO.execute_update(query, (level_id,))
            
            return affected_rows > 0
        except Exception as e:
            print(f"删除信用等级规则错误: {str(e)}")
            traceback.print_exc()
            return False
    
    @staticmethod
    def get_credit_level_by_score(credit_score):
        """根据信用分获取对应的信用等级
        
        Args:
            credit_score: 用户信用分
            
        Returns:
            dict: 信用等级信息，如果没找到则返回None
        """
        try:
            query = """
            SELECT 
                level_id, level_name, min_score, max_score, 
                benefits, limitations, icon_url
            FROM 
                credit_level_rules
            WHERE 
                %s BETWEEN min_score AND max_score
            LIMIT 1
            """
            
            results = BaseDAO.execute_query(query, (credit_score,))
            
            if not results:
                return None
            
            return results[0]
        except Exception as e:
            print(f"根据信用分获取等级错误: {str(e)}")
            traceback.print_exc()
            return None 