// Copyright (c) 2018-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <carb/Interface.h>

namespace isaacsim
{
namespace asset
{
namespace gen
{
namespace conveyor
{

/**
 * @brief Interface for the OmniIsaacConveyor plugin.
 *
 * @details This interface provides the core functionality for the conveyor belt plugin.
 * It enables loading the plugin, triggering carbOnPluginStartup() and carbOnPluginShutdown() methods,
 * and allows usage of other Carbonite plugins. This serves as a foundational interface for Kit extensions.
 */
struct IOmniIsaacConveyor
{
    CARB_PLUGIN_INTERFACE("isaacsim::asset::gen::conveyor", 1, 0);
};

} // namespace conveyor
} // namespace gen
} // namespace asset
} // namespace isaacsim
