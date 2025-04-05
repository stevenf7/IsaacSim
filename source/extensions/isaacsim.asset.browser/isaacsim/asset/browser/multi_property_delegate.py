# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

from typing import List, Optional

import omni.ui as ui
from omni.kit.browser.folder.core import BrowserPropertyDelegate, FileDetailItem


class MultiPropertyDelegate(BrowserPropertyDelegate):
    """
    A delegate to show when multiple items are selected.
    """

    def accepted(self, items: List[FileDetailItem]) -> bool:
        """BrowserPropertyDelegate method override"""
        return len(items) > 1

    def build_widgets(self, items: List[FileDetailItem]) -> None:
        """BrowserPropertyDelegate method override"""
        label_text = f"Multiple Isaac Assets Selected [{len(items)}]"
        ui.Label(label_text, alignment=ui.Alignment.CENTER)
