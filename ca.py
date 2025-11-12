#!/usr/bin/env python3
"""
课堂专注度检测系统 (Windows终极修复版)
彻底隔离OpenCV与MediaPipe资源，避免句柄冲突
"""

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from datetime import timedelta
import argparse
import os
import sys
import warnings

# 完全禁用可能冲突的库
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 禁用所有TF日志
warnings.filterwarnings('ignore')
# 强制MediaPipe使用同步模式
os.environ['MEDIAPIPE_DISABLE_GPU'] = '1'

# ==================== 警告过滤系统 ====================
warnings.filterwarnings('ignore')
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['MEDIAPIPE_DISABLE_GPU'] = '1'

# 重定向stderr避免MediaPipe警告
import logging
logging.getLogger().setLevel(logging.ERROR)
sys.stderr = open(os.devnull, 'w')  # Windows关键修复
# ==================== 配置参数 ====================
class Config:
    """系统配置参数"""
    YOLO_MODEL = "yolo11m.pt"
    CONFIDENCE_THRESHOLD = 0.5
    PERSON_CLASS_ID = 0
    MAX_AGE = 30
    N_INIT = 3
    MAX_IOU_DISTANCE = 0.7
    MIN_DETECTION_CONFIDENCE = 0.5
    MIN_TRACKING_CONFIDENCE = 0.5
    HEAD_DOWN_THRESHOLD = 0.1
    SHOULDER_TILT_THRESHOLD = 30
    HAND_BELOW_HIP_THRESHOLD = 0.0
    ATTENTION_SCORE_THRESHOLD = 50
    SHOW_VISUALIZATION = False
    OUTPUT_VIDEO = False  # Windows下默认关闭视频输出
    OUTPUT_CSV = True
    SKIP_FRAMES = 5  # 默认跳帧，减少资源占用


# ==================== 资源管理器 ====================
class ResourceManager:
    """独立管理所有模型资源，避免冲突"""
    
    @staticmethod
    def create_yolo():
        """创建YOLO检测器"""
        try:
            model = YOLO(Config.YOLO_MODEL)
            print("✓ YOLO模型加载成功")
            return model
        except Exception as e:
            print(f"✗ YOLO加载失败: {e}")
            return None
    
    @staticmethod
    def create_tracker():
        """创建DeepSORT跟踪器"""
        try:
            tracker = DeepSort(
                max_age=Config.MAX_AGE,
                n_init=Config.N_INIT,
                max_iou_distance=Config.MAX_IOU_DISTANCE
            )
            print("✓ DeepSORT跟踪器初始化成功")
            return tracker
        except Exception as e:
            print(f"✗ DeepSORT初始化失败: {e}")
            return None
    
    @staticmethod
    def create_pose_estimator():
        """创建MediaPipe姿态估计器"""
        try:
            # 在独立进程中初始化
            mp_pose = mp.solutions.pose
            estimator = mp_pose.Pose(
                static_image_mode=True,  # Windows下使用静态模式更稳定
                model_complexity=0,  # 使用轻量级模型
                min_detection_confidence=Config.MIN_DETECTION_CONFIDENCE,
                min_tracking_confidence=Config.MIN_TRACKING_CONFIDENCE
            )
            print("✓ MediaPipe姿态估计器初始化成功")
            return estimator
        except Exception as e:
            print(f"✗ MediaPipe初始化失败: {e}")
            return None
    
    @staticmethod
    def create_video_capture(video_path):
        """创建视频读取器 - Windows安全模式"""
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"文件不存在: {video_path}")
            
            # 使用CAP_FFMPEG后端（如果可用）更稳定
            cap = cv2.VideoCapture(video_path, cv2.CAP_FFMPEG)
            
            # 如果FFMPEG失败，回退到自动模式
            if not cap.isOpened():
                cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                # 尝试禁用硬件加速
                os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'
                cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError("无法打开视频文件，尝试重新编码为H.264格式")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if total_frames == 0 or fps == 0 or width == 0 or height == 0:
                cap.release()
                raise ValueError("视频文件格式不正确或已损坏")
            
            print(f"✓ 视频加载成功: {total_frames}帧, {fps:.2f}fps, {width}x{height}")
            return cap, fps, total_frames
            
        except Exception as e:
            print(f"✗ 视频加载失败: {e}")
            return None, 0, 0


# ==================== 姿态分析 ====================
mp_pose = mp.solutions.pose

def calculate_attention_score(landmarks, config):
    """计算专注度分数 - 优化版"""
    if not landmarks:
        return 0
    
    score = 100
    try:
        # 获取关键点的可见性
        nose = landmarks[mp_pose.PoseLandmark.NOSE]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        left_hand = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
        right_hand = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        
        # 规则1：低头检测
        if (nose.visibility > 0.5 and left_shoulder.visibility > 0.5 and 
            right_shoulder.visibility > 0.5):
            shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2
            if nose.y - shoulder_center_y > config.HEAD_DOWN_THRESHOLD:
                score -= 60
        
        # 规则2：肩膀倾斜
        if left_shoulder.visibility > 0.5 and right_shoulder.visibility > 0.5:
            shoulder_vector = np.array([right_shoulder.x - left_shoulder.x,
                                       right_shoulder.y - left_shoulder.y])
            angle = np.degrees(np.arctan2(abs(shoulder_vector[1]), 
                                         abs(shoulder_vector[0])))
            if angle > config.SHOULDER_TILT_THRESHOLD:
                score -= 30
        
        # 规则3：手部位置
        hand_below_hip = False
        if (left_hand.visibility > 0.5 and left_hip.visibility > 0.5 and 
            left_hand.y > left_hip.y + config.HAND_BELOW_HIP_THRESHOLD):
            hand_below_hip = True
        
        if (right_hand.visibility > 0.5 and right_hip.visibility > 0.5 and 
            right_hand.y > right_hip.y + config.HAND_BELOW_HIP_THRESHOLD):
            hand_below_hip = True
        
        if hand_below_hip:
            score -= 20
        
    except Exception as e:
        return max(0, score)
    
    return max(0, min(100, score))


# ==================== 主处理类 ====================
class ClassroomAttentionMonitor:
    """课堂专注度检测主类"""
    
    def __init__(self, video_path, config=Config()):
        self.video_path = video_path
        self.config = config
        self.attention_records = []
        
    def process(self, output_path="output_annotated.mp4"):
        """处理视频主流程"""
        print("\n" + "="*60)
        print("课堂专注度检测系统启动".center(60))
        print("="*60 + "\n")
        
        # 步骤1: 初始化所有资源
        print("步骤1: 初始化模型资源...")
        yolo = ResourceManager.create_yolo()
        tracker = ResourceManager.create_tracker()
        cap, fps, total_frames = ResourceManager.create_video_capture(self.video_path)
        
        if None in [yolo, tracker, cap]:
            print("\n✗ 关键资源初始化失败，程序退出")
            return None, None
        
        print("\n步骤2: 开始视频处理...")
        print(f"提示: 按 Ctrl+C 可安全中断\n")
        
        # 步骤2: 逐帧处理
        frame_idx = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break
                
                # 跳帧处理
                if frame_idx % (self.config.SKIP_FRAMES + 1) != 0:
                    frame_idx += 1
                    continue
                
                # YOLO检测
                results = yolo(frame, classes=[self.config.PERSON_CLASS_ID], 
                              conf=self.config.CONFIDENCE_THRESHOLD, verbose=False)
                
                # 准备检测框
                detections = []
                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    detections.append(([x1, y1, x2-x1, y2-y1], conf, 'student'))
                
                # DeepSORT跟踪
                tracks = tracker.update_tracks(detections, frame=frame)
                
                # 姿态分析
                for track in tracks:
                    if not track.is_confirmed():
                        continue
                    
                    track_id = track.track_id
                    bbox = track.to_ltrb()
                    x1, y1, x2, y2 = map(int, bbox)
                    
                    # 裁剪学生区域
                    student_crop = frame[y1:y2, x1:x2]
                    if student_crop.size == 0:
                        continue
                    
                    # MediaPipe姿态估计
                    with mp.solutions.pose.Pose(
                        static_image_mode=True,
                        model_complexity=0,
                        min_detection_confidence=self.config.MIN_DETECTION_CONFIDENCE
                    ) as pose_estimator:
                        
                        rgb_crop = cv2.cvtColor(student_crop, cv2.COLOR_BGR2RGB)
                        results = pose_estimator.process(rgb_crop)
                        
                        if results and results.pose_landmarks:
                            landmarks = results.pose_landmarks.landmark
                            
                            # 计算专注度
                            attention_score = calculate_attention_score(landmarks, self.config)
                            
                            # 记录不专注事件
                            if attention_score < self.config.ATTENTION_SCORE_THRESHOLD:
                                self.attention_records.append({
                                    'student_id': int(track_id),
                                    'time_sec': round(frame_idx / fps, 2),
                                    'time_str': str(timedelta(seconds=int(frame_idx / fps))),
                                    'frame': frame_idx,
                                    'score': attention_score,
                                    'bbox': (x1, y1, x2, y2)
                                })
                            
                            # 可视化
                            if self.config.OUTPUT_VIDEO:
                                color = (0, 0, 255) if attention_score < self.config.ATTENTION_SCORE_THRESHOLD else (0, 255, 0)
                                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                                status = "NOT FOCUS" if attention_score < self.config.ATTENTION_SCORE_THRESHOLD else "FOCUS"
                                cv2.putText(frame, f"ID:{track_id} {status}", 
                                           (x1, max(20, y1-10)), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # 显示进度
                if frame_idx % 100 == 0:
                    print(f"  已处理 {frame_idx}/{total_frames} 帧...", end='\r')
                
                frame_idx += 1
        
        except KeyboardInterrupt:
            print("\n\n用户中断处理，正在保存已有结果...")
        
        except Exception as e:
            print(f"\n处理出错: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 确保资源释放
            print("\n步骤3: 释放资源...")
            if 'cap' in locals():
                cap.release()
            print("✓ 资源已释放\n")
        
        # 生成报告
        return self.generate_report()
    
    def generate_report(self):
        """生成报告"""
        if not self.attention_records:
            return None, {}
        
        df = pd.DataFrame(self.attention_records)
        
        # 合并连续时间段
        summary = {}
        for student_id in sorted(df['student_id'].unique()):
            student_data = df[df['student_id'] == student_id].sort_values('time_sec')
            
            time_ranges = []
            if not student_data.empty:
                start_time = student_data.iloc[0]['time_sec']
                end_time = student_data.iloc[0]['time_sec']
                
                for _, row in student_data.iterrows():
                    if row['time_sec'] - end_time > 3:
                        if end_time - start_time >= 1:
                            time_ranges.append((start_time, end_time))
                        start_time = row['time_sec']
                    end_time = row['time_sec']
                
                if end_time - start_time >= 1:
                    time_ranges.append((start_time, end_time))
            
            # 格式化
            formatted_ranges = []
            total_duration = 0
            for start, end in time_ranges:
                duration = end - start
                formatted_ranges.append({
                    'start': str(timedelta(seconds=int(start))),
                    'end': str(timedelta(seconds=int(end))),
                    'duration_sec': round(duration, 1)
                })
                total_duration += duration
            
            if formatted_ranges:
                summary[student_id] = {
                    'time_ranges': formatted_ranges,
                    'total_duration_sec': round(total_duration, 1),
                    'event_count': len(formatted_ranges)
                }
        
        return df, summary
    
    def print_report(self, summary):
        """打印报告"""
        if not summary:
            print("\n=== 检测报告 ===")
            print("未检测到不专注行为！")
            return
        
        print("\n" + "="*70)
        print("课堂专注度检测报告".center(70))
        print("="*70)
        
        for student_id in sorted(summary.keys()):
            data = summary[student_id]
            print(f"\n【学生ID: {student_id:02d}】")
            print(f"不专注事件次数: {data['event_count']}")
            print(f"总不专注时长: {data['total_duration_sec']}秒")
            print("不专注时间段:")
            
            for i, time_range in enumerate(data['time_ranges'], 1):
                print(f"  {i}. {time_range['start']} ~ {time_range['end']} "
                      f"(持续 {time_range['duration_sec']}秒)")
        
        print("\n" + "="*70)
        print(f"总计不专注学生数: {len(summary)}人")
        print("="*70 + "\n")


def main():
    # 恢复stderr用于正常输出
    sys.stderr = sys.__stderr__
    
    parser = argparse.ArgumentParser(
        description='课堂专注度检测系统 (Windows生产版)'
    )
    parser.add_argument('video_path', help='输入视频文件路径')
    parser.add_argument('--threshold', type=int, default=50,
                       help='专注度阈值(0-100), 默认50')
    parser.add_argument('--skip-frames', type=int, default=5,
                       help='跳帧数(建议5), 每N+1帧处理1帧')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.video_path):
        print(f"错误: 文件不存在: {args.video_path}")
        sys.exit(1)
    
    config = Config()
    config.ATTENTION_SCORE_THRESHOLD = args.threshold
    config.SKIP_FRAMES = args.skip_frames
    
    print("\n" + "="*60)
    print("课堂专注度检测系统".center(60))
    print("="*60 + "\n")
    
    try:
        monitor = ClassroomAttentionMonitor(args.video_path, config)
        df, summary = monitor.process()
        
        # 重新过滤警告
        sys.stderr = open(os.devnull, 'w')
        monitor.print_report(summary)
        
        if df is not None:
            csv_path = "attention_report.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"✓ 报告已保存至: {os.path.abspath(csv_path)}")
        
        print("="*60)
        print("✓ 处理完成！")
        print("="*60 + "\n")
    
    except Exception as e:
        sys.stderr = sys.__stderr__
        print(f"\n程序出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()