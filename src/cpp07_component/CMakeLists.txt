cmake_minimum_required(VERSION 3.8)
project(cpp07_component)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(std_msgs REQUIRED)

# ── 发布者组件（编译为共享库）
add_library(talker_component SHARED src/talker_component.cpp)
ament_target_dependencies(talker_component rclcpp rclcpp_components std_msgs)
rclcpp_components_register_node(talker_component
  PLUGIN "cpp07_component::TalkerComponent"
  EXECUTABLE talker_node)

# ── 订阅者组件（编译为共享库）
add_library(listener_component SHARED src/listener_component.cpp)
ament_target_dependencies(listener_component rclcpp rclcpp_components std_msgs)
rclcpp_components_register_node(listener_component
  PLUGIN "cpp07_component::ListenerComponent"
  EXECUTABLE listener_node)

install(TARGETS
  talker_component
  listener_component
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
