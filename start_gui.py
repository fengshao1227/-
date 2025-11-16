#!/usr/bin/env python
"""
启动GUI的Python脚本 - 自动设置环境
"""
import os
import sys

# 设置Qt插件路径
if sys.platform == 'darwin':  # macOS
    # conda安装的Qt插件路径
    conda_prefix = os.environ.get('CONDA_PREFIX', '/opt/anaconda3')
    qt6_plugins = os.path.join(conda_prefix, 'lib', 'qt6', 'plugins')

    if os.path.exists(qt6_plugins):
        os.environ['QT_PLUGIN_PATH'] = qt6_plugins
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(qt6_plugins, 'platforms')
        print(f"✓ Qt插件路径: {qt6_plugins}")
    else:
        # 尝试PyQt6包内的插件
        try:
            import PyQt6
            pyqt6_path = os.path.dirname(PyQt6.__file__)
            qt6_plugins = os.path.join(pyqt6_path, 'Qt6', 'plugins')

            if os.path.exists(qt6_plugins):
                os.environ['QT_PLUGIN_PATH'] = qt6_plugins
                os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(qt6_plugins, 'platforms')
                print(f"✓ Qt插件路径: {qt6_plugins}")
        except ImportError:
            print("⚠️  警告: 未找到PyQt6")

# 导入并运行GUI
if __name__ == '__main__':
    from gui_main import main
    main()

