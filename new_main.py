#!/usr/bin/env python3
"""
羽毛球落点预测系统 - 新版主界面
Shuttlecock Landing Predictor - New Main Interface
System-Level Refactor Version
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
    QPushButton, QButtonGroup, QRadioButton, QGroupBox, QMessageBox,
    QStackedWidget, QGridLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
    QFileDialog, QTabWidget, QTextEdit, QProgressBar, QSlider,
    QCheckBox, QComboBox, QFormLayout, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QPixmap, QIcon

# Import system components
try:
    from utils import config, UIHelper
    from calibration import BadmintonCalibrator
    from network_camera import NetworkCameraManager
    from video_controls import EnhancedVideoControls
    import cv2
    import numpy as np
    SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"Warning: System components not available: {e}")
    SYSTEM_AVAILABLE = False


class ModeSelectionWidget(QWidget):
    """模式选择界面"""
    
    mode_selected = pyqtSignal(str)  # 'video' or 'camera'
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 标题
        title = QLabel("羽毛球落点预测系统")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(title)
        
        subtitle = QLabel("请选择输入模式")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Arial", 14))
        layout.addWidget(subtitle)
        
        layout.addStretch()
        
        # 模式选择组
        mode_group = QGroupBox("输入模式选择")
        mode_layout = QVBoxLayout()
        mode_group.setLayout(mode_layout)
        
        self.button_group = QButtonGroup()
        
        # 本地视频模式
        self.video_radio = QRadioButton("本地视频模式")
        self.video_radio.setFont(QFont("Arial", 12))
        video_desc = QLabel("• 从本地视频文件进行分析\n• 支持进度条控制\n• 适合离线分析和回放")
        video_desc.setStyleSheet("color: gray; margin-left: 20px;")
        
        # 网络摄像头模式  
        self.camera_radio = QRadioButton("网络摄像头模式")
        self.camera_radio.setFont(QFont("Arial", 12))
        camera_desc = QLabel("• 实时网络摄像头分析\n• 支持MJPEG流\n• 适合实时监测")
        camera_desc.setStyleSheet("color: gray; margin-left: 20px;")
        
        self.button_group.addButton(self.video_radio)
        self.button_group.addButton(self.camera_radio)
        
        mode_layout.addWidget(self.video_radio)
        mode_layout.addWidget(video_desc)
        mode_layout.addSpacing(20)
        mode_layout.addWidget(self.camera_radio)
        mode_layout.addWidget(camera_desc)
        
        layout.addWidget(mode_group)
        layout.addStretch()
        
        # 确认按钮
        confirm_btn = QPushButton("确认选择")
        confirm_btn.setFont(QFont("Arial", 14))
        confirm_btn.setMinimumHeight(50)
        confirm_btn.clicked.connect(self.on_confirm)
        layout.addWidget(confirm_btn)
        
        # 默认选择视频模式
        self.video_radio.setChecked(True)
    
    def on_confirm(self):
        """确认选择"""
        if self.video_radio.isChecked():
            self.mode_selected.emit('video')
        elif self.camera_radio.isChecked():
            self.mode_selected.emit('camera')


class SettingsWidget(QWidget):
    """设置界面"""
    
    settings_complete = pyqtSignal(dict)
    
    def __init__(self, mode: str):
        super().__init__()
        self.mode = mode
        self.settings = {}
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 标题
        title = QLabel(f"{'本地视频' if self.mode == 'video' else '网络摄像头'}模式设置")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 创建标签页
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # 输入设置标签页
        input_tab = self.create_input_settings_tab()
        tab_widget.addTab(input_tab, "输入设置")
        
        # 摄像头参数标签页
        camera_tab = self.create_camera_settings_tab()
        tab_widget.addTab(camera_tab, "摄像头参数")
        
        # 物理参数标签页
        physics_tab = self.create_physics_settings_tab()
        tab_widget.addTab(physics_tab, "物理参数")
        
        # 检测参数标签页
        detection_tab = self.create_detection_settings_tab()
        tab_widget.addTab(detection_tab, "检测参数")
        
        # 按钮
        button_layout = QHBoxLayout()
        back_btn = QPushButton("返回")
        back_btn.clicked.connect(self.parent().show_mode_selection)
        
        next_btn = QPushButton("下一步：标定")
        next_btn.clicked.connect(self.on_next)
        
        button_layout.addWidget(back_btn)
        button_layout.addStretch()
        button_layout.addWidget(next_btn)
        layout.addLayout(button_layout)
    
    def create_input_settings_tab(self) -> QWidget:
        """创建输入设置标签页"""
        widget = QWidget()
        layout = QFormLayout()
        widget.setLayout(layout)
        
        if self.mode == 'video':
            # 视频文件设置
            self.video1_edit = QLineEdit()
            self.video1_browse = QPushButton("浏览...")
            self.video1_browse.clicked.connect(lambda: self.browse_file(self.video1_edit, "选择摄像头1视频文件"))
            
            video1_layout = QHBoxLayout()
            video1_layout.addWidget(self.video1_edit)
            video1_layout.addWidget(self.video1_browse)
            layout.addRow("摄像头1视频文件:", video1_layout)
            
            self.video2_edit = QLineEdit()
            self.video2_browse = QPushButton("浏览...")
            self.video2_browse.clicked.connect(lambda: self.browse_file(self.video2_edit, "选择摄像头2视频文件"))
            
            video2_layout = QHBoxLayout()
            video2_layout.addWidget(self.video2_edit)
            video2_layout.addWidget(self.video2_browse)
            layout.addRow("摄像头2视频文件:", video2_layout)
            
        else:  # camera mode
            # 网络摄像头设置
            self.camera_url1_edit = QLineEdit("http://192.168.1.100:8080/video")
            layout.addRow("摄像头1 URL:", self.camera_url1_edit)
            
            self.camera_url2_edit = QLineEdit("http://192.168.1.101:8080/video")
            layout.addRow("摄像头2 URL:", self.camera_url2_edit)
            
            self.timestamp_header_edit = QLineEdit("X-Timestamp")
            layout.addRow("时间戳头:", self.timestamp_header_edit)
        
        return widget
    
    def create_camera_settings_tab(self) -> QWidget:
        """创建摄像头参数标签页"""
        widget = QWidget()
        layout = QFormLayout()
        widget.setLayout(layout)
        
        # 摄像头参数文件
        self.cam1_params_edit = QLineEdit()
        self.cam1_params_browse = QPushButton("浏览...")
        self.cam1_params_browse.clicked.connect(lambda: self.browse_file(self.cam1_params_edit, "选择摄像头1参数文件", "YAML files (*.yaml *.yml)"))
        
        cam1_layout = QHBoxLayout()
        cam1_layout.addWidget(self.cam1_params_edit)
        cam1_layout.addWidget(self.cam1_params_browse)
        layout.addRow("摄像头1内参文件:", cam1_layout)
        
        self.cam2_params_edit = QLineEdit()
        self.cam2_params_browse = QPushButton("浏览...")
        self.cam2_params_browse.clicked.connect(lambda: self.browse_file(self.cam2_params_edit, "选择摄像头2参数文件", "YAML files (*.yaml *.yml)"))
        
        cam2_layout = QHBoxLayout()
        cam2_layout.addWidget(self.cam2_params_edit)
        cam2_layout.addWidget(self.cam2_params_browse)
        layout.addRow("摄像头2内参文件:", cam2_layout)
        
        # 是否已标定
        self.calibrated_checkbox = QCheckBox("使用已有标定参数")
        layout.addRow("标定状态:", self.calibrated_checkbox)
        
        return widget
    
    def create_physics_settings_tab(self) -> QWidget:
        """创建物理参数标签页"""
        widget = QWidget()
        layout = QFormLayout()
        widget.setLayout(layout)
        
        # 羽毛球重量
        self.shuttlecock_mass = QDoubleSpinBox()
        self.shuttlecock_mass.setRange(4.0, 6.0)
        self.shuttlecock_mass.setValue(5.1)
        self.shuttlecock_mass.setSuffix(" g")
        self.shuttlecock_mass.setDecimals(1)
        layout.addRow("羽毛球重量:", self.shuttlecock_mass)
        
        # 重力加速度
        self.gravity = QDoubleSpinBox()
        self.gravity.setRange(9.7, 9.9)
        self.gravity.setValue(9.81)
        self.gravity.setSuffix(" m/s²")
        self.gravity.setDecimals(2)
        layout.addRow("重力加速度:", self.gravity)
        
        # 空气阻力长度
        self.aero_length = QDoubleSpinBox()
        self.aero_length.setRange(0.1, 2.0)
        self.aero_length.setValue(0.5)
        self.aero_length.setSuffix(" m")
        self.aero_length.setDecimals(2)
        layout.addRow("空气阻力长度:", self.aero_length)
        
        return widget
    
    def create_detection_settings_tab(self) -> QWidget:
        """创建检测参数标签页"""
        widget = QWidget()
        layout = QFormLayout()
        widget.setLayout(layout)
        
        # 缓冲图片张数
        self.buffer_size = QSpinBox()
        self.buffer_size.setRange(5, 50)
        self.buffer_size.setValue(20)
        layout.addRow("缓冲图片张数:", self.buffer_size)
        
        # 极距阈值
        self.polar_threshold = QDoubleSpinBox()
        self.polar_threshold.setRange(1.0, 20.0)
        self.polar_threshold.setValue(5.0)
        self.polar_threshold.setDecimals(1)
        layout.addRow("极距阈值:", self.polar_threshold)
        
        # 落地检测阈值
        self.landing_threshold = QSpinBox()
        self.landing_threshold.setRange(1, 20)
        self.landing_threshold.setValue(5)
        layout.addRow("落地检测阈值:", self.landing_threshold)
        
        # 落地确认帧数
        self.landing_frames = QSpinBox()
        self.landing_frames.setRange(1, 10)
        self.landing_frames.setValue(3)
        layout.addRow("落地确认帧数:", self.landing_frames)
        
        # 落地高度阈值
        self.landing_height = QDoubleSpinBox()
        self.landing_height.setRange(5.0, 50.0)
        self.landing_height.setValue(15.0)
        self.landing_height.setSuffix(" cm")
        self.landing_height.setDecimals(1)
        layout.addRow("落地高度阈值:", self.landing_height)
        
        return widget
    
    def browse_file(self, line_edit: QLineEdit, title: str, file_filter: str = "All files (*)"):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, title, "", file_filter)
        if file_path:
            line_edit.setText(file_path)
    
    def collect_settings(self) -> dict:
        """收集所有设置"""
        settings = {
            'mode': self.mode,
            'physics': {
                'shuttlecock_mass': self.shuttlecock_mass.value(),
                'gravity': self.gravity.value(),
                'aero_length': self.aero_length.value()
            },
            'detection': {
                'buffer_size': self.buffer_size.value(),
                'polar_threshold': self.polar_threshold.value(),
                'landing_threshold': self.landing_threshold.value(),
                'landing_frames': self.landing_frames.value(),
                'landing_height': self.landing_height.value()
            },
            'camera': {
                'cam1_params': self.cam1_params_edit.text(),
                'cam2_params': self.cam2_params_edit.text(),
                'calibrated': self.calibrated_checkbox.isChecked()
            }
        }
        
        if self.mode == 'video':
            settings['input'] = {
                'video1': self.video1_edit.text(),
                'video2': self.video2_edit.text()
            }
        else:
            settings['input'] = {
                'camera_url1': self.camera_url1_edit.text(),
                'camera_url2': self.camera_url2_edit.text(),
                'timestamp_header': self.timestamp_header_edit.text()
            }
        
        return settings
    
    def validate_settings(self) -> bool:
        """验证设置"""
        if self.mode == 'video':
            if not self.video1_edit.text() or not self.video2_edit.text():
                QMessageBox.warning(self, "设置错误", "请选择两个视频文件")
                return False
            
            # 检查文件是否存在
            if not os.path.exists(self.video1_edit.text()):
                QMessageBox.warning(self, "文件错误", f"视频文件1不存在: {self.video1_edit.text()}")
                return False
            
            if not os.path.exists(self.video2_edit.text()):
                QMessageBox.warning(self, "文件错误", f"视频文件2不存在: {self.video2_edit.text()}")
                return False
        
        else:  # camera mode
            if not self.camera_url1_edit.text():
                QMessageBox.warning(self, "设置错误", "请输入摄像头1的URL")
                return False
        
        return True
    
    def on_next(self):
        """下一步"""
        if self.validate_settings():
            settings = self.collect_settings()
            self.settings_complete.emit(settings)


class CalibrationWidget(QWidget):
    """标定界面"""
    
    calibration_complete = pyqtSignal(dict)
    
    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self.calibration_results = {}
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 标题
        title = QLabel("摄像头标定")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 说明文本
        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setMaximumHeight(120)
        instructions.setHtml("""
        <h3>标定说明:</h3>
        <ul>
        <li>标定过程将帮助系统了解两个摄像头的相对位置</li>
        <li>请确保羽毛球场地在两个摄像头画面中都清晰可见</li>
        <li>标定过程中需要选择场地的四个角点</li>
        <li>如果已有标定参数，可以跳过此步骤</li>
        </ul>
        """)
        layout.addWidget(instructions)
        
        # 状态显示
        self.status_label = QLabel("准备开始标定...")
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        back_btn = QPushButton("返回设置")
        back_btn.clicked.connect(self.on_back)
        
        self.start_btn = QPushButton("开始标定")
        self.start_btn.clicked.connect(self.start_calibration)
        
        self.skip_btn = QPushButton("跳过标定")
        self.skip_btn.clicked.connect(self.skip_calibration)
        
        next_btn = QPushButton("完成标定")
        next_btn.clicked.connect(self.on_complete)
        next_btn.setEnabled(False)
        self.next_btn = next_btn
        
        button_layout.addWidget(back_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.skip_btn)
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(next_btn)
        
        layout.addLayout(button_layout)
        
        # 如果已选择使用现有标定，启用跳过按钮
        if self.settings.get('camera', {}).get('calibrated', False):
            self.skip_btn.setEnabled(True)
            self.status_label.setText("已选择使用现有标定参数")
    
    def start_calibration(self):
        """开始标定"""
        self.status_label.setText("正在启动标定程序...")
        self.progress_bar.setValue(10)
        
        try:
            if SYSTEM_AVAILABLE:
                # 这里会调用实际的标定程序
                self.status_label.setText("标定程序启动中，请按照屏幕指示操作...")
                self.progress_bar.setValue(50)
                
                # 模拟标定过程
                QTimer.singleShot(2000, self.calibration_completed)
            else:
                self.status_label.setText("系统组件不可用，跳过标定")
                self.calibration_completed()
                
        except Exception as e:
            QMessageBox.warning(self, "标定错误", f"标定过程出现错误: {str(e)}")
            self.status_label.setText("标定失败")
    
    def calibration_completed(self):
        """标定完成"""
        self.status_label.setText("标定完成！")
        self.progress_bar.setValue(100)
        self.start_btn.setEnabled(False)
        self.next_btn.setEnabled(True)
        self.calibration_results = {'calibrated': True}
    
    def skip_calibration(self):
        """跳过标定"""
        self.status_label.setText("已跳过标定")
        self.progress_bar.setValue(100)
        self.start_btn.setEnabled(False)
        self.next_btn.setEnabled(True)
        self.calibration_results = {'calibrated': False, 'skipped': True}
    
    def on_back(self):
        """返回设置"""
        self.parent().show_settings()
    
    def on_complete(self):
        """完成标定"""
        self.calibration_complete.emit(self.calibration_results)


class VideoPlaybackWidget(QWidget):
    """视频播放界面"""
    
    def __init__(self, settings: dict, calibration_results: dict):
        super().__init__()
        self.settings = settings
        self.calibration_results = calibration_results
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 标题
        mode_text = "本地视频" if self.settings['mode'] == 'video' else "网络摄像头"
        title = QLabel(f"{mode_text}分析界面")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 视频显示区域
        video_layout = QHBoxLayout()
        
        # 左摄像头
        left_frame = QFrame()
        left_frame.setFrameStyle(QFrame.Shape.Box)
        left_frame.setMinimumSize(320, 240)
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("摄像头1"))
        left_layout.addWidget(QLabel("视频画面占位"))
        left_frame.setLayout(left_layout)
        
        # 右摄像头
        right_frame = QFrame()
        right_frame.setFrameStyle(QFrame.Shape.Box)
        right_frame.setMinimumSize(320, 240)
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("摄像头2"))
        right_layout.addWidget(QLabel("视频画面占位"))
        right_frame.setLayout(right_layout)
        
        video_layout.addWidget(left_frame)
        video_layout.addWidget(right_frame)
        layout.addLayout(video_layout)
        
        # 进度条 (仅视频模式)
        if self.settings['mode'] == 'video':
            progress_layout = QHBoxLayout()
            progress_layout.addWidget(QLabel("进度:"))
            
            self.progress_slider = QSlider(Qt.Orientation.Horizontal)
            self.progress_slider.setRange(0, 100)
            progress_layout.addWidget(self.progress_slider)
            
            self.progress_label = QLabel("00:00 / 00:00")
            progress_layout.addWidget(self.progress_label)
            
            layout.addLayout(progress_layout)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.play_pause_btn = QPushButton("播放/暂停")
        self.reset_btn = QPushButton("重置")
        self.predict_btn = QPushButton("开始预测")
        self.settings_btn = QPushButton("返回设置")
        
        self.play_pause_btn.clicked.connect(self.toggle_playback)
        self.reset_btn.clicked.connect(self.reset_system)
        self.predict_btn.clicked.connect(self.start_prediction)
        self.settings_btn.clicked.connect(self.return_to_settings)
        
        control_layout.addWidget(self.play_pause_btn)
        control_layout.addWidget(self.reset_btn)
        control_layout.addWidget(self.predict_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.settings_btn)
        
        layout.addLayout(control_layout)
        
        # 状态信息
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setPlainText("系统就绪，等待开始...")
        layout.addWidget(self.status_text)
    
    def toggle_playback(self):
        """切换播放/暂停"""
        self.status_text.append("播放/暂停切换")
    
    def reset_system(self):
        """重置系统"""
        self.status_text.append("系统重置")
    
    def start_prediction(self):
        """开始预测"""
        self.status_text.append("开始轨迹预测...")
    
    def return_to_settings(self):
        """返回设置"""
        self.parent().show_settings()


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.current_settings = {}
        self.calibration_results = {}
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("羽毛球落点预测系统 v6.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央widget和堆叠布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # 创建各个界面
        self.mode_selection = ModeSelectionWidget()
        self.mode_selection.mode_selected.connect(self.on_mode_selected)
        self.stacked_widget.addWidget(self.mode_selection)
        
        self.show_mode_selection()
    
    def show_mode_selection(self):
        """显示模式选择界面"""
        self.stacked_widget.setCurrentWidget(self.mode_selection)
    
    def on_mode_selected(self, mode: str):
        """模式选择完成"""
        # 创建设置界面
        self.settings_widget = SettingsWidget(mode)
        self.settings_widget.settings_complete.connect(self.on_settings_complete)
        self.stacked_widget.addWidget(self.settings_widget)
        self.show_settings()
    
    def show_settings(self):
        """显示设置界面"""
        self.stacked_widget.setCurrentWidget(self.settings_widget)
    
    def on_settings_complete(self, settings: dict):
        """设置完成"""
        self.current_settings = settings
        
        # 创建标定界面
        self.calibration_widget = CalibrationWidget(settings)
        self.calibration_widget.calibration_complete.connect(self.on_calibration_complete)
        self.stacked_widget.addWidget(self.calibration_widget)
        self.show_calibration()
    
    def show_calibration(self):
        """显示标定界面"""
        self.stacked_widget.setCurrentWidget(self.calibration_widget)
    
    def on_calibration_complete(self, calibration_results: dict):
        """标定完成"""
        self.calibration_results = calibration_results
        
        # 创建视频播放界面
        self.playback_widget = VideoPlaybackWidget(self.current_settings, calibration_results)
        self.stacked_widget.addWidget(self.playback_widget)
        self.show_playback()
    
    def show_playback(self):
        """显示播放界面"""
        self.stacked_widget.setCurrentWidget(self.playback_widget)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("Shuttlecock Landing Predictor")
    app.setApplicationVersion("6.0")
    app.setOrganizationName("Liao-cyber360")
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())