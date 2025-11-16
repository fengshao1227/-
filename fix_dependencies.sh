#!/bin/bash

echo "=========================================="
echo "  修复依赖问题"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}步骤1: 卸载PyQt5...${NC}"
pip3 uninstall -y PyQt5 PyQt5-Qt5 PyQt5-sip 2>/dev/null
echo -e "${GREEN}✓ 完成${NC}"
echo ""

echo -e "${YELLOW}步骤2: 安装PyQt6...${NC}"
pip3 install PyQt6
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PyQt6 安装成功${NC}"
else
    echo -e "${RED}✗ PyQt6 安装失败${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}步骤3: 验证PyQt6安装...${NC}"
python3 -c "import PyQt6; print('PyQt6 version:', PyQt6.QtCore.PYQT_VERSION_STR)"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PyQt6 验证成功${NC}"
else
    echo -e "${RED}✗ PyQt6 验证失败${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}步骤4: 测试GUI模块...${NC}"
python3 -c "from gui_main import MainWindow; print('GUI模块导入成功')"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ GUI模块测试通过${NC}"
else
    echo -e "${RED}✗ GUI模块测试失败${NC}"
    exit 1
fi
echo ""

echo "=========================================="
echo -e "${GREEN}✓ 所有依赖问题已修复！${NC}"
echo "=========================================="
echo ""
echo "下一步: 运行打包前检查"
echo "  ./pre_build_check.sh"
echo ""

