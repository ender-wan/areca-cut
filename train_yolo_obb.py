"""
YOLO OBB (Oriented Bounding Box) 模型训练脚本
用于训练槟榔旋转框检测模型
"""

import os
import sys
import argparse
import shutil
from pathlib import Path

try:
    from ultralytics import YOLO
    import torch
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("Error: ultralytics or torch not installed")
    print("Install with: pip install ultralytics torch torchvision")
    sys.exit(1)


def prepare_dataset(source_dir: str, train_ratio: float = 0.8):
    """
    准备OBB数据集（分割训练集和验证集）
    
    Args:
        source_dir: 数据集根目录（包含images和labels文件夹）
        train_ratio: 训练集比例
    """
    import random
    
    source_path = Path(source_dir)
    images_dir = source_path / 'images'
    labels_dir = source_path / 'labels'
    
    # 获取所有图像文件
    image_files = list(images_dir.glob('*.bmp')) + \
                  list(images_dir.glob('*.jpg')) + \
                  list(images_dir.glob('*.png'))
    
    print(f"Found {len(image_files)} images in {images_dir}")
    
    if len(image_files) == 0:
        print("Error: No images found!")
        return False
    
    # 随机打乱
    random.shuffle(image_files)
    
    # 计算分割点
    train_count = int(len(image_files) * train_ratio)
    
    # 创建训练和验证目录
    train_images_dir = source_path / 'train' / 'images'
    train_labels_dir = source_path / 'train' / 'labels'
    val_images_dir = source_path / 'val' / 'images'
    val_labels_dir = source_path / 'val' / 'labels'
    
    for dir_path in [train_images_dir, train_labels_dir, val_images_dir, val_labels_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # 分割数据集
    for idx, img_file in enumerate(image_files):
        # 对应的标签文件
        label_file = labels_dir / (img_file.stem + '.txt')
        
        if not label_file.exists():
            print(f"Warning: Label not found for {img_file.name}, skipping...")
            continue
        
        # 确定目标目录
        if idx < train_count:
            target_img_dir = train_images_dir
            target_label_dir = train_labels_dir
        else:
            target_img_dir = val_images_dir
            target_label_dir = val_labels_dir
        
        # 复制文件
        shutil.copy2(img_file, target_img_dir / img_file.name)
        shutil.copy2(label_file, target_label_dir / label_file.name)
    
    print(f"Dataset prepared:")
    print(f"  Train: {train_count} images")
    print(f"  Val: {len(image_files) - train_count} images")
    
    return True


def train_obb_model(
    data_yaml: str,
    model: str = 'yolov8n-obb.pt',
    epochs: int = 100,
    batch: int = 16,
    imgsz: int = 640,
    device: str = '0',
    project: str = 'runs/obb',
    name: str = 'betel_nut_obb'
):
    """
    训练YOLO OBB模型
    
    Args:
        data_yaml: 数据集配置文件路径
        model: 预训练模型名称（yolov8n-obb.pt, yolov8s-obb.pt等）
        epochs: 训练轮数
        batch: batch size
        imgsz: 图像尺寸
        device: 设备 ('0', 'cpu', 'mps'等)
        project: 项目保存路径
        name: 实验名称
    """
    print("="*60)
    print("Starting YOLO OBB Model Training")
    print("="*60)
    print(f"Model: {model}")
    print(f"Data: {data_yaml}")
    print(f"Epochs: {epochs}")
    print(f"Batch: {batch}")
    print(f"Image Size: {imgsz}")
    print(f"Device: {device}")
    print("="*60)
    
    # 检查CUDA是否可用
    if device == '0' and not torch.cuda.is_available():
        print("Warning: CUDA not available, falling back to CPU")
        device = 'cpu'
    
    # 加载模型
    try:
        model_obj = YOLO(model)
        print(f"Loaded pretrained model: {model}")
    except Exception as e:
        print(f"Error loading model: {e}")
        return None
    
    # 开始训练
    try:
        results = model_obj.train(
            data=data_yaml,
            epochs=epochs,
            batch=batch,
            imgsz=imgsz,
            device=device,
            project=project,
            name=name,
            patience=20,  # early stopping patience
            save=True,
            save_period=10,  # 每10个epoch保存一次
            plots=True,
            verbose=True,
            # OBB specific
            degrees=20.0,  # 旋转增强范围
            translate=0.1,  # 平移增强
            scale=0.5,      # 缩放增强
            flipud=0.0,     # 上下翻转（槟榔方向固定，不启用）
            fliplr=0.5,     # 左右翻转
            mosaic=1.0,     # mosaic增强
        )
        
        print("\n" + "="*60)
        print("Training completed successfully!")
        print("="*60)
        
        # 显示最佳模型路径
        best_model_path = Path(project) / name / 'weights' / 'best.pt'
        last_model_path = Path(project) / name / 'weights' / 'last.pt'
        
        print(f"Best model: {best_model_path}")
        print(f"Last model: {last_model_path}")
        
        return results
        
    except Exception as e:
        print(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def validate_model(model_path: str, data_yaml: str, device: str = '0'):
    """
    验证模型性能
    
    Args:
        model_path: 模型文件路径
        data_yaml: 数据集配置文件
        device: 计算设备
    """
    print("\n" + "="*60)
    print("Validating Model")
    print("="*60)
    
    try:
        model = YOLO(model_path)
        results = model.val(data=data_yaml, device=device, split='val')
        
        print("\nValidation Results:")
        print(f"  mAP50: {results.box.map50:.4f}")
        print(f"  mAP50-95: {results.box.map:.4f}")
        
        return results
        
    except Exception as e:
        print(f"Validation failed: {e}")
        return None


def export_model(model_path: str, format: str = 'onnx'):
    """
    导出模型到其他格式
    
    Args:
        model_path: 模型文件路径
        format: 导出格式 ('onnx', 'torchscript', 'coreml'等)
    """
    print(f"\nExporting model to {format}...")
    
    try:
        model = YOLO(model_path)
        export_path = model.export(format=format)
        print(f"Model exported to: {export_path}")
        return export_path
    except Exception as e:
        print(f"Export failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Train YOLO OBB model for betel nut detection')
    
    # 数据集参数
    parser.add_argument('--data', type=str, default='betel_nut_obb.yaml',
                        help='Dataset YAML config file')
    parser.add_argument('--prepare', action='store_true',
                        help='Prepare dataset (split train/val)')
    parser.add_argument('--source', type=str, 
                        default='test_img/labeled_img-at-2026-02-03-09-18-20f902cd',
                        help='Source dataset directory')
    
    # 训练参数
    parser.add_argument('--model', type=str, default='yolov8n-obb.pt',
                        help='Pretrained model (yolov8n-obb.pt, yolov8s-obb.pt, etc.)')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Number of training epochs')
    parser.add_argument('--batch', type=int, default=16,
                        help='Batch size')
    parser.add_argument('--imgsz', type=int, default=640,
                        help='Image size')
    parser.add_argument('--device', type=str, default='0',
                        help='Device (0, cpu, mps)')
    parser.add_argument('--project', type=str, default='runs/obb',
                        help='Project save directory')
    parser.add_argument('--name', type=str, default='betel_nut_obb',
                        help='Experiment name')
    
    # 其他操作
    parser.add_argument('--validate', type=str, default=None,
                        help='Validate model (provide model path)')
    parser.add_argument('--export', type=str, default=None,
                        help='Export model to format (onnx, torchscript, etc.)')
    
    args = parser.parse_args()
    
    # 准备数据集
    if args.prepare:
        print("Preparing dataset...")
        if not prepare_dataset(args.source):
            print("Dataset preparation failed!")
            return
        
        # 更新配置文件以使用train/val分割
        print("\nNote: Update betel_nut_obb.yaml to use 'train' and 'val' folders")
    
    # 验证模型
    if args.validate:
        validate_model(args.validate, args.data, args.device)
        return
    
    # 导出模型
    if args.export:
        model_path = args.validate if args.validate else f'{args.project}/{args.name}/weights/best.pt'
        export_model(model_path, args.export)
        return
    
    # 训练模型
    if not args.validate and not args.export:
        results = train_obb_model(
            data_yaml=args.data,
            model=args.model,
            epochs=args.epochs,
            batch=args.batch,
            imgsz=args.imgsz,
            device=args.device,
            project=args.project,
            name=args.name
        )
        
        if results:
            print("\n" + "="*60)
            print("Next Steps:")
            print("="*60)
            print("1. Check results in:", f"{args.project}/{args.name}")
            print("2. Copy best model:")
            print(f"   cp {args.project}/{args.name}/weights/best.pt models/betel_nut_obb_best.pt")
            print("3. Update vision_detector.py to use OBB model")
            print("="*60)


if __name__ == '__main__':
    main()
