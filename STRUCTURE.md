# 项目结构说明

betel-nut-vision-system/
│
├── __init__.py              # Python包初始化文件
│
├── config.py                # 【配置文件】
│   ├── PLC_CONFIG          # PLC连接参数 (IP, Port, Timeout)
│   ├── CAMERA_CONFIGS      # 8个相机的配置表
│   ├── TRIGGER_VALUES      # 触发状态定义 (10, 127, 128)
│   ├── CLASS_VALUES        # 分类定义 (1=异常, 2=可切, 3=备用)
│   └── CAMERA_PARAMS       # 相机参数 (曝光, 分辨率等)
│
├── plc_manager.py           # 【PLC通讯管理器】
│   └── PlcManager          # 线程安全的Modbus TCP客户端
│       ├── connect()       # 连接PLC
│       ├── disconnect()    # 断开PLC
│       ├── read_holding_register()   # 读取D寄存器
│       ├── write_holding_register()  # 写入D寄存器
│       └── write_multiple_registers() # 批量写入
│
├── vision_detector.py       # 【视觉识别算法接口】
│   ├── DetectionResult     # 结果数据类
│   │   ├── x_offset        # X轴偏移
│   │   ├── y_offset        # Y轴偏移
│   │   ├── r_angle         # 旋转角度
│   │   ├── height          # 产品高度
│   │   ├── classification  # 分类
│   │   └── confidence      # 置信度
│   │
│   └── VisionDetector      # 检测器类
│       ├── __init__()      # 加载模型
│       ├── detect_betel_nut() # 核心检测方法 ⚠️ 需替换为YOLO
│       └── release()       # 释放资源
│
├── camera_worker.py         # 【相机工作线程】
│   └── CameraWorker(QThread) # 单个相机的独立工作线程
│       ├── run()           # 主循环：轮询触发信号
│       ├── _process_trigger() # 处理触发流程
│       ├── _connect_camera()  # 连接相机 ⚠️ 需替换为真实SDK
│       ├── _capture_image()   # 拍照 ⚠️ 需替换为真实API
│       ├── _write_result_to_plc() # 回写结果
│       └── stop()          # 停止线程
│
├── main_window.py           # 【GUI主窗口】
│   ├── CameraWidget        # 单个相机的显示控件
│   │   ├── update_status() # 更新状态
│   │   ├── update_image()  # 更新图片
│   │   └── update_result() # 更新识别结果
│   │
│   ├── SettingsDialog      # 设置对话框
│   │   └── get_settings()  # 获取用户设置
│   │
│   └── MainWindow          # 主窗口类
│       ├── init_ui()       # 初始化界面
│       ├── connect_plc()   # 连接PLC
│       ├── start_system()  # 启动所有相机线程
│       ├── stop_system()   # 停止所有线程
│       └── add_log()       # 添加日志
│
├── mock_plc.py              # 【Mock PLC】用于测试
│   └── MockPlc
│       ├── read_holding_register()
│       ├── write_holding_register()
│       └── _auto_trigger_worker() # 自动触发线程
│
├── mock_camera.py           # 【Mock Camera】用于测试
│   └── MockCamera
│       ├── connect()
│       └── capture()       # 生成模拟图片
│
├── run.py                   # 【启动脚本】
│   └── main()              # 程序入口
│
├── requirements.txt         # Python依赖包列表
│
└── README.md                # 项目文档
