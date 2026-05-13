@echo off
title 校园二手集市
echo ========================================
echo   校园二手集市 v1.3
echo ========================================
echo.

rem Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

rem Check dependencies
echo [检测] 依赖库...
python -c "import flask,flask_cors" 2>nul
if %errorlevel% neq 0 (
    echo [安装] 正在安装 Flask + flask-cors ...
    pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org flask flask-cors
)

rem Open browser
start http://127.0.0.1:18800

rem Start server
cd /d "%~dp0backend"
echo.
echo [启动] 服务地址: http://127.0.0.1:18800
echo [提示] 按 Ctrl+C 停止
echo.
python server.py
pause
