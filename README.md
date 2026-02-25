# 槟榔视觉检测与切割定位系统

## 项目简介

这是一个基于PyQt5的工业视觉检测系统，用于槟榔的自动检测、分类和切割定位。系统通过Modbus TCP与PLC通讯，控制8路工业相机进行实时图像采集，使用YOLO深度学习模型进行槟榔识别和质量分类。

### 核心功能

- ✅ **多相机管理**: 支持8路海康工业相机并行工作
- ✅ **PLC通讯**: Modbus TCP协议，实时读写寄存器
- ✅ **视觉检测**: YOLO深度学习模型，自动识别槟榔并计算位置参数
- ✅ **三种模式**: 真实硬件/图片测试/Mock模拟，支持离线开发和测试
- ✅ **实时界面**: PyQt5 GUI，8宫格相机显示，状态监控
- ✅ **自动训练**: 提供YOLO模型训练脚本，支持自定义数据集

## 系统架构

```
┌─────────────┐
│   工控机PC   │ (192.168.3.30)
│  ┌────────┐  │
│  │ PyQt6  │  │ ← GUI界面
│  │  GUI   │  │
│  └───┬────┘  │
│      │       │
│  ┌───▼────┐  │
│  │  PLC   │  │ ← Modbus TCP通讯
│  │Manager │  │
│  └───┬────┘  │
│      │       │
└──────┼───────┘
       │ Modbus TCP
       │ (Port 502)
       │
┌──────▼───────┐
│   PLC服务器   │ (192.168.3.10)
└──────────────┘

┌──────────────────────────────────┐
│  8个工业相机 (192.168.1.110-117)  │
└──────────────────────────────────┘
```

## 核心模块

### 1. **plc_manager.py** - PLC通讯管理
- 线程安全的Modbus TCP客户端
- 读写保持寄存器（D寄存器）
- 自动重连机制

### 2. **camera_worker.py** - 相机工作线程
- 每个相机独立线程运行
- 完整流程：轮询 → 触发 → 拍照 → 识别 → 回写
- 信号机制实时更新GUI

### 3. **vision_detector.py** - 视觉识别算法
- 预留YOLO接口
- 输出：中心点(x,y)、角度(r)、高度(h)、分类

### 4. **main_window.py** - GUI主界面
- 8个相机实时状态监控
- 图片显示与数据展示
- 系统日志记录

### 5. **config.py** - 系统配置
- PLC地址和端口
- 8个相机的IP和寄存器映射表
- 触发状态和分类定义

## 工作流程

```
1. 轮询触发寄存器 (D100, D110, ..., D170)
   └─ 读取值 == 10 ?
      ├─ 是 → 进入步骤2
      └─ 否 → 继续轮询

2. 握手：写入127 (正在处理)
   └─ PLC收到确认

3. 拍照
   └─ 调用相机SDK获取图像

4. 握手：写入128 (图片就绪)
   └─ PLC收到确认

5. 视觉识别
   └─ detect_betel_nut(image) → DetectionResult

6. 回写结果
   ├─ 写入分类信号 (D101, D111, ...)
   │  ├─ 1 = 无法识别/异常
   │  ├─ 2 = 可切分类 (正常)
   │  └─ 3 = 备用分类
   │
   └─ 仅当分类=2时，写入坐标数据：
      ├─ X偏移 (D102, ...)
      ├─ Y偏移 (D103, ...)
      ├─ R角度 (D104, ...)
      └─ H高度 (D105, ...)

7. 回到待机状态
```

## 安装与运行

### 环境要求
- Python 3.8+
- macOS / Windows / Linux

### 安装步骤

```bash
# 1. 进入项目目录
cd betel-nut-vision-system

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行系统
python run.py
```

### Mock模式测试

系统已内置Mock模拟类，无需实际硬件即可测试：
- **MockPlc**: 模拟PLC，自动每3-8秒随机触发一个相机
- **MockCamera**: 模拟相机，**从test_img文件夹随机选择真实图片**（支持.bmp/.jpg/.png）

运行后会自动检测：
- 如果`pymodbus`未安装 → 使用MockPlc
- 相机连接失败 → 使用MockCamera（自动加载test_img文件夹中的33张测试图片）

## 替换为真实硬件

### 1. 替换PLC通讯

在 [plc_manager.py](plc_manager.py#L32-L47) 中：

```python
# 当前：自动检测pymodbus
if PYMODBUS_AVAILABLE:
    # 使用真实pymodbus
else:
    from mock_plc import MockPlc

# 修改：确保安装pymodbus后，删除Mock相关代码
```

### 2. 替换相机连接

在 [camera_worker.py](camera_worker.py#L149-L165) 的 `_connect_camera()` 方法：

```python
# 当前Mock实现：
from mock_camera import MockCamera
self.camera = MockCamera(self.camera_ip)

# 替换为真实SDK，例如海康威视：
from MvCameraControl import MvCamera
self.camera = MvCamera()
device_list = self.camera.enum_devices()
# 根据IP查找并连接设备
```

参考项目中现有的相机代码：
- `back-end/cameras/camera_factory.py`
- `back-end/cameras/camera.py`

### 3. 替换视觉算法

在 [vision_detector.py](vision_detector.py#L35-L77) 的 `detect_betel_nut()` 方法：

```python
# 当前Mock实现：模拟随机结果

# 替换为实际YOLO：
from ultralytics import YOLO
self.model = YOLO('best.pt')
results = self.model(image)
# 解析results...
```

参考项目中现有的算法代码：
- `back-end/core/yolo5_detection.py`
- `back-end/areca/business/detector.py`

## 配置表

| 相机ID | 相机IP | 触发寄存器 | 分类寄存器 | X偏移 | Y偏移 | R角度 | 高度 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 192.168.1.110 | D100 | D101 | D102 | D103 | D104 | D105 |
| 2 | 192.168.1.111 | D110 | D111 | D112 | D113 | D114 | D115 |
| 3 | 192.168.1.112 | D120 | D121 | D122 | D123 | D124 | D125 |
| 4 | 192.168.1.113 | D130 | D131 | D132 | D133 | D134 | D135 |
| 5 | 192.168.1.114 | D140 | D141 | D142 | D143 | D144 | D145 |
| 6 | 192.168.1.115 | D150 | D151 | D152 | D153 | D154 | D155 |
| 7 | 192.168.1.116 | D160 | D161 | D162 | D163 | D164 | D165 |
| 8 | 192.168.1.117 | D170 | D171 | D172 | D173 | D174 | D175 |

## 目录结构

```
betel-nut-vision-system/
├── __init__.py              # 包初始化
├── config.py                # 系统配置
├── plc_manager.py           # PLC通讯管理器
├── camera_worker.py         # 相机工作线程
├── vision_detector.py       # 视觉识别接口
├── main_window.py           # GUI主窗口
├── mock_plc.py              # Mock PLC (测试用)
├── mock_camera.py           # Mock Camera (测试用)
├── run.py                   # 启动脚本
├── requirements.txt         # 依赖列表
└── README.md                # 本文档
```

## 开发建议

1. **测试Mock模式**: 先在Mock模式下测试GUI逻辑和流程
2. **逐步替换**: 先替换PLC连接，再替换相机，最后替换算法
3. **日志调试**: 系统有完整的日志输出，方便调试
4. **线程安全**: PlcManager已实现线程安全，8个线程可以并发访问

## 三种运行模式

### 🎭 Mock模式（开发测试）

**自动使用test_img文件夹中的真实图片，无需硬件即可运行**

```bash
python run.py  # 自动降级到Mock模式
# MockCamera会自动从test_img/加载所有图片（支持.bmp/.jpg/.png）
# 当前已有33张真实标注图片可用
```

### 📁 图片测试模式（算法验证）

**添加更多测试图片**

```bash
# test_img文件夹已内置33张标注图片
# 可继续添加更多图片
cp your_images/*.jpg test_img/
python run.py
```

### 🏭 真实硬件模式（生产环境）

**连接海康相机和PLC**

```bash
# 确保网络连接和SDK已安装
python run.py
```

## YOLO模型训练

### 准备数据集

```
test_img/labeled/
├── images/ (图片)
└── labels/ (YOLO格式标注)
```

### 训练模型

```bash
# GPU训练（推荐）
python train_yolo.py --source test_img/labeled --epochs 200 --batch 32 --device 0

# CPU训练
python train_yolo.py --source test_img/labeled --epochs 100 --batch 8 --device cpu
```

### 部署模型

```bash
cp runs/train/betel_nut_detector/weights/best.pt models/betel_nut_best.pt
python run.py
```

## 技术支持

- 📖 **详细指南**: [GUIDE.md](GUIDE.md)
- 🏗️ **架构说明**: [STRUCTURE.md](STRUCTURE.md)
- 🧪 **快速测试**: `python test_system.py`

---

**版本**: v2.0.0  
**更新**: 2025-02-03  
**许可**: MIT License
