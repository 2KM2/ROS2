# intelligent_mower_description

这是一个面向 ROS 2 Jazzy 与 Gazebo Harmonic 的智能割草机描述包。它是独立于
`smartcar_description` 的新模型，使用四轮滑移转向：同侧前后轮同速，左右轮速度差
产生转向。

初学 URDF/Xacro 请先阅读 [URDF_TUTORIAL.md](URDF_TUTORIAL.md)。

## 模型组成

- `base_link`：18 kg、780 × 620 mm 的底盘外壳；
- 四个驱动轮：半径 160 mm，轮距 480 mm，轴距 580 mm；
- `cutter_deck_link` / `cutter_blade_joint`：520 mm 刀盘和独立刀片转轴；
- `bumper_link`：前保险杠；后续可接触碰撞传感器与停刀状态机；
- `lidar_link`、`camera_link`、`imu_link`：用于避障、建图和姿态估计；
- `gnss_antenna_link`：RTK/GNSS 天线安装坐标系；它只是坐标系，需由定位节点发布卫星数据；
- `charging_contact_link`：充电桩对接位置坐标系。

## 构建与运行

```bash
colcon build --packages-select intelligent_mower_description
source install/setup.bash
ros2 launch intelligent_mower_description intelligent_mower_sim.launch.py
```

通过 `/cmd_vel` 控制（已映射至 Gazebo 的 `/intelligent_mower/cmd_vel`）：

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.25}, angular: {z: 0.35}}" -r 10
```

## 可用话题

`/intelligent_mower/odom`、`/intelligent_mower/scan`、
`/intelligent_mower/imu`、`/intelligent_mower/camera/image`、`/joint_states`、`/tf`。

刀盘模型当前只提供关节和外观，尚未模拟切草或自动启停。实际控制应由安全节点在
速度为零、检测到碰撞/抬升或离开边界时停止刀盘，再将覆盖规划、RTK 定位和回充策略
接入导航系统。
