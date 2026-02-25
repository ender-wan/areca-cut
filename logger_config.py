"""
日志配置模块
提供统一的日志记录功能，记录到文件和控制台
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import traceback


def setup_logger(name='BetelNutVision', log_file=None, level=logging.INFO):
    """
    配置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径，None则自动生成
        level: 日志级别
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 获取日志文件路径
    if log_file is None:
        # 支持PyInstaller打包
        if getattr(sys, 'frozen', False):
            # 打包后，日志保存在exe同目录
            log_dir = Path(sys.executable).parent / 'logs'
        else:
            # 开发环境
            log_dir = Path(__file__).parent / 'logs'
        
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'system_{timestamp}.log'
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 确保子logger继承父logger的设置
    logger.propagate = True
    
    # 清除已有的处理器
    logger.handlers.clear()
    
    # 同时配置根logger，确保所有子logger都能输出
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        root_logger.addHandler(file_handler)  # 同时添加到根logger
        print(f"✓ 日志文件: {log_file}")
    except Exception as e:
        print(f"✗ 警告: 无法创建日志文件 {log_file}: {e}")
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    root_logger.addHandler(console_handler)  # 同时添加到根logger
    
    print(f"✓ 日志系统初始化完成")
    return logger


def log_exception(logger, exc_type, exc_value, exc_traceback):
    """
    记录未捕获的异常
    
    Args:
        logger: 日志记录器
        exc_type: 异常类型
        exc_value: 异常值
        exc_traceback: 异常追踪
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # 忽略Ctrl+C
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.critical("未捕获的异常:", exc_info=(exc_type, exc_value, exc_traceback))
    logger.critical("程序异常退出")


def setup_global_exception_handler(logger):
    """
    设置全局异常处理器
    
    Args:
        logger: 日志记录器
    """
    def exception_handler(exc_type, exc_value, exc_traceback):
        log_exception(logger, exc_type, exc_value, exc_traceback)
    
    sys.excepthook = exception_handler
