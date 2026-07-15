#include "rclcpp/rclcpp.hpp"
#include "rclcpp_components/register_node_macro.hpp"
#include "std_msgs/msg/string.hpp"

namespace cpp07_component
{

class ListenerComponent : public rclcpp::Node
{
public:
  explicit ListenerComponent(const rclcpp::NodeOptions & options)
  : Node("listener", options)
  {
    subscription_ = this->create_subscription<std_msgs::msg::String>(
      "chatter", 10,
      std::bind(&ListenerComponent::topic_callback, this, std::placeholders::_1));

    RCLCPP_INFO(get_logger(), "ListenerComponent 已加载，订阅 /chatter");
  }

private:
  void topic_callback(const std_msgs::msg::String & msg)
  {
    RCLCPP_INFO(get_logger(), "Received: '%s'", msg.data.c_str());
  }

  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
};

}  // namespace cpp07_component

RCLCPP_COMPONENTS_REGISTER_NODE(cpp07_component::ListenerComponent)
