# WSGI 入口，供 Gunicorn 在 Render 上使用
from app import create_app

app = create_app()
