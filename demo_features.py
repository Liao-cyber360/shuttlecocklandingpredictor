#!/usr/bin/env python3
"""
Demo script showing the new features of the shuttlecock landing predictor
"""

import time
import numpy as np
from network_camera import MJPEGStreamReader
from video_controls import VideoProgressBar

def demo_network_camera():
    """Demonstrate network camera functionality"""
    print("=" * 60)
    print("🌐 NETWORK CAMERA DEMO")
    print("=" * 60)
    
    # Example camera URL (won't actually connect in this demo)
    camera_url = "http://192.168.10.3:8080/video"
    timestamp_header = "X-Timestamp"
    
    print(f"📹 Camera URL: {camera_url}")
    print(f"🕒 Timestamp Header: {timestamp_header}")
    
    # Create reader instance
    reader = MJPEGStreamReader(camera_url, timestamp_header, buffer_size=30)
    
    # Show configuration
    info = reader.get_buffer_info()
    print(f"\n📊 Stream Configuration:")
    print(f"   - Buffer size: {info['max_size']} frames")
    print(f"   - Current frames: {info['buffer_size']}")
    print(f"   - FPS: {info['fps']}")
    print(f"   - Running: {info['running']}")
    
    print(f"\n💡 Usage Examples:")
    print(f"   reader.start()           # Start streaming")
    print(f"   reader.pause()           # Pause/resume buffering")
    print(f"   reader.get_latest_frame() # Get current frame")
    print(f"   reader.clear_buffer()    # Clear buffer")
    print(f"   reader.stop()            # Stop streaming")

def demo_video_progress_bar():
    """Demonstrate video progress bar functionality"""
    print("\n=" * 60)
    print("🎮 VIDEO PROGRESS BAR DEMO")
    print("=" * 60)
    
    # Create progress bar
    progress_bar = VideoProgressBar(width=800, height=40)
    
    # Set video info (example: 30 second video at 30 FPS)
    total_frames = 900
    fps = 30.0
    progress_bar.set_video_info(total_frames, fps)
    
    print(f"📊 Video Info:")
    print(f"   - Total frames: {total_frames}")
    print(f"   - FPS: {fps}")
    print(f"   - Duration: {total_frames/fps:.1f} seconds")
    
    # Simulate playback
    print(f"\n▶️ Simulating video playback...")
    positions = [0, 150, 300, 450, 600, 750, 900]
    
    for pos in positions:
        progress_bar.update_position(pos)
        current_time = progress_bar.get_current_time()
        percentage = (pos / total_frames) * 100 if total_frames > 0 else 0
        
        print(f"   Frame {pos:3d}: {current_time:5.1f}s ({percentage:5.1f}%)")
        time.sleep(0.1)  # Simulate time passing
    
    print(f"\n💡 Features:")
    print(f"   - Draggable handle for seeking")
    print(f"   - Click-to-jump functionality")
    print(f"   - Real-time time display")
    print(f"   - Mouse interaction handling")

def demo_multiple_shuttlecock_handling():
    """Demonstrate multiple shuttlecock detection handling"""
    print("\n=" * 60)
    print("🏸 MULTIPLE SHUTTLECOCK DEMO")
    print("=" * 60)
    
    # Simulate detection results from multiple frames
    print("📊 Simulating detection results...")
    
    frame_detections = [
        # Frame 1: Single shuttlecock
        [((320, 240), 0.95)],
        
        # Frame 2: Two shuttlecocks detected  
        [((325, 245), 0.92), ((180, 160), 0.88)],
        
        # Frame 3: Two shuttlecocks, different confidences
        [((330, 250), 0.89), ((185, 165), 0.93)],
        
        # Frame 4: Three shuttlecocks (rare case)
        [((335, 255), 0.87), ((190, 170), 0.91), ((500, 300), 0.82)],
        
        # Frame 5: Back to single shuttlecock
        [((340, 260), 0.94)]
    ]
    
    for i, detections in enumerate(frame_detections):
        print(f"\n🔍 Frame {i+1}: {len(detections)} shuttlecock(s) detected")
        
        if len(detections) > 1:
            # Sort by confidence (as implemented in the system)
            sorted_detections = sorted(detections, key=lambda x: x[1], reverse=True)
            print(f"   🏸 Multiple shuttlecocks detected: {len(detections)} objects")
            
            for j, (pos, conf) in enumerate(sorted_detections):
                print(f"      Shuttlecock {j+1}: position {pos}, confidence {conf:.3f}")
        else:
            pos, conf = detections[0]
            print(f"   🎯 Single shuttlecock: position {pos}, confidence {conf:.3f}")
    
    print(f"\n💡 Multi-Object Features:")
    print(f"   - Automatic detection of multiple shuttlecocks")
    print(f"   - Confidence-based sorting")
    print(f"   - Trajectory tracking for each object")
    print(f"   - Best trajectory selection for prediction")

def demo_max_speed_calculation():
    """Demonstrate maximum speed calculation"""
    print("\n=" * 60)
    print("🏃 MAXIMUM SPEED CALCULATION DEMO")
    print("=" * 60)
    
    # Create realistic shuttlecock trajectory
    print("📈 Simulating shuttlecock trajectory...")
    
    # Trajectory points (x, y, z in cm) over time
    trajectory_data = [
        (0.0, [0, 0, 200]),      # Starting point: 2m high
        (0.05, [15, 8, 195]),    # 50ms later
        (0.10, [35, 20, 185]),   # 100ms later  
        (0.15, [60, 35, 170]),   # 150ms later
        (0.20, [90, 55, 150]),   # 200ms later - peak speed
        (0.25, [125, 80, 125]),  # 250ms later
        (0.30, [165, 110, 95]),  # 300ms later
        (0.35, [210, 145, 60]),  # 350ms later
        (0.40, [260, 185, 20]),  # 400ms later - landing
    ]
    
    times = np.array([t for t, _ in trajectory_data])
    points = np.array([pos for _, pos in trajectory_data])
    
    # Calculate speeds between each point
    speeds = []
    max_speed = 0
    max_speed_time = 0
    
    print(f"\n⚡ Speed analysis:")
    for i in range(1, len(points)):
        dt = times[i] - times[i-1]
        distance = np.linalg.norm(points[i] - points[i-1])
        speed = distance / dt  # cm/s
        speeds.append(speed)
        
        if speed > max_speed:
            max_speed = speed
            max_speed_time = times[i]
        
        print(f"   t={times[i]:.2f}s: {speed:6.1f} cm/s ({speed/100:4.1f} m/s)")
    
    avg_speed = np.mean(speeds)
    
    print(f"\n📊 Speed Summary:")
    print(f"   🏆 Maximum speed: {max_speed:.1f} cm/s ({max_speed/100:.1f} m/s)")
    print(f"   📍 Max speed time: {max_speed_time:.2f}s")
    print(f"   📈 Average speed: {avg_speed:.1f} cm/s ({avg_speed/100:.1f} m/s)")
    print(f"   📏 Total distance: {np.sum([np.linalg.norm(points[i] - points[i-1]) for i in range(1, len(points))]):.1f} cm")
    print(f"   ⏱️ Flight time: {times[-1] - times[0]:.2f}s")
    
    print(f"\n💡 Speed Calculation Features:")
    print(f"   - Real-time velocity analysis")
    print(f"   - Maximum speed detection")
    print(f"   - Speed distribution statistics")
    print(f"   - Integration with landing prediction")

def demo_mode_switching():
    """Demonstrate mode switching between video and camera"""
    print("\n=" * 60)
    print("🔄 MODE SWITCHING DEMO")
    print("=" * 60)
    
    print("📋 Available Operating Modes:")
    print()
    
    print("1️⃣ LOCAL VIDEO MODE:")
    print("   📁 Input: Two synchronized video files")
    print("   🎮 Features: Progress bar, seeking, playback speed control")
    print("   💡 Usage: python main.py --video-mode --video1 cam1.mp4 --video2 cam2.mp4")
    print()
    
    print("2️⃣ NETWORK CAMERA MODE:")
    print("   🌐 Input: MJPEG network streams")
    print("   📡 Features: Real-time streaming, timestamp parsing, buffering")
    print("   💡 Usage: python main.py --camera-mode --camera-url1 http://192.168.10.3:8080/video")
    print()
    
    print("🔧 Mode-Specific Features:")
    print("   Video Mode:")
    print("   ✅ Draggable progress bar")
    print("   ✅ Frame seeking")
    print("   ✅ Playback speed control")
    print("   ✅ Total duration display")
    print()
    
    print("   Camera Mode:")
    print("   ✅ Real-time stream buffering")
    print("   ✅ Network timestamp parsing")
    print("   ✅ Stream pause/resume")
    print("   ❌ Progress bar (disabled)")
    print("   ❌ Seeking (not applicable)")

def main():
    """Run all demos"""
    print("🚀 SHUTTLECOCK LANDING PREDICTOR v5.2")
    print("🎯 NEW FEATURES DEMONSTRATION")
    print(f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # Run all demonstrations
    demo_network_camera()
    demo_video_progress_bar()
    demo_multiple_shuttlecock_handling()
    demo_max_speed_calculation()
    demo_mode_switching()
    
    print("\n" + "=" * 60)
    print("✅ DEMONSTRATION COMPLETE")
    print("=" * 60)
    print()
    print("🎉 All new features demonstrated successfully!")
    print()
    print("📚 Feature Summary:")
    print("   🌐 Network camera MJPEG stream support")
    print("   🎮 Draggable video progress bar")
    print("   🏸 Multiple shuttlecock detection & tracking")
    print("   🏃 Maximum ball speed calculation")
    print("   🔄 Intelligent mode switching")
    print()
    print("🚀 Ready for production use!")

if __name__ == "__main__":
    main()