"""
Intelligent mower simulation in a 1000 m² residential lawn.

Spawns a custom 750x550x280mm skid-steer mower robot equipped with:
  - 360° 2D LiDAR (720 samples, 12m range)
  - Stereo camera (120mm baseline, 640x480@15Hz)
  - IMU (100Hz)

World: 40m x 25m fenced lawn with trees, flower beds, furniture,
narrow passages, and a charging station.

Usage:
  ros2 launch tb3_mower_sim tb3_mower_sim.launch.py
  ros2 launch tb3_mower_sim tb3_mower_sim.launch.py use_rviz:=false headless:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = get_package_share_directory('tb3_mower_sim')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')

    world_file = os.path.join(pkg_share, 'world', 'lawn_1000sqm.sdf')
    rviz_config = os.path.join(pkg_share, 'config', 'tb3_mower.rviz')
    urdf_file = os.path.join(pkg_share, 'urdf', 'mower.urdf.xacro')

    use_rviz = LaunchConfiguration('use_rviz')
    headless = LaunchConfiguration('headless')
    spawn_x = LaunchConfiguration('spawn_x')
    spawn_y = LaunchConfiguration('spawn_y')
    spawn_yaw = LaunchConfiguration('spawn_yaw')

    robot_description = ParameterValue(
        Command(['xacro ', urdf_file]),
        value_type=str,
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': [
                PythonExpression([
                    "'-s --headless-rendering ' if '",
                    headless,
                    "' == 'true' else ''",
                ]),
                '-r -v 4 ', world_file,
            ],
        }.items(),
    )

    state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
        output='screen',
    )

    spawn = TimerAction(
        period=4.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                arguments=[
                    '-world', 'lawn_1000sqm',
                    '-topic', '/robot_description',
                    '-name', 'intelligent_mower',
                    '-x', spawn_x,
                    '-y', spawn_y,
                    '-z', '0.05',
                    '-Y', spawn_yaw,
                ],
                output='screen',
            )
        ],
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            '/stereo/left/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/stereo/right/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
        ],
        parameters=[{
            'use_sim_time': True,
            'qos_overrides./scan.publisher.reliability': 'best_effort',
            'qos_overrides./stereo/left/image_raw.publisher.reliability': 'best_effort',
            'qos_overrides./stereo/right/image_raw.publisher.reliability': 'best_effort',
        }],
        output='screen',
    )

    lidar_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0',
            '--roll', '0', '--pitch', '0', '--yaw', '0',
            '--frame-id', 'lidar_link',
            '--child-frame-id', 'intelligent_mower/lidar_link/lidar',
        ],
        parameters=[{'use_sim_time': True}],
    )

    imu_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0',
            '--roll', '0', '--pitch', '0', '--yaw', '0',
            '--frame-id', 'imu_link',
            '--child-frame-id', 'intelligent_mower/imu_link/imu',
        ],
        parameters=[{'use_sim_time': True}],
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(use_rviz),
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('spawn_x', default_value='0.0',
                             description='Near charging station'),
        DeclareLaunchArgument('spawn_y', default_value='-11.0',
                             description='Near south gate'),
        DeclareLaunchArgument('spawn_yaw', default_value='1.5708',
                             description='Facing north'),
        gazebo,
        state_publisher,
        bridge,
        lidar_tf,
        imu_tf,
        spawn,
        rviz,
    ])
