from enum import Enum

import pxr


class Classes(Enum):
    ROBOT_API = "RobotAPI"
    LINK_API = "LinkAPI"
    REFERENCE_POINT_API = "ReferencePointAPI"
    JOINT_API = "JointAPI"


_attr_prefix = "isaac"


class Attributes(Enum):
    DESCRIPTION = (f"{_attr_prefix}:description", pxr.Sdf.ValueTypeNames.String)
    NAMESPACE = (f"{_attr_prefix}:namespace", pxr.Sdf.ValueTypeNames.String)
    INDEX = (f"{_attr_prefix}:physics:index", pxr.Sdf.ValueTypeNames.Int)
    NAME_OVERRIDE = (f"{_attr_prefix}:nameOverride", pxr.Sdf.ValueTypeNames.String)
    FORWARD_AXIS = (f"{_attr_prefix}:forwardAxis", pxr.Sdf.ValueTypeNames.Token)
    JOINT_INDEX = (f"{_attr_prefix}:physics:index", pxr.Sdf.ValueTypeNames.Int)
    ROT_X_OFFSET = (f"{_attr_prefix}:physics:Rot_X:DofOffset", pxr.Sdf.ValueTypeNames.Int)
    ROT_Y_OFFSET = (f"{_attr_prefix}:physics:Rot_Y:DofOffset", pxr.Sdf.ValueTypeNames.Int)
    ROT_Z_OFFSET = (f"{_attr_prefix}:physics:Rot_Z:DofOffset", pxr.Sdf.ValueTypeNames.Int)
    TR_X_OFFSET = (f"{_attr_prefix}:physics:Tr_X:DofOffset", pxr.Sdf.ValueTypeNames.Int)
    TR_Y_OFFSET = (f"{_attr_prefix}:physics:Tr_Y:DofOffset", pxr.Sdf.ValueTypeNames.Int)
    TR_Z_OFFSET = (f"{_attr_prefix}:physics:Tr_Z:DofOffset", pxr.Sdf.ValueTypeNames.Int)
    ACCELERATION_LIMIT = (f"{_attr_prefix}:physics:AccelerationLimit", pxr.Sdf.ValueTypeNames.FloatArray)
    JERK_LIMIT = (f"{_attr_prefix}:physics:JerkLimit", pxr.Sdf.ValueTypeNames.FloatArray)
    ACTUATOR = (f"{_attr_prefix}:physics:JerkLimit", pxr.Sdf.ValueTypeNames.BoolArray)
    # Custom properties for name and type
    @property
    def name(self):
        return self.value[0]

    @property
    def type(self):
        return self.value[1]


class Relations(Enum):
    ROBOT_LINKS = f"{_attr_prefix}:physics:robotLinks"
    ROBOT_JOINTS = f"{_attr_prefix}:physics:robotjoints"


def ApplyRobotAPI(prim: pxr.Usd.Prim):
    prim.AddAppliedSchema(Classes.ROBOT_API.value)
    for attr in [Attributes.DESCRIPTION, Attributes.NAMESPACE]:
        prim.CreateAttribute(attr.name, attr.type, True)

    for rel in [Relations.ROBOT_LINKS, Relations.ROBOT_JOINTS]:
        prim.CreateRelationship(rel.value, custom=True)


def ApplyLinkAPI(prim: pxr.Usd.Prim):
    prim.AddAppliedSchema(Classes.LINK_API.value)
    for attr in [Attributes.NAME_OVERRIDE]:
        prim.CreateAttribute(attr.name, attr.type, True)


def ApplyReferencePointAPI(prim: pxr.Usd.Prim):
    prim.AddAppliedSchema(Classes.REFERENCE_POINT_API.value)
    for attr in [Attributes.DESCRIPTION, Attributes.FORWARD_AXIS]:
        prim.CreateAttribute(attr.name, attr.type, True)


def ApplyJointAPI(prim: pxr.Usd.Prim):
    prim.AddAppliedSchema(Classes.JOINT_API.value)
    for attr in [
        Attributes.ROT_X_OFFSET,
        Attributes.ROT_Y_OFFSET,
        Attributes.ROT_Z_OFFSET,
        Attributes.TR_X_OFFSET,
        Attributes.TR_Y_OFFSET,
        Attributes.TR_Z_OFFSET,
        Attributes.NAME_OVERRIDE,
        Attributes.ACCELERATION_LIMIT,
        Attributes.JERK_LIMIT,
    ]:
        prim.CreateAttribute(attr.name, attr.type, True)
