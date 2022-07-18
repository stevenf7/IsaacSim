# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.graph.core as og


class ScreenPrinter:
    def __init__(self, screen_pos_x=78, screen_pos_y=95):
        self.keys = og.Controller.Keys
        self.controller = og.Controller()

        (self.graph, self.nodes, _, _) = self.controller.edit(
            {"graph_path": "/World/PrintActionGraph", "evaluator_name": "push"},
            {
                self.keys.CREATE_NODES: [
                    ("tick", "omni.graph.action.OnTick"),
                    ("print_to_screen", "omni.graph.visualization.nodes.DrawScreenSpaceText"),
                ],
                self.keys.CONNECT: [("tick.outputs:tick", "print_to_screen.inputs:execIn")],
                self.keys.SET_VALUES: [
                    ("print_to_screen.inputs:position", [screen_pos_x, screen_pos_y]),
                    ("print_to_screen.inputs:text", ""),
                ],
            },
        )

    def set_text(self, text: str):
        self.controller.edit(self.graph, {self.keys.SET_VALUES: (("inputs:text", self.nodes[1]), text)})

    def clear_text(self):
        self.set_text("")
