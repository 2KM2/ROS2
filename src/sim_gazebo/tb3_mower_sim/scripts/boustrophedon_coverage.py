#!/usr/bin/env python3
"""
弓字形 (Boustrophedon) 覆盖路径规划器。

给定一个矩形割草区域和割刀宽度，生成往返条带路径并通过 Nav2 执行。

用法：
  python3 boustrophedon_coverage.py --ros-args \
    -p area_x_min:=-10.0 -p area_x_max:=10.0 \
    -p area_y_min:=-5.0 -p area_y_max:=5.0 \
    -p cut_width:=0.20 -p overlap:=0.05
"""

import math

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateThroughPoses
from geometry_msgs.msg import PoseStamped


class BoustrophedonCoverage(Node):
    def __init__(self):
        super().__init__('boustrophedon_coverage')

        self.declare_parameter('cut_width', 0.20)
        self.declare_parameter('overlap', 0.05)
        self.declare_parameter('area_x_min', -15.0)
        self.declare_parameter('area_x_max', 15.0)
        self.declare_parameter('area_y_min', -8.0)
        self.declare_parameter('area_y_max', 8.0)
        self.declare_parameter('batch_size', 20)

        self.cut_width = self.get_parameter('cut_width').value
        self.overlap = self.get_parameter('overlap').value
        self.x_min = self.get_parameter('area_x_min').value
        self.x_max = self.get_parameter('area_x_max').value
        self.y_min = self.get_parameter('area_y_min').value
        self.y_max = self.get_parameter('area_y_max').value
        self.batch_size = self.get_parameter('batch_size').value

        self.nav_client = ActionClient(
            self, NavigateThroughPoses, 'navigate_through_poses')

        self.get_logger().info('等待 Nav2 导航服务...')
        self.nav_client.wait_for_server()
        self.get_logger().info('Nav2 已就绪')

        self.execute_coverage()

    def generate_waypoints(self):
        """生成弓字形路径点: [(x, y, yaw), ...]"""
        waypoints = []
        step = self.cut_width - self.overlap
        y = self.y_min
        direction = 1

        while y <= self.y_max:
            if direction == 1:
                x_start, x_end = self.x_min, self.x_max
                yaw = 0.0
            else:
                x_start, x_end = self.x_max, self.x_min
                yaw = math.pi

            waypoints.append((x_start, y, yaw))
            waypoints.append((x_end, y, yaw))

            y += step
            direction *= -1

        self.get_logger().info(
            f'区域: [{self.x_min}, {self.x_max}] x [{self.y_min}, {self.y_max}]')
        self.get_logger().info(
            f'割刀宽: {self.cut_width}m, 重叠: {self.overlap}m, '
            f'步进: {step}m')
        self.get_logger().info(
            f'生成 {len(waypoints)//2} 条割草带, {len(waypoints)} 个路径点')

        total_dist = len(waypoints) // 2 * abs(self.x_max - self.x_min)
        self.get_logger().info(f'预计总路程: {total_dist:.0f}m')

        return waypoints

    def make_pose(self, x, y, yaw):
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.position.z = 0.0
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        return pose

    def execute_coverage(self):
        waypoints = self.generate_waypoints()
        total_batches = math.ceil(len(waypoints) / self.batch_size)

        for i in range(0, len(waypoints), self.batch_size):
            batch = waypoints[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1

            goal = NavigateThroughPoses.Goal()
            goal.poses = [self.make_pose(x, y, yaw) for x, y, yaw in batch]

            self.get_logger().info(
                f'[{batch_num}/{total_batches}] 发送 {len(batch)} 个路径点')

            future = self.nav_client.send_goal_async(goal)
            rclpy.spin_until_future_complete(self, future)

            goal_handle = future.result()
            if not goal_handle.accepted:
                self.get_logger().error('导航目标被拒绝，终止覆盖')
                return

            result_future = goal_handle.get_result_async()
            rclpy.spin_until_future_complete(self, result_future)

            result = result_future.result()
            if result.status == 4:  # SUCCEEDED
                self.get_logger().info(f'[{batch_num}/{total_batches}] 完成')
            else:
                self.get_logger().warn(
                    f'[{batch_num}/{total_batches}] '
                    f'结果状态: {result.status}，继续下一批')

        self.get_logger().info('=== 覆盖路径执行完毕 ===')


def main(args=None):
    rclpy.init(args=args)
    node = BoustrophedonCoverage()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
