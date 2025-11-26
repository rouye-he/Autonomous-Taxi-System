#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import pymysql
from app.config.database import db_config

class ExpenseDAO:
    """支出数据访问对象"""

    @staticmethod
    def get_expense_by_id(expense_id):
        """根据ID获取支出记录"""
        connection = None
        try:
            connection = pymysql.connect(**db_config)
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                SELECT * FROM expense 
                WHERE id = %s
                """
                cursor.execute(sql, (expense_id,))
                result = cursor.fetchone()
                return result
        except Exception as e:
            print(f"获取支出记录失败: {str(e)}")
            return None
        finally:
            if connection:
                connection.close()

    @staticmethod
    def get_all_expenses(search_params=None, page=1, per_page=10):
        """获取所有支出记录，支持分页和搜索"""
        connection = None
        try:
            connection = pymysql.connect(**db_config)
            
            # 基础SQL
            sql = "SELECT * FROM expense WHERE 1=1"
            params = []
            
            # 根据搜索参数添加条件
            if search_params:
                if search_params.get('amount_min'):
                    sql += " AND amount >= %s"
                    params.append(float(search_params['amount_min']))
                
                if search_params.get('amount_max'):
                    sql += " AND amount <= %s"
                    params.append(float(search_params['amount_max']))
                
                if search_params.get('type'):
                    sql += " AND type = %s"
                    params.append(search_params['type'])
                
                if search_params.get('vehicle_id'):
                    sql += " AND vehicle_id = %s"
                    params.append(int(search_params['vehicle_id']))
                
                if search_params.get('charging_station_id'):
                    sql += " AND charging_station_id = %s"
                    params.append(int(search_params['charging_station_id']))
                
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
                expenses = cursor.fetchall()
                
                # 计算总页数
                total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
                
                return {
                    'expenses': expenses,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'current_page': page,
                    'per_page': per_page,
                    'offset': offset
                }
        except Exception as e:
            print(f"获取支出记录失败: {str(e)}")
            return {
                'expenses': [],
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
    def get_expense_stats():
        """获取支出统计数据"""
        connection = None
        try:
            connection = pymysql.connect(**db_config)
            stats = {
                'total': 0,
                'vehicle': 0,  # 车辆相关支出
                'charging': 0, # 充电站相关支出
                'other': 0     # 其他支出
            }
            
            # 获取总支出金额
            with connection.cursor() as cursor:
                cursor.execute("SELECT SUM(amount) FROM expense")
                total = cursor.fetchone()[0]
                stats['total'] = float(total) if total else 0
            
            # 获取各类型支出
            with connection.cursor() as cursor:
                cursor.execute("SELECT type, SUM(amount) FROM expense GROUP BY type")
                for row in cursor.fetchall():
                    expense_type, amount = row
                    if expense_type == '车辆支出':
                        stats['vehicle'] = float(amount) if amount else 0
                    elif expense_type == '充电站支出':
                        stats['charging'] = float(amount) if amount else 0
                    else:  # '其他支出'
                        stats['other'] = float(amount) if amount else 0
            
            # 获取支出记录总数
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM expense")
                stats['count'] = cursor.fetchone()[0]
            
            return stats
        except Exception as e:
            print(f"获取支出统计失败: {str(e)}")
            return {
                'total': 0,
                'vehicle': 0,
                'charging': 0,
                'other': 0,
                'count': 0
            }
        finally:
            if connection:
                connection.close()

    @staticmethod
    def add_expense(amount, expense_type, vehicle_id=None, charging_station_id=None, user_id=None, date=None, description=None):
        """添加新的支出记录"""
        connection = None
        try:
            connection = pymysql.connect(**db_config)
            with connection.cursor() as cursor:
                sql = """
                INSERT INTO expense (amount, type, vehicle_id, charging_station_id, user_id, date, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(sql, (amount, expense_type, vehicle_id, charging_station_id, user_id, date, description, now, now))
                connection.commit()
                return cursor.lastrowid
        except Exception as e:
            if connection:
                connection.rollback()
            print(f"添加支出记录失败: {str(e)}")
            return None
        finally:
            if connection:
                connection.close()

    @staticmethod
    def update_expense(expense_id, amount=None, expense_type=None, vehicle_id=None, charging_station_id=None, user_id=None, date=None, description=None):
        """更新支出记录"""
        connection = None
        try:
            connection = pymysql.connect(**db_config)
            
            # 构建更新SQL
            update_fields = []
            params = []
            
            if amount is not None:
                update_fields.append("amount = %s")
                params.append(amount)
            
            if expense_type is not None:
                update_fields.append("type = %s")
                params.append(expense_type)
            
            if vehicle_id is not None:
                update_fields.append("vehicle_id = %s")
                params.append(vehicle_id)
            
            if charging_station_id is not None:
                update_fields.append("charging_station_id = %s")
                params.append(charging_station_id)
            
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
            params.append(expense_id)
            
            if not update_fields:
                return False
            
            with connection.cursor() as cursor:
                sql = f"UPDATE expense SET {', '.join(update_fields)} WHERE id = %s"
                result = cursor.execute(sql, params)
                connection.commit()
                return result > 0
        except Exception as e:
            if connection:
                connection.rollback()
            print(f"更新支出记录失败: {str(e)}")
            return False
        finally:
            if connection:
                connection.close()

    @staticmethod
    def delete_expense(expense_id):
        """删除支出记录"""
        connection = None
        try:
            connection = pymysql.connect(**db_config)
            with connection.cursor() as cursor:
                sql = "DELETE FROM expense WHERE id = %s"
                result = cursor.execute(sql, (expense_id,))
                connection.commit()
                return result > 0
        except Exception as e:
            if connection:
                connection.rollback()
            print(f"删除支出记录失败: {str(e)}")
            return False
        finally:
            if connection:
                connection.close() 