"""
配置管理器 - 支持外部配置文件
从exe同目录的config.json读取配置，方便现场修改
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


def get_exe_dir() -> Path:
    """
    获取exe所在目录
    
    Returns:
        Path: exe所在目录路径
    """
    if getattr(sys, 'frozen', False):
        # 打包后：exe所在目录
        return Path(sys.executable).parent
    else:
        # 开发环境：当前文件所在目录
        return Path(__file__).parent


def get_config_path() -> Path:
    """获取配置文件路径"""
    return get_exe_dir() / 'config.json'


def get_default_config() -> Dict[str, Any]:
    """
    获取默认配置
    
    Returns:
        Dict: 默认配置字典
    """
    return {
        "plc": {
            "ip": "192.168.3.10",
            "port": 502,
            "timeout": 3.0,
            "unit_id": 1
        },
        "pc": {
            "ip": "192.168.3.30"
        },
        "cameras": [
            {
                "id": i + 1,
                "name": f"Camera {i + 1}",
                "ip": f"192.168.1.{10 + i}",
                "pixel_to_mm": 0.1,
                "registers": {
                    "trigger": 100 + i * 10,
                    "class": 101 + i * 10,
                    "x_offset": 102 + i * 10,
                    "y_offset": 103 + i * 10,
                    "r_angle": 104 + i * 10,
                    "height": 105 + i * 10,
                    "head_direction": 106 + i * 10,
                    "length": 107 + i * 10
                }
            }
            for i in range(8)
        ],
        "trigger_values": {
            "READY": 10,
            "PROCESSING": 127,
            "IMAGE_READY": 128
        },
        "class_values": {
            "UNKNOWN": 1,
            "CUTTABLE": 2,
            "RESERVED": 3
        },
        "camera_params": {
            "exposure": 5000,
            "gain": 10,
            "width": 1920,
            "height": 1080,
            "timeout": 5000
        },
        "model": {
            "model_path": "models/obb_best_m.pt",
            "device": "auto"
        },
        "poll_interval": 0.1,
        "log": {
            "max_lines": 1000,
            "log_file": "system.log"
        }
    }


def save_config(config: Dict[str, Any], config_path: Path = None) -> bool:
    """
    保存配置到JSON文件
    
    Args:
        config: 配置字典
        config_path: 配置文件路径，None则使用默认路径
        
    Returns:
        bool: 保存成功返回True
    """
    if config_path is None:
        config_path = get_config_path()
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info(f"配置已保存到: {config_path}")
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        return False


def load_config(config_path: Path = None) -> Dict[str, Any]:
    """
    加载配置文件，不存在则创建默认配置
    
    Args:
        config_path: 配置文件路径，None则使用默认路径
        
    Returns:
        Dict: 配置字典
    """
    if config_path is None:
        config_path = get_config_path()
    
    # 如果配置文件不存在，创建默认配置
    if not config_path.exists():
        logger.info(f"配置文件不存在，创建默认配置: {config_path}")
        default_config = get_default_config()
        save_config(default_config, config_path)
        return default_config
    
    # 加载现有配置
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"配置已从文件加载: {config_path}")
        return config
    except Exception as e:
        logger.error(f"加载配置失败: {e}，使用默认配置")
        return get_default_config()


# 全局配置实例
_config_instance = None


def get_config() -> Dict[str, Any]:
    """
    获取全局配置实例（单例模式）
    
    Returns:
        Dict: 配置字典
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = load_config()
    return _config_instance


def reload_config():
    """重新加载配置"""
    global _config_instance
    _config_instance = load_config()
    logger.info("配置已重新加载")


# 兼容旧代码的配置变量（从JSON配置中读取）
def _load_legacy_vars():
    """为兼容性加载旧的配置变量"""
    cfg = get_config()
    
    return {
        'PLC_CONFIG': cfg['plc'],
        'PC_CONFIG': cfg['pc'],
        'CAMERA_CONFIGS': cfg['cameras'],
        'TRIGGER_VALUES': cfg['trigger_values'],
        'CLASS_VALUES': cfg['class_values'],
        'CAMERA_PARAMS': cfg['camera_params'],
        'MODEL_CONFIG': cfg['model'],
        'POLL_INTERVAL': cfg['poll_interval'],
        'LOG_CONFIG': cfg['log']
    }


# 初始化时加载配置
_legacy_vars = _load_legacy_vars()
PLC_CONFIG = _legacy_vars['PLC_CONFIG']
PC_CONFIG = _legacy_vars['PC_CONFIG']
CAMERA_CONFIGS = _legacy_vars['CAMERA_CONFIGS']
TRIGGER_VALUES = _legacy_vars['TRIGGER_VALUES']
CLASS_VALUES = _legacy_vars['CLASS_VALUES']
CAMERA_PARAMS = _legacy_vars['CAMERA_PARAMS']
MODEL_CONFIG = _legacy_vars['MODEL_CONFIG']
POLL_INTERVAL = _legacy_vars['POLL_INTERVAL']
LOG_CONFIG = _legacy_vars['LOG_CONFIG']
