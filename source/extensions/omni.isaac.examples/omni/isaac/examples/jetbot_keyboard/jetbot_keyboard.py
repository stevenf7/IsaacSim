# Copyright (c) 2021-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import omni.ext
import numpy as np
import omni.graph.core as og
from omni.isaac.core.utils.viewports import set_camera_view
from omni.isaac.examples.base_sample import BaseSample
from omni.isaac.jetbot import Jetbot


class JetbotKeyboard(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._gamepad_gains = (40.0, 40.0, 2.0)
        self._gamepad_deadzone = 0.15

    def setup_scene(self):
        world = self.get_world()
        self._jetbot = world.scene.add(
            Jetbot(
                prim_path="/jetbot",
                name="my_jetbot",
                position=np.array([0, 0.0, 2.0]),
                orientation=np.array([1.0, 0.0, 0.0, 0.0]),
            )
        )
        world.scene.add_default_ground_plane()
        set_camera_view(eye=np.array([75, 75, 45]), target=np.array([0, 0, 0]))

        # setup graph
        keys = og.Controller.Keys
        og.Controller.edit(
            {"graph_path": "/controller_graph", "evaluator_name": "execution"},
            {
                keys.CREATE_NODES: [
                    ("OnTick", "omni.graph.action.OnTick"),
                    ("W", "omni.graph.nodes.ReadKeyboardState"),
                    ("S", "omni.graph.nodes.ReadKeyboardState"),
                    ("A", "omni.graph.nodes.ReadKeyboardState"),
                    ("D", "omni.graph.nodes.ReadKeyboardState"),
                    ("ToFloat1", "omni.graph.nodes.ToFloat"),
                    ("ToFloat2", "omni.graph.nodes.ToFloat"),
                    ("ToFloat3", "omni.graph.nodes.ToFloat"),
                    ("ToFloat4", "omni.graph.nodes.ToFloat"),
                    ("Multiply1", "omni.graph.nodes.Multiply"),
                    ("Multiply2", "omni.graph.nodes.Multiply"),
                    ("Multiply3", "omni.graph.nodes.Multiply"),
                    ("Multiply4", "omni.graph.nodes.Multiply"),
                    ("LinearAdd", "omni.graph.nodes.Add"),
                    ("RotationAdd", "omni.graph.nodes.Add"),
                    ("ForwardGain", "omni.graph.nodes.ConstantFloat"),
                    ("BackwardGain", "omni.graph.nodes.ConstantFloat"),
                    ("LeftGain", "omni.graph.nodes.ConstantFloat"),
                    ("RightGain", "omni.graph.nodes.ConstantFloat"),
                    ("Jetbot", "omni.isaac.jetbot.JetbotController"),
                ],
                keys.SET_VALUES: [
                    ("W.inputs:key", "W"),
                    ("S.inputs:key", "S"),
                    ("A.inputs:key", "A"),
                    ("D.inputs:key", "D"),
                    ("OnTick.inputs:onlyPlayback", True),  # only tick when simulator is playing
                    ("ForwardGain.inputs:value", 50.0),
                    ("BackwardGain.inputs:value", -50.0),
                    ("LeftGain.inputs:value", 20),
                    ("RightGain.inputs:value", -20),
                ],
                keys.CONNECT: [
                    ("OnTick.outputs:tick", "Jetbot.inputs:execIn"),
                    ("ForwardGain.inputs:value", "Multiply1.inputs:a"),
                    ("BackwardGain.inputs:value", "Multiply2.inputs:a"),
                    ("LeftGain.inputs:value", "Multiply3.inputs:a"),
                    ("RightGain.inputs:value", "Multiply4.inputs:a"),
                    ("W.outputs:isPressed", "ToFloat1.inputs:value"),
                    ("S.outputs:isPressed", "ToFloat2.inputs:value"),
                    ("A.outputs:isPressed", "ToFloat3.inputs:value"),
                    ("D.outputs:isPressed", "ToFloat4.inputs:value"),
                    ("ToFloat1.outputs:converted", "Multiply1.inputs:b"),
                    ("ToFloat2.outputs:converted", "Multiply2.inputs:b"),
                    ("ToFloat3.outputs:converted", "Multiply3.inputs:b"),
                    ("ToFloat4.outputs:converted", "Multiply4.inputs:b"),
                    ("Multiply1.outputs:product", "LinearAdd.inputs:a"),
                    ("Multiply2.outputs:product", "LinearAdd.inputs:b"),
                    ("Multiply3.outputs:product", "RotationAdd.inputs:a"),
                    ("Multiply4.outputs:product", "RotationAdd.inputs:b"),
                    ("LinearAdd.outputs:sum", "Jetbot.inputs:forwardVelocity"),
                    ("RotationAdd.outputs:sum", "Jetbot.inputs:rotationVelocity"),
                ],
            },
        )

    def world_cleanup(self):
        pass
