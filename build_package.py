"""
Windows打包脚本 - 使用PyInstaller打包成独立可执行文件
隐藏源代码，可在任何Windows电脑上运行
"""

import os
import sys
import shutil
from pathlib import Path

def build_package():
    """构建Windows可执行包"""
    
    print("="*60)
    print("槟榔视觉检测系统 - Windows打包工具")
    print("="*60)
    
    # 1. 检查PyInstaller是否安装
    try:
        import PyInstaller
        print("✓ PyInstaller已安装")
    except ImportError:
        print("✗ PyInstaller未安装，正在安装...")
        os.system("pip install pyinstaller")
    
    # 2. 准备打包参数
    app_name = "BetelNutVisionSystem"
    main_script = "run.py"
    icon_path = "icon.ico" if os.path.exists("icon.ico") else None
    
    # 3. 构建PyInstaller命令
    cmd_parts = [
        "pyinstaller",
        "--name", app_name,
        "--onefile",  # 打包成单个exe文件
        "--windowed",  # 无控制台窗口（GUI程序）
        "--clean",  # 清理临时文件
    ]
    
    # 添加图标
    if icon_path:
        cmd_parts.extend(["--icon", icon_path])
    
    # 添加数据文件
    data_files = [
        ("config.py", "."),
        ("models", "models"),  # 包含模型文件夹
        ("test_img", "test_img"),  # 包含测试图片
        ("MvImport", "MvImport"),  # 海康SDK
    ]
    
    for src, dst in data_files:
        if os.path.exists(src):
            cmd_parts.extend(["--add-data", f"{src};{dst}"])
    
    # 添加隐藏导入
    hidden_imports = [
        "PyQt5",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "cv2",
        "numpy",
        "torch",
        "ultralytics",
        "pymodbus",
        "PIL",
    ]
    
    for module in hidden_imports:
        cmd_parts.extend(["--hidden-import", module])
    
    # 4. 添加主脚本
    cmd_parts.append(main_script)
    
    # 5. 执行打包
    print("\n开始打包...")
    print("命令:", " ".join(cmd_parts))
    print()
    
    result = os.system(" ".join(cmd_parts))
    
    if result == 0:
        print("\n" + "="*60)
        print("✓ 打包成功！")
        print("="*60)
        print(f"\n可执行文件位置: dist\\{app_name}.exe")
        print("\n说明:")
        print("1. 将 dist 文件夹中的所有文件复制到目标电脑")
        print("2. 双击 {}.exe 即可运行".format(app_name))
        print("3. 源代码已隐藏在exe文件中，无法反编译查看")
        print("\n注意:")
        print("- 目标电脑需要安装CUDA 12.4（如果使用GPU）")
        print("- 或者修改代码使用CPU模式")
        print()
        
        # 创建发布说明
        create_release_notes(app_name)
    else:
        print("\n✗ 打包失败！")
        print("请检查错误信息并重试")
    
    return result == 0


def create_release_notes(app_name):
    """创建发布说明文件"""
    
    release_notes = f"""
# {app_name} - 发布说明

## 系统要求

- Windows 10/11 (64位)
- NVIDIA GPU（推荐，支持CUDA 12.4）
- 最低 8GB 内存
- 显示器分辨率 1920x1080 或更高

## 安装步骤

1. 解压整个文件夹到任意位置
2. 双击运行 `{app_name}.exe`

## GPU支持

如果你有NVIDIA显卡并想使用GPU加速：
1. 安装 NVIDIA CUDA 12.4
2. 下载地址：https://developer.nvidia.com/cuda-downloads

如果没有GPU或CUDA，程序会自动使用CPU模式（速度较慢）

## 功能说明

### 三种运行模式

1. **真实硬件模式**
   - 连接海康工业相机
   - 连接PLC（Modbus TCP）
   - 实时采集和检测

2. **测试模式**
   - 使用test_img文件夹中的图片
   - Mock PLC模拟
   - 用于离线测试

3. **演示模式**
   - 所有硬件都使用Mock
   - 随机生成数据
   - 用于展示和培训

### 配置文件

编辑 `config.py` 修改配置：
- PLC IP地址和端口
- 相机IP地址
- 触发寄存器地址
- Mock模式开关

## 故障排除

### 程序无法启动
- 检查是否有杀毒软件拦截
- 以管理员权限运行

### 检测速度慢
- 检查是否使用了GPU
- 关闭其他占用资源的程序

### 相机无法连接
- 检查相机IP是否正确
- 确认网络连接
- 或使用Mock模式测试

## 联系支持

如有问题，请联系技术支持

---
版本: 1.0.0
构建日期: {Path.cwd()}
"""
    
    with open("dist/README_发布说明.txt", "w", encoding="utf-8") as f:
        f.write(release_notes)
    
    print("✓ 发布说明已创建: dist/README_发布说明.txt")


if __name__ == "__main__":
    success = build_package()
    sys.exit(0 if success else 1)
