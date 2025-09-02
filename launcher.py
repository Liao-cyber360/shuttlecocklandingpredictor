#!/usr/bin/env python3
"""
羽毛球落点预测系统启动器 / Shuttlecock Landing Predictor Launcher
"""

import sys
import os
import subprocess
import importlib.util

def check_dependency(package_name, pip_name=None):
    """检查依赖包是否安装"""
    if pip_name is None:
        pip_name = package_name
        
    try:
        spec = importlib.util.find_spec(package_name)
        return spec is not None
    except ImportError:
        return False

def install_package(package_name):
    """安装包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """主启动函数"""
    print("=" * 60)
    print("羽毛球落点预测系统 v6.0 启动器")
    print("Shuttlecock Landing Predictor v6.0 Launcher")
    print("=" * 60)
    
    # 检查基本依赖
    print("\n1. 检查基本依赖...")
    
    dependencies = [
        ("PyQt6", "PyQt6"),
        ("numpy", "numpy"),
        ("cv2", "opencv-python")
    ]
    
    missing_deps = []
    for package, pip_name in dependencies:
        if check_dependency(package):
            print(f"   ✓ {package} 已安装")
        else:
            print(f"   ✗ {package} 未安装")
            missing_deps.append((package, pip_name))
    
    # 检查可选依赖
    print("\n2. 检查可选依赖（完整功能需要）...")
    
    optional_deps = [
        ("ultralytics", "ultralytics"),
        ("open3d", "open3d")
    ]
    
    missing_optional = []
    for package, pip_name in optional_deps:
        if check_dependency(package):
            print(f"   ✓ {package} 已安装")
        else:
            print(f"   ✗ {package} 未安装")
            missing_optional.append((package, pip_name))
    
    # 处理依赖安装
    if missing_deps:
        print(f"\n⚠️  缺少基本依赖: {', '.join([dep[0] for dep in missing_deps])}")
        response = input("是否自动安装基本依赖? (y/n): ").strip().lower()
        
        if response == 'y':
            print("\n正在安装基本依赖...")
            for package, pip_name in missing_deps:
                print(f"  安装 {package}...")
                if install_package(pip_name):
                    print(f"  ✓ {package} 安装成功")
                else:
                    print(f"  ✗ {package} 安装失败")
                    print("请手动安装或检查网络连接")
                    return
        else:
            print("请手动安装基本依赖:")
            for package, pip_name in missing_deps:
                print(f"  pip install {pip_name}")
            return
    
    # 选择启动模式
    print("\n3. 选择启动模式:")
    print("   1) 演示模式 (推荐) - 无需完整依赖，展示所有GUI功能")
    print("   2) 完整模式 - 需要完整依赖，支持实际视频处理")
    print("   3) 原始模式 - 使用原始OpenCV界面")
    print("   4) 检查系统状态")
    
    while True:
        choice = input("\n请选择模式 (1-4): ").strip()
        
        if choice == "1":
            print("\n启动演示模式...")
            try:
                import demo_gui
                demo_gui.main()
            except Exception as e:
                print(f"演示模式启动失败: {e}")
                print("请检查PyQt6是否正确安装")
            break
            
        elif choice == "2":
            if missing_optional:
                print(f"\n⚠️  警告: 缺少可选依赖: {', '.join([dep[0] for dep in missing_optional])}")
                print("完整模式可能无法正常工作")
                response = input("仍要继续吗? (y/n): ").strip().lower()
                if response != 'y':
                    continue
            
            print("\n启动完整模式...")
            try:
                import gui_main
                gui_main.main()
            except Exception as e:
                print(f"完整模式启动失败: {e}")
                print("请安装所有依赖或使用演示模式")
            break
            
        elif choice == "3":
            print("\n启动原始模式...")
            print("使用命令行参数启动原始系统:")
            print("  python main.py --video-mode --video1 path1.mp4 --video2 path2.mp4")
            print("  python main.py --camera-mode --camera-url1 http://192.168.1.100:8080/video")
            break
            
        elif choice == "4":
            print("\n系统状态检查:")
            try:
                import test_core
                test_core.main()
            except Exception as e:
                print(f"系统状态检查失败: {e}")
            break
            
        else:
            print("无效选择，请输入1-4")
            continue

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断，退出启动器")
    except Exception as e:
        print(f"\n启动器异常: {e}")
        import traceback
        traceback.print_exc()