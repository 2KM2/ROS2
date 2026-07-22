---
name: navigate
description: 启动 Nav2 导航并发送目标点
user_invocable: true
---

# Nav2 自主导航

帮用户启动导航栈、设置初始位姿、发送导航目标。

## 前提

需要已保存的地图文件（先运行 /slam）。

## 启动

```bash
# 先关闭 SLAM（如果在运行）
ros2 launch tb3_mower_sim tb3_navigation.launch.py \
  map:=$HOME/workspace/ROS2/maps/lawn_1000sqm.yaml
```

## 设置初始位姿

在 RViz 中：
1. 点击 "2D Pose Estimate"
2. 在地图上点击当前位置并拖动方向

或命令行：
```bash
ros2 topic pub --once /initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
  "{header: {frame_id: 'map'}, pose: {pose: {position: {x: 0.0, y: -11.0}, orientation: {w: 1.0}}}}"
```

## 发送导航目标

RViz 中点击 "Nav2 Goal"，或命令行：
```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 5.0, y: 5.0}, orientation: {w: 1.0}}}}"
```

## 参数文件

`src/sim_gazebo/tb3_mower_sim/config/nav2_params.yaml`

常用调整：
- `robot_radius` — 碰撞半径
- `inflation_radius` — 障碍物膨胀
- `max_vel_x` — 最大线速度
