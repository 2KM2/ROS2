#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

class TopicSubscriber : public rclcpp::Node
{
public:
  TopicSubscriber() : Node("topic_subscriber")
  {
    // 订阅 "hello_topic" 话题，队列长度 10
    subscription_ = this->create_subscription<std_msgs::msg::String>(
      "hello_topic", 10,
      std::bind(&TopicSubscriber::topic_callback, this, std::placeholders::_1));
  }

private:
  void topic_callback(const std_msgs::msg::String & msg)
  {
    RCLCPP_INFO(this->get_logger(), "Received: '%s'", msg.data.c_str());
  }

  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<TopicSubscriber>());
  rclcpp::shutdown();
  return 0;
}
