# smartcar_description ROS 2 migration

This package uses an Ackermann layout because the original vehicle has two
front steering joints and two driven rear wheels. The Gazebo Harmonic plugin
drives only the rear wheel joints and commands the two front steering joints;
the model is not configured as a differential or skid-steer base. The legacy
ROS 1 rosbuild, Gazebo Classic, arbotix, and controller files remain in their
original subdirectories for reference, but they are not installed by the ROS 2
build.

## Build

```bash
colcon build --packages-select demo_gazebo_sim smartcar_description
source install/setup.bash
```

## Run

```bash
ros2 launch smartcar_description smartcar_sim.launch.py
```

Drive the vehicle with a Twist command. Linear X is vehicle speed and angular
Z is the requested yaw rate:

```bash
ros2 topic pub /smartcar/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.3}, angular: {z: 0.5}}" -r 10
```

Main ROS topics:

- `/smartcar/cmd_vel`
- `/smartcar/odom`
- `/smartcar/scan`
- `/smartcar/scan/points`
- `/smartcar/imu`
- `/smartcar/camera/image`
- `/smartcar/camera/image/camera_info`
- `/joint_states`
- `/tf`

The GPU lidar has 720 horizontal samples and 24 vertical channels. Gazebo
publishes its planar scan on `/smartcar/scan` and the full cloud on
`/smartcar/scan/points`.
