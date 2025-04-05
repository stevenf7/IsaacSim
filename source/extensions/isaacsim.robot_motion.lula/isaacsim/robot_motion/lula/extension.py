# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


import os
import pathlib

import omni.ext

# Work around a (not understood) issue on Windows where the lula python extension module (pyd file)
# is loaded properly but the DLLs on which it depends are not, despite being in the same directory.
if os.name == "nt":
    file_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
    lula_dir = file_dir.joinpath(pathlib.Path("../../../pip_prebundle")).resolve()
    os.add_dll_directory(lula_dir.__str__())


from lula import LogLevel, set_default_logger_prefix, set_log_level


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id):
        set_log_level(LogLevel.WARNING)
        set_default_logger_prefix("[Lula] ")

    def on_shutdown(self):
        pass
