#include "rclcpp/rclcpp.hpp"
#include "rclcpp_components/register_node_macro.hpp"
#include "std_msgs/msg/string.hpp"

namespace cpp07_component
{

class TalkerComponent : public rclcpp::Node
{
public:
  explicit TalkerComponent(const rclcpp::NodeOptions & options)
  : Node("talker", options), count_(0)
  {
    publisher_ = this->create_publisher<std_msgs::msg::String>("chatter", 10);

    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(500),
      std::bind(&TalkerComponent::timer_callback, this));

    RCLCPP_INFO(get_logger(), "TalkerComponent 已加载，开始发布 /chatter");
  }

private:
  void timer_callback()
  {
    auto msg = std_msgs::msg::String();
    msg.data = "[component] Hello! count: " + std::to_string(count_++);
    RCLCPP_INFO(get_logger(), "Publishing: '%s'", msg.data.c_str());
    publisher_->publish(msg);
  }

  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
  size_t count_;
};

}  // namespace cpp07_component

// 将类注册为可被 component_container 动态加载的组件
RCLCPP_COMPONENTS_REGISTER_NODE(cpp07_component::TalkerComponent)
