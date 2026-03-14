@echo off
chcp 65001 >nul
echo ========================================
echo    科技资讯聚合平台 - 启动器
echo ========================================
echo.

echo [1/3] 检查并安装依赖...
pip install -r requirements.txt

echo.
echo [2/3] 启动应用...
echo 应用启动后，请浏览器访问: http://localhost:5001
echo.
echo 如需停止，请按 Ctrl+C
echo ========================================

python run.py

pause
