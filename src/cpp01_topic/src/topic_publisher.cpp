#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

class TopicPublisher : public rclcpp::Node
{
public:
  TopicPublisher() : Node("topic_publisher"), count_(0)
  {
    // 创建发布者，话题名 "hello_topic"，队列长度 10
    publisher_ = this->create_publisher<std_msgs::msg::String>("hello_topic", 10);

    // 定时器，每 500ms 发布一次
    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(500),
      std::bind(&TopicPublisher::timer_callback, this));
  }

private:
  void timer_callback()
  {
    auto msg = std_msgs::msg::String();
    msg.data = "Hello World! count: " + std::to_string(count_++);
    RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", msg.data.c_str());
    publisher_->publish(msg);
  }

  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
  size_t count_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<TopicPublisher>());
  rclcpp::shutdown();
  return 0;
}
