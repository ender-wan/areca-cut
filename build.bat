@echo off
REM Windows打包脚本 - 一键打包
REM 使用PyInstaller创建独立可执行文件

echo ======================================
echo 槟榔视觉检测系统 - Windows打包工具
echo ======================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python
    pause
    exit /b 1
)

REM 安装PyInstaller
echo 正在检查PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 正在安装PyInstaller...
    pip install pyinstaller
)

REM 清理旧的构建文件
echo.
echo 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 使用spec文件打包
echo.
echo 开始打包（这可能需要几分钟）...
echo.
pyinstaller BetelNutVisionSystem.spec

REM 检查打包结果
if exist dist\BetelNutVisionSystem.exe (
    echo.
    echo ======================================
    echo 打包成功！
    echo ======================================
    echo.
    echo 可执行文件位置: dist\BetelNutVisionSystem.exe
    echo.
    echo 说明:
    echo 1. 将 dist 文件夹复制到目标电脑
    echo 2. 双击 BetelNutVisionSystem.exe 运行
    echo 3. 源代码已隐藏，无法查看
    echo.
    
    REM 复制必要文件到dist目录
    echo 复制配置文件到发布目录...
    copy config.json dist\BetelNutVisionSystem\ >nul 2>&1
    if not exist dist\BetelNutVisionSystem\config.json (
        echo 警告: config.json 复制失败
    ) else (
        echo   成功: config.json
    )
    
    REM 创建README
    echo 创建发布说明...
    python create_release_readme.py
    
    echo.
    echo 完成！按任意键退出...
    pause >nul
) else (
    echo.
    echo ======================================
    echo 打包失败！
    echo ======================================
    echo.
    echo 请检查错误信息
    pause
    exit /b 1
)
