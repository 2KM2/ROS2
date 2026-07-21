# 在 RViz 中查看 Gazebo 传感器：智能割草机实战

本教程说明为什么此前只看到 Gazebo，以及如何在 RViz 中查看智能割草机的模型、
激光雷达和前置相机。

## 1. 两个程序分别做什么

Gazebo Harmonic 负责物理仿真：地面、机器人运动、碰撞和传感器数据都在那里产生。
RViz 是 ROS 2 的数据可视化工具：它不模拟物理，而是订阅 ROS 话题并按 TF 坐标系显示。

```text
Gazebo 传感器 → ros_gz_bridge → ROS 2 话题 → RViz 显示项
                         ↑
                    TF 坐标变换
```

因此，“Gazebo 能看到机器人”不代表 RViz 已经订阅到传感器数据。

## 2. 正确启动方式

先在工作区根目录构建并加载环境：

```bash
colcon build --packages-select intelligent_mower_description
source install/setup.bash
ros2 launch intelligent_mower_description intelligent_mower_sim.launch.py
```

该启动文件默认 `use_rviz:=true`，会打开 RViz，并加载
`config/intelligent_mower.rviz`。配置已包含以下显示项：

| RViz 显示项 | ROS 2 话题/数据 |
| --- | --- |
| Intelligent mower | `/robot_description` 与 TF |
| Lidar scan | `/intelligent_mower/scan` |
| Front camera | `/intelligent_mower/camera/image` |
| TF | `/tf` 与 `/tf_static` |

若只想运行 Gazebo，可显式关闭 RViz：

```bash
ros2 launch intelligent_mower_description intelligent_mower_sim.launch.py use_rviz:=false
```

## 3. 为什么激光雷达需要 TF

激光消息中的每个点都在“传感器坐标系”中。RViz 的固定坐标系设为 `odom`，所以它必须知道：

```text
odom → base_footprint → base_link → lidar_link → Gazebo LiDAR frame
```

`robot_state_publisher` 根据 URDF 发布前半段；启动文件中的
`static_transform_publisher` 补上最后一段。没有这条变换，RViz 的 LaserScan 通常会报
`No transform`，或根本不显示点云。

## 4. QoS：为什么话题存在却没有数据

Gazebo 的高频传感器一般使用 **Best Effort** QoS，以避免因偶尔丢帧阻塞仿真。
本包的 RViz 配置也把 LiDAR 与相机设为 Best Effort。若你手动在 RViz 中添加显示项，
请在 Topic 的 QoS 设置中选择：

```text
Reliability: Best Effort
Durability:  Volatile
History:     Keep Last
```

QoS 不兼容时，话题列表看得到名称，但 RViz 不会收到任何消息。

## 5. 常用排错命令

在另一个已 `source install/setup.bash` 的终端运行：

```bash
# 确认桥接后存在话题
ros2 topic list | rg intelligent_mower

# 确认激光与相机真的在持续发布
ros2 topic hz /intelligent_mower/scan
ros2 topic hz /intelligent_mower/camera/image

# 查看激光消息的 frame_id；它必须能变换到 odom
ros2 topic echo /intelligent_mower/scan --once

# 确认 TF 树能查到雷达
ros2 run tf2_ros tf2_echo odom lidar_link
```

若 `topic hz` 没有输出，先检查 Gazebo 的传感器系统和 `ros_gz_bridge` 是否正常启动。
若有消息但 RViz 报 TF 错误，检查固定坐标系是否为 `odom`，再检查静态 TF 节点的日志。

## 6. 手动打开 RViz

默认配置文件位于安装空间。要在新终端手动打开它：

```bash
source install/setup.bash
rviz2 -d install/intelligent_mower_description/share/intelligent_mower_description/config/intelligent_mower.rviz
```

注意：此命令只启动显示器；Gazebo 仿真和启动文件仍需在另一个终端运行。

## 7. 常见现象

- **只出现网格，没有机器人**：确认 `robot_state_publisher` 正常运行，且 RViz 的 RobotModel
  的 Description Topic 是 `/robot_description`。
- **机器人出现，LiDAR 没有点**：确认 `/intelligent_mower/scan` 有频率，并将 LaserScan 的
  QoS 改为 Best Effort。
- **相机面板全黑**：确认 `/intelligent_mower/camera/image` 有消息；仿真刚启动时等待几秒。
- **显示变成红色 Status Error**：先展开 RViz 的 Displays 面板，读取完整错误；最常见原因是
  TF 或 QoS，而不是 URDF 外观。

掌握“话题是否发布、QoS 是否匹配、TF 是否连通”这三个检查点，就能排查绝大部分
Gazebo 到 RViz 的传感器显示问题。
