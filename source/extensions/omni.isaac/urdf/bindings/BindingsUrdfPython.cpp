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


    py::class_<ImportConfig>(m, "ImportConfig")
        .def(py::init<>())
        .def_readwrite("merge_fixed_joints", &ImportConfig::mergeFixedJoints,
                       "Consolidating links that are connected by fixed joints")
        .def_readwrite("enable_convex_decomp", &ImportConfig::enableConvexDecomp,
                       "Decompose a convex mesh into smaller pieces for a closer fit")
        .def_readwrite("distance_scale", &ImportConfig::distanceScale,
                       "Set the unit scaling factor, 1.0 means meters, 100.0 means cm")
        .def_readwrite("force_z_up", &ImportConfig::forceZUp, "Force Z axis to be up in the simulator durin import")
        .def_readwrite("add_debug_info", &ImportConfig::addDebugInfo, "Publish details for the imported URDF")
        .def_readwrite("import_inertia_tensor", &ImportConfig::importInertiaTensor,
                       "Import inertia tensor from urdf, if not specified in urdf it will import as identity");

    defineInterfaceClass<Urdf>(m, "Urdf", "acquire_urdf_interface", "release_urdf_interface")
        .def("import_urdf", wrapInterfaceFunction(&Urdf::importUrdf));
}
}
