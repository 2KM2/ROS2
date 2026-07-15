#include "rclcpp/rclcpp.hpp"
#include "cpp03_service/srv/add_ints.hpp"
#include <chrono>

using namespace std::chrono_literals;

class ServiceClient : public rclcpp::Node
{
public:
  ServiceClient() : Node("service_client")
  {
    // 创建客户端，服务名必须与服务端一致
    client_ = this->create_client<cpp03_service::srv::AddInts>("add_ints");
  }

  // 同步调用：等待服务端返回结果后再继续
  void send_request(int64_t a, int64_t b)
  {
    // 1. 等待服务端上线（最多等 3 秒）
    while (!client_->wait_for_service(3s)) {
      if (!rclcpp::ok()) {
        RCLCPP_ERROR(this->get_logger(), "等待服务时被中断");
        return;
      }
      RCLCPP_WARN(this->get_logger(), "服务未就绪，继续等待...");
    }

    // 2. 构造请求
    auto request = std::make_shared<cpp03_service::srv::AddInts::Request>();
    request->a = a;
    request->b = b;

    RCLCPP_INFO(this->get_logger(), "发送请求: %ld + %ld = ?", a, b);

    // 3. 异步发送请求，并用 spin_until_future_complete 等待结果
    auto future = client_->async_send_request(request);

    if (rclcpp::spin_until_future_complete(
          this->get_node_base_interface(), future) ==
        rclcpp::FutureReturnCode::SUCCESS)
    {
      auto response = future.get();
      RCLCPP_INFO(this->get_logger(),
        "收到响应: %s", response->message.c_str());
    } else {
      RCLCPP_ERROR(this->get_logger(), "服务调用失败");
    }
  }

private:
  rclcpp::Client<cpp03_service::srv::AddInts>::SharedPtr client_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto client_node = std::make_shared<ServiceClient>();

  // 从命令行读取参数，默认 a=10, b=20
  int64_t a = 10, b = 20;
  if (argc == 3) {
    a = std::stoll(argv[1]);
    b = std::stoll(argv[2]);
  }

  client_node->send_request(a, b);

  rclcpp::shutdown();
  return 0;
}
