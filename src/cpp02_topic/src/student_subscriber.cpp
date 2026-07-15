#include "rclcpp/rclcpp.hpp"
#include "cpp02_topic/msg/student.hpp"

class StudentSubscriber : public rclcpp::Node
{
public:
  StudentSubscriber() : Node("student_subscriber")
  {
    subscription_ = this->create_subscription<cpp02_topic::msg::Student>(
      "student_topic", 10,
      std::bind(&StudentSubscriber::topic_callback, this, std::placeholders::_1));

    RCLCPP_INFO(this->get_logger(), "StudentSubscriber 节点已启动，等待消息...");
  }

private:
  void topic_callback(const cpp02_topic::msg::Student & msg)
  {
    RCLCPP_INFO(this->get_logger(), "---------- 收到学生信息 ----------");
    RCLCPP_INFO(this->get_logger(), "  姓名: %s", msg.name.c_str());
    RCLCPP_INFO(this->get_logger(), "  年龄: %d", msg.age);
    RCLCPP_INFO(this->get_logger(), "  班级: %s", msg.class_name.c_str());
    RCLCPP_INFO(this->get_logger(), "  性别: %s", msg.gender.c_str());
    RCLCPP_INFO(this->get_logger(), "  成绩: %.1f", msg.score);

    // 打印爱好列表
    std::string hobbies_str;
    for (size_t i = 0; i < msg.hobbies.size(); ++i) {
      hobbies_str += msg.hobbies[i];
      if (i + 1 < msg.hobbies.size()) {
        hobbies_str += "、";
      }
    }
    RCLCPP_INFO(this->get_logger(), "  爱好: %s", hobbies_str.c_str());
  }

  rclcpp::Subscription<cpp02_topic::msg::Student>::SharedPtr subscription_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<StudentSubscriber>());
  rclcpp::shutdown();
  return 0;
}
