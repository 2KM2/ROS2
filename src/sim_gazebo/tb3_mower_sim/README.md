# 智能割草机仿真环境

自定义割草机器人在 **1000 m² (40m × 25m)** 别墅草坪中的仿真环境。

## 机器人规格

| 参数 | 值 |
|------|------|
| 尺寸 | 750 × 550 × 280 mm |
| 重量 | ~16 kg |
| 驱动方式 | 四轮滑移转向 (skid-steer) |
| 最大速度 | 1.0 m/s |
| 割刀宽度 | 220 mm (模拟) |
| 传感器 | 360° LiDAR + 双目相机 + IMU |

### 传感器配置

| 传感器 | 话题 | 规格 |
|--------|------|------|
| 360° LiDAR | `/scan` | 720 采样, 12m 量程, 10Hz |
| 双目左相机 | `/stereo/left/image_raw` | 640×480, 15Hz, 80° FOV |
| 双目右相机 | `/stereo/right/image_raw` | 640×480, 15Hz, 120mm 基线 |
| IMU | `/imu` | 100Hz, 含高斯噪声 |
| 里程计 | `/odom` | 30Hz |

## 仿真场景

模拟真实别墅草坪，障碍物对应实际割草场景：

| 类型 | 元素 | 尺寸/说明 |
|------|------|-----------|
| 固定障碍 | 树木 ×4 | Φ20-40cm 树干 |
| 固定障碍 | 花坛 ×3 | L 形/圆形/长条形 |
| 固定障碍 | 围栏 | 1.2m 高木围栏 |
| 半固定 | 庭院桌椅 | 桌子 + 长椅 |
| 临时障碍 | 玩具球 | Φ16cm |
| 临时障碍 | 掉落树枝 | 1.2m 长 |
| 低矮障碍 | 洒水器头 ×2 | Φ10cm, 高 6cm |
| 低矮障碍 | 花园水管 | 5m 长 |
| 低矮障碍 | 边缘石 | 3m 长, 8cm 高 |
| 窄通道 | 花园拱门 | 1.0m 宽 |
| 窄通道 | 侧面走廊 | 0.6m 宽, 3m 长 |
| 基础设施 | 充电站 | 南门内侧 |
| 地面元素 | 沙坑 | 2m×2m |
| 地面元素 | 踏脚石 ×3 | Φ40cm |

## 前置条件

```bash
sudo apt install \
  ros-jazzy-ros-gz \
  ros-jazzy-nav2-bringup \
  ros-jazzy-slam-toolbox \
  ros-jazzy-teleop-twist-keyboard \
  ros-jazzy-xacro
```

## 编译

```bash
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select tb3_mower_sim
source install/setup.bash
```

## 启动

### 终端 1：Gazebo 仿真 + 割草机

```bash
ros2 launch tb3_mower_sim tb3_mower_sim.launch.py
```

### 终端 2：SLAM 建图

```bash
ros2 launch tb3_mower_sim tb3_slam.launch.py
```

### 终端 3：键盘遥控

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### 保存地图

```bash
ros2 run nav2_map_server map_saver_cli \
  -f ~/workspace/ROS2/maps/lawn_1000sqm \
  --ros-args -p use_sim_time:=true
```

### 导航

```bash
ros2 launch tb3_mower_sim tb3_navigation.launch.py \
  map:=$HOME/workspace/ROS2/maps/lawn_1000sqm.yaml
```

## 话题列表

```
/clock            - 仿真时钟
/cmd_vel          - 速度指令 (Twist)
/odom             - 里程计
/scan             - 360° 激光扫描
/imu              - 惯性测量单元
/stereo/left/image_raw  - 左目图像
/stereo/right/image_raw - 右目图像
/tf               - 坐标变换
/joint_states     - 关节状态
/map              - SLAM 生成的地图
```

## 坐标系

```
map → odom → base_footprint → base_link
                                ├── lidar_link
                                ├── imu_link
                                ├── camera_left_link → camera_left_optical
                                ├── camera_right_link → camera_right_optical
                                ├── front_left_wheel_link
                                ├── front_right_wheel_link
                                ├── rear_left_wheel_link
                                ├── rear_right_wheel_link
                                ├── cutter_deck_link
                                └── bumper_link
```
