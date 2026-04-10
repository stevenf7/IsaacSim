# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""HSB Core extension — backend library and plugin lifecycle for Holoscan Sensor Bridge."""

from .bindings import _hsb_core  # noqa: F401
from .extension import HsbCoreExtension  # noqa: F401

__all__ = []
