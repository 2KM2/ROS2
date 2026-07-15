#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "cpp04_action/action/count_down.hpp"
#include <thread>

using CountDown = cpp04_action::action::CountDown;
using GoalHandleCountDown = rclcpp_action::ServerGoalHandle<CountDown>;

class ActionServer : public rclcpp::Node
{
public:
  ActionServer() : Node("action_server")
  {
    action_server_ = rclcpp_action::create_server<CountDown>(
      this,
      "count_down",
      // 回调1：收到目标请求，决定接受还是拒绝
      std::bind(&ActionServer::handle_goal, this,
        std::placeholders::_1, std::placeholders::_2),
      // 回调2：收到取消请求
      std::bind(&ActionServer::handle_cancel, this, std::placeholders::_1),
      // 回调3：目标被接受，开始执行
      std::bind(&ActionServer::handle_accepted, this, std::placeholders::_1));

    RCLCPP_INFO(this->get_logger(), "Action 服务端已就绪，等待目标...");
  }

private:
  rclcpp_action::Server<CountDown>::SharedPtr action_server_;

  // 接受 / 拒绝目标
  rclcpp_action::GoalResponse handle_goal(
    const rclcpp_action::GoalUUID &,
    std::shared_ptr<const CountDown::Goal> goal)
  {
    RCLCPP_INFO(this->get_logger(),
      "收到目标请求: 从 %d 开始倒计时", goal->countdown_from);

    if (goal->countdown_from <= 0) {
      RCLCPP_WARN(this->get_logger(), "倒计时值必须 > 0，拒绝目标");
      return rclcpp_action::GoalResponse::REJECT;
    }
    return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
  }

  // 处理取消请求
  rclcpp_action::CancelResponse handle_cancel(
    const std::shared_ptr<GoalHandleCountDown> goal_handle)
  {
    RCLCPP_WARN(this->get_logger(),
      "收到取消请求 (当前值: %d)",
      goal_handle->get_goal()->countdown_from);
    return rclcpp_action::CancelResponse::ACCEPT;
  }

  // 目标被接受后，在新线程中执行，避免阻塞 spin
  void handle_accepted(const std::shared_ptr<GoalHandleCountDown> goal_handle)
  {
    std::thread(
      std::bind(&ActionServer::execute, this, std::placeholders::_1),
      goal_handle).detach();
  }

  // 核心执行逻辑：倒计时 + 发送 Feedback + 最终 Result
  void execute(const std::shared_ptr<GoalHandleCountDown> goal_handle)
  {
    int32_t start = goal_handle->get_goal()->countdown_from;
    auto feedback = std::make_shared<CountDown::Feedback>();
    auto result   = std::make_shared<CountDown::Result>();

    rclcpp::Rate rate(1.0);  // 1Hz，每秒倒一格

    for (int32_t i = start; i >= 0; --i) {
      // 检查是否收到取消请求
      if (goal_handle->is_canceling()) {
        result->finish_message = "任务已取消，停在 " + std::to_string(i);
        goal_handle->canceled(result);
        RCLCPP_WARN(this->get_logger(), "任务已取消");
        return;
      }

      // 发布实时反馈
      feedback->current_count = i;
      goal_handle->publish_feedback(feedback);
      RCLCPP_INFO(this->get_logger(), "倒计时: %d", i);

      if (i > 0) rate.sleep();
    }

    // 任务完成，发布最终结果
    result->finish_message = "倒计时完成！";
    goal_handle->succeed(result);
    RCLCPP_INFO(this->get_logger(), "任务完成");
  }
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ActionServer>());
  rclcpp::shutdown();
  return 0;
}
