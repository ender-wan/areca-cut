# 生产环境配置总结

## ✅ 已完成配置

### 1. 模型更新
- ✅ 使用 YOLOv8m-obb 模型（`models/obb_best_m.pt`）
- ✅ 97.8%检测率（44/45张测试通过）
- ✅ vision_detector.py 优先级已更新

### 2. 打包配置优化
- ✅ 修改为**目录模式**（exe + 依赖库分离）
- ✅ BetelNutVisionSystem.spec 已更新
- ✅ 后续更新只需替换小的exe文件

### 3. 文档创建
- ✅ PRODUCTION_DEPLOYMENT.md - 完整部署指南
- ✅ QUICK_DEPLOY.md - 快速部署手册
- ✅ build_production.bat - 自动化打包脚本

---

## 📦 打包方式对比

### 旧方案（单文件模式）
```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,    # ← 所有依赖都打包进exe
    a.zipfiles,
    a.datas,
    ...
)
```
**结果**：一个500MB+的巨大exe文件

### ✅ 新方案（目录模式）
```python
exe = EXE(
    pyz,
    a.scripts,
    [],                    # ← 不包含binaries
    exclude_binaries=True, # ← 关键配置
    ...
)

coll = COLLECT(
    exe,
    a.binaries,  # ← 依赖库单独放在 _internal 文件夹
    a.zipfiles,
    a.datas,
    ...
)
```
**结果**：
- exe：10-50MB
- _internal/：500MB+（首次部署后不需要再传）

---

## 🚀 打包命令

```bash
# 切换到项目目录
cd E:\areca\betel-nut-vision-system

# 执行打包
python -m PyInstaller BetelNutVisionSystem.spec --clean
```

**打包时间**：约5-10分钟（首次打包）

---

## 📂 输出结构

```
dist/
└── BetelNutVisionSystem/
    ├── BetelNutVisionSystem.exe    ← 主程序（约10-50MB）
    ├── _internal/                   ← 依赖库文件夹（约500MB）
    │   ├── python310.dll
    │   ├── torch/
    │   ├── cv2/
    │   ├── PyQt5/
    │   ├── ultralytics/
    │   └── ... (所有DLL和依赖)
    ├── models/
    │   └── obb_best_m.pt           ← YOLOv8m-obb模型（约50MB）
    ├── test_img/                    ← 测试图片（可选）
    ├── MvImport/                    ← 海康SDK
    └── logs/                        ← 日志目录
```

---

## 📤 部署流程

### 首次部署
1. 打包完成后，压缩整个 `dist/BetelNutVisionSystem/` 文件夹
2. 传输到客户端（约600MB，一次性）
3. 解压后直接运行 `BetelNutVisionSystem.exe`

### 后续更新（核心优势）
1. 修改代码后重新打包
2. **只传输 `BetelNutVisionSystem.exe`**（约10-50MB）
3. 覆盖客户端的旧exe文件
4. 重启程序

**节省传输量：从600MB → 10-50MB，减少90%+**

---

## 🎯 更新场景

| 场景 | 需要替换的文件 | 大小 |
|------|---------------|------|
| 修改业务逻辑 | exe | ~10-50MB |
| 修改界面代码 | exe | ~10-50MB |
| 修改配置文件 | exe | ~10-50MB |
| **更新模型** | exe + models/ | ~60-100MB |
| **升级依赖库** | 完整文件夹 | ~600MB |

---

## 📝 版本管理建议

每次打包后创建版本记录：

```
版本: 1.2.0
日期: 2026-02-05
模型: YOLOv8m-obb (obb_best_m.pt)
变更:
  - 使用新训练的YOLOv8m-obb模型
  - 优化目录模式打包
  - 检测率提升到97.8%
exe大小: 约15MB
```

---

## ✅ 验证清单

打包完成后检查：

1. **文件结构**
   - [ ] `BetelNutVisionSystem.exe` 存在
   - [ ] `_internal/` 文件夹存在且不为空
   - [ ] `models/obb_best_m.pt` 存在

2. **功能测试**
   - [ ] exe能正常启动
   - [ ] 查看日志文件（logs/）
   - [ ] 模型加载成功
   - [ ] GUI界面正常显示
   - [ ] PLC连接测试（或Mock模式）
   - [ ] 相机连接测试（或Mock模式）
   - [ ] 图像检测功能正常

3. **性能测试**
   - [ ] 检测速度正常
   - [ ] 内存占用正常
   - [ ] CPU/GPU使用率正常

---

## 🛠️ 故障排查

### 问题1：打包失败
**症状**：PyInstaller报错

**解决**：
```bash
# 清理缓存重新打包
rmdir /s /q build dist
python -m PyInstaller BetelNutVisionSystem.spec --clean
```

### 问题2：exe无法启动
**症状**：双击exe无响应或闪退

**解决**：
1. 检查 `_internal` 文件夹是否完整
2. 查看日志文件（logs/）
3. 尝试命令行运行查看错误：
   ```bash
   BetelNutVisionSystem.exe
   ```

### 问题3：找不到模型
**症状**：启动后日志显示找不到模型文件

**解决**：
```bash
# 确保模型文件存在
dir models\obb_best_m.pt

# 如果不存在，复制训练好的模型
copy F:\areca\runs\obb\runs\obb\betel_nut_obb_m\weights\best.pt models\obb_best_m.pt
```

---

## 🎯 最佳实践

1. **首次部署必须包含完整文件夹**
2. **日常更新只替换exe**
3. **模型更新时同时替换models文件夹**
4. **大版本升级时重新部署完整包**
5. **保留每个版本的exe文件作为备份**
6. **测试后再发布到生产环境**

---

## 📞 技术支持

如遇问题：
1. 检查日志文件（logs/system_*.log）
2. 确认版本号（VERSION.txt）
3. 验证运行环境（Windows 10+）
4. 检查依赖库完整性（_internal/）
