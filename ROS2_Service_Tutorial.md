# ROS2 服务通信教程

> 基于 ROS2 Jazzy，C++ 实现
> 模式：请求 / 响应（Request / Response）

---

## 目录

1. [服务通信基本概念](#1-服务通信基本概念)
2. [话题 vs 服务 对比](#2-话题-vs-服务-对比)
3. [创建功能包](#3-创建功能包)
4. [包结构](#4-包结构)
5. [自定义服务文件 .srv](#5-自定义服务文件-srv)
6. [配置 package.xml 与 CMakeLists.txt](#6-配置-packagexml-与-cmakeliststxt)
7. [服务端节点](#7-服务端节点)
8. [客户端节点](#8-客户端节点)
9. [编译与运行](#9-编译与运行)
10. [常用调试命令](#10-常用调试命令)
11. [关键 API 速查](#11-关键-api-速查)

---

## 1. 服务通信基本概念

服务（Service）是 ROS2 中的**同步双向通信**方式，采用**请求 / 响应模型**：

```
客户端 (Client)  ──[ 请求 Request ]──▶  服务端 (Server)
客户端 (Client)  ◀─[ 响应 Response ]─  服务端 (Server)
```

- **服务端（Server）**：注册一个服务，等待客户端调用，处理请求后返回响应
- **客户端（Client）**：主动调用服务，发送请求并等待响应
- **服务类型**：`.srv` 文件定义，分为 `Request` 和 `Response` 两部分，用 `---` 分隔
- **一对多**：一个服务端可以被多个客户端调用，但同一时刻只处理一个请求

---

## 2. 话题 vs 服务 对比

| 特性 | 话题（Topic） | 服务（Service） |
|------|-------------|----------------|
| 通信模式 | 发布 / 订阅（单向） | 请求 / 响应（双向） |
| 适用场景 | 持续流式数据（传感器、状态） | 触发性操作（计算、查询、控制） |
| 是否等待响应 | 否（fire and forget） | 是（阻塞等待结果） |
| 消息定义 | `.msg` 文件 | `.srv` 文件（含 `---` 分隔） |
| 是否有反馈 | 无 | 有（Response） |
| 典型使用 | 激光雷达点云、IMU数据 | 开关电机、请求路径规划 |

---

## 3. 创建功能包

```bash
# 进入工作空间 src 目录
cd ~/workspace/ROS2/src

# 创建功能包，依赖 rclcpp 和 rosidl_default_generators
ros2 pkg create cpp03_service \
  --build-type ament_cmake \
  --dependencies rclcpp rosidl_default_generators

# 创建 srv 目录，存放 .srv 文件
mkdir -p cpp03_service/srv
```

---

## 4. 包结构

```
cpp03_service/
├── srv/
│   └── AddInts.srv          ← 自定义服务接口定义
├── src/
│   ├── service_server.cpp   ← 服务端：处理请求
│   └── service_client.cpp   ← 客户端：发起请求
├── CMakeLists.txt
└── package.xml
```

---

## 4. 自定义服务文件 .srv

`srv/AddInts.srv`：

```
# 请求部分（Request）
int64 a
int64 b
---
# 响应部分（Response）
int64 sum
string message
```

**`.srv` 文件规则：**

- 用 `---` 将文件分为上下两部分：上方为 **Request**，下方为 **Response**
- 字段类型与 `.msg` 文件完全相同（`int64`、`string`、`float32`、`bool` 等）
- 文件名使用大驼峰命名：`AddInts.srv` → 生成 `AddInts` 类型

**生成的 C++ 类型：**

```
服务文件：srv/AddInts.srv
→ 头文件：#include "cpp03_service/srv/add_ints.hpp"
→ 类型：  cpp03_service::srv::AddInts
→ 请求：  cpp03_service::srv::AddInts::Request
→ 响应：  cpp03_service::srv::AddInts::Response
```

---

## 5. 配置 package.xml 与 CMakeLists.txt

### package.xml

与自定义消息（`.msg`）配置相同，关键在于声明接口生成依赖：

```xml
<depend>rclcpp</depend>
<build_depend>rosidl_default_generators</build_depend>
<exec_depend>rosidl_default_runtime</exec_depend>
<member_of_group>rosidl_interface_packages</member_of_group>
```

### CMakeLists.txt

```cmake
find_package(rclcpp REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# 注册 .srv 文件，触发代码生成
rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/AddInts.srv"
)

ament_export_dependencies(rosidl_default_runtime)

# 获取本包生成的 C++ 类型支持目标
rosidl_get_typesupport_target(cpp_typesupport_target
  ${PROJECT_NAME} "rosidl_typesupport_cpp")

# 服务端
add_executable(service_server src/service_server.cpp)
ament_target_dependencies(service_server rclcpp)
target_link_libraries(service_server "${cpp_typesupport_target}")

# 客户端
add_executable(service_client src/service_client.cpp)
ament_target_dependencies(service_client rclcpp)
target_link_libraries(service_client "${cpp_typesupport_target}")

install(TARGETS service_server service_client
  DESTINATION lib/${PROJECT_NAME})
```

> ⚠️ 自定义 srv/msg 接口必须用 `target_link_libraries` + `rosidl_get_typesupport_target`，
> 而不是 `ament_target_dependencies`。

---

## 6. 服务端节点

```cpp
// src/service_server.cpp
#include "rclcpp/rclcpp.hpp"
#include "cpp03_service/srv/add_ints.hpp"

// 回调函数：接收请求，填写响应
void handle_add_ints(
  const std::shared_ptr<cpp03_service::srv::AddInts::Request> request,
  std::shared_ptr<cpp03_service::srv::AddInts::Response> response)
{
  response->sum     = request->a + request->b;
  response->message = std::to_string(request->a) + " + " +
                      std::to_string(request->b) + " = " +
                      std::to_string(response->sum);

  RCLCPP_INFO(rclcpp::get_logger("service_server"),
    "收到请求: a=%ld, b=%ld  →  响应: sum=%ld",
    request->a, request->b, response->sum);
}

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("service_server");

  // 创建服务：服务名 "add_ints"，绑定回调函数
  auto server = node->create_service<cpp03_service::srv::AddInts>(
    "add_ints", &handle_add_ints);

  RCLCPP_INFO(node->get_logger(), "服务端已就绪，等待请求...");
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
```

**服务端核心流程：**

```
rclcpp::init
    ↓
创建 Node
    ↓
create_service<T>(服务名, 回调函数)   ← 注册服务
    ↓
rclcpp::spin(node)                    ← 开始循环，等待请求
    ↓
[收到请求] → 触发回调 → 填写 response → 自动返回
```

---

## 7. 客户端节点

```cpp
// src/service_client.cpp
#include "rclcpp/rclcpp.hpp"
#include "cpp03_service/srv/add_ints.hpp"
#include <chrono>

using namespace std::chrono_literals;

class ServiceClient : public rclcpp::Node
{
public:
  ServiceClient() : Node("service_client")
  {
    // 创建客户端，服务名必须与服务端一致
    client_ = this->create_client<cpp03_service::srv::AddInts>("add_ints");
  }

  void send_request(int64_t a, int64_t b)
  {
    // 步骤 1：等待服务端上线
    while (!client_->wait_for_service(3s)) {
      if (!rclcpp::ok()) {
        RCLCPP_ERROR(this->get_logger(), "等待服务时被中断");
        return;
      }
      RCLCPP_WARN(this->get_logger(), "服务未就绪，继续等待...");
    }

    // 步骤 2：构造请求
    auto request = std::make_shared<cpp03_service::srv::AddInts::Request>();
    request->a = a;
    request->b = b;
    RCLCPP_INFO(this->get_logger(), "发送请求: %ld + %ld = ?", a, b);

    // 步骤 3：异步发送，同步等待结果
    auto future = client_->async_send_request(request);

    if (rclcpp::spin_until_future_complete(
          this->get_node_base_interface(), future) ==
        rclcpp::FutureReturnCode::SUCCESS)
    {
      auto response = future.get();
      RCLCPP_INFO(this->get_logger(),
        "收到响应: %s", response->message.c_str());
    } else {
      RCLCPP_ERROR(this->get_logger(), "服务调用失败");
    }
  }

private:
  rclcpp::Client<cpp03_service::srv::AddInts>::SharedPtr client_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<ServiceClient>();

  // 支持命令行传参：ros2 run cpp03_service service_client 3 7
  int64_t a = 10, b = 20;
  if (argc == 3) {
    a = std::stoll(argv[1]);
    b = std::stoll(argv[2]);
  }

  node->send_request(a, b);
  rclcpp::shutdown();
  return 0;
}
```

**客户端核心流程：**

```
rclcpp::init
    ↓
create_client<T>(服务名)
    ↓
wait_for_service()           ← 等待服务端上线
    ↓
构造 Request 并填充字段
    ↓
async_send_request(request)  ← 异步发送，返回 future
    ↓
spin_until_future_complete() ← 阻塞等待响应
    ↓
future.get()                 ← 获取 Response
```

---

## 8. 编译与运行

### 编译

```bash
cd ~/workspace/ROS2
colcon build --packages-select cpp03_service
source install/setup.bash
```

### 运行

**终端 1：启动服务端**

```bash
ros2 run cpp03_service service_server
```

输出：
```
[INFO] [service_server]: 服务端已就绪，等待请求...
```

**终端 2：启动客户端（默认 10 + 20）**

```bash
ros2 run cpp03_service service_client
```

或传入自定义参数：

```bash
ros2 run cpp03_service service_client 3 7
```

**预期完整交互输出：**

```
# 服务端
[INFO] [service_server]: 服务端已就绪，等待请求...
[INFO] [service_server]: 收到请求: a=3, b=7  →  响应: sum=10

# 客户端
[INFO] [service_client]: 发送请求: 3 + 7 = ?
[INFO] [service_client]: 收到响应: 3 + 7 = 10
```

---

## 9. 常用调试命令

```bash
# 查看当前所有活跃服务
ros2 service list

# 查看服务的接口类型
ros2 service type /add_ints

# 查看服务接口定义（Request / Response 字段）
ros2 interface show cpp03_service/srv/AddInts

# 在命令行直接调用服务（无需启动客户端节点）
ros2 service call /add_ints cpp03_service/srv/AddInts "{a: 5, b: 8}"

# 查看服务调用信息
ros2 service info /add_ints
```

`ros2 service call` 预期输出：
```
response:
  cpp03_service.srv.AddInts_Response(sum=13, message='5 + 8 = 13')
```

---

## 10. 关键 API 速查

### 服务端

| API | 说明 |
|-----|------|
| `node->create_service<T>(服务名, 回调)` | 创建服务，T 为服务类型 |
| `Request::SharedPtr` | 请求对象，回调入参 |
| `Response::SharedPtr` | 响应对象，回调入参，直接修改字段即返回 |

### 客户端

| API | 说明 |
|-----|------|
| `node->create_client<T>(服务名)` | 创建客户端 |
| `client_->wait_for_service(超时)` | 等待服务端上线，返回 `bool` |
| `client_->async_send_request(req)` | 异步发送请求，返回 `future` |
| `spin_until_future_complete(node, future)` | 阻塞等待 future 完成 |
| `future.get()` | 获取 `Response::SharedPtr` |

---

> 📌 **下一步建议**：
> - **动作通信（Action）**：适合长时间任务，带进度反馈（= 服务 + 话题的组合）
> - **参数（Parameter）**：节点运行时动态配置
> - **生命周期节点（Lifecycle Node）**：受控启停的节点状态机
