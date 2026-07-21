import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Launch the furnished house, cleaning robot, bridges, and RViz."""
    package_share = get_package_share_directory('demo_gazebo_sim')
    world_launch = os.path.join(
        package_share, 'launch', 'gazebo_sim_world.launch.py'
    )
    default_world = os.path.join(package_share, 'world', 'house.sdf')
    robot_file = os.path.join(package_share, 'urdf', 'cleaning_robot.urdf')
    rviz_config = os.path.join(
        package_share, 'rviz', 'cleaning_robot.rviz'
    )

    with open(robot_file, 'r', encoding='utf-8') as urdf_file:
        robot_description = urdf_file.read()

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

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
        output='screen',
    )

    # Gazebo scopes the lidar message frame with model / link / sensor names.
    # The sensor pose is the lidar_link origin, so this transform is identity.
    lidar_frame_bridge = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0',
            '--roll', '0', '--pitch', '0', '--yaw', '0',
            '--frame-id', 'lidar_link',
            '--child-frame-id', 'cleaning_robot/lidar_link/laser_scan',
        ],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    # Delay creation until the Gazebo world-create service is available.
    spawn_robot = TimerAction(
        period=3.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                arguments=[
                    '-world', 'mowing_field_5000sqm',
                    '-file', robot_file,
                    '-name', 'cleaning_robot',
                    '-allow_renaming', 'false',
                    '-x', spawn_x,
                    '-y', spawn_y,
                    '-z', '0.0',
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
            '/scan/points@sensor_msgs/msg/PointCloud2'
            '[gz.msgs.PointCloudPacked',
        ],
        parameters=[{
            'qos_overrides./scan.publisher.reliability': 'best_effort',
            'qos_overrides./scan/points.publisher.reliability': 'best_effort',
        }],
        output='screen',
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
        DeclareLaunchArgument(
            'world',
            default_value=default_world,
            description='Absolute path to the furnished house SDF',
        ),
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Start RViz with robot and point-cloud displays',
        ),
        DeclareLaunchArgument(
            'headless',
            default_value='false',
            description='Run Gazebo without its GUI',
        ),
        DeclareLaunchArgument(
            'spawn_x',
            default_value='0.0',
            description='Robot initial X position in metres',
        ),
        DeclareLaunchArgument(
            'spawn_y',
            default_value='-4.2',
            description='Robot initial Y position in metres',
        ),
        DeclareLaunchArgument(
            'spawn_yaw',
            default_value='1.5708',
            description='Robot initial yaw in radians',
        ),
        gazebo,
        robot_state_publisher,
        lidar_frame_bridge,
        bridge,
        spawn_robot,
        rviz,
    ])
