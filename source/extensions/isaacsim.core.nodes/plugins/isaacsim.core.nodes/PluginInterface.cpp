// SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
#define CARB_EXPORTS

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <carb/Framework.h>
#include <carb/PluginUtils.h>

#include <isaacsim/core/nodes/ICoreNodes.h>
#include <omni/graph/core/ogn/Registration.h>


const struct carb::PluginImplDesc g_kPluginDesc = { "isaacsim.core.nodes", "Isaac Sim Core OmniGraph Nodes", "NVIDIA",
                                                    carb::PluginHotReload::eEnabled, "dev" };

CARB_PLUGIN_IMPL(g_kPluginDesc, isaacsim::core::nodes::CoreNodes)

DECLARE_OGN_NODES()

namespace
{
std::map<uint64_t, void*> g_handleMap;
std::mutex g_handleMutex;
}


uint64_t addHandle(void* handle)
{
    uint64_t handleId = reinterpret_cast<uint64_t>(handle);
    std::lock_guard<std::mutex> guard(g_handleMutex);
    g_handleMap[handleId] = handle;
    return handleId;
}

void* getHandle(const uint64_t handleId)
{
    std::lock_guard<std::mutex> guard(g_handleMutex);
    auto it = g_handleMap.find(handleId);
    if (it == g_handleMap.end())
    {
        return nullptr;
    }
    else
    {
        return it->second;
    }
}

bool removeHandle(const uint64_t handleId)
{
    std::lock_guard<std::mutex> guard(g_handleMutex);
    return g_handleMap.erase(handleId);
}

CARB_EXPORT void carbOnPluginStartup(){ INITIALIZE_OGN_NODES() }

CARB_EXPORT void carbOnPluginShutdown()
{
    RELEASE_OGN_NODES()
}

// carbonite interface for this plugin (may contain multiple compute nodes)
void fillInterface(isaacsim::core::nodes::CoreNodes& iface)
{
    using namespace isaacsim::core::nodes;
    memset(&iface, 0, sizeof(iface));
    iface.addHandle = addHandle;
    iface.getHandle = getHandle;
    iface.removeHandle = removeHandle;
}
