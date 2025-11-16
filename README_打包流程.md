# 课堂专注度检测系统 - 打包流程

## 🎯 一键打包（推荐）

```bash
# 1. 修复依赖问题
./fix_dependencies.sh

# 2. 运行打包（会自动检查环境）
./build_macos_improved.sh
```

就这么简单！脚本会自动完成所有步骤。

---

## 📋 详细步骤说明

### 第一步: 修复依赖问题

```bash
./fix_dependencies.sh
```

这个脚本会:
- ✅ 卸载PyQt5（与代码不兼容）
- ✅ 安装PyQt6（代码需要的版本）
- ✅ 验证安装是否成功
- ✅ 测试GUI模块能否正常导入

### 第二步: 打包应用

```bash
./build_macos_improved.sh
```

这个脚本会:
- ✅ 运行打包前检查（自动）
- ✅ 清理旧的打包文件
- ✅ 安装/更新所有依赖
- ✅ 使用PyInstaller打包
- ✅ 验证打包结果
- ✅ 设置正确的权限

---

## 🔍 如果遇到问题

### 问题1: fix_dependencies.sh 失败

**可能原因**: pip权限问题

**解决方法**:
```bash
# 使用用户安装模式
pip3 install --user PyQt6

# 或者使用sudo（不推荐）
sudo pip3 install PyQt6
```

### 问题2: 打包前检查失败

**查看具体错误**:
```bash
./pre_build_check.sh
```

根据错误提示安装缺失的依赖。

### 问题3: 打包过程中断

**查看详细日志**:
```bash
./build_macos_improved.sh 2>&1 | tee build.log
```

然后查看 `build.log` 文件找到具体错误。

---

## 📦 打包成功后

### 文件位置
```
dist/课堂专注度检测系统.app
```

### 测试应用
```bash
# 方法1: 双击应用图标

# 方法2: 命令行运行（可以看到错误信息）
./dist/课堂专注度检测系统.app/Contents/MacOS/课堂专注度检测系统
```

### 分发应用

**方法1: 直接分享**
- 将 `课堂专注度检测系统.app` 压缩成zip
- 分享给其他Mac用户

**方法2: 创建DMG镜像**
```bash
# 安装create-dmg工具
brew install create-dmg

# 创建DMG
create-dmg \
  --volname "课堂专注度检测系统" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --app-drop-link 425 120 \
  "课堂专注度检测系统.dmg" \
  "dist/课堂专注度检测系统.app"
```

---

## 🧪 完整测试清单

打包完成后，请测试以下功能:

- [ ] 应用能正常启动
- [ ] 界面显示正常
- [ ] 能选择视频文件
- [ ] 能调整参数（阈值、跳帧等）
- [ ] 能开始处理视频
- [ ] 进度条正常更新
- [ ] 能查看标注视频
- [ ] 视频播放正常
- [ ] 能查看统计图表
- [ ] 能导出CSV报告
- [ ] 能查看详细报告

---

## 📊 预期结果

### 应用大小
- **未压缩**: 约 800MB - 1.5GB
- **压缩后**: 约 400MB - 700MB

### 包含内容
- ✅ Python运行时
- ✅ PyQt6 GUI框架
- ✅ PyTorch深度学习框架
- ✅ Ultralytics YOLO模型
- ✅ OpenCV视频处理
- ✅ Matplotlib图表库
- ✅ yolov8m-pose.pt 模型文件
- ✅ 所有必需的依赖库

---

## 🎓 技术说明

### 为什么应用这么大？

因为包含了完整的Python环境和所有依赖:
- PyTorch: ~500MB
- PyQt6: ~100MB
- OpenCV: ~50MB
- Ultralytics: ~30MB
- 模型文件: ~51MB
- 其他依赖: ~200MB

### 可以减小体积吗？

可以，但会影响功能:
1. 使用更小的模型（yolov8n-pose.pt 只有6MB）
2. 排除不必要的torch模块
3. 使用CPU版本的PyTorch

不推荐减小体积，因为会影响检测精度和性能。

---

## 📞 需要帮助？

如果打包仍然失败，请提供:
1. 运行 `./pre_build_check.sh` 的完整输出
2. 运行 `./build_macos_improved.sh` 的完整输出
3. Python版本: `python3 --version`
4. macOS版本: `sw_vers`

---

## 🔄 更新应用

如果代码有更新，重新打包:

```bash
# 清理旧文件
rm -rf build dist

# 重新打包
./build_macos_improved.sh
```

---

## ✅ 成功标志

打包成功后，你会看到:

```
==========================================
✓ 打包完成！
==========================================

📦 生成的文件位置:
   dist/课堂专注度检测系统.app

📝 使用说明:
   1. 双击运行应用程序
   2. 如果提示'无法验证开发者'，请:
      - 右键点击应用 -> 打开
      - 或在'系统偏好设置 -> 安全性与隐私'中允许
```

恭喜！你的应用已经成功打包！🎉

