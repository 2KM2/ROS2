import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory("mycar_slam_cartographer")
    configuration_directory = os.path.join(package_share, "config")
    use_sim_time = LaunchConfiguration("use_sim_time")

    cartographer_node = Node(
        package="cartographer_ros",
        executable="cartographer_node",
        name="cartographer_node",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
        arguments=[
            "-configuration_directory", configuration_directory,
            "-configuration_basename", "mycar_2d.lua",
        ],
        remappings=[
            ("scan", "/smartcar/scan"),
            ("odom", "/smartcar/odom"),
        ],
    )

    occupancy_grid_node = Node(
        package="cartographer_ros",
        executable="cartographer_occupancy_grid_node",
        name="cartographer_occupancy_grid_node",
        output="screen",
        parameters=[{
            "use_sim_time": use_sim_time,
            "resolution": 0.05,
            "publish_period_sec": 1.0,
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use the Gazebo simulation clock.",
        ),
        cartographer_node,
        occupancy_grid_node,
    ])
