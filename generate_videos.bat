@echo off

REM 检查是否已安装Python
where python >nul 2>nul
if %errorlevel% neq 0 (
echo Python is not installed. Please install Python and try again.
pause
exit /b 1
)

REM 安装所需的依赖包
echo Installing required packages...
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
echo Failed to install required packages. Please check your internet connection and try again.
pause
exit /b 1
)

REM 运行数据可视化脚本
echo Generating videos...
python cloud\visualization\data_visualizer.py

if %errorlevel% neq 0 (
echo Failed to generate videos.
pause
exit /b 1
)

echo All videos have been successfully generated!
echo Videos are saved in the 'output_videos' directory.
pause