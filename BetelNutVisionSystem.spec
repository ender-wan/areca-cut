# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 配置 — 槟榔视觉检测系统（传统CV版，无需PyTorch/YOLO）
生成 dist/BetelNutVisionSystem/ 目录模式包
"""

import sys, os
from pathlib import Path

project_dir = Path.cwd()

# 海康 SDK（仅 Windows 下打包）
hikvision_sdk_path = r'C:\Program Files (x86)\MVS\Development\Bin\win64'
if not os.path.exists(hikvision_sdk_path):
    hikvision_sdk_path = r'C:\Program Files\MVS\Development\Bin\win64'

block_cipher = None

datas = [
    ('MvImport', 'MvImport'),
]

# 如果有测试图片也打包进去，方便没有相机时演示
if Path('test_img').exists():
    datas.append(('test_img', 'test_img'))

hiddenimports = [
    'main_window', 'config', 'config_manager',
    'plc_manager', 'camera_worker', 'vision_detector',
    'mock_plc', 'mock_camera', 'hikvision_camera', 'logger_config',
    'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
    'PyQt5.QtPrintSupport', 'PyQt5.QtNetwork', 'sip',
    'cv2', 'numpy',
    'modbus_tk', 'modbus_tk.modbus', 'modbus_tk.modbus_tcp',
    'modbus_tk.defines', 'serial',
]

# 海康 SDK DLL
binaries = []
mvcc_dll = os.path.join(hikvision_sdk_path, 'MvCameraControl.dll')
if os.path.exists(mvcc_dll):
    binaries.append((mvcc_dll, '.'))

a = Analysis(
    ['run.py'],
    pathex=[str(project_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch', 'torchvision', 'ultralytics',
        'matplotlib', 'scipy', 'tensorboard',
        'pytest', 'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BetelNutVisionSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='icon.ico' if Path('icon.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='BetelNutVisionSystem',
)
