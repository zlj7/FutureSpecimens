@echo off

REM 检查是否已安装Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查是否已安装pip
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 未找到pip，请先安装pip
    pause
    exit /b 1
)

REM 安装依赖
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 依赖安装失败
    pause
    exit /b 1
)

REM 启动远程服务器
python remote_backend.py

pause