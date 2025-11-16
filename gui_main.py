#!/usr/bin/env python3
"""
课堂专注度检测系统 - PyQt5可视化界面
"""

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QProgressBar, QTextEdit, QGroupBox, QSpinBox,
                             QSlider, QGridLayout, QTabWidget, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QImage
import cv2
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('QtAgg')

# 配置matplotlib中文字体
import platform
if platform.system() == 'Darwin':  # macOS
    matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'STHeiti', 'SimHei']
elif platform.system() == 'Windows':
    matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi']
else:  # Linux
    matplotlib.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'Droid Sans Fallback', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 导入核心检测模块
from ca_gpu import ClassroomMonitor, Config


# ==================== 视频处理线程 ====================
class VideoProcessThread(QThread):
    """后台视频处理线程"""
    progress_update = pyqtSignal(int, str)  # 进度值, 状态消息
    finished = pyqtSignal(object, object)   # DataFrame, summary
    error = pyqtSignal(str)                 # 错误消息
    
    def __init__(self, video_path, config, max_frames=0):
        super().__init__()
        self.video_path = video_path
        self.config = config
        self.max_frames = max_frames
        self.is_running = True
    
    def run(self):
        """执行视频处理"""
        try:
            self.progress_update.emit(10, "正在加载YOLO模型...")
            
            # 创建监控器
            monitor = ClassroomMonitor(self.video_path, self.config)
            
            self.progress_update.emit(20, "开始处理视频...")
            
            # 处理视频
            df, summary = monitor.process(self.max_frames)
            
            self.progress_update.emit(100, "处理完成!")
            self.finished.emit(df, summary)
            
        except Exception as e:
            import traceback
            error_msg = f"处理出错:\n{str(e)}\n\n{traceback.format_exc()}"
            self.error.emit(error_msg)
    
    def stop(self):
        """停止处理"""
        self.is_running = False


# ==================== 视频播放器组件 ====================
class VideoPlayerWidget(QWidget):
    """视频播放器组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_path = None
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 30
        self.frame_skip = 1  # 跳帧播放，提高流畅度

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()

        # 视频显示区域
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("QLabel { background-color: black; }")
        self.video_label.setText("暂无视频")
        layout.addWidget(self.video_label)

        # 控制面板
        control_layout = QHBoxLayout()

        # 播放/暂停按钮
        self.play_btn = QPushButton("▶️ 播放")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.toggle_play)
        control_layout.addWidget(self.play_btn)

        # 停止按钮
        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_video)
        control_layout.addWidget(self.stop_btn)

        # 时间显示
        self.time_label = QLabel("00:00 / 00:00")
        control_layout.addWidget(self.time_label)

        # 播放速度选择
        control_layout.addWidget(QLabel("播放速度:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "1x", "1.5x", "2x"])
        self.speed_combo.setCurrentIndex(1)  # 默认1x
        self.speed_combo.currentIndexChanged.connect(self.change_speed)
        self.speed_combo.setEnabled(False)
        control_layout.addWidget(self.speed_combo)

        # 跳帧选择
        control_layout.addWidget(QLabel("跳帧:"))
        self.skip_combo = QComboBox()
        self.skip_combo.addItems(["不跳帧", "跳1帧", "跳2帧", "跳3帧"])
        self.skip_combo.setCurrentIndex(1)  # 默认跳1帧
        self.skip_combo.currentIndexChanged.connect(self.change_skip)
        self.skip_combo.setEnabled(False)
        control_layout.addWidget(self.skip_combo)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # 进度条
        progress_layout = QHBoxLayout()
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderReleased.connect(self.slider_released)
        progress_layout.addWidget(self.progress_slider)
        layout.addLayout(progress_layout)

        self.setLayout(layout)

    def load_video(self, video_path):
        """加载视频"""
        if not video_path or not os.path.exists(video_path):
            return

        # 释放之前的视频
        if self.cap:
            self.cap.release()

        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            QMessageBox.warning(self, "错误", "无法打开视频文件")
            return

        # 获取视频信息
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.current_frame = 0

        # 设置进度条
        self.progress_slider.setMaximum(self.total_frames - 1)
        self.progress_slider.setValue(0)
        self.progress_slider.setEnabled(True)

        # 启用控制按钮
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.speed_combo.setEnabled(True)
        self.skip_combo.setEnabled(True)

        # 显示第一帧
        self.show_frame(0)
        self.update_time_label()

    def show_frame(self, frame_number):
        """显示指定帧"""
        if not self.cap:
            return

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()

        if ret:
            # 转换颜色空间
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 调整大小以适应显示区域（使用更快的插值方法）
            label_size = self.video_label.size()
            h, w = frame.shape[:2]

            # 计算缩放比例
            scale = min(label_size.width() / w, label_size.height() / h)
            new_w = int(w * scale)
            new_h = int(h * scale)

            # 使用INTER_NEAREST进行快速缩放
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_NEAREST)

            # 转换为QImage
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

            # 显示
            self.video_label.setPixmap(QPixmap.fromImage(q_image))
            self.current_frame = frame_number

    def toggle_play(self):
        """切换播放/暂停"""
        if self.is_playing:
            self.pause_video()
        else:
            self.play_video()

    def play_video(self):
        """播放视频"""
        if not self.cap:
            return

        self.is_playing = True
        self.play_btn.setText("⏸️ 暂停")

        # 获取播放速度
        speed_index = self.speed_combo.currentIndex()
        speeds = [0.5, 1.0, 1.5, 2.0]
        speed = speeds[speed_index]

        # 设置定时器间隔（毫秒）- 考虑跳帧和播放速度
        interval = int(1000 / (self.fps * speed) * self.frame_skip)
        self.timer.start(interval)

    def pause_video(self):
        """暂停视频"""
        self.is_playing = False
        self.play_btn.setText("▶️ 播放")
        self.timer.stop()

    def stop_video(self):
        """停止视频"""
        self.pause_video()
        self.current_frame = 0
        self.show_frame(0)
        self.progress_slider.setValue(0)
        self.update_time_label()

    def next_frame(self):
        """播放下一帧"""
        if self.current_frame < self.total_frames - self.frame_skip:
            self.current_frame += self.frame_skip
            self.show_frame(self.current_frame)
            self.progress_slider.setValue(self.current_frame)
            self.update_time_label()
        else:
            # 播放结束
            self.pause_video()

    def slider_pressed(self):
        """进度条按下"""
        if self.is_playing:
            self.pause_video()

    def slider_released(self):
        """进度条释放"""
        frame_number = self.progress_slider.value()
        self.show_frame(frame_number)
        self.update_time_label()

    def update_time_label(self):
        """更新时间显示"""
        if not self.cap:
            return

        current_sec = int(self.current_frame / self.fps)
        total_sec = int(self.total_frames / self.fps)

        current_time = f"{current_sec // 60:02d}:{current_sec % 60:02d}"
        total_time = f"{total_sec // 60:02d}:{total_sec % 60:02d}"

        self.time_label.setText(f"{current_time} / {total_time}")

    def change_speed(self, index):
        """改变播放速度"""
        speeds = [0.5, 1.0, 1.5, 2.0]
        speed = speeds[index]

        # 如果正在播放，重新启动定时器
        if self.is_playing:
            was_playing = True
            self.pause_video()
        else:
            was_playing = False

        # 更新定时器间隔
        if was_playing:
            interval = int(1000 / (self.fps * speed) * self.frame_skip)
            self.timer.start(interval)
            self.is_playing = True

    def change_skip(self, index):
        """改变跳帧数"""
        self.frame_skip = index + 1  # 0->1, 1->2, 2->3, 3->4

        # 如果正在播放，重新启动定时器
        if self.is_playing:
            speed_index = self.speed_combo.currentIndex()
            speeds = [0.5, 1.0, 1.5, 2.0]
            speed = speeds[speed_index]

            self.timer.stop()
            interval = int(1000 / (self.fps * speed) * self.frame_skip)
            self.timer.start(interval)

    def closeEvent(self, event):
        """关闭事件"""
        if self.cap:
            self.cap.release()
        event.accept()


# ==================== 统计图表组件 ====================
class StatisticsCanvas(FigureCanvas):
    """统计图表画布"""
    
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(10, 4))
        super().__init__(self.fig)
        self.setParent(parent)
    
    def plot_statistics(self, summary):
        """绘制统计图表"""
        self.fig.clear()

        if not summary:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontsize=16)
            ax.axis('off')
            self.draw()
            return

        # 创建两个子图
        ax1 = self.fig.add_subplot(121)
        ax2 = self.fig.add_subplot(122)

        # 数据准备 - 确保学生ID是整数
        student_ids = sorted(summary.keys())
        student_id_labels = [f"学生{int(sid)}" for sid in student_ids]
        event_counts = [summary[sid]['event_count'] for sid in student_ids]
        durations = [summary[sid]['total_duration_sec'] for sid in student_ids]

        # X轴位置
        x_pos = range(len(student_ids))

        # 图1: 不专注事件次数
        bars1 = ax1.bar(x_pos, event_counts, color='#FF6B6B', alpha=0.7, width=0.6)
        ax1.set_xlabel('学生ID', fontsize=10)
        ax1.set_ylabel('不专注事件次数', fontsize=10)
        ax1.set_title('学生不专注事件统计', fontsize=12, fontweight='bold')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(student_id_labels, rotation=45, ha='right')
        ax1.grid(axis='y', alpha=0.3)

        # 在柱子上显示数值
        for bar in bars1:
            height = bar.get_height()
            if height > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom', fontsize=9)

        # 图2: 总不专注时长
        bars2 = ax2.bar(x_pos, durations, color='#4ECDC4', alpha=0.7, width=0.6)
        ax2.set_xlabel('学生ID', fontsize=10)
        ax2.set_ylabel('总不专注时长(秒)', fontsize=10)
        ax2.set_title('学生不专注时长统计', fontsize=12, fontweight='bold')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(student_id_labels, rotation=45, ha='right')
        ax2.grid(axis='y', alpha=0.3)

        # 在柱子上显示数值
        for bar in bars2:
            height = bar.get_height()
            if height > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}秒',
                        ha='center', va='bottom', fontsize=9)

        self.fig.tight_layout()
        self.draw()


# ==================== 主窗口 ====================
class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.video_path = None
        self.output_video_path = None
        self.df = None
        self.summary = None
        self.process_thread = None
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('课堂专注度检测系统 v2.0')
        self.setGeometry(100, 100, 1400, 800)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧控制面板
        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel, 1)
        
        # 右侧结果展示
        right_panel = self.create_result_panel()
        main_layout.addWidget(right_panel, 2)

    def create_control_panel(self):
        """创建左侧控制面板"""
        panel = QGroupBox("控制面板")
        layout = QVBoxLayout()

        # 视频选择
        video_group = QGroupBox("视频文件")
        video_layout = QVBoxLayout()

        self.video_label = QLabel("未选择视频")
        self.video_label.setWordWrap(True)
        video_layout.addWidget(self.video_label)

        select_btn = QPushButton("📁 选择视频文件")
        select_btn.clicked.connect(self.select_video)
        video_layout.addWidget(select_btn)

        video_group.setLayout(video_layout)
        layout.addWidget(video_group)

        # 参数设置
        param_group = QGroupBox("检测参数")
        param_layout = QGridLayout()

        # 专注度阈值
        param_layout.addWidget(QLabel("专注度阈值:"), 0, 0)
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(0, 100)
        self.threshold_spin.setValue(50)
        self.threshold_spin.setSuffix(" 分")
        param_layout.addWidget(self.threshold_spin, 0, 1)

        # 跳帧数
        param_layout.addWidget(QLabel("跳帧数:"), 1, 0)
        self.skip_frames_spin = QSpinBox()
        self.skip_frames_spin.setRange(0, 10)
        self.skip_frames_spin.setValue(2)
        param_layout.addWidget(self.skip_frames_spin, 1, 1)

        # 最大处理帧数
        param_layout.addWidget(QLabel("最大帧数:"), 2, 0)
        self.max_frames_spin = QSpinBox()
        self.max_frames_spin.setRange(0, 10000)
        self.max_frames_spin.setValue(0)
        self.max_frames_spin.setSpecialValueText("全部")
        param_layout.addWidget(self.max_frames_spin, 2, 1)

        param_group.setLayout(param_layout)
        layout.addWidget(param_group)

        # 控制按钮
        btn_layout = QVBoxLayout()

        self.start_btn = QPushButton("▶️ 开始检测")
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-size: 14px; padding: 10px; }")
        self.start_btn.clicked.connect(self.start_processing)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹️ 停止检测")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-size: 14px; padding: 10px; }")
        self.stop_btn.clicked.connect(self.stop_processing)
        btn_layout.addWidget(self.stop_btn)

        layout.addLayout(btn_layout)

        # 进度条
        progress_group = QGroupBox("处理进度")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.status_label)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # 导出按钮
        export_group = QGroupBox("导出结果")
        export_layout = QVBoxLayout()

        self.export_csv_btn = QPushButton("📊 导出CSV报告")
        self.export_csv_btn.setEnabled(False)
        self.export_csv_btn.clicked.connect(self.export_csv)
        export_layout.addWidget(self.export_csv_btn)

        self.open_video_btn = QPushButton("🎬 打开标注视频")
        self.open_video_btn.setEnabled(False)
        self.open_video_btn.clicked.connect(self.open_output_video)
        export_layout.addWidget(self.open_video_btn)

        export_group.setLayout(export_layout)
        layout.addWidget(export_group)

        layout.addStretch()
        panel.setLayout(layout)
        return panel

    def create_result_panel(self):
        """创建右侧结果展示面板"""
        panel = QGroupBox("检测结果")
        layout = QVBoxLayout()

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 标签页1: 视频预览
        video_tab = QWidget()
        video_layout = QVBoxLayout()
        self.video_player = VideoPlayerWidget()
        video_layout.addWidget(self.video_player)
        video_tab.setLayout(video_layout)
        self.tab_widget.addTab(video_tab, "🎬 视频预览")

        # 标签页2: 统计图表
        chart_tab = QWidget()
        chart_layout = QVBoxLayout()
        self.chart_canvas = StatisticsCanvas()
        chart_layout.addWidget(self.chart_canvas)
        chart_tab.setLayout(chart_layout)
        self.tab_widget.addTab(chart_tab, "📊 统计图表")

        # 标签页3: 详细报告
        report_tab = QWidget()
        report_layout = QVBoxLayout()
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QFont("Courier", 10))
        report_layout.addWidget(self.report_text)
        report_tab.setLayout(report_layout)
        self.tab_widget.addTab(report_tab, "📋 详细报告")

        layout.addWidget(self.tab_widget)
        panel.setLayout(layout)
        return panel

    def select_video(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.avi *.mov *.mkv);;所有文件 (*.*)"
        )

        if file_path:
            self.video_path = file_path
            self.video_label.setText(f"已选择: {os.path.basename(file_path)}")
            self.start_btn.setEnabled(True)

    def start_processing(self):
        """开始处理视频"""
        if not self.video_path:
            QMessageBox.warning(self, "警告", "请先选择视频文件!")
            return

        # 配置参数
        config = Config()
        config.ATTENTION_SCORE_THRESHOLD = self.threshold_spin.value()
        config.SKIP_FRAMES = self.skip_frames_spin.value()
        config.OUTPUT_VIDEO = True
        config.OUTPUT_VIDEO_PATH = "output_annotated.mp4"
        config.SHOW_LABELS = True

        # 禁用控制按钮
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.export_csv_btn.setEnabled(False)
        self.open_video_btn.setEnabled(False)

        # 创建并启动处理线程
        self.process_thread = VideoProcessThread(
            self.video_path,
            config,
            self.max_frames_spin.value()
        )
        self.process_thread.progress_update.connect(self.update_progress)
        self.process_thread.finished.connect(self.processing_finished)
        self.process_thread.error.connect(self.processing_error)
        self.process_thread.start()

    def stop_processing(self):
        """停止处理"""
        if self.process_thread and self.process_thread.isRunning():
            self.process_thread.stop()
            self.process_thread.wait()
            self.status_label.setText("已停止")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def update_progress(self, value, message):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def processing_finished(self, df, summary):
        """处理完成"""
        self.df = df
        self.summary = summary

        # 更新UI
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.export_csv_btn.setEnabled(True)
        self.open_video_btn.setEnabled(True)

        # 加载标注视频到播放器
        output_video = "output_annotated.mp4"
        if os.path.exists(output_video):
            self.video_player.load_video(output_video)
            # 自动切换到视频预览标签页
            self.tab_widget.setCurrentIndex(0)

        # 显示统计图表
        self.chart_canvas.plot_statistics(summary)

        # 显示详细报告
        report_text = self.format_report(summary)
        self.report_text.setText(report_text)

        # 显示完成消息
        QMessageBox.information(self, "完成", "视频处理完成！\n可在'视频预览'标签页查看标注结果。")

    def processing_error(self, error_msg):
        """处理错误"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        QMessageBox.critical(self, "错误", error_msg)

    def format_report(self, summary):
        """格式化报告文本"""
        if not summary:
            return "✅ 未检测到不专注行为！所有学生表现良好。"

        lines = ["=" * 70, "📊 课堂专注度检测报告", "=" * 70, ""]

        for student_id in sorted(summary.keys()):
            data = summary[student_id]
            lines.append(f"👤 学生ID: {student_id:02d}")
            lines.append(f"   📌 不专注事件次数: {data['event_count']}")
            lines.append(f"   ⏱️  总不专注时长: {data['total_duration_sec']}秒")
            lines.append(f"   📋 不专注时间段:")

            for i, time_range in enumerate(data['time_ranges'], 1):
                lines.append(
                    f"      {i}. {time_range['start']} ~ {time_range['end']} "
                    f"(持续 {time_range['duration_sec']}秒)"
                )
                lines.append(f"         原因: {time_range['reason']}")

            lines.append("")

        lines.extend([
            "=" * 70,
            f"📈 总计不专注学生数: {len(summary)}人",
            "=" * 70
        ])

        return "\n".join(lines)

    def export_csv(self):
        """导出CSV报告"""
        if self.df is None:
            QMessageBox.warning(self, "警告", "没有可导出的数据!")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存CSV报告", "attention_report.csv",
            "CSV文件 (*.csv);;所有文件 (*.*)"
        )

        if file_path:
            self.df.to_csv(file_path, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, "成功", f"CSV报告已保存至:\n{file_path}")

    def open_output_video(self):
        """打开输出视频"""
        if os.path.exists("output_annotated.mp4"):
            os.system(f'open "output_annotated.mp4"')  # macOS
        else:
            QMessageBox.warning(self, "警告", "标注视频文件不存在!")


# ==================== 主函数 ====================
def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion风格

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()

