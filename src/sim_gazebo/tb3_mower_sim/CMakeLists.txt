cmake_minimum_required(VERSION 3.8)
project(tb3_mower_sim)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  world launch config models urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
