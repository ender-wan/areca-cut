#!/usr/bin/env python3
"""
YOLO模型训练脚本
用于训练槟榔检测和切割定位的YOLO模型
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
import shutil


def create_dataset_yaml(data_root: str, output_path: str):
    """
    创建YOLO数据集配置文件
    
    Args:
        data_root: 数据集根目录
        output_path: 输出yaml文件路径
    """
    # YOLO数据集配置
    data_yaml = {
        'path': str(Path(data_root).absolute()),  # 数据集根目录
        'train': 'images/train',  # 训练集路径
        'val': 'images/val',      # 验证集路径
        'test': 'images/test',    # 测试集路径（可选）
        
        # 类别数量
        'nc': 3,
        
        # 类别名称
        'names': {
            0: 'cuttable',    # 可切分类
            1: 'defect',      # 异常/缺陷
            2: 'other'        # 其他类别
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(data_yaml, f, allow_unicode=True, sort_keys=False)
    
    print(f"✓ Created dataset config: {output_path}")
    return output_path


def prepare_dataset(source_folder: str, output_folder: str, train_ratio: float = 0.8):
    """
    准备YOLO训练数据集
    
    Args:
        source_folder: 源文件夹（包含images和labels子文件夹）
        output_folder: 输出文件夹
        train_ratio: 训练集比例
    """
    import random
    from glob import glob
    
    source_path = Path(source_folder)
    output_path = Path(output_folder)
    
    # 创建目录结构
    for split in ['train', 'val', 'test']:
        (output_path / 'images' / split).mkdir(parents=True, exist_ok=True)
        (output_path / 'labels' / split).mkdir(parents=True, exist_ok=True)
    
    # 查找所有图片
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
        image_files.extend(glob(str(source_path / 'images' / ext)))
    
    if len(image_files) == 0:
        print(f"✗ No images found in {source_path / 'images'}")
        return False
    
    print(f"Found {len(image_files)} images")
    
    # 随机打乱
    random.shuffle(image_files)
    
    # 划分数据集
    n_train = int(len(image_files) * train_ratio)
    n_val = int(len(image_files) * (1 - train_ratio) * 0.5)
    
    train_files = image_files[:n_train]
    val_files = image_files[n_train:n_train + n_val]
    test_files = image_files[n_train + n_val:]
    
    # 复制文件
    def copy_files(file_list, split):
        for img_path in file_list:
            img_path = Path(img_path)
            # 复制图片
            shutil.copy(img_path, output_path / 'images' / split / img_path.name)
            
            # 复制标签（如果存在）
            label_path = source_path / 'labels' / (img_path.stem + '.txt')
            if label_path.exists():
                shutil.copy(label_path, output_path / 'labels' / split / (img_path.stem + '.txt'))
    
    copy_files(train_files, 'train')
    copy_files(val_files, 'val')
    copy_files(test_files, 'test')
    
    print(f"✓ Dataset prepared:")
    print(f"  - Train: {len(train_files)} images")
    print(f"  - Val: {len(val_files)} images")
    print(f"  - Test: {len(test_files)} images")
    
    return True


def train_yolo_model(
    data_yaml: str,
    model: str = 'yolov8n.pt',
    epochs: int = 100,
    imgsz: int = 640,
    batch: int = 16,
    device: str = '0',
    project: str = 'runs/train',
    name: str = 'betel_nut_detector'
):
    """
    训练YOLO模型
    
    Args:
        data_yaml: 数据集配置文件路径
        model: 预训练模型（yolov8n.pt, yolov8s.pt, yolov8m.pt等）
        epochs: 训练轮数
        imgsz: 输入图像尺寸
        batch: 批次大小
        device: 设备（'0'表示GPU 0，'cpu'表示CPU）
        project: 项目保存路径
        name: 实验名称
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        print("✗ ultralytics not installed. Please install it:")
        print("  pip install ultralytics")
        return None
    
    print("\n" + "="*60)
    print("Starting YOLO Training")
    print("="*60)
    print(f"Model: {model}")
    print(f"Data: {data_yaml}")
    print(f"Epochs: {epochs}")
    print(f"Image size: {imgsz}")
    print(f"Batch size: {batch}")
    print(f"Device: {device}")
    print("="*60 + "\n")
    
    # 加载模型
    yolo_model = YOLO(model)
    
    # 训练
    results = yolo_model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        project=project,
        name=name,
        
        # 优化参数
        optimizer='AdamW',
        lr0=0.01,          # 初始学习率
        lrf=0.01,          # 最终学习率
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        
        # 数据增强
        hsv_h=0.015,       # 色调增强
        hsv_s=0.7,         # 饱和度增强
        hsv_v=0.4,         # 亮度增强
        degrees=0.0,       # 旋转角度
        translate=0.1,     # 平移
        scale=0.5,         # 缩放
        shear=0.0,         # 剪切
        perspective=0.0,   # 透视
        flipud=0.0,        # 上下翻转
        fliplr=0.5,        # 左右翻转
        mosaic=1.0,        # Mosaic增强
        mixup=0.0,         # Mixup增强
        
        # 保存选项
        save=True,
        save_period=10,    # 每10个epoch保存一次
        
        # 其他
        patience=50,       # 早停patience
        workers=8,         # 数据加载线程数
        verbose=True
    )
    
    print("\n" + "="*60)
    print("Training completed!")
    print(f"Best model saved to: {results.save_dir}/weights/best.pt")
    print(f"Last model saved to: {results.save_dir}/weights/last.pt")
    print("="*60 + "\n")
    
    return results


def validate_model(model_path: str, data_yaml: str):
    """
    验证模型性能
    
    Args:
        model_path: 模型权重路径
        data_yaml: 数据集配置文件
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        print("✗ ultralytics not installed")
        return
    
    print("\n" + "="*60)
    print("Validating Model")
    print("="*60)
    
    model = YOLO(model_path)
    results = model.val(data=data_yaml)
    
    print(f"\nValidation Results:")
    print(f"  mAP50: {results.box.map50:.4f}")
    print(f"  mAP50-95: {results.box.map:.4f}")
    print("="*60 + "\n")
    
    return results


def export_model(model_path: str, format: str = 'onnx'):
    """
    导出模型到其他格式
    
    Args:
        model_path: 模型权重路径
        format: 导出格式（onnx, torchscript, coreml等）
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        print("✗ ultralytics not installed")
        return
    
    print(f"\nExporting model to {format}...")
    model = YOLO(model_path)
    model.export(format=format)
    print(f"✓ Model exported\n")


def main():
    parser = argparse.ArgumentParser(description='Train YOLO model for betel nut detection')
    
    parser.add_argument('--source', type=str, default='test_img/labeled',
                        help='Source folder with images and labels')
    parser.add_argument('--output', type=str, default='dataset',
                        help='Output dataset folder')
    parser.add_argument('--model', type=str, default='yolov8n.pt',
                        help='Pretrained model (yolov8n/s/m/l/x.pt)')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Number of training epochs')
    parser.add_argument('--imgsz', type=int, default=640,
                        help='Input image size')
    parser.add_argument('--batch', type=int, default=16,
                        help='Batch size')
    parser.add_argument('--device', type=str, default='0',
                        help='Device (0 for GPU, cpu for CPU)')
    parser.add_argument('--project', type=str, default='runs/train',
                        help='Project save directory')
    parser.add_argument('--name', type=str, default='betel_nut_detector',
                        help='Experiment name')
    parser.add_argument('--skip-prepare', action='store_true',
                        help='Skip dataset preparation')
    parser.add_argument('--validate', type=str, default=None,
                        help='Validate model (provide model path)')
    parser.add_argument('--export', type=str, default=None,
                        help='Export model format (onnx, torchscript, etc.)')
    
    args = parser.parse_args()
    
    # 如果只是验证或导出，直接执行
    if args.validate:
        data_yaml = os.path.join(args.output, 'data.yaml')
        validate_model(args.validate, data_yaml)
        return
    
    if args.export:
        model_path = args.validate or 'runs/train/betel_nut_detector/weights/best.pt'
        export_model(model_path, args.export)
        return
    
    # 准备数据集
    if not args.skip_prepare:
        print("\n📁 Preparing dataset...")
        success = prepare_dataset(args.source, args.output, train_ratio=0.8)
        if not success:
            print("✗ Dataset preparation failed")
            return
    
    # 创建数据集配置
    data_yaml = create_dataset_yaml(args.output, os.path.join(args.output, 'data.yaml'))
    
    # 检查是否存在训练数据
    train_images = Path(args.output) / 'images' / 'train'
    if not train_images.exists() or len(list(train_images.glob('*'))) == 0:
        print("✗ No training images found. Please prepare dataset first.")
        return
    
    # 训练模型
    print("\n🚀 Starting training...")
    results = train_yolo_model(
        data_yaml=data_yaml,
        model=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name
    )
    
    if results:
        print("\n✅ Training completed successfully!")
        print(f"\nTo use the trained model:")
        print(f"  1. Copy best.pt to: models/betel_nut_best.pt")
        print(f"  2. Update vision_detector.py to use the model")
        print(f"\nTo validate:")
        print(f"  python train_yolo.py --validate {results.save_dir}/weights/best.pt")
        print(f"\nTo export:")
        print(f"  python train_yolo.py --validate {results.save_dir}/weights/best.pt --export onnx")


if __name__ == "__main__":
    main()
