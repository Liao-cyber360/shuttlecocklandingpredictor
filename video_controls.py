import cv2
import numpy as np
import math


class VideoProgressBar:
    """视频播放进度条组件"""
    
    def __init__(self, width=800, height=40, margin=10):
        self.width = width
        self.height = height
        self.margin = margin
        
        # 进度条颜色
        self.bg_color = (50, 50, 50)        # 背景
        self.track_color = (100, 100, 100)  # 轨道
        self.progress_color = (0, 150, 255) # 进度
        self.handle_color = (255, 255, 255) # 拖拽把手
        self.text_color = (255, 255, 255)   # 文字
        
        # 状态
        self.total_frames = 0
        self.current_frame = 0
        self.fps = 30.0
        self.dragging = False
        self.drag_start_x = 0
        
        # 进度条区域
        self.bar_x = margin
        self.bar_y = margin
        self.bar_width = width - 2 * margin
        self.bar_height = 20
        
        # 把手
        self.handle_radius = 8
        self.handle_x = self.bar_x
        
        print(f"📊 Video progress bar initialized ({width}x{height})")
    
    def set_video_info(self, total_frames, fps):
        """设置视频信息"""
        self.total_frames = total_frames
        self.fps = fps
        print(f"📊 Progress bar updated: {total_frames} frames @ {fps:.1f} FPS")
    
    def update_position(self, current_frame):
        """更新当前播放位置"""
        self.current_frame = max(0, min(current_frame, self.total_frames))
        self._update_handle_position()
    
    def _update_handle_position(self):
        """更新把手位置"""
        if self.total_frames > 0:
            progress = self.current_frame / self.total_frames
            self.handle_x = self.bar_x + progress * self.bar_width
        else:
            self.handle_x = self.bar_x
    
    def handle_mouse_event(self, event, x, y, flags, param):
        """处理鼠标事件"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # 检查是否点击在把手上
            if self._is_point_in_handle(x, y):
                self.dragging = True
                self.drag_start_x = x
                return True
            # 检查是否点击在进度条上
            elif self._is_point_in_bar(x, y):
                self._seek_to_position(x)
                return True
        
        elif event == cv2.EVENT_LBUTTONUP:
            if self.dragging:
                self.dragging = False
                return True
        
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.dragging:
                self._seek_to_position(x)
                return True
        
        return False
    
    def _is_point_in_handle(self, x, y):
        """检查点是否在把手内"""
        handle_y = self.bar_y + self.bar_height // 2
        distance = math.sqrt((x - self.handle_x) ** 2 + (y - handle_y) ** 2)
        return distance <= self.handle_radius + 5  # 增加一些容差
    
    def _is_point_in_bar(self, x, y):
        """检查点是否在进度条内"""
        return (self.bar_x <= x <= self.bar_x + self.bar_width and
                self.bar_y <= y <= self.bar_y + self.bar_height)
    
    def _seek_to_position(self, x):
        """根据鼠标位置设置播放位置"""
        if self.total_frames <= 0:
            return
        
        # 计算相对位置
        relative_x = max(0, min(x - self.bar_x, self.bar_width))
        progress = relative_x / self.bar_width
        
        # 更新帧位置
        self.current_frame = int(progress * self.total_frames)
        self._update_handle_position()
    
    def get_current_frame(self):
        """获取当前帧位置"""
        return self.current_frame
    
    def get_current_time(self):
        """获取当前时间位置（秒）"""
        if self.fps > 0:
            return self.current_frame / self.fps
        return 0
    
    def render(self):
        """渲染进度条"""
        # 创建进度条图像
        img = np.full((self.height, self.width, 3), self.bg_color, dtype=np.uint8)
        
        # 绘制进度条轨道
        cv2.rectangle(img, 
                     (self.bar_x, self.bar_y),
                     (self.bar_x + self.bar_width, self.bar_y + self.bar_height),
                     self.track_color, -1)
        
        # 绘制已播放部分
        if self.total_frames > 0:
            progress_width = int((self.current_frame / self.total_frames) * self.bar_width)
            if progress_width > 0:
                cv2.rectangle(img,
                             (self.bar_x, self.bar_y),
                             (self.bar_x + progress_width, self.bar_y + self.bar_height),
                             self.progress_color, -1)
        
        # 绘制把手
        handle_y = self.bar_y + self.bar_height // 2
        cv2.circle(img, (int(self.handle_x), handle_y), self.handle_radius, 
                   self.handle_color, -1)
        cv2.circle(img, (int(self.handle_x), handle_y), self.handle_radius, 
                   (0, 0, 0), 1)  # 黑色边框
        
        # 绘制时间信息
        current_time = self.get_current_time()
        total_time = self.total_frames / self.fps if self.fps > 0 else 0
        
        time_text = f"{self._format_time(current_time)} / {self._format_time(total_time)}"
        text_size = cv2.getTextSize(time_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        
        # 时间显示在右上角
        text_x = self.width - text_size[0] - self.margin
        text_y = self.bar_y + self.bar_height + 20
        
        cv2.putText(img, time_text, (text_x, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.text_color, 2)
        
        # 帧信息显示在左上角
        frame_text = f"Frame: {self.current_frame} / {self.total_frames}"
        cv2.putText(img, frame_text, (self.margin, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.text_color, 2)
        
        return img
    
    def _format_time(self, seconds):
        """格式化时间显示"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"


class EnhancedVideoControls:
    """增强的视频控制组件"""
    
    def __init__(self, video_width=1280):
        self.video_width = video_width
        self.progress_bar = VideoProgressBar(width=video_width-20, height=60)
        self.mouse_callback_set = False
        
        # 播放控制状态
        self.playing = True
        self.playback_speed = 1.0
        self.seek_requested = False
        self.seek_frame = 0
        
        print(f"🎮 Enhanced video controls initialized")
    
    def set_video_info(self, total_frames, fps):
        """设置视频信息"""
        self.progress_bar.set_video_info(total_frames, fps)
    
    def update_position(self, current_frame):
        """更新播放位置"""
        self.progress_bar.update_position(current_frame)
    
    def mouse_callback(self, event, x, y, flags, param):
        """鼠标回调函数"""
        # 调整坐标到进度条区域
        if y > self.video_width // 2:  # 进度条在视频下方
            progress_y = y - self.video_width // 2
            if self.progress_bar.handle_mouse_event(event, x, progress_y, flags, param):
                # 如果进度条处理了事件，检查是否需要跳转
                if event == cv2.EVENT_LBUTTONUP and not self.progress_bar.dragging:
                    self.seek_requested = True
                    self.seek_frame = self.progress_bar.get_current_frame()
    
    def is_seek_requested(self):
        """检查是否有跳转请求"""
        if self.seek_requested:
            self.seek_requested = False
            return True, self.seek_frame
        return False, 0
    
    def render_with_video(self, video_frame):
        """将进度条与视频帧组合渲染"""
        if video_frame is None:
            return None
        
        # 渲染进度条
        progress_img = self.progress_bar.render()
        
        # 调整视频帧大小以匹配控制面板宽度
        video_height, video_width = video_frame.shape[:2]
        target_width = self.video_width
        target_height = int(video_height * target_width / video_width)
        
        video_resized = cv2.resize(video_frame, (target_width, target_height))
        
        # 垂直组合视频和控制面板
        combined_height = target_height + progress_img.shape[0]
        combined = np.zeros((combined_height, target_width, 3), dtype=np.uint8)
        
        # 放置视频
        combined[:target_height, :target_width] = video_resized
        
        # 放置进度条
        progress_height = progress_img.shape[0]
        combined[target_height:target_height + progress_height, :target_width] = progress_img
        
        return combined
    
    def set_mouse_callback(self, window_name):
        """设置鼠标回调"""
        if not self.mouse_callback_set:
            cv2.setMouseCallback(window_name, self.mouse_callback)
            self.mouse_callback_set = True