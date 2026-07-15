#include "rclcpp/rclcpp.hpp"

class ParamNode : public rclcpp::Node
{
public:
  ParamNode() : Node("param_node")
  {
    // 声明参数（参数名，默认值）
    this->declare_parameter("robot_name",   "RoboA");
    this->declare_parameter("max_speed",    1.5);
    this->declare_parameter("loop_rate",    10);
    this->declare_parameter("auto_mode",    false);
    this->declare_parameter("target_rooms", std::vector<std::string>{"room1", "room2"});

    // 读取参数并打印
    print_params();

    // 注册参数变更回调（动态响应参数修改）
    param_cb_handle_ = this->add_on_set_parameters_callback(
      std::bind(&ParamNode::on_params_changed, this, std::placeholders::_1));

    // 定时器：每 3 秒打印一次当前参数值
    timer_ = this->create_wall_timer(
      std::chrono::seconds(3),
      std::bind(&ParamNode::print_params, this));
  }

private:
  // 打印所有参数当前值
  void print_params()
  {
    RCLCPP_INFO(this->get_logger(), "========== 当前参数 ==========");
    RCLCPP_INFO(this->get_logger(), "  robot_name : %s",
      this->get_parameter("robot_name").as_string().c_str());
    RCLCPP_INFO(this->get_logger(), "  max_speed  : %.2f",
      this->get_parameter("max_speed").as_double());
    RCLCPP_INFO(this->get_logger(), "  loop_rate  : %ld",
      this->get_parameter("loop_rate").as_int());
    RCLCPP_INFO(this->get_logger(), "  auto_mode  : %s",
      this->get_parameter("auto_mode").as_bool() ? "true" : "false");

    auto rooms = this->get_parameter("target_rooms").as_string_array();
    std::string rooms_str;
    for (size_t i = 0; i < rooms.size(); ++i) {
      rooms_str += rooms[i];
      if (i + 1 < rooms.size()) rooms_str += ", ";
    }
    RCLCPP_INFO(this->get_logger(), "  target_rooms: [%s]", rooms_str.c_str());
  }

  // 参数变更回调：验证并接受 / 拒绝修改
  rcl_interfaces::msg::SetParametersResult on_params_changed(
    const std::vector<rclcpp::Parameter> & params)
  {
    rcl_interfaces::msg::SetParametersResult result;
    result.successful = true;

    for (const auto & param : params) {
      RCLCPP_INFO(this->get_logger(),
        "参数被修改: %s = %s",
        param.get_name().c_str(),
        param.value_to_string().c_str());

      // 示例：限制 max_speed 不能超过 5.0
      if (param.get_name() == "max_speed" &&
          param.as_double() > 5.0)
      {
        result.successful = false;
        result.reason     = "max_speed 不能超过 5.0";
        RCLCPP_WARN(this->get_logger(), "参数验证失败: %s", result.reason.c_str());
      }
    }
    return result;
  }

  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr param_cb_handle_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ParamNode>());
  rclcpp::shutdown();
  return 0;
}
