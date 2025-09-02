#!/usr/bin/env python3
"""
系统适配器 - 将原始BufferedBadmintonSystem适配为支持PyQt6的版本
System Adapter - Adapts the original BufferedBadmintonSystem for PyQt6 integration
"""

import time
import threading
from typing import Optional, Callable, Dict, Any
import numpy as np

from main import BufferedBadmintonSystem, SystemState


class SystemAdapter:
    """
    系统适配器类
    将原始的BufferedBadmintonSystem包装为支持回调和事件驱动的版本
    """
    
    def __init__(self):
        self.system = BufferedBadmintonSystem()
        self.running = False
        self.processing_thread = None
        
        # 回调函数
        self.frame_callback: Optional[Callable[[np.ndarray], None]] = None
        self.status_callback: Optional[Callable[[str], None]] = None
        self.prediction_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self.error_callback: Optional[Callable[[str], None]] = None
        
        # 替换原始系统的键盘处理
        self._override_keyboard_handling()
        
    def _override_keyboard_handling(self):
        """覆盖原始系统的键盘处理逻辑"""
        # 保存原始方法
        self.system._original_handle_keyboard_input = self.system._handle_keyboard_input
        
        # 替换为空的处理方法（GUI会处理这些事件）
        def dummy_keyboard_handler(key, current_time):
            pass  # 不做任何事情，因为GUI会处理所有输入
            
        self.system._handle_keyboard_input = dummy_keyboard_handler
    
    def set_frame_callback(self, callback: Callable[[np.ndarray], None]):
        """设置帧回调函数"""
        self.frame_callback = callback
    
    def set_status_callback(self, callback: Callable[[str], None]):
        """设置状态回调函数"""
        self.status_callback = callback
    
    def set_prediction_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """设置预测回调函数"""
        self.prediction_callback = callback
    
    def set_error_callback(self, callback: Callable[[str], None]):
        """设置错误回调函数"""
        self.error_callback = callback
    
    def initialize_video_system(self, video1_path: str, video2_path: str) -> bool:
        """初始化视频系统"""
        try:
            result = self.system.initialize_system(video1_path, video2_path)
            if self.status_callback:
                self.status_callback("视频系统初始化完成")
            return result
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"视频系统初始化失败: {e}")
            return False
    
    def initialize_network_cameras(self, url1: str, url2: str, timestamp_header: str) -> bool:
        """初始化网络摄像头系统"""
        try:
            result = self.system.initialize_network_cameras(url1, url2, timestamp_header)
            if self.status_callback:
                self.status_callback("网络摄像头系统初始化完成")
            return result
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"网络摄像头系统初始化失败: {e}")
            return False
    
    def start_processing(self):
        """开始处理"""
        if self.running:
            return
            
        self.running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        if self.status_callback:
            self.status_callback("系统处理已开始")
    
    def stop_processing(self):
        """停止处理"""
        self.running = False
        if hasattr(self.system, 'running'):
            self.system.running = False
            
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=3.0)
            
        if self.status_callback:
            self.status_callback("系统处理已停止")
    
    def _processing_loop(self):
        """处理循环 - 在独立线程中运行"""
        try:
            # 使用修改后的处理逻辑，避免直接调用原始的start_processing
            self._run_modified_processing_loop()
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"处理循环错误: {e}")
    
    def _run_modified_processing_loop(self):
        """修改后的处理循环，集成GUI回调"""
        frame_count = 0
        last_fps_time = time.time()
        fps_counter = 0
        
        while self.running and hasattr(self.system, 'running') and self.system.running:
            try:
                # 获取当前帧（模拟原始系统的帧获取逻辑）
                current_frame = self._get_current_frame()
                
                if current_frame is not None and self.frame_callback:
                    self.frame_callback(current_frame)
                
                # 更新FPS计算
                fps_counter += 1
                current_time = time.time()
                if current_time - last_fps_time >= 1.0:
                    actual_fps = fps_counter
                    fps_counter = 0
                    last_fps_time = current_time
                    
                    if self.status_callback:
                        self.status_callback(f"FPS: {actual_fps:.1f} | 帧数: {frame_count}")
                
                frame_count += 1
                
                # 控制帧率
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                if self.error_callback:
                    self.error_callback(f"帧处理错误: {e}")
                time.sleep(0.1)
    
    def _get_current_frame(self) -> Optional[np.ndarray]:
        """获取当前帧（从原始系统）"""
        try:
            # 这里需要从原始系统获取当前帧
            # 由于原始系统的复杂性，我们先返回一个占位符
            if hasattr(self.system, 'current_frame1') and self.system.current_frame1 is not None:
                return self.system.current_frame1
            else:
                # 创建一个占位符帧
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                placeholder[200:280, 270:370] = [100, 100, 100]  # 灰色矩形
                return placeholder
        except Exception:
            return None
    
    # GUI控制方法
    def pause_system(self):
        """暂停系统"""
        self.system.paused = True
        if self.status_callback:
            self.status_callback("系统已暂停")
    
    def resume_system(self):
        """恢复系统"""
        self.system.paused = False
        if self.status_callback:
            self.status_callback("系统已恢复")
    
    def trigger_prediction(self):
        """触发预测"""
        try:
            if hasattr(self.system, '_handle_prediction_trigger'):
                self.system._handle_prediction_trigger(time.time())
                if self.status_callback:
                    self.status_callback("预测已触发")
            else:
                if self.error_callback:
                    self.error_callback("预测功能不可用")
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"预测触发失败: {e}")
    
    def reset_system(self):
        """重置系统"""
        try:
            if hasattr(self.system, '_handle_system_reset'):
                self.system._handle_system_reset()
                if self.status_callback:
                    self.status_callback("系统已重置")
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"系统重置失败: {e}")
    
    def set_playback_speed(self, speed: float):
        """设置播放速度"""
        try:
            self.system.playback_speed = max(0.1, min(5.0, speed))
            if self.status_callback:
                self.status_callback(f"播放速度: {speed:.1f}x")
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"设置播放速度失败: {e}")
    
    def toggle_3d_visualization(self):
        """切换3D可视化"""
        try:
            if hasattr(self.system, '_handle_toggle_3d_visualization'):
                self.system._handle_toggle_3d_visualization()
                if self.status_callback:
                    self.status_callback("3D可视化已切换")
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"3D可视化切换失败: {e}")
    
    def close_3d_visualization(self):
        """关闭3D可视化"""
        try:
            if hasattr(self.system, '_handle_close_3d_window'):
                self.system._handle_close_3d_window()
                if self.status_callback:
                    self.status_callback("3D可视化已关闭")
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"关闭3D可视化失败: {e}")
    
    def toggle_3d_element(self, element_type: str):
        """切换3D元素显示"""
        try:
            if (hasattr(self.system, 'interactive_3d_viz') and 
                self.system.interactive_3d_viz and
                hasattr(self.system.interactive_3d_viz, 'toggle_visualization_elements')):
                self.system.interactive_3d_viz.toggle_visualization_elements(element_type)
                if self.status_callback:
                    self.status_callback(f"3D元素 {element_type} 已切换")
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"3D元素切换失败: {e}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            info = {
                "state": getattr(self.system, 'state', SystemState.BUFFERING).value,
                "paused": getattr(self.system, 'paused', False),
                "frame_count": getattr(self.system, 'frame_count', 0),
                "actual_fps": getattr(self.system, 'actual_fps', 0),
                "total_predictions": getattr(self.system, 'total_predictions', 0),
                "successful_predictions": getattr(self.system, 'successful_predictions', 0),
                "playback_speed": getattr(self.system, 'playback_speed', 1.0),
                "3d_window_visible": False
            }
            
            # 检查3D窗口状态
            if (hasattr(self.system, 'interactive_3d_viz') and 
                self.system.interactive_3d_viz and
                hasattr(self.system.interactive_3d_viz, 'window_visible')):
                info["3d_window_visible"] = self.system.interactive_3d_viz.window_visible
            
            return info
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"获取系统信息失败: {e}")
            return {}
    
    def cleanup(self):
        """清理资源"""
        self.stop_processing()
        
        try:
            if hasattr(self.system, '_cleanup'):
                self.system._cleanup()
        except Exception as e:
            if self.error_callback:
                self.error_callback(f"清理失败: {e}")