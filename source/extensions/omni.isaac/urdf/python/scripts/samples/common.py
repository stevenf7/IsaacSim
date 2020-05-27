import os
import carb.tokens


def import_robot(urdf_interface, path, import_config):
    urdf_path = os.path.abspath(carb.tokens.get_tokens_interface().resolve("${app}/../" + path))
    urdf_interface.import_urdf(urdf_path, import_config)


def remove_all_schema_multiple_attributes(api, prim, schemaAPI, apiName):
    """For a given prim, remove all properties attached to a schema"""
    names = api.GetSchemaAttributeNames(False, apiName)
    schemaName = schemaAPI + ":" + apiName
    for name in names:
        attrRemove = schemaName + ":" + str(name)
        prim.RemoveProperty(attrRemove)
    pass


def set_angular_drive(drive, target_vel):
    """Enable velocity drive for a given joint"""

    if not drive.GetTargetTypeAttr():
        drive.CreateTargetTypeAttr("velocity")
    else:
        drive.GetTargetTypeAttr().Set("velocity")

    if not drive.GetTargetAttr():
        drive.CreateTargetAttr(target_vel)
    else:
        drive.GetTargetAttr().Set(target_vel)

    if not drive.GetStiffnessAttr():
        drive.CreateStiffnessAttr(0)
    else:
        drive.GetStiffnessAttr().Set(0)

    if not drive.GetDampingAttr():
        drive.CreateDampingAttr(100000)
    else:
        drive.GetDampingAttr().Set(100000)
