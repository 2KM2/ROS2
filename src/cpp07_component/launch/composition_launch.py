from launch import LaunchDescription
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    """
    将 TalkerComponent 和 ListenerComponent 加载到同一个 container 进程中。
    两个组件共享进程，消息在进程内传递，无需序列化/网络开销。
    """
    container = ComposableNodeContainer(
        name='component_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[
            ComposableNode(
                package='cpp07_component',
                plugin='cpp07_component::TalkerComponent',
                name='talker',
            ),
            ComposableNode(
                package='cpp07_component',
                plugin='cpp07_component::ListenerComponent',
                name='listener',
            ),
        ],
        output='screen',
    )

    return LaunchDescription([container])
