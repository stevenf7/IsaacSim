// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/input/InputTypes.h>
#include <carb/settings/ISettings.h>

#include <omni/isaac/manip/Input.h>

#include <unordered_map>

namespace omni
{
namespace isaac
{
namespace manip
{

template <typename T>
class SplitValue
{
public:
    enum Sign
    {
        eNeg,
        ePos
    };

    SplitValue()
    {
        m_value[eNeg] = m_value[ePos] = (T)0;
    }

    T operator=(T value)
    {
        if (value < (T)0)
        {
            m_value[eNeg] = -value;
            m_value[ePos] = (T)0;
        }
        else
        {
            m_value[eNeg] = (T)0;
            m_value[ePos] = value;
        }
    }

    operator T() const
    {
        return m_value[ePos] - m_value[eNeg];
    }

    T set(int signPos, T value)
    {
        m_value[signPos & 1] = value;
        return *this;
    }

private:
    T m_value[2];
};


// GamePadBinding
class GamePadBinding
{
public:
    enum Axis
    {
        eLeftStickX,
        eLeftStickY,
        eRightStickX,
        eRightStickY,
        eLeftTrigger,
        eRightTrigger,

        eAxisCount
    };

    typedef void (*AxisUpdateFn)(Axis axis, float value, const char* path);

    GamePadBinding();
    ~GamePadBinding();

    void bind(GamepadEventFn eventFn, void* userData);

    void unbind();

    float getValue(Axis axis) const
    {
        CARB_ASSERT(axis < eAxisCount);
        return axis < eAxisCount ? m_value[axis] : 0.f;
    }

private:
    template <int axis, int sign>
    void subscribOnGamepadAction(carb::input::Gamepad* gamepad,
                                 const char* action,
                                 const carb::input::GamepadInput gamepadInput);

    void unBindGamepad(carb::input::Gamepad* gamepad);

    void onGamepadConnectionEvent(const carb::input::GamepadConnectionEvent& evt);

    using ActionSubscriptionMappings = std::unordered_map<const char*, carb::input::SubscriptionId>;

    // Members
    carb::input::SubscriptionId m_gamepadConnectionEventId;
    std::unordered_map<carb::input::Gamepad*, ActionSubscriptionMappings> m_actionEventGamepadMappings;

    SplitValue<float> m_value[eAxisCount];
    carb::input::Gamepad* m_gamepad;
    GamepadEventFn m_gamepadEventFn;
    void* m_userData;
};

}
}
}
