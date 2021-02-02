import os
import carb
from omni.isaac.synthetic_utils import OmniKitHelper

CONFIG = {
    "experience": f'{os.environ["EXP_PATH"]}/isaac-sim.python.kit',
    "renderer": "RayTracedLighting",
    "headless": True,
}

if __name__ == "__main__":
    # Example usage, with step size test
    kit = OmniKitHelper(config=CONFIG)
    import omni.physx
    from omni.isaac.dynamic_control import _dynamic_control
    from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server

    stage = kit.get_stage()

    result, nucleus_server = find_nucleus_server()
    if result is False:
        carb.log_error("Could not find nucleus server with /Isaac folder")
    asset_path = nucleus_server + "/Isaac/Robots/Franka/franka_alt_fingers.usd"
    omni.usd.get_context().open_stage(asset_path)
    # start simulation
    kit.play()

    # perform step experiments
    kit.update(1.0 / 60.0)

    dc = _dynamic_control.acquire_dynamic_control_interface()

    ar = dc.get_articulation("/panda")
    if ar == _dynamic_control.INVALID_HANDLE:
        print("*** '%s' is not an articulation" % "/panda")
    else:
        root = dc.get_articulation_root_body(ar)
        print(str("Got articulation handle %d \n" % ar) + str("--- Hierarchy\n"))

        body_states = dc.get_articulation_body_states(ar, _dynamic_control.STATE_ALL)
        print(str("--- Body states:\n") + str(body_states) + "\n")

        dof_states = dc.get_articulation_dof_states(ar, _dynamic_control.STATE_ALL)
        print(str("--- DOF states:\n") + str(dof_states) + "\n")

        dof_props = dc.get_articulation_dof_properties(ar)
        print(str("--- DOF properties:\n") + str(dof_props) + "\n")
    kit.stop()
    kit.shutdown()
