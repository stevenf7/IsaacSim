// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include "UsdPCH.h"
// clang-format on

#include "GamePadBinding.h"

#include <carb/Framework.h>
#include <carb/input/IInput.h>
#include <carb/settings/ISettings.h>

#include <omni/isaac/manip/Input.h>
#include <omni/kit/IAppWindow.h>

#include <stdio.h>

using namespace pxr;

namespace omni
{
namespace isaac
{
namespace manip
{

// GamePadBinding methods
GamePadBinding::GamePadBinding() : m_gamepadConnectionEventId(0), m_gamepad(nullptr), m_gamepadEventFn(nullptr)
{
}

GamePadBinding::~GamePadBinding()
{
    carb::input::IInput* input = carb::getFramework()->acquireInterface<carb::input::IInput>();

    input->unsubscribeToGamepadConnectionEvents(m_gamepadConnectionEventId);

    auto mappings = m_actionEventGamepadMappings.find(m_gamepad);
    if (mappings != m_actionEventGamepadMappings.end())
        for (auto& entry : mappings->second)
            input->unsubscribeToActionEvents(entry.second);
}

void GamePadBinding::bind(GamepadEventFn eventFn, void* userData)
{
    if (m_gamepadConnectionEventId != 0)
        return;

    carb::input::IInput* input = carb::getFramework()->acquireInterface<carb::input::IInput>();
    m_gamepadConnectionEventId = input->subscribeToGamepadConnectionEvents(
        [](const carb::input::GamepadConnectionEvent& evt, void* userData)
        {
            GamePadBinding* binding = reinterpret_cast<GamePadBinding*>(userData);
            binding->onGamepadConnectionEvent(evt);
        },
        this);

    m_gamepadEventFn = eventFn;
    m_userData = userData;
}

void GamePadBinding::unbind()
{
    unBindGamepad(m_gamepad);
}

void GamePadBinding::onGamepadConnectionEvent(const carb::input::GamepadConnectionEvent& evt)
{
    if (m_gamepad != nullptr)
        return;

    // Setup gamepad control
    if (evt.type == carb::input::GamepadConnectionEventType::eConnected)
    {
        m_gamepad = evt.gamepad;
        subscribOnGamepadAction<eLeftStickX, -1>(
            evt.gamepad, "GamePadLeftStickLeft", carb::input::GamepadInput::eLeftStickLeft);
        subscribOnGamepadAction<eLeftStickX, 1>(
            evt.gamepad, "GamePadLeftStickRight", carb::input::GamepadInput::eLeftStickRight);
        subscribOnGamepadAction<eLeftStickY, -1>(
            evt.gamepad, "GamePadLeftStickDown", carb::input::GamepadInput::eLeftStickDown);
        subscribOnGamepadAction<eLeftStickY, 1>(
            evt.gamepad, "GamePadLeftStickUp", carb::input::GamepadInput::eLeftStickUp);

        subscribOnGamepadAction<eRightStickX, -1>(
            evt.gamepad, "GamePadRightStickLeft", carb::input::GamepadInput::eRightStickLeft);
        subscribOnGamepadAction<eRightStickX, 1>(
            evt.gamepad, "GamePadRightStickRight", carb::input::GamepadInput::eRightStickRight);
        subscribOnGamepadAction<eRightStickY, -1>(
            evt.gamepad, "GamePadRightStickDown", carb::input::GamepadInput::eRightStickDown);
        subscribOnGamepadAction<eRightStickY, 1>(
            evt.gamepad, "GamePadRightStickUp", carb::input::GamepadInput::eRightStickUp);

        subscribOnGamepadAction<eLeftTrigger, 1>(
            evt.gamepad, "GamePadLeftTrigger", carb::input::GamepadInput::eLeftTrigger);
        subscribOnGamepadAction<eRightTrigger, 1>(
            evt.gamepad, "GamePadRightTrigger", carb::input::GamepadInput::eRightTrigger);
    }
    else if (evt.type == carb::input::GamepadConnectionEventType::eDisconnected)
    {
        unBindGamepad(evt.gamepad);
    }
}

template <int axis, int sign>
void GamePadBinding::subscribOnGamepadAction(carb::input::Gamepad* gamepad,
                                             const char* action,
                                             const carb::input::GamepadInput gamepadInput)
{
    carb::input::IInput* input = carb::getFramework()->acquireInterface<carb::input::IInput>();
    omni::kit::IAppWindow* appWindow = omni::kit::getDefaultAppWindow();
    carb::input::ActionMappingSet* actionMappingSet =
        input->getActionMappingSetByPath(appWindow->getActionMappingSetPath());
    input->clearActionMappings(actionMappingSet, action);
    carb::input::SubscriptionId subId =
        input->subscribeToActionEvents(actionMappingSet, action,
                                       [](const carb::input::ActionEvent& evt, void* userData)
                                       {
                                           GamePadBinding* binding = reinterpret_cast<GamePadBinding*>(userData);
                                           const float value = binding->m_value[axis].set(sign > 0, evt.value);
                                           if (binding->m_gamepadEventFn != nullptr)
                                           {
                                               binding->m_gamepadEventFn(axis, value, binding->m_userData);
                                           }
                                           return false;
                                       },
                                       this);

    CARB_ASSERT(m_actionEventGamepadMappings[gamepad].find(action) == m_actionEventGamepadMappings[gamepad].end());
    m_actionEventGamepadMappings[gamepad][action] = subId;

    carb::input::ActionMappingDesc actionPadDesc{};
    actionPadDesc.deviceType = carb::input::DeviceType::eGamepad;
    actionPadDesc.gamepad = gamepad;
    actionPadDesc.gamepadInput = gamepadInput;

    input->addActionMapping(actionMappingSet, action, actionPadDesc);
}

void GamePadBinding::unBindGamepad(carb::input::Gamepad* gamepad)
{
    if (gamepad != m_gamepad)
        return;

    carb::input::IInput* input = carb::getFramework()->acquireInterface<carb::input::IInput>();

    auto mappings = m_actionEventGamepadMappings.find(gamepad);
    if (mappings != m_actionEventGamepadMappings.end())
    {
        for (auto& entry : mappings->second)
            input->unsubscribeToActionEvents(entry.second);
        mappings->second.clear();
    }
    m_actionEventGamepadMappings.erase(gamepad);

    input->unsubscribeToGamepadConnectionEvents(m_gamepadConnectionEventId);
    m_gamepadConnectionEventId = 0;

    m_gamepad = nullptr;
    m_gamepadEventFn = nullptr;
    m_userData = nullptr;
}

}
}
}
