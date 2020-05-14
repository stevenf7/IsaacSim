// Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/urdf/Urdf.h>

CARB_BINDINGS("omni.isaac.urdf.python")

namespace omni
{
namespace isaac
{
namespace urdf
{

}
}
}

namespace
{
PYBIND11_MODULE(_urdf, m)
{
    using namespace carb;
    using namespace omni::isaac::urdf;

    m.doc() = "Isaac URDF Utils bindings";

    defineInterfaceClass<Urdf>(m, "Urdf", "acquire_urdf_interface", "release_urdf_interface")
        .def("importUrdf", wrapInterfaceFunction(&Urdf::importUrdf))
        .def("merge_fixed_joints", wrapInterfaceFunction(&Urdf::mergeFixedJoints))
        .def("set_unit_scale", wrapInterfaceFunction(&Urdf::setUnitScale));
}
}
