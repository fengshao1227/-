@echo off
echo ======================================
echo   课堂专注度检测系统 - Windows打包脚本
echo ======================================
echo.

echo [1/4] 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo.
echo [2/4] 安装依赖...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [3/4] 开始打包exe...
pyinstaller --name="课堂专注度检测系统" ^
            --windowed ^
            --onefile ^
            --add-data "yolov8m-pose.pt;." ^
            --hidden-import=cv2 ^
            --hidden-import=torch ^
            --hidden-import=ultralytics ^
            --hidden-import=PyQt6 ^
            --hidden-import=PyQt6.QtCore ^
            --hidden-import=PyQt6.QtGui ^
            --hidden-import=PyQt6.QtWidgets ^
            --collect-all PyQt6 ^
            --collect-all ultralytics ^
            gui_main.py

echo.
echo [4/4] 打包完成！
echo.
echo 生成的exe文件位置: dist\课堂专注度检测系统.exe
echo.
pause

