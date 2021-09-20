# Quickstart:

## building

Follow the instructions in `lula_ros/README.md` setting up `lula_ros`.  That
will show how to build and install the `lula` dependency, and how to create the
catkin workspace with `lula_ros`.  

Additionally, add the `lula_ros_franka` package and the `franka_ros` package
(third party package from franka) to the catkin workspace.

Note, this should be on the real-time Franka
control machine when controlling the real robot. Communication is assumed to be
setup between that machine and the machine running Isaac Sim via ROS.

Build the catkin workspace.
```
cd ~/catkin_ws
catkin_make
```

## Running

Terminal 1: Start `roscore`:
```
source ~/catkin_ws/devel/setup.bash
roscore
```

Terminal 2: Start Isaac Sim. This runs the RMPs, Isaac Sim world model, and
simulated robot(s). From the base folder for the `omni_isaac_sim` package, execute:
```
./python.sh python_samples/ros/lula_ros/lula_ros_main.py
```

By default this script uses the simulated robot to publish joint state
information. If connecting to a real robot use the `--is_real_robot` flag as in
```
./python.sh python_samples/ros/lula_ros/lula_ros_main.py --is_real_robot
```

You should see a control robot (left) and a simulated "real" robot (right).
Click on the control ball at the left (control) robot's end-effector and drag it
around with the gizmo. You should see the control robot move, but the simulated
real robot will remain stationary.


Simulated "real" robot:

Terminal 3: Start the mock controller for testing. From the `lula_ros`
package run the command stream interpolator:
```
source ~/catkin_ws/devel/setup.bash
rosrun lula_ros lula_command_stream_interpolator
```
You should see the real robot and the sim robot synchronize with each other.
Click on the control ball at the left (control) robot's end-effector and drag it
around with the gizmo. Both robots should move this time.


Physical robot:

Make sure you start Isaac Sim with the `--is_real_robot` flag.

Now you can try running the real controller. From the real-time control machine
(where the catkin workspace described above should be installed), run the franka
controllers:
```
Terminal 4: roslaunch lula_ros_franka franka_control_lula.launch
Terminal 5: roslaunch lula_ros_franka joint_position_controller.launch
```
That final command will run the full controller analogous to the
`lula_command_stream_interpolator` from above. You should see the same behavior
as the simulated version, but with the actual controller running, the physical
robot will follow as well.

# Troubleshooting

When restarting the controller, it's best to bring down the entire controller
manager (i.e. both the controller `joint_position_controller.launch` and the
controller manager `lula_control_lula.launch`).
