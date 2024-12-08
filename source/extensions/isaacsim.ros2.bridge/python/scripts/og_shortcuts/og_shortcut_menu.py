# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import weakref

import carb
import omni.ext
import omni.usd
from isaacsim.core.utils.viewports import set_camera_view
from isaacsim.gui.components.menu import make_menu_item_description
from isaacsim.ros2.bridge.scripts.og_shortcuts.og_rtx_sensors import Ros2CameraGraph, Ros2RtxLidarGraph
from isaacsim.ros2.bridge.scripts.og_shortcuts.og_utils import (
    Ros2ClockGraph,
    Ros2GenericPubGraph,
    Ros2JointStatesGraph,
    Ros2OdometryGraph,
    Ros2TfPubGraph,
)
from isaacsim.storage.native.nucleus import get_assets_root_path
from omni.kit.menu.utils import (
    MenuItemDescription,
    MenuLayout,
    add_layout,
    add_menu_items,
    get_menu_layout,
    remove_layout,
    remove_menu_items,
)


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self.window_handle = None
        ros_og_menu = [
            make_menu_item_description(
                ext_id, "Camera", onclick_fun=lambda a=weakref.proxy(self): a._open_camera_sensor()
            ),
            make_menu_item_description(
                ext_id, "RTX Lidar", onclick_fun=lambda a=weakref.proxy(self): a._open_rtx_lidar_sensor()
            ),
            make_menu_item_description(
                ext_id, "TF Publisher", onclick_fun=lambda a=weakref.proxy(self): a._open_pub_tf()
            ),
            make_menu_item_description(
                ext_id,
                "Odometry Publisher",
                onclick_fun=lambda a=weakref.proxy(self): a._open_odometry_publisher(),
            ),
            make_menu_item_description(
                ext_id, "Joint States", onclick_fun=lambda a=weakref.proxy(self): a._open_joint_states_pubsub()
            ),
            make_menu_item_description(ext_id, "Clock", onclick_fun=lambda a=weakref.proxy(self): a._open_clock()),
            make_menu_item_description(
                ext_id, "Generic Publisher", onclick_fun=lambda a=weakref.proxy(self): a._open_rtf()
            ),
        ]

        self._menu_items = [
            MenuItemDescription(
                name="ROS 2 OmniGraphs",
                sub_menu=ros_og_menu,
            )
        ]

        add_menu_items(self._menu_items, "Tools/Robotics")

        ros_assets_sub_menu = [
            MenuItemDescription(
                name="Asset Browser", onclick_action=("isaacsim.asset.browser", "open_isaac_sim_asset_browser")
            ),
            MenuItemDescription(
                name="Nova Carter",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Samples/ROS2/Robots/Nova_Carter_ROS.usd", "/nova_carter_ROS"
                ),
            ),
            MenuItemDescription(
                name="Leatherback",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Samples/ROS2/Robots/leatherback_ROS.usd", "/leatherback_ROS"
                ),
            ),
            MenuItemDescription(
                name="iw.hub ROS",
                onclick_fn=lambda a=weakref.proxy(self): a.create_asset(
                    "/Isaac/Samples/ROS2/Robots/iw_hub_ROS.usd", "/iw_hub_ROS"
                ),
            ),
        ]

        self._ros_assets_menu = [
            MenuItemDescription(name="ROS 2 Assets", glyph="plug.svg", sub_menu=ros_assets_sub_menu)
        ]

        add_menu_items(self._ros_assets_menu, "Create")

        # self.__ros_menu_layout = [
        #     MenuLayout.Menu(
        #         "Create",
        #         [
        #             MenuLayout.SubMenu(
        #                 "ROS 2 Assets",
        #                 [
        #                     MenuLayout.Item("Asset Browser", source="Create/ROS 2 Assets/Asset Browser"),
        #                     MenuLayout.Seperator("Examples"),
        #                     MenuLayout.Item("Room", source="Create/ROS 2 Assets/Room"),
        #                     MenuLayout.Item("Room 2", source="Create/ROS 2 Assets/Room 2"),
        #                 ],
        #             ),
        #         ]
        #     )
        # ]
        # add_layout(self.__ros_menu_layout)

    def create_asset(self, usd_path, stage_path, camera_position=None, camera_target=None):

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        path_to = omni.kit.commands.execute(
            "CreateReferenceCommand",
            usd_context=omni.usd.get_context(),
            path_to=stage_path,
            asset_path=self._assets_root_path + usd_path,
            instanceable=False,
        )

        carb.log_info(f"Added reference to {stage_path} at {path_to}")

        if camera_position is not None and camera_target is not None:
            set_camera_view(camera_position, camera_target)

        pass

    def on_shutdown(self):
        remove_menu_items(self._menu_items, "Tools/Robotics")
        remove_menu_items(self._ros_assets_menu, "Create")
        # remove_layout(self.__ros_menu_layout)

        if self.window_handle:
            self.window_handle.visible = False

    def _open_clock(self):
        if self.window_handle:
            self.window_handle.visible = False
        clock_graph = Ros2ClockGraph()
        self.window_handle = clock_graph.create_clock_graph()

    def _open_rtf(self):
        if self.window_handle:
            self.window_handle.visible = False
        clock_graph = Ros2GenericPubGraph()
        self.window_handle = clock_graph.create_generic_pub_graph()

    def _open_camera_sensor(self):
        if self.window_handle:
            self.window_handle.visible = False
        camera_graph = Ros2CameraGraph()
        self.window_handle = camera_graph.create_camera_graph()

    def _open_rtx_lidar_sensor(self):
        if self.window_handle:
            self.window_handle.visible = False
        lidar_graph = Ros2RtxLidarGraph()
        self.window_handle = lidar_graph.create_lidar_graph()

    def _open_joint_states_pubsub(self):
        if self.window_handle:
            self.window_handle.visible = False
        js_graph = Ros2JointStatesGraph()
        self.window_handle = js_graph.create_jointstates_graph()

    def _open_pub_tf(self):
        if self.window_handle:
            self.window_handle.visible = False
        tf_pub_graph = Ros2TfPubGraph()
        self.window_handle = tf_pub_graph.create_tf_pub_graph()

    def _open_odometry_publisher(self):
        if self.window_handle:
            self.window_handle.visible = False
        odom_pub_graph = Ros2OdometryGraph()
        self.window_handle = odom_pub_graph.create_odometry_graph()
