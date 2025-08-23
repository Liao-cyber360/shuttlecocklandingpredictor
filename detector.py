import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque
import time
import threading
from utils import config


class MultiObjectTracker:
    """多目标跟踪器 - 用于处理多个羽毛球"""
    
    def __init__(self, max_objects=2, distance_threshold=100):
        self.max_objects = max_objects
        self.distance_threshold = distance_threshold
        self.tracks = {}  # track_id -> track_info
        self.next_track_id = 0
        self.max_missing_frames = 10
        
        print(f"🎯 Multi-object tracker initialized (max_objects={max_objects})")
    
    def update(self, detections, timestamp):
        """更新跟踪器"""
        # 标记所有现有轨迹为丢失
        for track_id in self.tracks:
            self.tracks[track_id]['missing_frames'] += 1
        
        # 将检测结果分配给现有轨迹或创建新轨迹
        for detection in detections:
            pos, conf = detection
            best_track_id = self._find_best_match(pos)
            
            if best_track_id is not None:
                # 更新现有轨迹
                self._update_track(best_track_id, pos, conf, timestamp)
            elif len(self.tracks) < self.max_objects:
                # 创建新轨迹
                self._create_track(pos, conf, timestamp)
        
        # 移除长时间丢失的轨迹
        self._remove_lost_tracks()
        
        return list(self.tracks.keys())
    
    def _find_best_match(self, pos):
        """找到最佳匹配的轨迹"""
        best_track_id = None
        min_distance = float('inf')
        
        for track_id, track in self.tracks.items():
            if len(track['positions']) > 0:
                last_pos = track['positions'][-1]
                distance = np.linalg.norm(np.array(pos) - np.array(last_pos))
                
                if distance < self.distance_threshold and distance < min_distance:
                    min_distance = distance
                    best_track_id = track_id
        
        return best_track_id
    
    def _create_track(self, pos, conf, timestamp):
        """创建新轨迹"""
        track_id = self.next_track_id
        self.next_track_id += 1
        
        self.tracks[track_id] = {
            'positions': [pos],
            'confidences': [conf],
            'timestamps': [timestamp],
            'missing_frames': 0,
            'created_at': timestamp
        }
        
        print(f"🆕 Created new track {track_id} at position {pos}")
    
    def _update_track(self, track_id, pos, conf, timestamp):
        """更新轨迹"""
        track = self.tracks[track_id]
        track['positions'].append(pos)
        track['confidences'].append(conf)
        track['timestamps'].append(timestamp)
        track['missing_frames'] = 0
        
        # 限制轨迹长度
        max_history = 50
        if len(track['positions']) > max_history:
            track['positions'] = track['positions'][-max_history:]
            track['confidences'] = track['confidences'][-max_history:]
            track['timestamps'] = track['timestamps'][-max_history:]
    
    def _remove_lost_tracks(self):
        """移除丢失的轨迹"""
        to_remove = []
        for track_id, track in self.tracks.items():
            if track['missing_frames'] > self.max_missing_frames:
                to_remove.append(track_id)
        
        for track_id in to_remove:
            print(f"🗑️ Removing lost track {track_id}")
            del self.tracks[track_id]
    
    def get_tracks(self):
        """获取所有活跃轨迹"""
        return self.tracks
    
    def get_best_track(self):
        """获取最佳轨迹（最长且最近活跃）"""
        if not self.tracks:
            return None, None
        
        best_track_id = None
        best_score = -1
        
        for track_id, track in self.tracks.items():
            # 评分标准：轨迹长度 + 最近活跃程度 + 平均置信度
            length_score = len(track['positions'])
            recency_score = max(0, 10 - track['missing_frames'])
            confidence_score = np.mean(track['confidences']) if track['confidences'] else 0
            
            total_score = length_score + recency_score + confidence_score * 10
            
            if total_score > best_score:
                best_score = total_score
                best_track_id = track_id
        
        if best_track_id is not None:
            return best_track_id, self.tracks[best_track_id]
        return None, None


class TrajectoryQualityEvaluator:
    """轨迹质量评估器"""

    def __init__(self):
        # 评估权重
        self.physics_weight = 0.3
        self.continuity_weight = 0.25
        self.completeness_weight = 0.25
        self.temporal_weight = 0.2

        # 物理模型参数
        self.gravity = 9.8 * 100  # cm/s²
        self.min_trajectory_length = 8  # 最少轨迹点数
        self.max_speed_change = 1000  # 最大速度变化 cm/s

    def evaluate_trajectory_segment(self, points_3d, timestamps, current_time):
        """评估轨迹片段质量"""
        if len(points_3d) < 3:
            return 0.0

        # 转换为numpy数组
        points = np.array(points_3d)
        times = np.array(timestamps)

        # 计算各项得分
        physics_score = self._evaluate_physics(points, times)
        continuity_score = self._evaluate_continuity(points, times)
        completeness_score = self._evaluate_completeness(points, times)
        temporal_score = self._evaluate_temporal_weight(times, current_time)

        # 综合得分
        total_score = (
                physics_score * self.physics_weight +
                continuity_score * self.continuity_weight +
                completeness_score * self.completeness_weight +
                temporal_score * self.temporal_weight
        )

        return total_score

    def _evaluate_physics(self, points, times):
        """评估物理合理性"""
        if len(points) < 3:
            return 0.0

        try:
            # 计算速度
            velocities = []
            for i in range(1, len(points)):
                dt = times[i] - times[i - 1]
                if dt > 0:
                    vel = (points[i] - points[i - 1]) / dt
                    velocities.append(vel)

            if len(velocities) < 2:
                return 0.0

            velocities = np.array(velocities)

            # 1. 检查Z方向是否有下降趋势
            z_velocities = velocities[:, 2]
            has_downward_trend = np.mean(z_velocities) < -50  # 平均向下速度 > 50 cm/s

            # 2. 检查速度变化的平滑性
            speed_changes = []
            for i in range(1, len(velocities)):
                speed_change = np.linalg.norm(velocities[i] - velocities[i - 1])
                speed_changes.append(speed_change)

            avg_speed_change = np.mean(speed_changes) if speed_changes else 0
            smooth_score = max(0, 1 - avg_speed_change / self.max_speed_change)

            # 3. 检查轨迹形状是否接近抛物线
            # 简化检查：Z坐标随时间的二次拟合
            try:
                z_coords = points[:, 2]
                time_relative = times - times[0]
                poly_coeffs = np.polyfit(time_relative, z_coords, 2)
                poly_fit = np.polyval(poly_coeffs, time_relative)
                fit_error = np.mean(np.abs(z_coords - poly_fit))
                parabola_score = max(0, 1 - fit_error / 100)  # 误差小于10cm得满分
            except:
                parabola_score = 0.5

            # 综合物理得分
            physics_score = (
                    (1.0 if has_downward_trend else 0.3) * 0.4 +
                    smooth_score * 0.3 +
                    parabola_score * 0.3
            )

            return min(1.0, physics_score)

        except Exception as e:
            return 0.0

    def _evaluate_continuity(self, points, times):
        """评估连续性"""
        if len(points) < 2:
            return 0.0

        # 时间间隔的一致性
        time_intervals = np.diff(times)
        expected_interval = 1.0 / 30.0  # 30fps

        # 计算时间间隔的标准差
        interval_std = np.std(time_intervals)
        time_consistency = max(0, 1 - interval_std / expected_interval)

        # 空间距离的合理性
        distances = []
        for i in range(1, len(points)):
            dist = np.linalg.norm(points[i] - points[i - 1])
            distances.append(dist)

        avg_distance = np.mean(distances) if distances else 0
        # 合理的帧间距离应该在1-50cm之间
        distance_score = 1.0 if 1 <= avg_distance <= 50 else max(0, 1 - abs(avg_distance - 25) / 100)

        # 综合连续性得分
        continuity_score = (time_consistency * 0.6 + distance_score * 0.4)

        return continuity_score

    def _evaluate_completeness(self, points, times):
        """评估完整性"""
        if len(points) < self.min_trajectory_length:
            length_score = len(points) / self.min_trajectory_length
        else:
            length_score = 1.0

        # 检查是否包含足够的下降段
        z_coords = points[:, 2]
        z_range = np.max(z_coords) - np.min(z_coords)
        height_score = min(1.0, z_range / 100)  # 1米高度差得满分

        # 检查是否接近地面
        min_height = np.min(z_coords)
        ground_proximity = max(0, 1 - min_height / 200)  # 2米以下开始得分

        # 时间跨度
        time_span = times[-1] - times[0]
        time_score = min(1.0, time_span / 1.0)  # 1秒时间跨度得满分

        completeness_score = (
                length_score * 0.3 +
                height_score * 0.3 +
                ground_proximity * 0.2 +
                time_score * 0.2
        )

        return completeness_score

    def _evaluate_temporal_weight(self, times, current_time):
        """评估时间权重（越近的轨迹权重越高）"""
        if len(times) == 0:
            return 0.0

        latest_time = times[-1]
        time_diff = current_time - latest_time

        # 指数衰减，2秒内保持高权重
        temporal_score = np.exp(-time_diff / 2.0)

        return temporal_score


class TrajectorySegmentManager:
    """轨迹片段管理器"""

    def __init__(self):
        self.quality_evaluator = TrajectoryQualityEvaluator()
        self.min_segment_length = 5
        self.segment_overlap = 0.3  # 片段重叠30%

    def find_best_trajectory_segment(self, points_3d, timestamps, current_time):
        """找到最佳轨迹片段"""
        if len(points_3d) < self.min_segment_length:
            return None, None, 0.0

        best_segment = None
        best_timestamps = None
        best_score = 0.0

        # 滑动窗口评估不同片段
        segment_length = max(self.min_segment_length, len(points_3d) // 3)
        step_size = max(1, int(segment_length * (1 - self.segment_overlap)))

        for start_idx in range(0, len(points_3d) - self.min_segment_length + 1, step_size):
            end_idx = min(start_idx + segment_length, len(points_3d))

            segment_points = points_3d[start_idx:end_idx]
            segment_times = timestamps[start_idx:end_idx]

            score = self.quality_evaluator.evaluate_trajectory_segment(
                segment_points, segment_times, current_time
            )

            if score > best_score:
                best_score = score
                best_segment = segment_points
                best_timestamps = segment_times

        return best_segment, best_timestamps, best_score


class BufferedImageProcessor:
    """缓冲图像处理器"""

    def __init__(self, model_path, buffer_duration=5.0, fps=30):
        self.model = YOLO(model_path)
        self.buffer_duration = buffer_duration
        self.fps = fps
        self.max_buffer_size = int(buffer_duration * fps)

        # 图像缓冲区
        self.image_buffer1 = deque(maxlen=self.max_buffer_size)
        self.image_buffer2 = deque(maxlen=self.max_buffer_size)
        self.timestamp_buffer = deque(maxlen=self.max_buffer_size)
        # Enhanced state management
        self.processing_lock = threading.Lock()  # Add thread safety
        self.last_processing_time = 0
        self.min_processing_interval = 2.0  # Minimum 2 seconds between processing

        # 处理状态
        self.is_processing = False
        self.processing_thread = None
        self.processing_callback = None

        print(f"BufferedImageProcessor initialized with {buffer_duration}s buffer")

    def add_frame_pair(self, frame1, frame2, timestamp):
        """添加帧对到缓冲区"""
        if not self.is_processing:  # 只在非处理状态下缓冲
            self.image_buffer1.append(frame1.copy() if frame1 is not None else None)
            self.image_buffer2.append(frame2.copy() if frame2 is not None else None)
            self.timestamp_buffer.append(timestamp)

    def trigger_processing(self, callback=None):
        """Thread-safe processing trigger with cooldown"""
        current_time = time.time()

        with self.processing_lock:
            if self.is_processing:
                print("⚠️ Processing already in progress...")
                return False

            # Check cooldown period
            if current_time - self.last_processing_time < self.min_processing_interval:
                remaining = self.min_processing_interval - (current_time - self.last_processing_time)
                print(f"⏱️ Processing cooldown: {remaining:.1f}s remaining")
                return False

            if len(self.image_buffer1) < 10:
                print("❌ Insufficient buffered frames for processing")
                return False

            self.processing_callback = callback
            self.is_processing = True
            self.last_processing_time = current_time

        # Start processing thread
        self.processing_thread = threading.Thread(target=self._process_buffered_frames)
        self.processing_thread.daemon = True
        self.processing_thread.start()

        return True



    def _process_buffered_frames(self):
        """处理缓冲的帧"""
        try:
            print(f"Processing {len(self.image_buffer1)} buffered frames...")

            # 复制缓冲区数据以避免处理期间的修改
            frames1 = list(self.image_buffer1)
            frames2 = list(self.image_buffer2)
            timestamps = list(self.timestamp_buffer)

            # 批量YOLO检测
            all_detections1 = []
            all_detections2 = []

            # 处理相机1
            for frame in frames1:
                if frame is not None:
                    detections = self._detect_shuttlecock_in_frame(frame)
                else:
                    detections = []
                all_detections1.append(detections)

            # 处理相机2
            for frame in frames2:
                if frame is not None:
                    detections = self._detect_shuttlecock_in_frame(frame)
                else:
                    detections = []
                all_detections2.append(detections)

            # 回调处理结果
            if self.processing_callback:
                self.processing_callback(
                    all_detections1, all_detections2, timestamps,
                    frames1, frames2
                )

        except Exception as e:
            print(f"❌ Error in processing buffered frames: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Ensure state is always reset
            with self.processing_lock:
                self.is_processing = False
            print("✅ Buffered frame processing completed")

    def force_reset_processing_state(self):
        """Force reset processing state (for emergency cleanup)"""
        with self.processing_lock:
            self.is_processing = False
            self.processing_callback = None
            if self.processing_thread and self.processing_thread.is_alive():
                # Don't join, just mark as completed
                pass
        print("🔄 Processing state force reset")

    def clear_buffer(self):
        """Enhanced buffer clearing with state reset"""
        with self.processing_lock:
            if not self.is_processing:
                self.image_buffer1.clear()
                self.image_buffer2.clear()
                self.timestamp_buffer.clear()
                print("✅ Image buffer cleared")
            else:
                print("⚠️ Cannot clear buffer while processing")

    def _detect_shuttlecock_in_frame(self, frame):
        """在单帧中检测羽毛球 - 支持多个羽毛球"""
        if frame is None:
            return []

        results = self.model(frame, conf=0.3, verbose=False)
        detections = []

        for r in results:
            # 处理关键点结果
            if hasattr(r, 'keypoints') and r.keypoints is not None:
                kpts = r.keypoints.xy.cpu().numpy() if hasattr(r.keypoints.xy, "cpu") else r.keypoints.xy
                for kp_list in kpts:
                    for kp in kp_list:
                        if not np.isnan(kp).any():
                            pos = (int(kp[0]), int(kp[1]))
                            detections.append((pos, 1.0))

            # 处理边界框结果
            if hasattr(r, 'boxes') and len(r.boxes) > 0:
                boxes = r.boxes.xyxy.cpu().numpy() if hasattr(r.boxes.xyxy, "cpu") else r.boxes.xyxy
                classes = r.boxes.cls.cpu().numpy() if hasattr(r.boxes.cls, "cpu") else r.boxes.cls
                confidences = r.boxes.conf.cpu().numpy() if hasattr(r.boxes.conf, "cpu") else r.boxes.conf

                shuttlecock_indices = np.where(classes == 0)[0]
                for idx in shuttlecock_indices:
                    box = boxes[idx]
                    conf = confidences[idx]
                    x1, y1, x2, y2 = map(int, box)
                    center = ((x1 + x2) // 2, (y1 + y2) // 2)
                    detections.append((center, conf))

        # 如果检测到多个羽毛球，按置信度排序并标记
        if len(detections) > 1:
            detections.sort(key=lambda x: x[1], reverse=True)  # 按置信度降序排序
            print(f"🏸 Multiple shuttlecocks detected: {len(detections)} objects")
            for i, (pos, conf) in enumerate(detections):
                print(f"   Shuttlecock {i+1}: position {pos}, confidence {conf:.3f}")

        return detections

    def get_buffer_info(self):
        """获取缓冲区信息"""
        return {
            'buffer_size': len(self.image_buffer1),
            'max_size': self.max_buffer_size,
            'is_processing': self.is_processing,
            'buffer_time_span': len(self.timestamp_buffer) / self.fps if self.timestamp_buffer else 0
        }

    def clear_buffer(self):
        """清空缓冲区"""
        if not self.is_processing:
            self.image_buffer1.clear()
            self.image_buffer2.clear()
            self.timestamp_buffer.clear()
            print("Image buffer cleared")


class StereoProcessor:
    """增强的双目视觉处理器 - 添加调试数据追踪和多目标支持"""

    def __init__(self):
        self.camera1_params = None
        self.camera2_params = None
        self.fundamental_matrix = None

        # 轨迹管理
        self.trajectory_manager = TrajectorySegmentManager()
        
        # 多目标跟踪器
        self.multi_tracker = MultiObjectTracker(max_objects=2, distance_threshold=100)

        # 场地过滤参数 (cm) - 扩大范围支持场地外预测
        self.court_bounds = {
            'x_min': -500,  # 扩大到场地外1.5米
            'x_max': 500,
            'y_min': -900,  # 扩大到场地外2米
            'y_max': 900,
            'z_min': 0,
            'z_max': 800  # 8米高度上限
        }

        # 3D点存储 - 支持多轨迹
        self.all_3d_points = []
        self.all_timestamps = []
        self.track_data = {}  # track_id -> {'points': [], 'timestamps': []}

        # 新增：调试数据存储
        self.rejected_points = []  # 被边界过滤排除的点
        self.low_quality_points = []  # 质量评估低的点
        self.triangulation_failed_points = []  # 三角测量失败的点对

        print("StereoProcessor initialized with debug tracking and multi-object support enabled")

    def load_camera_parameters(self, camera1_file, camera2_file):
        """加载相机参数"""
        try:
            self.camera1_params = self._load_camera_params(camera1_file)
            self.camera2_params = self._load_camera_params(camera2_file)
            self._compute_fundamental_matrix()
            print("Stereo camera parameters loaded successfully")
            return True
        except Exception as e:
            print(f"Error loading stereo parameters: {e}")
            return False

    def _load_camera_params(self, params_file):
        """从文件加载相机参数"""
        fs = cv2.FileStorage(params_file, cv2.FILE_STORAGE_READ)

        camera_matrix = fs.getNode("camera_matrix").mat()
        dist_coeffs = fs.getNode("distortion_coefficients").mat().flatten()
        rotation_vector = fs.getNode("rotation_vector").mat()
        translation_vector = fs.getNode("translation_vector").mat()

        fs.release()

        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
        camera_position = -np.dot(rotation_matrix.T, translation_vector)

        return {
            'camera_matrix': camera_matrix,
            'dist_coeffs': dist_coeffs,
            'rotation_vector': rotation_vector,
            'translation_vector': translation_vector,
            'rotation_matrix': rotation_matrix,
            'camera_position': camera_position
        }

    def _compute_fundamental_matrix(self):
        """计算基础矩阵"""
        if self.camera1_params is None or self.camera2_params is None:
            return

        try:
            R1 = self.camera1_params['rotation_matrix']
            R2 = self.camera2_params['rotation_matrix']
            t1 = self.camera1_params['translation_vector']
            t2 = self.camera2_params['translation_vector']

            R_rel = R2 @ R1.T
            t_rel = t2 - R_rel @ t1

            tx = np.array([[0, -t_rel[2, 0], t_rel[1, 0]],
                           [t_rel[2, 0], 0, -t_rel[0, 0]],
                           [-t_rel[1, 0], t_rel[0, 0], 0]])

            E = tx @ R_rel
            K1 = self.camera1_params['camera_matrix']
            K2 = self.camera2_params['camera_matrix']
            self.fundamental_matrix = np.linalg.inv(K2).T @ E @ np.linalg.inv(K1)

            print("Fundamental matrix computed successfully")

        except Exception as e:
            print(f"Error computing fundamental matrix: {e}")
            self.fundamental_matrix = None

    def process_batch_detections(self, detections_list1, detections_list2, timestamps):
        """批量处理检测结果 - 增强调试追踪和多目标支持"""
        if len(detections_list1) != len(detections_list2) != len(timestamps):
            print("Error: Detection lists and timestamps length mismatch")
            return []

        all_3d_points = []
        all_timestamps_3d = []

        # 清空调试数据
        self.rejected_points = []
        self.low_quality_points = []
        self.triangulation_failed_points = []

        print(f"Processing {len(detections_list1)} frame pairs with multi-object tracking...")

        # 处理每一帧的检测结果
        for i, (det1, det2, timestamp) in enumerate(zip(detections_list1, detections_list2, timestamps)):
            # 双目匹配
            matched_pairs = self._match_stereo_points(det1, det2)

            # 当前帧的所有3D检测点
            frame_3d_points = []
            
            # 三角测量
            for left_point, right_point, match_distance, match_conf in matched_pairs:
                point_3d = self._triangulate_point(left_point, right_point)

                if point_3d is None:
                    # 记录三角测量失败的点对
                    self.triangulation_failed_points.append({
                        'left_point': left_point,
                        'right_point': right_point,
                        'timestamp': timestamp,
                        'frame_index': i,
                        'reason': 'triangulation_failed'
                    })
                    continue

                if self._is_point_in_bounds(point_3d):
                    frame_3d_points.append((point_3d, match_conf))
                    all_3d_points.append(point_3d)
                    all_timestamps_3d.append(timestamp)
                else:
                    # 记录被边界过滤排除的点
                    self.rejected_points.append({
                        'point_3d': point_3d,
                        'timestamp': timestamp,
                        'frame_index': i,
                        'reason': 'out_of_bounds',
                        'match_confidence': match_conf,
                        'match_distance': match_distance
                    })
            
            # 更新多目标跟踪器
            if frame_3d_points:
                # 将3D点投影到2D用于跟踪（使用相机1的投影）
                tracking_detections = []
                for point_3d, conf in frame_3d_points:
                    # 简化投影：使用XY坐标作为2D位置
                    pos_2d = (int(point_3d[0] + 500), int(point_3d[1] + 500))  # 偏移到正值
                    tracking_detections.append((pos_2d, conf))
                
                # 更新跟踪器
                active_tracks = self.multi_tracker.update(tracking_detections, timestamp)
                
                if len(active_tracks) > 1:
                    print(f"📍 Frame {i}: Tracking {len(active_tracks)} shuttlecocks")

        # 存储所有3D点
        self.all_3d_points = all_3d_points
        self.all_timestamps = all_timestamps_3d

        # 分析跟踪结果
        tracks = self.multi_tracker.get_tracks()
        if len(tracks) > 1:
            print(f"🏸 Multiple shuttlecock tracks detected:")
            for track_id, track in tracks.items():
                print(f"   Track {track_id}: {len(track['positions'])} points, "
                      f"avg_conf={np.mean(track['confidences']):.3f}")

        print(f"Generated {len(all_3d_points)} valid 3D points from batch processing")
        print(f"Rejected {len(self.rejected_points)} out-of-bounds points")
        print(f"Failed triangulation for {len(self.triangulation_failed_points)} point pairs")

        return all_3d_points, all_timestamps_3d

    def get_best_trajectory_from_tracks(self, current_time):
        """从多个轨迹中选择最佳轨迹进行预测"""
        tracks = self.multi_tracker.get_tracks()
        
        if not tracks:
            # 没有轨迹时，使用传统方法
            return self.find_best_trajectory_for_prediction(current_time)
        
        if len(tracks) == 1:
            # 只有一个轨迹
            track_id, track = list(tracks.items())[0]
            print(f"📍 Using single track {track_id} with {len(track['positions'])} points")
            return self.find_best_trajectory_for_prediction(current_time)
        
        # 多个轨迹，选择最佳的
        best_track_id, best_track = self.multi_tracker.get_best_track()
        if best_track_id is not None:
            print(f"🎯 Selected best track {best_track_id} from {len(tracks)} tracks")
            print(f"   Track quality: {len(best_track['positions'])} points, "
                  f"missing_frames={best_track['missing_frames']}")
            
            # 过滤轨迹数据并转换为3D点
            track_3d_points = []
            track_timestamps = []
            
            # 在所有3D点中查找属于此轨迹的点
            # 这里简化处理，使用时间窗口匹配
            track_start_time = best_track['created_at']
            track_end_time = best_track['timestamps'][-1] if best_track['timestamps'] else current_time
            
            for i, timestamp in enumerate(self.all_timestamps):
                if track_start_time <= timestamp <= track_end_time + 0.1:  # 允许小误差
                    track_3d_points.append(self.all_3d_points[i])
                    track_timestamps.append(timestamp)
            
            if len(track_3d_points) >= 5:
                print(f"📊 Using {len(track_3d_points)} 3D points from best track")
                confidence = min(1.0, len(track_3d_points) / 20.0)  # 基于点数的置信度
                return track_3d_points, track_timestamps, confidence
        
        # 如果无法从轨迹获取足够数据，回退到传统方法
        print("⚠️ Falling back to traditional trajectory selection")
        return self.find_best_trajectory_for_prediction(current_time)

    def _match_stereo_points(self, detections_left, detections_right, epipolar_threshold=35.0):
        """基于极线约束匹配双目点"""
        if not detections_left or not detections_right or self.fundamental_matrix is None:
            return []

        matches = []

        for left_point, left_conf in detections_left:
            point_homo = np.array([left_point[0], left_point[1], 1])
            epipolar_line = self.fundamental_matrix @ point_homo

            best_match = None
            min_distance = float('inf')
            best_conf = 0

            for right_point, right_conf in detections_right:
                distance = abs(epipolar_line[0] * right_point[0] +
                               epipolar_line[1] * right_point[1] +
                               epipolar_line[2]) / np.sqrt(epipolar_line[0] ** 2 + epipolar_line[1] ** 2)

                if distance < epipolar_threshold and distance < min_distance:
                    min_distance = distance
                    best_match = right_point
                    best_conf = (left_conf + right_conf) / 2

            if best_match is not None:
                matches.append((left_point, best_match, min_distance, best_conf))

        return matches

    def _triangulate_point(self, point1, point2):
        """三角测量计算3D点"""
        if self.camera1_params is None or self.camera2_params is None:
            return None

        try:
            point1_normalized = cv2.undistortPoints(
                np.array([point1], dtype=np.float32),
                self.camera1_params['camera_matrix'],
                self.camera1_params['dist_coeffs']
            )

            point2_normalized = cv2.undistortPoints(
                np.array([point2], dtype=np.float32),
                self.camera2_params['camera_matrix'],
                self.camera2_params['dist_coeffs']
            )

            ray1_dir = np.array([
                point1_normalized[0][0][0],
                point1_normalized[0][0][1],
                1.0
            ])

            ray2_dir = np.array([
                point2_normalized[0][0][0],
                point2_normalized[0][0][1],
                1.0
            ])

            ray1_dir_world = self.camera1_params['rotation_matrix'].T @ ray1_dir
            ray2_dir_world = self.camera2_params['rotation_matrix'].T @ ray2_dir

            ray1_dir_world = ray1_dir_world / np.linalg.norm(ray1_dir_world)
            ray2_dir_world = ray2_dir_world / np.linalg.norm(ray2_dir_world)

            camera1_position = self.camera1_params['camera_position']
            camera2_position = self.camera2_params['camera_position']

            n = np.cross(ray1_dir_world.flatten(), ray2_dir_world.flatten())

            if np.linalg.norm(n) < 1e-10:
                return None

            n1 = np.cross(ray1_dir_world.flatten(), n)
            n2 = np.cross(ray2_dir_world.flatten(), n)

            c1 = camera1_position.flatten()
            c2 = camera2_position.flatten()

            t1 = np.dot((c2 - c1), n2) / np.dot(ray1_dir_world.flatten(), n2)
            t2 = np.dot((c1 - c2), n1) / np.dot(ray2_dir_world.flatten(), n1)

            p1 = c1 + t1 * ray1_dir_world.flatten()
            p2 = c2 + t2 * ray2_dir_world.flatten()

            point_3d = (p1 + p2) / 2

            return point_3d

        except Exception as e:
            return None

    def _is_point_in_bounds(self, point_3d):
        """检查3D点是否在扩展边界内"""
        if point_3d is None or len(point_3d) < 3:
            return False

        x, y, z = point_3d[0], point_3d[1], point_3d[2]

        return (self.court_bounds['x_min'] <= x <= self.court_bounds['x_max'] and
                self.court_bounds['y_min'] <= y <= self.court_bounds['y_max'] and
                self.court_bounds['z_min'] <= z <= self.court_bounds['z_max'])

    def find_best_trajectory_for_prediction(self, current_time):
        """找到最适合预测的轨迹片段 - 记录被排除的低质量点"""
        if len(self.all_3d_points) < 5:
            return None, None, 0.0

        # 在寻找最佳轨迹之前，记录所有不符合质量要求的点
        # 这里可以添加更复杂的质量评估逻辑
        for i, (point, timestamp) in enumerate(zip(self.all_3d_points, self.all_timestamps)):
            # 简单的质量检查示例
            if i > 0:
                prev_point = self.all_3d_points[i - 1]
                prev_time = self.all_timestamps[i - 1]

                # 检查距离和时间间隔的合理性
                distance = np.linalg.norm(point - prev_point)
                time_diff = timestamp - prev_time

                if time_diff > 0:
                    velocity = distance / time_diff
                    # 如果速度异常高，标记为低质量点
                    if velocity > 2000:  # 20m/s
                        self.low_quality_points.append({
                            'point_3d': point,
                            'timestamp': timestamp,
                            'reason': 'high_velocity',
                            'velocity': velocity,
                            'distance': distance,
                            'time_diff': time_diff
                        })

        best_points, best_timestamps, confidence = self.trajectory_manager.find_best_trajectory_segment(
            self.all_3d_points, self.all_timestamps, current_time
        )

        return best_points, best_timestamps, confidence

    def get_debug_data(self):
        """获取调试数据"""
        return {
            'all_valid_points': self.all_3d_points,
            'all_timestamps': self.all_timestamps,
            'rejected_points': self.rejected_points,
            'low_quality_points': self.low_quality_points,
            'triangulation_failed_points': self.triangulation_failed_points
        }

    def reset(self):
        """重置处理器状态"""
        self.all_3d_points = []
        self.all_timestamps = []
        self.rejected_points = []
        self.low_quality_points = []
        self.triangulation_failed_points = []
        print("StereoProcessor reset")