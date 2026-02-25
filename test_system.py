#!/usr/bin/env python3
"""
快速测试脚本 - 验证系统基础功能
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("槟榔视觉检测系统 - 快速测试")
print("=" * 60)
print()

# 1. 测试导入
print("1. 测试模块导入...")
try:
    from config import CAMERA_CONFIGS, PLC_CONFIG
    from plc_manager import PlcManager
    from vision_detector import VisionDetector, DetectionResult
    from camera_worker import CameraWorker
    print("   ✓ 所有模块导入成功")
except ImportError as e:
    print(f"   ✗ 导入失败: {e}")
    sys.exit(1)

# 2. 测试配置
print("\n2. 测试配置...")
print(f"   PLC地址: {PLC_CONFIG['ip']}:{PLC_CONFIG['port']}")
print(f"   相机数量: {len(CAMERA_CONFIGS)}")
print("   ✓ 配置加载成功")

# 3. 测试PLC连接
print("\n3. 测试PLC连接...")
plc = PlcManager()
if plc.connect():
    print("   ✓ PLC连接成功 (Mock模式)")
    
    # 测试读写
    plc.write_holding_register(100, 123)
    value = plc.read_holding_register(100)
    if value == 123:
        print("   ✓ PLC读写测试通过")
    else:
        print(f"   ✗ PLC读写测试失败: 期望123, 实际{value}")
    
    plc.disconnect()
else:
    print("   ✗ PLC连接失败")

# 4. 测试相机Mock
print("\n4. 测试Mock相机...")
try:
    from mock_camera import MockCamera
    import numpy as np
    
    cam = MockCamera("192.168.1.110")
    cam.connect()
    image = cam.capture()
    
    if isinstance(image, np.ndarray):
        print(f"   ✓ 拍照成功: 图像尺寸 {image.shape}")
    else:
        print("   ✗ 拍照失败")
    
    cam.disconnect()
except Exception as e:
    print(f"   ✗ 相机测试失败: {e}")

# 5. 测试视觉算法
print("\n5. 测试视觉检测...")
try:
    detector = VisionDetector()
    
    # 创建测试图像
    test_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
    result = detector.detect_betel_nut(test_image)
    
    print(f"   ✓ 检测成功")
    print(f"     - 分类: {result.classification}")
    print(f"     - 置信度: {result.confidence:.2f}")
    print(f"     - 坐标: ({result.x_offset:.1f}, {result.y_offset:.1f})")
    print(f"     - 角度: {result.r_angle:.1f}°")
    
except Exception as e:
    print(f"   ✗ 检测失败: {e}")

# 6. 检查GUI依赖
print("\n6. 检查GUI依赖...")
try:
    from PyQt6.QtWidgets import QApplication
    print("   ✓ PyQt6已安装")
except ImportError:
    print("   ✗ PyQt6未安装")
    print("     请运行: pip install PyQt6")

print("\n" + "=" * 60)
print("测试完成！")
print()
print("下一步:")
print("  1. 安装依赖: pip install -r requirements.txt")
print("  2. 运行系统: python run.py")
print("  3. 或使用快捷脚本: ./start.sh (macOS/Linux) 或 start.bat (Windows)")
print("=" * 60)
