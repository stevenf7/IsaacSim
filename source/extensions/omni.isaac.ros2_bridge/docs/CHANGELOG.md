**********
CHANGELOG
**********

[0.1.1] - 2021-12-08
========================

Fixed
--------
- odometry frame matches robot's starting frame, not the world frame. 
- horizontal and vertical aperture use camera prim values instead of computing vertical aperture
- lidar components publish point cloud data as PCL2 messages instead of PCL
- lidar PCL2 messages only contain points that hit

Added
-------
- usePhysicsStepSimTime setting and use_physics_step_sim_time to use physics step events to update simulation time


[0.1.0] - 2021-04-23
========================

Added
-------
- Initial version of ROS2 Bridge
