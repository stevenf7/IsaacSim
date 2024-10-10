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

#include <cstdint>

namespace isaacsim
{
namespace xr
{
namespace openxr
{

// ------------------
// custom API declaration. E.g.:
CARB_EXPORT void setDefaultStatus(const char* status);
// ------------------

/**
 * Carbonite interface
 */
struct IOpenxr
{
    CARB_PLUGIN_INTERFACE("isaacsim::xr::openxr::IOpenxr", 1, 0);

    // ------------------
    // custom API declaration. E.g.:
    virtual bool registerObject(uint32_t id) = 0;
    // ------------------
};

} // namespace isaacsim
} // namespace xr
} // namespace openxr
