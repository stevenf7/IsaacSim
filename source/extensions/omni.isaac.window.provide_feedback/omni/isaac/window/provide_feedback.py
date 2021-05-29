import omni.ext
import webbrowser


class Extension(omni.ext.IExt):
    def on_startup(self):
        import omni.kit.ui

        def provide_feedback_func(a, b):
            webbrowser.open("https://forums.developer.nvidia.com/c/omniverse/apps/create/405")

        self._menuEntry = omni.kit.ui.get_editor_menu().add_item("Help/Provide Feedback", provide_feedback_func)
        omni.kit.ui.get_editor_menu().set_priority("Help/Provide Feedback", -11)
