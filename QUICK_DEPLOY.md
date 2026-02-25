# 快速部署手册

## 📦 打包完成后的目录结构

```
dist/BetelNutVisionSystem/
├── BetelNutVisionSystem.exe    ← 主程序（10-50MB）
├── _internal/                   ← 依赖库文件夹（500MB+，首次部署）
│   ├── python310.dll
│   ├── torch/
│   ├── cv2/
│   ├── PyQt5/
│   └── ...
├── models/
│   └── obb_best_m.pt           ← YOLOv8m-obb模型
├── logs/                        ← 日志目录
└── VERSION.txt                  ← 版本信息
```

## 🚀 部署步骤

### 1️⃣ 首次部署（完整包）

1. 压缩整个文件夹：
   ```
   dist/BetelNutVisionSystem/ → BetelNutVisionSystem_v1.0.zip
   ```

2. 传输到客户端并解压

3. 运行 `BetelNutVisionSystem.exe`

### 2️⃣ 后续更新（仅exe）

当修改代码后：

1. **重新打包**：
   ```bash
   python -m PyInstaller BetelNutVisionSystem.spec --clean
   ```

2. **只替换exe**：
   ```
   dist/BetelNutVisionSystem/BetelNutVisionSystem.exe
   ```
   （约10-50MB，而不是整个500MB+的文件夹）

3. 传输到客户端，覆盖旧的exe文件

4. 重启程序即可

## ⚡ 优势

| 操作 | 旧方案（单文件） | 新方案（目录模式） |
|------|-----------------|-------------------|
| 首次部署 | 500MB+ | 600MB（只部署一次） |
| 代码更新 | 500MB | **10-50MB** ✅ |
| 传输时间 | 长 | **减少90%** ✅ |
| 客户体验 | 慢 | **快速** ✅ |

## 📋 注意事项

1. **首次部署必须包含 `_internal` 文件夹**
2. **后续更新只需替换exe**（除非依赖库升级）
3. **模型文件单独管理**（如果模型更新，同时替换 `models/obb_best_m.pt`）
4. **检查VERSION.txt确认版本**

## 🔍 验证清单

部署后必须检查：

- [ ] exe能正常启动
- [ ] 查看日志：`logs/system_*.log`
- [ ] 模型加载成功（日志中显示 `obb_best_m.pt`）
- [ ] PLC连接状态
- [ ] 相机连接状态
- [ ] 测试检测功能

## 📞 故障排查

### exe无法启动
- 检查 `_internal` 文件夹是否完整
- 查看日志文件

### 找不到模型
- 确认 `models/obb_best_m.pt` 存在
- 检查文件大小（约50MB）

### DLL缺失
- 重新部署完整的 `_internal` 文件夹

## 🎯 最佳实践

1. 每次打包后记录版本号
2. 保留历史版本的exe文件
3. 大版本更新时重新部署完整包
4. 小版本更新只替换exe
