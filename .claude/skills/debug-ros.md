---
name: debug-ros
description: 调试 ROS 2 仿真问题（话题、TF、节点）
user_invocable: true
---

# ROS 2 调试

帮用户排查仿真系统中的常见问题。

## 诊断流程

### 1. 节点状态

```bash
ros2 node list
ros2 lifecycle get <node_name>
```

### 2. 话题检查

```bash
ros2 topic list
ros2 topic info <topic> -v    # 查看发布者/订阅者
ros2 topic hz <topic>          # 检查频率
ros2 topic echo <topic> --once # 查看一帧数据
```

### 3. TF 问题

```bash
# 查看 TF 树
ros2 run tf2_tools view_frames

# 检查特定变换
ros2 run tf2_ros tf2_echo <parent_frame> <child_frame>

# 实时 TF 监控
ros2 run rqt_tf_tree rqt_tf_tree
```

### 4. Gazebo 侧检查

```bash
# Gazebo 内部话题
gz topic -l
gz topic -e <gz_topic>
```

### 5. 常见问题

| 症状 | 可能原因 | 解决方法 |
|------|---------|---------|
| /scan 无数据 | bridge 未运行 | 检查 ros_gz_bridge 节点 |
| TF 断裂 | robot_state_publisher 未启动 | 检查 /robot_description |
| 导航不动 | lifecycle 未激活 | `ros2 lifecycle set ... activate` |
| 机器人不出现 | spawn 失败 | 检查世界名称是否匹配 |
| SLAM 无地图 | scan 话题不匹配 | 检查 slam_params.yaml 中 scan_topic |

### 6. 日志

```bash
# 查看特定节点的日志
ros2 node info <node_name>

# 过滤 WARN/ERROR
ros2 topic echo /rosout | grep -E "WARN|ERROR"
```
