#include "rclcpp/rclcpp.hpp"
#include "cpp03_service/srv/add_ints.hpp"

// 回调函数：处理请求并填写响应
void handle_add_ints(
  const std::shared_ptr<cpp03_service::srv::AddInts::Request> request,
  std::shared_ptr<cpp03_service::srv::AddInts::Response> response)
{
  response->sum     = request->a + request->b;
  response->message = std::to_string(request->a) + " + " +
                      std::to_string(request->b) + " = " +
                      std::to_string(response->sum);

  RCLCPP_INFO(rclcpp::get_logger("service_server"),
    "收到请求: a=%ld, b=%ld  →  响应: sum=%ld",
    request->a, request->b, response->sum);
}

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<rclcpp::Node>("service_server");

  // 创建服务：服务名 "add_ints"，绑定处理函数
  auto server = node->create_service<cpp03_service::srv::AddInts>(
    "add_ints", &handle_add_ints);

  RCLCPP_INFO(node->get_logger(), "服务端已就绪，等待请求...");

  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
