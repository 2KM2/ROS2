#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch.actions import DeclareLaunchArgument, OpaqueFunction, SetLaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
def generate_launch_description():

    return LaunchDescription([
        Node(
            package="stage_ros2",
            executable="stage_ros2",
            parameters=[{
                "world_file":os.path.join(get_package_share_directory("demo_stage_sim"),"world","sim.world")
            }
            ]
        )
    ])