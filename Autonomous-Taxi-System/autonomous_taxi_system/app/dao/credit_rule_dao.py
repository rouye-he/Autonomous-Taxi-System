#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app.dao.base_dao import BaseDAO
import traceback

class CreditRuleDAO(BaseDAO):
    """信用分变动规则数据访问对象，封装所有信用规则相关的数据库操作"""
    
    @staticmethod
    def get_all_credit_rules():
        """获取所有信用分变动规则"""
        try:
            query = """
            SELECT 
                rule_id, rule_name, rule_type, trigger_event, 
                score_change, description, is_active,
                created_at, updated_at
            FROM 
                credit_rules
            ORDER BY 
                rule_type, score_change DESC
            """
            
            rules = BaseDAO.execute_query(query)
            return rules
        except Exception as e:
            print(f"获取信用分变动规则错误: {str(e)}")
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_credit_rules_by_type(rule_type):
        """根据类型获取信用分变动规则
        
        Args:
            rule_type: 规则类型 ("奖励", "惩罚", "恢复")
            
        Returns:
            list: 规则列表
        """
        try:
            query = """
            SELECT 
                rule_id, rule_name, rule_type, trigger_event, 
                score_change, description, is_active,
                created_at, updated_at
            FROM 
                credit_rules
            WHERE 
                rule_type = %s AND is_active = 1
            ORDER BY 
                score_change DESC
            """
            
            rules = BaseDAO.execute_query(query, (rule_type,))
            return rules
        except Exception as e:
            print(f"获取信用分变动规则错误: {str(e)}")
            traceback.print_exc()
            return []
    
    @staticmethod
    def get_credit_rule_by_id(rule_id):
        """根据ID获取信用分变动规则"""
        try:
            query = """
            SELECT 
                rule_id, rule_name, rule_type, trigger_event, 
                score_change, description, is_active,
                created_at, updated_at
            FROM 
                credit_rules
            WHERE 
                rule_id = %s
            """
            
            results = BaseDAO.execute_query(query, (rule_id,))
            
            if not results:
                return None
            
            return results[0]
        except Exception as e:
            print(f"获取信用分变动规则详情错误: {str(e)}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def add_credit_rule(rule_data):
        """添加新的信用分变动规则
        
        Args:
            rule_data: 包含rule_name, rule_type, trigger_event, score_change, description的字典
            
        Returns:
            新创建的规则ID，如果失败则返回None
        """
        try:
            query = """
            INSERT INTO credit_rules 
            (rule_name, rule_type, trigger_event, score_change, description) 
            VALUES (%s, %s, %s, %s, %s)
            """
            
            params = (
                rule_data.get('rule_name'),
                rule_data.get('rule_type'),
                rule_data.get('trigger_event'),
                rule_data.get('score_change'),
                rule_data.get('description')
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
            print(f"添加信用分变动规则错误: {str(e)}")
            traceback.print_exc()
            return None
    
    @staticmethod
    def update_credit_rule(rule_id, rule_data):
        """更新信用分变动规则
        
        Args:
            rule_id: 规则ID
            rule_data: 包含rule_name, rule_type, trigger_event, score_change, description的字典
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 构建更新语句
            update_parts = []
            params = []
            
            # 检查每个字段是否需要更新
            if 'rule_name' in rule_data:
                update_parts.append("rule_name = %s")
                params.append(rule_data['rule_name'])
                
            if 'rule_type' in rule_data:
                update_parts.append("rule_type = %s")
                params.append(rule_data['rule_type'])
                
            if 'trigger_event' in rule_data:
                update_parts.append("trigger_event = %s")
                params.append(rule_data['trigger_event'])
                
            if 'score_change' in rule_data:
                update_parts.append("score_change = %s")
                params.append(rule_data['score_change'])
                
            if 'description' in rule_data:
                update_parts.append("description = %s")
                params.append(rule_data['description'])
                
            if 'is_active' in rule_data:
                update_parts.append("is_active = %s")
                params.append(rule_data['is_active'])
            
            # 如果没有需要更新的字段，直接返回成功
            if not update_parts:
                return True
            
            # 构建完整的更新语句
            query = """
            UPDATE credit_rules 
            SET {} 
            WHERE rule_id = %s
            """.format(", ".join(update_parts))
            
            # 添加规则ID到参数列表
            params.append(rule_id)
            
            # 执行更新操作
            affected_rows = BaseDAO.execute_update(query, tuple(params))
            
            return affected_rows > 0
        except Exception as e:
            print(f"更新信用分变动规则错误: {str(e)}")
            traceback.print_exc()
            return False
    
    @staticmethod
    def delete_credit_rule(rule_id):
        """删除信用分变动规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            query = "DELETE FROM credit_rules WHERE rule_id = %s"
            affected_rows = BaseDAO.execute_update(query, (rule_id,))
            
            return affected_rows > 0
        except Exception as e:
            print(f"删除信用分变动规则错误: {str(e)}")
            traceback.print_exc()
            return False
    
    @staticmethod
    def change_rule_status(rule_id, is_active):
        """更改规则状态（激活/禁用）
        
        Args:
            rule_id: 规则ID
            is_active: 是否激活 (0表示禁用，1表示激活)
            
        Returns:
            bool: 操作是否成功
        """
        try:
            query = "UPDATE credit_rules SET is_active = %s WHERE rule_id = %s"
            affected_rows = BaseDAO.execute_update(query, (is_active, rule_id))
            
            return affected_rows > 0
        except Exception as e:
            print(f"更改规则状态错误: {str(e)}")
            traceback.print_exc()
            return False 