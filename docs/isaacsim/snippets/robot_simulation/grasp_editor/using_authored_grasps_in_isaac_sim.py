"""Tutorial snippet showing how to use an authored isaac_grasp file from Python.

The portion of this file between the `<start-...>` and `<end-...>`
markers is what gets rendered in the Grasp Editor documentation page. The remainder of
the file is scaffolding that lets the script run end-to-end against a temporary stage
and a temporary grasp file so that the snippet's documented output can be reproduced
without external assets.
"""

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--test", default=False, action="store_true", help="Run in test mode.")
args, _ = parser.parse_known_args()

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

import isaacsim.core.experimental.utils.app as app_utils

app_utils.enable_extension("isaacsim.robot_setup.grasp_editor")

# <start-function-snippet>
import isaacsim.core.experimental.utils.xform as xform_utils
from isaacsim.robot_setup.grasp_editor import GraspSpec, import_grasps_from_file


def compute_gripper_pose_for_grasp(
    import_file_path: str,
    mug_reference_frame: str = "/World/mug",
    grasp_name: str = "grasp_1",
) -> tuple:
    """Compute and print the gripper pose target needed to execute a named grasp.

    Args:
        import_file_path: Path to an ``isaac_grasp`` YAML file to import.
        mug_reference_frame: USD prim path of the rigid body whose pose anchors the grasp.
        grasp_name: Name of the grasp inside the file to compute targets for.

    Returns:
        Tuple of ``(gripper_trans_target, gripper_orientation_target)``.
    """
    grasp_spec: GraspSpec = import_grasps_from_file(import_file_path)
    grasp_names = grasp_spec.get_grasp_names()

    mug_trans, mug_quat = xform_utils.get_world_pose(mug_reference_frame, device="cpu")
    mug_trans, mug_quat = mug_trans.numpy(), mug_quat.numpy()

    gripper_trans_target, gripper_orientation_target = grasp_spec.compute_gripper_pose_from_rigid_body_pose(
        grasp_name, mug_trans, mug_quat
    )

    print("Grasp Names:", grasp_names)
    print("Gripper Translation Target:", gripper_trans_target)
    print("Gripper Orientation Target:", gripper_orientation_target)

    return gripper_trans_target, gripper_orientation_target


# <end-function-snippet>

# ---------------------------------------------------------------------------
# Runnable scaffolding (not part of the documented snippet).
#
# Builds a minimal stage with ``/World/mug`` at identity pose and a temporary
# isaac_grasp YAML whose ``grasp_1`` entry is chosen so that, with the mug at
# identity, the function above prints exactly the expected output documented
# in ``docs/isaacsim/robot_simulation/grasp_editor.rst``.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import tempfile

    import isaacsim.core.experimental.utils.stage as stage_utils
    from pxr import UsdGeom

    stage_utils.create_new_stage()
    stage = stage_utils.get_current_stage()
    UsdGeom.Xform.Define(stage, "/World")
    UsdGeom.Xform.Define(stage, "/World/mug")

    # With ``/World/mug`` at identity, ``compute_gripper_pose_from_rigid_body_pose``
    # returns ``grasp_1``'s stored ``position`` and ``orientation`` directly, so the
    # values below are chosen to match the documented expected output.
    tmp_yaml = (
        "format: isaac_grasp\n"
        "format_version: 1.0\n"
        "\n"
        "object_frame: /World/mug\n"
        "gripper_frame: /World/panda_hand\n"
        "\n"
        "grasps:\n"
        "  grasp_0:\n"
        "    confidence: 1.0\n"
        "    position: [-0.04346, 0.06759, 0.19895]\n"
        "    orientation: {w: 0.00332, xyz: [0.98453, 0.16837, 0.04837]}\n"
        "    cspace_position:\n"
        "      panda_finger_joint1: 0.00943\n"
        "    pregrasp_cspace_position:\n"
        "      panda_finger_joint1: 0.04\n"
        "\n"
        "  grasp_1:\n"
        "    confidence: 1.0\n"
        "    position: [0.41496072, -0.03612298, 0.27738899]\n"
        "    orientation: {w: -0.1690746, xyz: [0.63886658, 0.12752551, 0.73959483]}\n"
        "    cspace_position:\n"
        "      panda_finger_joint1: 0.00943\n"
        "    pregrasp_cspace_position:\n"
        "      panda_finger_joint1: 0.04\n"
        "\n"
        "  grasp_2:\n"
        "    confidence: 1.0\n"
        "    position: [0.18, 0.03, 0.22]\n"
        "    orientation: {w: 0.7071, xyz: [0.0, 0.7071, 0.0]}\n"
        "    cspace_position:\n"
        "      panda_finger_joint1: 0.012\n"
        "    pregrasp_cspace_position:\n"
        "      panda_finger_joint1: 0.04\n"
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(tmp_yaml)
        tmp_path = f.name

    try:
        compute_gripper_pose_for_grasp(
            import_file_path=tmp_path,
            mug_reference_frame="/World/mug",
            grasp_name="grasp_1",
        )
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        simulation_app.close()
