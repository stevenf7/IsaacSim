// Copyright (c) 2018-2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <carb/Interface.h>

namespace omni
{
namespace isaac
{
namespace conveyor
{

/**
 * Minimal interface.
 *
 * It doesn't have any functions, but just implementing it and acquiring will load your plugin, trigger call of
 * carbOnPluginStartup() and carbOnPluginShutdown() methods and allow you to use other Carbonite plugins. That by itself
 * can get you quite far and useful as basic building block for Kit extensions. One can define their own interface with
 * own python python bindings when needed and abandon that one.
 */
struct IOmniIsaacConveyor
{
    CARB_PLUGIN_INTERFACE("omni::isaac::conveyor", 1, 0);
};
}
}
}
