@echo off
REM 快速测试打包后的exe

echo.
echo ========================================
echo 测试打包后的exe文件
echo ========================================
echo.

cd /d "%~dp0"

if not exist "dist\BetelNutVisionSystem\BetelNutVisionSystem.exe" (
    echo 错误: 找不到 dist\BetelNutVisionSystem\BetelNutVisionSystem.exe
    echo 请先执行打包！
    pause
    exit /b 1
)

echo [1/4] 检查文件结构...
echo.
dir "dist\BetelNutVisionSystem" /b
echo.

echo [2/4] 检查模型文件...
if exist "dist\BetelNutVisionSystem\models\obb_best_m.pt" (
    echo     ✓ 模型文件存在
    for %%A in ("dist\BetelNutVisionSystem\models\obb_best_m.pt") do echo     大小: %%~zA 字节
) else (
    echo     ✗ 模型文件不存在！
)
echo.

echo [3/4] 检查_internal文件夹...
if exist "dist\BetelNutVisionSystem\_internal" (
    echo     ✓ _internal文件夹存在
) else (
    echo     ✗ _internal文件夹不存在！
)
echo.

echo [4/4] 运行exe测试（按Ctrl+C停止）...
echo ========================================
echo.
cd "dist\BetelNutVisionSystem"
start BetelNutVisionSystem.exe

echo.
echo exe已启动，请检查：
echo 1. 窗口是否正常显示
echo 2. 查看 logs 文件夹中的日志
echo 3. 检查是否有错误
echo.

pause
