#include "rclcpp/rclcpp.hpp"
#include "lifecycle_msgs/srv/change_state.hpp"
#include "lifecycle_msgs/msg/transition.hpp"
#include <chrono>

using namespace std::chrono_literals;

// 发送状态转移请求的辅助函数
bool change_state(
  rclcpp::Node::SharedPtr node,
  rclcpp::Client<lifecycle_msgs::srv::ChangeState>::SharedPtr client,
  uint8_t transition_id,
  const std::string & transition_label)
{
  auto request = std::make_shared<lifecycle_msgs::srv::ChangeState::Request>();
  request->transition.id = transition_id;

  if (!client->wait_for_service(3s)) {
    RCLCPP_ERROR(node->get_logger(), "服务未就绪");
    return false;
  }

  auto future = client->async_send_request(request);
  if (rclcpp::spin_until_future_complete(node, future) !=
      rclcpp::FutureReturnCode::SUCCESS)
  {
    RCLCPP_ERROR(node->get_logger(), "服务调用失败");
    return false;
  }

  if (future.get()->success) {
    RCLCPP_INFO(node->get_logger(), "✓ 状态转移成功: %s", transition_label.c_str());
  } else {
    RCLCPP_ERROR(node->get_logger(), "✗ 状态转移失败: %s", transition_label.c_str());
  }
  return future.get()->success;
}

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = rclcpp::Node::make_shared("lifecycle_controller");

  // 连接到 lifecycle_talker 的状态转移服务
  auto client = node->create_client<lifecycle_msgs::srv::ChangeState>(
    "/lifecycle_talker/change_state");

  RCLCPP_INFO(node->get_logger(), "开始控制生命周期节点...");
  rclcpp::sleep_for(1s);  // 等待节点启动

  // 1. configure：unconfigured → inactive
  change_state(node, client,
    lifecycle_msgs::msg::Transition::TRANSITION_CONFIGURE, "configure");
  rclcpp::sleep_for(2s);

  // 2. activate：inactive → active（开始发布）
  change_state(node, client,
    lifecycle_msgs::msg::Transition::TRANSITION_ACTIVATE, "activate");
  rclcpp::sleep_for(4s);  // 让节点发布 4 秒

  // 3. deactivate：active → inactive（暂停发布）
  change_state(node, client,
    lifecycle_msgs::msg::Transition::TRANSITION_DEACTIVATE, "deactivate");
  rclcpp::sleep_for(2s);

  // 4. activate again：重新激活
  change_state(node, client,
    lifecycle_msgs::msg::Transition::TRANSITION_ACTIVATE, "activate again");
  rclcpp::sleep_for(3s);

  // 5. deactivate → cleanup：清理资源
  change_state(node, client,
    lifecycle_msgs::msg::Transition::TRANSITION_DEACTIVATE, "deactivate");
  change_state(node, client,
    lifecycle_msgs::msg::Transition::TRANSITION_CLEANUP, "cleanup");

  // 6. shutdown：关闭节点
  change_state(node, client,
    lifecycle_msgs::msg::Transition::TRANSITION_UNCONFIGURED_SHUTDOWN, "shutdown");

  RCLCPP_INFO(node->get_logger(), "生命周期演示完成");
  rclcpp::shutdown();
  return 0;
}
