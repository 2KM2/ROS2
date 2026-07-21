# ROS 2 键盘控制教程：teleop_twist_keyboard

本文介绍如何在 ROS 2 Jazzy 中使用 `teleop_twist_keyboard`，通过键盘发布速度指令，控制 Gazebo 中的移动机器人或真实底盘。

工作空间：`/home/zkm/workspace/ROS2`

## 1. 工作原理

`teleop_twist_keyboard` 会读取终端中的按键，并将速度指令发布到 `/cmd_vel` 话题：

```text
键盘输入 -> teleop_twist_keyboard -> /cmd_vel -> 底盘控制器 -> 机器人运动
```

默认消息类型为：

```text
geometry_msgs/msg/Twist
```

其中：

- `linear.x`：前进或后退速度，单位为 `m/s`
- `linear.y`：横向移动速度，仅全向底盘支持
- `linear.z`：垂直移动速度，主要用于无人机等设备
- `angular.z`：绕 Z 轴旋转的角速度，单位为 `rad/s`

## 2. 安装功能包

如果命令尚未安装，执行：

```bash
sudo apt update
sudo apt install ros-jazzy-teleop-twist-keyboard
```

确认功能包可以找到：

```bash
source /opt/ros/jazzy/setup.bash
ros2 pkg prefix teleop_twist_keyboard
```

## 3. 启动机器人或仿真

先启动需要控制的机器人。以当前工作空间中的 Gazebo 智能车为例，打开终端 1：

```bash
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 launch smartcar_description smartcar_sim.launch.py
```

等待 Gazebo 和车辆模型完全加载。

## 4. 启动键盘控制节点

打开终端 2：

```bash
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

出现下面的信息表示节点已经启动：

```text
currently:      speed 0.50      turn 1.00
```

这表示当前最大线速度为 `0.50 m/s`，最大角速度为 `1.00 rad/s`。

> 按键必须在运行该节点的终端中输入。先用鼠标点击终端，使终端获得输入焦点；不要在 Gazebo 或 RViz 窗口中直接输入。

## 5. 基本移动按键

### 5.1 差速底盘常用按键

```text
   u    i    o
   j    k    l
   m    ,    .
```

| 按键 | 动作 |
|---|---|
| `i` | 直线前进 |
| `,` | 直线后退 |
| `j` | 原地左转 |
| `l` | 原地右转 |
| `u` | 左前方运动 |
| `o` | 右前方运动 |
| `m` | 左后方运动 |
| `.` | 右后方运动 |
| `k` | 停止 |
| 其他按键 | 停止 |

对于普通两轮差速智能车，最常用的是 `i`、`,`、`j`、`l` 和 `k`。

### 5.2 全向移动

按住 `Shift` 后输入大写按键，可发布横向速度：

```text
   U    I    O
   J    K    L
   M    <    >
```

| 按键 | 动作 |
|---|---|
| `J` | 向左平移 |
| `L` | 向右平移 |
| `I` | 向前平移 |
| `<` | 向后平移 |

只有麦克纳姆轮、全向轮等支持横移的底盘才会响应 `linear.y`。普通差速底盘不能横向移动。

### 5.3 垂直移动

| 按键 | 动作 |
|---|---|
| `t` | 向上，增加 `linear.z` |
| `b` | 向下，减小 `linear.z` |

地面移动机器人通常不会使用这两个按键。

## 6. 调节速度

| 按键 | 作用 |
|---|---|
| `q` | 线速度和角速度同时增加 10% |
| `z` | 线速度和角速度同时降低 10% |
| `w` | 仅线速度增加 10% |
| `x` | 仅线速度降低 10% |
| `e` | 仅角速度增加 10% |
| `c` | 仅角速度降低 10% |

每次调整后，终端都会显示新的速度值。例如：

```text
currently:      speed 0.55      turn 1.10
```

初次操作时建议降低速度：连续按几次 `z`，确认车辆运动方向和停止功能正常后，再逐步提高速度。

## 7. 检查速度话题

### 7.1 确认节点正在运行

打开终端 3，并加载环境：

```bash
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 node list
```

通常可以看到：

```text
/teleop_twist_keyboard
```

### 7.2 查看话题和消息类型

```bash
ros2 topic list
ros2 topic info /cmd_vel
```

预期消息类型：

```text
geometry_msgs/msg/Twist
```

### 7.3 查看实时速度指令

```bash
ros2 topic echo /cmd_vel
```

回到键盘控制终端按 `i`，可以看到类似输出：

```yaml
linear:
  x: 0.5
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 0.0
```

按 `j` 时，主要变化的是 `angular.z`。按 `k` 后，各方向速度应变为 `0.0`。

使用 `Ctrl+C` 结束 `ros2 topic echo`。

## 8. 重映射 cmd_vel 话题

有些机器人不订阅 `/cmd_vel`，而是使用 `/smartcar/cmd_vel`、`/diff_drive_controller/cmd_vel_unstamped` 等话题。此时需要重映射：

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/smartcar/cmd_vel
```

先查询底盘实际订阅的话题：

```bash
ros2 topic list | grep cmd_vel
```

再检查目标话题是否存在订阅者：

```bash
ros2 topic info /smartcar/cmd_vel
```

如果 `Subscription count` 为 `0`，说明当前没有底盘控制器订阅该话题，车辆不会响应速度指令。

## 9. 发布 TwistStamped 消息

部分控制器需要 `geometry_msgs/msg/TwistStamped`。可以启用带时间戳的输出：

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -p stamped:=true -p frame_id:=base_link
```

是否需要 `Twist` 或 `TwistStamped`，应以底盘速度话题的实际类型为准：

```bash
ros2 topic type /cmd_vel
```

## 10. 常见问题

### 10.1 按键后没有任何输出

检查以下事项：

1. 鼠标是否点击了运行键盘节点的终端。
2. 是否误开启了中文输入法；建议切换为英文输入状态。
3. 终端是否仍在运行，是否已被 `Ctrl+C` 结束。
4. 使用的是小写字母还是需要 `Shift` 的大写字母。

### 10.2 /cmd_vel 有数据，但车辆不动

按以下顺序检查：

```bash
ros2 topic info /cmd_vel
ros2 topic echo /cmd_vel
ros2 node list
```

重点确认：

- `/cmd_vel` 是否有订阅者
- 发布者和订阅者使用的消息类型是否一致
- 底盘控制器是否已经启动
- 仿真是否处于暂停状态
- 控制器使用的速度话题是否需要重映射
- 仿真节点是否都设置了正确的 `use_sim_time`

### 10.3 车辆速度过快

按 `z` 同时降低线速度和角速度，或按 `x` 只降低线速度。也可以在启动时直接设置较小的初始速度：

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -p speed:=0.2 -p turn:=0.5
```

### 10.4 松开按键后车辆仍然运动

该节点按一次键会发布对应速度，松开按键并不等于自动停止。需要按 `k` 或任意未定义按键发送零速度。

操作真实机器人时，应随时准备按 `k` 停车，并确保急停装置可用。

### 10.5 远程 SSH 终端无法正确读取按键

确保使用交互式终端连接，并直接在前台运行节点：

```bash
ssh -t 用户名@机器人地址
```

不要将 `teleop_twist_keyboard` 放到后台运行，因为它需要持续读取当前终端的键盘输入。

## 11. 推荐操作流程

完整操作顺序如下：

1. 启动 Gazebo 或真实机器人底盘控制器。
2. 使用 `ros2 topic list` 确认速度控制话题。
3. 启动 `teleop_twist_keyboard`，必要时重映射话题。
4. 先按 `z` 降低速度。
5. 按 `i` 短距离前进，再按 `k` 停止。
6. 测试 `j` 和 `l` 的旋转方向。
7. 使用 `ros2 topic echo /cmd_vel` 验证发布的数据。
8. 操作结束后按 `k`，再按 `Ctrl+C` 退出节点。

## 12. 常用命令速查

```bash
# 启动键盘控制
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# 设置初始速度
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -p speed:=0.2 -p turn:=0.5

# 重映射速度话题
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap cmd_vel:=/smartcar/cmd_vel

# 查看速度话题信息
ros2 topic info /cmd_vel

# 查看实时速度指令
ros2 topic echo /cmd_vel

# 查看话题消息类型
ros2 topic type /cmd_vel
```

