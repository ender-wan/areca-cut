# Windows打包说明

## 如何打包

### 方法1: 使用批处理脚本（推荐）

1. 确保已安装Python环境和所有依赖
2. 双击运行 `build.bat`
3. 等待打包完成（可能需要5-10分钟）
4. 打包结果在 `dist` 文件夹

### 方法2: 手动打包

```bash
# 安装PyInstaller
pip install pyinstaller

# 使用spec文件打包
pyinstaller BetelNutVisionSystem.spec

# 或使用Python脚本
python build_package.py
```

## 打包文件说明

- `BetelNutVisionSystem.spec` - PyInstaller配置文件
- `build.bat` - Windows一键打包脚本
- `build_package.py` - Python打包脚本
- `create_release_readme.py` - 生成发布说明

## 打包后的文件结构

```
dist/
├── BetelNutVisionSystem.exe    # 主程序（包含所有Python代码）
├── config.py                    # 配置文件（可编辑）
├── models/                      # 模型文件夹
│   └── betel_nut_obb_best.pt   # YOLO模型
├── test_img/                    # 测试图片
├── MvImport/                    # 海康SDK
└── README_发布说明.txt          # 用户手册
```

## 源代码保护

使用PyInstaller打包后：
- 所有Python源代码被编译成字节码并嵌入exe
- 无法直接查看或修改源代码
- 反编译非常困难且违法

## 分发说明

1. 将整个 `dist` 文件夹打包成zip
2. 分发给用户
3. 用户解压后直接运行exe即可

## 注意事项

1. **首次打包较慢** - PyInstaller需要分析所有依赖
2. **文件较大** - 包含完整的Python环境和所有库（约2-3GB）
3. **杀毒软件** - 可能被误报，需要添加白名单
4. **CUDA支持** - 如果打包机器有GPU，打包的exe也会包含CUDA库

## GPU版本 vs CPU版本

### GPU版本（当前）
- 包含CUDA 12.4支持
- 文件更大（约3GB）
- 需要目标机器有NVIDIA GPU
- 可以在无GPU机器上运行（自动降级CPU）

### CPU版本
修改requirements.txt，卸载torch+cu124，安装torch+cpu：
```bash
pip uninstall torch torchvision -y
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pyinstaller BetelNutVisionSystem.spec
```

## 测试打包结果

在另一台干净的Windows机器上测试：
1. 确保目标机器没有安装Python
2. 复制dist文件夹
3. 运行exe
4. 验证所有功能正常

## 常见问题

### Q: 打包时提示找不到模块
A: 在spec文件的hiddenimports中添加该模块

### Q: exe启动慢
A: 正常现象，首次启动需要解压临时文件

### Q: 杀毒软件拦截
A: 添加exe到白名单，或使用数字签名

### Q: 打包后文件太大
A: 
- 删除不需要的库
- 使用UPX压缩（已启用）
- 使用--onedir模式而不是--onefile
