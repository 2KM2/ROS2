---
name: teleop
description: 启动键盘遥控并说明操作方法
user_invocable: true
---

# 键盘遥控

启动 teleop_twist_keyboard 控制割草机。

## 启动

```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## 按键

```
   u    i    o        i:前进  u:左前  o:右前
   j    k    l        k:停止  j:左转  l:右转
   m    ,    .        ,:后退  m:左后  .:右后

q/z : 增加/减少 线速度 (10%)
w/x : 增加/减少 角速度 (10%)
空格/k : 急停
```

## 推荐速度

| 场景 | 线速度 | 角速度 |
|------|--------|--------|
| SLAM 建图 | 0.1-0.2 m/s | 0.3 rad/s |
| 普通行驶 | 0.3-0.5 m/s | 0.5 rad/s |
| 窄通道 | 0.05-0.1 m/s | 0.2 rad/s |

## 注意

- 割草机最大速度 1.0 m/s，建图时请保持低速
- 快速旋转会导致 LiDAR 扫描畸变，影响建图质量
- 如果 /cmd_vel 没有订阅者，检查仿真是否正常启动
