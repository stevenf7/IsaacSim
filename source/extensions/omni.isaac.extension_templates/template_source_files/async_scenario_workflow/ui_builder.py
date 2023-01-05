from omni.isaac.ui.widgets import DynamicComboBoxModel
from omni.isaac.ui.ui_utils import (
    add_line_rect_flourish,
    btn_builder,
    state_btn_builder,
    float_builder,
    int_builder,
    xyz_builder,
    color_picker_builder,
    setup_ui_headers,
    get_style,
    str_builder,
)
import omni.ui as ui
import omni.timeline

from omni.kit.window.property.templates import LABEL_WIDTH

from .ui_helper_functions import build_combobox, get_all_articulations, modify_combobox_items
from .scenario import Scenario
from omni.isaac.core.articulations import Articulation


class UIBuilder:
    def __init__(self):
        # All UI elements correspond to a model to access their values and create callback functions
        # See https://docs.omniverse.nvidia.com/kit/docs/omni.ui/2.12.10/omni.ui/omni.ui.AbstractValueModel.html
        self.models = {}

        # Comboboxes are UI elements with drop-down menus
        self.comboboxes = {}

        # Frames are sub-windows that can contain multiple UI elements
        self.frames = {}

        self._on_init()

    def on_menu_callback(self):
        """Callback for when this extension is opened
        """
        pass

    def on_timeline_event(self, event):
        """Callback for Timeline events (Play, Pause, Stop)

        Args:
            event (omni.timeline.TimelineEventType): Event Type
        """

        if event.type == int(omni.timeline.TimelineEventType.PLAY):
            pass
        elif event.type == int(omni.timeline.TimelineEventType.STOP):
            self._on_stop_event()

    def on_physics_step(self, step):
        """Callback for Physics Step.
        Physics steps only occur when the timeline is playing
           
        Args:
            step (float): Size of physics step
        """
        self._on_physics_step(step)

    def on_stage_event(self, event):
        """Callback for Stage Events

        Args:
            event (omni.usd.StageEventType): Event Type
        """

        # On every stage event check if any articulations have been added/removed from the Stage
        self._refresh_articulation_combobox()

    def build_ui(self):
        """
        Build a custom UI tool to run your extension
        """
        self._build_selection_panel()
        self._build_scenario_panel()

    #############################################################################
    # Functions Below This Point Support The Provided Example And Can Be Deleted
    #############################################################################

    def _on_init(self):
        self._running_scenario = False
        self._articulation = None
        self._articulation_list = ["None"]
        self._scenario = Scenario()

    def _build_selection_panel(self):
        """
        Build a combobox that allows the user to select an existing robot Articulation from the stage
        """
        frame = ui.CollapsableFrame(
            title="Selection Panel",
            height=0,
            collapsed=False,
            style=get_style(),
            style_type_name_override="CollapsableFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )
        self.frames["SelectionPanel"] = frame

        with frame:
            with ui.VStack(style=get_style(), spacing=5, height=0):

                # Create a dynamic ComboBox for Articulation Selection
                combobox = build_combobox("Select Articulation", self._articulation_list)
                combobox.model.add_item_changed_fn(self._on_combobox_selection)
                self.comboboxes["SelectArticulation"] = combobox

    def _build_scenario_panel(self):
        frame = ui.CollapsableFrame(
            title="Scenario Panel",
            height=0,
            collapsed=True,
            style=get_style(),
            style_type_name_override="CollapsableFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )
        self.frames["ScenarioPanel"] = frame

        with frame:
            with ui.VStack(style=get_style(), spacing=5, height=0):
                # Create a menu to run a simple scenario with the selected robot

                def _on_run_scenario(model=None):
                    self._running_scenario = not self._running_scenario
                    if self._running_scenario:
                        self._scenario.setup_scenario(self._articulation)
                    else:
                        self._scenario.teardown_scenario()

                self._running_scenario = False
                run_scenario_btn = state_btn_builder(
                    label="Run Scenario",
                    a_text="Run Scenario",
                    b_text="Stop Scenario",
                    tooltip="Run an example scenario",
                    on_clicked_fn=_on_run_scenario,
                )
                self._run_btn = run_scenario_btn

    def _on_physics_step(self, step):
        self._scenario.update_scenario(step)

    def _on_stop_event(self):
        # Reset any changes

        self._scenario.teardown_scenario()
        # TODO: Figure out if state_btn can be reset

    def _on_combobox_selection(self, model, val):
        # Callback for when an Articulation is Selected
        index = model.get_item_value_model().get_value_as_int()
        selected_articulation_prim_path = self._articulation_list[index]
        self._articulation = Articulation(selected_articulation_prim_path)
        self._articulation.initialize()

    def _refresh_articulation_combobox(self):
        # Repopulate the Articulation Combobox with the current list of Articulations on the Stage

        self._articulation_list = get_all_articulations()
        # TODO: Investigate why Articulations can't be found on stopped stage

        # Check if the currently selected Articulation in the new list of available Articulations
        if self._articulation is not None and self._articulation.prim_path in self._articulation_list:
            selected_index = int(self._articulation_list.index(self._articulation.prim_path))
        else:
            selected_index = 0
            self._articulation = None

        modify_combobox_items(
            self.comboboxes["SelectArticulation"],
            self._articulation_list,
            item_changed_fn=self._on_combobox_selection,
            select_index=selected_index,
        )
