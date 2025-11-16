#!/bin/bash

echo "=========================================="
echo "  触发GitHub Actions自动打包"
echo "  支持: Windows + macOS"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 检查是否在git仓库中
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}✗ 错误: 当前目录不是git仓库${NC}"
    exit 1
fi

# 检查是否有远程仓库
if ! git remote get-url origin > /dev/null 2>&1; then
    echo -e "${RED}✗ 错误: 未配置远程仓库${NC}"
    echo "请先添加远程仓库:"
    echo "  git remote add origin https://github.com/你的用户名/仓库名.git"
    exit 1
fi

REMOTE_URL=$(git remote get-url origin)
echo -e "${BLUE}📍 远程仓库: ${REMOTE_URL}${NC}"
echo ""

# 检查是否有未提交的更改
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo -e "${YELLOW}⚠ 检测到未提交的更改${NC}"
    echo ""
    git status --short
    echo ""
    read -p "是否要提交这些更改? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        read -p "请输入提交信息: " COMMIT_MSG
        git add .
        git commit -m "$COMMIT_MSG"
        echo -e "${GREEN}✓ 更改已提交${NC}"
    else
        echo -e "${YELLOW}⚠ 跳过提交，将使用最后一次提交的代码进行打包${NC}"
    fi
    echo ""
fi

# 获取当前版本号
CURRENT_TAG=$(git describe --tags --abbrev=0 2>/dev/null)
if [ -z "$CURRENT_TAG" ]; then
    SUGGESTED_VERSION="v1.0.0"
    echo -e "${YELLOW}⚠ 未找到现有标签，建议版本号: ${SUGGESTED_VERSION}${NC}"
else
    echo -e "${BLUE}📌 当前最新标签: ${CURRENT_TAG}${NC}"
    # 自动递增版本号
    VERSION_NUM=$(echo $CURRENT_TAG | sed 's/v//')
    MAJOR=$(echo $VERSION_NUM | cut -d. -f1)
    MINOR=$(echo $VERSION_NUM | cut -d. -f2)
    PATCH=$(echo $VERSION_NUM | cut -d. -f3)
    NEXT_PATCH=$((PATCH + 1))
    SUGGESTED_VERSION="v${MAJOR}.${MINOR}.${NEXT_PATCH}"
    echo -e "${BLUE}💡 建议版本号: ${SUGGESTED_VERSION}${NC}"
fi
echo ""

# 询问版本号
read -p "请输入新版本号 (直接回车使用 ${SUGGESTED_VERSION}): " VERSION
if [ -z "$VERSION" ]; then
    VERSION=$SUGGESTED_VERSION
fi

# 确保版本号以v开头
if [[ ! $VERSION =~ ^v ]]; then
    VERSION="v${VERSION}"
fi

echo ""
echo -e "${YELLOW}准备创建标签: ${VERSION}${NC}"
echo ""

# 确认
read -p "确认要触发打包吗? 这将: 
  1. 创建标签 ${VERSION}
  2. 推送到GitHub
  3. 自动触发Windows和macOS打包
  4. 创建GitHub Release
继续? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}已取消${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/3] 创建标签...${NC}"
git tag -a "$VERSION" -m "Release $VERSION"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 标签创建成功${NC}"
else
    echo -e "${RED}✗ 标签创建失败${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}[2/3] 推送代码到GitHub...${NC}"
git push origin main 2>/dev/null || git push origin master
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 代码推送成功${NC}"
else
    echo -e "${YELLOW}⚠ 代码推送失败或已是最新${NC}"
fi

echo ""
echo -e "${YELLOW}[3/3] 推送标签到GitHub...${NC}"
git push origin "$VERSION"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 标签推送成功${NC}"
else
    echo -e "${RED}✗ 标签推送失败${NC}"
    echo "如果标签已存在，请先删除:"
    echo "  git tag -d $VERSION"
    echo "  git push origin :refs/tags/$VERSION"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✓ GitHub Actions 打包已触发！${NC}"
echo "=========================================="
echo ""
echo -e "${BLUE}📊 查看打包进度:${NC}"
echo "  ${REMOTE_URL/\.git/}/actions"
echo ""
echo -e "${BLUE}⏱️  预计时间:${NC}"
echo "  - Windows打包: 约10-15分钟"
echo "  - macOS打包: 约10-15分钟"
echo "  - 总计: 约15-20分钟"
echo ""
echo -e "${BLUE}📥 下载位置:${NC}"
echo "  打包完成后，在以下位置下载:"
echo "  ${REMOTE_URL/\.git/}/releases/tag/$VERSION"
echo ""
echo -e "${GREEN}提示: 打开浏览器查看进度${NC}"
echo ""

