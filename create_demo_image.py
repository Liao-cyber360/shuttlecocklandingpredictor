#!/usr/bin/env python3
"""
GUI界面结构可视化演示
GUI Interface Structure Visualization Demo
"""

import cv2
import numpy as np

def create_interface_demo():
    """创建界面结构演示图"""
    
    # 创建画布
    width, height = 1200, 800
    demo_img = np.ones((height, width, 3), dtype=np.uint8) * 240
    
    # 颜色定义
    blue = (255, 200, 100)
    green = (100, 255, 100)
    orange = (100, 165, 255)
    red = (100, 100, 255)
    black = (0, 0, 0)
    white = (255, 255, 255)
    gray = (128, 128, 128)
    
    # 标题
    cv2.putText(demo_img, "Shuttlecock Landing Predictor v6.0 - GUI Interface", 
                (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, black, 2)
    cv2.putText(demo_img, "System-Level Refactor - Mode Selection Interface", 
                (50, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, gray, 2)
    
    # 界面1: 模式选择
    cv2.rectangle(demo_img, (50, 100), (280, 280), blue, 2)
    cv2.putText(demo_img, "1. Mode Selection", (60, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, black, 2)
    cv2.putText(demo_img, "O Local Video", (70, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, black, 1)
    cv2.putText(demo_img, "O Network Camera", (70, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, black, 1)
    cv2.putText(demo_img, "[Confirm]", (180, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.5, white, 1)
    cv2.rectangle(demo_img, (160, 235), (240, 265), blue, -1)
    
    # 箭头1
    cv2.arrowedLine(demo_img, (290, 190), (330, 190), black, 2)
    
    # 界面2: 设置界面
    cv2.rectangle(demo_img, (340, 100), (570, 380), green, 2)
    cv2.putText(demo_img, "2. Settings Interface", (350, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, black, 2)
    
    # 标签页
    tabs = ["Input", "Camera", "Physics", "Detection"]
    for i, tab in enumerate(tabs):
        x = 350 + i * 55
        color = green if i == 0 else gray
        cv2.rectangle(demo_img, (x, 135), (x+50, 155), color, -1)
        cv2.putText(demo_img, tab, (x+5, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.35, white, 1)
    
    # 设置内容
    settings_text = [
        "Video1: /path/to/video1.mp4",
        "Video2: /path/to/video2.mp4",
        "",
        "Physics Parameters:",
        "- Mass: 5.1g",
        "- Gravity: 9.81 m/s²",
        "- Aero Length: 0.5m",
        "",
        "Detection Parameters:",
        "- Buffer Size: 20",
        "- Polar Threshold: 5.0",
        "- Landing Threshold: 5"
    ]
    
    for i, text in enumerate(settings_text):
        cv2.putText(demo_img, text, (355, 180 + i * 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, black, 1)
    
    cv2.rectangle(demo_img, (480, 350), (560, 370), green, -1)
    cv2.putText(demo_img, "[Next]", (495, 365), cv2.FONT_HERSHEY_SIMPLEX, 0.5, white, 1)
    
    # 箭头2
    cv2.arrowedLine(demo_img, (580, 240), (620, 240), black, 2)
    
    # 界面3: 标定界面
    cv2.rectangle(demo_img, (630, 100), (860, 300), orange, 2)
    cv2.putText(demo_img, "3. Calibration", (640, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, black, 2)
    cv2.putText(demo_img, "Camera Calibration", (645, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, black, 1)
    cv2.putText(demo_img, "Instructions:", (645, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.5, black, 1)
    cv2.putText(demo_img, "- Select court corners", (650, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.4, black, 1)
    cv2.putText(demo_img, "- Auto calibration", (650, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.4, black, 1)
    
    # 进度条
    cv2.rectangle(demo_img, (645, 230), (845, 245), gray, 1)
    cv2.rectangle(demo_img, (645, 230), (745, 245), orange, -1)
    cv2.putText(demo_img, "Progress: 50%", (645, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.4, black, 1)
    
    cv2.rectangle(demo_img, (770, 270), (850, 290), orange, -1)
    cv2.putText(demo_img, "[Complete]", (775, 285), cv2.FONT_HERSHEY_SIMPLEX, 0.4, white, 1)
    
    # 箭头3
    cv2.arrowedLine(demo_img, (870, 200), (910, 200), black, 2)
    
    # 界面4: 播放界面
    cv2.rectangle(demo_img, (920, 100), (1150, 380), red, 2)
    cv2.putText(demo_img, "4. Video Playback", (930, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, black, 2)
    
    # 双摄像头画面
    cv2.rectangle(demo_img, (935, 140), (1025, 200), gray, 1)
    cv2.putText(demo_img, "Camera 1", (950, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.4, black, 1)
    
    cv2.rectangle(demo_img, (1040, 140), (1130, 200), gray, 1)
    cv2.putText(demo_img, "Camera 2", (1055, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.4, black, 1)
    
    # 进度条（仅视频模式）
    cv2.putText(demo_img, "Progress Bar (Video Mode Only):", (935, 225), cv2.FONT_HERSHEY_SIMPLEX, 0.4, black, 1)
    cv2.rectangle(demo_img, (935, 235), (1135, 245), gray, 1)
    cv2.rectangle(demo_img, (935, 235), (1035, 245), red, -1)
    
    # 控制按钮
    buttons = ["Play/Pause", "Reset", "Predict"]
    for i, btn in enumerate(buttons):
        x = 935 + i * 70
        cv2.rectangle(demo_img, (x, 260), (x+65, 280), red, -1)
        cv2.putText(demo_img, btn, (x+5, 275), cv2.FONT_HERSHEY_SIMPLEX, 0.35, white, 1)
    
    # 状态信息
    cv2.putText(demo_img, "Status: Ready for analysis...", (935, 305), cv2.FONT_HERSHEY_SIMPLEX, 0.4, black, 1)
    cv2.putText(demo_img, "Trajectory prediction active", (935, 325), cv2.FONT_HERSHEY_SIMPLEX, 0.4, black, 1)
    
    # 特性说明
    cv2.putText(demo_img, "Key Features:", (50, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.8, black, 2)
    features = [
        "• GUI Mode Selection (No CLI Arguments)",
        "• Comprehensive Parameter Settings",
        "• Integrated Calibration Interface", 
        "• Conditional Progress Bar Control",
        "• Real-time Physics Parameter Adjustment",
        "• All Detection Parameters Configurable"
    ]
    
    for i, feature in enumerate(features):
        cv2.putText(demo_img, feature, (70, 450 + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, black, 1)
    
    # 参数框
    cv2.rectangle(demo_img, (650, 420), (1150, 700), (200, 200, 200), 1)
    cv2.putText(demo_img, "Adjustable Parameters:", (660, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.6, black, 2)
    
    param_sections = [
        ("Physics:", ["Mass: 4.0-6.0g", "Gravity: 9.7-9.9 m/s²", "Aero: 0.1-2.0m"]),
        ("Detection:", ["Buffer: 5-50 frames", "Polar: 1.0-20.0", "Landing: 1-20"]),
        ("Camera:", ["Intrinsic params", "Calibration status"])
    ]
    
    y_offset = 460
    for section, params in param_sections:
        cv2.putText(demo_img, section, (660, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, black, 2)
        y_offset += 20
        for param in params:
            cv2.putText(demo_img, f"  • {param}", (670, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.4, black, 1)
            y_offset += 18
        y_offset += 10
    
    # 底部说明
    cv2.putText(demo_img, "System-Level Refactor: Complete workflow redesign with modern GUI interface", 
                (50, 750), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 50, 150), 2)
    cv2.putText(demo_img, "Usage: python main.py (GUI mode) | python main_original.py (Legacy CLI mode)", 
                (50, 780), cv2.FONT_HERSHEY_SIMPLEX, 0.5, gray, 1)
    
    return demo_img

def main():
    """创建并保存演示图"""
    demo_img = create_interface_demo()
    
    # 保存图片
    cv2.imwrite("gui_interface_demo.png", demo_img)
    print("GUI界面演示图已保存为: gui_interface_demo.png")
    print("GUI interface demo saved as: gui_interface_demo.png")
    
    # 显示图片（如果环境支持）
    try:
        cv2.imshow("GUI Interface Demo", demo_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except:
        print("无法显示图片，但已保存到文件")
        print("Cannot display image, but saved to file")

if __name__ == "__main__":
    main()