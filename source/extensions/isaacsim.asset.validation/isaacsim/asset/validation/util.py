# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Utility functions for asset validation."""


def is_relationship_prepended(relationship: object) -> bool:
    """Check if a relationship is prepended in the layer stack.

    Examines the property stack of the relationship to determine if it uses
    prepended items rather than explicit items in the target path list.

    Args:
        relationship: The USD relationship to check.

    Returns:
        True if the relationship is prepended, False if it uses explicit items.
    """
    rel_stack = relationship.GetPropertyStack()
    return all(not spec.targetPathList.isExplicit for spec in rel_stack)


def make_relationship_prepended(relationship: object) -> bool:
    """Convert a relationship to use prepended items in the layer stack.

    Modifies the relationship's property specs to use prepended items instead of
    explicit items, which allows for composition with stronger layers.

    Args:
        relationship: The USD relationship to convert.

    Returns:
        True if the operation was successful.
    """
    rel_stack = relationship.GetPropertyStack()
    for spec in rel_stack:
        if spec.targetPathList.isExplicit:
            items = list(spec.targetPathList.explicitItems)
            spec.targetPathList.prependedItems = items
            spec.targetPathList.explicitItems = []
    return True
