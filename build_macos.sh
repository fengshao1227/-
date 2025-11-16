#!/bin/bash

echo "======================================"
echo "  课堂专注度检测系统 - macOS打包脚本"
echo "======================================"
echo ""

echo "[1/4] 检查Python环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误: 未找到Python，请先安装Python 3.8+"
    exit 1
fi

echo ""
echo "[2/4] 安装依赖..."
pip3 install -r requirements.txt
pip3 install pyinstaller

echo ""
echo "[3/4] 开始打包app..."
pyinstaller --name="课堂专注度检测系统" \
            --windowed \
            --onefile \
            --add-data "yolov8m-pose.pt:." \
            --hidden-import=cv2 \
            --hidden-import=torch \
            --hidden-import=ultralytics \
            --hidden-import=PyQt6 \
            --hidden-import=PyQt6.QtCore \
            --hidden-import=PyQt6.QtGui \
            --hidden-import=PyQt6.QtWidgets \
            --collect-all PyQt6 \
            --collect-all ultralytics \
            --exclude-module PySide6 \
            --exclude-module tkinter \
            --exclude-module IPython \
            --exclude-module jupyter \
            gui_main.py

echo ""
echo "[4/4] 打包完成！"
echo ""
echo "生成的app文件位置: dist/课堂专注度检测系统.app"
echo ""
echo "提示: 如果遇到权限问题，请运行:"
echo "  chmod +x dist/课堂专注度检测系统.app/Contents/MacOS/*"
echo ""

