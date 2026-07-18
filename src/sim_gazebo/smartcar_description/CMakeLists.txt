cmake_minimum_required(VERSION 3.8)
project(smartcar_description)

find_package(ament_cmake REQUIRED)

install(
  FILES
    urdf/smartcar.urdf.xacro
  DESTINATION share/${PROJECT_NAME}/urdf
)

install(
  FILES
    launch/smartcar_sim.launch.py
  DESTINATION share/${PROJECT_NAME}/launch
)

install(
  FILES
    config/smartcar_ros2.rviz
  DESTINATION share/${PROJECT_NAME}/config
)

install(
  FILES
    README_ROS2.md
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
