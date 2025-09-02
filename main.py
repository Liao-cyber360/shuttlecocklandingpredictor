#!/usr/bin/env python3
"""
羽毛球落点预测系统 - 新版主入口
Shuttlecock Landing Predictor - New Main Entry Point
系统级重构版本 - 不再支持命令行参数，直接启动GUI界面
"""

import sys
import os

def main():
    """主函数 - 重定向到新的GUI界面"""
    print("=" * 80)
    print("羽毛球落点预测系统 v6.0 - 系统级重构版本")
    print("Shuttlecock Landing Predictor v6.0 - System-Level Refactor")
    print("=" * 80)
    print()
    print("注意: 系统已进行重构，不再支持命令行参数模式")
    print("Note: System has been refactored, command line arguments are no longer supported")
    print()
    print("正在启动新的图形界面...")
    print("Starting new GUI interface...")
    print()
    
    try:
        # 导入并启动新的主界面
        from new_main import main as new_main_func
        return new_main_func()
    except ImportError as e:
        print(f"新界面启动失败: {e}")
        print("请使用 launcher.py 启动系统")
        print()
        print("或者使用原始命令行版本:")
        print("python main_original.py --video-mode --video1 path1.mp4 --video2 path2.mp4")
        return 1
    except Exception as e:
        print(f"系统启动错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())