// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

/*
Carbonite SDK API:
  https://docs.omniverse.nvidia.com/kit/docs/carbonite/latest/api/carbonite_api.html
*/

#pragma once

#define CARB_EXPORTS

#include <carb/Defines.h>
#include <carb/Interface.h>
#include <carb/PluginUtils.h>
#include <carb/settings/ISettings.h>

#include <omni/core/IWeakObject.h>
#include <omni/ext/IExt.h>
#include <omni/kit/xr/system/openxr/IOpenXRComponent.h>
#include <omni/kit/xr/system/openxr/IOpenXRExtension.h>

#include <cstdint>
#include <optional>
#include <vector>

namespace isaacsim::xr::openxr
{

struct IOpenxr
{
    CARB_PLUGIN_INTERFACE("isaacsim::xr::openxr::IOpenxr", 1, 0);

    virtual std::optional<std::array<XrHandJointLocationEXT, XR_HAND_JOINT_COUNT_EXT>> locate_hand_joints(
        XrHandEXT hand, std::optional<XrTime> time) noexcept(false) = 0;
};

} // namespace isaacsim
