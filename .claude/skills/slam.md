---
name: slam
description: 启动 SLAM 建图并指导建图操作
user_invocable: true
---

# SLAM 建图

帮用户启动 SLAM、指导建图策略、保存地图。

## 启动

```bash
# 终端 2（仿真已启动）
source /opt/ros/jazzy/setup.bash
source ~/workspace/ROS2/install/setup.bash
ros2 launch tb3_mower_sim tb3_slam.launch.py
```

## 验证

```bash
ros2 topic hz /map
ros2 run tf2_ros tf2_echo map odom
```

## 建图建议

- 速度保持 0.1-0.2 m/s
- 沿围栏走一圈形成闭环
- 深入内部覆盖所有区域
- 避免快速旋转

## 保存地图

```bash
mkdir -p ~/workspace/ROS2/maps
ros2 run nav2_map_server map_saver_cli \
  -f ~/workspace/ROS2/maps/lawn_1000sqm \
  --ros-args -p use_sim_time:=true
```

## 参数调优

参数文件：`src/sim_gazebo/tb3_mower_sim/config/slam_params.yaml`

关键参数：
- `resolution`: 地图分辨率（默认 0.05m）
- `max_laser_range`: 使用的最大激光距离
- `minimum_travel_distance`: 插入新扫描的最小移动距离
- `do_loop_closing`: 回环检测开关
