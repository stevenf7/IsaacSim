# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import os
import sys

if sys.platform == "win32":
    pass
else:
    # Get executable path from command line argument if provided
    executable_path = sys.argv[1] if len(sys.argv) > 1 else None

    icon_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "omni.isaac.sim.png")
    user_apps_folder = os.path.expanduser("~/.local/share/applications")
    icon_file_path = os.path.join(user_apps_folder, "IsaacSim.desktop")
    if os.path.exists(user_apps_folder):
        with open(icon_file_path, "w") as file:
            print(f"Writing Isaac Sim icon file to {icon_file_path}")

            # Build desktop entry content
            desktop_content = f"""[Desktop Entry]
Version=1.0
Name=Isaac Sim
Icon={icon_path}
Terminal=false
Type=Application
StartupWMClass=IsaacSim"""

            # Add Exec field if executable path is provided
            if executable_path and os.path.exists(executable_path):
                desktop_content += f"\nExec={executable_path}"
                print(f"Added Exec field: {executable_path}")
            else:
                if executable_path:
                    print(f"Warning: Executable path not found: {executable_path}")
                else:
                    print("No executable path provided")

            file.write(desktop_content)
