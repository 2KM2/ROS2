#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/lifecycle_node.hpp"
#include "std_msgs/msg/string.hpp"

using CallbackReturn = rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

class LifecycleTalker : public rclcpp_lifecycle::LifecycleNode
{
public:
  explicit LifecycleTalker(const rclcpp::NodeOptions & options = rclcpp::NodeOptions())
  : LifecycleNode("lifecycle_talker", options), count_(0)
  {
    RCLCPP_INFO(get_logger(), "节点构造完成 → [unconfigured]");
  }

  // ── 状态回调 ────────────────────────────────────────────────
  // unconfigured → inactive
  CallbackReturn on_configure(const rclcpp_lifecycle::State &) override
  {
    publisher_ = this->create_publisher<std_msgs::msg::String>("lifecycle_topic", 10);
    timer_     = this->create_wall_timer(
      std::chrono::milliseconds(500),
      std::bind(&LifecycleTalker::publish_message, this));

    // 配置阶段创建资源，但 timer/publisher 还未激活
    timer_->cancel();
    RCLCPP_INFO(get_logger(), "on_configure() → [inactive]  资源已分配");
    return CallbackReturn::SUCCESS;
  }

  // inactive → active
  CallbackReturn on_activate(const rclcpp_lifecycle::State &) override
  {
    publisher_->on_activate();
    timer_->reset();   // 启动定时器，开始发布
    RCLCPP_INFO(get_logger(), "on_activate() → [active]  开始发布消息");
    return CallbackReturn::SUCCESS;
  }

  // active → inactive
  CallbackReturn on_deactivate(const rclcpp_lifecycle::State &) override
  {
    timer_->cancel();
    publisher_->on_deactivate();
    RCLCPP_INFO(get_logger(), "on_deactivate() → [inactive]  暂停发布");
    return CallbackReturn::SUCCESS;
  }

  // inactive → unconfigured
  CallbackReturn on_cleanup(const rclcpp_lifecycle::State &) override
  {
    timer_.reset();
    publisher_.reset();
    count_ = 0;
    RCLCPP_INFO(get_logger(), "on_cleanup() → [unconfigured]  资源已释放");
    return CallbackReturn::SUCCESS;
  }

  // any → finalized
  CallbackReturn on_shutdown(const rclcpp_lifecycle::State &) override
  {
    timer_.reset();
    publisher_.reset();
    RCLCPP_INFO(get_logger(), "on_shutdown() → [finalized]  节点关闭");
    return CallbackReturn::SUCCESS;
  }

private:
  void publish_message()
  {
    if (!publisher_->is_activated()) return;

    auto msg = std_msgs::msg::String();
    msg.data = "[lifecycle] Hello World! count: " + std::to_string(count_++);
    RCLCPP_INFO(get_logger(), "Publishing: '%s'", msg.data.c_str());
    publisher_->publish(msg);
  }

  rclcpp_lifecycle::LifecyclePublisher<std_msgs::msg::String>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
  size_t count_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  // LifecycleNode 需要通过 executor 来 spin，
  // 不能直接传给 rclcpp::spin()
  rclcpp::executors::SingleThreadedExecutor exe;
  auto node = std::make_shared<LifecycleTalker>();
  exe.add_node(node->get_node_base_interface());
  exe.spin();

  rclcpp::shutdown();
  return 0;
}
