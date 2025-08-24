import cv2
import numpy as np
import threading
import time
import requests
from datetime import datetime
from collections import deque
import queue
from io import BytesIO


class MJPEGStreamReader:
    """MJPEG网络摄像头流读取器 - 增强版"""

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

        # 连接配置
        self.reconnect_delay = 5
        self.timeout = (10, 30)  # (连接超时, 读取超时)
        self.max_retries = 3

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

    def _create_robust_session(self):
        """创建具有重试机制的HTTP会话"""
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _process_frame_data(self, data):
        """处理帧数据并解码为图像"""
        try:
            # 使用BytesIO处理二进制数据
            img_data = BytesIO(data)
            img_data.seek(0)
            frame = cv2.imdecode(np.frombuffer(img_data.read(), np.uint8), cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            print(f"解码错误: {e}")
            return None

    def _stream_worker(self):
        """流读取工作线程 - 使用您的健壮方法"""
        while self.running:
            session = self._create_robust_session()
            response = None

            try:
                print(f"🔗 Connecting to {self.camera_url}")

                # 设置请求头
                headers = {
                    'User-Agent': 'BadmintonSystem/1.0',
                    'Accept': 'multipart/x-mixed-replace,*/*'
                }

                response = session.get(self.camera_url, headers=headers, stream=True, timeout=self.timeout)

                if response.status_code != 200:
                    print(f"❌ Connection failed, status code: {response.status_code}")
                    raise ConnectionError("摄像头连接失败")

                # 获取内容类型和边界
                content_type = response.headers.get('Content-Type', '')
                if 'multipart/x-mixed-replace' not in content_type:
                    print("❌ Error: 不是MJPEG流")
                    raise ValueError("不是MJPEG流")

                boundary = content_type.split('boundary=')[-1].strip()
                if not boundary:
                    print("❌ 无法确定边界分隔符")
                    raise ValueError("边界分隔符无效")

                print(f"✅ Connected to camera stream (Status: {response.status_code})")
                print(f"   Boundary: {boundary}")

                # 使用您的健壮解析方法
                self._parse_mjpeg_stream(response, boundary)

            except KeyboardInterrupt:
                print("⚠️ Stream worker interrupted by user")
                break
            except Exception as e:
                print(f"❌ Stream error: {e}")
                if not self.running:
                    break

            finally:
                if response is not None:
                    response.close()
                session.close()

            if self.running:
                print(f"🔄 Waiting {self.reconnect_delay} seconds before reconnection...")
                time.sleep(self.reconnect_delay)

        print("🔌 Stream worker stopped")

    def _parse_mjpeg_stream(self, response, boundary):
        """解析MJPEG流 - 使用您的方法"""
        buffer = b''
        in_frame = False
        headers = {}

        for chunk in response.iter_content(chunk_size=4096):
            if not self.running:
                break

            if not chunk:
                continue

            buffer += chunk

            while True:
                if not in_frame:
                    # 查找边界标记
                    boundary_pos = buffer.find(b'--' + boundary.encode())
                    if boundary_pos == -1:
                        break

                    # 跳过边界标记
                    buffer = buffer[boundary_pos + len(boundary) + 2:]
                    in_frame = True
                    headers = {}

                # 查找头部结束标记
                header_end = buffer.find(b'\r\n\r\n')
                if header_end == -1:
                    break

                # 解析头部
                header_data = buffer[:header_end].decode('ascii', errors='ignore')
                for line in header_data.split('\r\n'):
                    if ':' in line:
                        key, val = line.split(':', 1)
                        headers[key.strip()] = val.strip()

                # 查找帧结束标记
                frame_end = buffer.find(b'--' + boundary.encode(), header_end + 4)
                if frame_end == -1:
                    break

                # 提取帧数据
                frame_data = buffer[header_end + 4:frame_end]
                buffer = buffer[frame_end:]
                in_frame = False

                # 处理帧
                if not self.paused:
                    self._process_frame(frame_data, headers)

    def _process_frame(self, frame_data, headers):
        """处理单个帧"""
        frame = self._process_frame_data(frame_data)

        if frame is not None:
            # 更新统计信息
            self.frame_count += 1
            current_time = datetime.now()

            # 计算FPS（每秒更新）
            if (current_time - self.last_time).total_seconds() >= 1:
                self.fps = self.frame_count
                self.frame_count = 0
                self.last_time = current_time

            # 解析时间戳
            ts_str = headers.get(self.timestamp_header, "")
            if ts_str and ts_str.isdigit():
                ts_ms = int(ts_str)
                timestamp = datetime.fromtimestamp(ts_ms / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            else:
                timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

            self.last_timestamp = timestamp

            # 存储到缓冲区
            self.frame_buffer.append(frame)
            self.timestamp_buffer.append(timestamp)


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

    # 添加这个方法来兼容cv2.VideoCapture接口
    def isOpened(self):
        """检查摄像头是否已打开并连接 - 兼容cv2.VideoCapture接口"""
        if not self.stream1:
            return False

        stream1_info = self.stream1.get_buffer_info()
        stream1_running = stream1_info['running']

        if self.stream2:
            stream2_info = self.stream2.get_buffer_info()
            stream2_running = stream2_info['running']
            return stream1_running and stream2_running
        else:
            return stream1_running

    def is_connected(self):
        """检查连接状态 - 别名方法"""
        return self.isOpened()

    # 其他现有方法保持不变...
    def start(self):
        """启动所有摄像头流"""
        print("🚀 Starting camera streams...")

        success1 = self.stream1.start()
        if success1:
            print("⏳ Waiting for stream1 to stabilize...")
            time.sleep(2)

        success2 = True
        if self.stream2:
            success2 = self.stream2.start()
            if success2:
                print("⏳ Waiting for stream2 to stabilize...")
                time.sleep(2)

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

    def read(self):
        """读取最新帧 - 兼容cv2.VideoCapture接口"""
        frame1, ts1 = self.stream1.get_latest_frame()

        if self.stream2:
            frame2, ts2 = self.stream2.get_latest_frame()
            return (frame1 is not None, frame2 is not None), (frame1, frame2)
        else:
            return (frame1 is not None, frame1 is not None), (frame1, frame1)

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
            status['fps'] = min(info1['fps'], info2['fps']) if info1['fps'] > 0 and info2['fps'] > 0 else max(
                info1['fps'], info2['fps'])
            status['total_frames'] = min(info1['frame_count'], info2['frame_count'])

        return status

    def is_connected(self):
        """检查连接状态"""
        connected1 = self.stream1.get_buffer_info()['running']
        if self.stream2:
            connected2 = self.stream2.get_buffer_info()['running']
            return connected1 and connected2
        return connected1

 # 保持向后兼容性
def create_network_camera_manager(camera_url1, camera_url2=None, timestamp_header="X-Timestamp"):
        """工厂函数 - 创建网络摄像头管理器"""
        return NetworkCameraManager(camera_url1, camera_url2, timestamp_header)

    # 测试功能
if __name__ == "__main__":
        import sys

        if len(sys.argv) < 2:
            print("Usage: python network_camera.py <camera_url>")
            print("Example: python network_camera.py http://192.168.10.8:8080/video")
            sys.exit(1)

        camera_url = sys.argv[1]
        print(f"🧪 Testing camera connection: {camera_url}")

        manager = NetworkCameraManager(camera_url)

        try:
            if manager.start():
                print("⏳ Waiting for frames...")
                time.sleep(5)

                ret, frames = manager.read()
                if ret[0] and frames[0] is not None:
                    print("✅ Successfully received frames")
                    print(f"   Frame shape: {frames[0].shape}")
                    print(f"   FPS: {manager.get_fps()}")
                else:
                    print("❌ No frames received")
            else:
                print("❌ Failed to start camera")

        except KeyboardInterrupt:
            print("\n⚠️ Test interrupted")
        finally:
            manager.stop()
            print("🧹 Cleanup completed")
