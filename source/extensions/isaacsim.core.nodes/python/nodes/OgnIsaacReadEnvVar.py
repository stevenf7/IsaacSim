# SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import os

import numpy
import omni


class OgnIsaacReadEnvVar:
    """
    look for environment variable on OS, and return it.
    """

    @staticmethod
    def compute(db) -> bool:

        # Empty input case:
        if len(db.inputs.envVar) == 0:
            db.outputs.value = ""

        else:
            # Get environment variable
            envv = os.getenv(db.inputs.envVar)

            if envv is None:
                db.outputs.value = ""
            else:
                db.outputs.value = envv

        return True
