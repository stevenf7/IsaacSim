# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


import omni.ext


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id):
        # Force reload of newer typing extensions provided by this extensions prebundle
        from importlib import reload

        import typing_extensions

        reload(typing_extensions)
        pass

    def on_shutdown(self):
        pass
