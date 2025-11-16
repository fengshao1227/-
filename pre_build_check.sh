#!/bin/bash

echo "=========================================="
echo "  课堂专注度检测系统 - 打包前检查"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# 1. 检查Python版本
echo "📋 [1/8] 检查Python版本..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Python版本: $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} 未找到Python3"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 2. 检查必需的模型文件
echo "📋 [2/8] 检查模型文件..."
if [ -f "yolov8m-pose.pt" ]; then
    SIZE=$(ls -lh yolov8m-pose.pt | awk '{print $5}')
    echo -e "${GREEN}✓${NC} yolov8m-pose.pt 存在 (大小: $SIZE)"
else
    echo -e "${RED}✗${NC} yolov8m-pose.pt 不存在"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 3. 检查PyQt6
echo "📋 [3/8] 检查PyQt6..."
python3 -c "import PyQt6; print('PyQt6 version:', PyQt6.QtCore.PYQT_VERSION_STR)" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} PyQt6 已安装"
else
    echo -e "${RED}✗${NC} PyQt6 未安装"
    echo "   请运行: pip3 install PyQt6"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 4. 检查torch
echo "📋 [4/8] 检查PyTorch..."
python3 -c "import torch; print('PyTorch version:', torch.__version__)" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} PyTorch 已安装"
else
    echo -e "${RED}✗${NC} PyTorch 未安装"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 5. 检查ultralytics
echo "📋 [5/8] 检查Ultralytics..."
python3 -c "import ultralytics; print('Ultralytics version:', ultralytics.__version__)" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Ultralytics 已安装"
else
    echo -e "${RED}✗${NC} Ultralytics 未安装"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 6. 检查opencv
echo "📋 [6/8] 检查OpenCV..."
python3 -c "import cv2; print('OpenCV version:', cv2.__version__)" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} OpenCV 已安装"
else
    echo -e "${RED}✗${NC} OpenCV 未安装"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 7. 检查matplotlib
echo "📋 [7/8] 检查Matplotlib..."
python3 -c "import matplotlib; print('Matplotlib version:', matplotlib.__version__)" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Matplotlib 已安装"
else
    echo -e "${RED}✗${NC} Matplotlib 未安装"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 8. 检查PyInstaller
echo "📋 [8/8] 检查PyInstaller..."
python3 -c "import PyInstaller; print('PyInstaller version:', PyInstaller.__version__)" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} PyInstaller 已安装"
else
    echo -e "${YELLOW}⚠${NC} PyInstaller 未安装"
    echo "   将在打包时自动安装"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 9. 测试GUI能否导入
echo "📋 [额外] 测试GUI模块导入..."
python3 -c "from gui_main import MainWindow" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} GUI模块可以正常导入"
else
    echo -e "${RED}✗${NC} GUI模块导入失败"
    echo "   请检查依赖是否完整"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 总结
echo "=========================================="
echo "  检查结果"
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ 所有检查通过！可以开始打包${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}✗ 发现 $ERRORS 个错误${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ 发现 $WARNINGS 个警告${NC}"
    fi
    echo ""
    echo "请先解决上述问题，然后重新运行此脚本"
    echo ""
    exit 1
fi

