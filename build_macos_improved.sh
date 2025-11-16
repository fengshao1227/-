#!/bin/bash

echo "=========================================="
echo "  课堂专注度检测系统 - macOS打包脚本"
echo "  改进版 v2.0"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 步骤1: 运行打包前检查
echo -e "${YELLOW}[1/6] 运行打包前检查...${NC}"
if [ -f "pre_build_check.sh" ]; then
    chmod +x pre_build_check.sh
    ./pre_build_check.sh
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ 打包前检查失败，请先解决问题${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ 未找到 pre_build_check.sh，跳过检查${NC}"
fi
echo ""

# 步骤2: 清理旧的打包文件
echo -e "${YELLOW}[2/6] 清理旧的打包文件...${NC}"
if [ -d "build" ]; then
    echo "删除 build/ 目录..."
    rm -rf build
fi
if [ -d "dist" ]; then
    echo "删除 dist/ 目录..."
    rm -rf dist
fi
if [ -f "课堂专注度检测系统.spec" ]; then
    echo "删除旧的 spec 文件..."
    rm -f "课堂专注度检测系统.spec"
fi
echo -e "${GREEN}✓ 清理完成${NC}"
echo ""

# 步骤3: 确保依赖已安装
echo -e "${YELLOW}[3/6] 检查并安装依赖...${NC}"
pip3 install --upgrade pip
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ 依赖安装失败${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 依赖安装完成${NC}"
echo ""

# 步骤4: 开始打包
echo -e "${YELLOW}[4/6] 开始打包应用程序...${NC}"
echo "这可能需要几分钟时间，请耐心等待..."
echo ""

pyinstaller --clean \
            --name="课堂专注度检测系统" \
            --windowed \
            --onefile \
            --noconfirm \
            --add-data "yolov8m-pose.pt:." \
            --hidden-import=cv2 \
            --hidden-import=numpy \
            --hidden-import=pandas \
            --hidden-import=torch \
            --hidden-import=torchvision \
            --hidden-import=ultralytics \
            --hidden-import=ultralytics.engine \
            --hidden-import=ultralytics.models \
            --hidden-import=ultralytics.nn \
            --hidden-import=ultralytics.utils \
            --hidden-import=PyQt6 \
            --hidden-import=PyQt6.QtCore \
            --hidden-import=PyQt6.QtGui \
            --hidden-import=PyQt6.QtWidgets \
            --hidden-import=matplotlib \
            --hidden-import=matplotlib.pyplot \
            --hidden-import=matplotlib.backends \
            --hidden-import=matplotlib.backends.backend_qtagg \
            --hidden-import=PIL \
            --hidden-import=PIL.Image \
            --collect-all PyQt6 \
            --collect-all ultralytics \
            --collect-all torch \
            --collect-submodules matplotlib \
            --exclude-module PySide6 \
            --exclude-module PySide2 \
            --exclude-module PyQt5 \
            --exclude-module tkinter \
            --exclude-module IPython \
            --exclude-module jupyter \
            --exclude-module notebook \
            --exclude-module pytest \
            --exclude-module sphinx \
            gui_main.py

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ 打包失败${NC}"
    exit 1
fi
echo ""

# 步骤5: 验证打包结果
echo -e "${YELLOW}[5/6] 验证打包结果...${NC}"
if [ -f "dist/课堂专注度检测系统.app/Contents/MacOS/课堂专注度检测系统" ]; then
    echo -e "${GREEN}✓ 应用程序已生成${NC}"
    
    # 设置执行权限
    chmod +x "dist/课堂专注度检测系统.app/Contents/MacOS/课堂专注度检测系统"
    
    # 检查文件大小
    APP_SIZE=$(du -sh "dist/课堂专注度检测系统.app" | awk '{print $1}')
    echo "  应用大小: $APP_SIZE"
    
    # 检查模型文件是否打包进去
    if [ -f "dist/课堂专注度检测系统.app/Contents/MacOS/yolov8m-pose.pt" ]; then
        echo -e "${GREEN}✓ 模型文件已打包${NC}"
    else
        echo -e "${YELLOW}⚠ 警告: 模型文件可能未正确打包${NC}"
    fi
else
    echo -e "${RED}✗ 应用程序生成失败${NC}"
    exit 1
fi
echo ""

# 步骤6: 完成
echo "=========================================="
echo -e "${GREEN}✓ 打包完成！${NC}"
echo "=========================================="
echo ""
echo "📦 生成的文件位置:"
echo "   dist/课堂专注度检测系统.app"
echo ""
echo "📝 使用说明:"
echo "   1. 双击运行应用程序"
echo "   2. 如果提示'无法验证开发者'，请:"
echo "      - 右键点击应用 -> 打开"
echo "      - 或在'系统偏好设置 -> 安全性与隐私'中允许"
echo ""
echo "   3. 可以将应用拖到'应用程序'文件夹"
echo ""
echo "🧪 建议测试:"
echo "   - 打开应用程序"
echo "   - 选择一个测试视频"
echo "   - 运行检测功能"
echo ""

