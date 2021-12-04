// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "omni/isaac/gamepad/Input.h"

#include <carb/BindingsPythonUtils.h>

#include <pybind11/pybind11/functional.h>
CARB_BINDINGS("omni.isaac.gamepad.python")

namespace omni
{
namespace isaac
{
namespace gamepad
{
}
}
}

namespace
{
PYBIND11_MODULE(_gamepad, m)
{
    using namespace carb;
    using namespace omni::isaac::gamepad;

    static std::function<void(int axis, float value)> s_gamepad_binding_fn = nullptr;

    m.doc() = R"pbdoc(
        This extension provides an interface to connecting with a gamepad controller. 
        
        Example:
            To use this interface you must first call the acquire interface function.
            To connect with gamepad, you bind to the gamepad before using it, and unbind with it at the end.
           
            ::

                from omni.isaac.gamepad import _gamepad, GamePadAxis

                gamepad_interface = _gamepad.acquire_gamepad_interface()
                
                def myfunc(axis: GamePadAxis, data: float):
                    print("called!  Axis is ", axis, " signal is", data)
                    if axis == GamePadAxis.eLeftStickX:
                        print("****in LX")
                    elif axis == GamePadAxis.eLeftStickY:
                        print("****in LY")
                    if axis == GamePadAxis.eRightStickX:
                        print("****in RX")
                    elif axis == GamePadAxis.eRightStickY:
                        print("****in RY")
                
                gamepad_interface.bind_gamepad(myfunc)
        
        Refer to the kaya sample documentation for more examples and usage
                )pbdoc";

    defineInterfaceClass<Input>(m, "GamepadInput", "acquire_gamepad_interface", "release_gamepad_interface")
        .def("bind_gamepad",
             [](Input* iface, std::function<void(int axis, float value)> eventFn)
             {
                 s_gamepad_binding_fn = std::move(eventFn);

                 iface->bind_gamepad(
                     [](int axis, float value, void* userData)
                     {
                         auto fn = reinterpret_cast<std::function<void(int axis, float value)>*>(userData);
                         if (fn && *fn)
                         {
                             carb::StdFuncUtils<std::function<void(int axis, float value)>>::callPythonCodeSafe(
                                 *fn, axis, value);
                         }
                     },
                     &s_gamepad_binding_fn);
             },
             R"pbdoc(
                Bind to gamepad. Gamepad must be plugged in before calling the bind function.

                Args: 
                    arg0 (:obj:`arg0: Callable[[int, float], None]`): The callback function, where the input arguments of this function is an ``int`` representing an axis of the gamepad and a ``float`` value detected on that axis".

                )pbdoc")

        .def("unbind_gamepad",
             [](Input* iface)
             {
                 s_gamepad_binding_fn = nullptr;
                 iface->unbind_gamepad();
             },
             R"pbdoc(
            Unbind gamepad, called to release gamepad connection properly.
            )pbdoc");
}
}
