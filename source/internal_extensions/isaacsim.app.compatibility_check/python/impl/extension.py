# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Extension entry point for the application compatibility check."""

import asyncio

import carb
import omni.ext
import omni.kit.app

from . import compatibility_checker


class Extension(omni.ext.IExt):
    """Extension for running application compatibility checks on startup."""

    def on_startup(self, ext_id):
        """Initialize the extension and run compatibility checks."""
        # extension metadata
        import omni  # FIXME: UnboundLocalError: local variable 'omni' referenced before assignment

        extension_manager = omni.kit.app.get_app().get_extension_manager()
        ext_path = extension_manager.get_extension_path(ext_id)

        # get extension settings
        settings = carb.settings.get_settings()

        gpu_driver = settings.get("/exts/isaacsim.app.compatibility_check/gpu_driver")
        gpu_vram = settings.get("/exts/isaacsim.app.compatibility_check/gpu_vram")

        cpu_cores = settings.get("/exts/isaacsim.app.compatibility_check/cpu_cores")
        ram = settings.get("/exts/isaacsim.app.compatibility_check/ram")
        storage = settings.get("/exts/isaacsim.app.compatibility_check/storage")

        operating_system = settings.get("/exts/isaacsim.app.compatibility_check/operating_system")

        test_kit_app = settings.get("/exts/isaacsim.app.compatibility_check/test_kit_app")
        test_kit_args = settings.get("/exts/isaacsim.app.compatibility_check/test_kit_args")

        checker = compatibility_checker.Checker()

        omni.kit.app.get_app().print_and_log("")
        omni.kit.app.get_app().print_and_log("=============================================")
        omni.kit.app.get_app().print_and_log("")
        omni.kit.app.get_app().print_and_log("NVIDIA GPU(s)")

        checker.check_nvidia_smi({})
        checker.check_driver_version(gpu_driver)
        checker.check_rtx_gpu({})
        checker.check_vram(gpu_vram)

        omni.kit.app.get_app().print_and_log("")
        omni.kit.app.get_app().print_and_log("CPU, RAM and Storage")
        checker.check_cpu(cpu_cores)
        checker.check_cpu_cores(cpu_cores)
        checker.check_cpu_power_governor({})
        checker.check_ram(ram)
        checker.check_storage(storage)

        omni.kit.app.get_app().print_and_log("")
        omni.kit.app.get_app().print_and_log("Others")
        checker.check_operating_system(operating_system)
        checker.check_display()

        omni.kit.app.get_app().print_and_log("")
        omni.kit.app.get_app().print_and_log("=============================================")
        omni.kit.app.get_app().print_and_log("")
        result = "PASSED" if checker.compatibility_check_status else "FAILED"
        omni.kit.app.get_app().print_and_log(f"System checking result: {result}")
        omni.kit.app.get_app().print_and_log("")
        omni.kit.app.get_app().print_and_log("=============================================")
        omni.kit.app.get_app().print_and_log("")

        # window
        self._window = None
        try:
            import omni.ui
        except ImportError as e:
            return
        from . import check_window

        self._window_title = "Compatibility check"
        self._window = check_window.CheckWindow(
            ext_path, self._window_title, checker, test_config={"kit": {"app": test_kit_app, "args": test_kit_args}}
        )
        self._build_task = asyncio.ensure_future(self._build_layout())

    async def _build_layout(self):
        import omni.ui as ui

        await omni.kit.app.get_app().next_update_async()

        window_handle = ui.Workspace.get_window(self._window_title)
        if window_handle is None:
            return

        # setup the docking Space
        main_dockspace = ui.Workspace.get_window("DockSpace")

        window_handle.dock_in(main_dockspace, ui.DockPosition.SAME)
        window_handle.dock_tab_bar_visible = False

        await omni.kit.app.get_app().next_update_async()

    def on_shutdown(self):
        """Clean up resources when the extension shuts down."""
        if self._window:
            self._window.destroy()
            self._window = None
