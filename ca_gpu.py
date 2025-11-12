#!/usr/bin/env python3
"""
课堂专注度检测系统 v2.0 (增强版)
新增：长时间低头、闭眼、发呆行为检测
"""

import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO
from datetime import timedelta
import argparse
import os
import sys
import warnings
import torch
from collections import defaultdict, deque

# ==================== 警告过滤 ====================
warnings.filterwarnings('ignore')
import logging
logging.getLogger().setLevel(logging.ERROR)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# ==================== 配置参数 ====================
class Config:
    """系统配置"""
    POSE_MODEL = "yolov8m-pose.pt"
    DEVICE = 0
    
    # **行为判断阈值**
    HEAD_DOWN_THRESHOLD = 0.03          # 低头检测阈值
    HEAD_DOWN_DURATION = 3.0            # **长时间低头：持续3秒以上**
    
    EYE_CLOSED_THRESHOLD = 0.18         # **闭眼：眼睛纵横比EAR < 0.18**
    EYE_CLOSED_DURATION = 2.0           # **长时间闭眼：持续2秒以上**
    
    STILLNESS_THRESHOLD = 5.0           # **发呆：头部移动小于5像素**
    STILLNESS_DURATION = 4.0            # **持续4秒以上**
    GAZE_FIXED_THRESHOLD = 0.02         # 视线变化阈值
    
    SHOULDER_TILT_THRESHOLD = 25
    HAND_BELOW_HIP_THRESHOLD = 0.02
    ATTENTION_SCORE_THRESHOLD = 50
    
    # 视频输出
    OUTPUT_VIDEO = True
    OUTPUT_VIDEO_PATH = "output_annotated.mp4"
    SHOW_LABELS = True
    
    # 性能
    SKIP_FRAMES = 2
    CONFIDENCE_THRESHOLD = 0.5

# ==================== 状态追踪器 ====================
class StudentStateTracker:
    """跟踪每个学生的行为状态"""
    
    def __init__(self):
        # 状态队列，保存最近30帧的数据
        self.head_position = defaultdict(lambda: deque(maxlen=30))  # 头部位置历史
        self.eye_openness = defaultdict(lambda: deque(maxlen=30))   # 眼睛开合历史
        self.gaze_position = defaultdict(lambda: deque(maxlen=30))  # 视线位置历史
        
        # 行为计时器
        self.head_down_timer = defaultdict(float)   # 低头计时
        self.eye_closed_timer = defaultdict(float)  # 闭眼计时
        self.stillness_timer = defaultdict(float)   # 静止计时
        
        # 上一帧时间戳
        self.last_update = defaultdict(float)
    
    def update(self, student_id, keypoints, fps):
        """更新学生状态"""
        current_time = len(self.head_position[student_id]) / fps
        
        # 提取头部关键点（鼻子）
        if keypoints is not None and len(keypoints) > 0:
            nose = keypoints[0]
            left_eye = keypoints[1]
            right_eye = keypoints[2]
            
            # 记录头部位置
            if nose[2] > 0.5:  # 可见
                self.head_position[student_id].append(nose[:2])
            
            # 计算眼睛纵横比EAR
            ear = self.calculate_eye_aspect_ratio(left_eye, right_eye, keypoints)
            self.eye_openness[student_id].append(ear)
            
            # 记录视线位置（眼睛中心）
            if left_eye[2] > 0.5 and right_eye[2] > 0.5:
                gaze_x = (left_eye[0] + right_eye[0]) / 2
                gaze_y = (left_eye[1] + right_eye[1]) / 2
                self.gaze_position[student_id].append((gaze_x, gaze_y))
        
        return current_time
    
    def calculate_eye_aspect_ratio(self, left_eye, right_eye, keypoints):
        """计算眼睛纵横比（Eye Aspect Ratio）"""
        try:
            # 使用眼睛周围的关键点计算EAR
            # YOLOv8-pose眼睛关键点索引: 1=左眼, 2=右眼
            if left_eye[2] > 0.5 and right_eye[2] > 0.5:
                # 简化的EAR计算：眼睛垂直/水平距离比
                # 需要更多眼周点，这里用置信度作为替代
                return (left_eye[2] + right_eye[2]) / 2
            return 1.0  # 默认眼睛睁开
        except:
            return 1.0
    
    def check_long_term_behaviors(self, student_id, keypoints, fps, config):
        """检测长期行为"""
        behaviors = []
        
        # 1. 检查长时间低头
        if keypoints is not None and len(keypoints) > 0:
            nose = keypoints[0]
            left_shoulder = keypoints[5]
            right_shoulder = keypoints[6]
            
            if (nose[2] > 0.5 and left_shoulder[2] > 0.5 and right_shoulder[2] > 0.5):
                shoulder_center_y = (left_shoulder[1] + right_shoulder[1]) / 2
                if nose[1] - shoulder_center_y > config.HEAD_DOWN_THRESHOLD:
                    self.head_down_timer[student_id] += 1 / fps
                    if self.head_down_timer[student_id] >= config.HEAD_DOWN_DURATION:
                        behaviors.append(f"长时间低头({self.head_down_timer[student_id]:.1f}s)")
                else:
                    self.head_down_timer[student_id] = 0
            else:
                self.head_down_timer[student_id] = 0
        
        # 2. 检查长时间闭眼
        if len(self.eye_openness[student_id]) > 0:
            ear = self.eye_openness[student_id][-1]
            if ear < config.EYE_CLOSED_THRESHOLD:  # 眼睛闭合
                self.eye_closed_timer[student_id] += 1 / fps
                if self.eye_closed_timer[student_id] >= config.EYE_CLOSED_DURATION:
                    behaviors.append(f"闭眼({self.eye_closed_timer[student_id]:.1f}s)")
            else:
                self.eye_closed_timer[student_id] = 0
        else:
            self.eye_closed_timer[student_id] = 0
        
        # 3. 检查发呆（头部静止+视线固定）
        if len(self.head_position[student_id]) >= 5:
            # 计算最近5帧头部移动距离
            recent_positions = list(self.head_position[student_id])[-5:]
            head_movement = 0
            for i in range(1, len(recent_positions)):
                dx = recent_positions[i][0] - recent_positions[i-1][0]
                dy = recent_positions[i][1] - recent_positions[i-1][1]
                head_movement += np.sqrt(dx*dx + dy*dy)
            
            if head_movement < config.STILLNESS_THRESHOLD:
                self.stillness_timer[student_id] += 1 / fps
                if self.stillness_timer[student_id] >= config.STILLNESS_DURATION:
                    behaviors.append(f"发呆({self.stillness_timer[student_id]:.1f}s)")
            else:
                self.stillness_timer[student_id] = 0
        else:
            self.stillness_timer[student_id] = 0
        
        return behaviors


# ==================== 姿态分析 ====================
def calculate_attention_score(keypoints, bbox_height, config, state_tracker, student_id, fps):
    """
    计算专注度分数
    返回: (分数, 不专注原因列表)
    """
    if keypoints is None or len(keypoints) < 17:
        return 0, []
    
    score = 100
    reasons = []
    
    try:
        # 更新状态追踪器
        current_time = state_tracker.update(student_id, keypoints, fps)
        
        # 检查长期行为（低头、闭眼、发呆）
        long_term_behaviors = state_tracker.check_long_term_behaviors(
            student_id, keypoints, fps, config
        )
        
        # 长期行为扣分更严重
        for behavior in long_term_behaviors:
            if "长时间低头" in behavior:
                score -= 80  # 严重扣分
            elif "闭眼" in behavior:
                score -= 70
            elif "发呆" in behavior:
                score -= 50
            reasons.append(behavior)
        
        # 短期行为检测（原有规则）
        nose = keypoints[0]
        left_shoulder = keypoints[5]
        right_shoulder = keypoints[6]
        left_hand = keypoints[9]
        right_hand = keypoints[10]
        left_hip = keypoints[13]
        right_hip = keypoints[14]
        
        # 短期低头（不持续）
        if (not any("长时间低头" in r for r in reasons) and 
            nose[2] > 0.5 and left_shoulder[2] > 0.5 and right_shoulder[2] > 0.5):
            shoulder_center_y = (left_shoulder[1] + right_shoulder[1]) / 2
            head_drop = (nose[1] - shoulder_center_y) * bbox_height
            
            if head_drop > config.HEAD_DOWN_THRESHOLD * bbox_height:
                score -= 30  # 短期低头扣分较轻
                reasons.append("短暂低头")
        
        # 肩膀倾斜
        if left_shoulder[2] > 0.5 and right_shoulder[2] > 0.5:
            shoulder_vec = np.array([right_shoulder[0] - left_shoulder[0], 
                                   right_shoulder[1] - left_shoulder[1]])
            angle = np.degrees(np.arctan2(abs(shoulder_vec[1]), abs(shoulder_vec[0])))
            
            if angle > config.SHOULDER_TILT_THRESHOLD:
                score -= 20
                reasons.append(f"侧身({int(angle)}°)")
        
        # 手部位置
        hand_low = False
        if left_hand[2] > 0.5 and left_hip[2] > 0.5:
            if left_hand[1] > left_hip[1] + config.HAND_BELOW_HIP_THRESHOLD:
                hand_low = True
        
        if right_hand[2] > 0.5 and right_hip[2] > 0.5:
            if right_hand[1] > right_hip[1] + config.HAND_BELOW_HIP_THRESHOLD:
                hand_low = True
        
        if hand_low:
            score -= 15
            reasons.append("手部异常")
    
    except Exception as e:
        print(f"姿态计算异常: {e}")
        return max(0, score), ["计算错误"]
    
    return max(0, min(100, score)), reasons


# ==================== 核心检测类 ====================
class ClassroomMonitor:
    def __init__(self, video_path, config=Config()):
        self.video_path = video_path
        self.config = config
        self.attention_records = []
        self.state_tracker = StudentStateTracker()  # **新增状态追踪器**
        
        if config.DEVICE == 0:
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"✓ GPU加速启用: {gpu_name} ({gpu_memory:.1f} GB)")
        else:
            print("⚠ 使用CPU模式")
    
    def process(self, max_frames=0):
        """处理视频"""
        print("\n" + "="*60)
        print("课堂专注度检测系统 v2.0 (增强版)".center(60))
        print("新增: 长时间低头、闭眼、发呆检测".center(60))
        print("="*60 + "\n")
        
        # 加载模型
        print("步骤1: 加载YOLOv8-pose模型...")
        yolo = YOLO(self.config.POSE_MODEL)
        if self.config.DEVICE == 0:
            yolo.to("cuda")
        
        print(f"✓ 模型加载成功\n")
        
        # 打开视频
        print("步骤2: 加载视频文件...")
        video_path = os.path.abspath(self.video_path)
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise FileNotFoundError(f"无法打开视频: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        if max_frames > 0:
            total_frames = min(total_frames, max_frames)
            print(f"✓ 视频: {total_frames}帧(测试模式), {fps:.2f}fps, {width}x{height}\n")
        else:
            print(f"✓ 视频: {total_frames}帧, {fps:.2f}fps, {width}x{height}\n")
        
        # 初始化视频写入器
        video_writer = None
        if self.config.OUTPUT_VIDEO:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(
                self.config.OUTPUT_VIDEO_PATH, 
                fourcc, 
                fps / (self.config.SKIP_FRAMES + 1), 
                (width, height)
            )
            if not video_writer.isOpened():
                raise ValueError(f"无法创建视频文件: {self.config.OUTPUT_VIDEO_PATH}")
            print(f"✓ 视频输出: {os.path.abspath(self.config.OUTPUT_VIDEO_PATH)}\n")
        
        print("步骤3: 开始GPU加速检测...")
        print("行为: 低头(短暂/长期) | 闭眼 | 发呆 | 侧身 | 手部异常\n")
        
        frame_idx = 0
        processed_count = 0
        
        try:
            while True:
                if max_frames > 0 and frame_idx >= max_frames:
                    break
                
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 跳帧
                if frame_idx % (self.config.SKIP_FRAMES + 1) != 0:
                    frame_idx += 1
                    continue
                
                # YOLO推理
                results = yolo.track(
                    frame,
                    classes=[0],
                    conf=self.config.CONFIDENCE_THRESHOLD,
                    persist=True,
                    tracker="bytetrack.yaml",
                    device=0,
                    verbose=False
                )
                
                # 处理结果
                if results[0].boxes and len(results[0].boxes) > 0:
                    boxes = results[0].boxes
                    keypoints = results[0].keypoints
                    orig_frame = results[0].orig_img
                    
                    for i, box in enumerate(boxes):
                        track_id = int(box.id[0]) if box.id is not None else 0
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        bbox_height = y2 - y1
                        
                        # 计算专注度（包含新行为检测）
                        if keypoints and i < len(keypoints.data):
                            kpts = keypoints.data[i].cpu().numpy()
                            attention_score, reasons = calculate_attention_score(
                                kpts, 
                                bbox_height, 
                                self.config,
                                self.state_tracker,  # 传入状态追踪器
                                track_id,
                                fps
                            )
                            
                            # 绘制增强标注
                            is_not_focused = attention_score < self.config.ATTENTION_SCORE_THRESHOLD
                            
                            color = (0, 0, 255) if is_not_focused else (0, 255, 0)
                            
                            # 加粗边框（长时间行为用更粗的框）
                            if any("长时间" in r for r in reasons):
                                border_thickness = 4
                            else:
                                border_thickness = 2
                            
                            cv2.rectangle(orig_frame, (x1, y1), (x2, y2), color, border_thickness)
                            
                            # 绘制文字标签
                            if self.config.SHOW_LABELS:
                                status = "NOT FOCUS" if is_not_focused else "FOCUS"
                                
                                # 原因标签（最多显示2个，避免过长）
                                main_reasons = reasons[:2]
                                reason_text = f"({'; '.join(main_reasons)})" if main_reasons else ""
                                
                                label = f"ID:{track_id} {status}({attention_score}) {reason_text}"
                                label_y = max(20, y1 - 10)
                                
                                # 文字背景
                                (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                                cv2.rectangle(orig_frame, (x1, label_y - text_h - 5), 
                                            (x1 + text_w, label_y + 5), (0, 0, 0), -1)
                                
                                cv2.putText(orig_frame, label, (x1, label_y), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                            
                            # 记录不专注事件
                            if is_not_focused:
                                self.attention_records.append({
                                    'student_id': track_id,
                                    'time_sec': round(frame_idx / fps, 2),
                                    'time_str': str(timedelta(seconds=int(frame_idx / fps))),
                                    'frame': frame_idx,
                                    'score': attention_score,
                                    'reason': ';'.join(reasons),
                                    'bbox': (x1, y1, x2, y2)
                                })
                    
                    # 写入视频
                    if video_writer:
                        video_writer.write(orig_frame)
                else:
                    if video_writer:
                        video_writer.write(frame)
                
                # 进度显示（包含每帧检测到的人数）
                if processed_count % 50 == 0:
                    progress = (frame_idx / total_frames) * 100
                    detected_people = len(results[0].boxes) if results[0].boxes else 0
                    not_focus_count = sum(1 for r in self.attention_records if r['frame'] == frame_idx)
                    print(f"  → 进度: {progress:.1f}% [{frame_idx}/{total_frames}] | "
                          f"检测到: {detected_people}人 | 不专注: {not_focus_count}人")
                
                processed_count += 1
                frame_idx += 1
                
        except KeyboardInterrupt:
            print("\n\n用户中断，正在保存...")
        
        except Exception as e:
            print(f"\n处理出错: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 资源释放
            try:
                cap.release()
                if video_writer:
                    video_writer.release()
                    print(f"\n✓ 标注视频已保存: {os.path.abspath(self.config.OUTPUT_VIDEO_PATH)}")
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception as e:
                print(f"清理资源时出错: {e}")
        
        return self.generate_report()
    
    def generate_report(self):
        """生成CSV报告"""
        if not self.attention_records:
            return None, {}
        
        df = pd.DataFrame(self.attention_records)
        
        # 按学生汇总
        summary = {}
        for student_id in sorted(df['student_id'].unique()):
            student_data = df[df['student_id'] == student_id].sort_values('time_sec')
            
            # 合并连续时间段
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
            
            formatted_ranges = []
            total_duration = 0
            for start, end in time_ranges:
                duration = end - start
                
                # 提取该时间段的主要不专注原因
                time_range_data = student_data[
                    (student_data['time_sec'] >= start) & 
                    (student_data['time_sec'] <= end)
                ]
                
                if not time_range_data.empty:
                    # 统计该时间段内各种不专注行为的出现频率
                    all_reasons = []
                    for reason_str in time_range_data['reason']:
                        all_reasons.extend(reason_str.split(';'))
                    
                    # 找出最常见的不专注行为
                    from collections import Counter
                    reason_counts = Counter(all_reasons)
                    main_reason = reason_counts.most_common(1)[0][0] if reason_counts else "未知"
                else:
                    main_reason = "未知"
                
                formatted_ranges.append({
                    'start': str(timedelta(seconds=int(start))),
                    'end': str(timedelta(seconds=int(end))),
                    'duration_sec': round(duration, 1),
                    'reason': main_reason
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
        """打印控制台报告"""
        if not summary:
            print("\n=== 检测报告 ===")
            print("未检测到不专注行为！")
            return
        
        print("\n" + "="*70)
        print("课堂专注度检测报告 v2.0".center(70))
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
                print(f"     主因: {time_range['reason']}")
        
        print("\n" + "="*70)
        print(f"总计不专注学生数: {len(summary)}人")
        print("="*70 + "\n")


# ==================== 主函数 ====================
def main():
    parser = argparse.ArgumentParser(
        description='课堂专注度检测 v2.0 (增强版)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
新增行为检测:
  - 长时间低头: 持续3秒以上
  - 闭眼: 持续2秒以上
  - 发呆: 头部静止4秒以上

示例:
  # 基础用法（保存视频和CSV报告）
  python ca_v2.py test.mp4 --save-video
  
  # 调整阈值，保存视频
  python ca_v2.py test.mp4 --threshold 40 --save-video
  
  # 处理前500帧测试
  python ca_v2.py test.mp4 --save-video --max-frames 500
        '''
    )
    
    parser.add_argument('video_path', help='输入视频文件路径')
    parser.add_argument('--threshold', type=int, default=85,
                       help='专注度阈值(0-100), 默认40')
    parser.add_argument('--skip-frames', type=int, default=2,
                       help='跳帧数(默认2)')
    parser.add_argument('--save-video', action='store_true',
                       help='保存标注后的视频文件')
    parser.add_argument('--no-labels', action='store_true',
                       help='不在视频上显示文字标签')
    parser.add_argument('-o', '--output', default='output_annotated.mp4',
                       help='输出视频路径(默认: output_annotated.mp4)')
    parser.add_argument('--max-frames', type=int, default=0,
                       help='最大处理帧数(0=全部), 用于测试')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.video_path):
        print(f"✗ 错误: 文件不存在: {args.video_path}")
        sys.exit(1)
    
    config = Config()
    config.ATTENTION_SCORE_THRESHOLD = args.threshold
    config.SKIP_FRAMES = args.skip_frames
    config.OUTPUT_VIDEO = args.save_video
    config.OUTPUT_VIDEO_PATH = args.output
    config.SHOW_LABELS = not args.no_labels
    
    print("\n" + "-"*60)
    print(f"PyTorch版本: {torch.__version__}")
    print(f"CUDA可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    print("-"*60 + "\n")
    
    try:
        monitor = ClassroomMonitor(args.video_path, config)
        df, summary = monitor.process(args.max_frames)
        
        monitor.print_report(summary)
        
        if df is not None:
            csv_path = "attention_report.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"✓ CSV报告已保存: {os.path.abspath(csv_path)}")
        
        if config.OUTPUT_VIDEO and os.path.exists(config.OUTPUT_VIDEO_PATH):
            print(f"✓ 标注视频已保存: {os.path.abspath(config.OUTPUT_VIDEO_PATH)}")
        
        print("\n" + "="*60)
        print("✓ 所有任务完成！")
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()