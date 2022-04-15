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
from omni.isaac.kaya import Kaya


class KayaGamepad(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._gamepad_gains = (40.0, 40.0, 2.0)
        self._gamepad_deadzone = 0.2

    def setup_scene(self):
        world = self.get_world()
        self._kaya = world.scene.add(
            Kaya(
                prim_path="/kaya",
                name="my_kaya",
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
                    ("Gamepad1", "omni.graph.nodes.ReadGamepadState"),
                    ("Gamepad2", "omni.graph.nodes.ReadGamepadState"),
                    ("Gamepad3", "omni.graph.nodes.ReadGamepadState"),
                    ("Multiply1", "omni.graph.nodes.Multiply"),
                    ("Multiply2", "omni.graph.nodes.Multiply"),
                    ("Multiply3", "omni.graph.nodes.Multiply"),
                    ("ForwardGain", "omni.graph.nodes.ConstantFloat"),
                    ("LateralGain", "omni.graph.nodes.ConstantFloat"),
                    ("RotationGain", "omni.graph.nodes.ConstantFloat"),
                    ("Kaya", "omni.isaac.kaya.KayaController"),
                ],
                keys.SET_VALUES: [
                    ("Gamepad1.inputs:gamepadElement", "Left Stick Y Axis"),
                    ("Gamepad2.inputs:gamepadElement", "Left Stick X Axis"),
                    ("Gamepad3.inputs:gamepadElement", "Right Stick X Axis"),
                    ("Gamepad1.inputs:deadzone", self._gamepad_deadzone),
                    ("Gamepad2.inputs:deadzone", self._gamepad_deadzone),
                    ("Gamepad3.inputs:deadzone", self._gamepad_deadzone),
                    ("OnTick.inputs:onlyPlayback", True),  # only tick when simulator is playing
                    ("ForwardGain.inputs:value", -10),
                    ("LateralGain.inputs:value", 10),
                    ("RotationGain.inputs:value", 2),
                ],
                keys.CONNECT: [
                    ("OnTick.outputs:tick", "Kaya.inputs:execIn"),
                    ("ForwardGain.inputs:value", "Multiply1.inputs:a"),
                    ("LateralGain.inputs:value", "Multiply2.inputs:a"),
                    ("RotationGain.inputs:value", "Multiply3.inputs:a"),
                    ("Gamepad1.outputs:value", "Multiply1.inputs:b"),
                    ("Gamepad2.outputs:value", "Multiply2.inputs:b"),
                    ("Gamepad3.outputs:value", "Multiply3.inputs:b"),
                    ("Multiply1.outputs:product", "Kaya.inputs:forwardVelocity"),
                    ("Multiply2.outputs:product", "Kaya.inputs:lateralVelocity"),
                    ("Multiply3.outputs:product", "Kaya.inputs:rotationVelocity"),
                ],
            },
        )

    def world_cleanup(self):
        pass
