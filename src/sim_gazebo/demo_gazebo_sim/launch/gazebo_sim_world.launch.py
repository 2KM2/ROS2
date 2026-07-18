import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """Launch Gazebo Sim with the 100 m² house world."""
    package_share = get_package_share_directory('demo_gazebo_sim')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')

    default_world = os.path.join(package_share, 'world', 'house.sdf')
    world = LaunchConfiguration('world')
    verbosity = LaunchConfiguration('verbosity')

    declare_world = DeclareLaunchArgument(
        'world',
        default_value=default_world,
        description='Absolute path to the SDF world file',
    )
    declare_verbosity = DeclareLaunchArgument(
        'verbosity',
        default_value='4',
        description='Gazebo Sim console verbosity (0-4)',
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': ['-r -v ', verbosity, ' ', world],
        }.items(),
    )

    return LaunchDescription([
        declare_world,
        declare_verbosity,
        gazebo,
    ])
