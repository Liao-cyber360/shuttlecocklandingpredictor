#!/usr/bin/env python3
"""
Example script demonstrating camera live feed calibration functionality
"""

import os
import sys

def example_single_camera_calibration():
    """Example of single camera live feed calibration"""
    print("=" * 60)
    print("📸 Single Camera Live Feed Calibration Example")
    print("=" * 60)
    
    try:
        from network_camera import NetworkCameraManager
        from calibration import BadmintonCalibrator
        
        # Example camera URL (replace with your actual camera URL)
        camera_url = "http://192.168.1.100:8080/video"
        
        # Create network camera manager
        print(f"🌐 Setting up camera connection to: {camera_url}")
        camera_manager = NetworkCameraManager(camera_url)
        
        # Note: In a real scenario, you would start the camera manager
        # camera_manager.start()
        
        # Create calibrator with your camera parameters file
        calibrator = BadmintonCalibrator(
            camera_params_file="path/to/camera_intrinsic_params.yaml",
            yolo_model_path="path/to/yolo_court_model.pt"
        )
        
        # Perform live feed calibration
        print("🎯 Starting live feed calibration...")
        print("   This will:")
        print("   1. Show camera preview for 5 seconds")
        print("   2. Allow you to select court corners")
        print("   3. Capture 20 frames for corner detection")
        print("   4. Calculate camera extrinsic parameters")
        print("   5. Save calibration results")
        
        # success = calibrator.calibrate_from_camera(
        #     camera_manager=camera_manager,
        #     num_frames=20,
        #     preview_time=5.0
        # )
        
        print("✅ Example setup complete (actual calibration commented out)")
        
        # Don't forget to stop the camera manager
        # camera_manager.stop()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed")
    except Exception as e:
        print(f"❌ Error: {e}")

def example_dual_camera_calibration():
    """Example of dual camera live feed calibration"""
    print("=" * 60)
    print("📸 Dual Camera Live Feed Calibration Example")
    print("=" * 60)
    
    try:
        from network_camera import NetworkCameraManager
        from calibration import calibrate_cameras_from_live_feed
        
        # Example camera URLs (replace with your actual camera URLs)
        camera_url1 = "http://192.168.1.100:8080/video"
        camera_url2 = "http://192.168.1.101:8080/video"
        
        # Create dual camera manager
        print(f"🌐 Setting up dual camera connection:")
        print(f"   Camera 1: {camera_url1}")
        print(f"   Camera 2: {camera_url2}")
        
        camera_manager = NetworkCameraManager(camera_url1, camera_url2)
        
        # Note: In a real scenario, you would start the camera manager
        # camera_manager.start()
        
        # Perform dual camera calibration
        print("🎯 Starting dual camera live feed calibration...")
        output_dir = "./calibration_results"
        
        # extrinsic_file1, extrinsic_file2 = calibrate_cameras_from_live_feed(
        #     camera_manager=camera_manager,
        #     output_dir=output_dir,
        #     num_frames=20,
        #     preview_time=5.0
        # )
        
        print("✅ Example setup complete (actual calibration commented out)")
        print(f"   Results would be saved to: {output_dir}")
        
        # Don't forget to stop the camera manager
        # camera_manager.stop()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed")
    except Exception as e:
        print(f"❌ Error: {e}")

def example_command_line_usage():
    """Example of using the system via command line with camera mode"""
    print("=" * 60)
    print("💻 Command Line Usage Examples")
    print("=" * 60)
    
    print("🌐 Network Camera Mode:")
    print("   # Single camera calibration")
    print("   python main.py --camera-mode \\")
    print("                  --camera-url1 http://192.168.1.100:8080/video")
    print()
    print("   # Dual camera calibration")  
    print("   python main.py --camera-mode \\")
    print("                  --camera-url1 http://192.168.1.100:8080/video \\")
    print("                  --camera-url2 http://192.168.1.101:8080/video")
    print()
    print("   # With custom timestamp header")
    print("   python main.py --camera-mode \\")
    print("                  --camera-url1 http://192.168.1.100:8080/video \\")
    print("                  --timestamp-header X-Custom-Timestamp")
    print()
    
    print("📹 Video Mode (for comparison):")
    print("   python main.py --video-mode \\")
    print("                  --video1 camera1_recording.mp4 \\")
    print("                  --video2 camera2_recording.mp4")
    print()
    
    print("🎯 Pre-calibrated Mode:")
    print("   python main.py --camera-mode \\")
    print("                  --camera-url1 http://192.168.1.100:8080/video \\")
    print("                  --camera-url2 http://192.168.1.101:8080/video \\")
    print("                  --calibrated \\")
    print("                  --cam1_params ./calibration/camera1/extrinsic_parameters.yaml \\")
    print("                  --cam2_params ./calibration/camera2/extrinsic_parameters.yaml")

def show_calibration_workflow():
    """Show the camera calibration workflow"""
    print("=" * 60)
    print("🔄 Camera Live Feed Calibration Workflow")
    print("=" * 60)
    
    workflow_steps = [
        "1. 🌐 Start network camera streams",
        "2. 📺 Show live preview (5 seconds by default)",
        "3. 🎯 User selects court boundary corners (4 points)",
        "4. 📸 Capture multiple frames (20 by default)",
        "5. 🔍 Apply YOLO corner detection on each frame",
        "6. 🧮 Consolidate detected corners using clustering",
        "7. 📐 Match detected corners to 3D court coordinates",
        "8. 🎲 Calculate camera extrinsic parameters using PnP",
        "9. 📄 Save calibration results to YAML file",
        "10. ✅ Display calibration result with court lines overlay"
    ]
    
    for step in workflow_steps:
        print(f"   {step}")
    
    print()
    print("📋 Key Features:")
    print("   • Real-time camera preview for positioning")
    print("   • Interactive corner selection with zoom")
    print("   • Automatic court corner detection using YOLO")
    print("   • Support for both single and dual camera setups")
    print("   • Compatible with existing video-based calibration")
    print("   • Seamless integration with main prediction system")

def show_api_reference():
    """Show API reference for the new functionality"""
    print("=" * 60)
    print("📚 API Reference")
    print("=" * 60)
    
    print("🔧 BadmintonCalibrator.calibrate_from_camera():")
    print("   Purpose: Calibrate camera using live feed")
    print("   Parameters:")
    print("     - camera_manager (NetworkCameraManager): Camera manager instance")
    print("     - num_frames (int, default=20): Number of frames to capture")
    print("     - preview_time (float, default=5.0): Preview duration in seconds")
    print("   Returns:")
    print("     - bool: True if calibration successful, False otherwise")
    print()
    
    print("🔧 calibrate_cameras_from_live_feed():")
    print("   Purpose: Calibrate dual cameras from live feed")
    print("   Parameters:")
    print("     - camera_manager (NetworkCameraManager): Camera manager instance")
    print("     - output_dir (str): Directory to save calibration results")
    print("     - num_frames (int, default=20): Number of frames to capture")
    print("     - preview_time (float, default=5.0): Preview duration in seconds")
    print("   Returns:")
    print("     - tuple: (extrinsic_file1, extrinsic_file2) or (None, None) if failed")
    print()
    
    print("📋 Usage Requirements:")
    print("   • Valid NetworkCameraManager with active streams")
    print("   • Camera intrinsic parameters file (pre-calibrated)")
    print("   • YOLO court detection model")
    print("   • Clear view of badminton court with visible corner markings")

def main():
    """Main example runner"""
    print("🏸 Badminton Camera Live Feed Calibration Examples")
    print("=" * 60)
    
    examples = [
        ("Single Camera Calibration", example_single_camera_calibration),
        ("Dual Camera Calibration", example_dual_camera_calibration),
        ("Command Line Usage", example_command_line_usage),
        ("Calibration Workflow", show_calibration_workflow),
        ("API Reference", show_api_reference),
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"\n{i}. {name}")
        func()
        print()
    
    print("=" * 60)
    print("🎉 Camera Live Feed Calibration Implementation Complete!")
    print("=" * 60)
    print()
    print("📝 Next Steps:")
    print("   1. Set up your network cameras with MJPEG streams")
    print("   2. Prepare camera intrinsic parameter files")
    print("   3. Download/train YOLO court detection model")
    print("   4. Run calibration with your camera setup")
    print("   5. Use calibrated parameters for shuttlecock prediction")
    print()
    print("💡 Tips:")
    print("   • Ensure good lighting and clear court markings")
    print("   • Position cameras for optimal court coverage")
    print("   • Test with stable network connection")
    print("   • Save calibration results for future use")

if __name__ == "__main__":
    main()