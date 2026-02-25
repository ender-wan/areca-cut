#!/bin/bash
# macOS/Linux 快速启动脚本

echo "=========================================="
echo " 槟榔视觉检测与切割定位系统"
echo " Betel Nut Vision Detection System"
echo "=========================================="
echo ""

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

echo "Python版本:"
python3 --version
echo ""

# 检查依赖
echo "正在检查依赖..."
pip3 list | grep -E "PyQt6|numpy|opencv-python" > /dev/null
if [ $? -ne 0 ]; then
    echo "警告: 部分依赖未安装"
    read -p "是否现在安装? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip3 install -r requirements.txt
    fi
fi

echo ""
echo "启动系统..."
python3 run.py
