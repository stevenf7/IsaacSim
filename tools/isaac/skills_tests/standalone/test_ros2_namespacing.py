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

"""Standalone tier: isaac-sim-ros2-bridge/multi_robot_namespacing.py.

The namespacing logic is verified headless by stubbing omni.graph.core and
capturing the og.Controller.edit() call. A live-bridge variant is guarded.
"""

from __future__ import annotations

import types

import pytest
from _util import load_module_from_path, skill_path

pytestmark = [pytest.mark.standalone, pytest.mark.ros2]

MOD = skill_path("isaac-sim-ros2-bridge", "scripts", "multi_robot_namespacing.py")


class _Keys:
    CREATE_NODES = "CREATE_NODES"
    SET_VALUES = "SET_VALUES"
    CONNECT = "CONNECT"


def _fake_og():
    calls = []

    class Controller:
        Keys = _Keys

        @staticmethod
        def edit(graph_cfg, spec):
            calls.append((graph_cfg, spec))

    omni = types.ModuleType("omni")
    omni.__path__ = []
    graph = types.ModuleType("omni.graph")
    graph.__path__ = []
    core = types.ModuleType("omni.graph.core")
    core.Controller = Controller
    omni.graph = graph
    graph.core = core
    return {"omni": omni, "omni.graph": graph, "omni.graph.core": core}, calls


@pytest.fixture
def loaded():
    fakes, calls = _fake_og()
    mod = load_module_from_path(MOD, name="multi_robot_ns", fake_modules=fakes)
    return mod, calls


def test_namespacing_logic(loaded):
    mod, calls = loaded
    mod.create_ros2_bridge_for_robot("carter_01", "/World/Carter_01")
    assert len(calls) == 1
    graph_cfg, spec = calls[0]
    assert graph_cfg["graph_path"] == "/ROS2_Bridge_carter_01"

    set_values = dict(spec["SET_VALUES"])
    assert set_values["PublishOdom.inputs:topicName"] == "/carter_01/odom"
    assert set_values["SubscribeTwist.inputs:topicName"] == "/carter_01/cmd_vel"
    assert set_values["PublishOdom.inputs:frameId"] == "carter_01/odom"
    assert set_values["PublishOdom.inputs:childFrameId"] == "carter_01/base_link"
    assert set_values["PublishOdom.inputs:chassisPrim"] == "/World/Carter_01"
    assert set_values["PublishTF.inputs:targetPrims"] == ["/World/Carter_01"]


def test_uses_current_bridge_namespace_not_legacy(loaded):
    mod, calls = loaded
    mod.create_ros2_bridge_for_robot("r2", "/World/R2")
    _, spec = calls[0]
    node_types = dict(spec["CREATE_NODES"])
    for node in ("PublishOdom", "PublishTF", "SubscribeTwist"):
        assert node_types[node].startswith("isaacsim.ros2.bridge."), node_types[node]
        assert "omni.isaac.ros2_bridge" not in node_types[node]


def test_playback_tick_drives_all_nodes(loaded):
    mod, calls = loaded
    mod.create_ros2_bridge_for_robot("r3", "/World/R3")
    _, spec = calls[0]
    sources = {src for src, _ in spec["CONNECT"]}
    targets = {dst for _, dst in spec["CONNECT"]}
    assert sources == {"OnPlaybackTick.outputs:tick"}
    assert targets == {
        "PublishOdom.inputs:execIn",
        "PublishTF.inputs:execIn",
        "SubscribeTwist.inputs:execIn",
    }
