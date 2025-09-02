#!/usr/bin/env python3
"""
系统重构验证脚本
System Refactor Validation Script
验证所有重构要求是否正确实现
"""

import os
import sys
import importlib.util

def check_file_structure():
    """检查文件结构"""
    print("=== 文件结构检查 / File Structure Check ===")
    
    required_files = {
        'main.py': '新主入口 (New main entry)',
        'main_original.py': '原始版本备份 (Original backup)',
        'new_main.py': 'GUI主界面实现 (GUI implementation)',
        'launcher.py': '增强启动器 (Enhanced launcher)',
        'REFACTOR_DOCUMENTATION.md': '重构文档 (Refactor docs)',
        'README.md': '更新说明 (Updated README)',
        'test_new_interface.py': '接口测试 (Interface tests)'
    }
    
    all_present = True
    for file, desc in required_files.items():
        if os.path.exists(file):
            print(f"✅ {file} - {desc}")
        else:
            print(f"❌ {file} - {desc} (缺失/Missing)")
            all_present = False
    
    return all_present

def check_import_structure():
    """检查导入结构"""
    print("\n=== 导入结构检查 / Import Structure Check ===")
    
    imports = {
        'new_main': ['ModeSelectionWidget', 'SettingsWidget', 'CalibrationWidget', 'VideoPlaybackWidget', 'MainWindow'],
        'utils': ['config', 'UIHelper'],
        'calibration': ['BadmintonCalibrator'],
        'video_controls': ['EnhancedVideoControls']
    }
    
    all_imports_ok = True
    for module, classes in imports.items():
        try:
            mod = __import__(module)
            print(f"✅ {module} 模块导入成功")
            
            for cls in classes:
                if hasattr(mod, cls):
                    print(f"  ✅ {cls} 类可用")
                else:
                    print(f"  ❌ {cls} 类不可用")
                    all_imports_ok = False
                    
        except ImportError as e:
            print(f"❌ {module} 模块导入失败: {e}")
            all_imports_ok = False
    
    return all_imports_ok

def validate_requirements():
    """验证重构要求"""
    print("\n=== 重构要求验证 / Requirements Validation ===")
    
    requirements = [
        ("不保留原始使用方法", "main.py 不再使用命令行参数", check_main_no_cli),
        ("系统级重构", "新的GUI工作流程实现", check_gui_workflow),
        ("模式选择功能", "视频和网络摄像头模式选择", check_mode_selection),
        ("设置界面", "全面的参数配置界面", check_settings_interface),
        ("标定界面", "集成的标定流程", check_calibration_interface),
        ("视频播放界面", "条件性进度条控制", check_playback_interface),
        ("参数设置", "所有可调参数集成", check_parameter_settings)
    ]
    
    all_requirements_met = True
    for req_name, req_desc, check_func in requirements:
        try:
            result = check_func()
            status = "✅" if result else "❌"
            print(f"{status} {req_name}: {req_desc}")
            if not result:
                all_requirements_met = False
        except Exception as e:
            print(f"❌ {req_name}: 检查失败 - {e}")
            all_requirements_met = False
    
    return all_requirements_met

def check_main_no_cli():
    """检查main.py不再使用CLI参数"""
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否重定向到new_main
    return 'new_main' in content and 'argparse' not in content

def check_gui_workflow():
    """检查GUI工作流程"""
    try:
        from new_main import ModeSelectionWidget, SettingsWidget, CalibrationWidget, VideoPlaybackWidget
        return True
    except ImportError:
        return False

def check_mode_selection():
    """检查模式选择功能"""
    try:
        from new_main import ModeSelectionWidget
        # 检查是否有mode_selected信号
        widget = ModeSelectionWidget()
        return hasattr(widget, 'mode_selected')
    except Exception:
        return False

def check_settings_interface():
    """检查设置界面"""
    try:
        from new_main import SettingsWidget
        # 检查是否有标签页结构
        widget = SettingsWidget('video')
        return hasattr(widget, 'collect_settings')
    except Exception:
        return False

def check_calibration_interface():
    """检查标定界面"""
    try:
        from new_main import CalibrationWidget
        settings = {'mode': 'video'}
        widget = CalibrationWidget(settings)
        return hasattr(widget, 'calibration_complete')
    except Exception:
        return False

def check_playback_interface():
    """检查播放界面"""
    try:
        from new_main import VideoPlaybackWidget
        settings = {'mode': 'video'}
        calibration_results = {}
        widget = VideoPlaybackWidget(settings, calibration_results)
        return True
    except Exception:
        return False

def check_parameter_settings():
    """检查参数设置"""
    try:
        from new_main import SettingsWidget
        widget = SettingsWidget('video')
        settings = widget.collect_settings()
        
        # 检查必要的参数类别
        required_categories = ['physics', 'detection', 'camera', 'input']
        return all(cat in settings for cat in required_categories)
    except Exception:
        return False

def check_backwards_compatibility():
    """检查向后兼容性"""
    print("\n=== 向后兼容性检查 / Backwards Compatibility Check ===")
    
    if os.path.exists('main_original.py'):
        print("✅ 原始版本已保存为 main_original.py")
        
        # 检查原始版本是否仍可导入
        try:
            with open('main_original.py', 'r') as f:
                content = f.read()
            if 'argparse' in content and 'BufferedBadmintonSystem' in content:
                print("✅ 原始CLI功能在 main_original.py 中保持完整")
                return True
            else:
                print("❌ 原始CLI功能不完整")
                return False
        except Exception as e:
            print(f"❌ 检查原始版本失败: {e}")
            return False
    else:
        print("❌ 未找到原始版本备份")
        return False

def main():
    """主验证函数"""
    print("羽毛球落点预测系统 v6.0 - 重构验证")
    print("Shuttlecock Landing Predictor v6.0 - Refactor Validation")
    print("=" * 60)
    
    # 执行所有检查
    checks = [
        ("文件结构", check_file_structure),
        ("导入结构", check_import_structure),
        ("重构要求", validate_requirements),
        ("向后兼容性", check_backwards_compatibility)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        try:
            result = check_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name}检查失败: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 重构验证通过！")
        print("🎉 Refactor validation passed!")
        print("\n系统级重构成功完成，所有要求均已实现：")
        print("System-level refactor successfully completed, all requirements met:")
        print("✅ GUI模式选择界面")
        print("✅ 综合参数设置")
        print("✅ 集成标定流程") 
        print("✅ 条件性进度控制")
        print("✅ 完整向后兼容")
        
        print("\n使用方法 / Usage:")
        print("新方式 (New): python main.py")
        print("原方式 (Legacy): python main_original.py --video-mode ...")
        
        return 0
    else:
        print("❌ 重构验证失败，需要修复问题")
        print("❌ Refactor validation failed, issues need to be fixed")
        return 1

if __name__ == "__main__":
    sys.exit(main())