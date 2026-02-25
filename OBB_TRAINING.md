# YOLO OBB 模型训练和使用指南

## 📊 当前状态

训练已启动，模型将保存在：
- `runs/obb/betel_nut_obb/weights/best.pt` - 最佳模型（根据验证集mAP）
- `runs/obb/betel_nut_obb/weights/last.pt` - 最后一个epoch的模型

## 🎯 数据集信息

- **位置**: `test_img/labeled_img-at-2026-02-03-09-18-20f902cd/`
- **总图片数**: 33张
- **训练集**: 26张 (80%)
- **验证集**: 7张 (20%)
- **标注格式**: YOLO OBB (8个坐标值：4个角点)
- **类别**: areca (槟榔)

## 🚀 训练命令

### 基础训练（已执行）
```bash
python train_yolo_obb.py --prepare --source test_img/labeled_img-at-2026-02-03-09-18-20f902cd
```

### 继续/重新训练
```bash
# 使用默认参数（100 epochs, CPU）
python train_yolo_obb.py --data betel_nut_obb.yaml

# 使用GPU（如果可用）
python train_yolo_obb.py --data betel_nut_obb.yaml --device 0

# 快速训练（较少epoch）
python train_yolo_obb.py --data betel_nut_obb.yaml --epochs 50 --batch 8

# 使用更大的模型
python train_yolo_obb.py --data betel_nut_obb.yaml --model yolov8s-obb.pt
```

### 验证模型
```bash
python train_yolo_obb.py --validate runs/obb/betel_nut_obb/weights/best.pt
```

### 导出模型（ONNX）
```bash
python train_yolo_obb.py --validate runs/obb/betel_nut_obb/weights/best.pt --export onnx
```

## 📦 部署模型到系统

训练完成后：

```bash
# 1. 复制最佳模型到models目录
cp runs/obb/betel_nut_obb/weights/best.pt models/betel_nut_obb_best.pt

# 2. 运行系统（会自动加载OBB模型）
python run.py
```

系统会自动按以下优先级查找模型：
1. `models/betel_nut_obb_best.pt` ⭐ **OBB模型（优先）**
2. `runs/obb/betel_nut_obb/weights/best.pt`
3. `models/betel_nut_best.pt`
4. `yolov8n-obb.pt` (预训练OBB模型)
5. `yolov8n.pt` (普通预训练模型)

## 🎨 OBB vs 普通检测框

### OBB（旋转框）优势
- ✅ 精确的旋转角度（直接从模型输出）
- ✅ 更紧密的边界框
- ✅ 更准确的切割线定位
- ✅ 适合有明确方向的物体（如槟榔）

### 可视化效果
OBB模型会在UI上显示：
- 🟢 **旋转矩形框**（4个角点）
- 🔴 **中心点**
- 🔴 **精确切割线**（基于真实旋转角度）
- 📊 **检测参数**（类别、置信度、角度、偏移）

## 📊 训练监控

### 查看训练进度
```bash
# 训练日志
cat runs/obb/betel_nut_obb/train.log

# TensorBoard（如果安装）
tensorboard --logdir runs/obb
```

### 查看训练结果
训练完成后，检查以下文件：
- `runs/obb/betel_nut_obb/results.png` - 训练曲线
- `runs/obb/betel_nut_obb/confusion_matrix.png` - 混淆矩阵
- `runs/obb/betel_nut_obb/labels.jpg` - 标签分布
- `runs/obb/betel_nut_obb/val_batch*.jpg` - 验证结果示例

## 🔧 性能调优

### 提高训练速度
```bash
# 减小图像尺寸
--imgsz 320

# 减小batch size
--batch 8

# 减少epoch
--epochs 50
```

### 提高准确度
```bash
# 使用更大的模型
--model yolov8m-obb.pt

# 增加训练轮数
--epochs 200

# 增大图像尺寸
--imgsz 800
```

## 📈 预期性能指标

基于33张图片的小数据集：
- **训练时间**: 
  - CPU: ~30-60分钟 (100 epochs)
  - GPU: ~5-10分钟 (100 epochs)
- **mAP50**: 0.85+ (预期)
- **mAP50-95**: 0.70+ (预期)
- **推理速度**: 
  - yolov8n-obb: ~15-20ms/图 (GPU)
  - yolov8s-obb: ~25-30ms/图 (GPU)

## ⚠️ 注意事项

1. **数据集较小**: 33张图片较少，建议：
   - 使用数据增强（已启用）
   - 避免过拟合（设置patience=20）
   - 收集更多训练数据（推荐100+张）

2. **CPU训练慢**: 
   - 100 epochs在CPU上需要30-60分钟
   - 建议使用GPU或减少epochs

3. **模型选择**:
   - `yolov8n-obb`: 最快，适合实时检测
   - `yolov8s-obb`: 平衡速度和精度
   - `yolov8m-obb`: 最准确，但较慢

## 🔍 测试模型

使用训练好的模型进行测试：

```python
from ultralytics import YOLO
import cv2

# 加载模型
model = YOLO('models/betel_nut_obb_best.pt')

# 预测单张图片
results = model('test_img/Image_20251229192321280.bmp')

# 显示结果
results[0].show()

# 保存结果
results[0].save('result.jpg')
```

## 📚 参考资料

- [Ultralytics YOLOv8 OBB文档](https://docs.ultralytics.com/tasks/obb/)
- [YOLO OBB数据格式](https://docs.ultralytics.com/datasets/obb/)
- [训练技巧](https://docs.ultralytics.com/modes/train/)

---

**更新日期**: 2026-02-03  
**版本**: v1.0.0
