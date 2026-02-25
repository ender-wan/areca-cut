"""
OBB模型检测测试脚本
测试整个流程：加载模型 -> 检测 -> 可视化
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# 导入vision_detector
from vision_detector import VisionDetector

def test_obb_detection():
    """测试OBB模型检测流程"""
    
    print("="*60)
    print("OBB模型检测测试")
    print("="*60)
    
    # 1. 初始化检测器（会自动查找并加载OBB模型）
    print("\n1. 初始化检测器...")
    detector = VisionDetector()
    
    if detector.use_mock:
        print("   ⚠️  使用Mock模式（未找到OBB模型）")
    else:
        print(f"   ✅ 模型加载成功: {detector.model_path}")
        print(f"   📊 OBB模型: {detector.is_obb}")
    
    # 2. 读取测试图片
    print("\n2. 读取测试图片...")
    test_images_dir = Path("test_img/labeled_img-at-2026-02-03-09-18-20f902cd/images")
    
    if not test_images_dir.exists():
        print(f"   ❌ 测试图片目录不存在: {test_images_dir}")
        # 尝试使用test_img根目录的图片
        test_images_dir = Path("test_img")
        image_files = list(test_images_dir.glob("*.bmp"))[:10]
    else:
        # 测试所有标注的图片
        image_files = list(test_images_dir.glob("*.bmp"))
    
    if not image_files:
        print("   ❌ 未找到测试图片")
        return False
    
    print(f"   ✅ 找到 {len(image_files)} 张测试图片")
    
    # 3. 对每张图片进行检测
    print("\n3. 开始检测...")
    print("="*60)
    
    output_dir = Path("test_results")
    output_dir.mkdir(exist_ok=True)
    
    for idx, img_path in enumerate(image_files, 1):
        print(f"\n[{idx}/{len(image_files)}] 处理: {img_path.name}")
        print("-"*60)
        
        # 读取图片
        image = cv2.imread(str(img_path))
        if image is None:
            print(f"   ❌ 无法读取图片: {img_path}")
            continue
        
        print(f"   图片尺寸: {image.shape[1]}x{image.shape[0]}")
        
        # 检测并绘制结果
        result, display_image = detector.detect_and_draw(image)
        
        # 显示检测结果
        print(f"   📊 检测结果:")
        print(f"      - 分类: {result.classification} ", end="")
        if result.classification == 2:
            print("✅ (可切)")
        elif result.classification == 1:
            print("❌ (无法识别)")
        else:
            print("⚠️  (其他)")
        
        print(f"      - 置信度: {result.confidence:.3f}")
        print(f"      - 中心偏移: ({result.x_offset:.1f}, {result.y_offset:.1f}) px")
        print(f"      - 旋转角度: {result.r_angle:.1f}°")
        print(f"      - 高度: {result.height:.1f} mm")
        
        if result.box_coords:
            if len(result.box_coords) == 4:
                print(f"      - 检测框: 普通矩形框")
            elif len(result.box_coords) == 8:
                print(f"      - 检测框: 旋转矩形框 (OBB) ⭐")
        
        # 保存结果图片
        output_path = output_dir / f"result_{img_path.stem}.jpg"
        cv2.imwrite(str(output_path), display_image)
        print(f"   💾 结果已保存: {output_path}")
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60)
    print(f"结果图片保存在: {output_dir.absolute()}")
    print("\n💡 提示:")
    print("   - 查看 test_results/ 目录中的图片")
    print("   - 图片上会显示检测框和切割线")
    if detector.is_obb:
        print("   - OBB模型会显示更精确的旋转框和角度 ⭐")
    print("="*60)
    
    return True


def test_single_image_detection(image_path: str):
    """测试单张图片的检测"""
    
    print("="*60)
    print(f"单张图片检测测试: {image_path}")
    print("="*60)
    
    # 初始化检测器
    detector = VisionDetector()
    
    # 读取图片
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ 无法读取图片: {image_path}")
        return False
    
    print(f"图片尺寸: {image.shape[1]}x{image.shape[0]}")
    
    # 检测
    result, display_image = detector.detect_and_draw(image)
    
    # 显示结果
    print(f"\n检测结果:")
    print(f"  分类: {result.classification}")
    print(f"  置信度: {result.confidence:.3f}")
    print(f"  角度: {result.r_angle:.1f}°")
    print(f"  偏移: ({result.x_offset:.1f}, {result.y_offset:.1f})")
    
    # 保存结果
    output_path = "test_result_single.jpg"
    cv2.imwrite(output_path, display_image)
    print(f"\n💾 结果已保存: {output_path}")
    
    # 尝试显示图片（如果在支持的环境中）
    try:
        cv2.imshow("Detection Result", display_image)
        print("\n按任意键关闭窗口...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except:
        print("\n无法显示窗口（可能在非GUI环境）")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test OBB detection')
    parser.add_argument('--image', type=str, default=None,
                        help='Test single image path')
    
    args = parser.parse_args()
    
    if args.image:
        # 测试单张图片
        test_single_image_detection(args.image)
    else:
        # 测试多张图片
        test_obb_detection()
