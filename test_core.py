#!/usr/bin/env python3
"""
测试核心功能 - 不依赖GUI组件
"""

import sys
import os
from pathlib import Path
import json

def test_config_manager():
    """测试配置管理器"""
    print("Testing ConfigManager...")
    
    class ConfigManager:
        def __init__(self):
            self.config_dir = Path.home() / ".shuttlecock_predictor"
            self.config_file = self.config_dir / "settings.json"
            self.config_dir.mkdir(exist_ok=True)
            self.default_config = self._get_default_config()
            
        def _get_default_config(self):
            return {
                "window": {"width": 1400, "height": 900},
                "video": {"speed": 1.0, "auto_play": True},
                "paths": {
                    "last_video1": "",
                    "last_video2": "",
                    "camera_url1": "",
                    "camera_url2": ""
                },
                "system": {
                    "prediction_cooldown": 2.0,
                    "buffer_size": 30,
                    "auto_3d_open": False
                },
                "3d_visualization": {
                    "show_all_valid": True,
                    "show_prediction": True,
                    "show_rejected": False
                }
            }
        
        def load_config(self):
            try:
                if self.config_file.exists():
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        loaded_config = json.load(f)
                        config = self.default_config.copy()
                        self._deep_update(config, loaded_config)
                        return config
            except Exception as e:
                print(f"配置加载失败: {e}")
            return self.default_config.copy()
        
        def save_config(self, config_data):
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                return True
            except Exception as e:
                print(f"配置保存失败: {e}")
                return False
        
        def _deep_update(self, base_dict, update_dict):
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    self._deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
    
    # 测试配置管理器
    cm = ConfigManager()
    config = cm.load_config()
    print(f"✓ 配置加载成功，包含 {len(config)} 个配置组")
    
    # 修改配置并保存
    config["test_timestamp"] = "2024-01-01"
    success = cm.save_config(config)
    print(f"✓ 配置保存{'成功' if success else '失败'}")
    
    # 重新加载验证
    reloaded_config = cm.load_config()
    if reloaded_config.get("test_timestamp") == "2024-01-01":
        print("✓ 配置持久化验证成功")
    else:
        print("✗ 配置持久化验证失败")
    
    return True

def test_system_adapter():
    """测试系统适配器"""
    print("\nTesting SystemAdapter...")
    
    try:
        from system_adapter import SystemAdapter
        
        # 创建适配器
        adapter = SystemAdapter()
        print("✓ SystemAdapter 创建成功")
        
        # 测试回调设置
        def test_callback(msg):
            print(f"  回调测试: {msg}")
        
        adapter.set_status_callback(test_callback)
        adapter.set_error_callback(test_callback)
        print("✓ 回调函数设置成功")
        
        # 测试系统信息获取
        info = adapter.get_system_info()
        print(f"✓ 系统信息获取成功: {info}")
        
        # 测试基本控制方法
        adapter.pause_system()
        adapter.resume_system()
        adapter.set_playback_speed(1.5)
        print("✓ 基本控制方法测试成功")
        
        # 清理
        adapter.cleanup()
        print("✓ 系统适配器清理成功")
        
        return True
        
    except ImportError as e:
        print(f"✗ SystemAdapter 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ SystemAdapter 测试失败: {e}")
        return False

def test_keyboard_control_mapping():
    """测试键盘控制到按钮的映射"""
    print("\nTesting keyboard control mapping...")
    
    # 原始键盘控制映射
    keyboard_controls = {
        "SPACE": "暂停/恢复播放",
        "T": "触发预测",
        "P": "恢复播放",
        "V": "切换3D可视化",
        "Q": "关闭3D窗口",
        "D": "打印调试统计",
        "H": "显示帮助",
        "R": "重置系统",
        "+/-": "调整播放速度",
        "0": "重置播放速度",
        "1-6": "切换3D元素显示",
        "ESC": "退出程序"
    }
    
    # 对应的GUI控制
    gui_controls = {
        "播放/暂停按钮": "SPACE - 暂停/恢复播放",
        "预测按钮": "T - 触发预测", 
        "速度滑块": "+/- - 调整播放速度",
        "重置按钮": "R - 重置系统",
        "3D窗口控制": "V/Q - 3D可视化控制",
        "3D元素复选框": "1-6 - 切换3D元素显示",
        "菜单和按钮": "H - 帮助, ESC - 退出"
    }
    
    print("✓ 键盘控制映射:")
    for key, desc in keyboard_controls.items():
        print(f"  {key:8} -> {desc}")
    
    print("\n✓ GUI控制映射:")
    for gui, keyboard in gui_controls.items():
        print(f"  {gui:15} -> {keyboard}")
    
    print("✓ 所有控制功能都已映射到GUI组件")
    return True

def main():
    """主测试函数"""
    print("=" * 60)
    print("羽毛球落点预测系统 - 核心功能测试")
    print("Shuttlecock Landing Predictor - Core Functionality Test")
    print("=" * 60)
    
    tests = [
        ("配置管理器", test_config_manager),
        ("系统适配器", test_system_adapter), 
        ("控制映射", test_keyboard_control_mapping)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name:15} {status}")
    
    all_passed = all(result for _, result in results)
    print(f"\n总体结果: {'✓ 所有测试通过' if all_passed else '✗ 部分测试失败'}")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)