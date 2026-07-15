cmake_minimum_required(VERSION 3.8)
project(cpp03_service)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# 生成自定义服务接口
rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/AddInts.srv"
)

ament_export_dependencies(rosidl_default_runtime)

# 获取本包生成的 C++ 类型支持目标
rosidl_get_typesupport_target(cpp_typesupport_target
  ${PROJECT_NAME} "rosidl_typesupport_cpp")

# 服务端节点
add_executable(service_server src/service_server.cpp)
ament_target_dependencies(service_server rclcpp)
target_link_libraries(service_server "${cpp_typesupport_target}")

# 客户端节点
add_executable(service_client src/service_client.cpp)
ament_target_dependencies(service_client rclcpp)
target_link_libraries(service_client "${cpp_typesupport_target}")

install(TARGETS
  service_server
  service_client
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
