# Cortex standalone examples and demos

Notes to add:
- difference between demos, examples, simple examples
- the model of setup and execution:
    - command API and how it's accessed from behaviors
    - computational pipeline: logical state, behavior, commanders
    - separation between stepping mechanisms in world and the behavior tools
    - separation between world setup and behavior
- full demo: ur10 bin stacking. See task, monitors, behavior, commanders all at work
- ROS
- what each example does and what it shows

# Quick runthrough for QA

Convenient alias:
```
alias isaac_python="<path_to_isaac_sim>/_build/linux-x86_64/release/python.sh"
```

This allows you to run Isaac Sim standalone python scripts as
```
isaac_python demo_leonardo_main.py
```

There are three demo worlds:
1. Leonardo: A Franka on a custom station with attached camera. Contains blocks for manipulation.
2. Simple Franka: The standard Franka added through the Isaac Sim core API. Contains blocks for manipulation.
3. UR10 conveyer: A UR10 robot in a factory setting with a conveyer platform.

Behaviors are stored in:
```
behaviors/ur10/bin_stacking_behavior.py
behaviors/franka/block_stacking_behavior.py
behaviors/franka/peck_game.py
behaviors/franka/peck_state_machine.py
behaviors/franka/peck_decider_network.py
behaviors/franka/simple/simple_state_machine.py
behaviors/franka/simple/simple_decider_network.py
```
Any behavior for a given robot can be run in any of the worlds with that robot.


## Procedure

For each of these demos and examples:
1. Launch the demo by invoking the python script using `isaac_python`.
2. Press play. This will start the demo.
3. Interact with the demo as instructed.
4. Press pause and play again. You should see the world freeze during the pause and resume
   seamlessly when played.
5. (restart) Press stop and then play again. When stopped you should see the world reset to the default USD
   configuration, then then when played again it'll reset to the initial world config and start the
   behavior again from the beginning.
6. Let the demo run as usual for a while. E.g. there's currently a known bug in the UR10 bin
   stacking where when it uses the suction gripper again for the first time after a restart it'll
   crash Isaac Sim. We want to catch things like thing.

### Leonardo demo

Run Leonardo demo:
```
isaac_python demo_leonardo_main.py [--behavior=<path_to_franka_behavior>]
```
The `--behavior` flag is optional. It defaults to `behaviors/franka/block_stacking_behavior.py` to
run the block stacking behavior.

Try the other behaviors using the `--behavior` flag they should all run and reset properly.
```
behaviors/franka/block_stacking_behavior.py
behaviors/franka/peck_game.py
behaviors/franka/peck_state_machine.py
behaviors/franka/peck_decider_network.py
behaviors/franka/simple/simple_state_machine.py
behaviors/franka/simple/simple_decider_network.py
```

### UR10 bin stacking demo

Run the UR10 bin stacking demo.
```
isaac_python demo_ur10_conveyer_main.py
```
There's only one behavior for this demo and it's run by default. You should see the bins come down
the conveyer to the robot. Once the bin gets close the robot will pick it up and stack it on the
pallet. It needs to stack them upside down, so if the bin is rightside up, it'll use the flip
station to flip it before stacking.


### Franka examples

Run the command API demo:
```
isaac_python example_command_api_main.py
```
The robot will reach forward to a target position, then just move its arm while maintaining that
position target (move in the nullspace).

Run the decider network example:
```
isaac_python example_decider_network_main.py
```
The robot should peck around on the floor.

Run the simple Franka examples:
```
isaac_python simple_franka_examples_main.py [--behavior=<path_to_franka_behavior>]
```
This should work with all behaviors (same as Leonardo demo), defaulting to
`simple_decider_network.py`:
```
behaviors/franka/block_stacking_behavior.py
behaviors/franka/peck_game.py
behaviors/franka/peck_state_machine.py
behaviors/franka/peck_decider_network.py
behaviors/franka/simple/simple_state_machine.py
behaviors/franka/simple/simple_decider_network.py
```

### ROS1.0 examples

Setup a catkin workspace and buidl the ROS `cortex_control` library.
```
source /opt/ros/noetic/setup.bash  # Assumes ROS noetic is installed.

mkdir -p ~/catkin_ws/src
cd ~/catkin_ws/src
catkin_init_workspace

ln -s <path_to_isaac_sim>/source/ros_workspace/src/cortex_control .
cd ..
catkin_make
```

In the following, if a terminal is a "ROS Terminal", source the `setup.bash` from your catkin
workspace first.
```
source ~/catkin_ws/devel/setup.bash
```

ROS Terminal 1: Launch the ROS core
```
source ~/catkin_ws/devel/setup.bash
roscore
```

Terminal 2: Run the Isaac Sim standalone python app.
```
isaac_python example_cortex_sync_main.py [--behavior=<path_to_franka_behavior>]
```
This should work with all behaviors (same as Leonardo demo), defaulting to
`simple_decider_network.py`:
```
behaviors/franka/block_stacking_behavior.py
behaviors/franka/peck_game.py
behaviors/franka/peck_state_machine.py
behaviors/franka/peck_decider_network.py
behaviors/franka/simple/simple_state_machine.py
behaviors/franka/simple/simple_decider_network.py
```
With all behaviors except the block stacking behavior, include the flag `--auto_sync_objects`.

There will be two robots in the scene. The closer robot controls the robot in back. When you press
play, currently only the front robot will move because the controller isn't started.

ROS Terminal 3: Launch the simulated controller.
```
source ~/catkin_ws/devel/setup.bash
rosrun cortex_control sim_controller
```
The front robot should synchronize with the back robot's position and the back robot will start
following the front robot.


