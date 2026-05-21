# SPDX-FileCopyrightText: Copyright (c) 2022-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Static information panel with title, doc link, and overview text."""

from __future__ import annotations

from isaacsim.gui.components.ui_utils import setup_ui_headers

from ..constants import EXTENSION_NAME

_DOC_LINK = "https://docs.isaacsim.omniverse.nvidia.com/latest/manipulators/manipulators_robot_description_editor.html"

_OVERVIEW = (
    "This utility is used to help generate a Lula Robot Description YAML file required to use Lula-based "
    "algorithms like RmpFlow, RRT, and Lula Kinematics, or to generate an XRDF file for use with Isaac "
    "cuMotion or future releases of Lula. Both file types contain a collision sphere representation of the "
    "robot that is used for collision avoidance, and information that is required to interpret the robot "
    "URDF.\n\n"
    "To begin using this editor, load a robot USD file onto the stage and press the 'Play' button.  In the "
    "'Selection Panel', select your robot from the 'Select Articulation' drop-down menu.  The 'Select Link' "
    "drop-down menu will populate once an Articulation has been selected.  The user may create collision "
    "spheres for the robot one link at a time. \n\n"
    "Joint Properties Panel:\nIn the Joint Properties Panel, the user may select the default positions of "
    "robot joints and choose a subset of joints that are considered 'Active Joints'. 'Active Joints' are "
    "considered to be directly controllable, while 'Fixed Joints' are assumed to never move. The default "
    "positions that 'Active Joints' are set to are used by Lula algorithms to resolve null-space behavior. "
    "For example, RmpFlow is typically configured to control only the joints in a robot arm, and assume "
    "the gripper to be in a fixed position.  While moving the gripper to a target, it will choose a path "
    "that moves the robot close to the default 'Active Joints' configuration.  By default, all joints are "
    "marked as 'Fixed Joints', which will cause Lula not to control the robot at all.  The user must "
    "determine a set of joints that should be considered 'Active'.  Maximum jerk and accelerations are "
    "required to be specified for each active joint in the robot.\n\n"
    "Adding Collision Spheres:\nIn the 'Link Sphere Editor' panel paired with 'Editor Tools', the user may "
    "add collision spheres on a per-link basis.  Spheres are added with positions specified relative to the "
    "base of the selected link, with their position relative to the link being fixed.  Once a sphere has "
    "been created, the user may move it around, resize or delete it on the USD stage until it looks right. "
    "Additionally, the user may generate spheres for a link automatically or select any two spheres under a "
    "link and linearly interpolate to create more spheres connecting them.  In general, the user will want "
    "to fully cover the robot in spheres, using around 40-60 spheres total.  It is easiest to create such a "
    "set of spheres when individual spheres are allowed to slightly exceed the volume of the robot. \n\n"
    "Importing and Exporting:\nLula robot description YAML files and cuMotion XRDF files are both supported "
    "file types for importing and exporting data from the Robot Description Editor. The Robot Description "
    "Editor does not represent every possible field in an XRDF file, and so when exporting to an existing "
    "XRDF file path, the user will have an option to pull data from the existing file that should not be "
    "overwritten by leaving the default setting to 'Merge With Existing XRDF'."
)


class InfoPanel:
    """Renders the static header / overview text for the extension window."""

    def __init__(self, ext_id: str, source_file: str) -> None:
        self._ext_id = ext_id
        self._source_file = source_file

    def build(self) -> None:
        """Build the static info section."""
        setup_ui_headers(self._ext_id, self._source_file, EXTENSION_NAME, _DOC_LINK, _OVERVIEW)
