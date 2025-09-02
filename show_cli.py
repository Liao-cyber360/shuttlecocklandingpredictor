#!/usr/bin/env python3
"""
Show the enhanced command line interface for the shuttlecock landing predictor
"""

import argparse

def show_help():
    """Show the enhanced command line help"""
    parser = argparse.ArgumentParser(
        description="Enhanced Buffered Badminton Landing Prediction System v5.2 - Network Camera Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

Local Video Mode:
  python main.py --video-mode --video1 camera1.mp4 --video2 camera2.mp4

Network Camera Mode:
  python main.py --camera-mode --camera-url1 http://192.168.10.3:8080/video

With Calibration:
  python main.py --video-mode --video1 cam1.mp4 --video2 cam2.mp4 \\
                 --calibrated --cam1_params cam1.yaml --cam2_params cam2.yaml

Dual Network Cameras:
  python main.py --camera-mode \\
                 --camera-url1 http://192.168.10.3:8080/video \\
                 --camera-url2 http://192.168.10.4:8080/video \\
                 --timestamp-header "X-Timestamp"

New Features in v5.2:
  🎮 Draggable progress bar for video seeking (video mode only)
  🏸 Multiple shuttlecock detection and tracking
  🏃 Maximum ball speed calculation before landing  
  🌐 Network camera MJPEG stream support with timestamps
        """
    )

    # Create mutually exclusive group: local video or network cameras
    mode_group = parser.add_mutually_exclusive_group(required=True)
    
    # Local video mode
    mode_group.add_argument("--video-mode", action="store_true",
                           help="Use local video files with progress bar controls")
    
    # Network camera mode
    mode_group.add_argument("--camera-mode", action="store_true",
                           help="Use network cameras (MJPEG streams) with real-time buffering")

    # Local video parameters
    parser.add_argument("--video1", type=str,
                        help="Path to first camera video file (required for --video-mode)")
    parser.add_argument("--video2", type=str,
                        help="Path to second camera video file (required for --video-mode)")
    
    # Network camera parameters
    parser.add_argument("--camera-url1", type=str,
                        help="URL for first camera MJPEG stream (required for --camera-mode)")
    parser.add_argument("--camera-url2", type=str,
                        help="URL for second camera MJPEG stream (optional for --camera-mode)")
    parser.add_argument("--timestamp-header", type=str, default="X-Timestamp",
                        help="HTTP header name for timestamp (default: X-Timestamp)")
    
    # Calibration parameters
    parser.add_argument("--calibrated", action="store_true",
                        help="Skip calibration if cameras are already calibrated")
    parser.add_argument("--cam1_params", type=str, default=None,
                        help="Path to camera 1 parameters file")
    parser.add_argument("--cam2_params", type=str, default=None,
                        help="Path to camera 2 parameters file")

    return parser

def main():
    """Display the enhanced command line interface"""
    print("=" * 80)
    print("🚀 Enhanced Shuttlecock Landing Predictor v5.2")
    print("Command Line Interface Preview")
    print("=" * 80)
    
    parser = show_help()
    parser.print_help()
    
    print("\n" + "=" * 80)
    print("📋 Key Changes in v5.2:")
    print("=" * 80)
    print("✅ Added mutually exclusive mode selection (--video-mode or --camera-mode)")
    print("✅ Network camera support with --camera-url1 and --camera-url2")
    print("✅ Configurable timestamp header with --timestamp-header")
    print("✅ Maintained backward compatibility for calibration parameters")
    print("✅ Enhanced help text with examples and feature descriptions")
    
    print("\n🎯 Usage Validation:")
    print("   Video mode requires: --video1 and --video2")
    print("   Camera mode requires: --camera-url1 (--camera-url2 optional)")
    print("   Progress bar: Enabled in video mode, disabled in camera mode")
    print("   All new features work in both modes where applicable")

if __name__ == "__main__":
    main()