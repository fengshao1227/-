# GitHub Actions 自动打包指南

## 🎯 概述

使用GitHub Actions可以自动打包Windows和macOS两个平台的应用程序，完全免费，无需本地环境。

---

## ✨ 优势

- ✅ **完全免费** - GitHub Actions对公开仓库免费
- ✅ **自动化** - 推送标签即可触发
- ✅ **多平台** - 同时打包Windows和macOS
- ✅ **无需本地环境** - 不需要Windows电脑
- ✅ **自动发布** - 自动创建GitHub Release

---

## 🚀 快速开始（一键触发）

### 方法1: 使用自动化脚本（推荐）

```bash
# 给脚本添加执行权限
chmod +x trigger_github_build.sh

# 运行脚本
./trigger_github_build.sh
```

脚本会自动：
1. ✅ 检查git状态
2. ✅ 提示提交未保存的更改
3. ✅ 自动建议版本号
4. ✅ 创建并推送标签
5. ✅ 触发GitHub Actions
6. ✅ 显示进度查看链接

### 方法2: 手动操作

```bash
# 1. 提交所有更改
git add .
git commit -m "准备发布 v1.0.0"

# 2. 创建版本标签
git tag v1.0.0

# 3. 推送代码和标签
git push origin main
git push origin v1.0.0
```

---

## 📋 详细步骤

### 第一步: 确保代码已推送到GitHub

```bash
# 检查远程仓库
git remote -v

# 如果没有远程仓库，添加一个
git remote add origin https://github.com/你的用户名/classroom_attention.git

# 推送代码
git push -u origin main
```

### 第二步: 创建版本标签

```bash
# 创建标签（版本号格式: v主版本.次版本.修订号）
git tag -a v1.0.0 -m "Release v1.0.0"

# 推送标签到GitHub
git push origin v1.0.0
```

### 第三步: 查看打包进度

1. 打开GitHub仓库页面
2. 点击 **Actions** 标签
3. 查看 "打包应用程序" workflow
4. 等待打包完成（约15-20分钟）

### 第四步: 下载打包文件

打包完成后：
1. 进入 **Releases** 页面
2. 找到对应版本
3. 下载：
   - `课堂专注度检测系统-Windows.zip` (Windows版本)
   - `课堂专注度检测系统-macOS.zip` (macOS版本)

---

## 🔧 手动触发打包

如果不想创建标签，可以手动触发：

1. 打开GitHub仓库页面
2. 点击 **Actions** 标签
3. 选择 "打包应用程序" workflow
4. 点击 **Run workflow** 按钮
5. 选择分支（通常是main）
6. 点击 **Run workflow** 确认

**注意**: 手动触发不会创建Release，只会生成Artifacts

---

## 📊 打包流程说明

### Windows打包流程

```
1. 启动Windows虚拟机
2. 检出代码
3. 安装Python 3.10
4. 安装依赖 (PyQt6, PyTorch, Ultralytics等)
5. 运行PyInstaller打包
6. 上传 课堂专注度检测系统.exe
```

### macOS打包流程

```
1. 启动macOS虚拟机
2. 检出代码
3. 安装Python 3.10
4. 安装依赖 (PyQt6, PyTorch, Ultralytics等)
5. 运行PyInstaller打包
6. 上传 课堂专注度检测系统.app
```

### Release创建流程

```
1. 等待Windows和macOS打包完成
2. 下载两个平台的构建产物
3. 压缩成zip文件
4. 创建GitHub Release
5. 上传zip文件到Release
```

---

## ⏱️ 时间预估

| 步骤 | 预计时间 |
|------|----------|
| Windows打包 | 10-15分钟 |
| macOS打包 | 10-15分钟 |
| 创建Release | 1-2分钟 |
| **总计** | **15-20分钟** |

---

## 🐛 常见问题

### Q1: 打包失败怎么办？

**查看错误日志**:
1. 进入Actions页面
2. 点击失败的workflow
3. 查看具体步骤的错误信息

**常见错误**:
- 依赖安装失败 → 检查requirements.txt
- 模型文件未找到 → 确保yolov8m-pose.pt已提交
- PyInstaller错误 → 检查.github/workflows/build.yml配置

### Q2: 如何删除错误的标签？

```bash
# 删除本地标签
git tag -d v1.0.0

# 删除远程标签
git push origin :refs/tags/v1.0.0
```

### Q3: 可以修改版本号格式吗？

可以，但必须以 `v` 开头，例如：
- ✅ v1.0.0
- ✅ v2.1.3
- ✅ v1.0.0-beta
- ❌ 1.0.0 (缺少v)

### Q4: 打包的文件在哪里？

**如果是标签触发**:
- 在 Releases 页面下载

**如果是手动触发**:
- 在 Actions 页面，点击对应的workflow
- 下载 Artifacts (windows-exe 和 macos-app)

### Q5: 可以只打包一个平台吗？

可以，修改 `.github/workflows/build.yml`:

```yaml
# 只保留需要的job
jobs:
  build-windows:  # 只打包Windows
    ...
  # 注释掉或删除 build-macos
```

---

## 🔐 私有仓库说明

如果你的仓库是私有的：
- GitHub Actions 每月有2000分钟免费额度
- 超出后需要付费
- 建议使用公开仓库进行打包

---

## 📝 版本号建议

遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范：

```
v主版本.次版本.修订号

例如:
v1.0.0 - 首次发布
v1.0.1 - 修复bug
v1.1.0 - 新增功能
v2.0.0 - 重大更新
```

---

## 🎓 高级配置

### 自定义Release说明

编辑 `.github/workflows/build.yml` 中的 `body` 部分：

```yaml
- name: 创建Release
  uses: softprops/action-gh-release@v1
  with:
    body: |
      ## 你的自定义说明
      
      ### 新功能
      - 功能1
      - 功能2
```

### 添加预发布版本

```bash
# 创建beta版本
git tag -a v1.0.0-beta -m "Beta release"
git push origin v1.0.0-beta
```

在workflow中标记为预发布：

```yaml
- name: 创建Release
  uses: softprops/action-gh-release@v1
  with:
    prerelease: true  # 标记为预发布
```

---

## 📞 需要帮助？

如果遇到问题：
1. 查看 [GitHub Actions文档](https://docs.github.com/actions)
2. 查看 [PyInstaller文档](https://pyinstaller.org/)
3. 检查Actions日志中的错误信息

---

## ✅ 成功标志

打包成功后，你会看到：

1. ✅ Actions页面显示绿色对勾
2. ✅ Releases页面出现新版本
3. ✅ 可以下载两个zip文件
4. ✅ zip文件包含可执行程序

恭喜！你的应用已成功打包并发布！🎉

