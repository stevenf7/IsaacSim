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

"""Register transformer rules with the global registry."""

import logging

try:
    import omni.ext

    _ExtBase = omni.ext.IExt
except ImportError:

    class _ExtBase:
        def on_startup(self, ext_id: str) -> None: ...
        def on_shutdown(self) -> None: ...


from isaacsim.asset.transformer import RuleRegistry

from .core.prims import PrimRoutingRule
from .core.properties import PropertyRoutingRule
from .core.remove_schema import RemoveSchemaRule
from .core.schemas import SchemaRoutingRule
from .isaac_sim.make_lists_non_explicit import MakeListsNonExplicitRule
from .isaac_sim.physics_joint_pose_fix import PhysicsJointPoseFixRule
from .isaac_sim.robot_schema import RobotSchemaRule
from .perf.geometries import GeometriesRoutingRule
from .perf.materials import MaterialsRoutingRule
from .structure.flatten import FlattenRule
from .structure.interface import InterfaceConnectionRule
from .structure.variants import VariantRoutingRule

logger = logging.getLogger(__name__)

_ALL_RULES = [
    FlattenRule,
    GeometriesRoutingRule,
    MaterialsRoutingRule,
    PhysicsJointPoseFixRule,
    MakeListsNonExplicitRule,
    RemoveSchemaRule,
    PrimRoutingRule,
    SchemaRoutingRule,
    PropertyRoutingRule,
    VariantRoutingRule,
    RobotSchemaRule,
    InterfaceConnectionRule,
]


def register_all_rules() -> None:
    """Register all built-in rule implementations with the global :class:`RuleRegistry`.

    This is called automatically by the Kit extension on startup. Standalone
    callers (outside Kit) should invoke this once before running the asset
    transformer pipeline.
    """
    registry = RuleRegistry()
    for rule_cls in _ALL_RULES:
        registry.register(rule_cls)
    logger.info("[isaacsim.asset.transformer.rules] Rules registered")


class Extension(_ExtBase):
    """Extension that registers transformation rules."""

    def on_startup(self, ext_id: str) -> None:
        """Register rule implementations with the global registry.

        Args:
            ext_id: Fully qualified extension identifier.

        """
        self._ext_id = ext_id
        logger.info(f"[isaacsim.asset.transformer.rules] Startup: {ext_id}")
        register_all_rules()

    def on_shutdown(self) -> None:
        """Log shutdown for the rules extension."""
        logger.info(f"[isaacsim.asset.transformer.rules] Shutdown: {getattr(self, '_ext_id', '')}")
