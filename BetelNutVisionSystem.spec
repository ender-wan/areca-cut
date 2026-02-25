# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller配置文件 - 槟榔视觉检测系统
用于创建独立的Windows可执行文件，隐藏源代码
"""

import sys
from pathlib import Path

# 项目根目录
project_dir = Path.cwd()

# 海康SDK路径(通常在C盘Program Files下)
import os
hikvision_sdk_path = r'C:\Program Files (x86)\MVS\Development\Bin\win64'
if not os.path.exists(hikvision_sdk_path):
    hikvision_sdk_path = r'C:\Program Files\MVS\Development\Bin\win64'

block_cipher = None

# 收集所有需要的数据文件
# 注意：config.json不打包进exe，而是在打包后复制到exe同目录，方便现场修改
datas = [
    ('models/obb_best_m.pt', 'models'),  # 只打包必需的模型文件（减小体积）
    ('MvImport', 'MvImport'),  # 海康SDK必须打包
    # config.json 不打包（见build.bat复制步骤）
    # test_img 不打包到生产环境（减小体积）
]

# 收集所有隐藏导入
hiddenimports = [
    # 基础模块（确保在打包环境中可用）
    'sys',
    'os',
    'traceback',
    'logging',
    'logging.handlers',
    # 项目内部模块（这些会被自动编译进exe）
    'main_window',
    'config',
    'config_manager',  # 配置管理器（必须）
    'plc_manager',
    'camera_worker',
    'vision_detector',
    'mock_plc',
    'mock_camera',
    'hikvision_camera',
    'logger_config',  # 日志配置模块
    # PyQt5 完整导入（必须包含所有子模块）
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui', 
    'PyQt5.QtWidgets',
    'PyQt5.QtPrintSupport',
    'PyQt5.QtNetwork',
    'sip',  # PyQt5依赖的sip模块
    # OpenCV
    'cv2',
    'numpy',
    # PyTorch 和 YOLO
    'torch',
    'torch._C',
    'torch._six',
    'torchvision',
    'ultralytics',
    'ultralytics.nn',
    'ultralytics.nn.modules',
    'ultralytics.models',
    'ultralytics.models.yolo',
    'ultralytics.engine',
    'ultralytics.engine.predictor',
    # Modbus（使用modbus_tk，不是pymodbus）
    'modbus_tk',
    'modbus_tk.modbus',
    'modbus_tk.modbus_tcp',
    'modbus_tk.defines',
    'serial',  # modbus_tk依赖pyserial
    # PIL
    'PIL',
    'PIL.Image',
    # 其他
    'yaml',
    'scipy',
    'matplotlib',
]

a = Analysis(
    [
        'run.py',
        'main_window.py',
        'config.py',
        'plc_manager.py',
        'camera_worker.py',
        'vision_detector.py',
        'mock_plc.py',
        'mock_camera.py',
        'hikvision_camera.py',
        'logger_config.py',
    ],
    pathex=[str(project_dir)],  # 添加项目根目录到搜索路径
    binaries=[
        # 海康SDK DLL文件 (如果存在则打包)
        (os.path.join(hikvision_sdk_path, 'MvCameraControl.dll'), '.'),
    ] if os.path.exists(hikvision_sdk_path) else [],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib.tests',
        'numpy.tests',
        'pytest',
        'tkinter',
        'tensorboard',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

# 目录模式：exe + 依赖库文件夹
# 优点：后续更新只需替换小的exe文件（约10-50MB），不需要替换整个依赖库（500MB+）
exe = EXE(
    pyz,
    a.scripts,
    [],  # 不包含binaries（放到COLLECT中）
    exclude_binaries=True,  # 关键：排除二进制文件，单独放在文件夹
    name='BetelNutVisionSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 禁用UPX压缩（避免与加密锁冲突）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if Path('icon.ico').exists() else None,
)

# 收集所有文件到dist目录
coll = COLLECT(
    exe,
    a.binaries,  # 所有DLL和依赖库
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='BetelNutVisionSystem',  # 输出文件夹名
)
