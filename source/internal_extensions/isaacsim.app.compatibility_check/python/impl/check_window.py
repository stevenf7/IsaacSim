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

"""Window UI for displaying compatibility check results."""

import os
import subprocess
import sys
import threading
from typing import Any, Final

import carb
import omni
import omni.kit.app
import omni.ui as ui

from .compatibility_checker import Checker, Level, Result

GRAY: Final[int] = 0xFF4A4A4A
LIGHT_GRAY: Final[int] = 0xFFA8A8A8
DARK_GRAY: Final[int] = 0xFF363636
GREEN: Final[int] = 0xFF00B976
BLACK: Final[int] = 0xFF000000
BLUE: Final[int] = 0xFFF6A66B
LIGHT_BLUE: Final[int] = 0xFF8A8777
WHITE: Final[int] = ui.color("#FFFFFF")

COLOR_WARNING: Final[int] = ui.color("#FFAF2B")
COLOR_DISABLED: Final[int] = ui.color("#444444")

COLOR_SOPPORTED: Final[int] = ui.color("#26B83A")
COLOR_UNSOPPORTED: Final[int] = ui.color("#B83326")

COLOR_UNMET: Final[int] = ui.color("#B83326")
COLOR_MINIMUM: Final[int] = ui.color("#F08232")
COLOR_GOOD: Final[int] = ui.color("#85C235")
COLOR_IDEAL: Final[int] = ui.color("#26B83A")


WINDOW_STYLE: dict[str, Any] = {}


class CheckWindow:
    """Window for displaying compatibility check results.

    Args:
        ext_path: Path to the extension directory.
        title: Window title.
        checker: Compatibility checker instance.
        test_config: Test configuration dictionary, or None to use an empty configuration.
    """

    def __init__(self, ext_path: str, title: str, checker: Checker, test_config: dict[str, Any] | None = None) -> None:
        self._ext_path = ext_path
        self._title = title
        self._checker = checker
        self._test_config = {} if test_config is None else test_config

        self._window = None
        self._check_list_frame = None
        self._test_output_frame = None

        self._build_window()

    def destroy(self) -> None:
        """Destroy the window and release resources."""
        self._window = None

    def _exit(self) -> None:
        omni.kit.app.get_app().post_quit()

    def _build_window(self) -> None:
        self._window = ui.Window(self._title, padding_x=0, padding_y=0, style={"Window": {"pading": 0}})
        assert self._window is not None
        self._window.frame.set_style(WINDOW_STYLE)
        with self._window.frame:
            with ui.VStack():
                self._build_check_items()
                self._build_test_items()
                self._build_actions()
                self._build_nvidia_status_bar()

    def _widget_single_state(self, label: str, result: Result) -> None:
        with ui.HStack(height=0):
            ui.Label(label, width=125, style={"font_size": 18, "color": 0xFFBBBBBB})
            ui.Spacer(width=15)
            with ui.ZStack(height=20, width=320):
                ui.Rectangle(
                    height=20, style={"background_color": COLOR_SOPPORTED if result.status else COLOR_UNSOPPORTED}
                )
                ui.Label(
                    result.message,
                    alignment=ui.Alignment.CENTER,
                    elided_text=True,
                    style={"font_size": 16, "color": WHITE},
                )

    def _widget_multi_state(self, label: str, result: Result, disable: bool = False) -> None:
        color_by_level = {
            Level.UNMET: COLOR_DISABLED if disable else COLOR_UNMET,
            Level.MINIMUM: COLOR_DISABLED if disable else COLOR_MINIMUM,
            Level.GOOD: COLOR_DISABLED if disable else COLOR_GOOD,
            Level.IDEAL: COLOR_DISABLED if disable else COLOR_IDEAL,
        }
        labels = [""] * 4
        colors: list[str | int] = [""] * 4
        for i in range(4):
            if i <= result.level.value:
                colors[i] = color_by_level[result.level]
            if i == result.level.value:
                labels[i] = result.message

        with ui.HStack(height=0):
            ui.Label(label, width=125, style={"font_size": 18, "color": 0xFFBBBBBB})
            ui.Spacer(width=15)
            for i, (_label, color) in enumerate(zip(labels, colors)):
                if i:
                    ui.Spacer(width=4)
                with ui.ZStack(height=20, width=77):
                    ui.Rectangle(height=20, style={"background_color": color})
                    ui.Label(
                        _label,
                        alignment=ui.Alignment.CENTER,
                        style={"font_size": 16, "color": LIGHT_GRAY if disable else WHITE},
                    )

    # Single bar, multi-state by color
    def _widget_single_level_state(
        self, label: str, result: Result, disable: bool = False, font_size: int = 16
    ) -> None:
        color_by_level = {
            Level.UNMET: COLOR_DISABLED if disable else COLOR_UNMET,
            Level.MINIMUM: COLOR_DISABLED if disable else COLOR_MINIMUM,
            Level.GOOD: COLOR_DISABLED if disable else COLOR_GOOD,
            Level.IDEAL: COLOR_DISABLED if disable else COLOR_IDEAL,
        }
        color = color_by_level[result.level]

        with ui.HStack(height=0):
            ui.Label(label, width=125, style={"font_size": 18, "color": 0xFFBBBBBB})
            ui.Spacer(width=15)
            with ui.ZStack(height=20, width=320):
                ui.Rectangle(height=20, style={"background_color": color})
                ui.Label(
                    result.message,
                    alignment=ui.Alignment.CENTER,
                    elided_text=True,
                    style={"font_size": font_size, "color": WHITE},
                )

    def _build_check_items(self) -> None:
        if not self._check_list_frame:
            self._check_list_frame = ui.ScrollingFrame(
                width=500, height=400, style={"background_color": DARK_GRAY, "padding": 20}
            )
        else:
            self._check_list_frame.clear()

        assert self._check_list_frame is not None
        with self._check_list_frame:
            with ui.VStack():
                # GPU
                ui.Line(height=0, style={"color": GREEN, "border_width": 2})
                ui.Spacer(height=7)
                ui.Label("NVIDIA GPU(s)", alignment=ui.Alignment.CENTER, style={"font_size": 18, "color": WHITE})
                ui.Spacer(height=7)
                # nvidia-smi
                if self._checker.nvidia_smi.status:
                    # driver
                    self._widget_single_state("Driver Version", self._checker.gpu_driver_version)
                    ui.Spacer(height=7)
                    # chip and memory
                    for i, (gpu_rtx, vram) in enumerate(zip(self._checker.gpu_rtx, self._checker.gpu_vram)):
                        if i:
                            ui.Spacer(height=7)
                        self._widget_single_state(f"GPU {i}", gpu_rtx)
                        ui.Spacer(height=7)
                        self._widget_multi_state(f"     VRAM (GB)", vram, disable=not gpu_rtx.status)
                else:
                    ui.Label(
                        "Unable to access GPU(s) configuration:",
                        width=460,
                        word_wrap=True,
                        style={"font_size": 18, "color": 0xFFBBBBBB},
                    )
                    ui.Label(
                        self._checker.nvidia_smi.message,
                        width=460,
                        word_wrap=True,
                        style={"font_size": 18, "color": COLOR_WARNING},
                    )

                # CPU, RAM & Storage
                ui.Line(height=20, style={"color": GREEN, "border_width": 2})
                ui.Label("CPU, RAM & Storage", alignment=ui.Alignment.CENTER, style={"font_size": 18, "color": WHITE})
                ui.Spacer(height=7)
                # processor
                self._widget_single_state("CPU processor", self._checker.cpu)
                ui.Spacer(height=7)
                # cores
                self._widget_multi_state("CPU cores", self._checker.cpu_cores)
                ui.Spacer(height=7)
                # cpu power governor - linux
                self._widget_single_level_state(
                    "CPU governor",
                    self._checker.cpu_power_governor,
                    disable=not self._checker.cpu_power_governor.status,
                )
                ui.Spacer(height=7)
                # memory
                self._widget_multi_state("RAM (GB)", self._checker.ram)
                ui.Spacer(height=7)
                # storage
                self._widget_multi_state("Storage (GB)", self._checker.disk_storage)

                # OS & others
                ui.Line(height=20, style={"color": GREEN, "border_width": 2})
                ui.Label("OS & others", alignment=ui.Alignment.CENTER, style={"font_size": 18, "color": WHITE})
                ui.Spacer(height=7)
                # operating system
                self._widget_single_state("Operating system", self._checker.operating_system)
                ui.Spacer(height=7)
                # display
                self._widget_single_state("Display", self._checker.display)
                ui.Spacer(height=7)

    def _build_test_items(self) -> None:
        enabled = self._resolve_test_config()[0]
        with ui.Frame(style={"padding": 0, "margin_width": 4.5}):
            with ui.VStack():
                ui.Spacer(height=8)
                with ui.HStack():
                    ui.Button(
                        text="Test Kit" + (" (disabled)" if not enabled else ""),
                        width=100 + (75 if not enabled else 0),
                        height=40,
                        style={"font_size": 18, "padding": 5},
                        clicked_fn=lambda: self._test_kit(),
                        enabled=enabled,
                    )
                    self._sub_build_test_output_frame("")
                ui.Spacer(height=8)

    def _sub_build_test_output_frame(self, text: str, color: int = 0xFFBBBBBB) -> None:
        if not self._test_output_frame:
            self._test_output_frame = ui.Frame()
        else:
            self._test_output_frame.clear()

        assert self._test_output_frame is not None
        with self._test_output_frame:
            with ui.VStack():
                ui.Label(
                    text,
                    width=362,
                    height=40,
                    alignment=ui.Alignment.LEFT_CENTER,
                    word_wrap=True,
                    style={"font_size": 14, "color": color},
                )

    def _build_actions(self) -> None:
        with ui.Frame(style={"padding": 0}):
            with ui.ZStack():
                ui.Rectangle(height=51, style={"background_color": ui.color("#666666")})
                with ui.VStack(width=0):
                    ui.Spacer(height=6)
                    with ui.HStack():
                        ui.Spacer(width=250)
                        ui.Button(
                            text="CLOSE",
                            width=234,
                            height=40,
                            style={
                                "font_size": 18,
                                "padding": 5,
                                "color": ui.color("#333333"),
                                "background_color": ui.color("#AAAAAA"),
                            },
                            clicked_fn=lambda: self._exit(),
                        )

    def _build_nvidia_status_bar(self) -> None:
        with ui.ZStack(height=30):
            ui.Rectangle(style={"background_color": 0xFF000000})
            with ui.HStack():
                ui.Spacer()
                with ui.VStack(width=0):
                    ui.Spacer()
                    ui.Image(f"{self._ext_path}/data/app/NVIDIA.png", height=18, width=150)
                    ui.Spacer()

    def _test_kit(self) -> None:
        def _execute(cmd: list[str], app: str) -> None:
            try:
                output = subprocess.check_output(cmd, shell=False).decode().strip()
            except subprocess.CalledProcessError as e:
                self._sub_build_test_output_frame(
                    f"{app} has ended with error ({e.returncode}): {e.output}", color=COLOR_WARNING
                )
                return
            # get logging path
            logging_file = output.split("\n")[1]
            logging_header = "[Info] [carb] Logging to file: "
            if logging_header in logging_file:
                logging_file = logging_file[len(logging_header) :]
                omni.kit.app.get_app().print_and_log(logging_file)
                logging_file = f".\nFull log: {logging_file}"
            else:
                logging_file = ""
            # check if app started correctly
            app_started = ""
            if " app ready" in output:
                app_started = "Kit app started correctly. "
            self._sub_build_test_output_frame(f"{app_started}Test execution completed{logging_file}")

        # resolve test config
        is_valid, (test_script_path, test_script, test_args) = self._resolve_test_config()
        if not is_valid:
            self._sub_build_test_output_frame(f"Test cannot run: {test_script} not found", color=COLOR_WARNING)
            return
        # execute test
        cmd = [test_script_path] + test_args
        threading.Thread(target=_execute, args=(cmd, test_script)).start()
        # show execution message
        self._sub_build_test_output_frame(f"Running: {' '.join([test_script] + test_args)}")

    def _resolve_test_config(self) -> tuple[bool, tuple[str, str, list[str]]]:
        # get app folder
        app_folder = carb.settings.get_settings().get_as_string("/app/folder")
        if not app_folder:
            app_folder = carb.tokens.get_tokens_interface().resolve("${app}")
        app_folder = os.path.normpath(os.path.join(app_folder, os.pardir))
        # get testing script
        test_script = self._test_config.get("kit", {}).get("app", "") + (
            ".sh" if sys.platform.startswith("linux") else ".bat"
        )
        test_args = self._test_config.get("kit", {}).get("args", [])
        test_script_path = os.path.join(app_folder, "kit", test_script)
        return os.path.isfile(test_script_path), (test_script_path, test_script, test_args)
