import cv2
import numpy as np
import requests
import threading
import time
from datetime import datetime
from collections import deque
import queue


class MJPEGStreamReader:
    """MJPEG网络摄像头流读取器"""
    
    def __init__(self, camera_url, timestamp_header="X-Timestamp", buffer_size=30):
        self.camera_url = camera_url
        self.timestamp_header = timestamp_header
        self.buffer_size = buffer_size
        
        # 帧缓冲区
        self.frame_buffer = deque(maxlen=buffer_size)
        self.timestamp_buffer = deque(maxlen=buffer_size)
        
        # 控制变量
        self.running = False
        self.paused = False
        self.thread = None
        
        # 统计信息
        self.frame_count = 0
        self.fps = 0
        self.last_timestamp = ""
        self.last_time = datetime.now()
        
        print(f"📹 MJPEG Stream Reader initialized")
        print(f"   Camera URL: {camera_url}")
        print(f"   Timestamp header: {timestamp_header}")
        print(f"   Buffer size: {buffer_size} frames")
    
    def start(self):
        """开始读取流"""
        if self.running:
            print("⚠️ Stream already running")
            return False
            
        self.running = True
        self.thread = threading.Thread(target=self._stream_worker, daemon=True)
        self.thread.start()
        print("✅ MJPEG stream started")
        return True
    
    def stop(self):
        """停止读取流"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        print("✅ MJPEG stream stopped")
    
    def pause(self):
        """暂停/恢复缓冲"""
        self.paused = not self.paused
        status = "paused" if self.paused else "resumed"
        print(f"📹 Stream buffering {status}")
    
    def get_latest_frame(self):
        """获取最新帧"""
        if not self.frame_buffer:
            return None, None
        return self.frame_buffer[-1], self.timestamp_buffer[-1]
    
    def get_buffered_frames(self):
        """获取所有缓冲的帧"""
        return list(self.frame_buffer), list(self.timestamp_buffer)
    
    def clear_buffer(self):
        """清空缓冲区"""
        self.frame_buffer.clear()
        self.timestamp_buffer.clear()
        print("🗑️ Stream buffer cleared")
    
    def get_buffer_info(self):
        """获取缓冲区信息"""
        return {
            'buffer_size': len(self.frame_buffer),
            'max_size': self.buffer_size,
            'fps': self.fps,
            'frame_count': self.frame_count,
            'last_timestamp': self.last_timestamp,
            'running': self.running,
            'paused': self.paused
        }
    
    def _stream_worker(self):
        """流读取工作线程"""
        try:
            print(f"🔗 Connecting to {self.camera_url}")
            
            # 设置请求头
            headers = {
                'User-Agent': 'BadmintonSystem/1.0',
                'Accept': 'multipart/x-mixed-replace,*/*'
            }
            
            # 开始流式请求
            response = requests.get(self.camera_url, headers=headers, stream=True, timeout=10)
            response.raise_for_status()
            
            print(f"✅ Connected to camera stream (Status: {response.status_code})")
            
            # 解析multipart boundary
            content_type = response.headers.get('Content-Type', '')
            boundary = self._extract_boundary(content_type)
            if not boundary:
                raise ValueError("Could not find multipart boundary")
            
            print(f"📦 Multipart boundary: {boundary}")
            
            # 读取流数据
            buffer = b''
            while self.running:
                try:
                    # 读取数据块
                    chunk = response.raw.read(8192)
                    if not chunk:
                        print("⚠️ Stream ended")
                        break
                    
                    buffer += chunk
                    
                    # 处理完整的帧
                    while True:
                        frame_start = buffer.find(b'--' + boundary.encode())
                        if frame_start == -1:
                            break
                        
                        # 寻找下一个boundary或数据结束
                        next_boundary = buffer.find(b'--' + boundary.encode(), frame_start + len(boundary) + 2)
                        if next_boundary == -1:
                            break
                        
                        # 提取一个完整的帧数据
                        frame_data = buffer[frame_start:next_boundary]
                        buffer = buffer[next_boundary:]
                        
                        # 解析并处理帧
                        self._process_frame_data(frame_data, response.headers)
                
                except Exception as e:
                    print(f"❌ Error reading stream: {e}")
                    time.sleep(1)  # 短暂等待后重试
                    
        except Exception as e:
            print(f"❌ Stream worker error: {e}")
        finally:
            print("🔌 Stream worker stopped")
    
    def _extract_boundary(self, content_type):
        """从Content-Type头中提取boundary"""
        if 'boundary=' in content_type:
            return content_type.split('boundary=')[1].split(';')[0].strip()
        return None
    
    def _process_frame_data(self, frame_data, headers):
        """处理单个帧数据"""
        try:
            # 查找JPEG数据开始位置
            jpeg_start = frame_data.find(b'\xff\xd8')  # JPEG文件头
            if jpeg_start == -1:
                return
            
            # 查找JPEG数据结束位置
            jpeg_end = frame_data.find(b'\xff\xd9', jpeg_start)  # JPEG文件尾
            if jpeg_end == -1:
                return
            
            # 提取JPEG数据
            jpeg_data = frame_data[jpeg_start:jpeg_end + 2]
            
            # 解码图像
            nparr = np.frombuffer(jpeg_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return
            
            # 更新统计信息
            self.update(headers)
            
            # 如果未暂停，添加到缓冲区
            if not self.paused:
                current_time = time.time()
                self.frame_buffer.append(frame.copy())
                self.timestamp_buffer.append(current_time)
            
        except Exception as e:
            print(f"⚠️ Error processing frame: {e}")
    
    def update(self, headers):
        """更新帧统计信息"""
        self.frame_count += 1
        
        # 计算实时FPS（每秒更新）
        current_time = datetime.now()
        if (current_time - self.last_time).total_seconds() >= 1:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_time = current_time
        
        # 解析时间戳
        ts_str = headers.get(self.timestamp_header, "")
        if ts_str and ts_str.isdigit():
            ts_ms = int(ts_str)
            self.last_timestamp = datetime.fromtimestamp(ts_ms / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]


class NetworkCameraManager:
    """网络摄像头管理器 - 支持双摄像头"""
    
    def __init__(self, camera_url1, camera_url2=None, timestamp_header="X-Timestamp"):
        self.camera_url1 = camera_url1
        self.camera_url2 = camera_url2
        self.timestamp_header = timestamp_header
        
        # 摄像头流读取器
        self.stream1 = MJPEGStreamReader(camera_url1, timestamp_header)
        self.stream2 = MJPEGStreamReader(camera_url2, timestamp_header) if camera_url2 else None
        
        print(f"🎥 Network Camera Manager initialized")
        print(f"   Camera 1: {camera_url1}")
        if camera_url2:
            print(f"   Camera 2: {camera_url2}")
        else:
            print(f"   Camera 2: Not configured (single camera mode)")
    
    def start(self):
        """启动所有摄像头流"""
        success1 = self.stream1.start()
        success2 = True
        
        if self.stream2:
            success2 = self.stream2.start()
        
        if success1 and success2:
            print("✅ All camera streams started successfully")
            return True
        else:
            print("❌ Failed to start one or more camera streams")
            return False
    
    def stop(self):
        """停止所有摄像头流"""
        self.stream1.stop()
        if self.stream2:
            self.stream2.stop()
        print("✅ All camera streams stopped")
    
    def pause(self):
        """暂停/恢复所有摄像头缓冲"""
        self.stream1.pause()
        if self.stream2:
            self.stream2.pause()
    
    def read(self):
        """读取最新帧 - 兼容cv2.VideoCapture接口"""
        frame1, ts1 = self.stream1.get_latest_frame()
        
        if self.stream2:
            frame2, ts2 = self.stream2.get_latest_frame()
            return (frame1 is not None, frame2 is not None), (frame1, frame2)
        else:
            # 单摄像头模式，返回相同帧
            return (frame1 is not None, frame1 is not None), (frame1, frame1)
    
    def get_buffered_frames(self):
        """获取所有缓冲的帧"""
        frames1, ts1 = self.stream1.get_buffered_frames()
        
        if self.stream2:
            frames2, ts2 = self.stream2.get_buffered_frames()
            return frames1, frames2, ts1, ts2
        else:
            return frames1, frames1, ts1, ts1
    
    def clear_buffer(self):
        """清空所有缓冲区"""
        self.stream1.clear_buffer()
        if self.stream2:
            self.stream2.clear_buffer()
    
    def get_fps(self):
        """获取FPS信息"""
        fps1 = self.stream1.get_buffer_info()['fps']
        if self.stream2:
            fps2 = self.stream2.get_buffer_info()['fps']
            return min(fps1, fps2) if fps1 > 0 and fps2 > 0 else max(fps1, fps2)
        return fps1
    
    def get_status(self):
        """获取状态信息"""
        info1 = self.stream1.get_buffer_info()
        status = {
            'camera1': info1,
            'camera2': None,
            'fps': info1['fps'],
            'total_frames': info1['frame_count']
        }
        
        if self.stream2:
            info2 = self.stream2.get_buffer_info()
            status['camera2'] = info2
            status['fps'] = min(info1['fps'], info2['fps']) if info1['fps'] > 0 and info2['fps'] > 0 else max(info1['fps'], info2['fps'])
            status['total_frames'] = min(info1['frame_count'], info2['frame_count'])
        
        return status
    
    def isOpened(self):
        """检查摄像头是否正常工作 - 兼容cv2.VideoCapture接口"""
        status1 = self.stream1.get_buffer_info()['running']
        if self.stream2:
            status2 = self.stream2.get_buffer_info()['running']
            return status1 and status2
        return status1
    
    def release(self):
        """释放资源 - 兼容cv2.VideoCapture接口"""
        self.stop()