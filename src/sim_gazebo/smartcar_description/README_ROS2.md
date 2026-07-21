# smartcar_description ROS 2 migration

This package models a four-wheel-drive skid-steer smart mower. The two wheels
on each side are driven at the same speed. The Gazebo Harmonic `DiffDrive`
system uses the left/right speed difference to turn, including an in-place turn
when the two sides move in opposite directions. The model uses a 1.000 m wheelbase, a 0.370 m track width, 400 mm diameter
wheels, and a 600 mm cutter disc. The estimated overall dimensions are
1400 x 434 x 500 mm. The legacy ROS 1 files remain for reference but are not installed by the ROS 2 build.

## Build

```bash
colcon build --packages-select demo_gazebo_sim smartcar_description
source install/setup.bash
```

## Run

```bash
ros2 launch smartcar_description smartcar_sim.launch.py
```

Drive the vehicle with a Twist command. `linear.x` is forward speed and
`angular.z` is the requested yaw rate. Setting `linear.x` to zero and
`angular.z` to a nonzero value turns the mower in place:

```bash
ros2 topic pub /smartcar/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.3}, angular: {z: 0.5}}" -r 10
```

In-place left turn:

```bash
ros2 topic pub /smartcar/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0}, angular: {z: 0.8}}" -r 10
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
