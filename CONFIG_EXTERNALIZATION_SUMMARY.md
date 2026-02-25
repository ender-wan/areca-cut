# 配置外置化完成总结

## 完成内容

### ✅ 1. 创建配置管理器 (config_manager.py)
- 从exe同目录读取 `config.json`
- 首次运行自动创建默认配置
- 支持配置热加载
- 保持向后兼容性（config.py导入不变）

### ✅ 2. 配置文件结构
```json
{
    "plc": {...},              // PLC配置
    "pc": {...},               // PC配置  
    "cameras": [...],          // 8个相机配置
    "trigger_values": {...},   // 触发值定义
    "class_values": {...},     // 分类值定义
    "camera_params": {...},    // 相机参数
    "model": {...},            // YOLO模型配置
    "poll_interval": 0.1,      // 轮询间隔
    "log": {...}               // 日志配置
}
```

### ✅ 3. 文档和脚本
- `CONFIG_GUIDE.md` - 详细配置说明
- `build_with_config.bat` - 自动打包脚本（包含配置复制）
- `dist/BetelNutVisionSystem/README.txt` - 用户快速指南

---

## 使用方式

### 开发环境
```bash
# 配置文件在工程根目录
E:\areca\betel-nut-vision-system\config.json

# 修改后直接运行
python run.py
```

### 生产环境
```
BetelNutVisionSystem\
├── BetelNutVisionSystem.exe
├── config.json              ← 在这里修改配置
├── README.txt               ← 使用说明
├── CONFIG_GUIDE.md          ← 详细配置指南
└── _internal\
```

**修改配置流程**：
1. 记事本打开 `config.json`
2. 修改需要的参数（如IP地址）
3. 保存文件
4. 重启 exe

⚠️ **无需重新打包exe！**

---

## 主要优势

### 1. 配置与代码分离
- exe内嵌默认配置
- 运行时优先读取外部config.json
- 现场修改无需源码和重新编译

### 2. 便于现场调试
```
修改PLC IP:     30秒（编辑config.json）
VS
重新打包exe:    5分钟（修改代码+打包+部署）
```

### 3. 减少更新成本
```
更新配置:   只需传输config.json（3KB）
更新程序:   只需传输exe（26MB）
完整部署:   exe + _internal + config.json（约550MB）
```

---

## 配置示例

### 修改PLC IP地址
```json
"plc": {
    "ip": "192.168.100.10",  ← 改这里
    "port": 502,
    "timeout": 3.0,
    "unit_id": 1
}
```

### 修改单个相机IP
```json
{
    "id": 1,
    "name": "Camera 1",
    "ip": "192.168.2.50",    ← 改这里
    "registers": {...}
}
```

### 调整轮询速度
```json
"poll_interval": 0.05        ← 改这里（秒）
```

### 使用其他模型
```json
"model": {
    "model_path": "models/new_model.pt",  ← 放新模型到models文件夹
    "device": "cpu"                        ← 强制CPU
}
```

---

## 测试验证

### 测试1: 配置加载
```bash
.\venv\Scripts\python.exe -c "from config_manager import load_config; print(load_config()['plc']['ip'])"
# 输出: 192.168.3.10 ✓
```

### 测试2: 首次运行自动创建配置
```bash
# 删除config.json
# 运行程序
# → 自动创建默认config.json ✓
```

### 测试3: 打包后配置外置
```bash
# 打包
.\venv\Scripts\python.exe -m PyInstaller BetelNutVisionSystem.spec --clean

# 复制config.json到dist目录
copy config.json dist\BetelNutVisionSystem\

# 运行exe
dist\BetelNutVisionSystem\BetelNutVisionSystem.exe
# → 从exe同目录读取config.json ✓
```

---

## 兼容性说明

### 旧代码完全兼容
```python
# 旧代码（仍然可用）
from config import PLC_CONFIG, CAMERA_CONFIGS
print(PLC_CONFIG['ip'])

# 新代码（推荐）
from config_manager import get_config
cfg = get_config()
print(cfg['plc']['ip'])
```

### 配置更新
```python
# 重新加载配置（无需重启程序）
from config import reload_config
reload_config()
```

---

## 打包流程更新

### 新的打包命令
```bash
# 使用虚拟环境打包（包含PyQt5和modbus_tk）
.\venv\Scripts\python.exe -m PyInstaller BetelNutVisionSystem.spec --clean

# 或使用自动化脚本
build_with_config.bat
```

### 打包输出
```
dist\BetelNutVisionSystem\
├── BetelNutVisionSystem.exe    (26MB)
├── config.json                  (3KB) ← 自动复制
├── CONFIG_GUIDE.md              ← 自动复制
├── README.txt                   ← 自动生成
└── _internal\                   (500MB)
    ├── PyQt5\                   ✓ 已包含
    ├── modbus_tk\               ✓ 已包含  
    └── models\obb_best_m.pt     ✓ 已内嵌
```

---

## 下一步建议

### 1. 版本控制
建议在config.json中添加版本信息：
```json
{
    "version": "1.0.0",
    "updated": "2026-02-05",
    ...
}
```

### 2. 配置校验
可以添加配置文件格式验证，防止错误配置导致程序崩溃

### 3. 配置备份
建议在首次修改配置前自动备份默认配置为 `config.json.backup`

### 4. GUI配置编辑器
未来可考虑在程序中添加"配置"菜单，提供可视化配置编辑界面

---

## 文件清单

### 新增文件
- ✅ `config_manager.py` - 配置管理器（核心）
- ✅ `CONFIG_GUIDE.md` - 配置详细说明
- ✅ `build_with_config.bat` - 自动化打包脚本
- ✅ `dist/BetelNutVisionSystem/README.txt` - 用户指南

### 修改文件
- ✅ `config.py` - 改为从config_manager导入
- ✅ `requirements.txt` - 修正modbus-tk依赖
- ✅ `BetelNutVisionSystem.spec` - 已优化（目录模式+PyQt5+modbus_tk）

### 生成文件
- ✅ `config.json` - 首次运行自动生成（包含默认配置）

---

**总结**: 配置外置化已完成，现在可以方便地修改配置而无需重新打包exe，大大提升了现场调试和维护效率！
