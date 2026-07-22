---
name: coverage
description: 运行弓字形覆盖路径规划（割草模式）
user_invocable: true
---

# 覆盖路径规划

帮用户运行割草覆盖路径，调整参数。

## 前提

需要 Nav2 导航栈已启动（先运行 /navigate）。

## 运行

```bash
cd ~/workspace/ROS2
source /opt/ros/jazzy/setup.bash
source install/setup.bash

python3 src/sim_gazebo/tb3_mower_sim/scripts/boustrophedon_coverage.py \
  --ros-args \
  -p area_x_min:=-10.0 \
  -p area_x_max:=10.0 \
  -p area_y_min:=-5.0 \
  -p area_y_max:=5.0 \
  -p cut_width:=0.20 \
  -p overlap:=0.05
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `area_x_min/max` | -15/15 | 割草区域 X 范围 (m) |
| `area_y_min/max` | -8/8 | 割草区域 Y 范围 (m) |
| `cut_width` | 0.20 | 割刀宽度 (m) |
| `overlap` | 0.05 | 相邻条带重叠量 (m) |
| `batch_size` | 20 | 每批发送的路径点数 |

## 覆盖率估算

```
步进 = cut_width - overlap
条带数 = (y_max - y_min) / 步进
总路程 = 条带数 × (x_max - x_min)
```

## 建议

- 先用小区域测试（如 5m×5m）
- 确保区域内无大障碍物阻断条带
- 如遇导航失败，检查 costmap 中障碍物是否把路径完全堵死
