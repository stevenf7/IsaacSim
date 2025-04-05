# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""This module provides the Selection class to encapsulate selection details, including a description and a timestamp."""

__all__ = ["Selection"]

import time


class Selection:
    """A class that encapsulates a selection with a description.

    This class holds the details of a selection, including a timestamp of when the selection was created or modified. It provides the ability to update the timestamp to the current time.

    Args:
        description (str): A brief description of the selection.
        selection: The actual content of the selection."""

    def __init__(self, description, selection):
        """Initialize a new Selection instance with the given description and selection data."""
        self.time = time.monotonic()
        self.description = description
        self.selection = selection

    def touch(self):
        """Updates the timestamp of the selection to the current time."""
        self.time = time.monotonic()
