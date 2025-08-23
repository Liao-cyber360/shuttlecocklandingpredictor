# Camera Live Feed Calibration Documentation

## 概述 (Overview)

本文档描述了新增的摄像头实时画面标定功能，该功能允许用户直接使用网络摄像头的实时画面进行羽毛球场地标定，而无需依赖预录制的视频文件。

This document describes the newly added camera live feed calibration functionality, which allows users to perform badminton court calibration directly using real-time network camera feeds without relying on pre-recorded video files.

## 新增功能 (New Features)

### 1. `BadmintonCalibrator.calibrate_from_camera()` 方法

**函数签名 (Function Signature):**
```python
def calibrate_from_camera(self, camera_manager, num_frames=20, preview_time=5.0):
    """
    使用摄像头实时画面进行标定
    
    参数:
        camera_manager: NetworkCameraManager实例
        num_frames: 用于检测的帧数 (默认: 20)
        preview_time: 预览时间(秒) (默认: 5.0)
    
    返回:
        bool: 标定是否成功
    """
```

**功能特点:**
- 实时摄像头画面预览
- 交互式角点选择
- 自动角点检测和聚类
- 兼容现有标定流程

### 2. `calibrate_cameras_from_live_feed()` 函数

**函数签名:**
```python
def calibrate_cameras_from_live_feed(camera_manager, output_dir, num_frames=20, preview_time=5.0):
    """
    对网络摄像头进行实时标定
    
    参数:
        camera_manager: NetworkCameraManager实例
        output_dir: 输出目录
        num_frames: 用于检测的帧数 (默认: 20)
        preview_time: 预览时间(秒) (默认: 5.0)
    
    返回:
        tuple: (extrinsic_file1, extrinsic_file2) 或 (None, None) 如果失败
    """
```

**功能特点:**
- 支持单摄像头和双摄像头模式
- 自动处理摄像头流管理
- 生成标准格式的标定文件

## 使用方法 (Usage)

### 1. 命令行使用 (Command Line Usage)

**单摄像头模式:**
```bash
python main.py --camera-mode \
                --camera-url1 http://192.168.1.100:8080/video
```

**双摄像头模式:**
```bash
python main.py --camera-mode \
                --camera-url1 http://192.168.1.100:8080/video \
                --camera-url2 http://192.168.1.101:8080/video
```

**使用已有标定参数:**
```bash
python main.py --camera-mode \
                --camera-url1 http://192.168.1.100:8080/video \
                --camera-url2 http://192.168.1.101:8080/video \
                --calibrated \
                --cam1_params ./calibration/camera1/extrinsic_parameters.yaml \
                --cam2_params ./calibration/camera2/extrinsic_parameters.yaml
```

### 2. 编程接口使用 (Programming Interface)

**单摄像头标定:**
```python
from network_camera import NetworkCameraManager
from calibration import BadmintonCalibrator

# 创建摄像头管理器
camera_manager = NetworkCameraManager("http://192.168.1.100:8080/video")
camera_manager.start()

# 创建标定器
calibrator = BadmintonCalibrator(
    camera_params_file="camera_intrinsic_params.yaml",
    yolo_model_path="yolo_court_model.pt"
)

# 执行标定
success = calibrator.calibrate_from_camera(
    camera_manager=camera_manager,
    num_frames=20,
    preview_time=5.0
)

# 清理资源
camera_manager.stop()
```

**双摄像头标定:**
```python
from network_camera import NetworkCameraManager
from calibration import calibrate_cameras_from_live_feed

# 创建双摄像头管理器
camera_manager = NetworkCameraManager(
    "http://192.168.1.100:8080/video",
    "http://192.168.1.101:8080/video"
)
camera_manager.start()

# 执行标定
extrinsic_file1, extrinsic_file2 = calibrate_cameras_from_live_feed(
    camera_manager=camera_manager,
    output_dir="./calibration_results",
    num_frames=20,
    preview_time=5.0
)

# 清理资源
camera_manager.stop()
```

## 标定流程 (Calibration Workflow)

### 步骤说明:

1. **🌐 启动摄像头流** - 建立与网络摄像头的连接
2. **📺 实时预览** - 显示摄像头画面供用户调整位置 (默认5秒)
3. **🎯 角点选择** - 用户右键点击选择场地四个角点
4. **📸 帧捕获** - 连续捕获多帧用于角点检测 (默认20帧)
5. **🔍 YOLO检测** - 在每一帧上运行YOLO角点检测
6. **🧮 角点聚类** - 使用聚类算法合并相近的角点
7. **📐 坐标匹配** - 将检测到的角点与3D场地坐标匹配
8. **🎲 参数计算** - 使用PnP算法计算摄像头外参
9. **📄 结果保存** - 保存标定结果到YAML文件
10. **✅ 结果显示** - 显示标定结果和场地线叠加

### 用户交互:

**预览阶段:**
- 观察摄像头画面，确保场地清晰可见
- 按空格键提前结束预览
- 按ESC键取消标定

**角点选择阶段:**
- 按顺序右键点击四个角点: 左下外角、右下外角、右上内角、左上内角
- 右键点击后会显示放大视图进行精确选择
- 在放大视图中左键点击精确位置
- 按空格键确认选择，按ESC键重新选择
- 选择错误可按ESC键重新开始

## 技术实现 (Technical Implementation)

### 核心组件:

1. **NetworkCameraManager**: 管理网络摄像头流
2. **BadmintonCalibrator**: 核心标定逻辑
3. **YOLO角点检测**: 自动检测场地角点
4. **角点聚类算法**: 合并相近的检测点
5. **PnP算法**: 计算摄像头外参

### 关键特性:

- **实时性**: 直接使用摄像头实时画面
- **鲁棒性**: 多帧检测和聚类提高准确性
- **兼容性**: 与现有视频标定流程完全兼容
- **灵活性**: 支持单/双摄像头配置
- **用户友好**: 直观的交互界面

## 系统要求 (System Requirements)

### 硬件要求:
- 网络摄像头支持MJPEG流输出
- 稳定的网络连接
- 足够的带宽支持视频流传输

### 软件要求:
- Python 3.7+
- OpenCV 4.0+
- ultralytics (YOLO)
- 现有的摄像头内参标定文件
- YOLO场地角点检测模型

### 环境配置:
- 良好的照明条件
- 清晰可见的场地线标记
- 摄像头稳定安装
- 场地完整覆盖

## 常见问题 (FAQ)

### Q: 标定失败如何解决？
A: 检查以下项目:
- 摄像头连接是否稳定
- 场地线是否清晰可见
- 照明条件是否足够
- YOLO模型是否正确加载
- 内参文件是否有效

### Q: 如何提高标定精度？
A: 建议:
- 增加捕获帧数 (num_frames)
- 确保场地角点清晰可见
- 手动选择角点时尽量精确
- 使用稳定的摄像头安装

### Q: 支持哪些摄像头类型？
A: 支持提供MJPEG流的网络摄像头，包括:
- IP摄像头
- USB摄像头(通过网络流软件)
- 手机摄像头(通过APP)

### Q: 标定结果如何验证？
A: 系统会自动:
- 显示场地线叠加验证准确性
- 保存标定参数供后续使用
- 提供详细的标定统计信息

## 示例和测试 (Examples and Testing)

项目中包含以下示例文件:

1. **`example_camera_calibration.py`** - 完整的使用示例
2. **`test_camera_calibration.py`** - 功能测试脚本

运行示例:
```bash
python example_camera_calibration.py
python test_camera_calibration.py
```

## 更新日志 (Changelog)

### v5.2 新增功能:
- ✅ 添加 `calibrate_from_camera()` 方法
- ✅ 添加 `calibrate_cameras_from_live_feed()` 函数
- ✅ 实时摄像头预览功能
- ✅ 交互式角点选择界面
- ✅ 多帧角点检测和聚类
- ✅ 与现有系统完全集成
- ✅ 支持单/双摄像头模式
- ✅ 完整的文档和示例

---

## 联系信息 (Contact)

如有问题或建议，请联系:
- 项目维护者: Liao-cyber360
- GitHub: https://github.com/Liao-cyber360/shuttlecocklandingpredictor