"""
视觉检测算法 - 传统CV版
基于阈值分割 + 轮廓分析 + 椭圆拟合，无需神经网络。
适用于固定白色背景下的槟榔检测。
"""

import math
import logging
import cv2
import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """检测结果数据类"""
    x_offset: float        # X轴偏移量（mm，相对于图片中心）
    y_offset: float        # Y轴偏移量（mm，相对于图片中心）
    r_angle: float         # R轴角度（度，长轴相对于水平方向）
    height: float          # 短轴宽度（mm）
    length: float          # 长轴长度（mm）
    head_direction: int    # 尖头朝向: 1=左, 2=右, 0=未知
    classification: int    # 分类: 1=无法识别, 2=可切, 3=备用
    confidence: float      # 置信度 0-1
    box_coords: Optional[Tuple] = None        # 旋转框角点坐标
    center_point: Optional[Tuple[float, float]] = None  # 中心点坐标 (x, y) 像素


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _segment_nut(gray: np.ndarray) -> np.ndarray:
    """
    从灰度图中分割出槟榔的二值掩膜。
    假设：深色目标在亮色（白色）背景上。
    """
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)

    # Otsu 自动阈值，白底深目标 → BINARY_INV 使目标为白色前景
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 形态学清理：先闭合小孔洞，再开运算去毛刺
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    return binary


def _largest_contour(binary: np.ndarray, min_area_ratio: float = 0.005):
    """
    返回面积最大且大于最小面积比的轮廓，None 表示没有。
    min_area_ratio 是相对于图像面积的比例阈值，用于过滤噪声。
    """
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    img_area = binary.shape[0] * binary.shape[1]
    min_area = img_area * min_area_ratio

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < min_area:
        return None
    return largest


def _determine_head_direction(contour: np.ndarray,
                              center: np.ndarray,
                              major_vec: np.ndarray,
                              major_len: float) -> int:
    """
    判断槟榔尖头朝向。

    方法：沿长轴在多个位置做横截面切片，用每个切片的最大宽度
    构建宽度剖面，比较两端的锥度。较窄（锥度更大）的一端是尖头。
    使用 max 宽度而非 mean，避免被果蒂等窄突出物干扰。

    返回:
        1 = 尖头朝左（tip_x < other_x）
        2 = 尖头朝右（tip_x > other_x）
        0 = 无法判断
    """
    pts = contour.reshape(-1, 2).astype(np.float64)
    rel = pts - center

    perp_vec = np.array([-major_vec[1], major_vec[0]])
    proj_major = rel @ major_vec
    proj_perp = np.abs(rel @ perp_vec)

    half = major_len / 2
    band = half * 0.08  # 每个切片的半带宽

    # 在 40%~85% 半长处采样横截面宽度（避开中心对称区和极端末端）
    sample_fracs = [0.40, 0.50, 0.60, 0.70, 0.80]
    widths_pos = []
    widths_neg = []

    for frac in sample_fracs:
        target = half * frac

        mask_p = np.abs(proj_major - target) < band
        if mask_p.sum() >= 2:
            widths_pos.append(float(proj_perp[mask_p].max()))

        mask_n = np.abs(proj_major + target) < band
        if mask_n.sum() >= 2:
            widths_neg.append(float(proj_perp[mask_n].max()))

    if len(widths_pos) < 2 or len(widths_neg) < 2:
        return 0

    score_pos = float(np.mean(widths_pos))
    score_neg = float(np.mean(widths_neg))

    if score_pos < score_neg:
        tip_endpoint = center + major_vec * half
    else:
        tip_endpoint = center - major_vec * half

    other_endpoint = 2 * center - tip_endpoint

    if tip_endpoint[0] < other_endpoint[0]:
        return 1
    else:
        return 2


# ---------------------------------------------------------------------------
# 主检测器类
# ---------------------------------------------------------------------------

class VisionDetector:
    """
    视觉检测器 — 传统 CV 版本

    流程: 灰度 → 二值分割 → 最大轮廓 → 椭圆拟合 → 尖头判断
    """

    def __init__(self, pixel_to_mm: float = 0.1, **_kwargs):
        """
        Args:
            pixel_to_mm: 像素到毫米的转换比例（根据相机标定）
        """
        self.pixel_to_mm = pixel_to_mm
        logger.info(f"VisionDetector initialized (traditional CV, pixel_to_mm={pixel_to_mm})")

    # ------------------------------------------------------------------ detect
    def detect_betel_nut(self, image: np.ndarray) -> DetectionResult:
        """
        检测图像中的槟榔并计算全部参数。
        检测后 self._last_contour 保存原始轮廓供绘图使用。
        """
        self._last_contour = None

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        binary = _segment_nut(gray)
        contour = _largest_contour(binary)

        if contour is None or len(contour) < 5:
            logger.warning("No betel nut contour found")
            return DetectionResult(0, 0, 0, 0, 0, 0, 1, 0.0)

        # --- 椭圆拟合 ---
        ellipse = cv2.fitEllipse(contour)
        (cx, cy), (axis_a, axis_b), angle_deg = ellipse
        # cv2.fitEllipse 返回的 axis_a, axis_b 是直径（不是半径）
        # axis_a 对应 angle_deg 方向的轴，不一定是长轴
        if axis_a < axis_b:
            major_diameter, minor_diameter = axis_b, axis_a
            major_angle = angle_deg + 90
        else:
            major_diameter, minor_diameter = axis_a, axis_b
            major_angle = angle_deg

        # 归一化角度到 -90 ~ +90
        major_angle = major_angle % 360
        if major_angle > 180:
            major_angle -= 360
        if major_angle > 90:
            major_angle -= 180
        elif major_angle < -90:
            major_angle += 180

        major_len_px = major_diameter
        minor_len_px = minor_diameter

        # 长轴方向单位向量
        rad = math.radians(major_angle)
        major_vec = np.array([math.cos(rad), math.sin(rad)])

        # --- 偏移量（相对于图片中心）---
        img_h, img_w = image.shape[:2]
        x_offset_px = cx - img_w / 2
        y_offset_px = cy - img_h / 2
        x_offset_mm = x_offset_px * self.pixel_to_mm
        y_offset_mm = y_offset_px * self.pixel_to_mm

        # --- 尺寸 ---
        length_mm = major_len_px * self.pixel_to_mm
        height_mm = minor_len_px * self.pixel_to_mm

        # --- 尖头方向 ---
        center = np.array([cx, cy])
        head_dir = _determine_head_direction(contour, center, major_vec, major_len_px)

        # --- 置信度（用轮廓面积 vs 椭圆面积的匹配度衡量）---
        contour_area = cv2.contourArea(contour)
        ellipse_area = math.pi * (major_len_px / 2) * (minor_len_px / 2)
        confidence = min(contour_area, ellipse_area) / max(contour_area, ellipse_area) if ellipse_area > 0 else 0

        classification = 2  # 检测到就是可切
        self._last_contour = contour

        # --- 旋转框角点：用轮廓的最小外接矩形（精确贴合实际形状）---
        min_rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(min_rect)
        box_tuple = tuple(box.flatten().tolist())

        logger.info(
            f"CV Detection: center=({cx:.1f},{cy:.1f})px, "
            f"offset=({x_offset_mm:.2f},{y_offset_mm:.2f})mm, "
            f"angle={major_angle:.1f}°, length={length_mm:.1f}mm, "
            f"height={height_mm:.1f}mm, head={head_dir}, conf={confidence:.2f}"
        )

        return DetectionResult(
            x_offset=x_offset_mm,
            y_offset=y_offset_mm,
            r_angle=major_angle,
            height=height_mm,
            length=length_mm,
            head_direction=head_dir,
            classification=classification,
            confidence=confidence,
            box_coords=box_tuple,
            center_point=(float(cx), float(cy))
        )

    # ------------------------------------------------------------------ draw
    @staticmethod
    def draw_detection_result(image: np.ndarray, result: DetectionResult,
                              contour: np.ndarray = None) -> np.ndarray:
        """在图片上绘制检测结果和切割线。"""
        display = image.copy()
        h, w = display.shape[:2]

        if result.classification == 1 or result.box_coords is None:
            cv2.line(display, (w // 2 - 20, h // 2), (w // 2 + 20, h // 2), (100, 100, 100), 1)
            cv2.line(display, (w // 2, h // 2 - 20), (w // 2, h // 2 + 20), (100, 100, 100), 1)
            cv2.putText(display, "No Detection", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            return display

        cx, cy = result.center_point

        # 轮廓（洋红色）
        if contour is not None:
            cv2.drawContours(display, [contour], -1, (255, 0, 255), 2)

        # 旋转框
        coords = result.box_coords
        pts = np.array([[coords[i], coords[i + 1]] for i in range(0, 8, 2)], dtype=np.int32)
        cv2.polylines(display, [pts], True, (0, 255, 0), 2)
        for pt in pts:
            cv2.circle(display, tuple(pt), 3, (0, 255, 0), -1)

        # 中心点（红），图片中心（蓝）
        cv2.circle(display, (int(cx), int(cy)), 5, (0, 0, 255), -1)
        cv2.circle(display, (w // 2, h // 2), 5, (255, 0, 0), -1)
        cv2.line(display, (w // 2, h // 2), (int(cx), int(cy)), (0, 255, 255), 1)

        # 切割线（沿长轴方向）
        angle_rad = math.radians(result.r_angle)
        cut_len = max(w, h) * 0.4
        dx = cut_len / 2 * math.cos(angle_rad)
        dy = cut_len / 2 * math.sin(angle_rad)
        p1 = (int(cx - dx), int(cy - dy))
        p2 = (int(cx + dx), int(cy + dy))
        cv2.line(display, p1, p2, (0, 0, 255), 3)

        # 尖头标记（青色箭头指向尖头方向）
        if result.head_direction in (1, 2):
            sign = -1 if result.head_direction == 1 else 1
            tip_x = int(cx + sign * dx)
            tip_y = int(cy + sign * dy)
            cv2.circle(display, (tip_x, tip_y), 8, (255, 255, 0), 2)
            cv2.putText(display, "TIP", (tip_x + 10, tip_y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

        # 信息面板
        info = [
            f"Class: {result.classification}",
            f"Conf: {result.confidence:.2f}",
            f"Angle: {result.r_angle:.1f}deg",
            f"Length: {result.length:.1f}mm",
            f"Height: {result.height:.1f}mm",
            f"Head: {'Left' if result.head_direction == 1 else 'Right' if result.head_direction == 2 else '?'}",
            f"Offset: ({result.x_offset:.0f}, {result.y_offset:.0f})",
        ]
        for i, text in enumerate(info):
            cv2.putText(display, text, (10, 30 + i * 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        return display

    # ------------------------------------------------------------------ combo
    def detect_and_draw(self, image: np.ndarray) -> Tuple[DetectionResult, np.ndarray]:
        result = self.detect_betel_nut(image)
        display_image = self.draw_detection_result(image, result, self._last_contour)
        return result, display_image

    def release(self):
        logger.info("Vision detector released")
