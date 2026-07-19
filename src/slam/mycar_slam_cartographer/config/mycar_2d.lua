-- Cartographer 地图构建器和轨迹构建器的基础配置。
-- 这两个文件由 cartographer 软件包提供，本文件只覆盖智能车需要调整的参数。
include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,

  -- 全局地图坐标系。Cartographer 最终发布 map -> odom。
  map_frame = "map",
  -- Cartographer 用于计算机器人运动的跟踪坐标系。
  tracking_frame = "base_footprint",
  -- 发布优化位姿时使用 odom，使 Gazebo 继续发布 odom -> base_footprint。
  published_frame = "odom",
  odom_frame = "odom",
  -- 已有 Gazebo 里程计坐标系，因此不让 Cartographer 再创建 odom 坐标系。
  provide_odom_frame = false,
  -- 将发布的位姿投影到二维平面，忽略滚转、俯仰和高度变化。
  publish_frame_projected_to_2d = true,
  -- 在两次传感器更新之间外推机器人位姿，使 TF 更连续。
  use_pose_extrapolator = true,

  -- 使用 /smartcar/odom 提供的轮式里程计辅助扫描匹配。
  use_odometry = true,
  use_nav_sat = false,
  use_landmarks = false,

  -- 当前仿真只有一个 LaserScan 雷达，不使用 MultiEcho 和点云输入。
  num_laser_scans = 1,
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 0,

  -- 等待传感器坐标变换的最长时间。
  lookup_transform_timeout_sec = 0.5,
  -- 子图、机器人位姿和轨迹的发布周期。
  submap_publish_period_sec = 0.3,
  pose_publish_period_sec = 5e-3,
  trajectory_publish_period_sec = 30e-3,

  -- 采样比例为 1 表示不主动丢弃对应传感器数据。
  rangefinder_sampling_ratio = 1.,
  odometry_sampling_ratio = 1.,
  fixed_frame_pose_sampling_ratio = 1.,
  imu_sampling_ratio = 1.,
  landmarks_sampling_ratio = 1.,
}

-- 启用二维轨迹构建器，关闭三维建图。
MAP_BUILDER.use_trajectory_builder_2d = true

-- 当前二维仿真使用雷达和轮式里程计，不依赖 IMU。
TRAJECTORY_BUILDER_2D.use_imu_data = false
-- 与 smartcar.urdf.xacro 中仿真雷达的有效量程保持一致。
TRAJECTORY_BUILDER_2D.min_range = 0.1
TRAJECTORY_BUILDER_2D.max_range = 30.
-- 未命中障碍物的射线按 30 米长度插入空闲空间。
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 30.
-- 每收到一帧雷达数据就进行一次扫描匹配和插入。
TRAJECTORY_BUILDER_2D.num_accumulated_range_data = 1
-- 每个子图累计 35 组距离数据；越小更新越快，越大子图越稳定。
TRAJECTORY_BUILDER_2D.submaps.num_range_data = 35

-- 启用实时相关扫描匹配，提高初始位姿误差和急转弯时的鲁棒性。
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true
-- 扫描匹配在当前位置前后 0.1 米范围内搜索。
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.linear_search_window = 0.1
-- 扫描匹配在当前朝向前后 20 度范围内搜索。
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.angular_search_window = math.rad(20.)
-- 平移变化惩罚较大，避免匹配结果产生不合理的位置跳变。
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.translation_delta_cost_weight = 10.
-- 旋转变化惩罚权重，允许车辆转向时匹配角度变化。
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.rotation_delta_cost_weight = 1e-1

-- 每累计 35 个轨迹节点执行一次全局位姿图优化。
POSE_GRAPH.optimize_every_n_nodes = 35
-- 局部回环约束的最低匹配得分，过低容易产生错误闭环。
POSE_GRAPH.constraint_builder.min_score = 0.55
-- 全局重定位约束需要更高得分，降低错误匹配概率。
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.60
-- Huber 鲁棒损失尺度，用于降低异常约束对整体地图的影响。
POSE_GRAPH.optimization_problem.huber_scale = 1e2

return options
