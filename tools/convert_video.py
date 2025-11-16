#!/usr/bin/env python3
"""
视频格式转换工具
将无法播放的视频转换为兼容性更好的H.264格式
"""

import cv2
import sys
import os
from pathlib import Path

def convert_video(input_path, output_path=None, codec='avc1'):
    """
    转换视频为兼容格式
    
    参数:
        input_path: 输入视频路径
        output_path: 输出视频路径（可选，默认添加_converted后缀）
        codec: 编码器（'avc1'=H.264, 'mp4v'=MPEG-4, 'XVID'=Xvid）
    """
    print(f"\n{'='*60}")
    print("视频格式转换工具".center(60))
    print(f"{'='*60}\n")
    
    # 检查输入文件
    if not os.path.exists(input_path):
        print(f"✗ 错误: 文件不存在: {input_path}")
        return False
    
    # 生成输出路径
    if output_path is None:
        input_file = Path(input_path)
        output_path = str(input_file.parent / f"{input_file.stem}_converted.mp4")
    
    print(f"输入文件: {input_path}")
    print(f"输出文件: {output_path}")
    print(f"编码器: {codec}\n")
    
    # 打开输入视频
    print("步骤1: 读取原始视频...")
    cap = cv2.VideoCapture(input_path)
    
    if not cap.isOpened():
        print("✗ 无法打开输入视频")
        return False
    
    # 获取视频属性
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"✓ 视频信息: {width}x{height}, {fps:.2f}fps, {total_frames}帧\n")
    
    # 创建输出视频
    print("步骤2: 创建输出视频...")
    fourcc = cv2.VideoWriter_fourcc(*codec)
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    if not out.isOpened():
        print(f"✗ 无法创建输出视频（编码器: {codec}）")
        cap.release()
        return False
    
    print(f"✓ 输出视频创建成功\n")
    
    # 逐帧转换
    print("步骤3: 转换视频帧...")
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            out.write(frame)
            frame_count += 1
            
            # 显示进度
            if frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"  进度: {progress:.1f}% [{frame_count}/{total_frames}]", end='\r')
        
        print(f"\n✓ 转换完成: {frame_count}帧\n")
        
    except Exception as e:
        print(f"\n✗ 转换出错: {e}")
        return False
    
    finally:
        cap.release()
        out.release()
    
    # 验证输出文件
    print("步骤4: 验证输出文件...")
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✓ 文件大小: {file_size:.2f} MB")
        
        # 尝试打开验证
        test_cap = cv2.VideoCapture(output_path)
        if test_cap.isOpened():
            test_fps = test_cap.get(cv2.CAP_PROP_FPS)
            test_frames = int(test_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            test_cap.release()
            print(f"✓ 验证成功: {test_frames}帧, {test_fps:.2f}fps")
            print(f"\n{'='*60}")
            print("✓ 转换成功！".center(60))
            print(f"{'='*60}\n")
            print(f"输出文件: {os.path.abspath(output_path)}")
            print("可以使用VLC、QuickTime等播放器打开\n")
            return True
        else:
            test_cap.release()
            print("⚠ 警告: 输出文件可能有问题")
            return False
    else:
        print("✗ 输出文件不存在")
        return False


def main():
    if len(sys.argv) < 2:
        print("用法: python convert_video.py <输入视频> [输出视频] [编码器]")
        print("\n编码器选项:")
        print("  avc1  - H.264 (推荐，兼容性最好)")
        print("  mp4v  - MPEG-4")
        print("  XVID  - Xvid")
        print("\n示例:")
        print("  python convert_video.py output_annotated.mp4")
        print("  python convert_video.py input.mp4 output.mp4 avc1")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    codec = sys.argv[3] if len(sys.argv) > 3 else 'avc1'
    
    success = convert_video(input_path, output_path, codec)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

