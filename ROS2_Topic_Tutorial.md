# ROS2 话题通信教程

> 基于 ROS2 Jazzy，C++ 实现
> 包含：原生消息类型 与 自定义接口消息

---

## 目录

1. [话题通信基本概念](#1-话题通信基本概念)
2. [原生消息类型（cpp01_topic）](#2-原生消息类型cpp01_topic)
   - [创建功能包](#21-创建功能包)
   - [包结构](#22-包结构)
   - [发布者](#23-发布者节点)
   - [订阅者](#24-订阅者节点)
   - [CMakeLists.txt 配置](#25-cmakeliststxt-配置)
   - [编译与运行](#26-编译与运行)
3. [自定义接口消息（cpp02_topic）](#3-自定义接口消息cpp02_topic)
   - [为什么需要自定义消息](#31-为什么需要自定义消息)
   - [创建功能包](#32-创建功能包)
   - [包结构](#33-包结构)
   - [定义消息文件](#34-定义消息文件-msg)
   - [配置消息生成](#35-配置消息生成)
   - [发布者](#36-发布者节点)
   - [订阅者](#37-订阅者节点)
   - [编译与运行](#38-编译与运行)
4. [常用调试命令](#4-常用调试命令)
5. [对比总结](#5-对比总结)

---

## 1. 话题通信基本概念

话题（Topic）是 ROS2 中最常用的通信方式，采用**发布/订阅模型**：

```
发布者 (Publisher)  ──[ /话题名 ]──▶  订阅者 (Subscriber)
```

- **发布者**：持续向话题发送消息，不关心是否有人接收
- **订阅者**：监听话题，每次收到消息触发回调函数
- **消息类型**：话题传输的数据结构，发布者和订阅者必须使用相同类型
- **队列长度（QoS）**：缓冲来不及处理的消息条数

---

## 2. 原生消息类型（cpp01_topic）

### 2.1 创建功能包

```bash
# 进入工作空间 src 目录
cd ~/workspace/ROS2/src

# 创建功能包，依赖 rclcpp 和 std_msgs
ros2 pkg create cpp01_topic \
  --build-type ament_cmake \
  --dependencies rclcpp std_msgs
```

### 2.2 包结构

```
cpp01_topic/
├── src/
│   ├── topic_publisher.cpp
│   └── topic_subscriber.cpp
├── CMakeLists.txt
└── package.xml
```

### 2.3 发布者节点

使用 `std_msgs/msg/String` 发布字符串消息，每 500ms 发送一次。

```cpp
// src/topic_publisher.cpp
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

class TopicPublisher : public rclcpp::Node
{
public:
  TopicPublisher() : Node("topic_publisher"), count_(0)
  {
    // 创建发布者：话题名 "hello_topic"，队列长度 10
    publisher_ = this->create_publisher<std_msgs::msg::String>("hello_topic", 10);

    // 定时器：每 500ms 触发一次回调
    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(500),
      std::bind(&TopicPublisher::timer_callback, this));
  }

private:
  void timer_callback()
  {
    auto msg = std_msgs::msg::String();
    msg.data = "Hello World! count: " + std::to_string(count_++);
    RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", msg.data.c_str());
    publisher_->publish(msg);
  }

  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
  size_t count_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<TopicPublisher>());
  rclcpp::shutdown();
  return 0;
}
```

**关键 API：**

| API | 说明 |
|-----|------|
| `create_publisher<T>(话题名, 队列长度)` | 创建发布者，T 为消息类型 |
| `create_wall_timer(间隔, 回调)` | 创建定时器 |
| `publisher_->publish(msg)` | 发布消息 |

### 2.3 订阅者节点

```cpp
// src/topic_subscriber.cpp
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

class TopicSubscriber : public rclcpp::Node
{
public:
  TopicSubscriber() : Node("topic_subscriber")
  {
    // 创建订阅者：话题名、队列长度、回调函数
    subscription_ = this->create_subscription<std_msgs::msg::String>(
      "hello_topic", 10,
      std::bind(&TopicSubscriber::topic_callback, this, std::placeholders::_1));
  }

private:
  void topic_callback(const std_msgs::msg::String & msg)
  {
    RCLCPP_INFO(this->get_logger(), "Received: '%s'", msg.data.c_str());
  }

  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<TopicSubscriber>());
  rclcpp::shutdown();
  return 0;
}
```

**关键 API：**

| API | 说明 |
|-----|------|
| `create_subscription<T>(话题名, 队列长度, 回调)` | 创建订阅者 |
| `std::placeholders::_1` | 占位符，表示回调的第一个参数（消息本身） |

### 2.4 CMakeLists.txt 配置

```cmake
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

add_executable(topic_publisher src/topic_publisher.cpp)
ament_target_dependencies(topic_publisher rclcpp std_msgs)

add_executable(topic_subscriber src/topic_subscriber.cpp)
ament_target_dependencies(topic_subscriber rclcpp std_msgs)

install(TARGETS
  topic_publisher
  topic_subscriber
  DESTINATION lib/${PROJECT_NAME}
)
```

### 2.5 运行

```bash
# 编译
cd ~/workspace/ROS2
colcon build --packages-select cpp01_topic
source install/setup.bash

# 终端 1：启动发布者
ros2 run cpp01_topic topic_publisher

# 终端 2：启动订阅者
ros2 run cpp01_topic topic_subscriber
```

预期输出：

```
# 发布者
[INFO] [topic_publisher]: Publishing: 'Hello World! count: 0'
[INFO] [topic_publisher]: Publishing: 'Hello World! count: 1'

# 订阅者
[INFO] [topic_subscriber]: Received: 'Hello World! count: 0'
[INFO] [topic_subscriber]: Received: 'Hello World! count: 1'
```

---

## 3. 自定义接口消息（cpp02_topic）

### 3.1 为什么需要自定义消息

原生消息（如 `std_msgs/String`）只能传递单一数据。当需要一次传递**多个相关字段**（如学生的姓名、年龄、班级等），就需要定义自己的消息类型。

### 3.2 创建功能包

```bash
cd ~/workspace/ROS2/src

# 多了 rosidl_default_generators 依赖，用于生成自定义消息代码
ros2 pkg create cpp02_topic \
  --build-type ament_cmake \
  --dependencies rclcpp std_msgs rosidl_default_generators

# 创建 msg 目录，存放 .msg 文件
mkdir -p cpp02_topic/msg
```

### 3.3 包结构

```
cpp02_topic/
├── msg/
│   └── Student.msg        ← 自定义消息定义文件
├── src/
│   ├── student_publisher.cpp
│   └── student_subscriber.cpp
├── CMakeLists.txt
└── package.xml
```

### 3.3 定义消息文件 `.msg`

`msg/Student.msg`：

```
# 学生自定义消息
string name        # 姓名
uint8  age         # 年龄
string class_name  # 班级
string gender      # 性别 male/female
float32 score      # 成绩
string[] hobbies   # 爱好列表（数组）
```

**常用字段类型：**

| 类型 | 说明 | 示例 |
|------|------|------|
| `bool` | 布尔 | `true` / `false` |
| `int8` / `int16` / `int32` / `int64` | 有符号整数 | `-128` ~ `127` |
| `uint8` / `uint16` / `uint32` / `uint64` | 无符号整数 | `0` ~ `255` |
| `float32` / `float64` | 浮点数 | `3.14` |
| `string` | 字符串 | `"hello"` |
| `T[]` | 动态数组 | `string[]` |
| `T[N]` | 固定长度数组 | `float32[3]` |

### 3.4 配置消息生成

**package.xml** 中必须声明消息生成依赖：

```xml
<build_depend>rosidl_default_generators</build_depend>
<exec_depend>rosidl_default_runtime</exec_depend>
<member_of_group>rosidl_interface_packages</member_of_group>
```

**CMakeLists.txt** 中注册消息文件并链接生成的类型支持：

```cmake
find_package(rosidl_default_generators REQUIRED)

# 注册 .msg 文件，触发代码生成
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Student.msg"
  DEPENDENCIES std_msgs
)

ament_export_dependencies(rosidl_default_runtime)

# 获取本包生成的 C++ 类型支持目标
rosidl_get_typesupport_target(cpp_typesupport_target
  ${PROJECT_NAME} "rosidl_typesupport_cpp")

add_executable(student_publisher src/student_publisher.cpp)
ament_target_dependencies(student_publisher rclcpp)
target_link_libraries(student_publisher "${cpp_typesupport_target}")

add_executable(student_subscriber src/student_subscriber.cpp)
ament_target_dependencies(student_subscriber rclcpp)
target_link_libraries(student_subscriber "${cpp_typesupport_target}")
```

> ⚠️ 自定义消息用 `target_link_libraries` 链接，而不是 `ament_target_dependencies`。

### 3.5 发布者节点

```cpp
// src/student_publisher.cpp
#include "rclcpp/rclcpp.hpp"
#include "cpp02_topic/msg/student.hpp"  // 头文件由编译自动生成
                                         // 规则：包名/msg/消息名(小写).hpp

class StudentPublisher : public rclcpp::Node
{
public:
  StudentPublisher() : Node("student_publisher"), count_(0)
  {
    publisher_ = this->create_publisher<cpp02_topic::msg::Student>("student_topic", 10);
    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(1000),
      std::bind(&StudentPublisher::timer_callback, this));
  }

private:
  void timer_callback()
  {
    auto msg = cpp02_topic::msg::Student();

    // 轮流发布三个学生信息
    switch (count_ % 3) {
      case 0:
        msg.name       = "张三";
        msg.age        = 18;
        msg.class_name = "计算机2301";
        msg.gender     = "male";
        msg.score      = 92.5f;
        msg.hobbies    = {"编程", "篮球", "音乐"};
        break;
      case 1:
        msg.name       = "李四";
        msg.age        = 19;
        msg.class_name = "软件工程2302";
        msg.gender     = "male";
        msg.score      = 85.0f;
        msg.hobbies    = {"游戏", "动漫"};
        break;
      case 2:
        msg.name       = "王五";
        msg.age        = 17;
        msg.class_name = "人工智能2303";
        msg.gender     = "female";
        msg.score      = 97.0f;
        msg.hobbies    = {"机器学习", "跑步", "绘画"};
        break;
    }

    RCLCPP_INFO(this->get_logger(),
      "Publishing => 姓名:%s  年龄:%d  班级:%s  成绩:%.1f",
      msg.name.c_str(), msg.age, msg.class_name.c_str(), msg.score);

    publisher_->publish(msg);
    count_++;
  }

  rclcpp::Publisher<cpp02_topic::msg::Student>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
  size_t count_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<StudentPublisher>());
  rclcpp::shutdown();
  return 0;
}
```

**头文件引入规则：**

```
消息文件路径：msg/Student.msg
→ 生成头文件：#include "<包名>/msg/<消息名小写>.hpp"
→ 命名空间：  <包名>::msg::<消息名>

示例：
  #include "cpp02_topic/msg/student.hpp"
  cpp02_topic::msg::Student msg;
```

### 3.6 订阅者节点

```cpp
// src/student_subscriber.cpp
#include "rclcpp/rclcpp.hpp"
#include "cpp02_topic/msg/student.hpp"

class StudentSubscriber : public rclcpp::Node
{
public:
  StudentSubscriber() : Node("student_subscriber")
  {
    subscription_ = this->create_subscription<cpp02_topic::msg::Student>(
      "student_topic", 10,
      std::bind(&StudentSubscriber::topic_callback, this, std::placeholders::_1));
  }

private:
  void topic_callback(const cpp02_topic::msg::Student & msg)
  {
    RCLCPP_INFO(this->get_logger(), "---------- 收到学生信息 ----------");
    RCLCPP_INFO(this->get_logger(), "  姓名: %s", msg.name.c_str());
    RCLCPP_INFO(this->get_logger(), "  年龄: %d", msg.age);
    RCLCPP_INFO(this->get_logger(), "  班级: %s", msg.class_name.c_str());
    RCLCPP_INFO(this->get_logger(), "  性别: %s", msg.gender.c_str());
    RCLCPP_INFO(this->get_logger(), "  成绩: %.1f", msg.score);

    // 遍历数组字段
    std::string hobbies_str;
    for (size_t i = 0; i < msg.hobbies.size(); ++i) {
      hobbies_str += msg.hobbies[i];
      if (i + 1 < msg.hobbies.size()) hobbies_str += "、";
    }
    RCLCPP_INFO(this->get_logger(), "  爱好: %s", hobbies_str.c_str());
  }

  rclcpp::Subscription<cpp02_topic::msg::Student>::SharedPtr subscription_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<StudentSubscriber>());
  rclcpp::shutdown();
  return 0;
}
```

### 3.7 运行

```bash
# 编译
cd ~/workspace/ROS2
colcon build --packages-select cpp02_topic
source install/setup.bash

# 终端 1：启动发布者
ros2 run cpp02_topic student_publisher

# 终端 2：启动订阅者
ros2 run cpp02_topic student_subscriber
```

预期输出：

```
# 订阅者
[INFO] [student_subscriber]: ---------- 收到学生信息 ----------
[INFO] [student_subscriber]:   姓名: 张三
[INFO] [student_subscriber]:   年龄: 18
[INFO] [student_subscriber]:   班级: 计算机2301
[INFO] [student_subscriber]:   性别: male
[INFO] [student_subscriber]:   成绩: 92.5
[INFO] [student_subscriber]:   爱好: 编程、篮球、音乐
```

---

## 4. 常用调试命令

```bash
# 查看当前所有活跃话题
ros2 topic list

# 实时打印话题内容
ros2 topic echo /hello_topic
ros2 topic echo /student_topic

# 查看话题的消息类型
ros2 topic info /student_topic

# 查看自定义消息的字段定义
ros2 interface show cpp02_topic/msg/Student

# 查看话题发布频率
ros2 topic hz /student_topic

# 手动发布一条消息（测试订阅者）
ros2 topic pub /hello_topic std_msgs/msg/String "{data: 'test message'}"
```

---

## 5. 对比总结

| 对比项 | 原生消息（std_msgs） | 自定义消息 |
|--------|---------------------|-----------|
| 适用场景 | 简单数据（单个字符串、数字） | 多字段复合数据 |
| 消息定义 | 无需定义，直接使用 | 需创建 `.msg` 文件 |
| 头文件 | `#include "std_msgs/msg/string.hpp"` | `#include "包名/msg/消息名.hpp"` |
| CMake 链接 | `ament_target_dependencies` | `target_link_libraries` + `rosidl_get_typesupport_target` |
| package.xml | `<depend>std_msgs</depend>` | 需额外声明 `rosidl_default_generators/runtime` |
| 编译额外步骤 | 无 | `rosidl_generate_interfaces` 触发代码生成 |
| 数组支持 | 有限 | 原生支持 `T[]` 动态数组、`T[N]` 固定数组 |

---

> 📌 **下一步建议**：
> - 学习 **服务通信（Service）**：适合请求-响应模式
> - 学习 **参数（Parameter）**：运行时动态配置节点
> - 学习 **动作（Action）**：适合长时间任务（带进度反馈）
