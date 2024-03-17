# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import gc

import omni.ext
import omni.usd
from omni.isaac.ros2_bridge.scripts.og_shortcuts.og_rtx_sensors import Ros2CameraGraph, Ros2RtxLidarGraph
from omni.isaac.ros2_bridge.scripts.og_shortcuts.og_utils import Ros2ClockGraph, Ros2JointStatesGraph
from omni.isaac.ui.menu import make_menu_item_description
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        ros_og_menu = [
            make_menu_item_description(ext_id, "ROS2 Camera", onclick_fun=self._open_camera_sensor),
            make_menu_item_description(ext_id, "ROS2 RTX Lidar", onclick_fun=self._open_rtx_lidar_sensor),
            # make_menu_item_description(
            #     ext_id, "ROS2 TF Tree", onclick_fun=self._open_tf_tree
            # ),
            # make_menu_item_description(
            #     ext_id, "ROS2 Navigation", onclick_fun=self._open_navigation_bundle
            # ),
            make_menu_item_description(ext_id, "ROS2 JointStates", onclick_fun=self._open_joint_states_pubsub),
            make_menu_item_description(ext_id, "ROS2 Clock", onclick_fun=self._open_clock),
        ]

        self._menu_items = [
            MenuItemDescription(
                name="Common Omnigraphs",
                sub_menu=ros_og_menu,
            )
        ]

        add_menu_items(self._menu_items, "Isaac Utils")

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Isaac Utils")
        gc.collect()
        # somehow shutdown the window

    def _open_clock(self):
        clock_graph = Ros2ClockGraph()
        clock_graph.create_clock_graph()

    def _open_camera_sensor(self):
        camera_graph = Ros2CameraGraph()
        camera_graph.create_camera_graph()

    def _open_rtx_lidar_sensor(self):
        lidar_graph = Ros2RtxLidarGraph()
        lidar_graph.create_lidar_graph()

    def _open_joint_states_pubsub(self):
        js_graph = Ros2JointStatesGraph()
        js_graph.create_jointstates_graph()
