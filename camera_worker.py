"""
相机工作线程
CameraWorker: 处理单个相机的"轮询-拍照-计算-回写"循环
"""

import time
import logging
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from typing import Optional

from config import TRIGGER_VALUES, CLASS_VALUES, POLL_INTERVAL, CAMERA_PARAMS
from plc_manager import PlcManager
from vision_detector import VisionDetector, DetectionResult
from hikvision_camera import HikvisionCamera, ImageFolderCamera, HIKVISION_SDK_AVAILABLE

# 获取logger
logger = logging.getLogger('BetelNutVision.camera_worker')


class CameraWorker(QThread):
    """
    相机工作线程 - 独立处理单个相机的完整流程
    继承自QThread，在独立线程中运行
    """
    
    # 信号定义
    status_changed = pyqtSignal(str)           # 状态更新信号: "待机"/"拍照"/"计算"
    image_captured = pyqtSignal(np.ndarray)    # 图片捕获信号
    result_computed = pyqtSignal(object)       # 结果计算信号 (DetectionResult)
    log_message = pyqtSignal(str)              # 日志消息信号
    error_occurred = pyqtSignal(str)           # 错误信号
    
    def __init__(self, camera_config: dict, plc_manager: PlcManager):
        """
        初始化相机工作线程
        
        Args:
            camera_config: 相机配置字典（来自config.CAMERA_CONFIGS）
            plc_manager: PLC管理器实例（共享）
        """
        super().__init__()
        
        self.camera_config = camera_config
        self.camera_id = camera_config['id']
        self.camera_name = camera_config['name']
        self.camera_ip = camera_config['ip']
        self.registers = camera_config['registers']
        self.pixel_to_mm = camera_config.get('pixel_to_mm', 0.1)  # 读取相机标定参数，默认0.1
        
        self.plc = plc_manager
        self.detector = VisionDetector(
            pixel_to_mm=self.pixel_to_mm
        )
        
        self.camera = None
        self.is_running = False
        self.is_camera_connected = False
        
    def run(self):
        """
        线程主循环 - 持续轮询触发信号
        """
        self.is_running = True
        self.log_message.emit(f"{self.camera_name} 工作线程启动")
        
        # 连接相机
        if not self._connect_camera():
            self.error_occurred.emit(f"{self.camera_name} 相机连接失败")
            return
        
        self.status_changed.emit("待机")
        
        # 主循环：轮询触发寄存器
        while self.is_running:
            try:
                # 1. 读取触发寄存器
                trigger_value = self.plc.read_holding_register(self.registers['trigger'])
                
                if trigger_value == TRIGGER_VALUES['READY']:
                    # 2. 检测到触发信号 (10)
                    self.log_message.emit(f"[{self.camera_name}] ✓ 检测到触发信号 D{self.registers['trigger']}={trigger_value}")
                    self._process_trigger()
                
                # 轮询间隔
                time.sleep(POLL_INTERVAL)
                
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                self.error_occurred.emit(f"[{self.camera_name}] ✗ 运行异常: {type(e).__name__}: {str(e)}")
                logger.error(f"[{self.camera_name}] 详细错误:\n{error_detail}")
                time.sleep(1)  # 错误后延迟重试
        
        # 清理资源
        self._disconnect_camera()
        self.log_message.emit(f"{self.camera_name} 工作线程停止")
    
    def _process_trigger(self):
        """
        处理触发流程：
        1. 写入处理中状态 (127)
        2. 拍照
        3. 写入图片就绪状态 (128)
        4. 识别计算
        5. 回写结果
        """
        try:
            # Step 1: 写入"正在处理"状态
            self.log_message.emit(f"[{self.camera_name}] 步骤1/5: 写入处理状态...")
            self.status_changed.emit("拍照中")
            if not self.plc.write_holding_register(self.registers['trigger'], TRIGGER_VALUES['PROCESSING']):
                self.error_occurred.emit(f"[{self.camera_name}] ✗ 写入处理中状态失败 D{self.registers['trigger']}")
                return
            
            # Step 2: 拍照
            self.log_message.emit(f"[{self.camera_name}] 步骤2/5: 拍照...")
            image = self._capture_image()
            if image is None:
                self.error_occurred.emit(f"[{self.camera_name}] ✗ 拍照失败")
                self._write_error_result()
                return
            
            self.image_captured.emit(image)
            self.log_message.emit(f"[{self.camera_name}] ✓ 拍照成功 {image.shape[1]}x{image.shape[0]}")
            
            # Step 3: 写入"图片就绪"状态
            self.log_message.emit(f"[{self.camera_name}] 步骤3/5: 写入图片就绪状态...")
            if not self.plc.write_holding_register(self.registers['trigger'], TRIGGER_VALUES['IMAGE_READY']):
                self.error_occurred.emit(f"[{self.camera_name}] ✗ 写入图片就绪状态失败 D{self.registers['trigger']}")
                return
            
            # Step 4: 视觉识别
            self.log_message.emit(f"[{self.camera_name}] 步骤4/5: 计算检测结果...")
            self.status_changed.emit("计算中")
            result, display_image = self.detector.detect_and_draw(image)
            self.log_message.emit(f"[{self.camera_name}] ✓ 检测完成 分类={result.classification}")
            self.result_computed.emit(result)
            
            # 发送绘制后的图片（带有检测框和切割线）
            self.image_captured.emit(display_image)
            
            # Step 5: 回写结果到PLC
            self.log_message.emit(f"[{self.camera_name}] 步骤5/5: 写入PLC结果...")
            self._write_result_to_plc(result)
            
            # 回到待机状态
            self.status_changed.emit("待机")
            self.log_message.emit(f"[{self.camera_name}] ✓ 完整流程处理完成")
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.error_occurred.emit(f"[{self.camera_name}] ✗ 处理流程异常: {type(e).__name__}: {str(e)}")
            logger.error(f"[{self.camera_name}] 详细错误:\n{error_detail}")
            self._write_error_result()
            self.status_changed.emit("待机")
    
    def _connect_camera(self) -> bool:
        """
        连接相机
        
        Returns:
            bool: 连接成功返回True
            
        优先尝试连接真实海康相机，失败则使用图片测试模式
        """
        try:
            # ============ 1. 尝试连接真实海康相机 ============
            if HIKVISION_SDK_AVAILABLE:
                self.camera = HikvisionCamera(self.camera_ip)
                self.is_camera_connected = self.camera.connect()
                
                if self.is_camera_connected:
                    self.log_message.emit(f"{self.camera_name} 海康相机连接成功")
                    return True
                else:
                    self.log_message.emit(f"{self.camera_name} 海康相机连接失败，尝试图片测试模式")
            else:
                self.log_message.emit(f"{self.camera_name} 海康SDK未安装")
            
            # ============ 2. 尝试使用图片测试模式 ============
            import os
            test_img_folder = "test_img"
            if os.path.exists(test_img_folder) and os.path.isdir(test_img_folder):
                self.camera = ImageFolderCamera(self.camera_ip, test_img_folder)
                self.is_camera_connected = self.camera.connect()
                
                if self.is_camera_connected:
                    self.log_message.emit(f"{self.camera_name} 图片测试模式连接成功")
                    return True
                else:
                    self.log_message.emit(f"{self.camera_name} 图片测试模式加载失败")
            
            # 所有连接方式都失败
            self.log_message.emit(f"{self.camera_name} 无法连接相机")
            return False
            
        except Exception as e:
            self.error_occurred.emit(f"{self.camera_name} 相机连接异常: {str(e)}")
            return False
    
    def _disconnect_camera(self):
        """断开相机连接"""
        if self.camera and self.is_camera_connected:
            try:
                self.camera.disconnect()
                self.is_camera_connected = False
            except Exception as e:
                self.error_occurred.emit(f"{self.camera_name} 相机断开异常: {str(e)}")
    
    def _capture_image(self) -> Optional[np.ndarray]:
        """
        拍照并返回图像
        
        Returns:
            np.ndarray: 图像数据 (BGR格式)，失败返回None
        """
        if not self.is_camera_connected:
            return None
        
        try:
            # 所有相机类都实现了capture()方法
            image = self.camera.capture()
            return image
            
        except Exception as e:
            self.error_occurred.emit(f"{self.camera_name} 拍照异常: {str(e)}")
            return None
    
    def _write_result_to_plc(self, result: DetectionResult):
        """
        将识别结果写入PLC

        寄存器布局（以Camera 1为例）：
            MW101  class            分类
            MW102  x_offset         X偏移 (×10)
            MW103  y_offset         Y偏移 (×10)
            MW104  r_angle          旋转角 (×10)
            MW105  height           短轴高度 (×10)
            MW106  head_direction   尖头朝向 1=左 2=右
            MW107  length           长轴长度 (×10)
        """
        try:
            logger.info(f"[{self.camera_name}] 写入分类结果 D{self.registers['class']}={result.classification}")
            if not self.plc.write_holding_register(self.registers['class'], result.classification):
                self.error_occurred.emit(f"[{self.camera_name}] ❌ 写入分类信号失败 D{self.registers['class']}")
                return

            if result.classification == CLASS_VALUES['CUTTABLE']:
                def clamp_int16(value):
                    return max(-32768, min(32767, value))

                x_int = clamp_int16(int(result.x_offset * 10))
                y_int = clamp_int16(int(result.y_offset * 10))
                r_int = clamp_int16(int(result.r_angle * 10))
                h_int = clamp_int16(int(result.height * 10))
                head_int = int(result.head_direction)
                l_int = clamp_int16(int(result.length * 10))

                # x_offset ~ length 寄存器连续: 102,103,104,105,106,107
                values = [x_int, y_int, r_int, h_int, head_int, l_int]
                logger.info(
                    f"[{self.camera_name}] 原始值: X={result.x_offset:.2f}, Y={result.y_offset:.2f}, "
                    f"R={result.r_angle:.2f}, H={result.height:.2f}, "
                    f"Head={result.head_direction}, L={result.length:.2f}"
                )
                logger.info(f"[{self.camera_name}] 转换后: D{self.registers['x_offset']}~D{self.registers['length']} = {values}")

                if self.plc.write_multiple_registers(self.registers['x_offset'], values):
                    self.log_message.emit(
                        f"[{self.camera_name}] ✓ PLC: "
                        f"X={result.x_offset:.1f} Y={result.y_offset:.1f} "
                        f"R={result.r_angle:.1f}° H={result.height:.1f}mm "
                        f"L={result.length:.1f}mm "
                        f"Head={'左' if result.head_direction == 1 else '右'}"
                    )
                else:
                    self.error_occurred.emit(f"[{self.camera_name}] ❌ 写入坐标数据失败 D{self.registers['x_offset']}")
            else:
                self.log_message.emit(f"[{self.camera_name}] 分类={result.classification}，跳过坐标写入")

        except Exception as e:
            import traceback
            self.error_occurred.emit(f"[{self.camera_name}] ❌ 写入结果异常: {type(e).__name__}: {str(e)}")
            logger.error(f"[{self.camera_name}] 写入结果详细错误:\n{traceback.format_exc()}")
    
    def _write_error_result(self):
        """写入错误结果（分类=1，表示异常）"""
        try:
            logger.warning(f"[{self.camera_name}] 写入错误结果 D{self.registers['class']}={CLASS_VALUES['UNKNOWN']}")
            self.plc.write_holding_register(self.registers['class'], CLASS_VALUES['UNKNOWN'])
        except Exception as e:
            self.error_occurred.emit(f"[{self.camera_name}] ❌ 写入错误结果异常: {type(e).__name__}: {str(e)}")
    
    def stop(self):
        """停止工作线程"""
        self.is_running = False
