"""
测试YOLOv8m-obb模型在7ccd文件夹图片上的效果
"""

import cv2
import os
from pathlib import Path
from ultralytics import YOLO
import numpy as np

def test_obb_model():
    """测试OBB模型"""
    
    # 模型路径
    model_path = 'models/obb_best_m.pt'
    
    # 测试图片文件夹
    test_dir = Path('test_img/7ccd')
    
    # 输出结果文件夹
    output_dir = Path('test_results_7ccd_obb_m')
    output_dir.mkdir(exist_ok=True)
    
    print("="*60)
    print("YOLOv8m-obb 模型测试")
    print("="*60)
    print(f"模型: {model_path}")
    print(f"测试图片: {test_dir}")
    print(f"输出目录: {output_dir}")
    print("="*60)
    
    # 加载模型
    print("\n加载模型...")
    model = YOLO(model_path)
    print(f"✓ 模型加载成功")
    
    # 获取所有测试图片
    image_files = list(test_dir.glob('*.bmp')) + list(test_dir.glob('*.jpg'))
    print(f"\n找到 {len(image_files)} 张测试图片")
    
    if len(image_files) == 0:
        print("❌ 未找到测试图片!")
        return
    
    # 统计结果
    total = 0
    detected = 0
    
    print("\n开始检测...")
    print("="*60)
    
    for idx, img_path in enumerate(image_files, 1):
        print(f"\n[{idx}/{len(image_files)}] {img_path.name}")
        
        # 读取图片
        image = cv2.imread(str(img_path))
        if image is None:
            print(f"  ❌ 无法读取图片")
            continue
        
        h, w = image.shape[:2]
        print(f"  图片尺寸: {w}x{h}")
        
        # 推理
        results = model(image, verbose=False)
        result = results[0]
        
        total += 1
        
        # 检查是否有检测结果
        has_detection = False
        if hasattr(result, 'obb') and result.obb is not None and len(result.obb) > 0:
            has_detection = True
            detected += 1
            
            # 解析OBB结果
            obb_boxes = result.obb
            conf = float(obb_boxes.conf[0].cpu().numpy())
            cls_id = int(obb_boxes.cls[0].cpu().numpy())
            
            # 获取旋转框参数 (center_x, center_y, width, height, rotation)
            xywhr = obb_boxes.xywhr[0].cpu().numpy()
            cx, cy, w_box, h_box, rotation = xywhr
            
            # 计算角度（弧度转角度）
            import math
            angle_deg = math.degrees(rotation)
            
            print(f"  ✓ 检测到目标")
            print(f"    置信度: {conf:.3f}")
            print(f"    类别: {cls_id}")
            print(f"    中心: ({cx:.1f}, {cy:.1f})")
            print(f"    尺寸: {w_box:.1f} x {h_box:.1f}")
            print(f"    角度: {angle_deg:.1f}°")
            
            # 绘制结果
            display_image = image.copy()
            
            # 获取4个角点
            xyxyxyxy = obb_boxes.xyxyxyxy[0].cpu().numpy()
            pts = xyxyxyxy.reshape((-1, 1, 2)).astype(np.int32)
            
            # 绘制旋转矩形框
            cv2.polylines(display_image, [pts], True, (0, 255, 0), 3)
            
            # 绘制中心点
            cv2.circle(display_image, (int(cx), int(cy)), 8, (0, 0, 255), -1)
            
            # 绘制图片中心点
            cv2.circle(display_image, (w//2, h//2), 8, (255, 0, 0), -1)
            
            # 绘制从图片中心到检测中心的连线
            cv2.line(display_image, (w//2, h//2), (int(cx), int(cy)), (0, 255, 255), 2)
            
            # 计算中心偏移
            offset_x = cx - w/2
            offset_y = cy - h/2
            
            # 添加文字信息
            cv2.putText(display_image, f"Conf: {conf:.2f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(display_image, f"Angle: {angle_deg:.1f}deg", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(display_image, f"Offset: ({offset_x:.0f}, {offset_y:.0f})", (10, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
        else:
            print(f"  ❌ 未检测到目标")
            display_image = image.copy()
            cv2.putText(display_image, "No Detection", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # 保存结果
        output_path = output_dir / f"result_{img_path.stem}.jpg"
        cv2.imwrite(str(output_path), display_image)
        print(f"  💾 已保存: {output_path.name}")
    
    # 统计总结
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)
    print(f"总图片数: {total}")
    print(f"检测成功: {detected}")
    print(f"检测失败: {total - detected}")
    print(f"检测率: {detected/total*100:.1f}%")
    print(f"\n结果已保存到: {output_dir.absolute()}")
    print("="*60)


if __name__ == '__main__':
    test_obb_model()
