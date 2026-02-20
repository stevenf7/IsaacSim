import omni
from isaacsim.robot_setup.assembler import RobotAssembler

# Prerequisites: Have both the base robot and the attach robot loaded in the stage at the paths specified below (or change the paths to where the assets are loaded in your stage)

# Prim path to the base robot
robot_base = "/World/BaseRobot"
# Prim path to the mount point of the base robot
robot_base_mount = "/World/BaseRobot/Mount"
# Prim path to the attach robot
robot_attach = "/World/AttachRobot"
# Prim path to the mount point of the attach robot
robot_attach_mount = "/World/AttachRobot/Mount"
# Assembly namespace
assembly_namespace = "Gripper"
variant_name = "my_assembled_robot"


stage = omni.usd.get_context().get_stage()
assembler = RobotAssembler()


# Begin the Assembly process - Creates a session layer and attach it to the current stage, where all the modifications necessary for the assembly will be made.
assembler.begin_assembly(
    stage, robot_base, robot_base_mount, robot_attach, robot_attach_mount, assembly_namespace, variant_name
)

# Perform any Additional transformations on the Attach robot pose here directly through USD.

assembler.assemble()

# That's where the Robot Assembler will create the fixed joint between the two robots.
# It will also remove Physic's Articualtion Root from the attached robot, and disable the root joint that attaches 	robot to the world, if it exists.
# If you need to perform any physics simulation test - this is the time to do it.
# If the assembly is successful, and you are ready to finish the assembly, you can call the following function.
# Otherwise at any point you can call the `assembler.cancel_assemble()` function to cancel the assembly process.
# It will remove the session layer from the stage, undoing any changes made to the stage.


assembler.finish_assemble()

# This function will finish the assembly process by adding the attachment link to the parent robot joint and link lists, and then either merge the session layer into the current stage, or save a configuration file, and remove the session layer from the stage.
# If modifing a robot asset directly, it will also create the variant set to load the configuration for the assembled component through a payload.
