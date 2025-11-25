@echo off
cls

REM 启动游戏后端服务器的批处理文件
REM 默认使用生产模式启动，可以避免端口冲突问题

REM 显示启动信息
echo ===================================================
echo          游戏后端服务器启动工具
echo ===================================================
echo. 
echo 选项:
echo 1. 使用生产模式启动 (推荐，无端口冲突问题)
echo 2. 使用开发模式启动 (有自动重载功能，但可能有端口冲突)
echo 3. 查看端口占用情况
echo 4. 退出
echo.

REM 读取用户选择
set /p choice=请输入选项 [1-4]: 

REM 根据用户选择执行不同操作
if %choice%==1 goto production_mode
if %choice%==2 goto development_mode
if %choice%==3 goto check_ports
if %choice%==4 goto exit

:production_mode
REM 生产模式启动
echo.
echo 正在以生产模式启动服务器...
echo 提示：生产模式下不会有端口冲突问题，但没有自动重载功能。
echo 如果需要修改代码后自动重启，请选择开发模式。
echo.

REM 修改game_backend.py中的server_mode为production
powershell -Command "(Get-Content game_backend.py) -replace 'server_mode = "development"', 'server_mode = "production"' | Set-Content game_backend.py"

REM 启动服务器
python game_backend.py
goto end

:development_mode
REM 开发模式启动
echo.
echo 正在以开发模式启动服务器...
echo 注意：开发模式下Flask会启动两个进程，可能会出现端口冲突警告。
echo 这是正常现象，服务器仍然可以正常运行。
echo.

REM 修改game_backend.py中的server_mode为development
powershell -Command "(Get-Content game_backend.py) -replace 'server_mode = "production"', 'server_mode = "development"' | Set-Content game_backend.py"

REM 启动服务器
python game_backend.py
goto end

:check_ports
REM 检查端口占用情况
echo.
echo 检查端口10001和10002的占用情况...
echo.

powershell -Command "Get-NetTCPConnection -LocalPort 10001,10002 | Select-Object LocalPort, RemotePort, State, OwningProcess | Format-Table -AutoSize"
echo.
echo 如果要释放被占用的端口，请关闭占用该端口的程序。
echo 可以使用任务管理器结束占用端口的进程（通过PID）。
echo.
pause
goto exit

:exit
echo.
echo 程序已退出。
goto end

:end
REM 结束
pause