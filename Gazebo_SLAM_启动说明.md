# ROS 2 Gazebo 智能车 SLAM 启动说明

工作空间：`/home/zkm/workspace/ROS2`

环境：ROS 2 Jazzy、Gazebo Sim、slam_toolbox。

## 1. 编译工作空间

修改源码、参数或启动文件后执行：

```bash
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash

colcon build --symlink-install \
  --packages-select demo_gazebo_sim smartcar_description mycar_slam_toolbox

source install/setup.bash
```

确认相关包可以找到：

```bash
ros2 pkg prefix smartcar_description
ros2 pkg prefix mycar_slam_toolbox
```

## 2. 启动 Gazebo 仿真

打开终端 1：

```bash
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 launch smartcar_description smartcar_sim.launch.py
```

该启动文件会启动 Gazebo、智能车模型、`robot_state_publisher`、ROS-Gazebo 消息桥接、RViz 和传感器。等待车辆完全加载后再启动 SLAM。

如果不需要 RViz：

```bash
ros2 launch smartcar_description smartcar_sim.launch.py use_rviz:=false
```

## 3. 检查仿真基础数据

打开终端 2：

```bash
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

查看话题：

```bash
ros2 topic list
```

应该至少包含：

```text
/clock
/cmd_vel
/joint_states
/smartcar/odom
/smartcar/scan
/tf
/tf_static
```

检查时钟、雷达和里程计频率：

```bash
ros2 topic hz /clock
ros2 topic hz /smartcar/scan
ros2 topic hz /smartcar/odom
```

每条命令使用 `Ctrl+C` 结束采样。

检查 TF：

```bash
ros2 run tf2_ros tf2_echo odom base_footprint
```

```bash
ros2 run tf2_ros tf2_echo \
  base_footprint smartcar/lidar_link/lidar_sensor
```

以上话题持续有数据且 TF 能正常输出，说明仿真侧正常。

## 4. 启动 SLAM Toolbox

打开终端 3：

```bash
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 launch mycar_slam_toolbox online_sync_launch.py
```

正常情况下可以看到：

```text
process started
Node using stack size 40000000
```

保持该终端运行。

## 5. 确认 SLAM 自动激活

`online_sync_launch.py` 已配置为启动后自动执行 `configure` 和 `activate`，正常情况下不再需要手动切换生命周期。

打开终端 4：

```bash
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

等待 SLAM 节点启动几秒，然后查看状态：

```bash
ros2 lifecycle get /mycar_slam_toolbox
```

预期状态：

```text
active [3]
```

SLAM 启动终端中还会出现：

```text
[LifecycleLaunch] Activating mycar_slam_toolbox.
```

如果自动切换失败，可按顺序手动恢复：

```bash
ros2 lifecycle set /mycar_slam_toolbox configure
ros2 lifecycle set /mycar_slam_toolbox activate
```

必须先成功执行 `configure`，再执行 `activate`。如果提示 `Node not found`，等待两三秒后重试。

也可以直接调用生命周期服务。配置节点：

```bash
ros2 service call /mycar_slam_toolbox/change_state \
  lifecycle_msgs/srv/ChangeState \
  "{transition: {id: 1}}"
```

返回 `success=true` 后激活：

```bash
ros2 service call /mycar_slam_toolbox/change_state \
  lifecycle_msgs/srv/ChangeState \
  "{transition: {id: 3}}"
```

## 6. 确认 SLAM 参数

```bash
ros2 param get /mycar_slam_toolbox use_sim_time
ros2 param get /mycar_slam_toolbox scan_topic
ros2 param get /mycar_slam_toolbox base_frame
ros2 param get /mycar_slam_toolbox odom_frame
ros2 param get /mycar_slam_toolbox map_frame
```

预期值：

```text
use_sim_time = true
scan_topic = /smartcar/scan
base_frame = base_footprint
odom_frame = odom
map_frame = map
```

## 7. 确认 SLAM 正常工作

检查雷达订阅者：

```bash
ros2 topic info /smartcar/scan -v
```

订阅者列表中应该出现 `mycar_slam_toolbox`。

检查地图和 TF：

```bash
ros2 topic info /map
ros2 topic hz /map
ros2 run tf2_ros tf2_echo map odom
```

车辆运动后，`/map` 应周期性更新，并能得到 `map -> odom` 变换。

## 8. 键盘控制车辆

打开终端 5：

```bash
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

如果找不到该软件包：

```bash
sudo apt install ros-jazzy-teleop-twist-keyboard
```

操作建议：

- 使用较低速度并缓慢转弯。
- 沿墙体和房间边缘行驶。
- 尽量形成闭环路线。
- 避免高速旋转和碰撞后车轮持续空转。

## 9. RViz 配置

将 RViz 的 `Fixed Frame` 设置为 `map`，然后添加：

- `Map`：话题选择 `/map`。
- `LaserScan`：话题选择 `/smartcar/scan`，Reliability 选择 `Best Effort`。
- `TF`：观察 `map`、`odom`、`base_footprint`、`base_link` 和雷达坐标系。
- `RobotModel`：显示车辆模型。

正常情况下，雷达点应与墙面基本重合，车辆移动后地图逐步扩大，回到经过的位置时能够进行闭环修正。

## 10. 保存地图

```bash
mkdir -p ~/workspace/ROS2/maps
```

```bash
ros2 run nav2_map_server map_saver_cli \
  -f ~/workspace/ROS2/maps/smartcar_house_map \
  --ros-args -p use_sim_time:=true
```

保存成功后会生成：

```text
smartcar_house_map.yaml
smartcar_house_map.pgm
```

## 11. 常见故障

### `/map` 不存在

检查生命周期：

```bash
ros2 lifecycle get /mycar_slam_toolbox
```

如果是 `unconfigured`，依次执行：

```bash
ros2 lifecycle set /mycar_slam_toolbox configure
ros2 lifecycle set /mycar_slam_toolbox activate
```

### 雷达存在但 SLAM 没有订阅

```bash
ros2 topic info /smartcar/scan -v
```

确认 SLAM 状态为 `active`，`scan_topic` 为 `/smartcar/scan`。

### 出现 `Message Filter dropping message`

检查两段 TF：

```bash
ros2 run tf2_ros tf2_echo odom base_footprint
```

```bash
ros2 run tf2_ros tf2_echo \
  base_footprint smartcar/lidar_link/lidar_sensor
```

同时确认仿真时间：

```bash
ros2 param get /mycar_slam_toolbox use_sim_time
```

结果必须为 `True`。

### 修改 YAML 后没有生效

```bash
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select mycar_slam_toolbox
source install/setup.bash
```

然后重新启动 SLAM 节点。

## 12. 每次启动顺序汇总

1. 启动 Gazebo：

   ```bash
   ros2 launch smartcar_description smartcar_sim.launch.py
   ```

2. 等待车辆加载完成。

3. 启动 SLAM：

   ```bash
   ros2 launch mycar_slam_toolbox online_sync_launch.py
   ```

4. 确认 SLAM 已自动激活：

   ```bash
   ros2 lifecycle get /mycar_slam_toolbox
   ```

   预期结果为 `active [3]`。

5. 启动键盘控制：

   ```bash
   ros2 run teleop_twist_keyboard teleop_twist_keyboard
   ```

6. 在 RViz 中观察 `/map` 和 `/smartcar/scan`。

7. 建图完成后保存地图：

   ```bash
   ros2 run nav2_map_server map_saver_cli \
     -f ~/workspace/ROS2/maps/smartcar_house_map \
     --ros-args -p use_sim_time:=true
   ```

8. 使用 `Ctrl+C` 依次关闭键盘控制、SLAM 和 Gazebo。
