# check_gpu.py
import torch
import cv2
import ultralytics

print("=== GPU诊断报告 ===")
print(f"PyTorch版本: {torch.__version__}")
print(f"CUDA可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA版本: {torch.version.cuda}")
    print(f"GPU设备: {torch.cuda.get_device_name(0)}")
    print(f"GPU显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
else:
    print("未检测到GPU，将使用CPU")

print(f"\nOpenCV版本: {cv2.__version__}")
print(f"OpenCV构建信息包含CUDA: {'CUDA' in cv2.getBuildInformation()}")

print(f"\nUltralytics版本: {ultralytics.__version__}")
print("\n=== 建议 ===")
if torch.cuda.is_available():
    print("✓ 可以启用GPU加速")
else:
    print("✗ 未检测到CUDA，请安装PyTorch GPU版本")