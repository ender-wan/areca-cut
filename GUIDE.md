# 槟榔视觉检测系统 - 快速使用指南

## 📋 目录

- [系统架构](#系统架构)
- [三种运行模式](#三种运行模式)
- [快速开始](#快速开始)
- [YOLO模型训练](#yolo模型训练)
- [真实硬件部署](#真实硬件部署)
- [常见问题](#常见问题)

---

## 系统架构

```
┌─────────────────────────────────────────┐
│         GUI主界面 (main_window.py)      │
├─────────────────────────────────────────┤
│  8个相机工作线程 (camera_worker.py)     │
├──────────┬──────────┬──────────────────┤
│  PLC通讯 │  相机控制 │  视觉识别         │
│  Modbus  │  海康SDK  │  YOLO模型        │
└──────────┴──────────┴──────────────────┘
```

---

## 三种运行模式

### 1. 🎭 Mock模式（默认）
**适用场景**: 首次测试、界面开发、无硬件环境

**特点**:
- 自动生成模拟图片
- Mock PLC自动触发
- 随机生成检测结果

**使用方法**:
```bash
python run.py
# 系统会自动降级到Mock模式
```

---

### 2. 📁 图片测试模式
**适用场景**: 算法测试、离线调试、无相机环境

**特点**:
- 从test_img文件夹读取真实图片
- 使用真实YOLO模型
- 可以验证检测效果

**使用方法**:
```bash
# 1. 准备测试图片
mkdir -p test_img
cp /path/to/betel_images/*.jpg test_img/

# 2. 运行系统
python run.py
# 系统检测到test_img文件夹后自动使用图片测试模式
```

---

### 3. 🏭 真实硬件模式
**适用场景**: 生产环境部署

**特点**:
- 连接真实海康相机
- 连接真实PLC
- 使用训练好的YOLO模型

**使用方法**:
```bash
# 1. 确保海康SDK已安装
# 2. 确保相机和PLC网络连接正常
# 3. 运行系统
python run.py
# 系统会自动尝试连接真实硬件
```

---

## 快速开始

### 安装依赖

```bash
# 基础依赖（必需）
pip install PyQt5 numpy opencv-python pymodbus

# YOLO模型支持（推荐）
pip install ultralytics torch torchvision

# 或一键安装
pip install -r requirements.txt
```

### 运行系统

```bash
# macOS/Linux
./start.sh

# Windows
start.bat

# 或直接运行Python
python run.py
```

### GUI 操作说明

启动后会看到主界面，包含：

1. **顶部按钮栏**
   - `启动系统`: 开启所有8个相机工作线程
   - `停止系统`: 停止所有线程
   - `设置`: 修改PLC IP和相机参数
   - PLC状态指示灯（绿色=已连接）

2. **中间相机网格区**（8个相机，4x2布局）
   - 每个相机卡片显示：
     - 状态（待机/拍照中/计算中）
     - 图片缩略图
     - 识别结果（X, Y, R, H, 分类, 置信度）

3. **底部日志区**
   - 滚动显示系统日志
   - 可清空日志

### 快速测试

```bash
# 运行系统测试脚本
python test_system.py
```

---

## YOLO模型训练

### 准备数据集

```
test_img/labeled/
├── images/
│   ├── betel_001.jpg
│   ├── betel_002.jpg
│   └── ...
└── labels/
    ├── betel_001.txt   # YOLO格式标注
    ├── betel_002.txt
    └── ...
```

**YOLO标注格式** (`betel_001.txt`):
```
0 0.5 0.5 0.3 0.4
```
- 第1列: 类别ID（0=可切, 1=异常, 2=其他）
- 第2-3列: 中心点坐标（归一化）
- 第4-5列: 宽高（归一化）

### 训练模型

```bash
# 基础训练
python train_yolo.py --source test_img/labeled --epochs 100

# 高级训练（自定义参数）
python train_yolo.py \
    --source test_img/labeled \
    --model yolov8s.pt \
    --epochs 200 \
    --batch 32 \
    --imgsz 640 \
    --device 0

# GPU训练（推荐）
python train_yolo.py --device 0 --batch 32

# CPU训练
python train_yolo.py --device cpu --batch 8
```

### 部署模型

```bash
# 1. 训练完成后，复制最佳模型
cp runs/train/betel_nut_detector/weights/best.pt models/betel_nut_best.pt

# 2. 系统会自动加载models/下的模型
python run.py
```

### 验证模型

```bash
# 验证模型性能
python train_yolo.py --validate runs/train/betel_nut_detector/weights/best.pt

# 导出ONNX格式（加速推理）
python train_yolo.py \
    --validate runs/train/betel_nut_detector/weights/best.pt \
    --export onnx
```

---

## 真实硬件部署

### 海康相机配置

**1. 网络配置**
```
相机IP: 192.168.1.110-117（8个相机）
PC IP: 192.168.1.1
子网掩码: 255.255.255.0
```

**2. SDK安装**
```bash
# 复制海康SDK到项目
cp -r /path/to/MVS/Samples/64/Python/MvImport back-end/cameras/

# 验证SDK
python -c "from cameras.MvImport.MvCameraControl_class import *"
```

**3. 相机参数**
- 触发模式: 软触发
- 图像格式: RGB8
- 分辨率: 1920x1080
- 曝光时间: 根据实际调整

### PLC配置

**1. Modbus TCP设置**
```
PLC IP: 192.168.3.10
端口: 502
从站ID: 1
```

**2. 寄存器映射**（参考 [config.py](config.py#L30-L100)）

| 相机 | 触发寄存器 | 分类寄存器 | X偏移 | Y偏移 | R角度 | 高度 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | D100 | D101 | D102 | D103 | D104 | D105 |
| 2 | D110 | D111 | D112 | D113 | D114 | D115 |
| ... | ... | ... | ... | ... | ... | ... |

**3. 触发流程**
```
PLC写入10 → PC读取触发 → PC写入127(处理中) → 
拍照 → PC写入128(图片就绪) → 识别 → 
写入结果 → 回到待机
```

### 生产环境检查清单

- [ ] 网络连接正常（ping相机IP和PLC IP）
- [ ] 海康SDK已安装并测试
- [ ] YOLO模型已训练并验证（mAP > 0.9）
- [ ] PLC寄存器地址已确认
- [ ] 相机曝光参数已调整
- [ ] 系统日志查看正常
- [ ] 完整流程测试通过

---

## 常见问题

### Q1: 如何知道系统使用的是哪种模式？

A: 查看系统日志：
- `海康相机连接成功` → 真实硬件模式
- `图片测试模式连接成功` → 图片测试模式  
- `Mock相机连接成功` → Mock模式
- `已降级到Mock模式` → 硬件连接失败，使用Mock

### Q2: YOLO模型没有自动加载？

A: 检查以下位置：
```bash
models/betel_nut_best.pt   # 最优先
models/betel_nut_last.pt   # 次优先
yolov8n.pt                  # 预训练模型
```

或在代码中指定：
```python
detector = VisionDetector(model_path='your_model.pt')
```

### Q3: 图片测试模式没有图片？

A: 确保test_img文件夹中有图片：
```bash
ls test_img/*.jpg
# 支持: .jpg, .jpeg, .png, .bmp
```

### Q4: 相机连接失败？

A: 检查步骤：
```bash
# 1. 网络连通性
ping 192.168.1.110

# 2. SDK是否正确安装
python -c "from hikvision_camera import HIKVISION_SDK_AVAILABLE; print(HIKVISION_SDK_AVAILABLE)"

# 3. 查看详细日志
python run.py  # 查看终端输出
```

### Q5: 训练时显存不足？

A: 减小batch size或图像尺寸：
```bash
python train_yolo.py --batch 8 --imgsz 320
```

### Q6: 如何强制使用Mock模式？

A: 在vision_detector.py中：
```python
detector = VisionDetector(use_mock=True)
```

---

## 性能优化建议

### 推理速度优化

**1. 使用更小的模型**
```bash
yolov8n.pt  # nano, 最快
yolov8s.pt  # small
yolov8m.pt  # medium
```

**2. 导出ONNX**
```bash
python train_yolo.py --validate models/best.pt --export onnx
```

**3. 调整图像尺寸**
```python
# config.py
CAMERA_PARAMS = {
    'width': 1280,   # 降低分辨率
    'height': 720
}
```

### 准确度优化

**1. 数据增强**
- 增加训练数据量（>1000张）
- 多样化光照条件
- 不同角度拍摄

**2. 模型调优**
```bash
# 使用更大的模型
--model yolov8m.pt

# 增加训练轮数
--epochs 300

# 调整学习率
# 在train_yolo.py中修改lr0参数
```

**3. 后处理优化**
```python
# vision_detector.py中调整置信度阈值
if confidence > 0.7:  # 提高阈值
    classification = 2
```

---

## 技术支持

- 📖 README: 项目概述和快速开始
- 🏗️ STRUCTURE.md: 代码架构说明
- 🧪 test_system.py: 快速测试各模块
- 💬 Issue: 提交问题和建议

---

**更新日期**: 2025-02-03  
**版本**: v2.0.0 - 支持真实硬件、图片测试、YOLO训练
