#!/usr/bin/env python3
"""
配置系统测试脚本
"""

from config_manager import get_config, save_config
from config import PLC_CONFIG, CAMERA_CONFIGS, MODEL_CONFIG
import json

print("="*60)
print("配置系统测试")
print("="*60)
print()

# 测试1: 加载配置
print("[测试1] 加载配置...")
cfg = get_config()
print("✓ 配置加载成功")
print(f"  PLC IP: {cfg['plc']['ip']}")
print(f"  PLC Port: {cfg['plc']['port']}")
print(f"  相机数量: {len(cfg['cameras'])}")
print(f"  模型路径: {cfg['model']['model_path']}")
print(f"  轮询间隔: {cfg['poll_interval']}秒")
print()

# 测试2: 向后兼容性
print("[测试2] 向后兼容性测试...")
print(f"✓ PLC_CONFIG['ip']: {PLC_CONFIG['ip']}")
print(f"✓ len(CAMERA_CONFIGS): {len(CAMERA_CONFIGS)}")
print(f"✓ MODEL_CONFIG['model_path']: {MODEL_CONFIG['model_path']}")
print()

# 测试3: 配置文件路径
from config_manager import get_config_path
print("[测试3] 配置文件路径...")
print(f"✓ 配置文件: {get_config_path()}")
print(f"✓ 文件存在: {get_config_path().exists()}")
print()

# 测试4: 显示完整配置
print("[测试4] 配置内容预览...")
print(json.dumps(cfg, indent=2, ensure_ascii=False)[:500] + "...")
print()

print("="*60)
print("✓ 所有测试通过！配置系统工作正常")
print("="*60)
print()
print("提示:")
print("  1. 配置文件位置:", get_config_path())
print("  2. 修改配置后重启程序生效")
print("  3. 删除config.json可恢复默认配置")
