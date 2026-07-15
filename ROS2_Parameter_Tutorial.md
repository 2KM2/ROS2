# ROS2 参数（Parameter）教程

> 基于 ROS2 Jazzy，C++ 实现
> 功能：节点运行时动态声明、读取、修改参数

---

## 目录

1. [参数基本概念](#1-参数基本概念)
2. [创建功能包](#2-创建功能包)
3. [包结构](#3-包结构)
4. [CMakeLists.txt 配置](#4-cmakeliststxt-配置)
5. [参数节点实现](#5-参数节点实现)
6. [编译与运行](#6-编译与运行)
7. [常用调试命令](#7-常用调试命令)
8. [关键 API 速查](#8-关键-api-速查)

---

## 1. 参数基本概念

参数（Parameter）是 ROS2 节点的**运行时配置项**，相当于节点的全局变量，支持：

- 在节点内声明和读取
- 从命令行启动时传入
- 从 YAML 配置文件加载
- 运行中通过 `ros2 param set` 动态修改
- 注册回调，响应参数变更事件

**支持的参数类型：**

| C++ 类型 | 参数类型 | 读取方法 |
|---------|---------|--------|
| `bool` | `BOOL` | `.as_bool()` |
| `int64_t` | `INTEGER` | `.as_int()` |
| `double` | `DOUBLE` | `.as_double()` |
| `std::string` | `STRING` | `.as_string()` |
| `std::vector<bool>` | `BOOL_ARRAY` | `.as_bool_array()` |
| `std::vector<int64_t>` | `INTEGER_ARRAY` | `.as_integer_array()` |
| `std::vector<double>` | `DOUBLE_ARRAY` | `.as_double_array()` |
| `std::vector<std::string>` | `STRING_ARRAY` | `.as_string_array()` |

---

## 2. 创建功能包

```bash
# 进入工作空间 src 目录
cd ~/workspace/ROS2/src

# 创建功能包，只依赖 rclcpp（参数是 rclcpp 内置功能，无需额外依赖）
ros2 pkg create cpp05_param \
  --build-type ament_cmake \
  --dependencies rclcpp
```

---

## 3. 包结构

```
cpp05_param/
├── src/
│   └── param_node.cpp   ← 参数声明、读取、动态修改回调
├── CMakeLists.txt
└── package.xml
```

---

## 4. CMakeLists.txt 配置

参数是 `rclcpp` 的内置功能，**无需额外配置接口生成**，CMakeLists.txt 比自定义消息/服务简单很多：

```cmake
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)

add_executable(param_node src/param_node.cpp)
ament_target_dependencies(param_node rclcpp)

install(TARGETS param_node
  DESTINATION lib/${PROJECT_NAME})

ament_package()
```

---

## 5. 参数节点实现

```cpp
// src/param_node.cpp
#include "rclcpp/rclcpp.hpp"

class ParamNode : public rclcpp::Node
{
public:
  ParamNode() : Node("param_node")
  {
    // 步骤1：声明参数（参数名，默认值）
    // 节点必须先声明参数才能使用
    this->declare_parameter("robot_name",    "RoboA");
    this->declare_parameter("max_speed",     1.5);
    this->declare_parameter("loop_rate",     10);
    this->declare_parameter("auto_mode",     false);
    this->declare_parameter("target_rooms",
      std::vector<std::string>{"room1", "room2"});

    // 步骤2：读取并打印参数
    print_params();

    // 步骤3：注册参数变更回调（动态响应外部修改）
    param_cb_handle_ = this->add_on_set_parameters_callback(
      std::bind(&ParamNode::on_params_changed, this, std::placeholders::_1));

    // 定时器：每 3 秒打印一次，验证动态修改是否生效
    timer_ = this->create_wall_timer(
      std::chrono::seconds(3),
      std::bind(&ParamNode::print_params, this));
  }

private:
  void print_params()
  {
    RCLCPP_INFO(this->get_logger(), "========== 当前参数 ==========");
    RCLCPP_INFO(this->get_logger(), "  robot_name : %s",
      this->get_parameter("robot_name").as_string().c_str());
    RCLCPP_INFO(this->get_logger(), "  max_speed  : %.2f",
      this->get_parameter("max_speed").as_double());
    RCLCPP_INFO(this->get_logger(), "  loop_rate  : %ld",
      this->get_parameter("loop_rate").as_int());
    RCLCPP_INFO(this->get_logger(), "  auto_mode  : %s",
      this->get_parameter("auto_mode").as_bool() ? "true" : "false");

    auto rooms = this->get_parameter("target_rooms").as_string_array();
    std::string rooms_str;
    for (size_t i = 0; i < rooms.size(); ++i) {
      rooms_str += rooms[i];
      if (i + 1 < rooms.size()) rooms_str += ", ";
    }
    RCLCPP_INFO(this->get_logger(), "  target_rooms: [%s]", rooms_str.c_str());
  }

  // 参数变更回调：对修改请求做验证，返回是否允许
  rcl_interfaces::msg::SetParametersResult on_params_changed(
    const std::vector<rclcpp::Parameter> & params)
  {
    rcl_interfaces::msg::SetParametersResult result;
    result.successful = true;

    for (const auto & param : params) {
      RCLCPP_INFO(this->get_logger(), "参数被修改: %s = %s",
        param.get_name().c_str(), param.value_to_string().c_str());

      // 示例：限制 max_speed 最大值
      if (param.get_name() == "max_speed" && param.as_double() > 5.0) {
        result.successful = false;
        result.reason     = "max_speed 不能超过 5.0";
        RCLCPP_WARN(this->get_logger(), "验证失败: %s", result.reason.c_str());
      }
    }
    return result;
  }

  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr param_cb_handle_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ParamNode>());
  rclcpp::shutdown();
  return 0;
}
```

---

## 6. 编译与运行

### 编译

```bash
cd ~/workspace/ROS2
colcon build --packages-select cpp05_param
source install/setup.bash
```

### 运行

**基本运行（使用默认参数值）：**

```bash
ros2 run cpp05_param param_node
```

**启动时通过命令行传入参数（覆盖默认值）：**

```bash
ros2 run cpp05_param param_node \
  --ros-args \
  -p robot_name:=RoboX \
  -p max_speed:=2.5 \
  -p loop_rate:=20 \
  -p auto_mode:=true
```

**从 YAML 文件加载参数：**

```bash
# 先创建参数文件 params.yaml
# 然后加载
ros2 run cpp05_param param_node \
  --ros-args --params-file ~/workspace/ROS2/params.yaml
```

`params.yaml` 示例：

```yaml
param_node:
  ros__parameters:
    robot_name: "RoboY"
    max_speed: 3.0
    loop_rate: 15
    auto_mode: true
    target_rooms:
      - "kitchen"
      - "bedroom"
      - "hallway"
```

---

## 7. 常用调试命令

```bash
# 列出节点的所有参数
ros2 param list /param_node

# 获取单个参数值
ros2 param get /param_node robot_name
ros2 param get /param_node max_speed

# 动态修改参数（节点运行时生效，触发回调）
ros2 param set /param_node robot_name "RoboZ"
ros2 param set /param_node max_speed 3.5
ros2 param set /param_node auto_mode true

# 尝试修改超出验证范围的值（会被回调拒绝）
ros2 param set /param_node max_speed 9.9

# 将当前参数值导出为 YAML 文件（方便保存配置）
ros2 param dump /param_node

# 从文件批量加载参数（节点已运行时）
ros2 param load /param_node ~/workspace/ROS2/params.yaml
```

---

## 8. 关键 API 速查

| API | 说明 |
|-----|------|
| `declare_parameter(名称, 默认值)` | 声明参数，必须先声明后使用 |
| `get_parameter(名称)` | 获取参数对象（`rclcpp::Parameter`） |
| `get_parameter(名称).as_string()` | 读取为字符串 |
| `get_parameter(名称).as_double()` | 读取为浮点数 |
| `get_parameter(名称).as_int()` | 读取为整数 |
| `get_parameter(名称).as_bool()` | 读取为布尔值 |
| `get_parameter(名称).as_string_array()` | 读取为字符串数组 |
| `set_parameter(rclcpp::Parameter(...))` | 在节点内部修改参数 |
| `add_on_set_parameters_callback(回调)` | 注册参数变更回调 |
| `param.get_name()` | 获取参数名 |
| `param.value_to_string()` | 参数值转字符串（调试用） |

---

> 📌 **小结**
>
> | 配置方式 | 适用场景 |
> |---------|---------|
> | 代码默认值 `declare_parameter` | 最基础的默认配置 |
> | 命令行 `-p key:=value` | 单次启动临时覆盖 |
> | YAML 文件 `--params-file` | 多参数批量配置、复用配置 |
> | `ros2 param set` | 节点运行中动态调整 |
