---
name: launch-sim
description: 启动割草机仿真环境（Gazebo + 机器人 + RViz）
user_invocable: true
---

# 启动割草机仿真

帮用户启动仿真环境，检查必要条件并给出终端命令。

## 步骤

1. 确认包已编译：
```bash
source /opt/ros/jazzy/setup.bash
cd ~/workspace/ROS2
colcon build --symlink-install --packages-select tb3_mower_sim
source install/setup.bash
```

2. 启动仿真：
```bash
ros2 launch tb3_mower_sim tb3_mower_sim.launch.py
```

3. 验证话题：
```bash
ros2 topic list
ros2 topic hz /scan
ros2 topic hz /odom
```

## 可选参数

- `headless:=true` — 无 GUI 运行 Gazebo
- `use_rviz:=false` — 不启动 RViz
- `spawn_x:=5.0 spawn_y:=3.0` — 指定初始位置
