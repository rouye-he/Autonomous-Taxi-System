#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import pymysql
from app.config.database import db_config

class IncomeDAO:
    """收入数据访问对象"""

    @staticmethod
    def get_income_by_id(income_id):
        """根据ID获取收入记录"""
        connection = None
        try:
            connection = pymysql.connect(**db_config)
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT * FROM income 
                WHERE id = %s
                """
                cursor.execute(sql, (income_id,))
                result = cursor.fetchone()
                return result
        except Exception as e:
            print(f"获取收入记录失败: {str(e)}")
            return None
        finally:
            if connection:
                connection.close()

    @staticmethod
    def get_all_incomes(search_params=None, page=1, per_page=10):
        """获取所有收入记录，支持分页和搜索"""
        connection = None
        try:
            connection = pymysql.connect(**db_config)
            
            # 基础SQL
            sql = "SELECT * FROM income WHERE 1=1"
            params = []
            
            # 根据搜索参数添加条件
            if search_params:
                if search_params.get('amount_min'):
                    sql += " AND amount >= %s"
                    params.append(float(search_params['amount_min']))
                
                if search_params.get('amount_max'):
                    sql += " AND amount <= %s"
                    params.append(float(search_params['amount_max']))
                
                if search_params.get('source'):
                    sql += " AND source = %s"
                    params.append(search_params['source'])
                
                if search_params.get('user_id'):
                    sql += " AND user_id = %s"
                    params.append(int(search_params['user_id']))
                
                if search_params.get('date_start'):
                    sql += " AND date >= %s"
                    params.append(search_params['date_start'])
                
                if search_params.get('date_end'):
                    sql += " AND date <= %s"
                    params.append(search_params['date_end'])
                
                if search_params.get('description'):
                    sql += " AND description LIKE %s"
                    params.append(f"%{search_params['description']}%")
            
            # 计算总记录数
            with connection.cursor() as count_cursor:
                count_sql = sql.replace("SELECT *", "SELECT COUNT(*)")
                count_cursor.execute(count_sql, params)
                total_count = count_cursor.fetchone()[0]
            
            # 添加排序和分页
            sql += " ORDER BY created_at DESC"
            sql += " LIMIT %s OFFSET %s"
            offset = (page - 1) * per_page
            params.extend([per_page, offset])
            
            # 执行查询
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, params)
                incomes = cursor.fetchall()
                
                # 计算总页数
                total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
                
                return {
                    'incomes': incomes,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'current_page': page,
                    'per_page': per_page,
                    'offset': offset
                }
        except Exception as e:
            print(f"获取收入记录失败: {str(e)}")
            return {
                'incomes': [],
                'total_count': 0,
                'total_pages': 1,
                'current_page': page,
                'per_page': per_page,
                'offset': 0
            }
        finally:
            if connection:
                connection.close()

    @staticmethod
    def get_income_stats():
        """获取收入统计数据"""
        connection = None
        try:
            connection = pymysql.connect(**db_config)
            stats = {
                'total': 0,
                'recharge': 0,  # 充值收入
                'fare': 0,      # 车费收入
                'other': 0      # 其他收入
            }
            
            # 获取总收入金额
            with connection.cursor() as cursor:
                cursor.execute("SELECT SUM(amount) FROM income")
                total = cursor.fetchone()[0]
                stats['total'] = float(total) if total else 0
            
            # 获取各类型收入统计
            with connection.cursor() as cursor:
                cursor.execute("SELECT source, SUM(amount) as total FROM income GROUP BY source")
                for row in cursor.fetchall():
                    source, amount = row
                    if source == '充值收入':
                        stats['recharge'] = float(amount) if amount else 0
                    elif source == '车费收入':
                        stats['fare'] = float(amount) if amount else 0
                    else:
                        stats['other'] += float(amount) if amount else 0
            
            # 获取收入记录总数
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM income")
                stats['count'] = cursor.fetchone()[0]
            
            return stats
        except Exception as e:
            print(f"获取收入统计失败: {str(e)}")
            return {
                'total': 0,
                'recharge': 0,
                'fare': 0,
                'other': 0,
                'count': 0
            }
        finally:
            if connection:
                connection.close()

    @staticmethod
    def add_income(amount, source, user_id, date, description=None, order_id=None):
        """添加新的收入记录"""
        connection = None
        try:
            connection = pymysql.connect(**db_config)
            with connection.cursor() as cursor:
                sql = """
                INSERT INTO income (amount, source, user_id, order_id, date, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(sql, (amount, source, user_id, order_id, date, description, now, now))
                connection.commit()
                return cursor.lastrowid
        except Exception as e:
            if connection:
                connection.rollback()
            print(f"添加收入记录失败: {str(e)}")
            return None
        finally:
            if connection:
                connection.close()

    @staticmethod
    def update_income(income_id, amount=None, source=None, user_id=None, date=None, description=None):
        """更新收入记录"""
        connection = None
        try:
            connection = pymysql.connect(**db_config)
            
            # 构建更新SQL
            update_fields = []
            params = []
            
            if amount is not None:
                update_fields.append("amount = %s")
                params.append(amount)
            
            if source is not None:
                update_fields.append("source = %s")
                params.append(source)
            
            if user_id is not None:
                update_fields.append("user_id = %s")
                params.append(user_id)
            
            if date is not None:
                update_fields.append("date = %s")
                params.append(date)
            
            if description is not None:
                update_fields.append("description = %s")
                params.append(description)
            
            # 添加更新时间
            update_fields.append("updated_at = %s")
            params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # 添加ID条件
            params.append(income_id)
            
            if not update_fields:
                return False
            
            with connection.cursor() as cursor:
                sql = f"UPDATE income SET {', '.join(update_fields)} WHERE id = %s"
                result = cursor.execute(sql, params)
                connection.commit()
                return result > 0
        except Exception as e:
            if connection:
                connection.rollback()
            print(f"更新收入记录失败: {str(e)}")
            return False
        finally:
            if connection:
                connection.close()

    @staticmethod
    def delete_income(income_id):
        """删除收入记录"""
        connection = None
        try:
            connection = pymysql.connect(**db_config)
            with connection.cursor() as cursor:
                sql = "DELETE FROM income WHERE id = %s"
                result = cursor.execute(sql, (income_id,))
                connection.commit()
                return result > 0
        except Exception as e:
            if connection:
                connection.rollback()
            return False
        finally:
            if connection:
                connection.close() 