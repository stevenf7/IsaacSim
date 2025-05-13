from functools import partial

import omni.ui as ui
import omni.usd
from omni.kit.widget.filter import FilterButton
from omni.kit.widget.options_button import OptionsButton
from omni.kit.widget.options_menu import OptionItem
from omni.kit.widget.searchfield import SearchField
from pxr import UsdGeom

from ..builders.joint_helper import (
    AXIS_LIST,
    DRIVE_TYPES,
    JOINT_TYPES,
    apply_drive_settings,
    apply_joint_apis,
    apply_joint_settings,
    define_joints,
    get_all_settings,
)
from ..builders.robot_templates import RobotRegistry
from ..style import get_popup_window_style
from ..utils.resetable_widget import ResetableComboBox, ResetableField, ResetableLabelField
from ..utils.robot_asset_picker import RobotAssetPicker
from ..utils.treeview_delegate import (
    SearchableItem,
    TreeViewIDColumn,
    TreeViewWithPlacerHolderDelegate,
    TreeViewWithPlacerHolderModel,
)
from ..utils.ui_utils import ButtonWithIcon, custom_header, info_frame, next_step, separator


class JointItem(SearchableItem):
    def __init__(self, name, joint_type, axis, drive_type="None", parent="body0", child="body1", editable=True):
        super().__init__()
        self.name = ui.SimpleStringModel(name)
        self.joint_type = ui.SimpleStringModel(joint_type)  # Joint Type: prismatic, revolute, spherical, fixed, d6
        self.axis = ui.SimpleStringModel(axis)
        self.parent = ui.SimpleStringModel(parent)
        self.child = ui.SimpleStringModel(child)
        self.editable = ui.SimpleBoolModel(editable)

        # TODO: joint setting, should wrap it into a joint setting class?
        self.drive_type = ui.SimpleStringModel(drive_type)  # Drive TYPES: acceleration, force
        self.break_force = ui.SimpleFloatModel(1e6)
        self.break_torque = ui.SimpleFloatModel(1e6)
        self.lower_limit = ui.SimpleFloatModel(-360)
        self.upper_limit = ui.SimpleFloatModel(360)

        # TODO: drive setting, should wrap it into a drive setting class?
        self.max_force = ui.SimpleFloatModel(1e9)
        self.target_position = ui.SimpleFloatModel(0.0)
        self.target_velocity = ui.SimpleFloatModel(0.0)
        self.damping = ui.SimpleFloatModel(1e3)
        self.stiffness = ui.SimpleFloatModel(1e4)
        self.text = " ".join((name, joint_type, axis, drive_type))

    def refresh_text(self):
        # TODO: should refresh text when item edited, so should add some on_item_changed callback in build function
        self.text = " ".join(
            (
                self.name.get_value_as_string(),
                self.joint_type.get_value_as_string(),
                self.axis.get_value_as_string(),
                self.drive_type.get_value_as_string(),
                self.parent.get_value_as_string(),
                self.child.get_value_as_string(),
            )
        )

    def set_property(self, property_name, value):
        """
        Sets the value of a specified property and refreshes the display text.

        Args:
            property_name (str): The name of the property to set (e.g., 'name', 'parent', 'child', 'axis', 'type', 'drive').
            value: The value to set for the property.
        """
        if hasattr(self, property_name):
            getattr(self, property_name).set_value(value)
            self.refresh_text()


class JointsModel(TreeViewWithPlacerHolderModel):
    def __init__(self, items):
        super().__init__(items)
        self._edit_window = None

    def destroy(self):
        if self._edit_window:
            self._edit_window.destroy()
        self._edit_window = None

        super().destroy()

    def get_item_value_model(self, item, column_id):
        """
        Return value model.
        It's the object that tracks the specific value.
        In our case we use ui.SimpleStringModel for the first column
        and SimpleFloatModel for the second column.
        """
        if isinstance(item, JointItem):
            if column_id == 1:
                return item.name
            elif column_id == 2:
                return item.joint_type
            elif column_id == 3:
                return item.axis
            elif column_id == 4:
                return item.drive_type
            elif column_id == 5:
                return item.parent
            elif column_id == 6:
                return item.child

    def edit_item(self, item):
        # This item is not necessarily the tree view selection.
        if not self._edit_window:
            self._edit_window = CreateJointWindow("Edit Joint", self, item)
        elif item:
            self._edit_window._window.visible = True
            self._edit_window._update_ui(item)

    def remove_item(self, item, enabled):
        # remove the joint from the robot
        robot = RobotRegistry().get()
        stage = omni.usd.get_context().get_stage()
        if not robot or not stage:
            return
        robot_name = robot.name
        joint_name = item.name.get_value_as_string()
        joint_path = f"/{robot_name}/Joints/{joint_name}"
        joint_prim = stage.GetPrimAtPath(joint_path)
        if joint_prim.IsValid():
            stage.RemovePrim(joint_prim.GetPath())

        super().remove_item(item, enabled)


class JointsandDrives:
    """Frame for the `Add Joints & Drivers` page"""

    def __init__(self, visible, *args, **kwargs):
        self.visible = visible
        self._tree_view = None
        self._treeview_empty_page = None
        self._create_joint_window = None
        self.joint_settings_stack = None
        self.drive_settings_stack = None
        self.articulation_root_stack = None
        self.__subscription = None
        self._joint_model = None
        self._next_step_button = None
        self._apply_settings_button = None
        self._treeview_initial_height = 200
        self.frame = ui.Frame(visible=visible)
        self.frame.set_build_fn(self._build_frame)
        self._select_robot_asset_window = None

    def destroy(self):
        self.__subscription = None
        if self._joint_model:
            self._joint_model.destroy()
        self._joint_model = None
        if self._create_joint_window:
            self._create_joint_window.destroy()
        self._create_joint_window = None
        if self._tree_view:
            self._tree_view.destroy()
        self._tree_view = None
        self._treeview_empty_page = None
        if self._select_robot_asset_window:
            self._select_robot_asset_window.destroy()
        self._select_robot_asset_window = None

    def _build_frame(self):
        with ui.ScrollingFrame():
            with ui.CollapsableFrame("Joints and Drives", build_header_fn=custom_header):
                with ui.ScrollingFrame():
                    with ui.VStack():
                        with ui.VStack(spacing=2, name="margin_vstack"):
                            separator("Create Joint")
                            ui.Spacer(height=4)
                            ui.Label(
                                "Joints are used as articulation points betwwen two parts",
                                name="sub_separator",
                                height=0,
                                word_wrap=True,
                            )
                            ui.Spacer(height=20)

                            with ui.ZStack(height=0):
                                ui.Rectangle(name="treeview")
                                with ui.HStack():
                                    ui.Spacer(width=2)
                                    with ui.VStack():
                                        ui.Spacer(height=4)
                                        with ui.HStack(spacing=4, height=0):
                                            # Search field
                                            self._search = SearchField(on_search_fn=self._filter_by_text)
                                            # Filter button
                                            self._filter_button = FilterButton([], width=20)
                                        ui.Spacer(height=4)
                                        self._build_tree_view()
                                        ui.Spacer(height=4)
                                    ui.Spacer(width=2)

                            ButtonWithIcon("Create New Joint", name="add", height=44, clicked_fn=self.create_joint)

                        with ui.VStack(spacing=20, name="setting_margin_vstack"):
                            self.joint_settings()
                            self.drive_settings()
                            self.select_articulation_root()

                        with ui.VStack(spacing=2, name="margin_vstack"):
                            ui.Spacer(height=10)
                            separator("Next: Save Robot")
                            ui.Spacer(height=12)
                            with ui.HStack():
                                self._apply_settings_button = ButtonWithIcon(
                                    "Apply Settings",
                                    name="next",
                                    clicked_fn=lambda: self._apply_settings_to_robot(self._tree_view.selection[0]),
                                    height=44,
                                    enabled=False,
                                )
                                ui.Spacer(width=10)
                                self._next_step_button = ButtonWithIcon(
                                    "Save Robot",
                                    name="next",
                                    clicked_fn=lambda: next_step(
                                        "Add Joints & Drivers", "Save Robot", self.add_joint_to_robot
                                    ),
                                    height=44,
                                    enabled=False,
                                )

    def select(self, selected_paths):
        self._select_robot_asset_window.visible = False
        self._selected_paths = selected_paths
        if self._selected_paths:
            self._articulation_root_widget.model.set_value(self._selected_paths[0])
            self._articulation_root_widget.checked = True
            self._next_step_button.enabled = True

    def select_robot_asset(self):
        if not self._select_robot_asset_window:
            stage = omni.usd.get_context().get_stage()
            self._select_robot_asset_window = RobotAssetPicker(
                "Select Robot Asset",
                stage,
                on_targets_selected=self.select,
                target_name="base of the robot",
            )
        self._select_robot_asset_window.visible = True

    def select_articulation_root(self):
        self.articulation_root_stack = ui.ZStack()
        with self.articulation_root_stack:
            ui.Rectangle(name="save_stack")
            with ui.VStack(spacing=8, name="setting_content_vstack"):
                separator("Articulation Root")
                ui.Label(
                    "The Articulation Root defines the first link or joint in the articulation chain.",
                    name="sub_separator",
                    word_wrap=True,
                    height=0,
                )
                with ui.HStack(height=0):
                    ui.Spacer(width=2)
                    self._articulation_root_widget = ui.StringField(width=300)
                    self._articulation_root_widget.model.set_value("Pick from the Robot")
                    ui.Spacer(width=2)
                    ui.Image(name="sample", width=24, mouse_pressed_fn=lambda x, y, b, a: self.select_robot_asset())

    def joint_settings(self):
        self.joint_settings_stack = ui.ZStack(visible=bool(self._tree_view.selection))
        if not self._tree_view.selection:
            return
        self.build_joint_settings_content(self._tree_view.selection[0])

    def build_joint_settings_content(self, current_item):
        self.joint_settings_stack.clear()
        with self.joint_settings_stack:
            ui.Rectangle(name="save_stack")
            with ui.VStack(spacing=8, name="setting_content_vstack"):
                separator("Joint Settings")
                ui.Spacer(height=6)
                with ui.HStack(height=22):
                    ui.Label("Parent Xform", name="property")
                    ui.Label("Child Xform", name="property")
                with ui.HStack(height=22):
                    self._parent_field = ui.StringField(name="resetable")
                    self._parent_field.model.set_value(current_item.parent.get_value_as_string())
                    self._parent_field.model.add_value_changed_fn(
                        lambda m: self._update_xform(current_item, current_item.parent, m)
                    )
                    ui.Spacer(width=30)
                    self._child_field = ui.StringField(name="resetable")
                    self._child_field.model.set_value(current_item.child.get_value_as_string())
                    self._child_field.model.add_value_changed_fn(
                        lambda m: self._update_xform(current_item, current_item.child, m)
                    )
                    ui.Spacer(width=30)
                ui.Spacer(height=4)
                with ui.HStack(height=22):
                    self._break_able_check = ui.CheckBox(width=25, height=22)
                    self._break_able_check.model.set_value(True)
                    self._break_able_check.model.add_value_changed_fn(
                        lambda m: self._set_joint_breakable(m.get_value_as_bool())
                    )
                    ui.Label("Joint is Breakable", width=0, height=0, name="property")
                with ui.HStack(height=0):
                    ui.Label("Break Force", name="property")
                    ui.Label("  Break Torque", name="property")
                with ui.HStack(height=22, spacing=10):
                    self._break_force_field = ResetableField(current_item.break_force, ui.FloatField)
                    self._break_torque_field = ResetableField(current_item.break_torque, ui.FloatField)
                ui.Spacer(height=4)
                with ui.HStack(height=30):
                    self._rotation_limit_check = ui.CheckBox(width=25, height=22)
                    self._rotation_limit_check.model.set_value(True)
                    self._rotation_limit_check.model.add_value_changed_fn(
                        lambda m: self._set_rotation_limit(m.get_value_as_bool())
                    )
                    ui.Label("Rotation is Limited", width=0, height=0, name="property")
                with ui.HStack(height=0):
                    ui.Label("Lower Limit", name="property")
                    ui.Label("  Upper Limit", name="property")
                with ui.HStack(height=22, spacing=10):
                    self._lower_limit_field = ResetableLabelField(
                        current_item.lower_limit, ui.FloatField, alignment=ui.Alignment.RIGHT
                    )
                    self._upper_limit_field = ResetableLabelField(
                        current_item.upper_limit, ui.FloatField, alignment=ui.Alignment.RIGHT
                    )

    def _update_xform(self, current_item, value_model, model):
        new_value = model.get_value_as_string()
        value_model.set_value(new_value)
        self._joint_model._item_changed(current_item)

    def _set_joint_breakable(self, enable):
        self._break_force_field.enable = enable
        self._break_torque_field.enable = enable

    def _set_rotation_limit(self, enable):
        self._lower_limit_field.enable = enable
        self._upper_limit_field.enable = enable

    def drive_settings(self):
        self.drive_settings_stack = ui.ZStack(visible=bool(self._tree_view.selection))
        if not self._tree_view.selection:
            return
        self.build_drive_settings_content(self._tree_view.selection[0])

    def build_drive_settings_content(self, current_item):
        self.drive_settings_stack.clear()
        with self.drive_settings_stack:
            ui.Rectangle(name="save_stack")
            with ui.VStack(spacing=8, name="setting_content_vstack"):
                separator("Drive Settings")
                ui.Spacer(height=6)
                with ui.HStack(height=0):
                    ui.Label("Type", name="property")
                    ui.Label("  Max Force", name="property")
                with ui.HStack(height=30, spacing=10):
                    self._drive_type_widget = ResetableComboBox(
                        current_item.drive_type, DRIVE_TYPES, partial(self._joint_model._item_changed, current_item)
                    )
                    ResetableField(current_item.max_force, ui.FloatField)
                with ui.HStack(height=0):
                    ui.Label("Target Position", name="property")
                    ui.Label("  Target Velocity", name="property")
                with ui.HStack(height=30, spacing=10):
                    ResetableField(current_item.target_position, ui.FloatField)
                    ResetableField(current_item.target_velocity, ui.FloatField)
                with ui.HStack(height=0):
                    ui.Label("Damping", name="property")
                    ui.Label("  Stiffness", name="property")
                with ui.HStack(height=30, spacing=10):
                    ResetableField(current_item.damping, ui.FloatField)
                    ResetableField(current_item.stiffness, ui.FloatField)

    def rebuild_settings(self, item):
        self.build_joint_settings_content(item)
        self.build_drive_settings_content(item)

    def _apply_settings_to_robot(self, current_item):
        """
        add joints and apply settings to the robot
        """

        robot = RobotRegistry().get()
        robot_name = robot.name
        if not robot:
            return

        # apply the settings to the selected joint
        joint_name = current_item.name.get_value_as_string()
        joint_type = current_item.joint_type.get_value_as_string()
        axis = current_item.axis.get_value_as_string()
        parent = current_item.parent.get_value_as_string()
        child = current_item.child.get_value_as_string()

        break_force = current_item.break_force.get_value_as_float()
        break_torque = current_item.break_torque.get_value_as_float()
        lower_limit = current_item.lower_limit.get_value_as_float()
        upper_limit = current_item.upper_limit.get_value_as_float()

        drive_type = current_item.drive_type.get_value_as_string()
        max_force = current_item.max_force.get_value_as_float()
        target_position = current_item.target_position.get_value_as_float()
        target_velocity = current_item.target_velocity.get_value_as_float()
        damping = current_item.damping.get_value_as_float()
        stiffness = current_item.stiffness.get_value_as_float()

        joint_path = f"/{robot_name}/Joints/{joint_name}"
        define_joints(joint_path=joint_path, joint_type=joint_type, axis=axis, parent=parent, child=child)

        apply_joint_settings(
            joint_path=joint_path,
            break_force=break_force,
            break_torque=break_torque,
            lower_limit=lower_limit,
            upper_limit=upper_limit,
        )

        apply_drive_settings(
            joint_path=joint_path,
            drive_type=drive_type,
            max_force=max_force,
            target_position=target_position,
            target_velocity=target_velocity,
            damping=damping,
            stiffness=stiffness,
        )

        self.articulation_root_stack.visible = True
        self._next_step_button.enabled = True

    def create_joint(self):
        if not self._create_joint_window:
            self._create_joint_window = CreateJointWindow("Create Joint", self._joint_model)
        self._create_joint_window._window.visible = True

    def _filter_by_text(self, filters):
        if self._joint_model:
            self._joint_model.filter_by_text(filters)

    def _update_settings_ui(self, item):
        # update the settings panel
        if item.parent.get_value_as_string() != self._parent_field.model.get_value_as_string():
            self._parent_field.model.set_value(item.parent.get_value_as_string())
        if item.child.get_value_as_string() != self._child_field.model.get_value_as_string():
            self._child_field.model.set_value(item.child.get_value_as_string())
        if (
            item.drive_type.get_value_as_string()
            != self._drive_type_widget._box.model.get_item_value_model().get_value_as_string()
        ):
            self._drive_type_widget._box.model.get_item_value_model().set_value(
                DRIVE_TYPES.index(item.drive_type.get_value_as_string())
            )
        if (
            item.joint_type.get_value_as_string()
            != self._joint_type_widget._box.model.get_item_value_model().get_value_as_string()
        ):
            self._joint_type_widget._box.model.get_item_value_model().set_value(
                JOINT_TYPES.index(item.joint_type.get_value_as_string())
            )
        if item.axis.get_value_as_string() != self._axis_collection.model.get_value_as_string():
            self._axis_collection.model.set_value(AXIS_LIST.index(item.axis.get_value_as_string()))
        if item.name.get_value_as_string() != self._joint_name_widget.model.get_value_as_string():
            self._joint_name_widget.model.set_value(item.name.get_value_as_string())

    def _model_changed(self, model, item):
        # item data changed
        if item:
            # we only update the settings panel when the item triggers the change is the same as the one selected in the
            # tree view, which means the item properties the settings panel is showing
            if self._tree_view.selection and item == self._tree_view.selection[0]:
                # update the settings panel
                self._update_settings_ui(item)

                return
        # item=None, root is changing meaning item has been added or removed
        if self._joint_model._searchable_num > 0:
            if self._treeview_empty_page.visible:
                self._treeview_empty_page.visible = False
        elif self._joint_model._searchable_num == 0:
            if self._next_step_button.enabled:
                self._next_step_button.enabled = False
            if not self._treeview_empty_page.visible:
                self._treeview_empty_page.visible = True
            if self.joint_settings_stack.visible:
                self.joint_settings_stack.visible = False
            if self.drive_settings_stack.visible:
                self.drive_settings_stack.visible = False
            if self._apply_settings_button:
                self._apply_settings_button.enabled = False

        # when self._joint_model changes, we update the id_column delegate
        if self._joint_model._searchable_num < TreeViewIDColumn.DEFAULT_ITEM_NUM:
            return
        if self._joint_model._searchable_num > self.id_column.num:
            self.id_column.add_item()
        elif self._joint_model._searchable_num < self.id_column.num:
            self.id_column.remove_item()

    def set_visible(self, visible):
        if self.frame:
            if visible:
                self._parse_joints_params()
            self.frame.visible = visible

    def _parse_joints_params(self):
        robot = RobotRegistry().get()
        stage = omni.usd.get_context().get_stage()
        if not robot or not stage:
            return

        # get joints folder
        settings_dict = {}

        if not self._joint_model:
            self._joint_model = JointsModel([])

        robot_name = robot.name
        joints_scope_path = f"/{robot_name}/Joints"
        joints_scope_prim = stage.GetPrimAtPath(joints_scope_path)
        if not joints_scope_prim:
            return
        joint_prims = joints_scope_prim.GetChildren()
        if joint_prims:
            for joint_prim in joint_prims:
                settings_dict = get_all_settings(joint_prim.GetPath().pathString)
            if settings_dict:
                self._joint_model.add_item(
                    JointItem(
                        name=settings_dict["joint_name"],
                        joint_type=settings_dict["joint_type"],
                        axis=settings_dict["axis"],
                        parent=settings_dict["parent"],
                        child=settings_dict["child"],
                        drive_type=settings_dict["drive_type"],
                        break_force=settings_dict["break_force"],
                        break_torque=settings_dict["break_torque"],
                        lower_limit=settings_dict["lower_limit"],
                        upper_limit=settings_dict["upper_limit"],
                        max_force=settings_dict["max_force"],
                        target_position=settings_dict["target_position"],
                        target_velocity=settings_dict["target_velocity"],
                        damping=settings_dict["damping"],
                        stiffness=settings_dict["stiffness"],
                    )
                )

    def __selection_changed(self, selection):
        if selection:
            item = selection[0]
            if isinstance(item, JointItem):
                self.rebuild_settings(item)
                self.joint_settings_stack.visible = True
                self.drive_settings_stack.visible = True
                self._apply_settings_button.enabled = True
                return

        self.joint_settings_stack.visible = False
        self.drive_settings_stack.visible = False
        self._apply_settings_button.enabled = False

    def treeview_empty_page(self):
        self._treeview_empty_page = ui.VStack(visible=True, height=self._treeview_initial_height)
        with self._treeview_empty_page:
            ui.Spacer(height=ui.Fraction(3))
            ui.Label("Joint list is empty", alignment=ui.Alignment.CENTER, name="empty_treeview_title")
            ui.Spacer(height=ui.Fraction(2))
            ui.Label("There are no joints created yet", alignment=ui.Alignment.CENTER)
            ui.Spacer(height=ui.Fraction(2))
            ui.Label("Click the 'Create New Joint' button", alignment=ui.Alignment.CENTER)
            ui.Label("to begin the joint creation process", alignment=ui.Alignment.CENTER)
            ui.Spacer(height=ui.Fraction(2))

        # ## TODO: shouldn't need this if the models are added and removed in a way that triggers _model_changed
        # if self._joint_model:
        self._treeview_empty_page.visible = False

    def _build_tree_view(self):
        with ui.ZStack():
            scrolling_frame = ui.ScrollingFrame(name="treeview", height=self._treeview_initial_height)
            with scrolling_frame:
                if not self._joint_model:
                    self._joint_model = JointsModel([])
                self.__subscription = self._joint_model.subscribe_item_changed_fn(self._model_changed)
                headers = ["Joint Name", "Joint Type", "Axis", "Drive Type", "Parent (Body0)", "Child (Body1)"]
                self._delegate = TreeViewWithPlacerHolderDelegate(
                    headers, [JOINT_TYPES, AXIS_LIST, DRIVE_TYPES], [2, 3, 4], self._joint_model
                )
                with ui.HStack():
                    self.id_column = TreeViewIDColumn()
                    with ui.ZStack():
                        self._tree_view = ui.TreeView(
                            self._joint_model,
                            delegate=self._delegate,
                            root_visible=False,
                            header_visible=True,
                            column_widths=[
                                20,
                                ui.Fraction(1),
                                ui.Fraction(1),
                                55,
                                ui.Fraction(0.8),
                                ui.Fraction(1.2),
                                ui.Fraction(1.2),
                                25,
                            ],
                            selection_changed_fn=self.__selection_changed,
                        )
                        self.treeview_empty_page()
            placer = ui.Placer(drag_axis=ui.Axis.Y, offset_y=self._treeview_initial_height, draggable=True)
            with placer:
                with ui.ZStack(height=4):
                    splitter_highlight = ui.Rectangle(name="splitter_highlight")

            def move(y):
                placer.offset_y = max(20, y.value)
                scrolling_frame.height = y

            placer.set_offset_y_changed_fn(move)

    def add_joint_to_robot(self):
        robot = RobotRegistry().get()
        robot_name = robot.name
        if not robot or self._joint_model._searchable_num == 0:
            return
        for item in self._joint_model.get_item_children(None):
            if isinstance(item, JointItem):
                joint_name = item.name.get_value_as_string()
                joint_path = f"/{robot_name}/Joints/{joint_name}"
                joint_type = item.joint_type.get_value_as_string()
                axis = item.axis.get_value_as_string()
                drive_type = item.drive_type.get_value_as_string()
                parent = item.parent.get_value_as_string()
                child = item.child.get_value_as_string()
                break_force = item.break_force.get_value_as_float()
                break_torque = item.break_torque.get_value_as_float()
                lower_limit = item.lower_limit.get_value_as_float()
                upper_limit = item.upper_limit.get_value_as_float()
                max_force = item.max_force.get_value_as_float()
                target_position = item.target_position.get_value_as_float()
                target_velocity = item.target_velocity.get_value_as_float()
                damping = item.damping.get_value_as_float()
                stiffness = item.stiffness.get_value_as_float()

                articulation_root_path = self._articulation_root_widget.model.get_value_as_string()
                define_joints(joint_path=joint_path, joint_type=joint_type, axis=axis, parent=parent, child=child)

                apply_joint_settings(
                    joint_path=joint_path,
                    break_force=break_force,
                    break_torque=break_torque,
                    lower_limit=lower_limit,
                    upper_limit=upper_limit,
                )

                apply_drive_settings(
                    joint_path=joint_path,
                    drive_type=drive_type,
                    max_force=max_force,
                    target_position=target_position,
                    target_velocity=target_velocity,
                    damping=damping,
                    stiffness=stiffness,
                )

        robot_path = f"/{robot_name}"
        apply_joint_apis(robot_path=robot_path, articulation_root_path=articulation_root_path)


class CreateJointWindow:
    """This is the pop up window of Create/Edit joint"""

    def __init__(self, window_title, model, item=None):
        self._is_edit = window_title == "Edit Joint"
        self._current_joint = item
        self._joint_model = model
        self._window_height = 410
        self._collapsed_height = 340
        self._parent_xform_model = None
        self._child_xform_stack = None
        self._joint_name_widget = None
        self._drive_type_widget = None
        self._joint_type_widget = None
        self._create_button = None
        self._create_close_button = None
        self.__subscription = self._joint_model.subscribe_item_changed_fn(self._model_changed)
        self.joint_types = JOINT_TYPES
        self._select_new_joint_target_window = None
        window_flags = ui.WINDOW_FLAGS_NO_SCROLLBAR | ui.WINDOW_FLAGS_NO_RESIZE
        self._window = ui.Window(window_title, width=600, height=self._collapsed_height, flags=window_flags)
        self._window.frame.set_build_fn(self._rebuild_frame)

    def destroy(self):
        self.__subscription = None
        if self._select_new_joint_target_window:
            self._select_new_joint_target_window.destroy()
        self._select_new_joint_target_window = None
        if self._window:
            self._window.destroy()
        self._window = None

    def _model_changed(self, model, item):
        # when model item changes, we need to update the ui if the window is visible
        if item and self._window.visible:
            self._update_ui(item)

    def _update_ui(self, item):
        # update window from model item data
        self._current_joint = item
        # parent xform
        self._parent_xform_widget.checked = bool(item)
        self._parent_xform_model.set_value(item.parent.get_value_as_string() if item else "Pick Parent Xform")
        # child xform
        self._child_xform_widget.checked = bool(item)
        self._child_xform_model.set_value(item.child.get_value_as_string() if item else "Pick Child Xform")
        # name
        self._joint_name_widget.model.set_value(
            item.name.get_value_as_string() if item else f"Joint{self._joint_model._searchable_num + 1}"
        )
        # axis
        index = AXIS_LIST.index(item.axis.get_value_as_string()) if item else 0
        self._axis_collection.model.set_value(index)
        # joint type
        type_idx = self.joint_types.index(item.joint_type.get_value_as_string()) if item else 0
        self._joint_type_widget.model.get_item_value_model().set_value(type_idx)
        # drive type
        drive_idx = DRIVE_TYPES.index(item.drive_type.get_value_as_string()) if item else 0
        self._drive_type_widget.model.get_item_value_model().set_value(drive_idx)
        # force the frame to update
        self._window.frame.invalidate_raster()

    def _update_item(self):
        # update item from ui
        self._current_joint.set_property("parent", self._parent_xform_model.get_value_as_string())
        self._current_joint.set_property("child", self._child_xform_model.get_value_as_string())
        self._current_joint.set_property("name", self._joint_name_widget.model.get_value_as_string())
        self._current_joint.set_property("axis", AXIS_LIST[self._axis_collection.model.get_value_as_int()])
        self._current_joint.set_property(
            "joint_type", self.joint_types[self._joint_type_widget.model.get_item_value_model().get_value_as_int()]
        )
        self._current_joint.set_property(
            "drive_type", DRIVE_TYPES[self._drive_type_widget.model.get_item_value_model().get_value_as_int()]
        )
        self._joint_model._item_changed(self._current_joint)

    def _on_parent_xform_changed(self, model):
        # only write to model when save is clicked
        if self._is_edit:
            return

        value = model.get_value_as_string()
        checked = value != "Pick Parent Xform"
        self._child_xform_stack.enabled = checked
        # change font style
        self._parent_xform_widget.checked = checked

        if checked:
            idx = self._joint_model._searchable_num + 1
            self._current_joint = JointItem(
                f"Joint{idx}", self.joint_types[0], AXIS_LIST[0], DRIVE_TYPES[0], editable=True
            )
            self._current_joint.set_property("parent", value)
        else:
            self._current_joint = None

    def _on_child_xform_changed(self, model):
        # only write to model when save is clicked
        if self._is_edit:
            return
        value = model.get_value_as_string()
        checked = value != "Pick Child Xform"
        self._joint_name_widget.enabled = checked
        self._axis_widget.enabled = checked
        self._joint_type_widget.enabled = checked
        self._drive_type_widget.enabled = checked
        self._create_button.enabled = checked
        self._create_close_button.enabled = checked
        # change font style
        self._child_xform_widget.checked = checked

        if checked and self._current_joint:
            self._current_joint.set_property("child", value)

    def _switch_xforms(self):
        if self._is_edit:
            return
        if not self._child_xform_stack.enabled:
            return
        parent_value = self._parent_xform_model.get_value_as_string()
        child_value = self._child_xform_model.get_value_as_string()
        self._parent_xform_model.set_value(child_value)
        self._child_xform_model.set_value(parent_value)

    def on_collapsed_changed(self, collapsed):
        if collapsed:
            self._window.height = self._collapsed_height
        else:
            self._window.height = self._window_height

    def _update_name(self, model):
        # only write to model when save is clicked
        if self._is_edit:
            return
        name = model.get_value_as_string()
        if self._current_joint:
            self._current_joint.set_property("name", name)

    def _update_axis(self, model):
        # only write to model when save is clicked
        if self._is_edit:
            return
        value = AXIS_LIST[model.get_value_as_int()]
        if self._current_joint:
            self._current_joint.set_property("axis", value)

    def _update_joint_type(self, model, root_item):
        # only write to model when save is clicked
        if self._is_edit:
            return
        root_model = model.get_item_value_model(root_item)
        value = root_model.get_value_as_int()
        joint_type = self.joint_types[value]
        if joint_type and self._current_joint:
            self._current_joint.set_property("joint_type", joint_type)

    def _update_drive_type(self, model, root_item):
        # only write to model when save is clicked
        if self._is_edit:
            return
        root_model = model.get_item_value_model(root_item)
        value = root_model.get_value_as_int()
        drive_type = DRIVE_TYPES[value]
        # self._current_joint will reset to None in click create, then reset drive_type will cause a error
        if drive_type and self._current_joint:
            self._current_joint.set_property("drive_type", drive_type)

    def _on_create_clicked(self, closed=False):

        self._robot = RobotRegistry().get()

        if not self._robot:
            return

        # if not self._current_joint:
        if not self._current_joint:
            return

        # add the joint to the Robot
        robot_name = self._robot.name
        joint_name = self._current_joint.name.get_value_as_string()
        joint_path = f"/{robot_name}/Joints/{joint_name}"
        joint_type = JOINT_TYPES[self._joint_type_widget.model.get_item_value_model().get_value_as_int()]
        axis = AXIS_LIST[self._axis_collection.model.get_value_as_int()]
        drive_type = DRIVE_TYPES[self._drive_type_widget.model.get_item_value_model().get_value_as_int()]
        define_joints(
            joint_path=joint_path,
            joint_type=joint_type,
            axis=axis,
            parent=self._parent_xform_model.get_value_as_string(),
            child=self._child_xform_model.get_value_as_string(),
        )
        apply_drive_settings(
            joint_path=joint_path,
            drive_type=drive_type,
        )

        if self._current_joint is not None:
            self._update_item()
        else:
            self._current_joint = JointItem(
                name=joint_name,
                joint_type=joint_type,
                axis=axis,
                drive_type=drive_type,
            )
            self._update_item()

        self._joint_model.add_item(self._current_joint)
        # clear the current joint from the pop up window

        if closed:
            self._window.visible = False

        self._update_ui(None)

    def _on_cancel_clicked(self):
        self._window.visible = False
        self._update_ui(None)

    def _on_save_clicked(self):
        if not self._current_joint:
            return

        self._on_create_clicked(True)
        # write to model
        self._update_item()
        self._window.visible = False

    def _rebuild_frame(self):
        with ui.HStack(height=0):
            ui.Spacer(width=10)
            with ui.VStack(style=get_popup_window_style(), spacing=10):
                infos = [
                    "Select 2 rigid bodies, a joint will be created between them.",
                    "To fix a body in place, select parent to be the /World or leave blank.",
                    "Joints can only move on a single axis.",
                    "Joints with Drives are powered and can receive movement commands.",
                    "Unpowered joints move under gravity or inertial forces.",
                ]
                info_frame(infos, self.on_collapsed_changed)
                with ui.HStack(height=66):
                    ui.Image(name="switch", width=26, mouse_pressed_fn=lambda x, y, b, a: self._switch_xforms())
                    ui.Spacer(width=4)
                    with ui.VStack():
                        with ui.HStack(height=18):
                            self._parent_xform_widget = ui.StringField(checked=bool(self._is_edit))
                            self._parent_xform_model = self._parent_xform_widget.model
                            parent_value = (
                                self._current_joint.parent.get_value_as_string()
                                if self._is_edit
                                else "Pick Parent Xform"
                            )
                            self._parent_xform_model.set_value(parent_value)
                            ui.Image(
                                name="sample",
                                height=18,
                                width=25,
                                mouse_pressed_fn=lambda x, y, b, a: self.select_new_joint_target(
                                    self._parent_xform_model, "Select Parent Xform"
                                ),
                            )
                            ui.Spacer(width=5)
                        ui.Spacer()
                        self._child_xform_stack = ui.HStack(height=18, enabled=bool(self._is_edit))
                        with self._child_xform_stack:
                            self._child_xform_widget = ui.StringField(checked=bool(self._is_edit))
                            self._child_xform_model = self._child_xform_widget.model
                            child_value = (
                                self._current_joint.child.get_value_as_string() if self._is_edit else "Pick Child Xform"
                            )
                            self._child_xform_model.set_value(child_value)
                            ui.Image(
                                name="sample",
                                height=18,
                                width=25,
                                mouse_pressed_fn=lambda x, y, b, a: self.select_new_joint_target(
                                    self._child_xform_model, "Select Child Xform"
                                ),
                            )
                            ui.Spacer(width=5)
                        self._parent_xform_model.add_value_changed_fn(self._on_parent_xform_changed)
                        self._child_xform_model.add_value_changed_fn(self._on_child_xform_changed)

                ui.Spacer()
                with ui.HStack(height=18):
                    self._joint_name_widget = ui.StringField(enabled=bool(self._is_edit), checked=True)
                    idx = self._joint_model._searchable_num + 1
                    name_value = self._current_joint.name.get_value_as_string() if self._is_edit else f"Joint{idx}"
                    self._joint_name_widget.model.set_value(name_value)
                    self._joint_name_widget.model.add_value_changed_fn(lambda m: self._update_name(m))
                    ui.Spacer(width=10)
                self._axis_widget = ui.HStack(enabled=bool(self._is_edit), height=30, spacing=4)
                with self._axis_widget:
                    self._axis_collection = ui.RadioCollection()
                    ui.RadioButton(width=18, radio_collection=self._axis_collection)
                    ui.Label("X Axis", width=80)
                    ui.RadioButton(width=18, radio_collection=self._axis_collection)
                    ui.Label("Y Axis", width=80)
                    ui.RadioButton(width=18, radio_collection=self._axis_collection)
                    ui.Label("Z Axis", width=80)
                    if self._is_edit:
                        axis_value = self._current_joint.axis.get_value_as_string()
                        idx = AXIS_LIST.index(axis_value)
                        self._axis_collection.model.set_value(idx)
                    self._axis_collection.model.add_value_changed_fn(lambda m: self._update_axis(m))

                with ui.HStack(height=30):
                    idx = (
                        self.joint_types.index(self._current_joint.joint_type.get_value_as_string())
                        if self._is_edit
                        else 0
                    )
                    ui.Label("Joint Type", width=80, height=20)
                    self._joint_type_widget = ui.ComboBox(idx, *self.joint_types, enabled=bool(self._is_edit))
                    self._joint_type_widget.model.add_item_changed_fn(lambda m, i: self._update_joint_type(m, i))
                    ui.Spacer(width=10)
                with ui.HStack(height=30):
                    ui.Label("Drive Type", width=80, height=20)
                    idx = (
                        DRIVE_TYPES.index(self._current_joint.drive_type.get_value_as_string()) if self._is_edit else 0
                    )
                    self._drive_type_widget = ui.ComboBox(idx, *DRIVE_TYPES, enabled=bool(self._is_edit))
                    self._drive_type_widget.model.add_item_changed_fn(lambda m, i: self._update_drive_type(m, i))
                    ui.Spacer(width=10)
                if not self._is_edit:
                    with ui.HStack(height=22):
                        ui.Spacer()
                        with ui.HStack(width=77):
                            ButtonWithIcon("Cancel", image_width=0, enabled=True, clicked_fn=self._on_cancel_clicked)
                        ui.Spacer(width=14)
                        with ui.HStack(width=77):
                            self._create_button = ButtonWithIcon(
                                "Create", name="add", image_width=12, enabled=False, clicked_fn=self._on_create_clicked
                            )
                        ui.Spacer(width=14)
                        with ui.HStack(width=123):
                            self._create_close_button = ButtonWithIcon(
                                "Create & Close",
                                name="add",
                                image_width=12,
                                enabled=False,
                                clicked_fn=lambda: self._on_create_clicked(True),
                            )
                        ui.Spacer(width=10)
                else:
                    with ui.HStack(height=22):
                        ui.Spacer()
                        with ui.HStack(width=77):
                            ButtonWithIcon("Cancel", image_width=0, enabled=True, clicked_fn=self._on_cancel_clicked)
                        ui.Spacer(width=14)
                        with ui.HStack(width=80):
                            self._create_button = ButtonWithIcon(
                                "Save", name="save", image_width=12, clicked_fn=lambda: self._on_save_clicked()
                            )
                        ui.Spacer(width=10)

    def select(self, model, selected_paths):
        self._select_new_joint_target_window.visible = False
        self._selected_paths = selected_paths
        if self._selected_paths:
            model.set_value(self._selected_paths[0])

    def select_new_joint_target(self, model, title):
        if not self._select_new_joint_target_window:
            stage = omni.usd.get_context().get_stage()
            self._select_new_joint_target_window = RobotAssetPicker(
                title,
                stage,
                # filter_type_list=[UsdGeom.Xform],
                on_targets_selected=partial(self.select, model),
                target_name="Path",
            )
        else:
            self._select_new_joint_target_window.set_on_selected(partial(self.select, model))
        self._select_new_joint_target_window.visible = True
