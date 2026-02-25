# 生产环境部署指南

## 📦 打包配置（目录模式）

### 优势对比

#### 🔴 旧方案 - 单文件模式（--onefile）
- ✅ 只有一个exe文件
- ❌ exe文件超大（500MB+）
- ❌ 每次更新都要传输500MB+
- ❌ 客户端更新慢，占用大量带宽

#### ✅ 新方案 - 目录模式（当前配置）
- ✅ exe文件小（10-50MB）
- ✅ 依赖库在 `_internal` 文件夹（一次性部署）
- ✅ 后续更新只需替换小的exe文件
- ✅ 极大减少更新文件传输量

---

## 🚀 打包步骤

### 1. 准备环境

```bash
# 确保已安装依赖
pip install pyinstaller

# 确保模型文件存在
# models/obb_best_m.pt (YOLOv8m-obb训练的模型)
```

### 2. 执行打包

```bash
# 方式1：使用批处理脚本（推荐）
build_production.bat

# 方式2：手动执行
pyinstaller BetelNutVisionSystem.spec --clean
```

### 3. 打包输出

```
dist/
└── BetelNutVisionSystem/          # 完整程序目录
    ├── BetelNutVisionSystem.exe   # 主程序 (10-50MB)
    ├── _internal/                  # 依赖库文件夹 (500MB+)
    │   ├── python310.dll
    │   ├── torch/
    │   ├── cv2/
    │   ├── PyQt5/
    │   └── ... (所有DLL和依赖)
    ├── models/                     # 模型文件
    │   └── obb_best_m.pt          # YOLOv8m-obb模型
    ├── test_img/                   # 测试图片（可选）
    ├── logs/                       # 日志目录
    └── VERSION.txt                 # 版本信息
```

---

## 📤 部署流程

### 首次部署（完整包）

1. 将整个 `dist/BetelNutVisionSystem/` 文件夹打包
2. 传输到客户端（约500-700MB，一次性）
3. 解压后直接运行 `BetelNutVisionSystem.exe`

### 后续更新（仅exe）

当修改代码后：

1. 重新执行打包脚本：
   ```bash
   build_production.bat
   ```

2. 只需替换客户端的：
   ```
   BetelNutVisionSystem.exe  (约10-50MB)
   ```

3. **无需替换**：
   - `_internal/` 文件夹（依赖库不变）
   - `models/` 文件夹（模型未变化时）

**节省传输量：从500MB+ → 10-50MB，减少90%以上！**

---

## 🔧 配置说明

### BetelNutVisionSystem.spec 关键配置

```python
# 目录模式打包
exe = EXE(
    pyz,
    a.scripts,
    [],  # 不包含binaries
    exclude_binaries=True,  # 关键：排除二进制文件
    name='BetelNutVisionSystem',
    console=False,
)

# 收集所有文件到目录
coll = COLLECT(
    exe,
    a.binaries,  # 所有DLL和依赖库
    a.zipfiles,
    a.datas,
    name='BetelNutVisionSystem',  # 输出文件夹名
)
```

### 模型文件优先级

vision_detector.py 会按以下顺序查找模型：

1. ✅ `models/obb_best_m.pt` - YOLOv8m-obb（最新，优先）
2. `models/betel_nut_obb_best.pt` - 旧OBB模型（备用）
3. 其他历史模型（兼容性）

---

## 📊 文件大小对比

| 文件 | 大小 | 说明 |
|------|------|------|
| BetelNutVisionSystem.exe | ~10-50MB | 主程序（需要经常更新） |
| _internal/ | ~500MB+ | 依赖库（首次部署后不变） |
| models/obb_best_m.pt | ~50MB | YOLOv8m-obb模型 |
| 总计（首次） | ~600MB | 首次完整部署 |
| **更新** | **~10-50MB** | **后续只需替换exe** |

---

## ✅ 测试清单

打包完成后，必须测试：

- [ ] exe能正常启动
- [ ] 模型加载成功（检查日志）
- [ ] PLC连接正常（或Mock模式工作）
- [ ] 相机连接正常（或Mock模式工作）
- [ ] 图像检测功能正常
- [ ] 结果写入PLC正常
- [ ] 日志文件正常生成

---

## 🛠️ 故障排查

### 问题1：找不到模型文件

**症状**：启动后提示找不到模型

**解决**：
```bash
# 确保模型文件存在
ls models/obb_best_m.pt

# 如果不存在，复制训练好的模型
copy runs\obb\betel_nut_obb_m\weights\best.pt models\obb_best_m.pt
```

### 问题2：DLL缺失错误

**症状**：运行时报错缺少某个DLL

**解决**：
1. 检查 `_internal` 文件夹是否完整
2. 重新打包：`build_production.bat`
3. 确保整个 `dist/BetelNutVisionSystem/` 文件夹都复制到客户端

### 问题3：GPU不可用

**症状**：检测速度慢，日志显示使用CPU

**解决**：
- RTX 5080需要PyTorch 2.7+（当前2.0.1不支持）
- 系统会自动降级到CPU模式
- 性能影响不大（YOLOv8m在CPU上也很快）

---

## 📝 版本管理建议

每次打包后记录：

1. 版本号（手动维护）
2. 打包时间（自动生成在 `VERSION.txt`）
3. 主要变更内容
4. 对应的Git commit

示例：
```
Version: 1.2.0
Date: 2026-02-05 10:30:00
Changes:
  - 使用YOLOv8m-obb模型（97.8%检测率）
  - 优化目录模式打包
  - 修复PLC通信稳定性
Git: abc123
```

---

## 🎯 最佳实践

1. **首次部署**：传输完整的 `dist/BetelNutVisionSystem/` 文件夹
2. **日常更新**：只替换 `BetelNutVisionSystem.exe`
3. **模型更新**：替换 `models/obb_best_m.pt` + exe
4. **大版本更新**：重新传输完整文件夹（依赖库升级时）

---

## 📞 支持

如有问题，检查：
- `logs/` 文件夹中的日志文件
- `VERSION.txt` 确认版本
- 运行环境（Windows版本、.NET Framework等）
