"""
配置模块
包含数据库配置和其他应用程序配置
"""

from app.config.database import db_config, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS

# 基础配置类
class Config:
    """基础配置"""
    SECRET_KEY = "dev-key-please-change-in-production"
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = SQLALCHEMY_TRACK_MODIFICATIONS
    DEBUG = False
    TESTING = False

# 开发环境配置
class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    ENV = 'development'

# 测试环境配置
class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    ENV = 'testing'

# 生产环境配置
class ProductionConfig(Config):
    """生产环境配置"""
    SECRET_KEY = "production-key-should-be-set-in-environment"
    ENV = 'production'

__all__ = [
    'db_config', 
    'SQLALCHEMY_DATABASE_URI', 
    'SQLALCHEMY_TRACK_MODIFICATIONS',
    'Config',
    'DevelopmentConfig',
    'TestingConfig',
    'ProductionConfig'
] 