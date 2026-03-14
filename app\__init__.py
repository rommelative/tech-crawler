# Flask 应用初始化

from flask import Flask
from app.routes import api_bp


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = 'tech-crawler-secret-key-2024'
    app.config['JSON_AS_ASCII'] = False  # 解决中文显示问题
    
    # 注册蓝图
    app.register_blueprint(api_bp)
    
    return app
