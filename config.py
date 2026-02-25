"""
系统配置文件 - 从外部config.json读取
Configuration for Betel Nut Vision Detection System

配置文件位置：exe同目录下的config.json
修改配置后重启程序生效，无需重新打包exe
"""

# 从配置管理器导入所有配置
from config_manager import (
    PLC_CONFIG,
    PC_CONFIG,
    CAMERA_CONFIGS,
    TRIGGER_VALUES,
    CLASS_VALUES,
    CAMERA_PARAMS,
    MODEL_CONFIG,
    POLL_INTERVAL,
    LOG_CONFIG,
    get_config,
    reload_config,
    save_config
)

# 向后兼容：保留常量定义供其他模块导入
# 注意：这些值从config.json读取，修改config.json后重启程序生效

__all__ = [
    'PLC_CONFIG',
    'PC_CONFIG',
    'CAMERA_CONFIGS',
    'TRIGGER_VALUES',
    'CLASS_VALUES',
    'CAMERA_PARAMS',
    'MODEL_CONFIG',
    'POLL_INTERVAL',
    'LOG_CONFIG',
    'get_config',
    'reload_config',
    'save_config'
]
