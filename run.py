#!/usr/bin/env python3
"""
槟榔视觉检测与切割定位系统 - 启动脚本
Betel Nut Vision Detection and Cutting System
"""

import sys
import os
import traceback

# 处理打包后的路径
if getattr(sys, 'frozen', False):
    # 如果是打包后的exe
    application_path = os.path.dirname(sys.executable)
    # 切换到exe所在目录
    os.chdir(application_path)
else:
    # 如果是源码运行
    application_path = os.path.dirname(os.path.abspath(__file__))

# 添加当前目录到Python路径
sys.path.insert(0, application_path)

# 导入日志配置
from logger_config import setup_logger, setup_global_exception_handler

# 设置日志
logger = setup_logger('BetelNutVision')
setup_global_exception_handler(logger)

logger.info("="*60)
logger.info("槟榔视觉检测与切割定位系统启动")
logger.info("="*60)
logger.info(f"Python版本: {sys.version}")
logger.info(f"工作目录: {os.getcwd()}")

try:
    from main_window import main
    logger.info("导入主窗口模块成功")
    
    logger.info("启动主程序...")
    main()
    
except Exception as e:
    logger.critical("程序启动失败!")
    logger.critical(f"错误类型: {type(e).__name__}")
    logger.critical(f"错误信息: {str(e)}")
    logger.critical("详细错误追踪:")
    logger.critical(traceback.format_exc())
    
    # 显示错误对话框
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox
        app = QApplication.instance() or QApplication(sys.argv)
        
        error_msg = f"""程序启动失败！

错误类型: {type(e).__name__}
错误信息: {str(e)}

详细信息已记录到日志文件。
请查看 logs 文件夹中的日志文件。"""
        
        QMessageBox.critical(None, "启动错误", error_msg)
    except:
        print(f"\n\n!!! 严重错误 !!!\n{traceback.format_exc()}")
    
    sys.exit(1)
