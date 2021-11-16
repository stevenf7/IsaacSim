# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.ext
import carb


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id):
        try:
            import lula
        except ImportError:
            carb.log_info("lula not found. attempting to install...")
            omni.kit.pipapi.install(
                "nvidia_lula_no_cuda", version="0.7.0", extra_args=["--no-dependencies"], ignore_import_check=True
            )
        pass

    def on_shutdown(self):
        pass
