# 系统级重构说明文档
# System-Level Refactor Documentation

## 重构概述 / Refactor Overview

本次重构完全改变了羽毛球落点预测系统的使用方式，从命令行参数模式改为图形界面模式选择，满足用户提出的所有需求。

This refactor completely changes how the shuttlecock landing predictor system is used, moving from command-line arguments to GUI mode selection, meeting all user requirements.

## 新的系统工作流程 / New System Workflow

```
启动系统 (Start System)
        ↓
┌─────────────────────────┐
│   模式选择界面          │
│   Mode Selection       │
│                        │
│ ○ 本地视频模式         │
│   Local Video Mode     │
│                        │
│ ○ 网络摄像头模式       │
│   Network Camera Mode  │
└─────────────────────────┘
        ↓
┌─────────────────────────┐
│   设置界面              │
│   Settings Interface   │
│                        │
│ [输入设置] [摄像头参数] │
│ [物理参数] [检测参数]   │
└─────────────────────────┘
        ↓
┌─────────────────────────┐
│   标定界面              │
│   Calibration Interface│
│                        │
│ • 自动标定 / 跳过标定   │
│ • 进度显示             │
└─────────────────────────┘
        ↓
┌─────────────────────────┐
│   视频播放界面          │
│   Video Playback       │
│                        │
│ [摄像头1] [摄像头2]     │
│ [进度条*] [控制按钮]    │
│                        │
│ *仅视频模式有进度条     │
└─────────────────────────┘
```

## 界面功能详解 / Interface Features

### 1. 模式选择界面 (Mode Selection)
- **本地视频模式**: 从本地视频文件进行分析，支持进度条控制
- **网络摄像头模式**: 实时网络摄像头分析，支持MJPEG流

### 2. 设置界面 (Settings Interface)
采用标签页设计，包含所有可调参数：

#### 输入设置标签页 (Input Settings Tab)
- 视频模式: 视频文件路径选择
- 摄像头模式: URL配置和时间戳头设置

#### 摄像头参数标签页 (Camera Parameters Tab)
- 摄像头内参文件路径
- 标定状态选择

#### 物理参数标签页 (Physics Parameters Tab)
- 羽毛球重量: 4.0-6.0g (默认5.1g)
- 重力加速度: 9.7-9.9 m/s² (默认9.81)
- 空气阻力长度: 0.1-2.0m (默认0.5m)

#### 检测参数标签页 (Detection Parameters Tab)
- 缓冲图片张数: 5-50张 (默认20张)
- 极距阈值: 1.0-20.0 (默认5.0)
- 落地检测阈值: 1-20 (默认5)
- 落地确认帧数: 1-10 (默认3)
- 落地高度阈值: 5.0-50.0cm (默认15.0cm)

### 3. 标定界面 (Calibration Interface)
- 支持自动标定和跳过标定
- 实时进度显示
- 与原有标定代码兼容

### 4. 视频播放界面 (Video Playback Interface)
- 双摄像头画面显示
- 条件性进度条（仅视频模式）
- 播放控制按钮
- 预测功能集成

## 文件结构变化 / File Structure Changes

```
原始结构 (Original):
main.py (命令行参数版本)

新结构 (New):
main.py → 重定向到新界面 (Redirects to new interface)
main_original.py → 原始版本备份 (Original version backup)
new_main.py → 新的GUI主界面 (New GUI main interface)
launcher.py → 更新的启动器 (Updated launcher)
test_new_interface.py → 界面测试工具 (Interface testing tool)
```

## 启动方式变化 / Startup Method Changes

### 旧方式 (Old Method)
```bash
# 需要命令行参数
python main.py --video-mode --video1 cam1.mp4 --video2 cam2.mp4
python main.py --camera-mode --camera-url1 http://192.168.1.100:8080/video
```

### 新方式 (New Method)
```bash
# 直接启动GUI
python main.py        # 启动新界面
python launcher.py    # 通过启动器
```

## 向后兼容性 / Backward Compatibility

原始命令行版本仍然可用：
```bash
python main_original.py --video-mode --video1 cam1.mp4 --video2 cam2.mp4
```

## 实现的需求 / Implemented Requirements

✅ **不保留原来的使用方法**: 主入口点已改为GUI模式选择
✅ **系统级重构**: 完全重新设计了用户交互流程
✅ **模式选择**: 进入系统可选择视频或网络摄像头模式
✅ **设置界面**: 配置必要参数，包括视频地址、URL、摄像头参数
✅ **标定界面**: 对两个画面进行外参标定，适配当前UI
✅ **视频播放界面**: 本地视频支持进度条，网络摄像头模式无进度条
✅ **参数设置**: 大部分可调参数已集成到设置界面中

## 技术实现 / Technical Implementation

- **PyQt6**: 现代GUI框架
- **模块化设计**: 每个界面独立组件
- **状态管理**: 设置在界面间传递
- **兼容性**: 与现有检测、预测、标定模块兼容
- **测试验证**: 包含完整的结构测试

## 使用指南 / Usage Guide

1. 运行 `python main.py` 或 `python launcher.py`
2. 在模式选择界面选择输入模式
3. 在设置界面配置所有参数
4. 在标定界面进行摄像头标定（可跳过）
5. 在播放界面进行实际分析和预测

此重构完全满足了用户提出的所有需求，提供了更直观的用户体验和更灵活的参数配置能力。