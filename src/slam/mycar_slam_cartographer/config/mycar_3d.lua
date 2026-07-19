-- 智能车 Cartographer 3D 建图配置。
-- 输入数据：四线点云 /smartcar/scan/points、IMU /smartcar/imu、里程计 /smartcar/odom。
include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,

  -- Cartographer 发布 map -> odom，Gazebo 发布 odom -> base_footprint。
  map_frame = "map",
  -- IMU 坐标系作为三维姿态跟踪坐标系，用于估计重力方向。
  tracking_frame = "imu_link",
  published_frame = "odom",
  odom_frame = "odom",
  provide_odom_frame = false,
  -- 保留三维姿态，不将结果强制投影到二维平面。
  publish_frame_projected_to_2d = false,
  use_pose_extrapolator = true,

  -- 使用 Gazebo 轮式里程计，不使用卫星定位和人工路标。
  use_odometry = true,
  use_nav_sat = false,
  use_landmarks = false,

  -- 3D 模式使用一个 PointCloud2 输入，不再订阅 LaserScan。
  num_laser_scans = 0,
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 1,

  lookup_transform_timeout_sec = 0.5,
  submap_publish_period_sec = 0.3,
  pose_publish_period_sec = 5e-3,
  trajectory_publish_period_sec = 30e-3,

  -- 全量使用点云、里程计和 IMU 数据。
  rangefinder_sampling_ratio = 1.,
  odometry_sampling_ratio = 1.,
  fixed_frame_pose_sampling_ratio = 1.,
  imu_sampling_ratio = 1.,
  landmarks_sampling_ratio = 1.,
}

-- 启用三维轨迹构建器。
MAP_BUILDER.use_trajectory_builder_3d = true
MAP_BUILDER.num_background_threads = 4

-- 与仿真雷达 0.1 至 30 米量程保持一致。
TRAJECTORY_BUILDER_3D.min_range = 0.1
TRAJECTORY_BUILDER_3D.max_range = 30.
-- 四线雷达每帧已有约 2880 个点，因此每帧直接参与一次匹配。
TRAJECTORY_BUILDER_3D.num_accumulated_range_data = 1
-- 预滤波体素大小，降低重复点数量和计算量。
TRAJECTORY_BUILDER_3D.voxel_filter_size = 0.05

-- 高分辨率点云用于精确扫描匹配。
TRAJECTORY_BUILDER_3D.high_resolution_adaptive_voxel_filter.max_length = 0.15
TRAJECTORY_BUILDER_3D.high_resolution_adaptive_voxel_filter.min_num_points = 100
TRAJECTORY_BUILDER_3D.high_resolution_adaptive_voxel_filter.max_range = 15.
-- 低分辨率点云用于较大范围和回环匹配。
TRAJECTORY_BUILDER_3D.low_resolution_adaptive_voxel_filter.max_length = 0.30
TRAJECTORY_BUILDER_3D.low_resolution_adaptive_voxel_filter.min_num_points = 150
TRAJECTORY_BUILDER_3D.low_resolution_adaptive_voxel_filter.max_range = 30.

-- 低线数雷达启用在线相关扫描匹配，提高转弯时的鲁棒性。
TRAJECTORY_BUILDER_3D.use_online_correlative_scan_matching = true
TRAJECTORY_BUILDER_3D.real_time_correlative_scan_matcher.linear_search_window = 0.1
TRAJECTORY_BUILDER_3D.real_time_correlative_scan_matcher.angular_search_window = math.rad(10.)
TRAJECTORY_BUILDER_3D.real_time_correlative_scan_matcher.translation_delta_cost_weight = 1e-1
TRAJECTORY_BUILDER_3D.real_time_correlative_scan_matcher.rotation_delta_cost_weight = 1e-1

-- 地面车辆主要绕 Z 轴转向，扫描匹配仅优化偏航角可减少漂移和计算量。
TRAJECTORY_BUILDER_3D.ceres_scan_matcher.only_optimize_yaw = true
TRAJECTORY_BUILDER_3D.ceres_scan_matcher.translation_weight = 5.
TRAJECTORY_BUILDER_3D.ceres_scan_matcher.rotation_weight = 4e2

-- 运动量很小时不重复插入节点。
TRAJECTORY_BUILDER_3D.motion_filter.max_time_seconds = 0.5
TRAJECTORY_BUILDER_3D.motion_filter.max_distance_meters = 0.05
TRAJECTORY_BUILDER_3D.motion_filter.max_angle_radians = math.rad(0.5)
TRAJECTORY_BUILDER_3D.imu_gravity_time_constant = 10.

-- 子图分辨率与小型室内环境相匹配。
TRAJECTORY_BUILDER_3D.submaps.high_resolution = 0.10
TRAJECTORY_BUILDER_3D.submaps.high_resolution_max_range = 15.
TRAJECTORY_BUILDER_3D.submaps.low_resolution = 0.30
TRAJECTORY_BUILDER_3D.submaps.num_range_data = 40

-- 小型房屋内较频繁地执行全局优化和回环检测。
POSE_GRAPH.optimize_every_n_nodes = 40
POSE_GRAPH.constraint_builder.sampling_ratio = 0.30
POSE_GRAPH.constraint_builder.min_score = 0.50
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.55
POSE_GRAPH.optimization_problem.huber_scale = 5e2
POSE_GRAPH.optimization_problem.ceres_solver_options.max_num_iterations = 20

return options
