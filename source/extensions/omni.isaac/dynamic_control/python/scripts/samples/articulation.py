import carb
import omni
import asyncio
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.utils.scripts.test_utils import load_test_file
from omni.physx import _physx


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


class articulation_info:
    def __init__(self, dc):
        self._dc = dc
        self._window = omni.kit.ui.Window(
            "Articulation Info",
            300,
            200,
            menu_path="Isaac Samples/Dynamic Control/Articulation info",
            open=False,
            dock=omni.kit.ui.DockPreference.DISABLED,
        )
        sublayout = self._window.layout.add_child(omni.kit.ui.ColumnLayout())
        load_robot_btn = sublayout.add_child(omni.kit.ui.Button("Load Robot"))
        load_robot_btn.set_clicked_fn(self._on_load_robot)

        get_info_btn = sublayout.add_child(omni.kit.ui.Button("Get Info"))
        get_info_btn.set_clicked_fn(self._on_print_info)
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

    def _on_load_robot(self, widget):
        asyncio.ensure_future(load_test_file("assets/robots/franka/franka.usd"))

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
