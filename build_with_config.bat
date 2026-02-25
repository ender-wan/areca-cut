@echo off
REM 槟榔视觉系统 - 使用虚拟环境打包脚本
REM 打包后config.json放在exe同目录，方便现场修改配置

echo ========================================
echo 槟榔视觉检测系统 - 生产环境打包
echo ========================================
echo.

cd /d "%~dp0"

REM 1. 清理旧文件
echo [1/5] 清理旧的打包文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo ✓ 清理完成
echo.

REM 2. 使用虚拟环境打包
echo [2/5] 使用虚拟环境的Python进行打包...
.\venv\Scripts\python.exe -m PyInstaller BetelNutVisionSystem.spec --clean
if %ERRORLEVEL% neq 0 (
    echo ✗ 打包失败！
    pause
    exit /b 1
)
echo ✓ 打包完成
echo.

REM 3. 复制配置文件到dist目录
echo [3/5] 复制配置文件...
copy /y config.json dist\BetelNutVisionSystem\
echo ✓ 配置文件已复制
echo.

REM 4. 创建配置说明
echo [4/5] 创建使用说明...
copy /y CONFIG_GUIDE.md dist\BetelNutVisionSystem\
copy /y PACKAGING_FIXES.md dist\BetelNutVisionSystem\
echo ✓ 说明文档已复制
echo.

REM 5. 显示结果
echo [5/5] 打包结果:
echo.
cd dist\BetelNutVisionSystem
dir /a BetelNutVisionSystem.exe config.json
cd ..\..
echo.

echo ========================================
echo ✓ 打包成功！
echo ========================================
echo.
echo 输出目录: dist\BetelNutVisionSystem\
echo.
echo 包含文件:
echo   - BetelNutVisionSystem.exe (约26MB)
echo   - _internal\ (依赖库，约500MB)
echo   - config.json (配置文件，可直接修改)
echo   - CONFIG_GUIDE.md (配置说明)
echo.
echo 后续更新只需替换exe文件（26MB），
echo 配置文件保持不变，无需重新打包！
echo.

pause
