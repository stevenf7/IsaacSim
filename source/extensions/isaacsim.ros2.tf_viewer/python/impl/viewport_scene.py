# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
import omni.ui as ui
from omni.ui import color as cl
from omni.ui import scene as sc

from .view_manipulator import ViewManipulator


class ViewportScene:
    def __init__(self, viewport_window: ui.Window, ext_id: str) -> None:
        self._scene_view = None
        self._viewport_window = viewport_window

        # scene view frame
        with self._viewport_window.get_frame(ext_id):
            # scene view (default camera-model)
            self._scene_view = sc.SceneView()

            # add handlers into the scene view's scene
            with self._scene_view.scene:
                self.manipulator = ViewManipulator()
                self.manipulator.update_transforms({}, [])

            # register the scene view to get projection and view updates
            self._viewport_window.viewport_api.add_scene_view(self._scene_view)

    def __del__(self):
        self.destroy()

    def destroy(self):
        if self._scene_view:
            # empty the scene view
            self._scene_view.scene.clear()
            # un-register the scene view
            if self._viewport_window:
                self._viewport_window.viewport_api.remove_scene_view(self._scene_view)
        # remove references
        self._viewport_window = None
        self._scene_view = None
