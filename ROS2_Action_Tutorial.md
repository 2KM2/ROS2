# ROS2 Action 通信教程

> 基于 ROS2 Jazzy，C++ 实现
> 模式：目标 → 实时反馈 → 最终结果（长任务异步执行）

---

## 目录

1. [Action 基本概念](#1-action-基本概念)
2. [服务 vs Action 对比](#2-服务-vs-action-对比)
3. [创建功能包](#3-创建功能包)
4. [包结构](#4-包结构)
5. [自定义 Action 文件 .action](#5-自定义-action-文件-action)
6. [配置 package.xml 与 CMakeLists.txt](#6-配置-packagexml-与-cmakeliststxt)
7. [Action 服务端](#7-action-服务端)
8. [Action 客户端](#8-action-客户端)
9. [编译与运行](#9-编译与运行)
10. [常用调试命令](#10-常用调试命令)
11. [关键 API 速查](#11-关键-api-速查)

---

## 1. Action 基本概念

Action 是 ROS2 中适合**长时间异步任务**的通信方式，结合了话题和服务的特点：

```
客户端 ──[ Goal 目标 ]──────────────▶ 服务端
客户端 ◀─[ Feedback 实时反馈 ]─────── 服务端（任务执行中，持续推送）
客户端 ◀─[ Result 最终结果 ]────────  服务端（任务完成时，推送一次）
客户端 ──[ Cancel 取消请求 ]─────────▶ 服务端（可中途取消）
```

三个核心组成：

| 组成 | 方向 | 说明 |
|------|------|------|
| **Goal** | 客户端 → 服务端 | 发送任务目标，服务端决定接受或拒绝 |
| **Feedback** | 服务端 → 客户端 | 任务执行期间持续推送进度 |
| **Result** | 服务端 → 客户端 | 任务结束时推送最终结果（一次性） |

---

## 2. 服务 vs Action 对比

| 特性 | 服务（Service） | Action |
|------|----------------|--------|
| 适用场景 | 短时快速操作 | 长时间任务（导航、抓取） |
| 执行期间反馈 | 无 | 有（Feedback） |
| 可取消 | 不支持 | 支持（Cancel） |
| 是否阻塞客户端 | 阻塞等待 | 非阻塞，回调驱动 |
| 接口文件 | `.srv`（两段） | `.action`（三段） |

---

## 3. 创建功能包

```bash
# 进入工作空间 src 目录
cd ~/workspace/ROS2/src

# 创建功能包，依赖 rclcpp、rclcpp_action、rosidl_default_generators
ros2 pkg create cpp04_action \
  --build-type ament_cmake \
  --dependencies rclcpp rclcpp_action rosidl_default_generators

# 创建 action 目录（存放 .action 文件）
mkdir -p cpp04_action/action
```

---

## 4. 包结构

```
cpp04_action/
├── action/
│   └── CountDown.action     ← 自定义 Action 接口定义
├── src/
│   ├── action_server.cpp    ← 服务端：执行任务，发反馈，返回结果
│   └── action_client.cpp    ← 客户端：发目标，处理反馈和结果
├── CMakeLists.txt
└── package.xml
```

---

## 5. 自定义 Action 文件 .action

`action/CountDown.action`：

```
# Goal（目标）：从几开始倒计时
int32 countdown_from
---
# Result（最终结果）：任务完成后的消息
string finish_message
---
# Feedback（实时反馈）：当前倒计时数值
int32 current_count
```

**`.action` 文件规则：**

- 用两个 `---` 将文件分为三段：`Goal` / `Result` / `Feedback`
- 字段类型与 `.msg` 相同
- 文件名大驼峰：`CountDown.action` → 类型名 `CountDown`

**生成的 C++ 类型：**

```
action/CountDown.action
→ 头文件：  #include "cpp04_action/action/count_down.hpp"
→ 类型：    cpp04_action::action::CountDown
→ Goal：    cpp04_action::action::CountDown::Goal
→ Result：  cpp04_action::action::CountDown::Result
→ Feedback：cpp04_action::action::CountDown::Feedback
```

---

## 6. 配置 package.xml 与 CMakeLists.txt

### package.xml

```xml
<depend>rclcpp</depend>
<depend>rclcpp_action</depend>
<build_depend>rosidl_default_generators</build_depend>
<exec_depend>rosidl_default_runtime</exec_depend>
<member_of_group>rosidl_interface_packages</member_of_group>
```

### CMakeLists.txt

```cmake
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# 注册 .action 文件
rosidl_generate_interfaces(${PROJECT_NAME}
  "action/CountDown.action"
)

ament_export_dependencies(rosidl_default_runtime)

rosidl_get_typesupport_target(cpp_typesupport_target
  ${PROJECT_NAME} "rosidl_typesupport_cpp")

add_executable(action_server src/action_server.cpp)
ament_target_dependencies(action_server rclcpp rclcpp_action)
target_link_libraries(action_server "${cpp_typesupport_target}")

add_executable(action_client src/action_client.cpp)
ament_target_dependencies(action_client rclcpp rclcpp_action)
target_link_libraries(action_client "${cpp_typesupport_target}")

install(TARGETS action_server action_client
  DESTINATION lib/${PROJECT_NAME})
```

---

## 7. Action 服务端

```cpp
// src/action_server.cpp
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "cpp04_action/action/count_down.hpp"
#include <thread>

using CountDown = cpp04_action::action::CountDown;
using GoalHandleCountDown = rclcpp_action::ServerGoalHandle<CountDown>;

class ActionServer : public rclcpp::Node
{
public:
  ActionServer() : Node("action_server")
  {
    action_server_ = rclcpp_action::create_server<CountDown>(
      this, "count_down",
      std::bind(&ActionServer::handle_goal,     this, std::placeholders::_1, std::placeholders::_2),
      std::bind(&ActionServer::handle_cancel,   this, std::placeholders::_1),
      std::bind(&ActionServer::handle_accepted, this, std::placeholders::_1));
  }

private:
  rclcpp_action::Server<CountDown>::SharedPtr action_server_;

  // 回调1：接受或拒绝目标
  rclcpp_action::GoalResponse handle_goal(
    const rclcpp_action::GoalUUID &,
    std::shared_ptr<const CountDown::Goal> goal)
  {
    if (goal->countdown_from <= 0) {
      return rclcpp_action::GoalResponse::REJECT;      // 拒绝无效目标
    }
    return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
  }

  // 回调2：处理取消请求
  rclcpp_action::CancelResponse handle_cancel(
    const std::shared_ptr<GoalHandleCountDown>)
  {
    return rclcpp_action::CancelResponse::ACCEPT;
  }

  // 回调3：目标接受后，在新线程中执行（避免阻塞 spin）
  void handle_accepted(const std::shared_ptr<GoalHandleCountDown> goal_handle)
  {
    std::thread(
      std::bind(&ActionServer::execute, this, std::placeholders::_1),
      goal_handle).detach();
  }

  // 核心执行：倒计时 + 发 Feedback + 发 Result
  void execute(const std::shared_ptr<GoalHandleCountDown> goal_handle)
  {
    int32_t start = goal_handle->get_goal()->countdown_from;
    auto feedback = std::make_shared<CountDown::Feedback>();
    auto result   = std::make_shared<CountDown::Result>();
    rclcpp::Rate rate(1.0);   // 每秒倒一格

    for (int32_t i = start; i >= 0; --i) {
      if (goal_handle->is_canceling()) {               // 检查取消请求
        result->finish_message = "已取消，停在 " + std::to_string(i);
        goal_handle->canceled(result);
        return;
      }
      feedback->current_count = i;
      goal_handle->publish_feedback(feedback);         // 发布实时反馈
      RCLCPP_INFO(this->get_logger(), "倒计时: %d", i);
      if (i > 0) rate.sleep();
    }

    result->finish_message = "倒计时完成！";
    goal_handle->succeed(result);                      // 发布最终结果
  }
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ActionServer>());
  rclcpp::shutdown();
  return 0;
}
```

**服务端三个回调的职责：**

```
handle_goal     → 决定接受(ACCEPT_AND_EXECUTE) 或 拒绝(REJECT)
handle_cancel   → 决定允许(ACCEPT) 或 拒绝(REJECT) 取消
handle_accepted → 目标被接受后触发，通常在新线程中调用 execute()
```

---

## 8. Action 客户端

```cpp
// src/action_client.cpp
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "cpp04_action/action/count_down.hpp"

using CountDown = cpp04_action::action::CountDown;
using GoalHandleCountDown = rclcpp_action::ClientGoalHandle<CountDown>;

class ActionClient : public rclcpp::Node
{
public:
  ActionClient() : Node("action_client")
  {
    client_ = rclcpp_action::create_client<CountDown>(this, "count_down");
  }

  void send_goal(int32_t countdown_from)
  {
    if (!client_->wait_for_action_server(std::chrono::seconds(5))) {
      RCLCPP_ERROR(this->get_logger(), "Action 服务端未就绪");
      return;
    }

    auto goal_msg = CountDown::Goal();
    goal_msg.countdown_from = countdown_from;

    auto options = rclcpp_action::Client<CountDown>::SendGoalOptions();

    // 目标被接受/拒绝时触发
    options.goal_response_callback =
      [this](const GoalHandleCountDown::SharedPtr & gh) {
        if (!gh) RCLCPP_ERROR(this->get_logger(), "目标被拒绝");
        else     RCLCPP_INFO(this->get_logger(),  "目标已接受，执行中...");
      };

    // 收到实时反馈时触发
    options.feedback_callback =
      [this](GoalHandleCountDown::SharedPtr,
             const std::shared_ptr<const CountDown::Feedback> fb) {
        RCLCPP_INFO(this->get_logger(), "  [反馈] 当前: %d", fb->current_count);
      };

    // 任务结束时触发
    options.result_callback =
      [this](const GoalHandleCountDown::WrappedResult & result) {
        switch (result.code) {
          case rclcpp_action::ResultCode::SUCCEEDED:
            RCLCPP_INFO(this->get_logger(), "✓ 成功: %s",
              result.result->finish_message.c_str());  break;
          case rclcpp_action::ResultCode::CANCELED:
            RCLCPP_WARN(this->get_logger(), "✗ 取消: %s",
              result.result->finish_message.c_str());  break;
          default:
            RCLCPP_ERROR(this->get_logger(), "✗ 异常中止");  break;
        }
      };

    client_->async_send_goal(goal_msg, options);
  }

private:
  rclcpp_action::Client<CountDown>::SharedPtr client_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<ActionClient>();

  int32_t n = 5;
  if (argc == 2) n = std::stoi(argv[1]);

  node->send_goal(n);
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
```

---

## 9. 编译与运行

### 编译

```bash
cd ~/workspace/ROS2
colcon build --packages-select cpp04_action
source install/setup.bash
```

### 运行

**终端 1：启动 Action 服务端**

```bash
ros2 run cpp04_action action_server
```

**终端 2：启动 Action 客户端（默认倒计时 5 秒）**

```bash
ros2 run cpp04_action action_client
# 或自定义倒计时数
ros2 run cpp04_action action_client 10
```

**预期交互输出：**

```
# 服务端
[INFO] [action_server]: 倒计时: 5
[INFO] [action_server]: 倒计时: 4
[INFO] [action_server]: 倒计时: 3
[INFO] [action_server]: 倒计时: 2
[INFO] [action_server]: 倒计时: 1
[INFO] [action_server]: 倒计时: 0
[INFO] [action_server]: 任务完成

# 客户端
[INFO] [action_client]: 目标已接受，执行中...
[INFO] [action_client]:   [反馈] 当前: 5
[INFO] [action_client]:   [反馈] 当前: 4
[INFO] [action_client]:   [反馈] 当前: 3
[INFO] [action_client]:   [反馈] 当前: 2
[INFO] [action_client]:   [反馈] 当前: 1
[INFO] [action_client]:   [反馈] 当前: 0
[INFO] [action_client]: ✓ 成功: 倒计时完成！
```

---

## 10. 常用调试命令

```bash
# 查看所有 Action
ros2 action list

# 查看 Action 接口定义
ros2 interface show cpp04_action/action/CountDown

# 查看 Action 服务端信息
ros2 action info /count_down

# 命令行发送目标（无需启动客户端节点）
ros2 action send_goal /count_down cpp04_action/action/CountDown \
  "{countdown_from: 3}" --feedback
```

---

## 11. 关键 API 速查

### 服务端

| API | 说明 |
|-----|------|
| `rclcpp_action::create_server<T>(...)` | 创建 Action 服务端，注册三个回调 |
| `goal_handle->publish_feedback(fb)` | 发布实时反馈 |
| `goal_handle->succeed(result)` | 任务成功，发布结果 |
| `goal_handle->canceled(result)` | 任务已取消，发布结果 |
| `goal_handle->is_canceling()` | 检查是否收到取消请求 |

### 客户端

| API | 说明 |
|-----|------|
| `rclcpp_action::create_client<T>(node, 名称)` | 创建 Action 客户端 |
| `client_->wait_for_action_server(超时)` | 等待服务端上线 |
| `client_->async_send_goal(goal, options)` | 异步发送目标 |
| `result.code` | 结果状态：`SUCCEEDED` / `CANCELED` / `ABORTED` |

---

> 📌 **下一步建议**：
> - **参数（Parameter）**：节点运行时动态配置，参见 `ROS2_Parameter_Tutorial.md`
> - **生命周期节点（Lifecycle Node）**：受控启停
> - **组合节点（Component）**：多节点共享进程，降低通信开销
