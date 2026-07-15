cmake_minimum_required(VERSION 3.8)
project(cpp04_action)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# 生成自定义 Action 接口
rosidl_generate_interfaces(${PROJECT_NAME}
  "action/CountDown.action"
)

ament_export_dependencies(rosidl_default_runtime)

rosidl_get_typesupport_target(cpp_typesupport_target
  ${PROJECT_NAME} "rosidl_typesupport_cpp")

# Action 服务端
add_executable(action_server src/action_server.cpp)
ament_target_dependencies(action_server rclcpp rclcpp_action)
target_link_libraries(action_server "${cpp_typesupport_target}")

# Action 客户端
add_executable(action_client src/action_client.cpp)
ament_target_dependencies(action_client rclcpp rclcpp_action)
target_link_libraries(action_client "${cpp_typesupport_target}")

install(TARGETS action_server action_client
  DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
