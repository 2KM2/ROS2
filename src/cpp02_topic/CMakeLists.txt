cmake_minimum_required(VERSION 3.8)
project(cpp02_topic)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# 生成自定义消息
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Student.msg"
  DEPENDENCIES std_msgs
)

ament_export_dependencies(rosidl_default_runtime)

# 发布者节点
add_executable(student_publisher src/student_publisher.cpp)
ament_target_dependencies(student_publisher rclcpp)
rosidl_get_typesupport_target(cpp_typesupport_target ${PROJECT_NAME} "rosidl_typesupport_cpp")
target_link_libraries(student_publisher "${cpp_typesupport_target}")

# 订阅者节点
add_executable(student_subscriber src/student_subscriber.cpp)
ament_target_dependencies(student_subscriber rclcpp)
target_link_libraries(student_subscriber "${cpp_typesupport_target}")

install(TARGETS
  student_publisher
  student_subscriber
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
