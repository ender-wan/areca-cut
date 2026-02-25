"""
视觉检测算法接口
VisionDetector: 槟榔识别算法的预留接口
"""

import sys
import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

# 尝试导入YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except (ImportError, OSError, Exception) as e:
    YOLO_AVAILABLE = False
    YOLO = None
    print(f"Warning: YOLO not available ({type(e).__name__}: {e}). Using mock detection.")


@dataclass
class DetectionResult:
    """检测结果数据类"""
    x_offset: float        # X轴偏移量（相对于图片中心）
    y_offset: float        # Y轴偏移量（相对于图片中心）
    r_angle: float         # R轴角度（0度平行于X轴）
    height: float          # 产品高度
    classification: int    # 分类: 1=无法识别, 2=可切, 3=备用
    confidence: float      # 置信度 0-1
    box_coords: Optional[Tuple[float, float, float, float]] = None  # 检测框坐标 (x1, y1, x2, y2)
    center_point: Optional[Tuple[float, float]] = None  # 中心点坐标 (x, y)


class VisionDetector:
    """
    视觉检测器 - YOLO算法接口封装
    
    支持真实YOLO模型和Mock模式
    """
    
    def __init__(self, model_path: Optional[str] = None, use_mock: bool = False, pixel_to_mm: float = 0.1):
        """
        初始化检测器
        
        Args:
            model_path: YOLO模型文件路径（.pt文件）
            use_mock: 是否强制使用Mock模式
            pixel_to_mm: 像素到毫米的转换比例（根据相机标定）
        """
        self.model_path = model_path
        self.model = None
        self.use_mock = use_mock
        
        # 像素到毫米的转换比例（从配置中读取）
        self.pixel_to_mm = pixel_to_mm
        
        # 如果没有指定模型路径，尝试查找默认模型
        if not self.use_mock and model_path is None:
            # 获取资源文件基础路径（支持PyInstaller打包）
            if getattr(sys, 'frozen', False):
                # 打包后的路径：从临时目录读取
                base_path = Path(sys._MEIPASS)
            else:
                # 开发环境路径
                base_path = Path(__file__).parent
            
            default_paths = [
                base_path / 'models/obb_best_m.pt',  # YOLOv8m-obb训练模型（优先）
                base_path / 'models/betel_nut_obb_best.pt',  # 旧OBB模型（备用）
                base_path / 'runs/obb/runs/obb/betel_nut_obb3/weights/best.pt',
                base_path / 'runs/obb/betel_nut_obb/weights/best.pt',
                base_path / 'models/betel_nut_best.pt',
                base_path / 'models/betel_nut_last.pt',
                base_path / 'yolov8n-obb.pt',
            ]
            for path in default_paths:
                if path.exists():
                    self.model_path = str(path)
                    logger.info(f"Found model: {self.model_path}")
                    break
            
            # 如果没有找到任何模型，使用预训练模型（会自动下载）
            if self.model_path is None and YOLO_AVAILABLE:
                self.model_path = 'yolov8n.pt'
                logger.info("Using YOLOv8n pretrained model (will download if needed)")
        # 如果指定了相对路径，从资源目录查找
        elif model_path and not Path(model_path).is_absolute():
            if getattr(sys, 'frozen', False):
                base_path = Path(sys._MEIPASS)
                self.model_path = str(base_path / model_path)
            else:
                self.model_path = model_path
        
        # 加载模型
        self.is_obb = False  # 是否是OBB模型
        self.device = 'cpu'  # 默认CPU
        if not self.use_mock and YOLO_AVAILABLE and self.model_path:
            try:
                # 检测CUDA是否可用
                import torch
                cuda_available = False
                if torch.cuda.is_available():
                    # 检查CUDA架构兼容性
                    try:
                        # 尝试创建一个测试张量到GPU
                        import warnings
                        with warnings.catch_warnings():
                            warnings.filterwarnings('ignore')
                            test_tensor = torch.randn(2, 2).cuda()
                            _ = test_tensor + test_tensor  # 简单运算测试
                            del test_tensor
                        cuda_available = True
                        self.device = 'cuda:0'
                        logger.info(f"GPU available and compatible: {torch.cuda.get_device_name(0)}")
                    except Exception as e:
                        logger.warning(f"GPU detected but not compatible (RTX 50 series需要PyTorch 2.7+): {e}")
                        logger.info("Falling back to CPU mode")
                        self.device = 'cpu'
                else:
                    logger.info("GPU not available, using CPU")
                
                self.model = YOLO(self.model_path)
                
                # 检测是否是OBB模型
                self.is_obb = 'obb' in str(self.model_path).lower() or \
                              (hasattr(self.model, 'task') and self.model.task == 'obb')
                logger.info(f"YOLO model loaded: {self.model_path} (OBB={self.is_obb}, device={self.device})")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}")
                logger.warning("Falling back to Mock mode")
                self.use_mock = True
        else:
            if not self.use_mock:
                logger.warning("YOLO not available or no model found. Using Mock mode")
            self.use_mock = True
        
    def detect_betel_nut(self, image: np.ndarray) -> DetectionResult:
        """
        检测槟榔并计算切割参数
        
        Args:
            image: 输入图像 (numpy array, BGR格式)
            
        Returns:
            DetectionResult: 检测结果，包含中心点、角度、高度和分类
        """
        
        if self.use_mock or self.model is None:
            # Mock模式
            return self._mock_detect(image)
        
        try:
            # ============ 真实YOLO检测 ============
            # 1. 运行YOLO推理（指定设备）
            results = self.model(image, verbose=False, device=self.device)
            
            # 2. 检查是否为OBB模型
            if self.is_obb and hasattr(results[0], 'obb') and results[0].obb is not None:
                # ============ OBB检测结果处理 ============
                return self._process_obb_result(results[0], image)
            else:
                # ============ 普通检测框结果处理 ============
                return self._process_regular_result(results[0], image)
            
        except Exception as e:
            logger.error(f"YOLO detection failed: {e}")
            import traceback
            traceback.print_exc()
            # 出错时返回异常分类
            return DetectionResult(0, 0, 0, 0, 1, 0.0)
    
    def _process_obb_result(self, result, image: np.ndarray) -> DetectionResult:
        """
        处理OBB（旋转框）检测结果
        
        Args:
            result: YOLO OBB检测结果
            image: 原始图像
            
        Returns:
            DetectionResult
        """
        import math
        
        obb_boxes = result.obb
        
        if len(obb_boxes) == 0:
            logger.warning("No OBB detected")
            return DetectionResult(0, 0, 0, 0, 1, 0.0)
        
        # 获取最高置信度的OBB
        confidences = obb_boxes.conf.cpu().numpy()
        best_idx = np.argmax(confidences)
        
        # 获取旋转框信息
        # xywhr格式: center_x, center_y, width, height, rotation(弧度)
        xywhr = obb_boxes.xywhr[best_idx].cpu().numpy()
        center_x, center_y, width, height, rotation = xywhr
        
        confidence = float(obb_boxes.conf[best_idx].cpu().numpy())
        class_id = int(obb_boxes.cls[best_idx].cpu().numpy())
        
        # 计算相对于图片中心的偏移（像素）
        image_center_x = image.shape[1] / 2
        image_center_y = image.shape[0] / 2
        x_offset_px = float(center_x - image_center_x)
        y_offset_px = float(center_y - image_center_y)
        
        # 转换为毫米
        x_offset = x_offset_px * self.pixel_to_mm
        y_offset = y_offset_px * self.pixel_to_mm
        
        # 旋转角度（弧度转角度）
        r_angle = float(math.degrees(rotation))
        
        # 计算高度（使用旋转框的高度）
        height_mm = float(height * self.pixel_to_mm)
        
        # 确定分类
        if class_id == 0 and confidence > 0.5:
            classification = 2  # 可切
        else:
            classification = 1  # 无法识别/异常
        
        # 获取四个角点（用于绘制）
        xyxyxyxy = obb_boxes.xyxyxyxy[best_idx].cpu().numpy()  # 4个角点坐标
        
        logger.info(f"OBB Detection: class={class_id}, conf={confidence:.2f}, "
                   f"pos=({center_x:.1f}px, {center_y:.1f}px), "
                   f"offset=({x_offset:.2f}mm, {y_offset:.2f}mm), "
                   f"angle={r_angle:.1f}°, height={height_mm:.1f}mm")
        
        return DetectionResult(
            x_offset=x_offset,
            y_offset=y_offset,
            r_angle=r_angle,
            height=height_mm,
            classification=classification,
            confidence=confidence,
            box_coords=tuple(xyxyxyxy.flatten().tolist()),  # 8个值：4个角点
            center_point=(float(center_x), float(center_y))
        )
    
    def _process_regular_result(self, result, image: np.ndarray) -> DetectionResult:
        """
        处理普通检测框结果
        
        Args:
            result: YOLO检测结果
            image: 原始图像
            
        Returns:
            DetectionResult
        """
        # 解析结果
        if len(result.boxes) == 0:
            # 未检测到目标
            logger.warning("No object detected")
            return DetectionResult(0, 0, 0, 0, 1, 0.0)  # 分类1=无法识别
        
        # 获取最高置信度的检测框
        boxes = result.boxes
        confidences = boxes.conf.cpu().numpy()
        best_idx = np.argmax(confidences)
        
        box = boxes[best_idx]
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        confidence = float(box.conf[0].cpu().numpy())
        class_id = int(box.cls[0].cpu().numpy())
        
        # 计算中心点
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        # 计算相对于图片中心的偏移（像素）
        image_center_x = image.shape[1] / 2
        image_center_y = image.shape[0] / 2
        x_offset_px = center_x - image_center_x
        y_offset_px = center_y - image_center_y
        
        # 转换为毫米
        x_offset = x_offset_px * self.pixel_to_mm
        y_offset = y_offset_px * self.pixel_to_mm
        
        # 计算旋转角度（使用自定义算法）
        r_angle = self._calculate_rotation_angle(image, x1, y1, x2, y2)
        
        # 计算高度（基于检测框大小）
        box_height = y2 - y1
        height_mm = box_height * self.pixel_to_mm
        
        # 确定分类
        # YOLO类别: 0=cuttable, 1=defect, 2=other
        # 系统分类: 1=异常, 2=可切, 3=备用
        if class_id == 0 and confidence > 0.5:
            classification = 2  # 可切
        elif class_id == 1:
            classification = 1  # 异常
        else:
            classification = 3  # 其他
        
        logger.info(f"Detection: class={class_id}, conf={confidence:.2f}, "
                   f"pos=({center_x:.1f}px, {center_y:.1f}px), "
                   f"offset=({x_offset:.2f}mm, {y_offset:.2f}mm), "
                   f"angle={r_angle:.1f}°, height={height_mm:.1f}mm")
        
        return DetectionResult(
            x_offset=float(x_offset),
            y_offset=float(y_offset),
            r_angle=float(r_angle),
            height=float(height_mm),
            classification=classification,
            confidence=float(confidence),
            box_coords=(float(x1), float(y1), float(x2), float(y2)),
            center_point=(float(center_x), float(center_y))
        )
    
    def _calculate_rotation_angle(self, image: np.ndarray, x1, y1, x2, y2) -> float:
        """
        计算槟榔的旋转角度（相对于X轴）
        
        Args:
            image: 原图
            x1, y1, x2, y2: 检测框坐标
            
        Returns:
            float: 旋转角度（度）
        """
        import cv2
        
        try:
            # 提取ROI
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            roi = image[y1:y2, x1:x2]
            
            if roi.size == 0:
                return 0.0
            
            # 转换为灰度图
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # 二值化
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 查找轮廓
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if len(contours) == 0:
                return 0.0
            
            # 获取最大轮廓
            max_contour = max(contours, key=cv2.contourArea)
            
            # 拟合椭圆或最小外接矩形
            if len(max_contour) >= 5:
                ellipse = cv2.fitEllipse(max_contour)
                angle = ellipse[2]  # 椭圆长轴角度
                
                # 归一化到-45到45度
                if angle > 90:
                    angle = angle - 180
                elif angle < -90:
                    angle = angle + 180
                    
                return angle
            else:
                # 使用最小外接矩形
                rect = cv2.minAreaRect(max_contour)
                angle = rect[2]
                return angle
                
        except Exception as e:
            logger.warning(f"Calculate rotation angle failed: {e}")
            return 0.0
    
    def _mock_detect(self, image: np.ndarray) -> DetectionResult:
        """
        Mock检测（用于测试）
        """
        import random
        
        # 模拟随机分类
        classification = random.choice([1, 2, 2, 2, 3])  # 更高概率返回可切(2)
        
        if classification == 2:  # 可切分类
            # 模拟计算中心点偏移（相对于图片中心，单位：像素）
            image_center_x = image.shape[1] // 2
            image_center_y = image.shape[0] // 2
            
            # 模拟检测到的槟榔中心点
            detected_x = image_center_x + random.randint(-100, 100)
            detected_y = image_center_y + random.randint(-80, 80)
            
            x_offset = detected_x - image_center_x
            y_offset = detected_y - image_center_y
            
            # 模拟检测框（中心点周围的矩形）
            box_w = random.randint(120, 200)
            box_h = random.randint(80, 150)
            x1 = detected_x - box_w // 2
            y1 = detected_y - box_h // 2
            x2 = detected_x + box_w // 2
            y2 = detected_y + box_h // 2
            
            # 模拟角度和高度
            r_angle = random.uniform(-45, 45)
            height = random.uniform(20, 35)
            confidence = random.uniform(0.85, 0.99)
            
            return DetectionResult(
                x_offset=x_offset,
                y_offset=y_offset,
                r_angle=r_angle,
                height=height,
                classification=classification,
                confidence=confidence,
                box_coords=(x1, y1, x2, y2),
                center_point=(detected_x, detected_y)
            )
            
        else:  # 无法识别或备用分类
            x_offset = 0
            y_offset = 0
            r_angle = 0
            height = 0
            confidence = random.uniform(0.3, 0.6) if classification == 1 else 0.7
            
            return DetectionResult(
                x_offset=x_offset,
                y_offset=y_offset,
                r_angle=r_angle,
                height=height,
                classification=classification,
                confidence=confidence,
                box_coords=None,
                center_point=None
            )
    
    @staticmethod
    def draw_detection_result(image: np.ndarray, result: DetectionResult) -> np.ndarray:
        """
        在图片上绘制检测结果和切割线
        
        Args:
            image: 原始图像
            result: 检测结果
            
        Returns:
            绘制后的图像（副本）
        """
        import cv2
        
        # 创建图像副本
        display_image = image.copy()
        h, w = display_image.shape[:2]
        
        # 如果没有检测到或分类为异常，只显示基本信息
        if result.classification == 1 or result.box_coords is None:
            # 绘制图片中心十字线
            cv2.line(display_image, (w//2 - 20, h//2), (w//2 + 20, h//2), (100, 100, 100), 1)
            cv2.line(display_image, (w//2, h//2 - 20), (w//2, h//2 + 20), (100, 100, 100), 1)
            
            # 显示检测失败信息
            cv2.putText(display_image, "No Detection", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            return display_image
        
        # 可切分类：绘制完整的检测结果
        if result.box_coords and result.center_point:
            cx, cy = result.center_point
            
            # 判断是OBB还是普通框
            is_obb = len(result.box_coords) == 8  # 8个值=4个角点
            
            if is_obb:
                # ============ OBB旋转框绘制 ============
                # 提取4个角点
                coords = result.box_coords
                pts = np.array([
                    [coords[0], coords[1]],  # 点1
                    [coords[2], coords[3]],  # 点2
                    [coords[4], coords[5]],  # 点3
                    [coords[6], coords[7]]   # 点4
                ], dtype=np.int32)
                
                # 1. 绘制旋转矩形框（绿色）
                cv2.polylines(display_image, [pts], True, (0, 255, 0), 2)
                
                # 2. 绘制角点（小圆圈）
                for pt in pts:
                    cv2.circle(display_image, tuple(pt), 3, (0, 255, 0), -1)
                
            else:
                # ============ 普通矩形框绘制 ============
                x1, y1, x2, y2 = result.box_coords
                
                # 1. 绘制检测框（绿色）
                cv2.rectangle(display_image, 
                             (int(x1), int(y1)), (int(x2), int(y2)), 
                             (0, 255, 0), 2)
            
            # 2. 绘制中心点（红色圆点）
            cv2.circle(display_image, (int(cx), int(cy)), 5, (0, 0, 255), -1)
            
            # 3. 绘制图片中心点（蓝色圆点）
            cv2.circle(display_image, (w//2, h//2), 5, (255, 0, 0), -1)
            
            # 4. 绘制从图片中心到检测中心的连线（黄色虚线）
            cv2.line(display_image, (w//2, h//2), (int(cx), int(cy)), (0, 255, 255), 1)
            
            # 5. 绘制切割线（根据旋转角度）
            # 切割线沿着槟榔的长轴方向，竖着切成两半
            import math
            angle_rad = math.radians(result.r_angle)
            
            # 计算切割线的两个端点（经过中心点，沿着长轴方向）
            # 切割线长度：OBB使用检测框范围，普通框使用宽高
            if is_obb:
                # 计算OBB框的最大跨度
                box_width = max(np.linalg.norm(pts[i] - pts[(i+1)%4]) for i in range(4))
                cut_length = box_width * 1.2
            else:
                cut_length = max(x2 - x1, y2 - y1) * 1.2
            
            # 切割线方向（沿着长轴方向，竖着切）
            cut_angle = angle_rad
            
            dx = cut_length / 2 * math.cos(cut_angle)
            dy = cut_length / 2 * math.sin(cut_angle)
            
            cut_p1 = (int(cx - dx), int(cy - dy))
            cut_p2 = (int(cx + dx), int(cy + dy))
            
            # 绘制切割线（红色粗线）
            cv2.line(display_image, cut_p1, cut_p2, (0, 0, 255), 3)
            
            # 在切割线两端绘制箭头标记
            cv2.circle(display_image, cut_p1, 4, (255, 255, 0), -1)
            cv2.circle(display_image, cut_p2, 4, (255, 255, 0), -1)
            
            # 6. 绘制文本信息
            info_y = 30
            cv2.putText(display_image, f"Class: {result.classification}", 
                       (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            info_y += 25
            cv2.putText(display_image, f"Conf: {result.confidence:.2f}", 
                       (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            info_y += 25
            cv2.putText(display_image, f"Angle: {result.r_angle:.1f}deg", 
                       (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            info_y += 25
            cv2.putText(display_image, f"Offset: ({result.x_offset:.0f}, {result.y_offset:.0f})", 
                       (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return display_image
    
    def detect_and_draw(self, image: np.ndarray) -> Tuple[DetectionResult, np.ndarray]:
        """
        检测并绘制结果
        
        Args:
            image: 输入图像
            
        Returns:
            (DetectionResult, 绘制后的图像)
        """
        result = self.detect_betel_nut(image)
        display_image = self.draw_detection_result(image, result)
        return result, display_image
    
    def release(self):
        """释放模型资源"""
        self.model = None
        logger.info("Vision detector released")


