"""
Mock Camera 模拟相机类
用于在无实际相机硬件的情况下测试系统
"""

import numpy as np
import cv2
import os
import random
import datetime
from pathlib import Path


class MockCamera:
    """
    模拟工业相机 - 用于测试
    
    替换位置: camera_worker.py 中 _connect_camera() 方法
    """
    
    def __init__(self, ip: str):
        self.ip = ip
        self.connected = False
        self.width = 1920
        self.height = 1080
        
        # 扫描test_img文件夹中的所有图片
        self.test_images = []
        test_img_dir = Path(__file__).parent / "test_img"
        if test_img_dir.exists():
            # 支持多种图片格式
            for ext in ['*.bmp', '*.jpg', '*.jpeg', '*.png']:
                self.test_images.extend(test_img_dir.glob(ext))
            
            # 只保留文件（排除目录）
            self.test_images = [img for img in self.test_images if img.is_file()]
            
        print(f"MockCamera: 找到 {len(self.test_images)} 张测试图片")
    
    def connect(self) -> bool:
        """模拟连接相机"""
        print(f"MockCamera: 连接到相机 {self.ip} (模拟)")
        self.connected = True
        return True
    
    def disconnect(self):
        """模拟断开相机"""
        print(f"MockCamera: 断开相机 {self.ip} (模拟)")
        self.connected = False
    
    def capture(self) -> np.ndarray:
        """
        模拟拍照 - 从test_img文件夹随机选择一张真实图片
        
        Returns:
            np.ndarray: 模拟的BGR图像
        """
        if not self.connected:
            return None
        
        # 如果有真实测试图片，随机选择一张
        if self.test_images:
            image_path = random.choice(self.test_images)
            image = cv2.imread(str(image_path))
            
            if image is not None:
                # 在图片上添加相机标识和时间戳
                # 添加半透明背景
                overlay = image.copy()
                cv2.rectangle(overlay, (0, 0), (400, 100), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.3, image, 0.7, 0, image)
                
                # 绘制相机IP
                cv2.putText(
                    image,
                    f"Camera: {self.ip}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2
                )
                
                # 绘制时间戳
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(
                    image,
                    timestamp,
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2
                )
                
                # 绘制图片文件名
                cv2.putText(
                    image,
                    f"Source: {image_path.name}",
                    (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 255),
                    1
                )
                
                return image
        
        # 后备方案：如果没有测试图片，生成模拟图片
        image = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        image[:, :] = (200, 200, 200)
        
        # 绘制一个模拟的槟榔（椭圆）
        center_x = self.width // 2 + random.randint(-100, 100)
        center_y = self.height // 2 + random.randint(-80, 80)
        axes = (random.randint(100, 150), random.randint(150, 200))
        angle = random.uniform(-45, 45)
        color = (60, 100, 140)
        cv2.ellipse(image, (center_x, center_y), axes, angle, 0, 360, color, -1)
        
        # 添加纹理
        noise = np.random.randint(-30, 30, image.shape, dtype=np.int16)
        image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # 添加信息
        cv2.putText(image, f"Camera: {self.ip}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(image, timestamp, (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.putText(image, "NO TEST IMAGES", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # 绘制中心十字线
        cv2.line(image, (self.width // 2 - 50, self.height // 2), 
                 (self.width // 2 + 50, self.height // 2), (0, 255, 0), 2)
        cv2.line(image, (self.width // 2, self.height // 2 - 50), 
                 (self.width // 2, self.height // 2 + 50), (0, 255, 0), 2)
        
        return image
