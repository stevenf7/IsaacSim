# Cortex concepts

Cortex uses Isaac Sim to create a belief representation of the robot and the world that can make
decisions. You can think of this belief as what lives inside the mind of the robot. The basic belief
is entirely independent of ROS, but we can use ROS to create connections between the physical world
and this internal belief world to synchronize the belief with reality in real time. This involves
perception transforms streaming in so we know where objects really are in the physical world, and
control signals streaming out so the physical robot will mimic the movement of the belief robot in
real time.

For testing these ROS connections we can use a sim world to create a replica of the real robot and
environment that implements the required ROS communication protocols. With both the belief and sim
robots running, the belief robot can make decisions based on what it believes about the world while
the simulated and belief worlds remain in sync.

Then, we can simply swap the sim world for the physical world to execute on a physical robot that
implements the same ROS communication protocol.

# Tutorials

These tutorials run a demo of cortex (Franka block stacking). It assumes scripts are run from the
`standalone_examples/cortex` directory. Note that many of the commands listed below will have to be
run in separate terminals. A convenient tool for organizing the terminals is `Terminator`.

## Basic startup and manual control

These first two tutorials will start cortex with a belief robot only. We'll look at starting both a
belief and a sim robot connected by ROS after that.

Startup cortex
```
cd standalone_examples/cortex

# The cortex script launches cortex. Take a look at the options. Then launch with the franka blocks
# world belief robot.
./cortex launch -h
./cortex launch --usd_env=omniverse://ov-isaac-dev/Users/nratliff/Cortex/Franka/BlocksWorld/cortex_franka_blocks_belief.usd
```

Select the belief world's motion controller target prim
```
/cortex/belief/motion_controller_target
```
and use the Move tool from the toolbar on the left of the viewport to manually drag it around. The
belief robot's end-effector should follow.

At this point, the end-effector will be following the _full_ pose of the motion controller target. We
can set the commander to follow only the _position_ of the target. Run
```
./cortex activate set_commander_to_position_only.py
```
You might immediately see the arm relax into a more natural configuration while maintaining the same
end-effector position. Now dragging the motion controller target will command only the
end-effector's position.

Set the commander back to tracking the full target:
```
./cortex activate set_commander_to_full_pose.py
```

Send the robot home:
```
./cortex activate go_home.py
```
Once the robot arrives at its home configuration, you can again manually control it by dragging the
motion controller target.

## Block stacking demo

Make sure the commander is set to track the full pose of the targets. Run `./activate
set_commander_to_full_pose.py` if you're unsure.

Launch the block stacking demo behavior:
```
./cortex activate franka/build_block_tower.py
```
While the block stacking demo is running, you can interact with the blocks. Move them around and see
the robot react. You can even disturb the block tower.

Note that there are no singulation behaviors currently (pushing blocks away from each other or away
from the tower region), so if blocks end up too close to each other, there might be errors in
execution. The system should still be pretty robust to those -- try helping it out and see the robot
react and pick up from where it needs to.

If the tower ends up in the wrong order, the robot will deconstruct the tower first before
reconstructing it in the right order. Try the following two things.

First, let the robot build at least part of the block tower. Then select the bottom block and use
the Move widget to drag it out from under the other blocks. The upper portion of the block tower
will fall into the gap left by the removal of the lower block, and the resulting tower will be out
of order. The robot will immediately begin deconstructing the tower and reconstructing it in the
right order.

Second, you can also run
```
./cortex activate franka/send_blocks_to_bad_tower.py
```
to send all of the blocks to the tower location, but out of order. Then restart the block stacking
demo
```
./cortex activate franka/build_block_tower.py
```
The robot will proceed to deconstruct the bad tower and reconstruct it in the right order.

## Using ROS communication for synchronization

First we'll describe how to start up cortex with both belief and sim robots and how to connect them
via ROS, then we'll outline a tutorial procedure you can run to step through some of the ideas.

### Starting cortex with both a belief and sim robot

The command for starting up the belief and sim robots with ROS enabled is similar. The only
difference is we pass it the `..._belief_sim.usd` variant of the world setup with both
`/cortex/belief` and `/cortex/sim` USD environments, and we use the flag `--enable_ros`.
```
./cortex launch \
    --usd_env=omniverse://ov-isaac-dev/Users/nratliff/Cortex/Franka/BlocksWorld/cortex_franka_blocks_belief_sim.usd \
    --enable_ros
```
Make sure a `roscore` is running. If one isn't, this command will hang (with a hint reminding you to
start the `roscore`).

This environment will load with two robots, each with its own blocks setups. The robot in front is
the belief robot, and the robot in back is the sim robot. Initially, these two robots won't be
communicating. This is similar to the physical robot setup -- we need to first start the controller
before the two connect.

From a terminal with the `cortex_control` ROS package installed and sourced run
```
rosrun cortex_control sim_controller
```
This will start a simulated controller up. That simulated controller will accept commands from the
belief robot, interpolate them, and stream low-level commands to the simulated robot at a higher
rate, mimicking the control flow used on physical robots.

When the controller starts up, it performs a synchronization handshake with the belief robot, and
you'll see the belief robot snap to the configuration the simulated robot is currently in. This
prevents the cortex controller from jerking the robot it's connecting to.

### A tutorial stepping through startup and synchronization

Try the following.

Start a `roscore`.

Start cortex with a belief and sim variant of the blocks world:
```
./cortex launch \
    --usd_env=omniverse://ov-isaac-dev/Users/nratliff/Cortex/Franka/BlocksWorld/cortex_franka_blocks_belief_sim.usd \
    --enable_ros
```
You should see the environment load with two robots. The robot in front is the belief robot; the
robot in back is the sim robot.

Start the block stacking demo:
```
./cortex activate franka/build_block_tower.py
```
You should see the belief robot start into the block stacking procedure. But since the controller
isn't currently running, the sim robot won't be following the belief robot.

The sim environment is constantly streaming the ground truth poses of the blocks to the belief, and
the block stacking behavior is set up to constantly synchronize the belief with those ground truth
poses it receives. Therefore, you'll see the belief robot try to pick up the first block, realize
that the block isn't moving in the (simulated version of the) real world, snap that block belief
back to its original location, then try again. 

It'll repeat trying to pick up the block and failing until we connect the two robots and get the sim
robot to follow the belief to make a real change to the simulated world.

Additionally, try manually moving the block the robot is trying to manipulate (initially the blue
block) in the simulated world's. You'll see the belief block follow and the robot react to that. But
still, the belief robot is unable to affect the simulated world because control hasn't been
launched.

Now start the controller. From a terminal with the `cortex_control` ROS package installed and
sourced run
```
rosrun cortex_control sim_controller
```
At this point, you'll see the belief robot snap to a configuration matching the simulated robot, and
then continue reaching toward that first block. This time the simulated robot will follow the belief
and actually pick up that first block. Now, with control running, the belief robot is making a real
impact on (the simulated version of) reality so the procedure can make progress.

If you leave it running, both robots will run in synchrony and build the block tower. The belief
robot is the one making the decisions, and the simulated robot is following that belief robot
closely, in real time, performing the same operations in (the simulated version of) reality.

## Starting cortex and connecting to a physical robot

See the description in `exts/omni.isaac.cortex/docs/README.md`.


# Details of launching cortex

Here's a full listing of the flags:
```
./cortex launch -h
usage: cortex [-h] --usd_env USD_ENV [--position_only] [--enable_ros]
              [--loop_fast] [--print_stage_prims_on_startup]
              [--print_diagnostics] [--suppress_behaviors] [--test]

optional arguments:
  -h, --help            show this help message and exit
  --usd_env USD_ENV     Path to the USD environment to load.
  --enable_ros          Enable cortex ROS-based extensions for communicating
                        with physical robots.
  --position_only       Contol only the position, not the orientation.
  --loop_fast           Usually uses a steady step of 60 hz. Setting this flag
                        tells the system to step as fast as it can.
  --print_stage_prims_on_startup
                        Prints the stage prims when the environment is first
                        loaded during startup.
  --print_diagnostics   Print diagnostic information, including profiling
                        info.
  --suppress_behaviors  If set, suppresses the behaviors. Useful for
                        diagnosing issues.
  --test                Run a simple bringup test to make sure the cortex
                        system starts.
```

The most relevant are `--usd_env` and `--enable_ros` as described above. In addition to that,
`--position_only` will set the cortex commander into position only mode from startup. That can be
set back to full pose as above using `set_commander_to_full_pose.py`. Additionally, by default the
system will loop at 60 hz. Use `--loop_fast` to set the loop runner spinning as quickly as it can
go.

The rest of the flags are for diagnostics.


# Available pre-made environments

Here's a list of pre-made environments:
```
omniverse://ov-isaac-dev/Users/nratliff/Cortex/Franka/BlocksWorld/cortex_franka_blocks_belief.usd
omniverse://ov-isaac-dev/Users/nratliff/Cortex/Franka/BlocksWorld/cortex_franka_blocks_belief_sim.usd
omniverse://ov-isaac-dev/Users/nratliff/Cortex/UR10/Basic/cortex_ur10_basic_belief.usd
omniverse://ov-isaac-dev/Users/nratliff/Cortex/UR10/Basic/cortex_ur10_basic_belief_sim.usd
```
The belief robot (under `belief`) will be controlled by the behaviors in all cases. When using a
`..._belief_sim.usd` world, a sim version of the world will be loaded as well, offset from the
belief robot. The sim robot will be present in all cases when it's in the environment, however, it's
only accessible from cortex if `--enable_ros` is selected. If it is, then starting the
`sim_controller` will synchronize the two robots, and you'll see the simulated robot following the
belief robot.

See above on more details of connecting the sim and belief robots using control. See also
`exts/omni.issac.cortex/docs/README.md` for details on the USD conventions used to setup the worlds.

# More information

See the cortex extension's readme file for detailed documentation:
```
exts/omni.isaac.cortex/omni/isaac/cortex/docs/README.md
```
