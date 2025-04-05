# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import numpy as np


class OgnCountIndices:
    @staticmethod
    def compute(db) -> bool:
        indices = np.array(db.inputs.indices)

        # WAR because omni.replicator.core.distributions don't accept num_samples=0
        if len(indices) != 0:
            db.outputs.count = len(indices)
        else:
            db.outputs.count = 1

        return True
