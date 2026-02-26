"""
主窗口GUI
MainWindow: 显示8个相机的实时状态, 图片和数据
"""

import sys
import logging
import traceback
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QTextEdit, QGroupBox,
    QLineEdit, QSpinBox, QStatusBar, QDialog, QDialogButtonBox,
    QFormLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
import numpy as np

from config import CAMERA_CONFIGS, PLC_CONFIG, CAMERA_PARAMS
from plc_manager import PlcManager
from camera_worker import CameraWorker
from vision_detector import DetectionResult

# 获取日志记录器
logger = logging.getLogger('BetelNutVision')


class CameraWidget(QGroupBox):
    """单个相机的显示控件"""
    
    def __init__(self, camera_config: dict):
        super().__init__(camera_config['name'])
        self.camera_config = camera_config
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 状态标签
        self.status_label = QLabel("状态: 离线")
        self.status_label.setStyleSheet("color: gray; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # IP地址标签
        self.ip_label = QLabel(f"IP: {self.camera_config['ip']}")
        self.ip_label.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(self.ip_label)
        
        # 图像显示区域
        self.image_label = QLabel()
        self.image_label.setFixedSize(320, 180)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("无图像")
        layout.addWidget(self.image_label)
        
        # 数据显示
        data_layout = QGridLayout()
        self.data_labels = {}
        
        labels = [
            ('X(mm):', 'x'), ('Y(mm):', 'y'),
            ('R(°):', 'r'), ('H(mm):', 'h'),
            ('L(mm):', 'l'), ('朝向:', 'head'),
            ('分类:', 'class'), ('置信度:', 'conf'),
        ]
        
        for i, (text, key) in enumerate(labels):
            row = i // 2
            col = (i % 2) * 2
            
            label = QLabel(text)
            value = QLabel("--")
            value.setStyleSheet("font-weight: bold;")
            
            data_layout.addWidget(label, row, col)
            data_layout.addWidget(value, row, col + 1)
            
            self.data_labels[key] = value
        
        layout.addLayout(data_layout)
        self.setLayout(layout)
    
    def update_status(self, status: str):
        """更新状态"""
        color_map = {
            "待机": "green",
            "拍照中": "blue",
            "计算中": "orange",
            "离线": "gray",
            "错误": "red"
        }
        color = color_map.get(status, "gray")
        self.status_label.setText(f"状态: {status}")
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
    
    def update_image(self, image: np.ndarray):
        """更新图像显示"""
        try:
            # 转换为QImage
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            
            # BGR转RGB
            rgb_image = image[:, :, ::-1].copy()
            
            q_image = QImage(
                rgb_image.data,
                width,
                height,
                bytes_per_line,
                QImage.Format_RGB888
            )
            
            # 缩放到显示区域
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.image_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"更新图像失败: {e}")
    
    def update_result(self, result: DetectionResult):
        """更新检测结果"""
        self.data_labels['x'].setText(f"{result.x_offset:.1f}")
        self.data_labels['y'].setText(f"{result.y_offset:.1f}")
        self.data_labels['r'].setText(f"{result.r_angle:.1f}°")
        self.data_labels['h'].setText(f"{result.height:.1f}")
        self.data_labels['l'].setText(f"{result.length:.1f}")

        head_text = {1: "← 左", 2: "右 →", 0: "--"}.get(result.head_direction, "--")
        self.data_labels['head'].setText(head_text)

        class_text = {1: "无法识别", 2: "可切", 3: "备用"}.get(result.classification, "未知")
        self.data_labels['class'].setText(class_text)
        self.data_labels['conf'].setText(f"{result.confidence:.2f}")
    
    def clear_data(self):
        """清空数据显示"""
        for label in self.data_labels.values():
            label.setText("--")


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统设置")
        self.init_ui()
        
    def init_ui(self):
        layout = QFormLayout()
        
        # PLC IP设置
        self.plc_ip_edit = QLineEdit(PLC_CONFIG['ip'])
        layout.addRow("PLC IP地址:", self.plc_ip_edit)
        
        # PLC端口设置
        self.plc_port_edit = QSpinBox()
        self.plc_port_edit.setRange(1, 65535)
        self.plc_port_edit.setValue(PLC_CONFIG['port'])
        layout.addRow("PLC 端口:", self.plc_port_edit)
        
        # 相机曝光设置（模拟）
        self.exposure_edit = QSpinBox()
        self.exposure_edit.setRange(100, 100000)
        self.exposure_edit.setValue(CAMERA_PARAMS['exposure'])
        layout.addRow("相机曝光(μs):", self.exposure_edit)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | 
            QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def get_settings(self):
        """获取设置"""
        return {
            'plc_ip': self.plc_ip_edit.text(),
            'plc_port': self.plc_port_edit.value(),
            'exposure': self.exposure_edit.value()
        }


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        try:
            logger.info("初始化主窗口...")
            self.setWindowTitle("areca v1.0")
            self.setGeometry(100, 100, 1400, 900)
            
            # 初始化管理器
            logger.info("创建PLC管理器...")
            self.plc_manager = PlcManager()
            self.camera_workers = []
            self.camera_widgets = []
            
            logger.info("初始化界面...")
            self.init_ui()
            
            logger.info("连接PLC...")
            self.connect_plc()
            
            logger.info("主窗口初始化完成")
            
        except Exception as e:
            logger.error(f"主窗口初始化失败: {e}")
            logger.error(traceback.format_exc())
            raise
        
    def init_ui(self):
        """初始化界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        # 顶部按钮栏
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("启动系统")
        self.start_btn.clicked.connect(self.start_system)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止系统")
        self.stop_btn.clicked.connect(self.stop_system)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        self.settings_btn = QPushButton("设置")
        self.settings_btn.clicked.connect(self.open_settings)
        button_layout.addWidget(self.settings_btn)
        
        button_layout.addStretch()
        
        self.plc_status_label = QLabel("PLC: 未连接")
        self.plc_status_label.setStyleSheet("color: red; font-weight: bold;")
        button_layout.addWidget(self.plc_status_label)
        
        main_layout.addLayout(button_layout)
        
        # 中间相机网格区域
        camera_grid = QGridLayout()
        
        for i, cam_config in enumerate(CAMERA_CONFIGS):
            cam_widget = CameraWidget(cam_config)
            self.camera_widgets.append(cam_widget)
            
            row = i // 4
            col = i % 4
            camera_grid.addWidget(cam_widget, row, col)
        
        main_layout.addLayout(camera_grid)
        
        # 底部日志区域
        log_group = QGroupBox("系统日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        central_widget.setLayout(main_layout)
        
        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪")
    
    def connect_plc(self):
        """连接PLC"""
        self.add_log("正在连接PLC...")
        if self.plc_manager.connect():
            self.plc_status_label.setText("PLC: 已连接")
            self.plc_status_label.setStyleSheet("color: green; font-weight: bold;")
            self.add_log("PLC连接成功")
        else:
            self.plc_status_label.setText("PLC: 连接失败")
            self.plc_status_label.setStyleSheet("color: red; font-weight: bold;")
            self.add_log("PLC连接失败，请检查网络和PLC配置")
            QMessageBox.critical(
                self,
                "PLC连接失败",
                f"无法连接到PLC {self.plc_manager.ip}:{self.plc_manager.port}\n"
                "请检查:\n"
                "1. PLC是否开机\n"
                "2. 网络连接是否正常\n"
                "3. config.py中的IP地址是否正确"
            )
    
    def start_system(self):
        """启动系统 - 启动所有相机工作线程"""
        try:
            self.add_log("=== 启动系统 ===")
            logger.info("启动系统按钮被点击")
            
            # 检查PLC连接状态
            plc_connected = self.plc_manager.is_connected()
            self.add_log(f"PLC连接状态: {plc_connected}")
            logger.info(f"PLC连接状态: {plc_connected}")
            
            if not plc_connected:
                self.add_log("错误: PLC未连接，无法启动")
                logger.error("PLC未连接，无法启动系统")
                return
            
            # 创建并启动8个相机工作线程
            self.add_log(f"开始创建 {len(CAMERA_CONFIGS)} 个相机工作线程...")
            logger.info(f"开始创建 {len(CAMERA_CONFIGS)} 个相机工作线程")
            
            for i, cam_config in enumerate(CAMERA_CONFIGS):
                self.add_log(f"创建相机 {i+1} 工作线程: {cam_config.get('name', f'Camera{i+1}')}")
                logger.info(f"创建相机 {i+1} 工作线程")
                
                worker = CameraWorker(cam_config, self.plc_manager)
                
                # 连接信号
                worker.status_changed.connect(
                    lambda status, idx=i: self.camera_widgets[idx].update_status(status)
                )
                worker.image_captured.connect(
                    lambda image, idx=i: self.camera_widgets[idx].update_image(image)
                )
                worker.result_computed.connect(
                    lambda result, idx=i: self.camera_widgets[idx].update_result(result)
                )
                worker.log_message.connect(self.add_log)
                worker.error_occurred.connect(
                    lambda msg: self.add_log(f"错误: {msg}")
                )
                
                self.camera_workers.append(worker)
                worker.start()
                self.add_log(f"相机 {i+1} 工作线程已启动")
            
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.add_log("所有相机工作线程已启动")
            logger.info("所有相机工作线程已启动")
            self.statusBar.showMessage("系统运行中...")
            
        except Exception as e:
            error_msg = f"启动系统失败: {str(e)}"
            self.add_log(error_msg)
            logger.error(error_msg)
            logger.error(traceback.format_exc())
    
    def stop_system(self):
        """停止系统 - 停止所有相机工作线程"""
        self.add_log("=== 停止系统 ===")
        
        for worker in self.camera_workers:
            worker.stop()
            worker.wait()  # 等待线程结束
        
        self.camera_workers.clear()
        
        # 清空相机显示
        for widget in self.camera_widgets:
            widget.update_status("离线")
            widget.clear_data()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.add_log("系统已停止")
        self.statusBar.showMessage("系统已停止")
    
    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_settings()
            self.add_log(f"设置已更新: PLC={settings['plc_ip']}:{settings['plc_port']}")
            # TODO: 应用新设置（需要重启连接）
    
    def add_log(self, message: str):
        """添加日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.camera_workers:
            self.stop_system()
        
        self.plc_manager.disconnect()
        event.accept()


def main():
    """主函数"""
    try:
        logger.info("创建QApplication...")
        app = QApplication(sys.argv)
        
        # 设置应用样式
        app.setStyle("Fusion")
        logger.info("应用样式设置完成")
        
        logger.info("创建主窗口...")
        window = MainWindow()
        logger.info("主窗口创建成功")
        
        window.show()
        logger.info("主窗口已显示")
        
        logger.info("进入事件循环...")
        exit_code = app.exec()
        logger.info(f"程序正常退出，退出码: {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.critical("主函数发生异常!")
        logger.critical(f"错误: {e}")
        logger.critical(traceback.format_exc())
        
        # 尝试显示错误对话框
        try:
            QMessageBox.critical(
                None, 
                "严重错误", 
                f"程序运行时发生严重错误:\n\n{str(e)}\n\n详细信息请查看日志文件。"
            )
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()
