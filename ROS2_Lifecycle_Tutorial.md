# ROS2 生命周期节点（Lifecycle Node）教程

> 基于 ROS2 Jazzy，C++ 实现
> 功能：受控启停的节点状态机，精确管理资源分配与释放

---

## 目录

1. [生命周期节点基本概念](#1-生命周期节点基本概念)
2. [状态机详解](#2-状态机详解)
3. [创建功能包](#3-创建功能包)
4. [包结构](#4-包结构)
5. [CMakeLists.txt 配置](#5-cmakeliststxt-配置)
6. [生命周期节点实现](#6-生命周期节点实现)
7. [生命周期控制器实现](#7-生命周期控制器实现)
8. [编译与运行](#8-编译与运行)
9. [常用调试命令](#9-常用调试命令)
10. [关键 API 速查](#10-关键-api-速查)

---

## 1. 生命周期节点基本概念

普通 ROS2 节点启动后立即运行，无法精确控制**何时分配资源、何时开始工作、何时暂停**。

生命周期节点（Lifecycle Node）引入**状态机**，将节点的运行过程拆分为若干阶段，外部可通过服务调用驱动状态转移，适用于：

- 需要在使用前完成配置（连接传感器、加载模型）
- 需要暂停运行而不销毁节点（省电模式）
- 需要协调多个节点按顺序启动的系统
- 需要安全地释放资源（关闭硬件设备）

---

## 2. 状态机详解

```
                    ┌─────────────────────────────────────┐
                    │                                     │
              configure()                           shutdown()
                    │                                     │
                    ▼                                     │
[unconfigured] ──────────▶ [inactive] ◀──── deactivate() ─── [active]
      │                       │    │                              │
      │                  activate() │                        shutdown()
      │                       │  cleanup()                       │
      │                       ▼    │                             │
      │                   [active] │                             ▼
      │                            ▼                        [finalized]
      └──────── shutdown() ──▶ [unconfigured]
```

**四个主要状态：**

| 状态 | 说明 |
|------|------|
| `unconfigured` | 初始状态，节点刚构造完毕，尚未分配任何资源 |
| `inactive` | 已配置，资源已分配（publisher/timer 已创建），但尚未运行 |
| `active` | 正常运行中，publisher 激活，timer 在跳动 |
| `finalized` | 终态，节点已关闭，不可恢复 |

**五个状态回调（必须重写）：**

| 回调 | 触发条件 | 状态转移 | 典型操作 |
|------|---------|---------|---------|
| `on_configure` | 调用 configure | unconfigured → inactive | 创建 publisher/subscriber/timer，加载配置 |
| `on_activate` | 调用 activate | inactive → active | 激活 publisher，启动 timer |
| `on_deactivate` | 调用 deactivate | active → inactive | 停止 timer，停用 publisher |
| `on_cleanup` | 调用 cleanup | inactive → unconfigured | 释放所有资源，重置状态 |
| `on_shutdown` | 调用 shutdown | any → finalized | 安全关闭，释放硬件资源 |

---

## 3. 创建功能包

```bash
cd ~/workspace/ROS2/src

# 依赖 rclcpp_lifecycle（生命周期 API）和 lifecycle_msgs（状态转移服务类型）
ros2 pkg create cpp06_lifecycle \
  --build-type ament_cmake \
  --dependencies rclcpp rclcpp_lifecycle std_msgs lifecycle_msgs
```

---

## 4. 包结构

```
cpp06_lifecycle/
├── src/
│   ├── lifecycle_node.cpp        ← 生命周期节点（实现五个状态回调）
│   └── lifecycle_controller.cpp  ← 控制器（发送状态转移命令）
├── CMakeLists.txt
└── package.xml
```

---

## 5. CMakeLists.txt 配置

```cmake
find_package(rclcpp REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)
find_package(std_msgs REQUIRED)

# 生命周期节点：用 executor 而非 rclcpp::spin()
add_executable(lifecycle_node src/lifecycle_node.cpp)
ament_target_dependencies(lifecycle_node rclcpp rclcpp_lifecycle std_msgs)

# 控制器：发送 ChangeState 服务请求
add_executable(lifecycle_controller src/lifecycle_controller.cpp)
ament_target_dependencies(lifecycle_controller rclcpp lifecycle_msgs)

install(TARGETS lifecycle_node lifecycle_controller
  DESTINATION lib/${PROJECT_NAME})
```

> ⚠️ `LifecycleNode` 必须通过 `executor.add_node(node->get_node_base_interface())` 加入 executor，
> 不能直接传给 `rclcpp::spin()`。

---

## 6. 生命周期节点实现

```cpp
// src/lifecycle_node.cpp
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/lifecycle_node.hpp"
#include "std_msgs/msg/string.hpp"

using CallbackReturn =
  rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

class LifecycleTalker : public rclcpp_lifecycle::LifecycleNode
{
public:
  explicit LifecycleTalker(const rclcpp::NodeOptions & options = rclcpp::NodeOptions())
  : LifecycleNode("lifecycle_talker", options), count_(0)
  {
    RCLCPP_INFO(get_logger(), "节点构造完成 → [unconfigured]");
  }

  // unconfigured → inactive：分配资源，但不激活
  CallbackReturn on_configure(const rclcpp_lifecycle::State &) override
  {
    publisher_ = this->create_publisher<std_msgs::msg::String>("lifecycle_topic", 10);
    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(500),
      std::bind(&LifecycleTalker::publish_message, this));
    timer_->cancel();   // 配置阶段先停止 timer
    RCLCPP_INFO(get_logger(), "on_configure() → [inactive]");
    return CallbackReturn::SUCCESS;
  }

  // inactive → active：激活 publisher，启动 timer
  CallbackReturn on_activate(const rclcpp_lifecycle::State &) override
  {
    publisher_->on_activate();
    timer_->reset();
    RCLCPP_INFO(get_logger(), "on_activate() → [active]  开始发布");
    return CallbackReturn::SUCCESS;
  }

  // active → inactive：暂停，不销毁资源
  CallbackReturn on_deactivate(const rclcpp_lifecycle::State &) override
  {
    timer_->cancel();
    publisher_->on_deactivate();
    RCLCPP_INFO(get_logger(), "on_deactivate() → [inactive]  暂停发布");
    return CallbackReturn::SUCCESS;
  }

  // inactive → unconfigured：释放所有资源
  CallbackReturn on_cleanup(const rclcpp_lifecycle::State &) override
  {
    timer_.reset();
    publisher_.reset();
    count_ = 0;
    RCLCPP_INFO(get_logger(), "on_cleanup() → [unconfigured]  资源已释放");
    return CallbackReturn::SUCCESS;
  }

  // any → finalized
  CallbackReturn on_shutdown(const rclcpp_lifecycle::State &) override
  {
    timer_.reset();
    publisher_.reset();
    RCLCPP_INFO(get_logger(), "on_shutdown() → [finalized]");
    return CallbackReturn::SUCCESS;
  }

private:
  void publish_message()
  {
    if (!publisher_->is_activated()) return;
    auto msg = std_msgs::msg::String();
    msg.data = "[lifecycle] Hello! count: " + std::to_string(count_++);
    RCLCPP_INFO(get_logger(), "Publishing: '%s'", msg.data.c_str());
    publisher_->publish(msg);
  }

  // 注意：使用 LifecyclePublisher 而非普通 Publisher
  rclcpp_lifecycle::LifecyclePublisher<std_msgs::msg::String>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
  size_t count_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  // LifecycleNode 需要 executor，不能直接 rclcpp::spin()
  rclcpp::executors::SingleThreadedExecutor exe;
  auto node = std::make_shared<LifecycleTalker>();
  exe.add_node(node->get_node_base_interface());
  exe.spin();

  rclcpp::shutdown();
  return 0;
}
```

**关键区别——普通节点 vs 生命周期节点：**

| 对比项 | 普通节点 | 生命周期节点 |
|--------|---------|------------|
| 基类 | `rclcpp::Node` | `rclcpp_lifecycle::LifecycleNode` |
| Publisher 类型 | `rclcpp::Publisher<T>` | `rclcpp_lifecycle::LifecyclePublisher<T>` |
| spin 方式 | `rclcpp::spin(node)` | `executor.add_node(node->get_node_base_interface()); executor.spin()` |
| 资源分配时机 | 构造函数中 | `on_configure` 回调中 |

---

## 7. 生命周期控制器实现

控制器通过 `/lifecycle_talker/change_state` 服务驱动状态转移：

```cpp
// src/lifecycle_controller.cpp
#include "rclcpp/rclcpp.hpp"
#include "lifecycle_msgs/srv/change_state.hpp"
#include "lifecycle_msgs/msg/transition.hpp"

using namespace std::chrono_literals;

bool change_state(
  rclcpp::Node::SharedPtr node,
  rclcpp::Client<lifecycle_msgs::srv::ChangeState>::SharedPtr client,
  uint8_t transition_id, const std::string & label)
{
  auto request = std::make_shared<lifecycle_msgs::srv::ChangeState::Request>();
  request->transition.id = transition_id;
  client->wait_for_service(3s);
  auto future = client->async_send_request(request);
  rclcpp::spin_until_future_complete(node, future);
  bool ok = future.get()->success;
  RCLCPP_INFO(node->get_logger(), "%s %s", ok ? "✓" : "✗", label.c_str());
  return ok;
}

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node   = rclcpp::Node::make_shared("lifecycle_controller");
  auto client = node->create_client<lifecycle_msgs::srv::ChangeState>(
    "/lifecycle_talker/change_state");

  rclcpp::sleep_for(1s);

  // configure → activate → (运行4秒) → deactivate → activate → cleanup → shutdown
  using T = lifecycle_msgs::msg::Transition;
  change_state(node, client, T::TRANSITION_CONFIGURE,             "configure");     rclcpp::sleep_for(2s);
  change_state(node, client, T::TRANSITION_ACTIVATE,              "activate");      rclcpp::sleep_for(4s);
  change_state(node, client, T::TRANSITION_DEACTIVATE,            "deactivate");    rclcpp::sleep_for(2s);
  change_state(node, client, T::TRANSITION_ACTIVATE,              "activate again");rclcpp::sleep_for(3s);
  change_state(node, client, T::TRANSITION_DEACTIVATE,            "deactivate");
  change_state(node, client, T::TRANSITION_CLEANUP,               "cleanup");
  change_state(node, client, T::TRANSITION_UNCONFIGURED_SHUTDOWN,  "shutdown");

  rclcpp::shutdown();
  return 0;
}
```

---

## 8. 编译与运行

### 编译

```bash
cd ~/workspace/ROS2
colcon build --packages-select cpp06_lifecycle
source install/setup.bash
```

### 运行

**终端 1：启动生命周期节点（初始处于 [unconfigured]）**

```bash
ros2 run cpp06_lifecycle lifecycle_node
```

**终端 2：启动控制器（自动驱动完整生命周期）**

```bash
ros2 run cpp06_lifecycle lifecycle_controller
```

**或手动用命令行控制（不用控制器节点）：**

```bash
# configure
ros2 lifecycle set /lifecycle_talker configure

# activate（开始发布消息）
ros2 lifecycle set /lifecycle_talker activate

# deactivate（暂停）
ros2 lifecycle set /lifecycle_talker deactivate

# cleanup（释放资源）
ros2 lifecycle set /lifecycle_talker cleanup

# shutdown
ros2 lifecycle set /lifecycle_talker shutdown
```

**预期输出：**

```
[INFO] [lifecycle_talker]: 节点构造完成 → [unconfigured]
[INFO] [lifecycle_talker]: on_configure() → [inactive]  资源已分配
[INFO] [lifecycle_talker]: on_activate() → [active]  开始发布
[INFO] [lifecycle_talker]: Publishing: '[lifecycle] Hello! count: 0'
[INFO] [lifecycle_talker]: Publishing: '[lifecycle] Hello! count: 1'
...
[INFO] [lifecycle_talker]: on_deactivate() → [inactive]  暂停发布
[INFO] [lifecycle_talker]: on_activate() → [active]  开始发布
[INFO] [lifecycle_talker]: Publishing: '[lifecycle] Hello! count: 2'
...
[INFO] [lifecycle_talker]: on_cleanup() → [unconfigured]  资源已释放
[INFO] [lifecycle_talker]: on_shutdown() → [finalized]
```

---

## 9. 常用调试命令

```bash
# 列出系统中所有生命周期节点
ros2 lifecycle nodes

# 查看节点当前状态
ros2 lifecycle get /lifecycle_talker

# 查看节点支持的所有状态转移
ros2 lifecycle list /lifecycle_talker

# 手动触发状态转移
ros2 lifecycle set /lifecycle_talker configure
ros2 lifecycle set /lifecycle_talker activate
ros2 lifecycle set /lifecycle_talker deactivate
ros2 lifecycle set /lifecycle_talker cleanup
ros2 lifecycle set /lifecycle_talker shutdown
```

---

## 10. 关键 API 速查

| API | 说明 |
|-----|------|
| `rclcpp_lifecycle::LifecycleNode` | 生命周期节点基类 |
| `rclcpp_lifecycle::LifecyclePublisher<T>` | 支持激活/停用的 publisher |
| `publisher_->on_activate()` | 在 `on_activate` 中激活 publisher |
| `publisher_->on_deactivate()` | 在 `on_deactivate` 中停用 publisher |
| `publisher_->is_activated()` | 检查 publisher 是否处于激活状态 |
| `CallbackReturn::SUCCESS` | 回调返回：状态转移成功 |
| `CallbackReturn::FAILURE` | 回调返回：转移失败，节点进入错误状态 |
| `executor.add_node(node->get_node_base_interface())` | 将 LifecycleNode 加入 executor |
| `lifecycle_msgs::msg::Transition::TRANSITION_CONFIGURE` | configure 转移 ID |
| `lifecycle_msgs::msg::Transition::TRANSITION_ACTIVATE` | activate 转移 ID |

---

> 📌 **应用场景举例**
>
> | 场景 | 说明 |
> |------|------|
> | 相机节点 | configure 时初始化驱动，activate 时开始采集图像 |
> | 导航节点 | configure 时加载地图，activate 时开始规划路径 |
> | 系统启动序列 | 先 configure 全部节点，再依次 activate，保证启动顺序 |
> | 省电模式 | deactivate 停止计算密集型节点，随时可 activate 恢复 |
