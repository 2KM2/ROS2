# 智能割草机仿真 —— 从零到覆盖路径规划完整教程

本教程将带你从环境搭建开始，逐步学习 ROS 2 机器人仿真的核心概念，最终实现割草机在 1000m² 草坪中的自主建图与导航。

---

## 目录

1. [环境准备](#1-环境准备)
2. [理解机器人模型 (URDF)](#2-理解机器人模型-urdf)
3. [启动 Gazebo 仿真](#3-启动-gazebo-仿真)
4. [理解坐标系与 TF](#4-理解坐标系与-tf)
5. [传感器数据详解](#5-传感器数据详解)
6. [手动遥控与运动学](#6-手动遥控与运动学)
7. [SLAM 建图](#7-slam-建图)
8. [Nav2 自主导航](#8-nav2-自主导航)
9. [覆盖路径规划（割草模式）](#9-覆盖路径规划割草模式)
10. [进阶：多传感器融合避障](#10-进阶多传感器融合避障)

---

## 1. 环境准备

### 1.1 系统要求

- Ubuntu 24.04 (Noble)
- ROS 2 Jazzy
- Gazebo Sim (Harmonic)

### 1.2 安装依赖

```bash
# 如果还没安装 ROS 2 Jazzy，运行项目提供的脚本：
cd ~/workspace/ROS2
./scripts/install_dependencies.sh

# 安装本仿真包的额外依赖
sudo apt install -y \
  ros-jazzy-ros-gz \
  ros-jazzy-xacro \
  ros-jazzy-slam-toolbox \
  ros-jazzy-nav2-bringup \
  ros-jazzy-teleop-twist-keyboard \
  ros-jazzy-tf2-tools \
  ros-jazzy-rqt-graph \
  ros-jazzy-rqt-tf-tree
```

### 1.3 编译工作空间

```bash
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select tb3_mower_sim
source install/setup.bash
```

> **提示**：`--symlink-install` 让 config/launch/urdf 文件以软链接方式安装，
> 修改源码后无需重新编译即可生效。

### 1.4 验证安装

```bash
# 确认包能被找到
ros2 pkg prefix tb3_mower_sim

# 确认 URDF 能正确展开
xacro $(ros2 pkg prefix tb3_mower_sim)/share/tb3_mower_sim/urdf/mower.urdf.xacro | head -20
```

---

## 2. 理解机器人模型 (URDF)

### 2.1 什么是 URDF

URDF (Unified Robot Description Format) 用 XML 描述机器人的：
- **Link**：刚体部件（有质量、惯性、外观、碰撞体）
- **Joint**：连接两个 Link 的关节（固定、旋转、平移等）
- **Sensor**：通过 Gazebo 插件附加传感器

### 2.2 割草机模型结构

打开 `urdf/mower.urdf.xacro`，其结构如下：

```
base_footprint (虚拟地面接触点)
  └── base_link (车体: 750×550×280mm, 16kg)
        ├── front_left_wheel_link  (连续旋转关节)
        ├── front_right_wheel_link
        ├── rear_left_wheel_link
        ├── rear_right_wheel_link
        ├── cutter_deck_link (割刀盘, 固定)
        ├── bumper_link (前保险杠, 固定)
        ├── lidar_link (360°雷达, 固定)
        │     └── [Gazebo gpu_lidar sensor]
        ├── imu_link (惯性单元, 固定)
        │     └── [Gazebo imu sensor]
        ├── camera_left_link (左目, 固定)
        │     ├── camera_left_optical (光学坐标系)
        │     └── [Gazebo camera sensor]
        └── camera_right_link (右目, 固定)
              ├── camera_right_optical (光学坐标系)
              └── [Gazebo camera sensor]
```

### 2.3 关键概念解析

#### 惯性矩阵

每个 Link 都需要正确的惯性参数，否则物理仿真会不稳定：

```xml
<!-- 长方体惯性公式 -->
<inertia
  ixx="mass*(y²+z²)/12"
  iyy="mass*(x²+z²)/12"
  izz="mass*(x²+y²)/12"/>
```

#### 差速驱动插件

```xml
<plugin filename="gz-sim-diff-drive-system" name="gz::sim::systems::DiffDrive">
  <!-- 左侧两轮 -->
  <left_joint>front_left_wheel_joint</left_joint>
  <left_joint>rear_left_wheel_joint</left_joint>
  <!-- 右侧两轮 -->
  <right_joint>front_right_wheel_joint</right_joint>
  <right_joint>rear_right_wheel_joint</right_joint>
  <!-- 轮距决定转弯半径 -->
  <wheel_separation>0.50</wheel_separation>
  <wheel_radius>0.08</wheel_radius>
</plugin>
```

**滑移转向原理**：左右两侧车轮差速旋转实现转弯。正向速度相同则直行，
一侧快一侧慢则弧线转弯，反向旋转则原地转向。

### 2.4 动手练习：修改参数

尝试修改以下参数并观察效果：

```bash
# 修改后不需要重新编译（symlink-install），只需重启仿真
```

| 参数 | 文件位置 | 效果 |
|------|---------|------|
| `wheel_radius` | urdf 第 10 行 | 轮子大小和速度比 |
| `track_width` | urdf 第 11 行 | 轮距：越大越稳定但转弯半径大 |
| `max_velocity` | urdf 最后的插件区 | 最大线速度 |
| LiDAR `samples` | urdf 传感器区 | 雷达分辨率 |

---

## 3. 启动 Gazebo 仿真

### 3.1 启动仿真世界

```bash
# 终端 1
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 launch tb3_mower_sim tb3_mower_sim.launch.py
```

你会看到：
1. Gazebo 窗口打开，显示绿色草坪、围栏、树木等
2. 4 秒后割草机出现在充电站附近（南门内侧）
3. RViz 窗口打开，显示机器人模型和激光扫描

### 3.2 理解 Launch 文件做了什么

`tb3_mower_sim.launch.py` 按顺序启动了：

```
1. Gazebo Sim       ← 物理仿真引擎 + 渲染
2. robot_state_publisher ← 读取 URDF，发布 /tf_static 和 /robot_description
3. ros_gz_bridge    ← Gazebo 话题 ↔ ROS 2 话题的桥梁
4. static_transform ← 传感器额外坐标系 TF
5. ros_gz_sim/create ← 在 Gazebo 世界中生成机器人
6. RViz             ← 可视化工具
```

### 3.3 检查系统状态

```bash
# 终端 2
source /opt/ros/jazzy/setup.bash
source ~/workspace/ROS2/install/setup.bash

# 查看所有活跃话题
ros2 topic list

# 查看节点图（谁在发布/订阅什么）
rqt_graph
```

预期话题列表：
```
/clock
/cmd_vel
/imu
/joint_states
/odom
/robot_description
/scan
/stereo/left/image_raw
/stereo/right/image_raw
/tf
/tf_static
```

### 3.4 无头模式（节省 GPU）

如果你的机器 GPU 不强，可以无头运行 Gazebo：

```bash
ros2 launch tb3_mower_sim tb3_mower_sim.launch.py headless:=true
```

这样只运行物理引擎，不做 3D 渲染，但传感器数据照常产生。

---

## 4. 理解坐标系与 TF

### 4.1 ROS 2 中的坐标系

机器人系统中有多个坐标系（frame），它们之间的变换关系通过 TF 树维护：

```
map          ← 全局地图坐标系（由 SLAM 或定位提供）
  └── odom   ← 里程计坐标系（连续但会漂移）
        └── base_footprint ← 机器人在地面的投影
              └── base_link ← 机器人本体
                    ├── lidar_link      ← 雷达安装位置
                    ├── camera_left_link ← 左目位置
                    └── ...
```

### 4.2 查看 TF 树

```bash
# 图形化查看完整 TF 树
ros2 run rqt_tf_tree rqt_tf_tree

# 或者命令行查看两个坐标系之间的变换
ros2 run tf2_ros tf2_echo odom base_footprint

# 查看雷达相对于机器人的位置
ros2 run tf2_ros tf2_echo base_link lidar_link
```

### 4.3 为什么需要 base_footprint？

- `base_link`：机器人本体中心，z 轴方向有偏移
- `base_footprint`：机器人在地面的正下方投影，z=0

导航栈需要 `base_footprint` 来做 2D 规划（忽略高度）。

### 4.4 动手练习：观察 TF

启动仿真后，用键盘控制机器人移动，同时观察：

```bash
# 实时打印 odom → base_footprint 的位姿变化
ros2 run tf2_ros tf2_echo odom base_footprint
```

你会看到 Translation 的 x、y 随运动变化，Rotation 的 yaw 随转向变化。

---

## 5. 传感器数据详解

### 5.1 360° LiDAR

```bash
# 查看话题信息
ros2 topic info /scan -v

# 查看单帧数据
ros2 topic echo /scan --once
```

关键字段：
- `angle_min / angle_max`：-π 到 +π（360°全向）
- `ranges[]`：720 个距离值（每 0.5° 一个采样）
- `range_min / range_max`：0.12m ~ 12.0m

**用途**：建图(SLAM)、避障、定位

### 5.2 IMU

```bash
ros2 topic echo /imu --once
```

关键字段：
- `angular_velocity`：三轴角速度 (rad/s)
- `linear_acceleration`：三轴线加速度 (m/s²)
- `orientation`：四元数姿态

**用途**：姿态估计、里程计融合、坡度检测

### 5.3 双目相机

```bash
# 查看左目图像信息
ros2 topic info /stereo/left/image_raw -v

# 用 RViz 的 Image 面板实时查看图像
# 或用 rqt_image_view
ros2 run rqt_image_view rqt_image_view
```

**双目原理**：两个相机相距 120mm（基线），同一物体在左右图像中的视差(disparity)与距离成反比：

```
距离 = 焦距 × 基线 / 视差
```

**用途**：深度估计、物体识别、视觉避障

### 5.4 里程计

```bash
ros2 topic echo /odom --once
```

关键字段：
- `pose.position`：累计位移 (x, y, z)
- `pose.orientation`：四元数朝向
- `twist.linear`：当前线速度
- `twist.angular`：当前角速度

**注意**：里程计会随时间漂移（轮子打滑、地面不平），所以需要 SLAM 来修正。

### 5.5 动手练习：数据可视化

在 RViz 中：
1. 添加 LaserScan 显示（红色激光点）
2. 移动机器人，观察激光点如何勾勒出障碍物轮廓
3. 添加 Image 显示，对比左右目的视差

---

## 6. 手动遥控与运动学

### 6.1 键盘遥控

```bash
# 终端 3
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

控制键：
```
   u    i    o        ← i:前进  u:左前  o:右前
   j    k    l        ← k:停止  j:左转  l:右转
   m    ,    .        ← ,:后退  m:左后  .:右后

q/z : 增加/减少线速度 (步进 10%)
w/x : 增加/减少角速度 (步进 10%)
```

**建议初始速度**：
- 线速度：0.2 m/s（慢速探索）
- 角速度：0.5 rad/s

### 6.2 理解 cmd_vel

`/cmd_vel` 话题使用 `geometry_msgs/msg/Twist` 消息：

```yaml
linear:
  x: 0.2   # 前进速度 (m/s)，负值为后退
  y: 0.0   # 差速机器人此项始终为 0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 0.3   # 旋转速度 (rad/s)，正值左转，负值右转
```

### 6.3 差速运动学

对于滑移转向机器人：

```
左轮速度 = (v - ω × L/2) / R
右轮速度 = (v + ω × L/2) / R

其中：
  v = 线速度 (linear.x)
  ω = 角速度 (angular.z)
  L = 轮距 (0.50m)
  R = 轮半径 (0.08m)
```

### 6.4 动手练习：画正方形

尝试用键盘让割草机走一个正方形：
1. 前进 2m（约 10 秒 @ 0.2m/s）
2. 原地左转 90°（约 3 秒 @ 0.5rad/s）
3. 重复 4 次

观察 `/odom` 中的位置是否回到起点（如果不在，这就是里程计漂移）。

---

## 7. SLAM 建图

### 7.1 什么是 SLAM

SLAM (Simultaneous Localization and Mapping)：在未知环境中同时建立地图并定位自身。

我们使用的 `slam_toolbox` 基于 **图优化 + 扫描匹配**：
1. 每帧激光扫描与之前的扫描匹配，确定相对位移
2. 构建位姿图 (pose graph)
3. 检测回环（回到走过的地方）并优化全局一致性

### 7.2 启动 SLAM

```bash
# 终端 2（确保仿真已启动）
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 launch tb3_mower_sim tb3_slam.launch.py
```

### 7.3 验证 SLAM 工作

```bash
# 检查 /map 话题是否有数据
ros2 topic info /map
ros2 topic hz /map

# 检查 map → odom 变换
ros2 run tf2_ros tf2_echo map odom
```

在 RViz 中，将 Fixed Frame 设为 `map`，添加 Map 显示，你会看到地图随着机器人移动而逐渐扩大。

### 7.4 建图策略

**好的建图习惯**：
- 慢速移动（0.1-0.2 m/s）以获取清晰扫描
- 沿墙壁和障碍物边缘行驶
- 尽量形成**闭环**（回到走过的地方），这能大幅提升地图精度
- 避免快速旋转（会导致扫描畸变）

**建议路线**：
```
1. 从充电站出发，沿南围栏向右走
2. 到东围栏后向北
3. 沿北围栏向左
4. 到西围栏后向南回到起点（第一个闭环！）
5. 深入内部，绕过树木和花坛
6. 最后通过窄通道
```

### 7.5 SLAM 参数说明

`config/slam_params.yaml` 关键参数：

| 参数 | 值 | 作用 |
|------|------|------|
| `resolution` | 0.05 | 地图分辨率：5cm/格 |
| `max_laser_range` | 3.5 | 使用的最大激光距离 |
| `minimum_travel_distance` | 0.3 | 移动 30cm 才插入新扫描 |
| `minimum_travel_heading` | 0.3 | 转动 0.3rad 才插入新扫描 |
| `do_loop_closing` | true | 启用回环检测 |

### 7.6 保存地图

建图满意后：

```bash
mkdir -p ~/workspace/ROS2/maps

ros2 run nav2_map_server map_saver_cli \
  -f ~/workspace/ROS2/maps/lawn_1000sqm \
  --ros-args -p use_sim_time:=true
```

生成两个文件：
- `lawn_1000sqm.pgm`：灰度图像（白色=空闲，黑色=障碍，灰色=未知）
- `lawn_1000sqm.yaml`：地图元数据（分辨率、原点等）

### 7.7 动手练习：对比建图质量

1. 快速建图（高速、不回环）：观察地图错位和漂移
2. 慢速建图（低速、走闭环）：观察地图如何在回环时"跳"一下修正

---

## 8. Nav2 自主导航

### 8.1 Nav2 系统架构

```
                    ┌─────────────┐
                    │ BT Navigator │  ← 行为树调度
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
    ┌─────────────┐ ┌──────────┐ ┌───────────┐
    │   Planner   │ │Controller│ │ Behaviors │
    │  (全局路径) │ │ (局部跟踪)│ │ (恢复行为)│
    └──────┬──────┘ └────┬─────┘ └─────┬─────┘
           │             │             │
           ▼             ▼             ▼
    ┌─────────────┐ ┌──────────┐ ┌───────────┐
    │Global Costmap│ │Local     │ │ spin/backup│
    │  (静态地图) │ │ Costmap  │ │  /wait    │
    └─────────────┘ └──────────┘ └───────────┘
```

### 8.2 启动导航

确保你已经有保存好的地图，然后：

```bash
# 先关闭 SLAM（SLAM 和导航的 map→odom 会冲突）
# Ctrl+C 终止 SLAM 终端

# 启动导航
ros2 launch tb3_mower_sim tb3_navigation.launch.py \
  map:=$HOME/workspace/ROS2/maps/lawn_1000sqm.yaml
```

### 8.3 设置初始位姿

Nav2 启动后，机器人需要知道自己在地图上的位置：

1. 在 RViz 中点击工具栏的 **"2D Pose Estimate"**
2. 在地图上点击机器人的当前位置，拖动箭头指示朝向
3. 观察激光扫描点是否与地图墙壁对齐

### 8.4 发送导航目标

1. 在 RViz 中点击 **"Nav2 Goal"**（或 "2D Goal Pose"）
2. 在地图上点击目标位置，拖动箭头指示期望朝向
3. 观察全局路径（绿线）和机器人沿路径移动

### 8.5 代码发送目标

也可以用命令行发送导航目标：

```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 5.0, y: 5.0, z: 0.0}, orientation: {w: 1.0}}}}"
```

### 8.6 导航参数说明

`config/nav2_params.yaml` 关键部分：

| 组件 | 参数 | 作用 |
|------|------|------|
| controller | `max_vel_x: 0.22` | 导航最大速度 |
| controller | `max_vel_theta: 1.0` | 最大转向速度 |
| local_costmap | `robot_radius: 0.18` | 机器人半径（用于避障膨胀） |
| inflation | `inflation_radius: 0.55` | 障碍物膨胀半径 |
| planner | `tolerance: 0.5` | 到达目标的容差 |

> **注意**：我们的割草机实际尺寸是 750×550mm，但 Nav2 使用圆形近似。
> `robot_radius` 应设为 max(750, 550)/2 ≈ 0.375m。但目前设为 0.18m
> 是为了能通过窄通道。后续可以改为多边形 footprint 以更精确地表示机器形状。

### 8.7 动手练习：多点导航

```bash
# 使用 navigate_through_poses 发送多个途经点
ros2 action send_goal /navigate_through_poses nav2_msgs/action/NavigateThroughPoses \
  "{poses: [
    {header: {frame_id: 'map'}, pose: {position: {x: 5.0, y: 0.0}, orientation: {w: 1.0}}},
    {header: {frame_id: 'map'}, pose: {position: {x: 10.0, y: 5.0}, orientation: {w: 1.0}}},
    {header: {frame_id: 'map'}, pose: {position: {x: 0.0, y: 0.0}, orientation: {w: 1.0}}}
  ]}"
```

---

## 9. 覆盖路径规划（割草模式）

这是智能割草机的核心功能——如何高效地覆盖整片草坪。

### 9.1 覆盖路径算法分类

| 算法 | 原理 | 适用场景 |
|------|------|---------|
| 随机行走 | 遇障转随机角度 | 简单但效率低 |
| 弓字形 (Boustrophedon) | 平行往返条带 | 规则区域，效率最高 |
| 螺旋式 | 从外向内或从内向外 | 小区域或高草区 |
| 分区覆盖 | 先分解区域再逐区清扫 | 有障碍物的复杂区域 |

### 9.2 实现简单弓字形覆盖

创建一个 Python 节点来生成弓字形路径点：

```bash
mkdir -p ~/workspace/ROS2/src/sim_gazebo/tb3_mower_sim/scripts
```

创建 `scripts/boustrophedon_coverage.py`：

```python
#!/usr/bin/env python3
"""
弓字形覆盖路径生成器。
给定一个矩形区域和割刀宽度，生成往返条带路径并通过 Nav2 执行。
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateThroughPoses
from geometry_msgs.msg import PoseStamped
import math


class BoustrophedonCoverage(Node):
    def __init__(self):
        super().__init__('boustrophedon_coverage')

        # 参数
        self.declare_parameter('cut_width', 0.20)       # 割刀宽度 (m)
        self.declare_parameter('overlap', 0.05)         # 重叠量 (m)
        self.declare_parameter('area_x_min', -15.0)     # 覆盖区域 X 最小值
        self.declare_parameter('area_x_max', 15.0)      # 覆盖区域 X 最大值
        self.declare_parameter('area_y_min', -8.0)      # 覆盖区域 Y 最小值
        self.declare_parameter('area_y_max', 8.0)       # 覆盖区域 Y 最大值
        self.declare_parameter('speed', 0.3)            # 行驶速度

        self.cut_width = self.get_parameter('cut_width').value
        self.overlap = self.get_parameter('overlap').value
        self.x_min = self.get_parameter('area_x_min').value
        self.x_max = self.get_parameter('area_x_max').value
        self.y_min = self.get_parameter('area_y_min').value
        self.y_max = self.get_parameter('area_y_max').value

        self.nav_client = ActionClient(
            self, NavigateThroughPoses, 'navigate_through_poses')

        self.get_logger().info('等待 Nav2 导航服务...')
        self.nav_client.wait_for_server()
        self.get_logger().info('Nav2 已就绪，开始生成覆盖路径')

        self.execute_coverage()

    def generate_waypoints(self):
        """生成弓字形路径点列表。"""
        waypoints = []
        step = self.cut_width - self.overlap  # 每条线间距
        y = self.y_min
        direction = 1  # 1: 向 x_max 方向, -1: 向 x_min 方向
        strip_index = 0

        while y <= self.y_max:
            if direction == 1:
                x_start, x_end = self.x_min, self.x_max
            else:
                x_start, x_end = self.x_max, self.x_min

            # 条带起点
            waypoints.append((x_start, y, 0.0 if direction == 1 else math.pi))
            # 条带终点
            waypoints.append((x_end, y, 0.0 if direction == 1 else math.pi))

            y += step
            direction *= -1
            strip_index += 1

        self.get_logger().info(
            f'生成 {strip_index} 条割草带，共 {len(waypoints)} 个路径点')
        return waypoints

    def make_pose(self, x, y, yaw):
        """创建 PoseStamped 消息。"""
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        return pose

    def execute_coverage(self):
        """执行覆盖路径。"""
        waypoints = self.generate_waypoints()

        # Nav2 一次发送的途经点不宜过多，分批发送
        batch_size = 20
        for i in range(0, len(waypoints), batch_size):
            batch = waypoints[i:i + batch_size]
            goal = NavigateThroughPoses.Goal()
            goal.poses = [self.make_pose(x, y, yaw) for x, y, yaw in batch]

            self.get_logger().info(
                f'发送第 {i//batch_size + 1} 批路径点 '
                f'({len(batch)} 个点)')

            future = self.nav_client.send_goal_async(goal)
            rclpy.spin_until_future_complete(self, future)

            goal_handle = future.result()
            if not goal_handle.accepted:
                self.get_logger().error('导航目标被拒绝！')
                return

            result_future = goal_handle.get_result_async()
            rclpy.spin_until_future_complete(self, result_future)

            self.get_logger().info(f'第 {i//batch_size + 1} 批完成')

        self.get_logger().info('覆盖路径执行完毕！')


def main(args=None):
    rclpy.init(args=args)
    node = BoustrophedonCoverage()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 9.3 运行覆盖路径

```bash
# 确保导航栈已启动
# 然后运行覆盖节点
cd ~/workspace/ROS2/src/sim_gazebo/tb3_mower_sim
python3 scripts/boustrophedon_coverage.py \
  --ros-args \
  -p area_x_min:=-10.0 \
  -p area_x_max:=10.0 \
  -p area_y_min:=-5.0 \
  -p area_y_max:=5.0 \
  -p cut_width:=0.20
```

### 9.4 覆盖率计算

```
总面积 = (x_max - x_min) × (y_max - y_min)
条带数 = ceil(宽度 / (割刀宽度 - 重叠量))
理论覆盖率 = 条带数 × 割刀宽度 × 长度 / 总面积

对于 20m×10m 区域，割刀宽 0.20m，重叠 0.05m：
条带数 = ceil(10 / 0.15) = 67 条
总路程 = 67 × 20 = 1340m
工作时间 = 1340 / 0.3 ≈ 74 分钟（不含转弯）
```

### 9.5 进阶：处理障碍物区域

真实割草需要避开花坛等禁区。思路：

1. 在地图上标记"割草区"和"禁区"
2. 对割草区做 Boustrophedon 分解（在障碍物处分割为子区域）
3. 为每个子区域生成条带路径
4. 用 TSP (旅行商问题) 优化子区域访问顺序

---

## 10. 进阶：多传感器融合避障

### 10.1 为什么需要融合

| 传感器 | 优势 | 局限 |
|--------|------|------|
| LiDAR | 精确距离，360°覆盖 | 看不见地面上极低矮的物体 |
| 双目 | 能识别物体类别，看到颜色/纹理 | FOV 有限，计算量大 |
| IMU | 快速响应，检测碰撞/倾斜 | 不能直接检测障碍物 |

**融合策略**：
- LiDAR 负责全局避障和建图
- 双目负责前方低矮障碍物检测（洒水器、玩具）
- IMU 负责检测突然的碰撞或倾斜（被卡住、上坡过陡）

### 10.2 将双目深度信息转化为点云

```bash
# 安装 stereo_image_proc（双目处理包）
sudo apt install ros-jazzy-stereo-image-proc

# 启动双目处理节点（生成视差图和点云）
ros2 launch stereo_image_proc stereo_image_proc.launch.py \
  left_namespace:=/stereo/left \
  right_namespace:=/stereo/right
```

这会产生 `/stereo/points2` 话题（PointCloud2），可以输入到 costmap 的障碍物层。

### 10.3 修改 Nav2 参数加入双目点云

在 `nav2_params.yaml` 的 `local_costmap` 中添加：

```yaml
obstacle_layer:
  observation_sources: scan stereo_cloud
  scan:
    topic: /scan
    # ... 现有配置
  stereo_cloud:
    topic: /stereo/points2
    data_type: "PointCloud2"
    max_obstacle_height: 0.3
    min_obstacle_height: 0.03
    obstacle_max_range: 3.0
    obstacle_min_range: 0.2
    clearing: true
    marking: true
```

### 10.4 IMU 坡度保护

创建一个简单的安全节点，当检测到过大倾斜时停止机器人：

```python
#!/usr/bin/env python3
"""当 IMU 检测到过大倾斜角时发布零速度停止机器人。"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Twist
import math


class TiltProtection(Node):
    def __init__(self):
        super().__init__('tilt_protection')
        self.declare_parameter('max_tilt_deg', 25.0)
        self.max_tilt = math.radians(
            self.get_parameter('max_tilt_deg').value)

        self.sub = self.create_subscription(Imu, '/imu', self.imu_cb, 10)
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.is_tilted = False

    def imu_cb(self, msg):
        # 从加速度计估算倾斜角
        ax = msg.linear_acceleration.x
        ay = msg.linear_acceleration.y
        az = msg.linear_acceleration.z

        # 计算与重力方向的偏差
        pitch = math.atan2(ax, math.sqrt(ay*ay + az*az))
        roll = math.atan2(ay, math.sqrt(ax*ax + az*az))
        tilt = math.sqrt(pitch*pitch + roll*roll)

        if tilt > self.max_tilt and not self.is_tilted:
            self.is_tilted = True
            self.get_logger().warn(
                f'倾斜角 {math.degrees(tilt):.1f}° 超过阈值，紧急停止！')
            self.pub.publish(Twist())  # 发布零速度
        elif tilt < self.max_tilt * 0.8:
            if self.is_tilted:
                self.get_logger().info('倾斜恢复正常')
            self.is_tilted = False


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(TiltProtection())
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

---

## 附录 A：常见问题排查

### Q: Gazebo 启动后看不到机器人

```bash
# 检查 spawn 是否成功
ros2 topic echo /robot_description --once | head -5

# 手动在 Gazebo 中生成
ros2 run ros_gz_sim create -world lawn_1000sqm \
  -topic /robot_description -name mower -z 0.1
```

### Q: /scan 没有数据

```bash
# 检查 bridge 是否运行
ros2 node list | grep bridge

# 检查 Gazebo 侧的话题（gz topic）
gz topic -l | grep scan
gz topic -e /scan
```

### Q: SLAM 的 /map 话题不存在

```bash
# 确认 slam_toolbox 节点在运行
ros2 node list | grep slam

# 检查是否收到 scan
ros2 topic echo /scan --once

# 检查 TF 是否完整
ros2 run tf2_ros tf2_echo odom base_footprint
```

### Q: 导航时机器人不动

```bash
# 检查 Nav2 的状态
ros2 lifecycle get /controller_server
ros2 lifecycle get /planner_server

# 应该都是 active。如果是 inactive：
ros2 lifecycle set /controller_server activate
ros2 lifecycle set /planner_server activate
```

---

## 附录 B：有用的调试命令

```bash
# 查看完整节点图
rqt_graph

# 查看 TF 树
ros2 run tf2_tools view_frames
# 生成 frames.pdf

# 实时 TF 监控
ros2 run rqt_tf_tree rqt_tf_tree

# 查看话题带宽
ros2 topic bw /scan
ros2 topic bw /stereo/left/image_raw

# 记录所有数据用于回放
ros2 bag record -a -o lawn_mapping_session

# 回放数据
ros2 bag play lawn_mapping_session --clock
```

---

## 附录 C：下一步学习方向

| 方向 | 说明 | 推荐资源 |
|------|------|---------|
| RTK-GPS 定位 | 添加 GNSS 仿真插件 | `gz-sim-navsat-system` |
| 视觉 SLAM | 用双目做 ORB-SLAM3 | `ros-jazzy-rtabmap-ros` |
| 深度学习避障 | 训练模型识别临时障碍物 | YOLOv8 + ROS 2 |
| 电量管理 | 模拟电池消耗，自动回充 | 自定义 BT 节点 |
| 多机协作 | 多台割草机分区作业 | ROS 2 命名空间 + 调度器 |
| 真实部署 | 从仿真迁移到实车 | ros2_control + 硬件驱动 |

---

## 附录 D：项目文件结构

```
tb3_mower_sim/
├── CMakeLists.txt
├── package.xml
├── README.md
├── TUTORIAL.md              ← 本文件
├── config/
│   ├── nav2_params.yaml     ← Nav2 导航参数
│   ├── slam_params.yaml     ← SLAM 建图参数
│   └── tb3_mower.rviz       ← RViz 显示配置
├── launch/
│   ├── tb3_mower_sim.launch.py   ← 主仿真启动
│   ├── tb3_slam.launch.py        ← SLAM 建图
│   └── tb3_navigation.launch.py  ← Nav2 导航
├── urdf/
│   └── mower.urdf.xacro     ← 割草机机器人模型
├── world/
│   └── lawn_1000sqm.sdf     ← 1000m² 草坪世界
├── models/                   ← (预留) 自定义 Gazebo 模型
└── scripts/
    └── boustrophedon_coverage.py  ← 弓字形覆盖路径
```
