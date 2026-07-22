import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    pkg_share = get_package_share_directory('tb3_mower_sim')
    slam_params_file = os.path.join(pkg_share, 'config', 'slam_params.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time')

    configured_params = RewrittenYaml(
        source_file=slam_params_file,
        param_rewrites={'use_sim_time': use_sim_time},
        convert_types=True,
    )

    slam_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[configured_params],
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        slam_node,
    ])
