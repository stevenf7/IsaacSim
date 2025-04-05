# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
from typing import Dict


class OmniStats:
    def get_stats(self) -> Dict:
        scopes_dict = {}
        for scope in self._scopes:
            stats = self._stats_if.get_stats(scope["scopeId"])
            stats_dict = {}
            for x in stats:
                name = x["name"].replace(" - ", "_")
                name = name.replace(" ", "_")
                stats_dict[name] = x["value"]
            scopes_dict[scope["name"]] = stats_dict
        return scopes_dict
