cmake_minimum_required(VERSION 3.8)
project(cpp06_lifecycle)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)
find_package(std_msgs REQUIRED)

# 生命周期节点
add_executable(lifecycle_node src/lifecycle_node.cpp)
ament_target_dependencies(lifecycle_node rclcpp rclcpp_lifecycle std_msgs)

# 生命周期控制器（发送状态转移命令）
add_executable(lifecycle_controller src/lifecycle_controller.cpp)
ament_target_dependencies(lifecycle_controller rclcpp lifecycle_msgs)

install(TARGETS lifecycle_node lifecycle_controller
  DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
