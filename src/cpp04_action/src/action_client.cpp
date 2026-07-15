#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "cpp04_action/action/count_down.hpp"

using CountDown = cpp04_action::action::CountDown;
using GoalHandleCountDown = rclcpp_action::ClientGoalHandle<CountDown>;

class ActionClient : public rclcpp::Node
{
public:
  ActionClient() : Node("action_client")
  {
    client_ = rclcpp_action::create_client<CountDown>(this, "count_down");
  }

  void send_goal(int32_t countdown_from)
  {
    // 等待服务端上线
    if (!client_->wait_for_action_server(std::chrono::seconds(5))) {
      RCLCPP_ERROR(this->get_logger(), "Action 服务端未就绪");
      return;
    }

    // 构造目标
    auto goal_msg = CountDown::Goal();
    goal_msg.countdown_from = countdown_from;

    // 配置回调选项
    auto send_goal_options = rclcpp_action::Client<CountDown>::SendGoalOptions();

    // 回调1：目标被服务端接受 / 拒绝
    send_goal_options.goal_response_callback =
      [this](const GoalHandleCountDown::SharedPtr & goal_handle) {
        if (!goal_handle) {
          RCLCPP_ERROR(this->get_logger(), "目标被服务端拒绝");
        } else {
          RCLCPP_INFO(this->get_logger(), "目标已接受，任务开始执行...");
        }
      };

    // 回调2：收到实时反馈
    send_goal_options.feedback_callback =
      [this](GoalHandleCountDown::SharedPtr,
             const std::shared_ptr<const CountDown::Feedback> feedback) {
        RCLCPP_INFO(this->get_logger(),
          "  [反馈] 当前倒计时: %d", feedback->current_count);
      };

    // 回调3：任务结束（成功 / 取消 / 中止）
    send_goal_options.result_callback =
      [this](const GoalHandleCountDown::WrappedResult & result) {
        switch (result.code) {
          case rclcpp_action::ResultCode::SUCCEEDED:
            RCLCPP_INFO(this->get_logger(),
              "任务成功: %s", result.result->finish_message.c_str());
            break;
          case rclcpp_action::ResultCode::CANCELED:
            RCLCPP_WARN(this->get_logger(),
              "任务取消: %s", result.result->finish_message.c_str());
            break;
          default:
            RCLCPP_ERROR(this->get_logger(), "任务异常中止");
            break;
        }
      };

    RCLCPP_INFO(this->get_logger(),
      "发送目标: 从 %d 开始倒计时", countdown_from);
    client_->async_send_goal(goal_msg, send_goal_options);
  }

private:
  rclcpp_action::Client<CountDown>::SharedPtr client_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<ActionClient>();

  // 支持命令行传参：ros2 run cpp04_action action_client 10
  int32_t n = 5;
  if (argc == 2) {
    n = std::stoi(argv[1]);
  }

  node->send_goal(n);
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
