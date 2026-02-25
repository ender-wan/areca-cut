@echo off
REM Windows 快速启动脚本

echo ==========================================
echo  槟榔视觉检测与切割定位系统
echo  Betel Nut Vision Detection System
echo ==========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python
    pause
    exit /b 1
)

echo Python版本:
python --version
echo.

echo 启动系统...
python run.py

pause
