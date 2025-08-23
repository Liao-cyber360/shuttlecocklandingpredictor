import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import cv2
import numpy as np
import time
import argparse
from enum import Enum

from utils import config, UIHelper
from calibration import calibrate_cameras
from detector import BufferedImageProcessor, StereoProcessor
from predictor import TrajectoryPredictor, CourtBoundaryAnalyzer
from visualization_3d import Interactive3DVisualizer
from network_camera import NetworkCameraManager
from video_controls import EnhancedVideoControls


class SystemState(Enum):
    """系统状态枚举"""
    BUFFERING = "buffering"
    PROCESSING = "processing"
    PREDICTION_READY = "prediction_ready"
    PREDICTION_COMPLETE = "prediction_complete"


class BufferedBadmintonSystem:
    """基于图像缓冲的羽毛球落点预测系统 - 完全修复版"""

    def __init__(self):
        """初始化系统"""
        self.state = SystemState.BUFFERING
        self.running = False
        self.calibration_done = False

        # 视频和相机参数
        self.video_path1 = None
        self.video_path2 = None
        self.camera1_params_file = None
        self.camera2_params_file = None
        
        # 新增：网络摄像头支持
        self.camera_url1 = None
        self.camera_url2 = None
        self.network_mode = False
        self.timestamp_header = "X-Timestamp"

        # 核心模块
        self.buffered_processor = None
        self.stereo_processor = None
        self.trajectory_predictor = None
        self.court_analyzer = None
        self.interactive_3d_viz = None

        # 视频捕获
        self.cap1 = None
        self.cap2 = None
        self.network_camera_manager = None
        
        # 新增：视频控制组件
        self.video_controls = None

        # 帧率控制
        self.video_fps = 30.0
        self.frame_time = 1.0 / self.video_fps
        self.last_frame_time = 0
        self.playback_speed = 1.0

        # 暂停控制 - 增强状态管理
        self.paused = False
        self.pause_requested = False

        # 数据和状态
        self.frame_count = 0
        self.actual_fps = 0
        self.fps_counter = 0
        self.fps_prev_time = time.time()

        # 预测结果和控制 - 增强管理
        self.prediction_result = None
        self.last_prediction_time = 0
        self.prediction_cooldown = 2.0  # 减少冷却时间
        self.processing_lock = False  # 处理锁标志

        # 轨迹数据保存
        self.current_trajectory_data = None

        # 当前帧缓存（用于显示）
        self.current_frame1 = None
        self.current_frame2 = None

        # 系统性能监控
        self.system_start_time = time.time()
        self.total_predictions = 0
        self.successful_predictions = 0
        
        # 视频控制相关
        self.total_frames = 0
        self.current_frame_index = 0
        self.seek_requested = False
        self.seek_frame = 0

        print("=" * 80)
        print("Enhanced Buffered Badminton System v5.2 - Network Camera Support")
        print(f"Initialized at: {time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"Current User: Liao-cyber360")
        print("Key Features: Network cameras, Progress bar, Multi-object tracking")
        print("=" * 80)

    def initialize_system(self, video_path1, video_path2):
        """初始化系统 - 增强版本"""
        print("🚀 Initializing enhanced buffered badminton analysis system...")

        UIHelper.display_splash_screen(3)

        self.video_path1 = video_path1
        self.video_path2 = video_path2

        # 验证视频文件
        if not os.path.exists(video_path1):
            raise FileNotFoundError(f"Video file not found: {video_path1}")
        if not os.path.exists(video_path2):
            raise FileNotFoundError(f"Video file not found: {video_path2}")

        # 打开视频捕获
        self.cap1 = cv2.VideoCapture(video_path1)
        self.cap2 = cv2.VideoCapture(video_path2)

        if not self.cap1.isOpened():
            raise ValueError(f"Cannot open video file: {video_path1}")
        if not self.cap2.isOpened():
            raise ValueError(f"Cannot open video file: {video_path2}")

        # 获取视频信息
        fps1 = self.cap1.get(cv2.CAP_PROP_FPS)
        fps2 = self.cap2.get(cv2.CAP_PROP_FPS)
        frame_count1 = int(self.cap1.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_count2 = int(self.cap2.get(cv2.CAP_PROP_FRAME_COUNT))

        self.video_fps = min(fps1, fps2) if fps1 > 0 and fps2 > 0 else 30.0
        self.frame_time = 1.0 / self.video_fps
        self.total_frames = min(frame_count1, frame_count2)

        print(f"📹 Video Information:")
        print(f"   Camera 1: {fps1:.1f} FPS, {frame_count1} frames")
        print(f"   Camera 2: {fps2:.1f} FPS, {frame_count2} frames")
        print(f"   Using playback FPS: {self.video_fps:.1f}")
        print(f"   Total frames: {self.total_frames}")

        # 初始化视频控制组件
        self.video_controls = EnhancedVideoControls(video_width=1280)
        self.video_controls.set_video_info(self.total_frames, self.video_fps)

        # 初始化核心模块
        self._initialize_core_modules()

        print("✅ Enhanced system initialization complete!")
        print(f"📊 System ready for operation at {time.strftime('%H:%M:%S')} UTC")
        return True

    def _initialize_core_modules(self):
        """初始化核心模块"""
        print("🔧 Initializing core modules...")

        # 缓冲处理器
        self.buffered_processor = BufferedImageProcessor(
            config.yolo_ball_model,
            buffer_duration=5.0,
            fps=self.video_fps
        )

        # 双目处理器
        self.stereo_processor = StereoProcessor()

        # 轨迹预测器
        self.trajectory_predictor = TrajectoryPredictor()

        # 场地分析器
        self.court_analyzer = CourtBoundaryAnalyzer()

        # 3D可视化器 - 使用增强版本
        self.interactive_3d_viz = Interactive3DVisualizer()
        self.interactive_3d_viz.start()

        print("✅ Enhanced system initialization complete!")
        print(f"📊 System ready for operation at {time.strftime('%H:%M:%S')} UTC")
        return True

    def initialize_network_cameras(self, camera_url1, camera_url2=None, timestamp_header="X-Timestamp"):
        """初始化网络摄像头系统"""
        print("🌐 Initializing network camera system...")
        
        self.camera_url1 = camera_url1
        self.camera_url2 = camera_url2
        self.timestamp_header = timestamp_header
        self.network_mode = True
        
        # 创建网络摄像头管理器
        self.network_camera_manager = NetworkCameraManager(
            camera_url1, camera_url2, timestamp_header
        )
        
        # 启动网络流
        if not self.network_camera_manager.start():
            raise RuntimeError("Failed to start network camera streams")
        
        # 等待几秒让流稳定
        print("⏳ Waiting for network streams to stabilize...")
        time.sleep(3)
        
        # 获取FPS信息
        self.video_fps = self.network_camera_manager.get_fps()
        if self.video_fps <= 0:
            self.video_fps = 30.0  # 默认FPS
        self.frame_time = 1.0 / self.video_fps
        
        print(f"📹 Network Camera Information:")
        print(f"   Camera 1: {camera_url1}")
        if camera_url2:
            print(f"   Camera 2: {camera_url2}")
        print(f"   Timestamp header: {timestamp_header}")
        print(f"   Estimated FPS: {self.video_fps:.1f}")
        
        # 初始化核心模块（与视频文件模式相同）
        self._initialize_core_modules()
        
        print("✅ Network camera system initialization complete!")
        print(f"📊 System ready for network operation at {time.strftime('%H:%M:%S')} UTC")
        return True

    def calibration_mode(self):
        """相机标定模式 - 增强错误处理"""
        print("🎯 Starting enhanced camera calibration...")

        output_dir = os.path.join(config.results_dir, "calibration")
        os.makedirs(output_dir, exist_ok=True)

        try:
            extrinsic_file1, extrinsic_file2 = calibrate_cameras(
                self.video_path1, self.video_path2, output_dir
            )

            if not extrinsic_file1 or not extrinsic_file2:
                raise ValueError("Calibration files not generated properly")

            self.camera1_params_file = extrinsic_file1
            self.camera2_params_file = extrinsic_file2

            # 验证标定文件
            if not os.path.exists(extrinsic_file1) or not os.path.exists(extrinsic_file2):
                raise FileNotFoundError("Calibration files not found after generation")

            # 加载标定结果
            success = self.stereo_processor.load_camera_parameters(extrinsic_file1, extrinsic_file2)
            if not success:
                raise ValueError("Failed to load calibration parameters")

            self.calibration_done = True
            print("✅ Camera calibration completed successfully!")
            print(f"   Camera 1 params: {extrinsic_file1}")
            print(f"   Camera 2 params: {extrinsic_file2}")
            return True

        except Exception as e:
            print(f"❌ Calibration failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def load_existing_calibration(self, cam1_params, cam2_params):
        """加载已有的标定参数 - 增强验证"""
        try:
            # 验证文件存在
            if not os.path.exists(cam1_params):
                raise FileNotFoundError(f"Camera 1 parameters file not found: {cam1_params}")
            if not os.path.exists(cam2_params):
                raise FileNotFoundError(f"Camera 2 parameters file not found: {cam2_params}")

            print(f"📁 Loading calibration parameters...")
            print(f"   Camera 1: {cam1_params}")
            print(f"   Camera 2: {cam2_params}")

            self.camera1_params_file = cam1_params
            self.camera2_params_file = cam2_params

            success = self.stereo_processor.load_camera_parameters(cam1_params, cam2_params)
            if not success:
                raise ValueError("Failed to load camera parameters into stereo processor")

            self.calibration_done = True
            print("✅ Existing calibration parameters loaded successfully!")
            return True

        except Exception as e:
            print(f"❌ Failed to load calibration parameters: {e}")
            return False

    def _on_processing_complete(self, detections1, detections2, timestamps, frames1, frames2):
        """处理完成回调 - 完全重写修复"""
        try:
            print("🔄 Processing buffered frames...")
            current_time = time.time()

            # 批量生成3D点
            points_3d, timestamps_3d = self.stereo_processor.process_batch_detections(
                detections1, detections2, timestamps
            )

            # 获取调试数据
            debug_data = self.stereo_processor.get_debug_data()

            # 找到最佳轨迹片段 - 使用多目标跟踪
            best_trajectory, best_timestamps, confidence = \
                self.stereo_processor.get_best_trajectory_from_tracks(current_time)

            if best_trajectory is None or confidence < 0.3:
                print(f"❌ Trajectory quality insufficient for prediction (confidence: {confidence:.2f})")
                print("   Trying fallback trajectory selection...")
                # 回退到传统方法
                best_trajectory, best_timestamps, confidence = \
                    self.stereo_processor.find_best_trajectory_for_prediction(current_time)
                
                if best_trajectory is None or confidence < 0.3:
                    self._handle_prediction_failure(debug_data, "Insufficient trajectory quality")
                    return

            print(f"✅ Found quality trajectory: {len(best_trajectory)} points, confidence: {confidence:.2f}")

            # 执行预测
            self.state = SystemState.PROCESSING
            self.total_predictions += 1

            prediction_result = self._predict_landing_point(best_trajectory, best_timestamps, confidence)

            if prediction_result is not None:
                self.successful_predictions += 1
                self._handle_prediction_success(
                    prediction_result, best_trajectory, best_timestamps,
                    confidence, points_3d, timestamps_3d, debug_data
                )
            else:
                print("❌ Landing prediction computation failed")
                self._handle_prediction_failure(debug_data, "Prediction computation failed")

        except Exception as e:
            print(f"❌ Critical error in processing callback: {e}")
            import traceback
            traceback.print_exc()
            self._handle_prediction_failure({}, f"Critical error: {str(e)}")

    def _handle_prediction_success(self, prediction_result, best_trajectory, best_timestamps,
                                   confidence, points_3d, timestamps_3d, debug_data):
        """处理预测成功 - 增强版本"""
        try:
            landing_position, in_bounds = prediction_result
            self.state = SystemState.PREDICTION_COMPLETE

            # 保存完整轨迹数据
            self.current_trajectory_data = {
                'trajectory': best_trajectory,
                'timestamps': best_timestamps,
                'confidence': confidence,
                'all_points_3d': points_3d,
                'all_timestamps_3d': timestamps_3d,
                'debug_data': debug_data,
                'prediction_result': self.prediction_result,
                'prediction_time': time.time(),
                'success': True
            }

            # 准备调试数据用于可视化
            debug_data['prediction_points'] = best_trajectory
            debug_data['prediction_timestamps'] = best_timestamps

            # 更新3D可视化（如果存在）
            if self.interactive_3d_viz:
                try:
                    self.interactive_3d_viz.update_debug_data(debug_data)

                    predicted_trajectory = self.prediction_result.get('trajectory', [])
                    self.interactive_3d_viz.update_predicted_trajectory(predicted_trajectory)
                    self.interactive_3d_viz.update_landing_point(landing_position, in_bounds)

                    print("✅ 3D visualization updated successfully")
                except Exception as viz_error:
                    print(f"⚠️ 3D visualization update error (non-critical): {viz_error}")

            # 显示预测结果
            self._display_prediction_result(landing_position, in_bounds, confidence)

            # 打印详细调试信息
            self._print_detailed_debug_info(debug_data, best_trajectory,
                                            self.prediction_result.get('trajectory', []))

        except Exception as e:
            print(f"❌ Error handling prediction success: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 确保状态被重置
            self._reset_processing_state()

    def _handle_prediction_failure(self, debug_data, reason="Unknown"):
        """处理预测失败 - 增强版本"""
        try:
            print(f"❌ Prediction failed: {reason}")

            # 保存失败数据用于调试
            self.current_trajectory_data = {
                'success': False,
                'failure_reason': reason,
                'debug_data': debug_data,
                'failure_time': time.time()
            }

            # 更新3D可视化显示调试数据但没有预测轨迹
            if self.interactive_3d_viz:
                try:
                    debug_data['prediction_points'] = []
                    debug_data['prediction_timestamps'] = []
                    self.interactive_3d_viz.update_debug_data(debug_data)
                    self.interactive_3d_viz.update_predicted_trajectory([])

                    # 打印调试统计
                    self._print_detailed_debug_info(debug_data, [], [])
                except Exception as viz_error:
                    print(f"⚠️ 3D visualization error during failure handling: {viz_error}")

        except Exception as e:
            print(f"❌ Error handling prediction failure: {e}")
        finally:
            # 确保状态被重置
            self._reset_processing_state()

    def _reset_processing_state(self):
        """重置处理状态 - 集中化管理"""
        try:
            # 重置系统状态
            self.state = SystemState.BUFFERING
            self.processing_lock = False

            # 重置缓冲处理器状态
            if self.buffered_processor:
                self.buffered_processor.is_processing = False

            print("🔄 Processing state reset to BUFFERING")

        except Exception as e:
            print(f"⚠️ Error resetting processing state: {e}")
            # 强制重置关键状态
            self.state = SystemState.BUFFERING
            self.processing_lock = False

    def _predict_landing_point(self, trajectory_points, trajectory_timestamps, confidence):
        """预测羽毛球落地点 - 增强错误处理"""
        try:
            print(f"🎯 Starting landing point prediction...")
            print(f"   Input points: {len(trajectory_points)}")
            print(f"   Time span: {trajectory_timestamps[-1] - trajectory_timestamps[0]:.3f}s")

            landing_position, landing_time, predicted_trajectory = \
                self.trajectory_predictor.predict_landing_point(trajectory_points, trajectory_timestamps)

            if landing_position is None:
                print("❌ Trajectory predictor returned None")
                return None

            # 判断是否在界内
            in_bounds = self.court_analyzer.is_point_in_court(landing_position, game_type='singles')

            # 保存预测结果
            self.prediction_result = {
                'landing_point': landing_position,
                'landing_time': landing_time,
                'trajectory': predicted_trajectory,
                'in_bounds': in_bounds,
                'confidence': confidence,
                'prediction_timestamp': time.time()
            }

            print(f"✅ Prediction computed successfully")
            print(f"   Landing point: ({landing_position[0]:.1f}, {landing_position[1]:.1f})")
            print(f"   Trajectory points: {len(predicted_trajectory) if predicted_trajectory else 0}")

            return landing_position, in_bounds

        except Exception as e:
            print(f"❌ Error in landing point prediction: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _display_prediction_result(self, landing_position, in_bounds, confidence):
        """显示预测结果 - 增强版本"""
        current_time = time.strftime('%H:%M:%S')

        print(f"\n{'=' * 60}")
        print(f"🎯 PREDICTION RESULT - {current_time} UTC")
        print(f"{'=' * 60}")
        print(f"📍 Landing Position: ({landing_position[0]:.1f}, {landing_position[1]:.1f}) cm")
        print(f"🏆 Status: {'✅ IN BOUNDS' if in_bounds else '❌ OUT OF BOUNDS'}")
        print(f"🎲 Confidence: {confidence:.2f}")
        print(f"📊 Session Stats: {self.successful_predictions}/{self.total_predictions} successful")

        # 显示调试信息摘要
        if self.current_trajectory_data and 'debug_data' in self.current_trajectory_data:
            debug_data = self.current_trajectory_data['debug_data']
            print(f"\n📊 Debug Summary:")
            print(f"   Valid points used: {len(debug_data.get('all_valid_points', []))}")
            print(f"   Trajectory points: {len(debug_data.get('prediction_points', []))}")
            print(f"   Rejected points: {len(debug_data.get('rejected_points', []))}")

        print(f"\n📋 Available Actions:")
        print(f"   V - Open 3D visualization with full debug data")
        print(f"   D - Print detailed debug statistics")
        print(f"   P - Resume video playback")
        print(f"   R - Reset system for new analysis")
        print(f"   1-6 - Toggle point types in 3D view (when open)")
        print(f"{'=' * 60}")

    def _print_detailed_debug_info(self, debug_data, selected_trajectory, predicted_trajectory):
        """打印详细调试信息 - 增强版本"""
        print(f"\n📊 DETAILED DEBUG ANALYSIS:")
        print(f"{'─' * 50}")

        # 数据统计
        all_points = len(debug_data.get('all_valid_points', []))
        selected_points = len(selected_trajectory) if selected_trajectory else 0
        predicted_points = len(predicted_trajectory) if predicted_trajectory else 0
        rejected_points = len(debug_data.get('rejected_points', []))
        low_quality = len(debug_data.get('low_quality_points', []))
        failed_triangulation = len(debug_data.get('triangulation_failed_points', []))

        print(f"📈 Data Statistics:")
        print(f"   All valid points (150 frames): {all_points}")
        print(f"   Selected for prediction: {selected_points}")
        print(f"   Predicted trajectory points: {predicted_points}")
        print(f"   Rejected (out-of-bounds): {rejected_points}")
        print(f"   Low quality: {low_quality}")
        print(f"   Failed triangulation: {failed_triangulation}")

        # 轨迹质量分析
        if selected_trajectory and len(selected_trajectory) > 1:
            points = np.array(selected_trajectory)
            distances = [np.linalg.norm(points[i] - points[i - 1]) for i in range(1, len(points))]
            z_range = np.max(points[:, 2]) - np.min(points[:, 2])

            print(f"\n🎯 Selected Trajectory Quality:")
            print(f"   Average point distance: {np.mean(distances):.1f} cm")
            print(f"   Height range: {z_range:.1f} cm")
            print(f"   Initial height: {points[0, 2]:.1f} cm")
            print(f"   Final height: {points[-1, 2]:.1f} cm")
            print(f"   Height drop: {points[0, 2] - points[-1, 2]:.1f} cm")

        # 预测轨迹分析
        if predicted_trajectory and len(predicted_trajectory) > 0:
            print(f"\n🎲 Prediction Analysis:")
            print(f"   Predicted trajectory length: {len(predicted_trajectory)}")

            if len(predicted_trajectory) > 1:
                start_pos = predicted_trajectory[0]['position'] if isinstance(predicted_trajectory[0], dict) else \
                predicted_trajectory[0]
                end_pos = predicted_trajectory[-1]['position'] if isinstance(predicted_trajectory[-1], dict) else \
                predicted_trajectory[-1]

                horizontal_distance = np.linalg.norm(np.array(end_pos[:2]) - np.array(start_pos[:2]))
                print(f"   Horizontal prediction distance: {horizontal_distance:.1f} cm")

        print(f"{'─' * 50}")

    def start_processing(self):
        """开始处理视频 - 完全重写的主循环"""
        if not self.calibration_done:
            print("⚠️ Warning: Cameras not calibrated. System may not work properly.")
            return

        # 创建主显示窗口
        cv2.namedWindow('Enhanced Badminton System - Live View', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Enhanced Badminton System - Live View', 1280, 640)

        # 初始化运行状态
        self.running = True
        self.state = SystemState.BUFFERING
        self.last_frame_time = time.time()
        self.fps_prev_time = time.time()

        print(f"\n{'=' * 80}")
        print(f"🚀 STARTING ENHANCED VIDEO PROCESSING at {self.video_fps:.1f} FPS")
        print(f"Session started: {time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"User: Liao-cyber360")
        print(f"{'=' * 80}")

        self._print_control_instructions()

        # 主处理循环
        try:
            while self.running:
                loop_start_time = time.time()

                # 1. 处理暂停状态
                if self.paused:
                    self._handle_paused_state()
                    continue

                # 2. 帧率控制
                if not self._should_process_frame(loop_start_time):
                    # 在等待期间处理背景任务
                    self._handle_background_tasks()
                    continue

                # 3. 读取和处理视频帧
                if not self._process_video_frame():
                    print("📹 End of video reached")
                    break

                # 4. 更新显示
                self._update_display()

                # 5. 处理背景任务
                self._handle_background_tasks()

                # 6. 性能监控
                self._monitor_performance()

        except KeyboardInterrupt:
            print(f"\n{'=' * 80}")
            print("⚠️ Program interrupted by user (Ctrl+C)")
            print(f"Session ended: {time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print(f"{'=' * 80}")
        except Exception as e:
            print(f"❌ Critical error in main processing loop: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._cleanup()

    def _print_control_instructions(self):
        """打印控制说明 - 完整版本，包含新功能"""
        print("\n📋 ENHANCED SYSTEM CONTROLS:")
        print("   ▶️  SPACE     - Pause/Resume video playback")
        print("   🎯 T         - Trigger trajectory analysis (when paused)")
        print("   ▶️  P         - Resume playback (when paused)")
        
        if not self.network_mode:
            print("   🎮 MOUSE     - Drag progress bar to seek video position")
            print("   📍 CLICK     - Click progress bar to jump to position")
        else:
            print("   📡 NETWORK   - Network camera mode (seeking disabled)")
        
        print("   🔍 V         - Toggle 3D visualization window")
        print("   ❌ Q         - Close 3D visualization window")
        print("   📊 D         - Print detailed debug statistics")
        print("   ❓ H         - Show complete help screen")
        print("   🔄 R         - Complete system reset")
        print("   ⏩ +/=       - Increase playback speed")
        print("   ⏪ -/_       - Decrease playback speed")
        print("   🔄 0         - Reset playback speed")
        print("   🚪 ESC       - Exit program")
        print("\n🔧 3D VISUALIZATION CONTROLS (when window open):")
        print("   1 - Toggle all valid points (light green)")
        print("   2 - Toggle prediction points (dark blue)")
        print("   3 - Toggle rejected points (red)")
        print("   4 - Toggle low quality points (orange)")
        print("   5 - Toggle triangulation failed (gray)")
        print("   6 - Toggle predicted trajectory (cyan line)")
        print("\n🏸 NEW FEATURES v5.2:")
        print("   • Multi-shuttlecock detection and tracking")
        print("   • Maximum ball speed calculation before landing")
        print("   • Network camera MJPEG stream support")
        print("   • Draggable progress bar for video seeking")
        print("   • Intelligent mode switching (video/camera)")
        print("\n💡 RECOMMENDED WORKFLOW:")
        if self.network_mode:
            print("   1. Monitor network stream → 2. SPACE to pause buffering → 3. T to predict → 4. V for 3D")
        else:
            print("   1. Use progress bar to find trajectory → 2. SPACE to pause → 3. T to predict → 4. V for 3D")
        print(f"{'=' * 80}")

    def _handle_paused_state(self):
        """处理暂停状态 - 优化版本"""
        # 在暂停时仍需处理3D可视化和键盘事件
        self._handle_background_tasks()
        time.sleep(0.01)  # 小延迟避免CPU占用过高

    def _should_process_frame(self, current_time):
        """检查是否应该处理帧（帧率控制）"""
        elapsed_since_last_frame = current_time - self.last_frame_time
        target_frame_time = self.frame_time / self.playback_speed
        return elapsed_since_last_frame >= target_frame_time

    def _process_video_frame(self):
        """处理视频帧 - 增强版本，支持网络摄像头和进度条"""
        if self.network_mode:
            # 网络摄像头模式
            return self._process_network_camera_frame()
        else:
            # 本地视频文件模式
            return self._process_local_video_frame()
    
    def _process_network_camera_frame(self):
        """处理网络摄像头帧"""
        if not self.network_camera_manager:
            return False
        
        # 读取最新帧
        (ret1, ret2), (frame1, frame2) = self.network_camera_manager.read()
        
        if not ret1 or not ret2 or frame1 is None or frame2 is None:
            return True  # 网络流可能暂时无数据，继续运行
        
        # 更新时间基准
        self.last_frame_time = time.time()
        
        # 更新帧计数和FPS
        self.frame_count += 1
        self._update_fps()
        
        # 添加到缓冲区（只在缓冲状态且未处理时）
        if self.state == SystemState.BUFFERING and not self.processing_lock:
            self.buffered_processor.add_frame_pair(frame1, frame2, self.last_frame_time)
        
        # 保存当前帧用于显示
        self.current_frame1 = frame1.copy() if frame1 is not None else np.zeros((480, 640, 3), dtype=np.uint8)
        self.current_frame2 = frame2.copy() if frame2 is not None else np.zeros((480, 640, 3), dtype=np.uint8)
        
        return True
    
    def _process_local_video_frame(self):
        """处理本地视频文件帧"""
        # 检查是否有跳转请求
        if self.video_controls:
            seek_requested, seek_frame = self.video_controls.is_seek_requested()
            if seek_requested:
                self._seek_to_frame(seek_frame)
                print(f"📍 Seeking to frame {seek_frame}")
        
        # 读取帧
        ret1, frame1 = self.cap1.read()
        ret2, frame2 = self.cap2.read()

        if not ret1 or not ret2:
            return False

        # 更新当前帧索引
        self.current_frame_index += 1
        
        # 更新进度条
        if self.video_controls:
            self.video_controls.update_position(self.current_frame_index)

        # 更新时间基准
        self.last_frame_time = time.time()

        # 更新帧计数和FPS
        self.frame_count += 1
        self._update_fps()

        # 添加到缓冲区（只在缓冲状态且未处理时）
        if self.state == SystemState.BUFFERING and not self.processing_lock:
            self.buffered_processor.add_frame_pair(frame1, frame2, self.last_frame_time)

        # 保存当前帧用于显示
        self.current_frame1 = frame1 if frame1 is not None else np.zeros((480, 640, 3), dtype=np.uint8)
        self.current_frame2 = frame2 if frame2 is not None else np.zeros((480, 640, 3), dtype=np.uint8)

        return True
    
    def _seek_to_frame(self, frame_number):
        """跳转到指定帧"""
        if self.network_mode:
            print("⚠️ Seeking not supported in network camera mode")
            return
        
        if self.cap1 and self.cap2:
            self.cap1.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.cap2.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.current_frame_index = frame_number
            print(f"📍 Seeked to frame {frame_number}")

    def _update_display(self):
        """更新显示 - 增强版本，支持进度条"""
        if hasattr(self, 'current_frame1') and hasattr(self, 'current_frame2'):
            display_frame = self._create_display_frame(self.current_frame1, self.current_frame2)
            if display_frame is not None:
                # 在网络摄像头模式下，不显示进度条
                if self.network_mode or not self.video_controls:
                    cv2.imshow('Enhanced Badminton System - Live View', display_frame)
                else:
                    # 本地视频模式，添加进度条
                    combined_frame = self.video_controls.render_with_video(display_frame)
                    if combined_frame is not None:
                        cv2.imshow('Enhanced Badminton System - Live View', combined_frame)
                        # 设置鼠标回调（仅第一次）
                        self.video_controls.set_mouse_callback('Enhanced Badminton System - Live View')
                    else:
                        cv2.imshow('Enhanced Badminton System - Live View', display_frame)

    def _handle_background_tasks(self):
        """处理背景任务 - 优化版本"""
        # 1. 更新3D可视化（非阻塞）
        if self.interactive_3d_viz:
            try:
                self.interactive_3d_viz.update_if_visible()
            except Exception as e:
                print(f"⚠️ 3D visualization background update error: {e}")

        # 2. 处理键盘事件
        key = cv2.waitKey(1) & 0xFF
        if key != 255:  # 有按键
            self._handle_keyboard_input(key, time.time())

    def _monitor_performance(self):
        """性能监控"""
        # 可以在这里添加性能监控逻辑
        pass

    def _handle_keyboard_input(self, key, current_time):
        """统一的键盘事件处理 - 完全重写"""
        if key == 27:  # ESC - 退出
            self.running = False
            print("🚪 Exit requested by user")

        elif key == ord(' '):  # SPACE - 暂停/恢复播放
            self._handle_space_key()

        elif key == ord('t') or key == ord('T'):  # T - 触发预测
            self._handle_prediction_trigger(current_time)

        elif key == ord('p') or key == ord('P'):  # P - 恢复播放
            self._handle_resume_playback()

        elif key == ord('v') or key == ord('V'):  # V - 切换3D可视化
            self._handle_toggle_3d_visualization()

        elif key == ord('q') or key == ord('Q'):  # Q - 关闭3D窗口
            self._handle_close_3d_window()

        elif key == ord('d') or key == ord('D'):  # D - 打印调试统计
            self._handle_debug_statistics()

        elif key == ord('h') or key == ord('H'):  # H - 帮助
            UIHelper.display_help_screen()

        elif key == ord('r') or key == ord('R'):  # R - 重置系统
            self._handle_system_reset()

        elif key == ord('+') or key == ord('='):  # 增加播放速度
            self._handle_speed_change(1.2)

        elif key == ord('-') or key == ord('_'):  # 减少播放速度
            self._handle_speed_change(1 / 1.2)

        elif key == ord('0'):  # 重置到正常速度
            self._handle_speed_reset()

        # 3D可视化元素切换
        elif key in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5'), ord('6')]:
            self._handle_3d_element_toggle(key)

    def _handle_space_key(self):
        """处理空格键 - 暂停/恢复"""
        if self.paused:
            print("\n📋 Video is paused. Choose action:")
            print("   P - Resume playback")
            print("   T - Trigger trajectory analysis and prediction")
            print("   V - Open 3D visualization (if data available)")
        else:
            self.paused = True
            print("⏸️  Video PAUSED")
            print("   Press P to resume playback")
            print("   Press T to analyze current trajectory")

    def _handle_prediction_trigger(self, current_time):
        """处理预测触发 - 增强版本"""
        # 检查是否暂停
        if not self.paused:
            print("❌ Please pause video first (SPACE), then press T to predict")
            return

        # 检查系统状态
        if self.processing_lock or self.state != SystemState.BUFFERING:
            print("❌ System busy. Please wait for current operation to complete.")
            return

        # 检查冷却时间
        if current_time - self.last_prediction_time < self.prediction_cooldown:
            remaining_time = self.prediction_cooldown - (current_time - self.last_prediction_time)
            print(f"⏱️ Prediction cooldown: {remaining_time:.1f}s remaining")
            return

        # 检查缓冲区
        buffer_info = self.buffered_processor.get_buffer_info()
        if buffer_info['buffer_size'] < 10:
            print(f"❌ Insufficient buffered frames: {buffer_info['buffer_size']}/10 minimum")
            return

        # 设置处理锁和状态
        self.processing_lock = True
        self.last_prediction_time = current_time

        # 触发处理
        success = self.buffered_processor.trigger_processing(self._on_processing_complete)

        if success:
            self.state = SystemState.PROCESSING
            print("🎯 TRAJECTORY ANALYSIS STARTED...")
            print(f"   Processing {buffer_info['buffer_size']} buffered frames")
            print("   Please wait for prediction results...")
        else:
            print("❌ Failed to start processing")
            self.processing_lock = False

    def _handle_resume_playback(self):
        """处理恢复播放"""
        if self.paused:
            self.paused = False
            self.last_frame_time = time.time()
            print("▶️  Playback RESUMED")
        else:
            print("ℹ️  Video is already playing")

    def _handle_toggle_3d_visualization(self):
        """处理3D可视化切换"""
        if not self.interactive_3d_viz:
            print("❌ 3D visualizer not available")
            return

        if self.prediction_result or self.current_trajectory_data:
            try:
                self.interactive_3d_viz.toggle_window()
            except Exception as e:
                print(f"❌ Error toggling 3D visualization: {e}")
        else:
            print("❌ No prediction data available for 3D visualization")
            print("   Please run trajectory analysis first (T key when paused)")

    def _handle_close_3d_window(self):
        """处理关闭3D窗口"""
        if self.interactive_3d_viz and self.interactive_3d_viz.window_visible:
            try:
                self.interactive_3d_viz.close_window()
                print("✅ 3D visualization window closed")
            except Exception as e:
                print(f"⚠️ Error closing 3D window: {e}")
        else:
            print("ℹ️  3D visualization window is not currently open")

    def _handle_debug_statistics(self):
        """处理调试统计打印"""
        if self.interactive_3d_viz:
            try:
                self.interactive_3d_viz.print_debug_statistics()
            except Exception as e:
                print(f"❌ Error printing debug statistics: {e}")
        else:
            print("❌ 3D visualizer not available for debug statistics")

    def _handle_system_reset(self):
        """处理系统重置 - 完全重写"""
        if self.processing_lock or self.state == SystemState.PROCESSING:
            print("❌ Cannot reset while processing. Please wait.")
            return

        try:
            print("🔄 Performing COMPLETE system reset...")

            # 1. 关闭并重置3D可视化
            if self.interactive_3d_viz:
                if self.interactive_3d_viz.window_visible:
                    self.interactive_3d_viz.close_window()
                self.interactive_3d_viz.reset()

            # 2. 重置缓冲处理器
            if self.buffered_processor:
                self.buffered_processor.clear_buffer()
                # 强制重置处理状态
                if hasattr(self.buffered_processor, 'force_reset_processing_state'):
                    self.buffered_processor.force_reset_processing_state()
                else:
                    self.buffered_processor.is_processing = False

            # 3. 重置双目处理器
            if self.stereo_processor:
                self.stereo_processor.reset()

            # 4. 清理系统状态
            self.prediction_result = None
            self.current_trajectory_data = None
            self.state = SystemState.BUFFERING
            self.processing_lock = False

            # 5. 重置计数和时间
            self.last_prediction_time = 0
            self.last_frame_time = time.time()

            # 6. 重置播放状态
            if self.paused:
                self.paused = False
                print("▶️  Video playback resumed after reset")

            print("✅ COMPLETE system reset successful")
            print("📺 System ready for new trajectory analysis")
            print(f"🔄 Reset completed at {time.strftime('%H:%M:%S')} UTC")

        except Exception as e:
            print(f"⚠️ Error during system reset: {e}")
            # 强制重置关键状态
            self.state = SystemState.BUFFERING
            self.processing_lock = False
            if self.buffered_processor:
                self.buffered_processor.is_processing = False

    def _handle_speed_change(self, factor):
        """处理播放速度变化"""
        self.playback_speed = max(0.1, min(5.0, self.playback_speed * factor))
        print(f"⏩ Playback speed: {self.playback_speed:.1f}x")

    def _handle_speed_reset(self):
        """重置播放速度"""
        self.playback_speed = 1.0
        print("▶️  Playback speed reset to 1.0x")

    def _handle_3d_element_toggle(self, key):
        """处理3D元素切换"""
        if not self.interactive_3d_viz:
            print("❌ 3D visualizer not available")
            return

        element_map = {
            ord('1'): 'all_valid',
            ord('2'): 'prediction',
            ord('3'): 'rejected',
            ord('4'): 'low_quality',
            ord('5'): 'triangulation_failed',
            ord('6'): 'predicted_trajectory'
        }

        element_type = element_map.get(key)
        if element_type:
            try:
                self.interactive_3d_viz.toggle_visualization_elements(element_type)
            except Exception as e:
                print(f"❌ Error toggling 3D element: {e}")

    def _create_display_frame(self, frame1, frame2):
        """创建显示帧 - 完全重写"""
        if frame1 is None and frame2 is None:
            return None

        # 调整帧大小
        display_height = 480
        display_width = 640

        if frame1 is not None:
            frame1_resized = cv2.resize(frame1, (display_width, display_height))
        else:
            frame1_resized = np.zeros((display_height, display_width, 3), dtype=np.uint8)

        if frame2 is not None:
            frame2_resized = cv2.resize(frame2, (display_width, display_height))
        else:
            frame2_resized = np.zeros((display_height, display_width, 3), dtype=np.uint8)

        # 水平拼接主视频
        combined_frame = np.hstack([frame1_resized, frame2_resized])

        # 创建增强状态栏
        status_bar = self._create_enhanced_status_bar(combined_frame.shape[1])

        # 垂直拼接
        final_frame = np.vstack([combined_frame, status_bar])

        return final_frame

    def _create_enhanced_status_bar(self, width):
        """创建增强状态栏"""
        status_bar = np.zeros((160, width, 3), dtype=np.uint8)

        # 系统状态显示
        state_colors = {
            SystemState.BUFFERING: (0, 255, 0),
            SystemState.PROCESSING: (255, 255, 0),
            SystemState.PREDICTION_READY: (255, 165, 0),
            SystemState.PREDICTION_COMPLETE: (0, 255, 255)
        }

        state_color = state_colors.get(self.state, (255, 255, 255))
        state_text = f"State: {self.state.value.upper()}"
        if self.processing_lock:
            state_text += " [LOCKED]"

        cv2.putText(status_bar, state_text, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, state_color, 2)

        # 3D窗口状态
        if self.interactive_3d_viz:
            viz_status = "OPEN" if self.interactive_3d_viz.window_visible else "CLOSED"
            viz_color = (0, 255, 255) if self.interactive_3d_viz.window_visible else (100, 100, 100)
            cv2.putText(status_bar, f"3D Debug: {viz_status}", (350, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, viz_color, 2)

        # 时间和用户信息
        current_time_str = time.strftime('%H:%M:%S UTC')
        cv2.putText(status_bar, f"Time: {current_time_str}", (650, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.putText(status_bar, f"User: Liao-cyber360", (900, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # 缓冲区和性能信息
        if self.buffered_processor:
            buffer_info = self.buffered_processor.get_buffer_info()
            cv2.putText(status_bar, f"Buffer: {buffer_info['buffer_size']}/{buffer_info['max_size']} frames",
                        (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # 播放状态
        if self.paused:
            pause_text = "[⏸️  PAUSED - T:Predict P:Resume]"
            pause_color = (0, 255, 255)
        else:
            pause_text = f"[▶️  PLAYING - Speed: {self.playback_speed:.1f}x]"
            pause_color = (255, 255, 255)

        cv2.putText(status_bar, pause_text, (350, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, pause_color, 1)

        # FPS和帧信息
        cv2.putText(status_bar, f"FPS: {self.actual_fps:.1f} | Frame: {self.frame_count}",
                    (650, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # 预测统计
        if self.total_predictions > 0:
            success_rate = (self.successful_predictions / self.total_predictions) * 100
            cv2.putText(status_bar,
                        f"Predictions: {self.successful_predictions}/{self.total_predictions} ({success_rate:.1f}%)",
                        (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # 调试数据显示
        if self.current_trajectory_data and 'debug_data' in self.current_trajectory_data:
            debug_data = self.current_trajectory_data['debug_data']
            debug_text = f"Debug: V:{len(debug_data.get('all_valid_points', []))} P:{len(debug_data.get('prediction_points', []))} R:{len(debug_data.get('rejected_points', []))}"
            cv2.putText(status_bar, debug_text, (350, 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

        # 控制提示行1
        if self.paused:
            controls1 = "⏸️  PAUSED: T:Predict | P:Resume | V:3D | D:Debug | R:Reset | H:Help"
        else:
            controls1 = "▶️  PLAYING: SPACE:Pause | V:3D | D:Debug | R:Reset | H:Help"

        cv2.putText(status_bar, controls1, (10, 105),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        # 控制提示行2
        controls2 = "3D Controls: 1:AllValid 2:Prediction 3:Rejected 4:LowQuality 5:TriFailed 6:Trajectory"
        cv2.putText(status_bar, controls2, (10, 125),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 200, 255), 1)

        # 控制提示行3
        controls3 = "Playback: +/-:Speed 0:Reset | System: Q:Close3D ESC:Exit"
        cv2.putText(status_bar, controls3, (10, 145),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 200, 255), 1)

        return status_bar

    def _update_fps(self):
        """更新FPS计算"""
        current_time = time.time()
        self.fps_counter += 1

        if current_time - self.fps_prev_time >= 1.0:
            self.actual_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_prev_time = current_time

    def _cleanup(self):
        """清理系统资源 - 增强版本，支持网络摄像头"""
        print("\n🔄 Cleaning up system resources...")

        try:
            # 停止网络摄像头
            if self.network_camera_manager:
                self.network_camera_manager.stop()

            # 停止视频捕获
            if self.cap1:
                self.cap1.release()
            if self.cap2:
                self.cap2.release()

            # 停止3D可视化
            if self.interactive_3d_viz:
                self.interactive_3d_viz.stop()

            # 关闭OpenCV窗口
            cv2.destroyAllWindows()

            # 打印会话统计
            session_duration = time.time() - self.system_start_time
            print(f"\n📊 SESSION STATISTICS:")
            print(f"   Duration: {session_duration:.1f} seconds")
            print(f"   Frames processed: {self.frame_count}")
            print(f"   Predictions attempted: {self.total_predictions}")
            print(f"   Successful predictions: {self.successful_predictions}")
            if self.total_predictions > 0:
                success_rate = (self.successful_predictions / self.total_predictions) * 100
                print(f"   Success rate: {success_rate:.1f}%")
            
            mode_text = "Network Camera" if self.network_mode else "Local Video"
            print(f"   Mode: {mode_text}")

        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")

        print("✅ System cleanup complete")
        print(f"Session ended at: {time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"User: Liao-cyber360")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Enhanced Buffered Badminton Landing Prediction System v5.2 - Network Camera Support"
    )

    # 创建互斥组：本地视频或网络摄像头
    mode_group = parser.add_mutually_exclusive_group(required=True)
    
    # 本地视频模式
    mode_group.add_argument("--video-mode", action="store_true",
                           help="Use local video files")
    
    # 网络摄像头模式
    mode_group.add_argument("--camera-mode", action="store_true",
                           help="Use network cameras (MJPEG streams)")

    # 本地视频参数
    parser.add_argument("--video1", type=str,
                        help="Path to first camera video file (required for --video-mode)")
    parser.add_argument("--video2", type=str,
                        help="Path to second camera video file (required for --video-mode)")
    
    # 网络摄像头参数
    parser.add_argument("--camera-url1", type=str,
                        help="URL for first camera MJPEG stream (required for --camera-mode)")
    parser.add_argument("--camera-url2", type=str,
                        help="URL for second camera MJPEG stream (optional for --camera-mode)")
    parser.add_argument("--timestamp-header", type=str, default="X-Timestamp",
                        help="HTTP header name for timestamp (default: X-Timestamp)")
    
    # 标定参数
    parser.add_argument("--calibrated", action="store_true",
                        help="Skip calibration if cameras are already calibrated")
    parser.add_argument("--cam1_params", type=str, default=None,
                        help="Path to camera 1 parameters file")
    parser.add_argument("--cam2_params", type=str, default=None,
                        help="Path to camera 2 parameters file")

    return parser.parse_args()


def main():
    """主函数 - 增强版本，支持网络摄像头"""
    try:
        print("=" * 80)
        print("Enhanced Buffered Badminton Shuttlecock Landing Prediction System v5.2")
        print("Network Camera Support with Multi-Object Tracking")
        print("=" * 80)
        print(f"Session started at: {time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"Current User: Liao-cyber360")
        print(f"Features: Network cameras, Progress bar, Multi-shuttlecock tracking, Max speed calculation")
        print("=" * 80)

        args = parse_arguments()

        # 创建和初始化系统
        system = BufferedBadmintonSystem()
        
        # 根据模式初始化
        if args.video_mode:
            # 本地视频模式
            if not args.video1 or not args.video2:
                raise ValueError("--video1 and --video2 are required for --video-mode")
            
            # 验证视频文件
            if not os.path.exists(args.video1):
                raise FileNotFoundError(f"Video file not found: {args.video1}")
            if not os.path.exists(args.video2):
                raise FileNotFoundError(f"Video file not found: {args.video2}")

            print(f"📹 Local Video Mode:")
            print(f"   Camera 1: {args.video1}")
            print(f"   Camera 2: {args.video2}")
            
            system.initialize_system(args.video1, args.video2)
            
        elif args.camera_mode:
            # 网络摄像头模式
            if not args.camera_url1:
                raise ValueError("--camera-url1 is required for --camera-mode")
            
            print(f"🌐 Network Camera Mode:")
            print(f"   Camera 1: {args.camera_url1}")
            if args.camera_url2:
                print(f"   Camera 2: {args.camera_url2}")
            else:
                print(f"   Camera 2: Single camera mode")
            print(f"   Timestamp header: {args.timestamp_header}")
            
            system.initialize_network_cameras(
                args.camera_url1, 
                args.camera_url2, 
                args.timestamp_header
            )

        # 处理标定
        if args.calibrated and args.cam1_params and args.cam2_params:
            if os.path.exists(args.cam1_params) and os.path.exists(args.cam2_params):
                system.load_existing_calibration(args.cam1_params, args.cam2_params)
            else:
                print("⚠️ Warning: Calibration files not found, starting calibration...")
                if not system.calibration_mode():
                    raise RuntimeError("Calibration failed")
        else:
            print("🎯 Starting camera calibration process...")
            if not system.calibration_mode():
                raise RuntimeError("Calibration failed")

        print("\n" + "=" * 80)
        print("✅ SYSTEM READY - Starting Enhanced Video Processing")
        if system.network_mode:
            print("🌐 Network Camera Mode - Progress bar disabled")
            print("📡 Stream buffering active - Use pause for trajectory analysis")
        else:
            print("📹 Local Video Mode - Progress bar enabled")
            print("🎮 Drag progress bar to seek, pause for trajectory analysis")
        print("=" * 80)

        # 开始主处理循环
        system.start_processing()

    except KeyboardInterrupt:
        print(f"\n{'=' * 80}")
        print("⚠️ Program interrupted by user (Ctrl+C)")
        print(f"Session ended at: {time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"{'=' * 80}")
    except FileNotFoundError as e:
        print(f"❌ File Error: {e}")
    except RuntimeError as e:
        print(f"❌ Runtime Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error in main: {e}")
        import traceback
        traceback.print_exc()
        print(f"\nSession ended with error at: {time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    finally:
        cv2.destroyAllWindows()
        print("\n✅ All resources cleaned up successfully.")
        print("Thank you for using Enhanced Badminton Prediction System v5.2")


if __name__ == "__main__":
    main()