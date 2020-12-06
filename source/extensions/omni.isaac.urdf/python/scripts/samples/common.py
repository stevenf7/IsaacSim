import os
import carb.tokens


def import_robot(urdf_interface, urdf_path, import_config):
    root_path, filename = os.path.split(os.path.abspath(urdf_path))
    imported_robot = urdf_interface.parse_urdf(root_path, filename, import_config)
    path = urdf_interface.import_robot(root_path, filename, imported_robot, import_config)
    return path


def set_drive_parameters(drive, target_type, target_value, stiffness, damping, max_force=None):
    """Enable velocity drive for a given joint"""

    if target_type == "position":
        if not drive.GetTargetPositionAttr():
            drive.CreateTargetPositionAttr(target_value)
        else:
            drive.GetTargetPositionAttr().Set(target_value)
    elif target_type == "velocity":
        if not drive.GetTargetVelocityAttr():
            drive.CreateTargetVelocityAttr(target_value)
        else:
            drive.GetTargetVelocityAttr().Set(target_value)

    if not drive.GetStiffnessAttr():
        drive.CreateStiffnessAttr(stiffness)
    else:
        drive.GetStiffnessAttr().Set(stiffness)

    if not drive.GetDampingAttr():
        drive.CreateDampingAttr(damping)
    else:
        drive.GetDampingAttr().Set(damping)

    if max_force is not None:
        if not drive.GetMaxForceAttr():
            drive.CreateMaxForceAttr(max_force)
        else:
            drive.GetMaxForceAttr().Set(max_force)
