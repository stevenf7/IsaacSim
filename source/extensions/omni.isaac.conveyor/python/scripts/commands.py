# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni
import pxr
import omni.graph.core as og
from pxr import UsdPhysics


class CreateConveyorBelt(omni.kit.commands.Command):
    """Commands class to create a Utility to control .

    Typical usage example:

    .. code-block:: python

        result, prim = omni.kit.commands.execute(
            "RangeSensorCreateGeneric",
            path="/GenericSensor",
            parent=None,
            min_range=0.4,
            max_range=100.0,
            draw_points=False,
            draw_lines=False,
            sampling_rate=60,
        )
    """

    def __init__(self, prim_name: str = "ConveyorBelt", conveyor_prim=None):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        self._stage = omni.usd.get_context().get_stage()
        self._prim_path = None
        self._conveyor_prim_selected = conveyor_prim is not None
        pass

    def do(self):
        if self._conveyor_prim is None:
            _selection = omni.usd.get_context().get_selection()
            selected_paths = _selection.get_selected_prim_paths()
            self._conveyor_prim = self._stage.GetDefaultPrim()
            self._conveyor_prim_selected = False
            if selected_paths:
                self._conveyor_prim_selected = True
                self._conveyor_prim = self._stage.GetPrimAtPath(selected_paths[0])
                if not UsdPhysics.RigidBodyAPI(self._conveyor_prim):
                    alt_conveyor = self._conveyor_prim.GetParent()
                    while alt_conveyor:
                        if UsdPhysics.RigidBodyAPI(alt_conveyor):
                            self._conveyor_prim = alt_conveyor
                            break
                        alt_conveyor = alt_conveyor.GetParent()
                    if not alt_conveyor:
                        UsdPhysics.RigidBodyAPI.Apply(self._conveyor_prim)
                        UsdPhysics.CollisionAPI.Apply(self._conveyor_prim)
        self._prim_path = omni.usd.get_stage_next_free_path(
            self._stage, self._conveyor_prim.GetPath().AppendChild(pxr.Tf.MakeValidIdentifier(self._prim_name)), True
        )
        keys = og.Controller.Keys
        og.Controller.edit(
            {"graph_path": self._prim_path, "evaluator_name": "execution"},
            {
                keys.CREATE_NODES: [
                    ("OnTick", "omni.graph.action.OnTick"),
                    ("conveyor", "omni.isaac.conveyor.Conveyor"),
                ],
                keys.SET_VALUES: [],
                keys.CONNECT: [
                    ("OnTick.outputs:tick", "conveyor.inputs:onStep"),
                    ("OnTick.outputs:deltaSeconds", "conveyor.inputs:delta"),
                ],
            },
        )
        if self._conveyor_prim_selected:
            conveyor_node = self._stage.GetPrimAtPath(self._prim_path + "/conveyor")
            input_rel = conveyor_node.GetRelationship("inputs:conveyorPrim")
            if not input_rel:
                input_rel = conveyor_node.CreateRelationship("inputs:conveyorPrim")
            input_rel.SetTargets([self._conveyor_prim.GetPath()])

        self._prim = self._stage.GetPrimAtPath(self._prim_path)
        return True, self._prim

    def undo(self):
        if self._prim:
            return self._stage.RemovePrim(self._prim_path)
        pass


omni.kit.commands.register_all_commands_in_module(__name__)
