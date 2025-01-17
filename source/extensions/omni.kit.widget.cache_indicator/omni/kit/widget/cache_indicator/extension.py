# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import omni.ext
import omni.kit.app

from .cache_state_menu import CacheStateMenu
from .icons import Icons
from .style import Styles


class OmniCacheIndicatorWidgetExtension(omni.ext.IExt):
    def __init__(self):
        super().__init__()

    def on_startup(self, ext_id):
        extension_path = omni.kit.app.get_app_interface().get_extension_manager().get_extension_path(ext_id)
        Icons.on_startup(extension_path)
        Styles.on_startup()

        self._cache_state_menu = CacheStateMenu()
        self._cache_state_menu.register_menu_widgets()

    def on_shutdown(self):
        self._cache_state_menu.unregister_menu_widgets()
        Icons.on_shutdown()
