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
    smartcar_share = get_package_share_directory('smartcar_description')
    demo_share = get_package_share_directory('demo_gazebo_sim')
    xacro_file = os.path.join(smartcar_share, 'urdf', 'smartcar.urdf.xacro')
    rviz_file = os.path.join(smartcar_share, 'config', 'smartcar_ros2.rviz')
    world_launch = os.path.join(
        demo_share, 'launch', 'gazebo_sim_world.launch.py'
    )
    default_world = os.path.join(demo_share, 'world', 'house.sdf')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str,
    )

    world = LaunchConfiguration('world')
    use_rviz = LaunchConfiguration('use_rviz')
    headless = LaunchConfiguration('headless')
    spawn_x = LaunchConfiguration('spawn_x')
    spawn_y = LaunchConfiguration('spawn_y')
    spawn_yaw = LaunchConfiguration('spawn_yaw')

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(world_launch),
        launch_arguments={
            'world': world,
            'headless': headless,
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
        period=3.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                arguments=[
                    '-world', 'house_100sqm',
                    '-topic', '/robot_description',
                    '-name', 'smartcar',
                    '-allow_renaming', 'false',
                    '-x', spawn_x,
                    '-y', spawn_y,
                    '-z', '0.1',
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
            '/smartcar/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/smartcar/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/smartcar/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/smartcar/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/smartcar/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/smartcar/scan/points@sensor_msgs/msg/PointCloud2'
            '[gz.msgs.PointCloudPacked',
            '/smartcar/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            '/smartcar/camera/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/smartcar/camera/camera_info@sensor_msgs/msg/CameraInfo'
            '[gz.msgs.CameraInfo',
        ],
        remappings=[
            ('/smartcar/tf', '/tf'),
            ('/smartcar/joint_states', '/joint_states'),
            ('/smartcar/cmd_vel', '/cmd_vel'),
            ('/smartcar/camera/camera_info',
             '/smartcar/camera/image/camera_info'),
        ],
        parameters=[{
            'qos_overrides./smartcar/scan.publisher.reliability':
                'best_effort',
            'qos_overrides./smartcar/scan/points.publisher.reliability':
                'best_effort',
            'qos_overrides./smartcar/camera/image.publisher.reliability':
                'best_effort',
            'qos_overrides./smartcar/camera/image/camera_info.publisher.'
            'reliability': 'best_effort',
        }],
        output='screen',
    )

    lidar_frame = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0',
            '--roll', '0', '--pitch', '0', '--yaw', '0',
            '--frame-id', 'lidar_link',
            '--child-frame-id', 'smartcar/lidar_link/lidar_sensor',
        ],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_file],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(use_rviz),
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world', default_value=default_world,
            description='SDF world used by the smart car simulation',
        ),
        DeclareLaunchArgument(
            'use_rviz', default_value='true',
            description='Start RViz',
        ),
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='Run Gazebo without the GUI',
        ),
        DeclareLaunchArgument('spawn_x', default_value='0.0'),
        DeclareLaunchArgument('spawn_y', default_value='-4.0'),
        DeclareLaunchArgument('spawn_yaw', default_value='1.5708'),
        gazebo,
        state_publisher,
        bridge,
        lidar_frame,
        spawn,
        rviz,
    ])
