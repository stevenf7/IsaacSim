# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
import omni.ext
import omni.appwindow
import omni.ui as ui
import weakref
import omni.kit.settings
import gc
import numpy as np
import asyncio
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

from omni.isaac.dynamic_control import _dynamic_control

from pxr import Gf, UsdGeom, UsdPhysics

from omni.isaac.utils.scripts.scene_utils import set_up_z_axis, setup_physics, create_background
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server

import socket
import struct
import time
import threading

EXTENSION_NAME = "DofBot Picking"


def toDegree(x):
    return x * 180 / np.pi


def toRad(x):
    return x * np.pi / 180


class Extension(omni.ext.IExt):
    def on_startup(self):
        """Initialize extension and UI elements"""

        # IP address of the real dofbot if you have one
        self._ip_address = None
        self.port = 65432  # Port to listen on (non-privileged ports are > 1023)

        self._pickup_button_pressed = False

        # joint angular positions for cube picking trajectory
        # dofbot has 6 joints : from the base to the gripper
        self.cube_picking_trajectory = [
            [90, 90, 90, 90, 90, 90],
            [90, 90, 90, 90, 90, 70],
            [90, 20, 90, 90, 90, 70],
            [90, 20, 45, 90, 90, 70],
            [90, 20, 45, 90, 90, 150],
            [90, 50, 45, 90, 90, 150],
            [90, 50, 45, 90, 90, 150],
        ]

        # spend 1000ms or 1 second for each action
        self.cube_picking_trajectory_sim_time = [1000, 1000, 1000, 1000, 1000, 1000]

        self.curr_action_index = 0
        self.ready_for_next_action = True
        self.use_sim_only = False  # can't connect to the real dofbot
        self._socket = None

        self.curr_sim_position = self.cube_picking_trajectory[0]
        self.start_time = 0
        self.real_bot_delay = 300
        self.real_to_sim_angle_offset = 90

        self._timeline = omni.timeline.get_timeline_interface()
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._appwindow = omni.appwindow.get_default_app_window()
        self._sub_stage_event = self._usd_context.get_stage_event_stream().create_subscription_to_pop(
            self._on_stage_event
        )

        self._dofbot_articulation = _dynamic_control.INVALID_HANDLE

        self._window = None
        self._load_dofbot_btn = None
        self._send_current_joints_btn = False
        self._pickup_cube_btn = False
        self._time = 0.0

        self.cube_path = "/cube"
        self.cube_size = 3
        self.cube_position = (31, 0, self.cube_size / 2)
        self.work_threads = []

        # set up dofbot menu
        menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        self._menu_items = [
            MenuItemDescription(
                name="Controlling", sub_menu=[MenuItemDescription(name="Manipulation", sub_menu=menu_items)]
            )
        ]
        add_menu_items(self._menu_items, "Isaac Examples")

    def _menu_callback(self):
        self._build_ui()

    def _build_ui(self):
        if not self._window:
            self._window = ui.Window(
                title=EXTENSION_NAME, width=300, height=200, visible=True, dockPreference=ui.DockPreference.LEFT_BOTTOM
            )
            # self._window.set_update_fn(self._on_update_ui)

            with self._window.frame:
                with ui.VStack():
                    self._load_dofbot_btn = ui.Button(
                        "Load DofBot",
                        clicked_fn=self._on_environment_setup,
                        tooltip="Reset the stage and load the dofbot environment",
                    )

                    self._pickup_cube_btn = ui.Button(
                        "Pick up the cube", clicked_fn=self._on_pickup_cube, tooltip="Pick up the cube"
                    )

                    self._send_current_joints_btn = ui.Button(
                        "Send current joint states to real DofBot",
                        clicked_fn=self._on_send_current_states,
                        tooltip="Send current joint states to real DofBot",
                    )

                    omni.ui.Label("Real DofBot IP Address: ")
                    self._ip_address = omni.ui.StringField().model
                    hostNums = ["0.0.0.0"]
                    self._ip_address.set_value(hostNums[0])

                    self._load_dofbot_btn.enabled = True
                    self._send_current_joints_btn.enabled = False
                    self._pickup_cube_btn.enabled = False

        self._window.visible = True

    def _on_send_current_states(self):
        self.send_joint_states_to_real_dofbot()

    def _set_joints_in_sim(self, joint_position_array):
        """Takes in desired positions of each DofBot servo in degrees, sets target position
        of sim to that position in radians
        """
        self._dc.wake_up_articulation(self._dofbot_articulation)

        for i in range(len(joint_position_array)):
            if i == 0:
                self._dc.set_dof_position_target(
                    self._base_joint, toRad(joint_position_array[i] - self.real_to_sim_angle_offset)
                )
            elif i == 1:
                self._dc.set_dof_position_target(
                    self._shouder_pan_joint, toRad(joint_position_array[i] - self.real_to_sim_angle_offset)
                )
            elif i == 2:
                self._dc.set_dof_position_target(
                    self._shouder_lift_joint, toRad(joint_position_array[i] - self.real_to_sim_angle_offset)
                )
            elif i == 3:
                self._dc.set_dof_position_target(
                    self._elbow_joint, toRad(joint_position_array[i] - self.real_to_sim_angle_offset)
                )
            elif i == 4:
                self._dc.set_dof_position_target(
                    self._wrist_joint, toRad(joint_position_array[i] - self.real_to_sim_angle_offset)
                )
            elif i == 5:
                self._dc.set_dof_position_target(self._finger_left_01_joint, toRad(joint_position_array[i] / 2 - 45))
                self._dc.set_dof_position_target(self._finger_right_01_joint, -toRad(joint_position_array[i] / 2 - 45))

    def _set_joints_real_dofbot(self):
        """Send the target positions to the real dofbot via TCP/IP"""
        currTime = time.time()
        self.ready_for_next_action = False

        curr_action = self.cube_picking_trajectory[self.curr_action_index]

        try:
            # Create a TCP/IP socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (self._ip_address.get_value_as_string(), self.port)
            self._socket.connect(server_address)

            print("curr_action_index #: " + str(self.curr_action_index))
            print(curr_action)
            values = (curr_action[0], curr_action[1], curr_action[2], curr_action[3], curr_action[4], curr_action[5])
            packer = struct.Struct("f f f f f f")
            packed_data = packer.pack(*values)

            # Send data
            # print("sending" + binascii.hexlify(packed_data), values)
            self._socket.sendall(packed_data)

            self.start_time = time.time() * 1000

            # put acknowledgement waiting from the real dofbot in another thread to not block
            t = threading.Thread(target=self.wait_for_ack, daemon=True)
            t.start()
            self.work_threads.append(t)

            print("_set_joints_real_dofbot takes this long : ", time.time() - currTime)

            self.use_sim_only = False

        except socket.error as e:
            print("Can't connect to real DofBot, just use Sim")
            self.ready_for_next_action = True
            self.use_sim_only = True

    def wait_for_ack(self):
        """Create a separate thread to wait for ack so sim doesn't get blocked"""
        print("wait_for_ack")

        try:
            currTime = time.time()
            encodedAckText = self._socket.recv(1024)
            print("Time taken for ack: ", time.time() - currTime)
            ackText = encodedAckText.decode("utf-8")
            print("Ack msg: ", ackText)

            if ackText == "complete":
                self.ready_for_next_action = True
            elif ackText == "":
                print("Empty message received")
            else:
                print("Unexpected result received")
            print("closing socket")
            print("\n  \n")
            self._socket.close()

        except socket.error as e:
            print("Error: ", e)

    def _on_pickup_cube(self):
        """Sends the action stored in self.cube_picking_trajectory to the real JetBot for execution"""
        # reset cube position
        cube_body = self._dc.get_rigid_body(self.cube_path)
        new_pose = _dynamic_control.Transform(self.cube_position, (0, 0, 0, 1))
        self._dc.set_rigid_body_pose(cube_body, new_pose)

        for thread in self.work_threads:
            thread.join()
        self.work_threads.clear()

        #  Reset values to prepare for another iteration
        self.curr_action_index = 0
        self.curr_sim_position = self.cube_picking_trajectory[0]
        self._pickup_button_pressed = True
        self.ready_for_next_action = True
        self.start_time = time.time() * 1000.0  # currTime in ms

    def send_joint_states_to_real_dofbot(self):
        # Create a new TCP/IP socket for one time sending
        try:
            new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (self._ip_address.get_value_as_string(), self.port)
            new_socket.connect(server_address)
        except socket.error as e:
            print("no connection to the real dofbot")
            return

        self.use_sim_only = False

        base_joint_pos_orig = self._dc.get_dof_position(self._base_joint)
        base_joint_pos = toDegree(base_joint_pos_orig) + self.real_to_sim_angle_offset

        shouder_pan_joint_pos = (
            toDegree(self._dc.get_dof_position(self._shouder_pan_joint)) + self.real_to_sim_angle_offset
        )
        shouder_lift_joint_pos = (
            toDegree(self._dc.get_dof_position(self._shouder_lift_joint)) + self.real_to_sim_angle_offset
        )
        elbow_joint_pos = toDegree(self._dc.get_dof_position(self._elbow_joint)) + self.real_to_sim_angle_offset
        wrist_joint_pos = toDegree(self._dc.get_dof_position(self._wrist_joint)) + self.real_to_sim_angle_offset
        finger_left_01_joint_pos = (
            2.0 * toDegree(self._dc.get_dof_position(self._finger_left_01_joint)) + self.real_to_sim_angle_offset + 45
        )

        values = (
            base_joint_pos,
            shouder_pan_joint_pos,
            shouder_lift_joint_pos,
            elbow_joint_pos,
            wrist_joint_pos,
            finger_left_01_joint_pos,
        )

        packer = struct.Struct("f f f f f f")
        packed_data = packer.pack(*values)

        try:
            # Send data
            new_socket.sendall(packed_data)
        finally:
            print("closing socket")
            new_socket.close()

    async def _create_dofbot(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            print("Loading DofBot Environment")
            self._viewport.set_camera_position("/OmniverseKit_Persp", 150, 150, 50, True)
            self._viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)
            self._stage = self._usd_context.get_stage()
            result, nucleus_server = find_nucleus_server()
            if result is False:
                carb.log_error("Could not find nucleus server with /Isaac folder")
                return

            self._asset_path = nucleus_server + "/Isaac"
            dofbot_usd = self._asset_path + "/Robots/Dofbot/dofbot.usd"

            prim_path = "/dofbot"
            self.prim = self._stage.DefinePrim(prim_path, "Xform")
            self.prim.GetReferences().AddReference(dofbot_usd)

            set_up_z_axis(self._stage)
            setup_physics(self._stage)

            create_background(
                self._stage,
                self._asset_path + "/Environments/Grid/gridroom_black.usd",
                background_path="/background",
                offset=Gf.Vec3d(0, 0, 14),
            )

            # add a cube
            cubeGeom = UsdGeom.Cube.Define(self._stage, self.cube_path)
            self.cube_prim = self._stage.GetPrimAtPath(self.cube_path)
            cubeGeom.CreateSizeAttr(self.cube_size)
            cubeGeom.AddTranslateOp().Set(Gf.Vec3f(self.cube_position))
            await omni.kit.app.get_app().next_update_async()  # Need this to avoid flatcache errors
            rigid_api = UsdPhysics.RigidBodyAPI.Apply(self.cube_prim)
            rigid_api.CreateRigidBodyEnabledAttr(True)
            UsdPhysics.CollisionAPI.Apply(self.cube_prim)

            # start stepping after dofbot is created
            self._editor_event_subscription = (
                omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._on_editor_step)
            )

            self.count = 0

    def _on_environment_setup(self):
        # wait for new stage before creating dofbot
        self._retrieve_joints_check = False
        task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._create_dofbot(task))

    def _on_stage_event(self, event):
        """This function is called when stage events occur.
        Enables UI elements when stage is opened.
        Prevents tasks from being started until all assets are loaded

        Arguments:
            event (int): event type
        """
        if event.type == int(omni.usd.StageEventType.OPENED):
            if self._window:
                self._load_dofbot_btn.enabled = True
                self._send_current_joints_btn.enabled = False
                self._pickup_cube_btn.enabled = False
                self._editor_event_subscription = None
                self._timeline.stop()
                self._stop_tasks()

        if event.type == int(omni.usd.StageEventType.CLOSED):
            self._dofbot_articulation = _dynamic_control.INVALID_HANDLE

    def _stop_tasks(self):
        gc.collect()

    def _on_editor_step(self, step):
        """Updates dofbot Sim physics once per step"""
        if not self._timeline.is_playing():
            self._send_current_joints_btn.text = "Press Play to Enable Controller"
            self._send_current_joints_btn.enabled = False
            self._pickup_cube_btn.text = "Press Play to Enable Controller"
            self._pickup_cube_btn.enabled = False
            return

        if not self._dc.is_simulating():
            return
        if not self._retrieve_joints_check:
            self._retrieve_joints()

        # Wake up articulation every move command to ensure commands are applied
        if self._dofbot_articulation != _dynamic_control.INVALID_HANDLE:
            self._dc.wake_up_articulation(self._dofbot_articulation)

            self._send_current_joints_btn.text = "Send current joint states to real DofBot"
            self._pickup_cube_btn.text = "Pick up the cube"
            self._load_dofbot_btn.enabled = False
            self._send_current_joints_btn.enabled = True
            self._pickup_cube_btn.enabled = True

            # Execute move action commands in the Sim
            if self._pickup_button_pressed:

                # Time since last message sent in ms
                currTime = (time.time() * 1000) - self.start_time

                # sim only path
                if self.use_sim_only:
                    # print(
                    #     currTime,
                    #     " > ",
                    #     self.cube_picking_trajectory_sim_time[self.curr_action_index],
                    #     " ",
                    #     self.curr_action_index,
                    # )
                    if currTime > self.cube_picking_trajectory_sim_time[self.curr_action_index]:
                        self.curr_action_index += 1
                        self.curr_sim_position = self.cube_picking_trajectory[self.curr_action_index]
                        self.start_time = time.time() * 1000

                    if self.curr_action_index >= len(self.cube_picking_trajectory) - 1:  # Last action
                        self._pickup_button_pressed = False

                else:  # both sim and real dofbot
                    # Keep sim 1 sub-action behind real until self.real_bot_delay has elapsed
                    if self.curr_action_index > 0:
                        self.curr_sim_position = self.cube_picking_trajectory[self.curr_action_index - 1]

                    if currTime > self.real_bot_delay:
                        self.curr_sim_position = self.cube_picking_trajectory[self.curr_action_index]

                    # We've received the ack, move forward 1 sub-action
                    if self.ready_for_next_action:
                        if self.curr_action_index >= len(self.cube_picking_trajectory) - 1:  # Last action
                            self._pickup_button_pressed = False
                            self._set_joints_real_dofbot()
                        else:
                            self.curr_action_index += 1
                            # Set joints on real dofbot
                            self._set_joints_real_dofbot()

                # Set position in sim
                self._set_joints_in_sim(self.curr_sim_position)

        else:
            self._load_dofbot_btn.enabled = True
            self._send_current_joints_btn.enabled = False
            self._pickup_cube_btn.enabled = False

    def _retrieve_joints(self):
        """retrieve articulation joints"""
        if self._dofbot_articulation == _dynamic_control.INVALID_HANDLE:
            self._dofbot_articulation = self._dc.get_articulation(str(self.prim.GetPath()))

        self._base_joint = self._dc.find_articulation_dof(self._dofbot_articulation, "Base_RevoluteJoint")
        self._shouder_pan_joint = self._dc.find_articulation_dof(
            self._dofbot_articulation, "Shoulder_Pan_RevoluteJoint"
        )
        self._shouder_lift_joint = self._dc.find_articulation_dof(
            self._dofbot_articulation, "Shoulder_Lift_RevoluteJoint"
        )
        self._elbow_joint = self._dc.find_articulation_dof(self._dofbot_articulation, "Elbow_RevoluteJoint")
        self._wrist_joint = self._dc.find_articulation_dof(self._dofbot_articulation, "Wrist_Lift_RevoluteJoint")
        self._finger_left_01_joint = self._dc.find_articulation_dof(
            self._dofbot_articulation, "Finger_Left_01_RevoluteJoint"
        )
        self._finger_right_01_joint = self._dc.find_articulation_dof(
            self._dofbot_articulation, "Finger_Right_01_RevoluteJoint"
        )

        # set shoulder pan to 0
        self._dc.set_dof_position(self._shouder_pan_joint, 0)

        self._retrieve_joints_check = True

    def on_shutdown(self):
        """Cleanup objects on extension shutdown"""
        self._timeline.stop()
        self._dc = None
        self._editor_event_subscription = None
        self._sub_stage_event = None
        self._stop_tasks()
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None
        gc.collect()
