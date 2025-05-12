from typing import Callable, List, Optional, Tuple, Union

import numpy as np
import omni.ui as ui
from isaacsim.gui.components.element_wrappers import DropDown, Frame
from isaacsim.gui.components.widgets import DynamicComboBoxModel

LABEL_WIDTH = 90


class CustomDropDown(DropDown):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _create_ui_widget(self, label, tooltip):
        items = []
        combobox_model = DynamicComboBoxModel(items)
        containing_frame = Frame().frame
        with containing_frame:
            with ui.HStack():
                self._label = ui.Label(
                    label, name="dropdown_label", width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER, tooltip=tooltip
                )
                self._combobox = ui.ComboBox(combobox_model)

        return containing_frame
