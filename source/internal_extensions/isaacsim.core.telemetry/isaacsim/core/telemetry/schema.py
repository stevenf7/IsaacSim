# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Common telemetry schema for Isaac Sim extensions.

Loads the baked JSON Schema (draft-07) from ``schemas/isaacsim.telemetry.common.1.0.json``
and exposes it for ``omni.structuredlog.register_schema()``.
The schema contains three events shared across all Isaac Sim extensions:

* **extensionActivated** -- tracks which extensions are enabled/disabled per session.
* **featureUsed** -- tracks commands, menu items, and API calls within extensions.
* **errorOccurred** -- tracks errors with structured category, type, and operation fields.
"""

from __future__ import annotations

import json
from pathlib import Path

COMMON_SCHEMA_NAME = "isaacsim.telemetry.common"
#: Schema name used as the key when registering with `TelemetryManager`.

_SCHEMA_FILE = Path(__file__).parent.parent.parent.parent / "schemas" / "isaacsim.telemetry.common.1.0.json"

with open(_SCHEMA_FILE) as _f:
    ISAACSIM_COMMON_SCHEMA: dict = json.load(_f)
