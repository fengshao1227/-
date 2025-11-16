# 🎓 课堂专注度检测系统 (Classroom Attention Detection System)
https://github.com/mzniu/classroom_attention
基于YOLOv8姿态估计的智能课堂行为分析系统，自动识别学生专注状态并生成可视化报告。

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)
![CUDA](https://img.shields.io/badge/CUDA-11.8+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ 核心功能

### v2.0 增强版行为检测
- ✅ **长时间低头检测** - 持续低头超过3秒触发严重警告
- ✅ **闭眼检测** - 捕捉打瞌睡行为（持续2秒以上）
- ✅ **发呆检测** - 头部静止超4秒判定为发呆
- ✅ **短暂低头/侧身/手部异常** - 原始姿态异常检测
- ✅ **多目标跟踪** - 自动识别并跟踪每个学生
- ✅ **视频标注输出** - 红框标记不专注学生，生成可回放视频
- ✅ **CSV详细报告** - 包含时间戳、行为类型、持续时长
- ✅ **图形化界面** - 基于PyQt5的桌面GUI，操作简单直观

---

## 🏗️ 系统架构

```
输入视频 → YOLOv8-pose → 关键点提取 → 行为分析 → 状态追踪 → 可视化输出
                     ↓
              ByteTrack跟踪器 → 学生ID管理
                     ↓
              标注视频 & CSV报告
```

**技术栈**：
- **检测模型**: YOLOv8m-pose (COCO预训练)
- **跟踪算法**: ByteTrack (比DeepSORT更快更稳)
- **GPU加速**: PyTorch CUDA支持
- **视频处理**: OpenCV
- **数据分析**: Pandas

---

## 🚀 安装部署

### 环境要求
- **操作系统**: Windows 10/11 (推荐) / Linux / macOS
- **Python**: 3.9 或更高版本
- **显卡**: NVIDIA GPU (推荐RTX 3060+) 或 CPU模式
- **存储**: 至少5GB可用空间

### 快速安装

```bash
# 1. 克隆项目
git clone https://github.com/mzniu/classroom_attention.git
cd classroom——attention

# 2. 创建conda环境
conda create -n classroom_attention python=3.9 -y
conda activate classroom_attention

# 3. 安装依赖
pip install -r requirements.txt

# 4. 如果没有下载本地模型，项目首次运行会自动下载YOLO模型 (~50MB)
```



**GPU用户额外安装**:
```bash
# CUDA 12.6版本
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

---

## 📖 使用方法

### 方法1: 图形化界面（推荐）

```bash
# 启动GUI界面
./run_gui.sh

# 或直接运行
python3 gui_main.py
```

**GUI界面功能**：
- 📁 可视化选择视频文件
- ⚙️ 直观调整检测参数
- 📊 实时查看统计图表
- 📋 查看详细分析报告
- 💾 一键导出CSV和视频

详细使用说明请查看：[GUI使用说明](docs/GUI使用说明.md)

### 方法2: 命令行模式

```bash
# 基础检测（生成CSV报告）
python ca_gpu.py classroom_video.mp4

# 保存标注视频（推荐）
python ca_gpu.py classroom_video.mp4 --save-video

# 调整敏感度（阈值越低越严格）
python ca_gpu.py classroom_video.mp4 --threshold 40 --save-video
```

### 高级参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--threshold` | 专注度阈值(0-100)，越低越严格 | 50 |
| `--skip-frames` | 跳帧数(0=处理所有帧)，提升速度 | 2 |
| `--save-video` | 保存标注视频 | 不保存 |
| `--output` | 输出视频文件名 | output_annotated.mp4 |
| `--max-frames` | 测试模式：只处理前N帧 | 0(全部) |

### 命令示例

```bash
# 场景1：快速测试前1000帧
python ca_v2.py /path/to/video.mp4 --save-video --max-frames 1000

# 场景2：严格模式，检测所有细微行为
python ca_v2.py video.mp4 --threshold 30 --skip-frames 1 --save-video

# 场景3：处理长视频，只显示边框不显示文字
python ca_v2.py video.mp4 --save-video --no-labels --threshold 60

# 场景4：CPU模式（无GPU）
python ca_v2.py video.mp4 --device cpu --save-video
```

---

## 📊 输出结果

### 1. 可视化标注视频
- **红色粗边框**: 长时间不专注（低头/闭眼/发呆）
- **红色细边框**: 短期不专注
- **绿色边框**: 专注状态
- **标签信息**: 学生ID、状态、分数、行为原因

### 2. CSV详细报告 (`attention_report.csv`)
```csv
student_id,time_sec,time_str,frame,score,reason,bbox
12,15.67,0:00:15,783,25,长时间低头(3.2s);发呆(4.1s),(125,340,189,456)
7,15.67,0:00:15,783,35,闭眼(2.4s),(234, 298, 267, 389)
```

### 3. 控制台汇总报告
```
============================================================
                 课堂专注度检测报告 v2.0
============================================================

【学生ID: 12】
不专注事件次数: 5
总不专注时长: 87.3秒
不专注时间段:
  1. 0:00:15 ~ 0:01:23 (持续 68.0秒)
     主因: 长时间低头(3.2s)
  2. 0:02:15 ~ 0:02:34 (持续 19.3秒)
     主因: 发呆(4.1s)

============================================================
总计不专注学生数: 8人
============================================================
```

---

## ⚙️ 配置调整指南

### 调整行为敏感度

```python
# 在 ca_v2.py 的Config类中修改

# 长时间低头: 从3秒改为2秒更敏感
HEAD_DOWN_DURATION = 2.0  

# 闭眼检测: 从2秒改为1.5秒
EYE_CLOSED_DURATION = 1.5  

# 发呆检测: 从4秒改为5秒更宽松
STILLNESS_DURATION = 5.0  

# 专注度阈值: 越低越严格
ATTENTION_SCORE_THRESHOLD = 40  # <50分判定为不专注
```

---

## 🎯 性能指标

| 硬件配置 | 处理速度 | 12.5万帧耗时 | GPU显存占用 |
|----------|----------|--------------|-------------|
| **RTX 4060 Ti 16GB** | ~250 FPS | **8-10分钟** | ~4GB |
| RTX 3060 12GB | ~200 FPS | 10-12分钟 | ~3.5GB |
| CPU (i7-12700K) | ~5 FPS | 7小时 | - |
| **CPU + 跳帧5** | ~30 FPS | 70分钟 | - |

---

## ⚠️ 重要注意事项

### ✅ 最佳实践
1. **视频质量**: 建议分辨率≥720p，帧率≥25fps
2. **拍摄角度**: 摄像头位于教室前方45度角，覆盖所有学生
3. **光照条件**: 避免背光，确保学生面部清晰可见
4. **测试建议**: 先用 `--max-frames 500` 测试，确认效果再处理完整视频

### ❌ 已知限制
- **遮挡问题**: 学生被遮挡超过1秒会导致ID切换
- **密集场景**: 教室超过50人时建议降低分辨率或增大跳帧
- **极端姿态**: 躺卧、大幅度转身可能导致关键点丢失

---

## 🔧 故障排除

### Q1: `RuntimeError: CUDA out of memory`
**解决**: 降低批处理量或处理分辨率
```bash
python ca_v2.py video.mp4 --skip-frames 3  # 跳更多帧
```

### Q2: `VideoWriter无法创建文件`
**解决**: 
1. 确保输出目录有写入权限
2. 使用绝对路径: `-o "C:/path/to/output.mp4"`

### Q3: `ImportError: No module named 'ultralytics'`
**解决**: 
```bash
pip install ultralytics==8.3.0
```

---

## 🚀 未来规划

- [x] 长时间低头检测
- [x] 闭眼/打瞌睡检测  
- [x] 发呆检测
- [ ] 聊天检测（双人距离分析）
- [ ] 举手检测（互动参与度）
- [ ] 多摄像头融合
- [ ] Web界面（实时预览）
- [ ] 云端部署方案

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📄 许可证

本项目采用 **MIT License** - 查看 [LICENSE.md](LICENSE.md) 文件了解详情

---

## 📞 联系支持

- **项目地址**: [https://github.com/mzniu/classroom_attention](https://github.com/mzniu/classroom_attention)
- **问题反馈**: [Issues页面](https://github.com/mzniu/classroom_attention/issues)
- **邮箱**: aindy@126.com

---

**如果觉得项目有帮助，请给颗⭐Star！**