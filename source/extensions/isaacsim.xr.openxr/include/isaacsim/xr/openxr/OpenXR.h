// Copyright (c) 2024-2025, NVIDIA CORPORATION. All rights reserved.
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

/**
 * @brief Interface for OpenXR hand tracking functionality
 * @details Provides access to OpenXR hand tracking features, allowing applications
 *          to retrieve hand joint locations for VR/AR applications
 */
struct IOpenxr
{
    CARB_PLUGIN_INTERFACE("isaacsim::xr::openxr::IOpenxr", 1, 0);

    /**
     * @brief Retrieves the locations of hand joints
     * @details Gets the positions and orientations of all joints in a specified hand
     *          at a given time, optionally transforming to stage space coordinates
     *
     * @param[in] hand The hand to get joint locations for (left or right)
     * @param[in] time Optional timestamp for the joint locations
     * @param[in] stageAxis if true,axis/units will respect USD stage conventions
     * @return Array of joint locations if successful, empty optional if not
     * @throws May throw exceptions if hand tracking fails
     */
    virtual std::optional<std::array<XrHandJointLocationEXT, XR_HAND_JOINT_COUNT_EXT>> locate_hand_joints(
        XrHandEXT hand, std::optional<XrTime> time, bool stageAxis) noexcept(false) = 0;
};

} // namespace isaacsim
