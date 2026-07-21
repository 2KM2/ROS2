cmake_minimum_required(VERSION 3.8)
project(intelligent_mower_description)

find_package(ament_cmake REQUIRED)

install(DIRECTORY urdf launch config
  DESTINATION share/${PROJECT_NAME}
)
install(FILES README.md URDF_TUTORIAL.md RVIZ_SENSOR_TUTORIAL.md DESTINATION share/${PROJECT_NAME})

ament_package()
