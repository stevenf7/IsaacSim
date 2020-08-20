import os
import carb.tokens


def import_robot(urdf_interface, path, import_config):
    urdf_path = os.path.abspath(carb.tokens.get_tokens_interface().resolve("${app}/../" + path))
    root_path, filename = os.path.split(os.path.abspath(urdf_path))
    imported_robot = urdf_interface.parse_urdf(root_path, filename, import_config)
    urdf_interface.import_robot(root_path, filename, imported_robot, import_config)


def remove_all_schema_multiple_attributes(api, prim, schemaAPI, apiName):
    """For a given prim, remove all properties attached to a schema"""
    names = api.GetSchemaAttributeNames(False, apiName)
    schemaName = schemaAPI + ":" + apiName
    for name in names:
        attrRemove = schemaName + ":" + str(name)
        prim.RemoveProperty(attrRemove)
    pass


def set_drive_parameters(drive, target_type, target_value, stiffness, damping, max_force):
    """Enable velocity drive for a given joint"""

    if not drive.GetTargetTypeAttr():
        drive.CreateTargetTypeAttr(target_type)
    else:
        drive.GetTargetTypeAttr().Set(target_type)

    if not drive.GetTargetAttr():
        drive.CreateTargetAttr(target_value)
    else:
        drive.GetTargetAttr().Set(target_value)

    if not drive.GetStiffnessAttr():
        drive.CreateStiffnessAttr(stiffness)
    else:
        drive.GetStiffnessAttr().Set(stiffness)

    if not drive.GetDampingAttr():
        drive.CreateDampingAttr(damping)
    else:
        drive.GetDampingAttr().Set(damping)

    if not drive.GetMaxForceAttr():
        drive.CreateMaxForceAttr(max_force)
    else:
        drive.GetMaxForceAttr().Set(max_force)
