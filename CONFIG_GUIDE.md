# 配置文件说明 (config.json)

## 配置文件位置
- **开发环境**: `betel-nut-vision-system/config.json`
- **生产环境**: `BetelNutVisionSystem.exe` 同目录下的 `config.json`

## 修改配置步骤
1. 用记事本或任何文本编辑器打开 `config.json`
2. 修改需要的配置项（注意JSON格式）
3. 保存文件
4. **重启程序**使配置生效

⚠️ **无需重新打包exe！** 只需修改config.json即可。

---

## 配置项说明

### 1. PLC配置 (`plc`)
```json
"plc": {
    "ip": "192.168.3.10",    // PLC的IP地址
    "port": 502,              // Modbus TCP端口（通常是502）
    "timeout": 3.0,           // 连接超时时间（秒）
    "unit_id": 1              // Modbus从站ID
}
```

### 2. PC配置 (`pc`)
```json
"pc": {
    "ip": "192.168.3.30"     // 本机IP地址（预留）
}
```

### 3. 相机配置 (`cameras`)
8个相机的配置数组，每个相机包含：

```json
{
    "id": 1,                  // 相机编号
    "name": "Camera 1",       // 相机名称
    "ip": "192.168.1.10",     // 相机IP地址
    "registers": {
        "trigger": 100,       // D100 - 触发/握手寄存器（读写）
        "class": 101,         // D101 - 分类结果（写）
        "x_offset": 102,      // D102 - X偏移量（写）
        "y_offset": 103,      // D103 - Y偏移量（写）
        "r_angle": 104,       // D104 - 旋转角度（写）
        "height": 105         // D105 - 产品高度（写）
    }
}
```

**寄存器规律**: 每个相机间隔10（Camera 1从D100开始，Camera 2从D110开始...）

### 4. 触发值定义 (`trigger_values`)
```json
"trigger_values": {
    "READY": 10,             // PLC写入10表示触发拍照
    "PROCESSING": 127,       // PC写入127表示正在处理
    "IMAGE_READY": 128       // PC写入128表示处理完成
}
```

**PLC交互流程**:
1. PLC写D100=10（触发相机1）
2. PC读到10，开始拍照，写D100=127
3. PC拍照完成，写D100=128
4. PC识别完成，写分类和坐标到D101-D105
5. PLC读到128，取走结果，重置D100=0

### 5. 分类值定义 (`class_values`)
```json
"class_values": {
    "UNKNOWN": 1,            // 无法识别/异常
    "CUTTABLE": 2,           // 可切（正常）
    "RESERVED": 3            // 备用分类
}
```

写入到`class`寄存器（D101, D111...），仅当分类=2时才写入坐标数据。

### 6. 相机参数 (`camera_params`)
```json
"camera_params": {
    "exposure": 5000,        // 曝光时间（微秒）
    "gain": 10,              // 增益
    "width": 1920,           // 图像宽度
    "height": 1080,          // 图像高度
    "timeout": 5000          // 拍照超时（毫秒）
}
```

### 7. YOLO模型配置 (`model`)
```json
"model": {
    "model_path": "models/obb_best_m.pt",  // 模型文件路径
    "device": "auto"                        // 'auto', 'cuda', 'cpu'
}
```

**设备选择**:
- `auto`: 自动检测（优先GPU）
- `cuda`: 强制使用GPU
- `cpu`: 强制使用CPU

### 8. 轮询间隔 (`poll_interval`)
```json
"poll_interval": 0.1     // 轮询触发寄存器的间隔（秒）
```

建议值: 0.05-0.2秒

### 9. 日志配置 (`log`)
```json
"log": {
    "max_lines": 1000,       // 日志显示最大行数
    "log_file": "system.log" // 日志文件名
}
```

---

## 常见配置场景

### 场景1：修改PLC IP地址
```json
"plc": {
    "ip": "192.168.100.10",  // 改为新的PLC地址
    "port": 502,
    ...
}
```

### 场景2：修改单个相机IP
```json
{
    "id": 1,
    "name": "Camera 1",
    "ip": "192.168.2.50",    // 改为新的相机地址
    ...
}
```

### 场景3：调整相机曝光参数
```json
"camera_params": {
    "exposure": 8000,        // 增加曝光时间
    "gain": 15,              // 增加增益
    ...
}
```

### 场景4：使用不同的模型
```json
"model": {
    "model_path": "models/new_model.pt",  // 放新模型到models文件夹
    "device": "cpu"                        // 强制CPU运行
}
```

---

## JSON格式注意事项

✅ **正确格式**:
```json
{
    "ip": "192.168.1.10",  // 字符串用双引号
    "port": 502,           // 数字不用引号
    "timeout": 3.0         // 小数不用引号
}
```

❌ **错误格式**:
```json
{
    "ip": '192.168.1.10',  // ✗ 不能用单引号
    port: 502,             // ✗ 键必须加引号
    "timeout": 3.0,        // ✗ 最后一项不能有逗号
}
```

⚠️ **编辑建议**:
- 使用 [JSONLint](https://jsonlint.com/) 验证格式
- 或使用 VS Code / Notepad++ 等支持JSON高亮的编辑器
- 修改前备份原文件

---

## 故障排查

### 问题1: 程序启动后配置未生效
**原因**: JSON格式错误导致加载失败，使用默认配置
**解决**: 检查日志文件，查看是否有"加载配置失败"错误

### 问题2: 找不到config.json
**原因**: 首次运行会自动创建默认配置
**解决**: 正常现象，查看exe同目录是否已生成config.json

### 问题3: 修改后还是原来的值
**原因**: 程序未重启
**解决**: 关闭程序，重新打开

---

## 配置文件示例

完整的默认配置参见自动生成的 `config.json` 文件。
