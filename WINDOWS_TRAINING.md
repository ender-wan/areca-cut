# Windows环境下模型训练指南

## 环境准备

### 1. 安装CUDA和cuDNN（GPU训练）

**推荐配置：**
- CUDA 11.8 或 12.1
- cuDNN 8.9+
- NVIDIA显卡驱动（最新版本）

下载链接：
- CUDA: https://developer.nvidia.com/cuda-downloads
- cuDNN: https://developer.nvidia.com/cudnn

### 2. 安装Python环境

```powershell
# 使用Anaconda（推荐）
conda create -n betel-nut python=3.11
conda activate betel-nut

# 或使用系统Python
python --version  # 确保3.8+
```

### 3. 安装依赖

```powershell
# 进入项目目录
cd betel-nut-vision-system

# 安装PyTorch（GPU版本）
# 访问 https://pytorch.org/get-started/locally/ 选择配置
# CUDA 11.8示例:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1示例:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 安装其他依赖
pip install -r requirements.txt

# 验证GPU可用
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU count: {torch.cuda.device_count()}')"
```

## 数据集检查

```powershell
# 检查数据集结构
dir test_img\labeled_img-at-2026-02-03-09-18-20f902cd

# 应该看到:
# ├── images\     (33张.bmp图片)
# ├── labels\     (33个.txt标注文件)
# ├── train\      (已分割的训练集)
# └── val\        (已分割的验证集)
```

## 开始训练

### 方式1：使用OBB旋转框模型（推荐）

```powershell
# GPU训练（推荐）
python train_yolo_obb.py --device 0 --epochs 200 --batch 16

# 多GPU训练
python train_yolo_obb.py --device 0,1 --epochs 200 --batch 32

# CPU训练（非常慢，不推荐）
python train_yolo_obb.py --device cpu --epochs 100 --batch 4
```

**参数说明：**
- `--device 0`: 使用第一块GPU
- `--epochs 200`: 训练200轮
- `--batch 16`: batch size（根据显存调整）
- `--imgsz 640`: 图像尺寸
- `--model yolov8n-obb.pt`: 使用nano模型（可选s/m/l/x）

### 方式2：使用标准YOLO模型

```powershell
python train_yolo.py --device 0 --epochs 200 --batch 16
```

## 训练参数优化

### 根据显卡显存调整batch size

| 显存 | 推荐batch | 模型版本 |
|:---:|:---:|:---:|
| 4GB | 4-8 | yolov8n |
| 6GB | 8-16 | yolov8n/s |
| 8GB | 16-24 | yolov8s |
| 12GB+ | 32+ | yolov8m/l |

### 常用训练命令

```powershell
# 快速训练测试（50轮）
python train_yolo_obb.py --epochs 50 --batch 8 --device 0

# 完整训练（高精度）
python train_yolo_obb.py --epochs 300 --batch 16 --device 0 --model yolov8s-obb.pt

# 使用更大模型
python train_yolo_obb.py --epochs 200 --batch 8 --device 0 --model yolov8m-obb.pt

# 恢复训练（从中断处继续）
python train_yolo_obb.py --epochs 200 --batch 16 --device 0 --resume
```

## 监控训练过程

### 1. 实时日志

训练过程会在终端实时显示：
```
Epoch  GPU_mem  box_loss  cls_loss  dfl_loss  mAP50  mAP50-95
1/200  2.41G    1.234     0.567     1.890     0.123  0.056
```

### 2. TensorBoard可视化（可选）

```powershell
# 安装TensorBoard
pip install tensorboard

# 启动TensorBoard
tensorboard --logdir runs/obb
# 浏览器打开: http://localhost:6006
```

### 3. 查看训练结果

训练完成后，结果保存在：
```
runs/obb/betel_nut_obb/
├── weights/
│   ├── best.pt          # 最佳模型
│   └── last.pt          # 最后一轮模型
├── results.png          # 训练曲线
├── confusion_matrix.png # 混淆矩阵
└── val_batch*.jpg       # 验证样本
```

## 模型验证

```powershell
# 验证最佳模型
python train_yolo_obb.py --validate runs/obb/betel_nut_obb/weights/best.pt

# 测试检测效果
python test_obb_detection.py
```

## 模型部署

### 1. 复制模型到部署目录

```powershell
# 复制最佳模型
copy runs\obb\betel_nut_obb\weights\best.pt models\betel_nut_obb_best.pt
```

### 2. 测试完整系统

```powershell
# 运行GUI系统
python run.py
```

## 常见问题

### Q1: CUDA out of memory错误

**解决方案：**
```powershell
# 减小batch size
python train_yolo_obb.py --batch 4 --device 0

# 减小图像尺寸
python train_yolo_obb.py --imgsz 416 --batch 8 --device 0
```

### Q2: 训练速度很慢

**检查清单：**
1. 确认GPU正在使用：`nvidia-smi`
2. 确认CUDA版本匹配：`python -c "import torch; print(torch.version.cuda)"`
3. 升级显卡驱动
4. 关闭其他占用GPU的程序

### Q3: 数据集未找到

```powershell
# 检查数据集路径
type betel_nut_obb.yaml

# 确保path字段正确指向数据集
# path: test_img/labeled_img-at-2026-02-03-09-18-20f902cd
```

### Q4: 模型精度不够

**优化建议：**
1. 增加训练轮数（300-500 epochs）
2. 使用更大的模型（yolov8s/m/l-obb.pt）
3. 增加数据增强
4. 标注更多数据

## 性能基准

**参考训练时间（RTX 3060 12GB）：**
- yolov8n-obb: ~2分钟/epoch（batch=16）
- yolov8s-obb: ~3分钟/epoch（batch=16）
- yolov8m-obb: ~5分钟/epoch（batch=8）

**预期精度（33张训练图片）：**
- 100 epochs: mAP50 ~0.85-0.95
- 200 epochs: mAP50 ~0.90-0.98
- 300 epochs: mAP50 ~0.95-0.99

## 下一步

训练完成后：
1. ✅ 在test_obb_detection.py中测试模型
2. ✅ 复制best.pt到models/目录
3. ✅ 运行完整GUI系统验证
4. ✅ 调整切割算法参数
5. ✅ 部署到生产环境

---

**技术支持：** 参考 [OBB_TRAINING.md](OBB_TRAINING.md) 和 [GUIDE.md](GUIDE.md)
