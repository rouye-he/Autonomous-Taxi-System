# 数据库配置文件
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# MySQL数据库连接配置
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '123456'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME', 'autonomous_taxi_system')
}

# SQLAlchemy数据库URI
SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
    f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False