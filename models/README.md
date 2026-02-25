# 模型文件夹

存放YOLO训练好的模型文件。

## 模型文件

- `betel_nut_best.pt` - 最佳模型权重（从训练中获得）
- `betel_nut_last.pt` - 最后一次训练的模型权重
- `*.onnx` - ONNX格式导出的模型（可选）

## 如何获取模型

### 方法1: 训练新模型

```bash
# 准备好test_img/labeled文件夹中的图片和标注
python train_yolo.py --epochs 100

# 训练完成后复制模型
cp runs/train/betel_nut_detector/weights/best.pt models/betel_nut_best.pt
```

### 方法2: 使用预训练模型

如果没有标注数据，可以先使用YOLOv8的预训练模型：

```python
# 在vision_detector.py中设置
model_path = 'yolov8n.pt'  # 使用预训练模型
```

## 模型性能要求

- mAP50 > 0.9（在验证集上）
- 推理速度 < 50ms（保证实时性）
- 模型大小 < 50MB（便于部署）

## 模型规格

- 输入尺寸: 640x640
- 类别数: 3
  - 0: cuttable（可切）
  - 1: defect（异常）
  - 2: other（其他）
