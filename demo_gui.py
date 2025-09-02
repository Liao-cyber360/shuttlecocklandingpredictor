#!/usr/bin/env python3
"""
PyQt6 GUI 演示版本 - 无需完整系统依赖
Demo version of PyQt6 GUI - without full system dependencies
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
        QGridLayout, QLabel, QPushButton, QSlider, QSpinBox, QDoubleSpinBox,
        QLineEdit, QTextEdit, QFileDialog, QMessageBox, QSplitter, QFrame,
        QGroupBox, QCheckBox, QComboBox, QProgressBar, QStatusBar, QMenuBar,
        QMenu, QDialog, QFormLayout, QDialogButtonBox
    )
    from PyQt6.QtCore import (
        QTimer, QThread, pyqtSignal, Qt, QSettings, QStandardPaths
    )
    from PyQt6.QtGui import QPixmap, QImage, QAction, QIcon, QFont
    
    import numpy as np
    PYQT6_AVAILABLE = True
except ImportError as e:
    print(f"PyQt6 not available: {e}")
    PYQT6_AVAILABLE = False
    # 创建模拟类以便代码可以运行
    class QApplication:
        def __init__(self, args): pass
        def exec(self): return 0
        def setApplicationName(self, name): pass
        def setApplicationVersion(self, version): pass
        def setOrganizationName(self, name): pass
    
    class QMainWindow:
        def __init__(self): pass
        def show(self): pass
        def close(self): pass


class MockConfigManager:
    """配置管理器 - 演示版本"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".shuttlecock_predictor"
        self.config_file = self.config_dir / "settings.json"
        self.config_dir.mkdir(exist_ok=True)
        self.default_config = self._get_default_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "window": {
                "width": 1400,
                "height": 900,
                "x": 100,
                "y": 100,
                "maximized": False
            },
            "video": {
                "speed": 1.0,
                "auto_play": True,
                "pause_on_start": False
            },
            "paths": {
                "last_video1": "",
                "last_video2": "",
                "last_calibration1": "",
                "last_calibration2": "",
                "camera_url1": "",
                "camera_url2": ""
            },
            "system": {
                "prediction_cooldown": 2.0,
                "buffer_size": 30,
                "auto_3d_open": False,
                "show_debug_info": True
            },
            "3d_visualization": {
                "show_all_valid": True,
                "show_prediction": True,
                "show_rejected": False,
                "show_low_quality": False,
                "show_triangulation_failed": False,
                "show_trajectory": True
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    config = self.default_config.copy()
                    self._deep_update(config, loaded_config)
                    return config
        except Exception as e:
            print(f"配置加载失败: {e}")
        
        return self.default_config.copy()
    
    def save_config(self, config_data: Dict[str, Any]):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"配置保存失败: {e}")
    
    def _deep_update(self, base_dict: dict, update_dict: dict):
        """深度更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value


if PYQT6_AVAILABLE:
    class MockSystemThread(QThread):
        """模拟系统线程 - 演示版本"""
        
        frame_ready = pyqtSignal(np.ndarray)
        status_update = pyqtSignal(str)
        prediction_result = pyqtSignal(dict)
        error_occurred = pyqtSignal(str)
        system_info_update = pyqtSignal(dict)
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self.is_running = False
            self.is_paused = False
            self.frame_count = 0
            self.fps = 30.0
            self.playback_speed = 1.0
            
            # 模拟系统信息
            self.mock_info = {
                "state": "buffering",
                "paused": False,
                "frame_count": 0,
                "actual_fps": 30.0,
                "total_predictions": 0,
                "successful_predictions": 0,
                "playback_speed": 1.0,
                "3d_window_visible": False
            }
            
            # 信息更新定时器
            self.info_timer = QTimer()
            self.info_timer.timeout.connect(self._update_info)
            self.info_timer.setInterval(1000)
            
            # 帧生成定时器
            self.frame_timer = QTimer()
            self.frame_timer.timeout.connect(self._generate_frame)
        
        def _update_info(self):
            """更新系统信息"""
            self.mock_info["frame_count"] = self.frame_count
            self.mock_info["actual_fps"] = self.fps
            self.mock_info["paused"] = self.is_paused
            self.mock_info["playback_speed"] = self.playback_speed
            self.system_info_update.emit(self.mock_info.copy())
        
        def _generate_frame(self):
            """生成模拟帧"""
            if not self.is_paused:
                # 创建模拟视频帧
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                
                # 添加动态内容
                import math
                t = time.time()
                x = int(320 + 200 * math.sin(t))
                y = int(240 + 150 * math.cos(t * 0.7))
                
                # 画一个移动的圆（模拟羽毛球）
                cv2_available = False
                try:
                    import cv2
                    cv2.circle(frame, (x, y), 20, (0, 255, 0), -1)
                    cv2_available = True
                except ImportError:
                    # 不使用cv2的简单版本
                    pass
                
                # 添加文字信息
                if cv2_available:
                    cv2.putText(frame, f"Frame: {self.frame_count}", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    cv2.putText(frame, f"Speed: {self.playback_speed:.1f}x", (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(frame, "PyQt6 Demo Mode", (10, 450),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                else:
                    # 简单的像素填充
                    frame[20:40, 10:200] = [255, 255, 255]  # 白色矩形代替文字
                
                self.frame_ready.emit(frame)
                self.frame_count += 1
        
        def initialize_system(self, video1_path: str, video2_path: str):
            """初始化系统"""
            self.status_update.emit(f"正在初始化视频系统: {video1_path}, {video2_path}")
            return True
        
        def initialize_network_cameras(self, url1: str, url2: str, timestamp_header: str):
            """初始化网络摄像头"""
            self.status_update.emit(f"正在初始化网络摄像头: {url1}")
            return True
        
        def start_processing(self):
            """开始处理"""
            self.is_running = True
            self.frame_timer.setInterval(int(1000 / (self.fps * self.playback_speed)))
            self.frame_timer.start()
            self.info_timer.start()
            self.status_update.emit("系统处理已开始")
        
        def pause_system(self):
            """暂停系统"""
            self.is_paused = True
            self.status_update.emit("系统已暂停")
        
        def resume_system(self):
            """恢复系统"""
            self.is_paused = False
            self.status_update.emit("系统已恢复")
        
        def trigger_prediction(self):
            """触发预测"""
            self.mock_info["total_predictions"] += 1
            self.mock_info["successful_predictions"] += 1
            result = {
                "landing_point": [5.2, 8.1],
                "confidence": 0.85,
                "trajectory_points": 15
            }
            self.prediction_result.emit(result)
            self.status_update.emit(f"预测完成: 落点({result['landing_point'][0]:.1f}, {result['landing_point'][1]:.1f})")
        
        def reset_system(self):
            """重置系统"""
            self.frame_count = 0
            self.mock_info["total_predictions"] = 0
            self.mock_info["successful_predictions"] = 0
            self.status_update.emit("系统已重置")
        
        def set_playback_speed(self, speed: float):
            """设置播放速度"""
            self.playback_speed = max(0.1, min(5.0, speed))
            if self.frame_timer.isActive():
                self.frame_timer.setInterval(int(1000 / (self.fps * self.playback_speed)))
            self.status_update.emit(f"播放速度: {self.playback_speed:.1f}x")
        
        def toggle_3d_visualization(self):
            """切换3D可视化"""
            self.mock_info["3d_window_visible"] = not self.mock_info["3d_window_visible"]
            status = "打开" if self.mock_info["3d_window_visible"] else "关闭"
            self.status_update.emit(f"3D可视化已{status}")
        
        def close_3d_visualization(self):
            """关闭3D可视化"""
            self.mock_info["3d_window_visible"] = False
            self.status_update.emit("3D可视化已关闭")
        
        def toggle_3d_element(self, element_type: str):
            """切换3D元素"""
            self.status_update.emit(f"3D元素 {element_type} 已切换")
        
        def stop_system(self):
            """停止系统"""
            self.is_running = False
            self.frame_timer.stop()
            self.info_timer.stop()


    class VideoDisplayWidget(QLabel):
        """视频显示组件"""
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setMinimumSize(640, 480)
            self.setStyleSheet("border: 2px solid #555; background-color: #222;")
            self.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setText("视频显示区域\nVideo Display Area\n\n等待视频加载...")
            self.setStyleSheet("color: white; background-color: #222; border: 2px solid #555; font-size: 14px;")
            
        def update_frame(self, frame: np.ndarray):
            """更新显示帧"""
            try:
                # 转换OpenCV BGR到RGB
                if len(frame.shape) == 3:
                    rgb_frame = frame[:, :, ::-1]  # BGR到RGB
                else:
                    rgb_frame = frame
                    
                height, width = rgb_frame.shape[:2]
                if len(rgb_frame.shape) == 3:
                    bytes_per_line = 3 * width
                    format_type = QImage.Format.Format_RGB888
                else:
                    bytes_per_line = width
                    format_type = QImage.Format.Format_Grayscale8
                
                # 创建QImage
                q_image = QImage(rgb_frame.data, width, height, bytes_per_line, format_type)
                
                # 缩放以适应控件大小
                scaled_pixmap = QPixmap.fromImage(q_image).scaled(
                    self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
                
                self.setPixmap(scaled_pixmap)
            except Exception as e:
                print(f"帧更新错误: {e}")


    class VideoControlsWidget(QWidget):
        """视频控制组件"""
        
        play_pause_clicked = pyqtSignal()
        predict_clicked = pyqtSignal()
        reset_clicked = pyqtSignal()
        speed_changed = pyqtSignal(float)
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setup_ui()
            self.is_playing = True
            
        def setup_ui(self):
            """设置UI"""
            layout = QHBoxLayout(self)
            
            # 播放/暂停按钮
            self.play_pause_btn = QPushButton("⏸️ 暂停")
            self.play_pause_btn.clicked.connect(self.on_play_pause)
            self.play_pause_btn.setStyleSheet("font-size: 14px; padding: 8px;")
            layout.addWidget(self.play_pause_btn)
            
            # 预测按钮
            self.predict_btn = QPushButton("🎯 触发预测")
            self.predict_btn.clicked.connect(self.predict_clicked.emit)
            self.predict_btn.setEnabled(False)  # 默认禁用，暂停时启用
            self.predict_btn.setStyleSheet("font-size: 14px; padding: 8px;")
            layout.addWidget(self.predict_btn)
            
            # 速度控制
            layout.addWidget(QLabel("速度:"))
            self.speed_slider = QSlider(Qt.Orientation.Horizontal)
            self.speed_slider.setRange(10, 300)  # 0.1x to 3.0x
            self.speed_slider.setValue(100)  # 1.0x
            self.speed_slider.valueChanged.connect(self.on_speed_change)
            layout.addWidget(self.speed_slider)
            
            self.speed_label = QLabel("1.0x")
            layout.addWidget(self.speed_label)
            
            # 重置按钮
            self.reset_btn = QPushButton("🔄 重置")
            self.reset_btn.clicked.connect(self.reset_clicked.emit)
            self.reset_btn.setStyleSheet("font-size: 14px; padding: 8px;")
            layout.addWidget(self.reset_btn)
            
            layout.addStretch()
        
        def on_play_pause(self):
            """播放/暂停切换"""
            self.is_playing = not self.is_playing
            if self.is_playing:
                self.play_pause_btn.setText("⏸️ 暂停")
                self.predict_btn.setEnabled(False)
            else:
                self.play_pause_btn.setText("▶️ 播放")
                self.predict_btn.setEnabled(True)
            
            self.play_pause_clicked.emit()
        
        def on_speed_change(self, value):
            """速度变化"""
            speed = value / 100.0
            self.speed_label.setText(f"{speed:.1f}x")
            self.speed_changed.emit(speed)


    class DemoMainWindow(QMainWindow):
        """演示主窗口"""
        
        def __init__(self):
            super().__init__()
            self.config_manager = MockConfigManager()
            self.config = self.config_manager.load_config()
            self.system_thread = None
            
            self.setup_ui()
            self.restore_window_state()
            
        def setup_ui(self):
            """设置用户界面"""
            self.setWindowTitle("羽毛球落点预测系统 v6.0 - PyQt6演示版")
            self.setMinimumSize(1200, 800)
            
            # 创建菜单栏
            self.create_menu_bar()
            
            # 创建中央tab widget
            self.tab_widget = QTabWidget()
            self.setCentralWidget(self.tab_widget)
            
            # 创建各个标签页
            self.create_video_tab()
            self.create_3d_visualization_tab()
            self.create_settings_tab()
            
            # 创建状态栏
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            self.status_bar.showMessage("系统就绪 - 演示模式")
            
        def create_menu_bar(self):
            """创建菜单栏"""
            menubar = self.menuBar()
            
            # 文件菜单
            file_menu = menubar.addMenu("文件(&F)")
            
            open_video_action = QAction("打开视频文件...", self)
            open_video_action.triggered.connect(self.open_video_files)
            file_menu.addAction(open_video_action)
            
            open_camera_action = QAction("连接网络摄像头...", self)
            open_camera_action.triggered.connect(self.open_network_cameras)
            file_menu.addAction(open_camera_action)
            
            file_menu.addSeparator()
            
            exit_action = QAction("退出(&X)", self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            # 视图菜单
            view_menu = menubar.addMenu("视图(&V)")
            
            toggle_3d_action = QAction("切换3D可视化", self)
            toggle_3d_action.triggered.connect(self.toggle_3d_visualization)
            view_menu.addAction(toggle_3d_action)
            
            # 帮助菜单
            help_menu = menubar.addMenu("帮助(&H)")
            
            about_action = QAction("关于...", self)
            about_action.triggered.connect(self.show_about)
            help_menu.addAction(about_action)
        
        def create_video_tab(self):
            """创建视频标签页"""
            video_tab = QWidget()
            layout = QVBoxLayout(video_tab)
            
            # 视频显示区域
            self.video_display = VideoDisplayWidget()
            layout.addWidget(self.video_display, stretch=1)
            
            # 视频控制区域
            self.video_controls = VideoControlsWidget()
            self.video_controls.play_pause_clicked.connect(self.on_play_pause)
            self.video_controls.predict_clicked.connect(self.on_predict)
            self.video_controls.reset_clicked.connect(self.on_reset)
            self.video_controls.speed_changed.connect(self.on_speed_change)
            layout.addWidget(self.video_controls)
            
            # 系统状态显示
            status_group = QGroupBox("系统状态")
            status_layout = QGridLayout(status_group)
            
            self.system_state_label = QLabel("状态: 演示模式")
            self.fps_label = QLabel("FPS: 30.0")
            self.frame_count_label = QLabel("帧数: 0")
            self.prediction_count_label = QLabel("预测次数: 0")
            
            status_layout.addWidget(self.system_state_label, 0, 0)
            status_layout.addWidget(self.fps_label, 0, 1)
            status_layout.addWidget(self.frame_count_label, 1, 0)
            status_layout.addWidget(self.prediction_count_label, 1, 1)
            
            layout.addWidget(status_group)
            
            self.tab_widget.addTab(video_tab, "📹 视频控制")
        
        def create_3d_visualization_tab(self):
            """创建3D可视化标签页"""
            viz_tab = QWidget()
            layout = QVBoxLayout(viz_tab)
            
            # 说明文本
            info_label = QLabel("3D可视化功能演示\n"
                               "在实际版本中，这里将集成Open3D 3D可视化窗口\n"
                               "支持实时显示羽毛球轨迹和落点预测")
            info_label.setStyleSheet("color: #666; font-size: 12px; padding: 10px; background-color: #f0f0f0;")
            layout.addWidget(info_label)
            
            # 3D控制按钮组
            controls_group = QGroupBox("3D可视化控制")
            controls_layout = QGridLayout(controls_group)
            
            # 显示控制复选框
            self.show_all_valid_cb = QCheckBox("显示所有有效点")
            self.show_prediction_cb = QCheckBox("显示预测点")
            self.show_rejected_cb = QCheckBox("显示被拒绝点")
            self.show_low_quality_cb = QCheckBox("显示低质量点")
            self.show_triangulation_failed_cb = QCheckBox("显示三角化失败点")
            self.show_trajectory_cb = QCheckBox("显示预测轨迹")
            
            # 设置默认状态
            viz_config = self.config.get("3d_visualization", {})
            self.show_all_valid_cb.setChecked(viz_config.get("show_all_valid", True))
            self.show_prediction_cb.setChecked(viz_config.get("show_prediction", True))
            self.show_rejected_cb.setChecked(viz_config.get("show_rejected", False))
            self.show_low_quality_cb.setChecked(viz_config.get("show_low_quality", False))
            self.show_triangulation_failed_cb.setChecked(viz_config.get("show_triangulation_failed", False))
            self.show_trajectory_cb.setChecked(viz_config.get("show_trajectory", True))
            
            # 连接信号
            self.show_all_valid_cb.toggled.connect(lambda: self.toggle_3d_element('all_valid'))
            self.show_prediction_cb.toggled.connect(lambda: self.toggle_3d_element('prediction'))
            self.show_rejected_cb.toggled.connect(lambda: self.toggle_3d_element('rejected'))
            self.show_low_quality_cb.toggled.connect(lambda: self.toggle_3d_element('low_quality'))
            self.show_triangulation_failed_cb.toggled.connect(lambda: self.toggle_3d_element('triangulation_failed'))
            self.show_trajectory_cb.toggled.connect(lambda: self.toggle_3d_element('predicted_trajectory'))
            
            controls_layout.addWidget(self.show_all_valid_cb, 0, 0)
            controls_layout.addWidget(self.show_prediction_cb, 0, 1)
            controls_layout.addWidget(self.show_rejected_cb, 1, 0)
            controls_layout.addWidget(self.show_low_quality_cb, 1, 1)
            controls_layout.addWidget(self.show_triangulation_failed_cb, 2, 0)
            controls_layout.addWidget(self.show_trajectory_cb, 2, 1)
            
            layout.addWidget(controls_group)
            
            # 3D窗口控制按钮
            window_controls_layout = QHBoxLayout()
            
            self.open_3d_btn = QPushButton("打开3D窗口")
            self.open_3d_btn.clicked.connect(self.toggle_3d_visualization)
            self.open_3d_btn.setStyleSheet("font-size: 14px; padding: 8px;")
            window_controls_layout.addWidget(self.open_3d_btn)
            
            self.close_3d_btn = QPushButton("关闭3D窗口")
            self.close_3d_btn.clicked.connect(self.close_3d_visualization)
            self.close_3d_btn.setStyleSheet("font-size: 14px; padding: 8px;")
            window_controls_layout.addWidget(self.close_3d_btn)
            
            window_controls_layout.addStretch()
            layout.addLayout(window_controls_layout)
            
            # 调试信息显示
            debug_group = QGroupBox("调试信息")
            debug_layout = QVBoxLayout(debug_group)
            
            self.debug_text = QTextEdit()
            self.debug_text.setMaximumHeight(200)
            self.debug_text.setReadOnly(True)
            self.debug_text.append("演示模式 - 调试信息将在此显示")
            self.debug_text.append("3D可视化元素切换功能已启用")
            debug_layout.addWidget(self.debug_text)
            
            layout.addWidget(debug_group)
            layout.addStretch()
            
            self.tab_widget.addTab(viz_tab, "🌐 3D可视化")
        
        def create_settings_tab(self):
            """创建设置标签页"""
            settings_tab = QWidget()
            layout = QVBoxLayout(settings_tab)
            
            # 路径设置组
            paths_group = QGroupBox("文件路径设置")
            paths_layout = QFormLayout(paths_group)
            
            self.video1_path_edit = QLineEdit()
            self.video1_path_edit.setText(self.config.get("paths", {}).get("last_video1", ""))
            video1_btn = QPushButton("浏览...")
            video1_btn.clicked.connect(lambda: self.browse_file(self.video1_path_edit, "选择视频文件1", "视频文件 (*.mp4 *.avi *.mov)"))
            
            video1_layout = QHBoxLayout()
            video1_layout.addWidget(self.video1_path_edit)
            video1_layout.addWidget(video1_btn)
            paths_layout.addRow("视频文件1:", video1_layout)
            
            self.video2_path_edit = QLineEdit()
            self.video2_path_edit.setText(self.config.get("paths", {}).get("last_video2", ""))
            video2_btn = QPushButton("浏览...")
            video2_btn.clicked.connect(lambda: self.browse_file(self.video2_path_edit, "选择视频文件2", "视频文件 (*.mp4 *.avi *.mov)"))
            
            video2_layout = QHBoxLayout()
            video2_layout.addWidget(self.video2_path_edit)
            video2_layout.addWidget(video2_btn)
            paths_layout.addRow("视频文件2:", video2_layout)
            
            layout.addWidget(paths_group)
            
            # 网络摄像头设置组
            camera_group = QGroupBox("网络摄像头设置")
            camera_layout = QFormLayout(camera_group)
            
            self.camera_url1_edit = QLineEdit()
            self.camera_url1_edit.setText(self.config.get("paths", {}).get("camera_url1", ""))
            self.camera_url1_edit.setPlaceholderText("http://192.168.1.100:8080/video")
            camera_layout.addRow("摄像头1 URL:", self.camera_url1_edit)
            
            self.camera_url2_edit = QLineEdit()
            self.camera_url2_edit.setText(self.config.get("paths", {}).get("camera_url2", ""))
            self.camera_url2_edit.setPlaceholderText("http://192.168.1.101:8080/video")
            camera_layout.addRow("摄像头2 URL:", self.camera_url2_edit)
            
            layout.addWidget(camera_group)
            
            # 系统参数设置组
            system_group = QGroupBox("系统参数")
            system_layout = QFormLayout(system_group)
            
            self.prediction_cooldown_spin = QDoubleSpinBox()
            self.prediction_cooldown_spin.setRange(0.1, 10.0)
            self.prediction_cooldown_spin.setSingleStep(0.1)
            self.prediction_cooldown_spin.setValue(self.config.get("system", {}).get("prediction_cooldown", 2.0))
            system_layout.addRow("预测冷却时间(秒):", self.prediction_cooldown_spin)
            
            self.buffer_size_spin = QSpinBox()
            self.buffer_size_spin.setRange(10, 100)
            self.buffer_size_spin.setValue(self.config.get("system", {}).get("buffer_size", 30))
            system_layout.addRow("缓冲区大小:", self.buffer_size_spin)
            
            self.auto_3d_open_cb = QCheckBox("自动打开3D可视化")
            self.auto_3d_open_cb.setChecked(self.config.get("system", {}).get("auto_3d_open", False))
            system_layout.addRow("", self.auto_3d_open_cb)
            
            self.show_debug_info_cb = QCheckBox("显示调试信息")
            self.show_debug_info_cb.setChecked(self.config.get("system", {}).get("show_debug_info", True))
            system_layout.addRow("", self.show_debug_info_cb)
            
            layout.addWidget(system_group)
            
            # 控制按钮
            buttons_layout = QHBoxLayout()
            
            save_config_btn = QPushButton("保存配置")
            save_config_btn.clicked.connect(self.save_configuration)
            save_config_btn.setStyleSheet("font-size: 14px; padding: 8px;")
            buttons_layout.addWidget(save_config_btn)
            
            load_config_btn = QPushButton("重载配置")
            load_config_btn.clicked.connect(self.load_configuration)
            load_config_btn.setStyleSheet("font-size: 14px; padding: 8px;")
            buttons_layout.addWidget(load_config_btn)
            
            start_demo_btn = QPushButton("启动演示模式")
            start_demo_btn.clicked.connect(self.start_demo_mode)
            start_demo_btn.setStyleSheet("font-size: 14px; padding: 8px; background-color: #4CAF50; color: white;")
            buttons_layout.addWidget(start_demo_btn)
            
            buttons_layout.addStretch()
            layout.addLayout(buttons_layout)
            
            layout.addStretch()
            
            self.tab_widget.addTab(settings_tab, "⚙️ 设置")
        
        def restore_window_state(self):
            """恢复窗口状态"""
            window_config = self.config.get("window", {})
            
            # 设置窗口大小和位置
            self.resize(window_config.get("width", 1400), window_config.get("height", 900))
            self.move(window_config.get("x", 100), window_config.get("y", 100))
            
            if window_config.get("maximized", False):
                self.showMaximized()
        
        def save_window_state(self):
            """保存窗口状态"""
            if not self.isMaximized():
                self.config["window"]["width"] = self.width()
                self.config["window"]["height"] = self.height()
                self.config["window"]["x"] = self.x()
                self.config["window"]["y"] = self.y()
            
            self.config["window"]["maximized"] = self.isMaximized()
        
        def start_demo_mode(self):
            """启动演示模式"""
            if self.system_thread and hasattr(self.system_thread, 'is_running') and self.system_thread.is_running:
                QMessageBox.information(self, "提示", "演示模式已在运行")
                return
            
            # 创建并启动模拟系统线程
            self.system_thread = MockSystemThread()
            self.system_thread.frame_ready.connect(self.video_display.update_frame)
            self.system_thread.status_update.connect(self.status_bar.showMessage)
            self.system_thread.error_occurred.connect(self.on_system_error)
            self.system_thread.system_info_update.connect(self.update_system_status_display)
            self.system_thread.prediction_result.connect(self.on_prediction_result)
            
            self.system_thread.initialize_system("demo_video1.mp4", "demo_video2.mp4")
            self.system_thread.start_processing()
            
            self.status_bar.showMessage("演示模式已启动")
            QMessageBox.information(self, "演示模式", 
                                   "演示模式已启动！\n\n"
                                   "• 模拟视频帧显示\n"
                                   "• 可使用所有控制按钮\n"
                                   "• 配置保存/加载功能\n"
                                   "• 3D可视化控制面板\n\n"
                                   "切换到视频控制页面查看效果。")
        
        def open_video_files(self):
            """打开视频文件"""
            video1, _ = QFileDialog.getOpenFileName(
                self, "选择视频文件1", "", "视频文件 (*.mp4 *.avi *.mov *.mkv)"
            )
            if not video1:
                return
                
            video2, _ = QFileDialog.getOpenFileName(
                self, "选择视频文件2", "", "视频文件 (*.mp4 *.avi *.mov *.mkv)"
            )
            if not video2:
                return
            
            # 更新界面显示
            self.video1_path_edit.setText(video1)
            self.video2_path_edit.setText(video2)
            
            QMessageBox.information(self, "提示", 
                                   f"已选择视频文件：\n"
                                   f"文件1: {video1}\n"
                                   f"文件2: {video2}\n\n"
                                   f"在完整版本中，这里会初始化视频系统。")
        
        def open_network_cameras(self):
            """打开网络摄像头连接对话框"""
            url1 = self.camera_url1_edit.text()
            url2 = self.camera_url2_edit.text()
            
            if not url1:
                QMessageBox.warning(self, "警告", "请先在设置页面中配置摄像头URL")
                self.tab_widget.setCurrentIndex(2)  # 切换到设置页面
                return
            
            QMessageBox.information(self, "网络摄像头", 
                                   f"网络摄像头配置：\n"
                                   f"摄像头1: {url1}\n"
                                   f"摄像头2: {url2 if url2 else '未配置'}\n\n"
                                   f"在完整版本中，这里会连接网络摄像头。")
        
        def on_play_pause(self):
            """播放/暂停控制"""
            if self.system_thread:
                if self.video_controls.is_playing:
                    self.system_thread.resume_system()
                else:
                    self.system_thread.pause_system()
        
        def on_predict(self):
            """触发预测"""
            if self.system_thread:
                self.system_thread.trigger_prediction()
        
        def on_reset(self):
            """重置系统"""
            if self.system_thread:
                self.system_thread.reset_system()
        
        def on_speed_change(self, speed: float):
            """速度变化"""
            if self.system_thread:
                self.system_thread.set_playback_speed(speed)
        
        def on_prediction_result(self, result: dict):
            """处理预测结果"""
            self.debug_text.append(f"预测结果: 落点({result['landing_point'][0]:.1f}, {result['landing_point'][1]:.1f}), "
                                  f"置信度: {result['confidence']:.2f}")
        
        def update_system_status_display(self, info: dict):
            """更新系统状态显示"""
            try:
                self.system_state_label.setText(f"状态: {info.get('state', '演示模式')}")
                self.fps_label.setText(f"FPS: {info.get('actual_fps', 0):.1f}")
                self.frame_count_label.setText(f"帧数: {info.get('frame_count', 0)}")
                
                total_pred = info.get('total_predictions', 0)
                success_pred = info.get('successful_predictions', 0)
                self.prediction_count_label.setText(f"预测: {success_pred}/{total_pred}")
                
                # 更新3D窗口状态按钮
                if info.get('3d_window_visible', False):
                    self.open_3d_btn.setText("3D窗口已打开")
                    self.close_3d_btn.setEnabled(True)
                else:
                    self.open_3d_btn.setText("打开3D窗口")
                    self.close_3d_btn.setEnabled(False)
                    
            except Exception as e:
                print(f"更新状态显示错误: {e}")
        
        def toggle_3d_visualization(self):
            """切换3D可视化"""
            if self.system_thread:
                self.system_thread.toggle_3d_visualization()
        
        def close_3d_visualization(self):
            """关闭3D可视化"""
            if self.system_thread:
                self.system_thread.close_3d_visualization()
        
        def toggle_3d_element(self, element_type: str):
            """切换3D元素显示"""
            if self.system_thread:
                self.system_thread.toggle_3d_element(element_type)
                self.debug_text.append(f"切换3D元素: {element_type}")
        
        def browse_file(self, line_edit: QLineEdit, title: str, filter_str: str):
            """浏览文件"""
            file_path, _ = QFileDialog.getOpenFileName(self, title, "", filter_str)
            if file_path:
                line_edit.setText(file_path)
        
        def save_configuration(self):
            """保存配置"""
            # 更新配置数据
            self.config["paths"]["last_video1"] = self.video1_path_edit.text()
            self.config["paths"]["last_video2"] = self.video2_path_edit.text()
            self.config["paths"]["camera_url1"] = self.camera_url1_edit.text()
            self.config["paths"]["camera_url2"] = self.camera_url2_edit.text()
            
            self.config["system"]["prediction_cooldown"] = self.prediction_cooldown_spin.value()
            self.config["system"]["buffer_size"] = self.buffer_size_spin.value()
            self.config["system"]["auto_3d_open"] = self.auto_3d_open_cb.isChecked()
            self.config["system"]["show_debug_info"] = self.show_debug_info_cb.isChecked()
            
            self.config["3d_visualization"]["show_all_valid"] = self.show_all_valid_cb.isChecked()
            self.config["3d_visualization"]["show_prediction"] = self.show_prediction_cb.isChecked()
            self.config["3d_visualization"]["show_rejected"] = self.show_rejected_cb.isChecked()
            self.config["3d_visualization"]["show_low_quality"] = self.show_low_quality_cb.isChecked()
            self.config["3d_visualization"]["show_triangulation_failed"] = self.show_triangulation_failed_cb.isChecked()
            self.config["3d_visualization"]["show_trajectory"] = self.show_trajectory_cb.isChecked()
            
            self.save_window_state()
            self.config_manager.save_config(self.config)
            
            QMessageBox.information(self, "提示", "配置已保存到本地文件")
        
        def load_configuration(self):
            """重载配置"""
            self.config = self.config_manager.load_config()
            
            # 更新界面
            self.video1_path_edit.setText(self.config.get("paths", {}).get("last_video1", ""))
            self.video2_path_edit.setText(self.config.get("paths", {}).get("last_video2", ""))
            self.camera_url1_edit.setText(self.config.get("paths", {}).get("camera_url1", ""))
            self.camera_url2_edit.setText(self.config.get("paths", {}).get("camera_url2", ""))
            
            self.prediction_cooldown_spin.setValue(self.config.get("system", {}).get("prediction_cooldown", 2.0))
            self.buffer_size_spin.setValue(self.config.get("system", {}).get("buffer_size", 30))
            self.auto_3d_open_cb.setChecked(self.config.get("system", {}).get("auto_3d_open", False))
            self.show_debug_info_cb.setChecked(self.config.get("system", {}).get("show_debug_info", True))
            
            viz_config = self.config.get("3d_visualization", {})
            self.show_all_valid_cb.setChecked(viz_config.get("show_all_valid", True))
            self.show_prediction_cb.setChecked(viz_config.get("show_prediction", True))
            self.show_rejected_cb.setChecked(viz_config.get("show_rejected", False))
            self.show_low_quality_cb.setChecked(viz_config.get("show_low_quality", False))
            self.show_triangulation_failed_cb.setChecked(viz_config.get("show_triangulation_failed", False))
            self.show_trajectory_cb.setChecked(viz_config.get("show_trajectory", True))
            
            QMessageBox.information(self, "提示", "配置已从本地文件重载")
        
        def on_system_error(self, error_msg: str):
            """处理系统错误"""
            QMessageBox.critical(self, "系统错误", error_msg)
            self.status_bar.showMessage(f"错误: {error_msg}")
        
        def show_about(self):
            """显示关于对话框"""
            QMessageBox.about(self, "关于", 
                             "羽毛球落点预测系统 v6.0\n"
                             "PyQt6 图形界面版本\n\n"
                             "功能特点:\n"
                             "• 多标签页界面，避免界面拥挤\n"
                             "• 配置记忆功能，保存用户设置\n"
                             "• 可视化按钮控制，替代键盘操作\n"
                             "• 3D可视化集成与控制\n"
                             "• 网络摄像头支持\n"
                             "• 视频文件处理\n\n"
                             "原键盘控制已完全转换为GUI按钮:\n"
                             "• SPACE → 播放/暂停按钮\n"
                             "• T → 预测按钮\n"
                             "• +/- → 速度滑块\n"
                             "• R → 重置按钮\n"
                             "• V/Q → 3D可视化控制\n"
                             "• 1-6 → 3D元素复选框\n\n"
                             "作者: Liao-cyber360\n"
                             "基于原始系统完全重构")
        
        def closeEvent(self, event):
            """关闭事件"""
            # 保存窗口状态
            self.save_window_state()
            self.config_manager.save_config(self.config)
            
            # 停止系统线程
            if self.system_thread:
                self.system_thread.stop_system()
            
            event.accept()


def main():
    """主函数"""
    if not PYQT6_AVAILABLE:
        print("PyQt6 不可用，无法运行GUI演示")
        print("请安装PyQt6: pip install PyQt6")
        return
    
    import sys
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("ShuttlecockLandingPredictor")
    app.setApplicationVersion("6.0")
    app.setOrganizationName("Liao-cyber360")
    
    # 创建并显示主窗口
    window = DemoMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()