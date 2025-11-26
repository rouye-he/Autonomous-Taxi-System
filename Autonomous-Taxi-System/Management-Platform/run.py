"""
无人驾驶出租车管理平台启动脚本
"""
from app import create_app, socketio
import argparse
import sys
import os
import logging

# 配置日志
def configure_logging(log_level=logging.WARNING):
    # 设置Werkzeug的日志级别 (Werkzeug是Flask使用的WSGI库，负责产生HTTP请求日志)
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(log_level)
    
    # 设置Flask的日志级别
    flask_logger = logging.getLogger('flask')
    flask_logger.setLevel(log_level)
    
    # 设置SocketIO的日志级别
    socketio_logger = logging.getLogger('socketio')
    socketio_logger.setLevel(log_level)
    engineio_logger = logging.getLogger('engineio')
    engineio_logger.setLevel(log_level)
    

    if log_level <= logging.INFO:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        werkzeug_logger.addHandler(handler)
        flask_logger.addHandler(handler)

if __name__ == '__main__':

    # 检查templates目录
    templates_path = os.path.join(os.getcwd(), 'app', 'templates')

    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='启动无人驾驶出租车管理平台')
    parser.add_argument('--host', default=os.getenv('HOST', '127.0.0.1'), help='监听IP地址')
    parser.add_argument('--port', type=int, default=int(os.getenv('PORT', 5000)), help='监听端口')
    parser.add_argument('--debug', action='store_true', default=os.getenv('DEBUG', 'False').lower() == 'true', help='开启调试模式')
    parser.add_argument('--init-test-data', action='store_true', help='初始化测试数据')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        default='WARNING', help='日志级别')
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = getattr(logging, args.log_level)
    configure_logging(log_level)
    
    # 如果有init-test-data参数，添加到sys.argv中以便app/__init__.py中的函数能够检测到
    if args.init_test_data and '--init-test-data' not in sys.argv:
        sys.argv.append('--init-test-data')
    
    # 创建应用 - 不再传递init_test_data参数
    app = create_app()
    


    
    # 使用socketio.run代替app.run,关闭日志输出
    socketio.run(app, host=args.host, port=args.port, debug=args.debug, log_output=False, allow_unsafe_werkzeug=True) 