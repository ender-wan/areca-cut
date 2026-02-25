@echo off
REM ========================================
REM 槟榔视觉系统 - 生产环境打包脚本
REM 目录模式：exe + 依赖库文件夹分离
REM ========================================

echo.
echo ========================================
echo 槟榔视觉检测系统 - 生产环境打包
echo ========================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 清理旧的打包文件
echo [1/5] 清理旧的打包文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
echo     完成！
echo.

REM 检查模型文件
echo [2/5] 检查模型文件...
if not exist "models\obb_best_m.pt" (
    echo     错误: 找不到 models\obb_best_m.pt
    echo     请确保已训练并复制模型文件！
    pause
    exit /b 1
)
echo     模型文件: models\obb_best_m.pt
for %%A in ("models\obb_best_m.pt") do echo     文件大小: %%~zA 字节
echo.

REM 使用PyInstaller打包（目录模式）
echo [3/5] 开始PyInstaller打包...
echo     模式: 目录模式（exe + 依赖库分离）
pyinstaller BetelNutVisionSystem.spec --clean
if %errorlevel% neq 0 (
    echo     打包失败！
    pause
    exit /b 1
)
echo     完成！
echo.

REM 复制额外的运行时文件
echo [4/5] 复制运行时文件...
if not exist "dist\BetelNutVisionSystem\logs" mkdir "dist\BetelNutVisionSystem\logs"
copy /Y "README.md" "dist\BetelNutVisionSystem\" >nul 2>&1
echo     完成！
echo.

REM 显示打包结果
echo [5/5] 打包完成！
echo.
echo ========================================
echo 打包结果:
echo ========================================
echo 输出目录: dist\BetelNutVisionSystem\
echo.

REM 显示exe信息
echo exe文件: BetelNutVisionSystem.exe

REM 计算总大小
echo.
echo 依赖库文件夹: _internal\ (包含所有DLL和依赖)
echo 模型文件: models\obb_best_m.pt
echo.

echo ========================================
echo 后续更新流程:
echo ========================================
echo 1. 修改代码后，只需重新打包
echo 2. 替换客户端的 BetelNutVisionSystem.exe (约10-50MB)
echo 3. 无需替换 _internal 文件夹 (约500MB+)
echo 4. 极大减少更新文件大小！
echo ========================================
echo.

REM 创建版本信息文件
echo %date% %time% > "dist\BetelNutVisionSystem\VERSION.txt"
echo Build completed at %date% %time% >> "dist\BetelNutVisionSystem\VERSION.txt"

echo 按任意键退出...
pause >nul
