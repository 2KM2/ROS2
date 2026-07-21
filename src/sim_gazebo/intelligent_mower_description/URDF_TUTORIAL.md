# URDF 与 Xacro 入门：用智能割草机模型学习 ROS 2 机器人描述

本教程面向第一次接触 URDF 的读者。读完后，你可以看懂本包的 `urdf/intelligent_mower.urdf.xacro`，并能够自己给机器人添加一个部件。

## 1. URDF 是什么

URDF（Unified Robot Description Format）是一份 XML 文件，用于描述**机器人长什么样、各个部件有多重，以及部件如何连接**。它不是控制程序：让轮子转动、规划路线或识别草坪，需要另外的 ROS 2 节点完成。

在 ROS 中，机器人由两类基本元素构成：

| 元素 | 含义 | 本模型的例子 |
| --- | --- | --- |
| `link` | 一个刚性部件及其坐标系 | `base_link`、`lidar_link`、一个车轮 |
| `joint` | 两个部件之间的连接方式 | `front_left_wheel_joint` |

可以把它理解为“积木 + 积木之间的关节”。所有 `link` 与 `joint` 最终必须连成一棵树。本模型的根是 `base_footprint`，底盘 `base_link`、轮子、刀盘、传感器都从它延伸出来。

```text
base_footprint
└── base_link
    ├── 4 个 wheel_link
    ├── cutter_deck_link ── cutter_blade_link
    ├── bumper_link
    ├── lidar_link / camera_link / imu_link
    ├── gnss_antenna_link
    └── charging_contact_link
```

## 2. 为什么文件后缀是 `.urdf.xacro`

纯 URDF 会重复很多 XML。Xacro 是 URDF 的预处理器，提供变量和宏，先将 `.urdf.xacro` 展开为普通 `.urdf`，再交给 ROS 和 Gazebo 使用。

例如本模型只定义一次车轮宏：

```xml
<xacro:macro name="wheel" params="name">
  <link name="${name}"> ... </link>
</xacro:macro>
```

随后用四行生成四个车轮：

```xml
<xacro:wheel name="front_left_wheel_link"/>
<xacro:wheel name="front_right_wheel_link"/>
```

变量也让尺寸集中管理：

```xml
<xacro:property name="wheel_radius" value="0.16"/>
```

单位统一为 **米、千克、弧度、秒**。`0.16` 表示 160 mm。

## 3. 一个 link 内有什么

以底盘 `base_link` 为例，它有三个常见部分：

```xml
<link name="base_link">
  <inertial>...</inertial>
  <visual>...</visual>
  <collision>...</collision>
</link>
```

- `visual`：RViz 与 Gazebo 中看到的外观；本模型用 `<box>`、`<cylinder>` 等基本几何体。
- `collision`：物理引擎用于碰撞的形状。它可以比外观更简单，以降低仿真开销。
- `inertial`：质量与惯性矩。没有正确惯性，Gazebo 中的机器人可能漂浮、抖动或运动异常。

本包的 `box_inertia` Xacro 宏根据盒子的质量和三边长度计算惯性矩，因此新增盒状部件时不必手算。

## 4. joint 怎么连接部件

每个 joint 都指定父、子和相对位置：

```xml
<joint name="front_left_wheel_joint" type="continuous">
  <parent link="base_link"/>
  <child link="front_left_wheel_link"/>
  <origin xyz="0.29 0.24 0.16"/>
  <axis xyz="0 1 0"/>
</joint>
```

- `parent`：安装位置所在的部件；这里是底盘。
- `child`：被安装的部件；这里是左前轮。
- `origin`：子部件相对父部件的位姿。`xyz` 是平移，`rpy` 是绕 X、Y、Z 的旋转。
- `axis`：可动关节的转轴方向。

常用 `type`：

| 类型 | 含义 | 本模型使用处 |
| --- | --- | --- |
| `fixed` | 完全固定 | LiDAR、相机、保险杠 |
| `continuous` | 可无限旋转 | 车轮、刀片 |
| `revolute` | 有角度上下限的旋转 | 例如机械臂关节 |
| `prismatic` | 直线伸缩 | 例如升降机构 |

ROS 通常约定：X 向前、Y 向左、Z 向上；绕 Z 轴的正方向是逆时针。

## 5. Gazebo 专有配置

URDF 负责结构；文件末尾的 `<gazebo>` 标签负责仿真功能。例如 LiDAR：

```xml
<gazebo reference="lidar_link">
  <sensor name="lidar" type="gpu_lidar">
    <update_rate>15</update_rate>
    <topic>/intelligent_mower/scan</topic>
  </sensor>
</gazebo>
```

它把传感器安装到已有的 `lidar_link`，并在 Gazebo 中发布激光数据。`DiffDrive` 插件读取 `/intelligent_mower/cmd_vel`，按照左右轮速度差驱动四个车轮，并产生里程计。

`gnss_antenna_link` **只是天线安装坐标系**，不会自动产生 GNSS 数据；真实的 RTK/GNSS 仿真或驱动节点需要另外发布消息。模型描述不等于传感器驱动。

## 6. 从 Xacro 到仿真

启动文件的关键步骤：

1. `xacro` 将模型展开为 `robot_description`；
2. `robot_state_publisher` 发布模型的静态坐标关系（TF）；
3. `ros_gz_sim create` 在 Gazebo 中生成机器人；
4. `ros_gz_bridge` 把 Gazebo 的里程计、激光、IMU 和相机消息桥接到 ROS 2。

因此，RViz 用于查看模型和传感器数据，Gazebo 用于运行物理仿真；两者作用不同。

## 7. 动手练习：添加一个状态灯

在 `bumper_link` 后、Gazebo 配置前加入下面内容：

```xml
<link name="status_light_link">
  <visual>
    <geometry><sphere radius="0.025"/></geometry>
    <material name="safety"/>
  </visual>
</link>
<joint name="status_light_joint" type="fixed">
  <parent link="base_link"/>
  <child link="status_light_link"/>
  <origin xyz="0.0 0.0 0.50"/>
</joint>
```

这个练习只添加外观，因此不需要 `collision` 和 `inertial`。完成后执行：

```bash
xacro src/sim_gazebo/intelligent_mower_description/urdf/intelligent_mower.urdf.xacro \
  > /tmp/intelligent_mower.urdf
colcon build --packages-select intelligent_mower_description
source install/setup.bash
ros2 launch intelligent_mower_description intelligent_mower_sim.launch.py use_rviz:=true
```

若模型不出现，先检查终端中的 XML/Xacro 报错；若部件位置不对，优先修改 joint 的 `origin xyz`。

## 8. 下一步建议

1. 给状态灯增加绿色、红色两种材质；
2. 给保险杠添加接触传感器，并在撞到障碍物时发布急停；
3. 为 `cutter_blade_joint` 编写控制节点：只有机器人运动正常且未触发安全条件时才允许转动；
4. 学习 TF2 与 Nav2，将 LiDAR、IMU、RTK 数据用于定位、避障、覆盖式割草和回充。

安全提醒：仿真中的刀盘只是模型。真实割草机还必须有独立的硬件急停、抬升检测、边界保护与功能安全设计；不能仅依赖 ROS 软件逻辑。
