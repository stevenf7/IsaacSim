import omni.ui as ui
from omni.isaac.ui.ui_utils import get_style


class UIFrameWrapper:
    """
    Wraps omni.ui.frame in order to allow the user to create a UI Frame in a less verbose way
    This class may also be used as the parent class for Frames with added functionality
    """

    def __init__(self, title: str, collapsed: bool = True, enabled: bool = True, visible: bool = True):
        # Create a Frame UI element
        self.frame = self._create_frame(title, collapsed, enabled, visible)

    @property
    def collapsed(self) -> bool:
        return self.frame.collapsed

    @collapsed.setter
    def collapsed(self, value: bool):
        self.frame.collapsed = value

    @property
    def enabled(self) -> bool:
        return self.frame.enabled

    @enabled.setter
    def enabled(self, value: bool):
        self.frame.enabled = value

    @property
    def visible(self) -> bool:
        return self.frame.visible

    @visible.setter
    def visible(self, value: bool):
        self.frame.visible = value

    def get_frame(self) -> ui.CollapsableFrame:
        return self.frame

    def _create_frame(self, title: str, collapsed: bool, enabled: bool, visible: bool) -> ui.CollapsableFrame:
        frame = ui.CollapsableFrame(
            title=title,
            name=title,
            height=0,
            collapsed=collapsed,
            visible=visible,
            enabled=enabled,
            style=get_style(),
            style_type_name_override="CollapsableFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )

        return frame


class UIWidgetWrapper:
    """
    Base class for creating wrappers around any subclass of omni.ui.Widget in order to provide an easy interface
    for creating and managing specific types of widgets such as state buttons or file pickers.
    """

    def __init__(self, ui_element: ui.Widget):
        self.ui_element = ui_element

    @property
    def enabled(self) -> bool:
        return self.ui_element.enabled

    @enabled.setter
    def enabled(self, value: bool):
        self.ui_element.enabled = value

    @property
    def visible(self) -> bool:
        return self.ui_element.visible

    @visible.setter
    def visible(self, value: bool):
        self.ui_element.visible = value

    def cleanup(self):
        """
		Perform any necessary cleanup
		"""
        pass

    def get_ui_element(self) -> ui.Widget:
        """Return the UI element being wrapped

		Returns:
			omni.ui.Widget: An instance of omni.ui.Widget
		"""
        return self.ui_element
