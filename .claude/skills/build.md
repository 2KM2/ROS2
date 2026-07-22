---
name: build
description: 编译 ROS 2 工作空间（全量或指定包）
user_invocable: true
---

# 编译工作空间

帮用户编译 ROS 2 工作空间，处理编译错误。

## 编译指定包

```bash
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select <包名>
source install/setup.bash
```

## 编译全部

```bash
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## 常用选项

| 选项 | 作用 |
|------|------|
| `--symlink-install` | 用软链接安装，改配置不用重编 |
| `--packages-select pkg1 pkg2` | 只编译指定包 |
| `--packages-up-to pkg` | 编译指定包及其依赖 |
| `--cmake-args -DCMAKE_BUILD_TYPE=Debug` | Debug 编译 |

## 清理重编

```bash
rm -rf build/ install/ log/
colcon build --symlink-install
```

## 常见编译错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `Could not find package` | 依赖未安装 | `rosdep install --from-paths src -y` |
| `No such file or directory (msg/srv)` | 接口包未先编译 | 用 `--packages-up-to` |
| `xacro error` | URDF 语法错误 | `xacro file.xacro` 单独检查 |
