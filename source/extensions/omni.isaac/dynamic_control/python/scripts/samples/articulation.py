import carb
import omni
import asyncio
from omni.isaac.dynamic_control import _dynamic_control
from pxr import Usd
import os
from omni.physx import _physx


def get_data_file(file_name: str):
    if os.path.isabs(file_name):
        path_to_file = file_name
    else:
        path_to_file = os.path.abspath(
            os.path.join(carb.tokens.get_tokens_interface().resolve("${app}"), "..", "data", "usd", file_name)
        )
    return path_to_file


async def load_test_file(test_file_name: str):
    """
    Load the contents of the USD test file onto the stage, synchronously, when called as "await load_test_file(X)".
    In a testing environment we need to run one test at a time since there is no guarantee
    that tests can run concurrently, especially when loading files. This method encapsulates
    the logic necessary to load a test file using the omni.kit.asyncapi method and then wait
    for it to complete before returning.
    :param test_file_name: Name of the test file to load - if not an absolute path then looks in the data/usd/tests/ComputeGraph directory
    :raises: ValueError if the test file is not a valid USD file
    """
    if not Usd.Stage.IsSupportedFile(test_file_name):
        raise ValueError("Only USD files can be loaded with this method")

    path_to_file = get_data_file(test_file_name)

    usd_context = omni.usd.get_context()
    usd_context.disable_save_to_recent_files()
    (result, error) = await omni.kit.asyncapi.open_stage(path_to_file)
    usd_context.enable_save_to_recent_files()
    return (result, error)


def _print_body_rec(dc, body, indent_level=0):
    indent = " " * indent_level

    body_name = dc.get_rigid_body_name(body)
    str_output = "%sBody: %s\n" % (indent, body_name)

    for i in range(dc.get_rigid_body_child_joint_count(body)):
        joint = dc.get_rigid_body_child_joint(body, i)
        joint_name = dc.get_joint_name(joint)
        child = dc.get_joint_child_body(joint)
        child_name = dc.get_rigid_body_name(child)
        str_output = str_output + "%s  Joint: %s -> %s\n" % (indent, joint_name, child_name)
        str_output = str_output + _print_body_rec(dc, child, indent_level + 4)
    return str_output


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._window = omni.kit.ui.Window(
            "Articulation Info",
            300,
            200,
            menu_path="Isaac Robotics/Dynamic Control/Articulation info",
            open=False,
            dock=omni.kit.ui.DockPreference.LEFT_BOTTOM,
        )
        sublayout = self._window.layout.add_child(omni.kit.ui.ColumnLayout())
        sublayout.add_child(
            omni.kit.ui.Label(
                "This sample demonstrates how to load a USD stage containing an articulated robot and then retreiving that articulation and using the dynamic_control python API to query it",
                clippingmode=omni.kit.ui.ClippingType.WRAP,
            )
        )

        load_robot_btn = sublayout.add_child(omni.kit.ui.Button("Load Franka USD"))
        load_robot_btn.set_clicked_fn(self._on_load_robot)
        load_robot_btn.tooltip = omni.kit.ui.Label("Press to load the Franka USD file and start simulation")
        get_info_btn = sublayout.add_child(omni.kit.ui.Button("Get Articulation Info"))
        get_info_btn.set_clicked_fn(self._on_print_info)
        get_info_btn.tooltip = omni.kit.ui.Label("Pressing this button will print information below")
        sublayout.add_child(
            omni.kit.ui.Label(
                'Note: The buttons above only work with the robot loaded by the "Load Franka USD" button and not existing robots/articulations in the stage'
            )
        )
        sublayout.add_child(omni.kit.ui.Separator())
        scrolling_frame = sublayout.add_child(omni.kit.ui.ScrollingFrame("", -1, -1))
        self.hierarchy_label = scrolling_frame.add_child(
            omni.kit.ui.Label("", useclipboard=True, clippingmode=omni.kit.ui.ClippingType.WRAP)
        )
        self.body_states_label = scrolling_frame.add_child(
            omni.kit.ui.Label("", useclipboard=True, clippingmode=omni.kit.ui.ClippingType.WRAP)
        )
        self.dof_states_label = scrolling_frame.add_child(
            omni.kit.ui.Label("", useclipboard=True, clippingmode=omni.kit.ui.ClippingType.WRAP)
        )
        self.dof_props_label = scrolling_frame.add_child(
            omni.kit.ui.Label("", useclipboard=True, clippingmode=omni.kit.ui.ClippingType.WRAP)
        )
        self._physxIFace = _physx.acquire_physx_interface()
        self._editor = omni.kit.editor.get_editor_interface()

    def on_shutdown(self):
        _dynamic_control.release_dynamic_control_interface(self._dc)
        _physx.release_physx_interface(self._physxIFace)
        self._editor = None
        self._window = None

    async def _setup_camera(self, task):
        # wait for the stage load task to finish before setting camera and starting simulation
        done, pending = await asyncio.wait({task})
        if task in done:
            self._editor.set_camera_position("/OmniverseKit_Persp", 150, 150, 50, True)
            self._editor.set_camera_target("/OmniverseKit_Persp", 0, 0, 50, True)
            self._editor.play()

    def _on_load_robot(self, widget):
        task = asyncio.ensure_future(load_test_file("assets/robots/franka/franka.usd"))
        asyncio.ensure_future(self._setup_camera(task))

    def _on_print_info(self, widget):
        self._physxIFace.force_load_physics_from_usd()

        ar = self._dc.get_articulation("/panda")
        if ar == _dynamic_control.INVALID_HANDLE:
            print("*** '%s' is not an articulation" % "/panda")
            return

        root = self._dc.get_articulation_root_body(ar)
        self.hierarchy_label.text = (
            str("Got articulation handle %d \n" % ar) + str("--- Hierarchy\n") + _print_body_rec(self._dc, root)
        )

        body_states = self._dc.get_articulation_body_states(ar, _dynamic_control.STATE_ALL)
        self.body_states_label.text = str("--- Body states:\n") + str(body_states) + "\n"

        dof_states = self._dc.get_articulation_dof_states(ar, _dynamic_control.STATE_ALL)
        self.dof_states_label.text = str("--- DOF states:\n") + str(dof_states) + "\n"

        dof_props = self._dc.get_articulation_dof_properties(ar)
        self.dof_props_label.text = str("--- DOF properties:\n") + str(dof_props) + "\n"

        return
