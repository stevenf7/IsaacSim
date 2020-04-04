// Copyright (c) 2018-2019, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include "omni/isaac/manip/Input.h"

#include <carb/BindingsPythonUtils.h>

CARB_BINDINGS("omni.isaac.manip.python")

namespace omni
{
namespace isaac
{
namespace manip
{
}
}
}

namespace
{
PYBIND11_MODULE(_manip, m)
{
    using namespace carb;
    using namespace omni::isaac::manip;

    static decltype(std::function<void(int axis, float value)>())* s_gamepad_binding_fn = nullptr;

    m.doc() = "pybind11 omni.isaac.manip bindings";

    defineInterfaceClass<Input>(m, "ManipInput", "acquire")
        .def("bind_gamepad",
             [](Input* iface, std::function<void(int axis, float value)> eventFn) {
                 delete s_gamepad_binding_fn;
                 s_gamepad_binding_fn = new decltype(std::function<void(int axis, float value)>())(eventFn);
                 iface->bind_gamepad(
                     [](int axis, float value, void* userData) {
                         auto fn = static_cast<decltype(std::function<void(int axis, float value)>())*>(userData);
                         if (fn && *fn)
                             carb::StdFuncUtils<std::function<void(int axis, float value)>>::callPythonCodeSafe(
                                 *fn, axis, value);
                     },
                     s_gamepad_binding_fn);
             })
        .def("unbind_gamepad", [](Input* iface) {
            delete s_gamepad_binding_fn;
            s_gamepad_binding_fn = nullptr;
            iface->unbind_gamepad();
        });
}
}
