# ROS2 组合节点（Component）教程

> 基于 ROS2 Jazzy，C++ 实现
> 功能：多节点共享同一进程，消息在进程内传递，消除序列化开销

---

## 目录

1. [组合节点基本概念](#1-组合节点基本概念)
2. [普通节点 vs 组合节点对比](#2-普通节点-vs-组合节点对比)
3. [创建功能包](#3-创建功能包)
4. [包结构](#4-包结构)
5. [CMakeLists.txt 配置](#5-cmakeliststxt-配置)
6. [TalkerComponent 实现](#6-talkercomponent-实现)
7. [ListenerComponent 实现](#7-listenercomponent-实现)
8. [Launch 文件组合加载](#8-launch-文件组合加载)
9. [编译与运行](#9-编译与运行)
10. [常用调试命令](#10-常用调试命令)
11. [关键 API 速查](#11-关键-api-速查)

---

## 1. 组合节点基本概念

在标准 ROS2 中，每个节点运行在独立进程里，话题消息需要经过：

```
节点A（进程1） → 序列化 → DDS 传输 → 反序列化 → 节点B（进程2）
```

**组合节点（Component）** 将多个节点放入同一进程（`component_container`），
同一进程内的消息传递通过**共享内存指针**完成，完全跳过序列化/反序列化：

```
TalkerComponent ──[ 进程内共享内存 ]──▶ ListenerComponent
         └───── 共同运行在 component_container ─────┘
```

**优势：**
- 零拷贝消息传递，延迟极低（适合高频传感器数据）
- 节省内存（共享 heap、代码段）
- 仍可独立部署（编译一次，既可组合也可单独运行）

---

## 2. 普通节点 vs 组合节点对比

| 对比项 | 普通节点 | 组合节点 |
|--------|---------|---------|
| 部署方式 | 独立可执行文件 | 共享库（`.so`），由 container 加载 |
| 消息传输 | 序列化 → DDS → 反序列化 | 进程内指针传递（可零拷贝） |
| 跨机通信 | ✅ 支持 | ✅ 支持（container 之间仍走 DDS） |
| 延迟 | 较高（µs~ms 级） | 极低（ns 级，同进程） |
| 构造函数签名 | `Node(name)` | `Node(name, NodeOptions)` |
| 注册宏 | 无需 | `RCLCPP_COMPONENTS_REGISTER_NODE(ClassName)` |
| CMake 编译目标 | `add_executable` | `add_library(SHARED)` + `rclcpp_components_register_node` |
| 独立运行 | ✅ | ✅（`rclcpp_components_register_node` 会自动生成可执行入口） |

---

## 3. 创建功能包

```bash
cd ~/workspace/ROS2/src

# 依赖 rclcpp_components（组件注册和容器）
ros2 pkg create cpp07_component \
  --build-type ament_cmake \
  --dependencies rclcpp rclcpp_components std_msgs

# 创建 launch 目录
mkdir -p cpp07_component/launch
```

---

## 4. 包结构

```
cpp07_component/
├── src/
│   ├── talker_component.cpp    ← 发布者组件（共享库）
│   └── listener_component.cpp  ← 订阅者组件（共享库）
├── launch/
│   └── composition_launch.py   ← 将两组件加载到同一 container
├── CMakeLists.txt
└── package.xml
```

---

## 5. CMakeLists.txt 配置

组合节点编译为**共享库**而非可执行文件，这是与普通节点最大的区别：

```cmake
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(std_msgs REQUIRED)

# ── 发布者组件：编译为共享库
add_library(talker_component SHARED src/talker_component.cpp)
ament_target_dependencies(talker_component rclcpp rclcpp_components std_msgs)
# 注册组件插件，同时生成独立可执行文件 talker_node
rclcpp_components_register_node(talker_component
  PLUGIN "cpp07_component::TalkerComponent"
  EXECUTABLE talker_node)

# ── 订阅者组件：编译为共享库
add_library(listener_component SHARED src/listener_component.cpp)
ament_target_dependencies(listener_component rclcpp rclcpp_components std_msgs)
rclcpp_components_register_node(listener_component
  PLUGIN "cpp07_component::ListenerComponent"
  EXECUTABLE listener_node)

install(TARGETS talker_component listener_component
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME})
```

**`rclcpp_components_register_node` 做了两件事：**
1. 将类注册为可被动态加载的插件（给 `component_container` 用）
2. 自动生成一个独立可执行文件（`talker_node`），让组件也能单独运行

---

## 6. TalkerComponent 实现

```cpp
// src/talker_component.cpp
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_components/register_node_macro.hpp"
#include "std_msgs/msg/string.hpp"

namespace cpp07_component
{

class TalkerComponent : public rclcpp::Node
{
public:
  // 构造函数必须接收 NodeOptions 参数（组合节点规范）
  explicit TalkerComponent(const rclcpp::NodeOptions & options)
  : Node("talker", options), count_(0)
  {
    publisher_ = this->create_publisher<std_msgs::msg::String>("chatter", 10);
    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(500),
      std::bind(&TalkerComponent::timer_callback, this));
    RCLCPP_INFO(get_logger(), "TalkerComponent 已加载");
  }

private:
  void timer_callback()
  {
    auto msg = std_msgs::msg::String();
    msg.data = "[component] Hello! count: " + std::to_string(count_++);
    RCLCPP_INFO(get_logger(), "Publishing: '%s'", msg.data.c_str());
    publisher_->publish(msg);
  }

  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
  size_t count_;
};

}  // namespace cpp07_component

// 将类注册为组件插件，必须在命名空间外调用
RCLCPP_COMPONENTS_REGISTER_NODE(cpp07_component::TalkerComponent)
```

**编写组合节点的两个关键规范：**

```
1. 构造函数必须接收 const rclcpp::NodeOptions & options
   → 普通：MyNode(std::string name)
   → 组合：MyNode(const rclcpp::NodeOptions & options)

2. 文件末尾必须调用注册宏（命名空间外）
   RCLCPP_COMPONENTS_REGISTER_NODE(命名空间::类名)
```

---

## 7. ListenerComponent 实现

```cpp
// src/listener_component.cpp
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_components/register_node_macro.hpp"
#include "std_msgs/msg/string.hpp"

namespace cpp07_component
{

class ListenerComponent : public rclcpp::Node
{
public:
  explicit ListenerComponent(const rclcpp::NodeOptions & options)
  : Node("listener", options)
  {
    subscription_ = this->create_subscription<std_msgs::msg::String>(
      "chatter", 10,
      std::bind(&ListenerComponent::topic_callback, this, std::placeholders::_1));
    RCLCPP_INFO(get_logger(), "ListenerComponent 已加载，订阅 /chatter");
  }

private:
  void topic_callback(const std_msgs::msg::String & msg)
  {
    RCLCPP_INFO(get_logger(), "Received: '%s'", msg.data.c_str());
  }

  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
};

}  // namespace cpp07_component

RCLCPP_COMPONENTS_REGISTER_NODE(cpp07_component::ListenerComponent)
```

---

## 8. Launch 文件组合加载

`launch/composition_launch.py`：

```python
from launch import LaunchDescription
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    """
    将 TalkerComponent 和 ListenerComponent 加载到同一个 container 进程。
    两个组件共享进程，消息在进程内传递，无需序列化/网络开销。
    """
    container = ComposableNodeContainer(
        name='component_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[
            ComposableNode(
                package='cpp07_component',
                plugin='cpp07_component::TalkerComponent',
                name='talker',
            ),
            ComposableNode(
                package='cpp07_component',
                plugin='cpp07_component::ListenerComponent',
                name='listener',
            ),
        ],
        output='screen',
    )
    return LaunchDescription([container])
```

---

## 9. 编译与运行

### 编译

```bash
cd ~/workspace/ROS2
colcon build --packages-select cpp07_component
source install/setup.bash
```

### 方式一：Launch 文件（推荐）—— 两个组件共享同一进程

```bash
ros2 launch cpp07_component composition_launch.py
```

输出：
```
[component_container]: TalkerComponent 已加载
[component_container]: ListenerComponent 已加载，订阅 /chatter
[component_container]: Publishing: '[component] Hello! count: 0'
[component_container]: Received: '[component] Hello! count: 0'
[component_container]: Publishing: '[component] Hello! count: 1'
[component_container]: Received: '[component] Hello! count: 1'
```

### 方式二：手动加载（运行时动态加载组件）

```bash
# 终端 1：启动空容器
ros2 run rclcpp_components component_container

# 终端 2：动态加载 TalkerComponent
ros2 component load /ComponentManager cpp07_component cpp07_component::TalkerComponent

# 终端 3：动态加载 ListenerComponent
ros2 component load /ComponentManager cpp07_component cpp07_component::ListenerComponent
```

### 方式三：单独运行（独立进程，退化为普通节点）

```bash
# rclcpp_components_register_node 自动生成了独立可执行文件
ros2 run cpp07_component talker_node
ros2 run cpp07_component listener_node
```

---

## 10. 常用调试命令

```bash
# 查看 container 中当前加载的组件
ros2 component list

# 查看系统中已注册的所有组件插件
ros2 component types

# 动态卸载组件（需要知道组件 ID）
ros2 component unload /ComponentManager <component_id>

# 查看话题（组合后 /chatter 仍然可见）
ros2 topic echo /chatter
ros2 topic hz /chatter
```

---

## 11. 关键 API 速查

### 实现端

| 要点 | 说明 |
|------|------|
| 构造函数签名 | `explicit MyNode(const rclcpp::NodeOptions & options)` |
| 注册宏 | `RCLCPP_COMPONENTS_REGISTER_NODE(命名空间::类名)` |
| 头文件 | `#include "rclcpp_components/register_node_macro.hpp"` |

### CMake 端

| API | 说明 |
|-----|------|
| `add_library(name SHARED ...)` | 编译为共享库，不是 `add_executable` |
| `rclcpp_components_register_node(lib PLUGIN "ns::Class" EXECUTABLE exe)` | 注册插件 + 生成独立可执行文件 |
| `install(TARGETS ... LIBRARY DESTINATION lib)` | 安装共享库 |

### 运行时

| 命令 | 说明 |
|-----|------|
| `ros2 launch ... composition_launch.py` | 通过 launch 文件组合加载 |
| `ros2 run rclcpp_components component_container` | 启动空容器 |
| `ros2 component load /容器名 包名 插件名` | 动态加载组件 |
| `ros2 component list` | 查看已加载组件 |

---

> 📌 **何时选择组合节点？**
>
> | 场景 | 建议 |
> |------|------|
> | 高频传感器数据（>100Hz）需要低延迟传递 | ✅ 用组合节点 |
> | 图像处理流水线（摄像头→预处理→检测→控制） | ✅ 用组合节点 |
> | 节点间需要跨机器通信 | ❌ 用普通节点（组合只优化同机通信） |
> | 调试阶段，需要独立查看每个节点日志 | ❌ 先用普通节点，稳定后再组合 |
