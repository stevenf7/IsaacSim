# Overview

The cortex tools provide a decision framework for orchestrating the tools provided in Isaac Sim to
design behavior and execute it on physical robots. It consists of:
- A main cortex loop runner. This is the mind of the robot, with a belief model of the world and
  robot itself, and tools to analyzing the logical state of the world and choosing action. It uses
  motion generation tools built into Isaac Sim to control the belief robot.
- An extension `cortex_ros` that connects this belief to and from the physical world using ROS.
  Perception transforms stream in to the belief model, and actuation streams out to the physical
  robot.
- An extension `cortex_sim` that represents a simulated version of the real world for software and
  hardware in the loop development. It implements the ROS interfacing protocols expected from the
  physical robot's control system and the real-world perception module.
- Some example environments and behaviors, including a blocks world and scripts implementing a
  reactive block stacking behavior demonstrating the cortex decision framework.

# Quickstart -- block stacking demo

Running the block stacking demo. These commands are relative to
`omni_isaac_sim/source/extensions/omni.isaac.cortex/omni/isaac/cortex`.

Note: When starting multiple terminals as outlined below, it's convenient to use the `Terminator` app.

##  Starting the system with belief robot only

Running a belief robot only:
```
Terminal 1: Start a roscore

Terminal 2: Launch cortex loop runner passing in the blocks world USD env.
<release_path>/python.sh cortex_main.py --usd_env=omniverse://ov-isaac-dev.nvidia.com/Users/nratliff/cortex/blocks_world/cortex_blocks_world_belief.usd

Terminal 3: Activate behavior.
cd user
./activate build_block_tower.py
# It starts runner the block stacking behavior. At any point we can switch behaviors.
./activate go_home.py # Sends the robot to home and allows manual control using target prim.
./activate reset_world.py # Reset blocks to home.
```
In this example, you can interact with the blocks as its trying to build the
tower and the robot will react.

##  Starting the system with belief and sim robots

Running both the belief and sim robots. This setup is similar, except it uses a
different USD environment file, and you need to run the simulated controller
from `lula_ros` to connect the sim robot to the belief robot making decisions.
```
Terminal 1: Start a roscore

Terminal 2: Launch cortex loop runner passing in the blocks world USD env.
<release_path>/python.sh cortex_main.py --usd_env=omniverse://ov-isaac-dev.nvidia.com/Users/nratliff/cortex/blocks_world/cortex_blocks_world_belief_sim.usd

Terminal 3: Activate behavior.
cd user
./activate build_block_tower.py

# At this point the belief robot will start trying to grab the first block, but
# the sim robot isn't following because the controller isn't running. We need
# to start the controller.
Terminal 4: Start the simulated controller
rosrun lula_ros sim_controller
```

#  Connecting to a physical robot

The physical robot will take the place of the sim robot, and we'll run a
real-world controller rather than the simulated controller. Here, we'll show
how to send the robot home and use manual control since otherwise you'd need a
real-world perception module.

Start the system with belief only. This is the same procedure outlined above.
```
Terminal 1: Start a roscore

Terminal 2: Launch cortex loop runner passing in the blocks world USD env.
<release_path>/python.sh cortex_main.py --usd_env=omniverse://ov-isaac-dev.nvidia.com/Users/nratliff/cortex/blocks_world/cortex_blocks_world_belief.usd
```
At this point, we can run behaviors as before, but the system will only run the
simulated belief robot. The physical robot isn't yet connected.

Now start up the Franka robot, and start the `lula_ros_franka` controllers. At
the point were we launch the joint position controller in terminal 3 below, you
should see the simulated cortex belief robot synchronize with the physical
robot. It will engage the robot at that point, so you may see some slight
movement, but it shouldn't be much. Make sure you have the e-stop ready in case
anything goes wrong.
```
Terminal 1: Start the Franka controller manager
source ~/catkin_ws/devel/setup.bash
roslaunch lula_ros_franka franka_control_lula.launch

Terminal 2: Set high torque thresholds for Franka
rosrun lula_ros_franka set_high_collision_thresholds

Terminal 3: Startup the position controller -- launching this controller syncs the belief with the physical robot.
roslaunch lula_ros_franka joint_position_controller.launch

Terminal 4: Start the gripper commander listener
rosrun lula_ros_franka franka_gripper_command_relay.py
```

At this point, we can run some behaviors and we'll see the physical robot
following the simulated robot. Try the following:
```
cd user
./activate open_gripper.py  # Opens the physical gripper
./activate close_gripper.py  # Closes the physical gripper
./activate go_home.py  # Sends the robot to its home position
```
Once the robot gets to its home position, you'll be able to control the robot manually by moving the 
`motion_controller_target` prim in the stage located at
```
/cortex/world/motion_controller_target
```
Select the prim, then select the "Move" tool from the toolbar along the left edge of the viewport.
Then drag the arrows. 


# Breakdown of files

Main cortex loop runner: Standalone python app that runs the main cortex loop runner and starts the
`cortex_{ros,sim}` extensions.
- `cortex_main.py` : Primary entry point and main cortex loop runner. This runs the main standalone
cortex python app. It points to its own experience file which includes the omni.isaac.cortex
extension. A cortex compatible USD env is passed in via a flag. It automatically starts up the
`cortex_ros` and `cortex_sim` extensions. The former is always running, so a physical robot can be
connected at any time. If the USD env has a sim environment, that robot will be used in place of a
physical robot.

Extensions: Extensions loaded on startup handing ROS communication to physical robot and simulated
robot.
- `cortex_ros.py` : Handles ROS connections to get perceptual information into cortex and to send
  control information out of cortex.
- `cortex_sim.py` : Handles creating the ROS communication interface to mimic a physical robot using
  a simulated environment.

Decision framework: The core decision framework
- `df.py` : Core framework tools, including an implementation of decider networks and state
  machines.
- `dfb.py` : Decision framework behaviors useful across multiple behavior scripts. These include
  specific decider node types and actions.
- `df_behavior_watcher.py` : Monitors the `df_behavior_module.py` file watching for changes. Reloads
  when a change is detected.
- `df_behavior_module.py` : This file is constantly monitored by the main cortex loop runner. When
  it changes, the behavior is loaded and run. On startup, nothing is run until a behavior is
  explicitly activated.

`user` subdirectory: Contains user defined task scripts.
- `activate` : simple script for copying a behavior to the monitored `df_behavior_module.py` in the
  main cortex directory to activate it. `df_behavior_module.py` is monitored by the behavior watcher
  in `df_behavior_watcher.py`.
- `animation_trigger` : A script to trigger state transitions in the `replay_state_trajectory.py`
  standalone python app.
- `go_home.py` : Send the robot to the home position. Once the robot arrives at the home position,
  it can be controller using the `motion_controller_target` prim.
- `build_block_tower.py` : Build a block tower in the blocks world. This behavior is reactive to
  unexpected changes the blocks / tower.
- `block_tower_monitors.py` : Start up the block tower monitors only.
- `open_gripper.py` : Open the gripper.
- `close_gripper.py` : Close the gripper.
- `manual_control.py` : Set the robot to maual control. The robot can be controlled by moving the
  `motion_controller_target` prim.
- `reset_world.py` : resets the objects in both the belief and sim environments back to their
  initial configurations.

to remove: These will be moved / replaced
- `send_blocks_to_tower.py`
- `send_blocks_to_bad_tower.py`

cortex tools:
- `cortex_utils.py` : Utilities for setting up cortex.
- `cortex_object.py`: An object representation wrapping core API objects that simplifies accessing
  and using the cortex attributes. For instance, cortex objects have measured poses written into the
  USD. The cortex object has APIs for reading that measured pose and syncing the (belief) object's
  pose to that measured pose.
- `motion_commander.py` : A wrapper around Isaac Sim's intelligent motion policies providing a
  command API interface with a pose target and accompanying approach direction. Provides convenience
  methods for accessing forward kinematics to the control frame and opening and closing the gripper.
  Also, automatically smooths commands sent to the commander using `smoothed_command.py` and uses
  the `RmpFlowSmoothed` to make the resulting motions safe to run on the real robot.
- `state_trajectory_recorder.py` : Tool used by the main cortex loop to record state trajectories
  produced by cortex behaviors. These trajectories can then be replayed by
  `replay_state_trajectory.py`.
- `replay_state_trajectory.py` : Replays state trajectories produced by the
  `state_trajectory_recorder.py` to create animations.
- `smoothed_command.py` : A tool for smoothing commands automatically.
- `synchronized_time.py` : A ROS utility used to implement the clock synchronization protocol with
  the controller to adapt to slighly different clock speeds between the embedded robot controller
  and the machine running cortex. (E.g. the Franka controller's clock sometimes runs slightly fast
  causing the controller's interpolator to overrun the buffer over time. This synchronization
  protocol enables constant monitoring of the time delta to enable continual long-term runs on the
  physical robot.)

utils:
- `cli.py` : Simple tools for setting up convenient command line interfaces. Used especially in some
  of the tests.
- `gf_conversions.py` : Tools for more easily reading information to and from USD through the Gf
  interface.
- `math_util.py` : Math tools and utilities.
- `ros_tf_util.py` : ROS-based utilities.
- `tools.py` : Common utilities for running steady loops and profiling.

tests:
- `test_df.py` : Unit tests for the decision framework (df.py).
- `test_motion_commander.py` : A standalone python app that starts up the motion commander in a
  basic Franka environment to test and demo the motion commander interface.
- `test_load_robot_and_set_init_config.py` : A standalone python app for loading robots and testing
  setting the intiial config in a clean environment.

unused: 
- `cortex_core.py` : an experimental version of a cortex extension.




# Details

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

# Troubleshooting

When restarting the controller for the physical robot, it's best to bring down the entire controller
manager (i.e. everything on the real-time machine) and restart everything.


# Recording and replaying trajectories

Recording from `cortex_main.py`
1. Use the `--record` flag when starting `cortex_main.py` to enable recording. 
2. In your behavior, include `record_animation_state_trajectory = True` at the bottom. Once this
   behaivor is activated, the recording will start.
3. When you want to stop recording, activate a behavior that doesn't have that attribute set. E.g.
   `go_home.py` is a good choice.
4. The behavior will be written as a trajectory pickle file `traj.pkl` to the cortex directory where
   `cortex_main.py` is located.

Replay the trajectory file using `replay_state_trajectory.py`. Use the flag `--traj_filepath` to
point to the recorded trajectory file, and use the flag `--env_filepath` to point to the USD
environment.

The resulting animation file will be written to `--anim_filepath`, which defaults to
`saved_animation.usd`.

