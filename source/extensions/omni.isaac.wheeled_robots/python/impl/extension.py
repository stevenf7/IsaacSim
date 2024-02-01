# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

"""
Support required by the Carbonite extension loader
"""
import omni.ext

from ..bindings._omni_isaac_wheeled_robots import acquire_interface, release_interface

# Any class derived from `omni.ext.IExt` in a top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when the extension is enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() will be called.


class Extension(omni.ext.IExt):
    def on_startup(self):
        self.__interface = acquire_interface()
        pass

    def on_shutdown(self):
        release_interface(self.__interface)
        pass
