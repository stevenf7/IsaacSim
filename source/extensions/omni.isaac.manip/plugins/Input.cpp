// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define CARB_EXPORTS

#include "GamePadBinding.h"

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/input/IInput.h>

#include <omni/isaac/manip/Input.h>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.manip.plugin", "ManipInput", "NVIDIA",
                                                  carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::manip::Input)
CARB_PLUGIN_IMPL_DEPS(carb::input::IInput)

namespace omni
{
namespace isaac
{
namespace manip
{

// privates
namespace
{

} // end of anonymous namespace

//
// Plugin stuff
//

static GamePadBinding* s_gamePadBinding = nullptr;

CARB_EXPORT void carbOnPluginStartup()
{
    if (s_gamePadBinding == nullptr)
        s_gamePadBinding = new GamePadBinding;

    CARB_ASSERT(s_gamePadBinding != nullptr);
}

CARB_EXPORT void carbOnPluginShutdown()
{
    if (s_gamePadBinding)
    {
        delete s_gamePadBinding;
        s_gamePadBinding = nullptr;
    }
}

// Input interface
void bind_gamepad(GamepadEventFn eventFn, void* userData)
{
    if (s_gamePadBinding)
        s_gamePadBinding->bind(eventFn, userData);
}

void unbind_gamepad()
{
    if (s_gamePadBinding)
        s_gamePadBinding->unbind();
}

}
}
}

void fillInterface(omni::isaac::manip::Input& iface)
{
    iface = {
        omni::isaac::manip::bind_gamepad,
        omni::isaac::manip::unbind_gamepad,
    };
}
