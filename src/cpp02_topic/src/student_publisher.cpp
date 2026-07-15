#include "rclcpp/rclcpp.hpp"
#include "cpp02_topic/msg/student.hpp"

class StudentPublisher : public rclcpp::Node
{
public:
  StudentPublisher() : Node("student_publisher"), count_(0)
  {
    publisher_ = this->create_publisher<cpp02_topic::msg::Student>("student_topic", 10);

    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(1000),
      std::bind(&StudentPublisher::timer_callback, this));

    RCLCPP_INFO(this->get_logger(), "StudentPublisher 节点已启动");
  }

private:
  void timer_callback()
  {
    auto msg = cpp02_topic::msg::Student();

    // 模拟几个学生轮流发布
    switch (count_ % 3) {
      case 0:
        msg.name       = "张三";
        msg.age        = 18;
        msg.class_name = "计算机2301";
        msg.gender     = "male";
        msg.score      = 92.5f;
        msg.hobbies    = {"编程", "篮球", "音乐"};
        break;
      case 1:
        msg.name       = "李四";
        msg.age        = 19;
        msg.class_name = "软件工程2302";
        msg.gender     = "male";
        msg.score      = 85.0f;
        msg.hobbies    = {"游戏", "动漫"};
        break;
      case 2:
        msg.name       = "王五";
        msg.age        = 17;
        msg.class_name = "人工智能2303";
        msg.gender     = "female";
        msg.score      = 97.0f;
        msg.hobbies    = {"机器学习", "跑步", "绘画"};
        break;
    }

    RCLCPP_INFO(this->get_logger(),
      "Publishing student => 姓名:%s  年龄:%d  班级:%s  性别:%s  成绩:%.1f",
      msg.name.c_str(), msg.age, msg.class_name.c_str(),
      msg.gender.c_str(), msg.score);

    publisher_->publish(msg);
    count_++;
  }

  rclcpp::Publisher<cpp02_topic::msg::Student>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
  size_t count_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<StudentPublisher>());
  rclcpp::shutdown();
  return 0;
}
