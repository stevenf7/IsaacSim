// Copyright (c) 2020-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/BindingsPythonUtils.h>
#include <carb/logging/Log.h>

#include <isaacsim/asset/gen/conveyor/IOmniIsaacConveyor.h>

CARB_BINDINGS("isaacsim.asset.gen.conveyor.python")

namespace
{

PYBIND11_MODULE(_isaacsim_asset_gen_conveyor, m)
{
    using namespace carb;

    m.doc() = "pybind11 isaacsim.asset.gen.conveyor bindings";

    defineInterfaceClass<isaacsim::asset::gen::conveyor::IOmniIsaacConveyor>(
        m, "IOmniIsaacConveyor", "acquire_interface", "release_interface");
}

} // anonymous namespace
