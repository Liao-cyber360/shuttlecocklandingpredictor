#!/usr/bin/env python3
"""
PyQt6 GUI for Enhanced Badminton Shuttlecock Landing Prediction System
重构版本：使用PyQt6图形界面，支持多标签页和配置记忆功能
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

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

import cv2
import numpy as np

# Import the original system components
try:
    from system_adapter import SystemAdapter
    from utils import config, UIHelper
    SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"Warning: System components not available: {e}")
    SYSTEM_AVAILABLE = False


class ConfigManager:
    """配置管理器 - 负责保存和加载用户配置"""
    
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


class SystemThread(QThread):
    """系统处理线程 - 使用SystemAdapter"""
    
    frame_ready = pyqtSignal(np.ndarray)  # 新帧准备就绪
    status_update = pyqtSignal(str)  # 状态更新
    prediction_result = pyqtSignal(dict)  # 预测结果
    error_occurred = pyqtSignal(str)  # 错误信息
    system_info_update = pyqtSignal(dict)  # 系统信息更新
    
    def __init__(self, parent=None):
        super().__init__(parent)
        if SYSTEM_AVAILABLE:
            self.adapter = SystemAdapter()
            self._setup_callbacks()
        else:
            self.adapter = None
        
        self.info_timer = QTimer()
        self.info_timer.timeout.connect(self._update_system_info)
        self.info_timer.setInterval(1000)  # 每秒更新一次
        
    def _setup_callbacks(self):
        """设置适配器回调"""
        if self.adapter:
            self.adapter.set_frame_callback(self.frame_ready.emit)
            self.adapter.set_status_callback(self.status_update.emit)
            self.adapter.set_error_callback(self.error_occurred.emit)
    
    def _update_system_info(self):
        """更新系统信息"""
        if self.adapter:
            info = self.adapter.get_system_info()
            self.system_info_update.emit(info)
    
    def initialize_system(self, video1_path: str, video2_path: str):
        """初始化系统"""
        if not self.adapter:
            self.error_occurred.emit("系统适配器不可用")
            return False
            
        return self.adapter.initialize_video_system(video1_path, video2_path)
    
    def initialize_network_cameras(self, url1: str, url2: str, timestamp_header: str):
        """初始化网络摄像头"""
        if not self.adapter:
            self.error_occurred.emit("系统适配器不可用")
            return False
            
        return self.adapter.initialize_network_cameras(url1, url2, timestamp_header)
    
    def start_processing(self):
        """开始处理"""
        if self.adapter:
            self.adapter.start_processing()
            self.info_timer.start()
    
    def pause_system(self):
        """暂停系统"""
        if self.adapter:
            self.adapter.pause_system()
    
    def resume_system(self):
        """恢复系统"""
        if self.adapter:
            self.adapter.resume_system()
    
    def trigger_prediction(self):
        """触发预测"""
        if self.adapter:
            self.adapter.trigger_prediction()
    
    def reset_system(self):
        """重置系统"""
        if self.adapter:
            self.adapter.reset_system()
    
    def set_playback_speed(self, speed: float):
        """设置播放速度"""
        if self.adapter:
            self.adapter.set_playback_speed(speed)
    
    def toggle_3d_visualization(self):
        """切换3D可视化"""
        if self.adapter:
            self.adapter.toggle_3d_visualization()
    
    def close_3d_visualization(self):
        """关闭3D可视化"""
        if self.adapter:
            self.adapter.close_3d_visualization()
    
    def toggle_3d_element(self, element_type: str):
        """切换3D元素"""
        if self.adapter:
            self.adapter.toggle_3d_element(element_type)
    
    def stop_system(self):
        """停止系统"""
        if self.adapter:
            self.adapter.stop_processing()
        self.info_timer.stop()


class VideoDisplayWidget(QLabel):
    """视频显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 480)
        self.setStyleSheet("border: 1px solid gray;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("视频显示区域\nVideo Display Area")
        
    def update_frame(self, frame: np.ndarray):
        """更新显示帧"""
        try:
            # 转换OpenCV BGR到RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = rgb_frame.shape
            bytes_per_line = 3 * width
            
            # 创建QImage
            q_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            
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
        layout.addWidget(self.play_pause_btn)
        
        # 预测按钮
        self.predict_btn = QPushButton("🎯 触发预测")
        self.predict_btn.clicked.connect(self.predict_clicked.emit)
        self.predict_btn.setEnabled(False)  # 默认禁用，暂停时启用
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


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.system_thread = None
        
        self.setup_ui()
        self.restore_window_state()
        
        # 检查系统可用性
        if not SYSTEM_AVAILABLE:
            self.status_bar.showMessage("警告: 系统组件不可用，仅演示模式")
            QMessageBox.warning(self, "警告", 
                               "系统组件不可用。\n"
                               "这可能是因为缺少依赖或在无显示环境中运行。\n"
                               "界面功能正常，但系统功能受限。")
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("羽毛球落点预测系统 v6.0 - PyQt6版本")
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
        self.status_bar.showMessage("系统就绪")
        
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
        
        self.system_state_label = QLabel("状态: 未初始化")
        self.fps_label = QLabel("FPS: --")
        self.frame_count_label = QLabel("帧数: --")
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
        window_controls_layout.addWidget(self.open_3d_btn)
        
        self.close_3d_btn = QPushButton("关闭3D窗口")
        self.close_3d_btn.clicked.connect(self.close_3d_visualization)
        window_controls_layout.addWidget(self.close_3d_btn)
        
        window_controls_layout.addStretch()
        layout.addLayout(window_controls_layout)
        
        # 调试信息显示
        debug_group = QGroupBox("调试信息")
        debug_layout = QVBoxLayout(debug_group)
        
        self.debug_text = QTextEdit()
        self.debug_text.setMaximumHeight(200)
        self.debug_text.setReadOnly(True)
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
        buttons_layout.addWidget(save_config_btn)
        
        load_config_btn = QPushButton("重载配置")
        load_config_btn.clicked.connect(self.load_configuration)
        buttons_layout.addWidget(load_config_btn)
        
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
        
        # 初始化系统
        self.initialize_video_system(video1, video2)
    
    def open_network_cameras(self):
        """打开网络摄像头连接对话框"""
        # 这里可以实现一个专门的网络摄像头配置对话框
        url1 = self.camera_url1_edit.text()
        url2 = self.camera_url2_edit.text()
        
        if not url1:
            QMessageBox.warning(self, "警告", "请先在设置页面中配置摄像头URL")
            self.tab_widget.setCurrentIndex(2)  # 切换到设置页面
            return
        
        self.initialize_camera_system(url1, url2)
    
    def initialize_video_system(self, video1: str, video2: str):
        """初始化视频系统"""
        if self.system_thread and self.system_thread.isRunning():
            self.system_thread.stop_system()
            self.system_thread.wait()
        
        self.system_thread = SystemThread()
        self.system_thread.frame_ready.connect(self.video_display.update_frame)
        self.system_thread.status_update.connect(self.status_bar.showMessage)
        self.system_thread.error_occurred.connect(self.on_system_error)
        
        self.system_thread.frame_ready.connect(self.video_display.update_frame)
        self.system_thread.status_update.connect(self.status_bar.showMessage)
        self.system_thread.error_occurred.connect(self.on_system_error)
        self.system_thread.system_info_update.connect(self.update_system_status_display)
        
        if self.system_thread.initialize_system(video1, video2):
            self.system_thread.start_processing()
            self.status_bar.showMessage("视频系统已初始化")
        else:
            QMessageBox.critical(self, "错误", "视频系统初始化失败")
    
    def initialize_camera_system(self, url1: str, url2: str):
        """初始化网络摄像头系统"""
        if self.system_thread and self.system_thread.isRunning():
            self.system_thread.stop_system()
            self.system_thread.wait()
        
        self.system_thread = SystemThread()
        self.system_thread.frame_ready.connect(self.video_display.update_frame)
        self.system_thread.status_update.connect(self.status_bar.showMessage)
        self.system_thread.error_occurred.connect(self.on_system_error)
        
        self.system_thread.frame_ready.connect(self.video_display.update_frame)
        self.system_thread.status_update.connect(self.status_bar.showMessage)
        self.system_thread.error_occurred.connect(self.on_system_error)
        self.system_thread.system_info_update.connect(self.update_system_status_display)
        
        if self.system_thread.initialize_network_cameras(url1, url2, "X-Timestamp"):
            self.system_thread.start_processing()
            self.status_bar.showMessage("网络摄像头系统已初始化")
        else:
            QMessageBox.critical(self, "错误", "网络摄像头系统初始化失败")
    
    def on_play_pause(self):
        """播放/暂停控制"""
        if self.system_thread:
            if self.video_controls.is_playing:
                self.system_thread.resume_system()
                self.status_bar.showMessage("播放中...")
            else:
                self.system_thread.pause_system()
                self.status_bar.showMessage("已暂停")
    
    def on_predict(self):
        """触发预测"""
        if self.system_thread:
            self.system_thread.trigger_prediction()
            self.status_bar.showMessage("触发预测...")
    
    def on_reset(self):
        """重置系统"""
        if self.system_thread and hasattr(self.system_thread.system, '_handle_system_reset'):
            self.system_thread.system._handle_system_reset()
            self.status_bar.showMessage("系统已重置")
    
    def on_speed_change(self, speed: float):
        """速度变化"""
        if self.system_thread:
            self.system_thread.set_playback_speed(speed)
    
    def update_system_status_display(self, info: Dict[str, Any]):
        """更新系统状态显示"""
        try:
            self.system_state_label.setText(f"状态: {info.get('state', '未知')}")
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
    
    def toggle_3d_element(self, element_type: str):
        """切换3D元素显示"""
        if self.system_thread:
            self.system_thread.toggle_3d_element(element_type)
    
    def toggle_3d_visualization(self):
        """切换3D可视化"""
        if self.system_thread:
            self.system_thread.toggle_3d_visualization()
    
    def close_3d_visualization(self):
        """关闭3D可视化"""
        if self.system_thread:
            self.system_thread.close_3d_visualization()
    
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
        
        QMessageBox.information(self, "提示", "配置已保存")
    
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
        
        QMessageBox.information(self, "提示", "配置已重载")
    
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
                         "• 多标签页界面\n"
                         "• 配置记忆功能\n"
                         "• 可视化按钮控制\n"
                         "• 3D可视化集成\n"
                         "• 网络摄像头支持\n\n"
                         "作者: Liao-cyber360\n"
                         "基于原始系统重构")
    
    def closeEvent(self, event):
        """关闭事件"""
        # 保存窗口状态
        self.save_window_state()
        self.config_manager.save_config(self.config)
        
        # 停止系统线程
        if self.system_thread:
            self.system_thread.stop_system()
            # 不需要wait，因为现在使用的是适配器，不是QThread的run方法
        
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("ShuttlecockLandingPredictor")
    app.setApplicationVersion("6.0")
    app.setOrganizationName("Liao-cyber360")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()