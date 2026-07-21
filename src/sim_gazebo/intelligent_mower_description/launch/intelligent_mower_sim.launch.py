import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    package_share = get_package_share_directory('intelligent_mower_description')
    gazebo_demo_share = get_package_share_directory('demo_gazebo_sim')
    rviz_config = os.path.join(package_share, 'config', 'intelligent_mower.rviz')
    robot_description = ParameterValue(Command([
        'xacro ', os.path.join(package_share, 'urdf', 'intelligent_mower.urdf.xacro')
    ]), value_type=str)
    world = LaunchConfiguration('world')
    use_rviz = LaunchConfiguration('use_rviz')
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            gazebo_demo_share, 'launch', 'gazebo_sim_world.launch.py')),
        launch_arguments={'world': world}.items())
    state_publisher = Node(package='robot_state_publisher', executable='robot_state_publisher',
                           parameters=[{'robot_description': robot_description, 'use_sim_time': True}])
    spawn = TimerAction(period=3.0, actions=[Node(
        package='ros_gz_sim', executable='create',
        arguments=['-world', 'mowing_field_5000sqm', '-topic', '/robot_description',
                   '-name', 'intelligent_mower', '-x', '0', '-y', '-4', '-z', '0.08'])])
    bridge = Node(package='ros_gz_bridge', executable='parameter_bridge', arguments=[
        '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        '/intelligent_mower/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
        '/intelligent_mower/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
        '/intelligent_mower/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
        '/intelligent_mower/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
        '/intelligent_mower/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
        '/intelligent_mower/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
        '/intelligent_mower/camera/image@sensor_msgs/msg/Image[gz.msgs.Image'],
        remappings=[('/intelligent_mower/cmd_vel', '/cmd_vel'),
                    ('/intelligent_mower/tf', '/tf'),
                    ('/intelligent_mower/joint_states', '/joint_states')],
        parameters=[{'qos_overrides./intelligent_mower/scan.publisher.reliability': 'best_effort',
                     'qos_overrides./intelligent_mower/camera/image.publisher.reliability': 'best_effort'}])
    lidar_sensor_tf = Node(
        package='tf2_ros', executable='static_transform_publisher',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0',
            '--roll', '0', '--pitch', '0', '--yaw', '0',
            '--frame-id', 'lidar_link',
            '--child-frame-id', 'intelligent_mower/lidar_link/lidar',
        ],
        parameters=[{'use_sim_time': True}],
    )
    rviz = Node(
        package='rviz2', executable='rviz2', arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}], condition=IfCondition(use_rviz))
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value=os.path.join(gazebo_demo_share, 'world', 'house.sdf')),
        DeclareLaunchArgument('use_rviz', default_value='true', description='Start RViz with lidar and camera displays'),
        gazebo, state_publisher, bridge, lidar_sensor_tf, spawn, rviz])
