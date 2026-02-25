# 打包问题修复记录

## 问题1：PyQt5模块缺失

### 错误现象
```
ModuleNotFoundError: No module named 'PyQt5'
```

### 原因分析
spec文件中PyQt5的hiddenimports不完整，缺少关键的sip模块

### 解决方案
修改 `BetelNutVisionSystem.spec`：

```python
hiddenimports = [
    # PyQt5 完整导入（必须包含所有子模块）
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui', 
    'PyQt5.QtWidgets',
    'PyQt5.QtPrintSupport',
    'PyQt5.QtNetwork',
    'sip',  # PyQt5依赖的sip模块（关键！）
    ...
]
```

---

## 问题2：Modbus库导入错误

### 原因分析
spec文件中错误地使用了pymodbus，实际项目使用的是modbus_tk

### 解决方案
```python
hiddenimports = [
    # Modbus（使用modbus_tk，不是pymodbus）
    'modbus_tk',
    'modbus_tk.modbus',
    'modbus_tk.modbus_tcp',
    'modbus_tk.defines',
    'serial',  # modbus_tk依赖pyserial
    ...
]
```

---

## 优化：模型文件打包

### 变更说明
只打包必需的obb_best_m.pt模型，减小包体积

### 修改内容
```python
datas = [
    ('models/obb_best_m.pt', 'models'),  # 只打包必需的模型文件
    ('MvImport', 'MvImport'),             # 海康SDK
    # test_img 不打包（减小体积）
]
```

**优势**：
- 减小打包体积
- 模型文件内嵌到exe包中
- 不依赖外部模型文件

---

## 验证步骤

### 1. 重新打包
```bash
cd E:\areca\betel-nut-vision-system
python -m PyInstaller BetelNutVisionSystem.spec --clean
```

### 2. 检查输出
```
dist/BetelNutVisionSystem/
├── BetelNutVisionSystem.exe
├── _internal/
│   ├── PyQt5/           ← 确认存在
│   ├── modbus_tk/       ← 确认存在
│   └── ...
└── models/
    └── obb_best_m.pt    ← 确认存在
```

### 3. 测试运行
```bash
dist\BetelNutVisionSystem\BetelNutVisionSystem.exe
```

检查日志：`dist\BetelNutVisionSystem\logs\system_*.log`

应该看到：
```
✓ PyQt5导入成功
✓ 模型加载成功: models/obb_best_m.pt
✓ PLC管理器初始化成功
```

---

## 打包配置总结

### 目录模式优势保留
- exe文件独立（约15-30MB）
- 依赖库在_internal文件夹（约500MB）
- **后续更新只需替换exe文件**

### 新增优化
- ✅ 修复PyQt5导入
- ✅ 修复modbus_tk导入
- ✅ 模型文件内嵌
- ✅ 移除测试图片（减小体积）

### 最终包结构
```
首次部署：完整文件夹（约550MB）
后续更新：只需exe（约15-30MB）
节省传输量：95%+
```
