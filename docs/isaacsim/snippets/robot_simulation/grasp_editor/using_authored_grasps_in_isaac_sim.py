from isaacsim.core.utils.xforms import get_world_pose
from isaacsim.robot_setup.grasp_editor import GraspSpec, import_grasps_from_file

import_file_path = "/path/to/franka_mug_grasp.yaml"
grasp_spec = import_grasps_from_file(import_file_path)

mug_reference_frame = "/World/mug"

grasp_names = grasp_spec.get_grasp_names()

mug_trans, mug_quat = get_world_pose(mug_reference_frame)
gripper_trans_target, gripper_orientation_target = grasp_spec.compute_gripper_pose_from_rigid_body_pose(
    "grasp_1", mug_trans, mug_quat
)

print("Grasp Names:", grasp_names)
print("Gripper Translation Target:", gripper_trans_target)
print("Gripper Orientation Target:", gripper_orientation_target)
