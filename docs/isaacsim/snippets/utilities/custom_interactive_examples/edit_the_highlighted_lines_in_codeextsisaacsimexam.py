import os

import omni.ext
from isaacsim.examples.interactive.base_sample import BaseSampleUITemplate
from isaacsim.examples.interactive.user_examples import HelloWorld


class HelloWorldExtension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self.example_name = "Awesome Example"
        self.category = "MyExamples"

        ui_kwargs = {
            "ext_id": ext_id,
            "file_path": os.path.abspath(__file__),
            "title": "My Awesome Example",
            "doc_link": "https://docs.omniverse.nvidia.com/isaacsim/latest/core_api_tutorials/tutorial_core_hello_world.html",
            "overview": "This Example introduces the user on how to do cool stuff with Isaac Sim through scripting in asynchronous mode.",
            "sample": HelloWorld(),
        }

        ui_handle = BaseSampleUITemplate(**ui_kwargs)

        # register the example with examples browser
        get_browser_instance().register_example(
            name=self.example_name,
            execute_entrypoint=ui_handle.build_window,
            ui_hook=ui_handle.build_ui,
            category=self.category,
        )

    return
