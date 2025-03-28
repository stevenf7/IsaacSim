// SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#include <carb/BindingsPythonUtils.h>
#include <carb/logging/Log.h>

#include <isaacsim/asset/gen/conveyor/IOmniIsaacConveyor.h>

CARB_BINDINGS("isaacsim.asset.gen.conveyor.python")

namespace
{

PYBIND11_MODULE(_isaacsim_asset_gen_conveyor, m)
{
    using namespace carb;

    m.doc() = R"pbdoc(
        Internal interface that is automatically called when the extension is loaded so that Omnigraph nodes are registered.

        Example:

            # import  isaacsim.asset.gen.conveyor.bindings._isaacsim_asset_gen_conveyor as _isaacsim_asset_gen_conveyor

            # Acquire the interface
            interface = _isaacsim_asset_gen_conveyor.acquire_interface()

            # Use the interface
            # ...

            # Release the interface
            _isaacsim_asset_gen_conveyor.release_interface(interface)
    )pbdoc";

    defineInterfaceClass<isaacsim::asset::gen::conveyor::IOmniIsaacConveyor>(
        m, "IOmniIsaacConveyor", "acquire_interface", "release_interface");
}

} // anonymous namespace
