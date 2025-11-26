#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymysql
from app.config.database import db_config
from datetime import datetime

class UserDAO:
    """用户数据访问对象"""

    @staticmethod
    def get_user_by_id(user_id):
        """根据ID获取用户信息"""
        connection = None
        try:
            connection = pymysql.connect(**db_config)
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT user_id, username, real_name, phone, email, status
                FROM users
                WHERE user_id = %s
                """
                cursor.execute(sql, (user_id,))
                return cursor.fetchone()
        except Exception as e:
            print(f"获取用户信息失败: {str(e)}")
            return None
        finally:
            if connection:
                connection.close()

    @staticmethod
    def get_all_users():
        """获取所有用户简要信息"""
        connection = None
        try:
            connection = pymysql.connect(**db_config)
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT user_id, username, real_name, phone, email, status
                FROM users
                ORDER BY user_id
                """
                cursor.execute(sql)
                return cursor.fetchall()
        except Exception as e:
            print(f"获取用户列表失败: {str(e)}")
            return []
        finally:
            if connection:
                connection.close()

    @staticmethod
    def update_last_login(user_id):
        """更新用户最后登录时间
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        connection = None
        try:
            connection = pymysql.connect(**db_config)
            with connection.cursor() as cursor:
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                sql = """
                UPDATE users
                SET last_login_time = %s
                WHERE user_id = %s
                """
                result = cursor.execute(sql, (now, user_id))
                connection.commit()
                return result > 0
        except Exception as e:
            if connection:
                connection.rollback()
            print(f"更新用户最后登录时间失败: {str(e)}")
            return False
        finally:
            if connection:
                connection.close() 