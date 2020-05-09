// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/utils/MagicJoint.h>
#include <omni/isaac/utils/Math.h>
#include <omni/isaac/utils/Conversions.h>

CARB_BINDINGS("omni.isaac.utils.python")

namespace omni
{
namespace isaac
{
namespace utils
{
}
}
}

namespace
{
PYBIND11_MODULE(_isaac_utils, m)
{
    using namespace omni::isaac::utils::math;
    using namespace omni::isaac::utils;
    using namespace omni::isaac::dynamic_control;

    m.doc() = "Isaac utils bindings";

    auto magic_joints = m.def_submodule("magic_joints");

    py::class_<omni::isaac::utils::MagicJointProperties>(
        magic_joints, "Magic_Joint_Properties",
        "Creates a magic joint to connect two rigid bodies when it's actuated in close proximity")
        .def(py::init<>())
        .def_readwrite("d6JointPath", &omni::isaac::utils::MagicJointProperties::d6JointPath, "USD path to joint")
        .def_readwrite("parentPath", &omni::isaac::utils::MagicJointProperties::parentPath, "DC handle to parent body")
        .def_readwrite("offset", &omni::isaac::utils::MagicJointProperties::offset, "Transform from body to joint")
        .def_readwrite("gripThreshold", &omni::isaac::utils::MagicJointProperties::gripThreshold,
                       "Threshold in which the gripper will respond to closing")
        .def_readwrite("forceLimit", &omni::isaac::utils::MagicJointProperties::forceLimit, "Force Breaking limit")
        .def_readwrite("torqueLimit", &omni::isaac::utils::MagicJointProperties::torqueLimit, "Torque Breaking limit")
        .def(py::pickle(
            [](const omni::isaac::utils::MagicJointProperties& props) {
                return py::make_tuple(props.d6JointPath, props.parentPath, props.offset.p.x, props.offset.p.y,
                                      props.offset.p.z, props.offset.r.x, props.offset.r.y, props.offset.r.z,
                                      props.offset.r.w, props.gripThreshold, props.forceLimit, props.torqueLimit);
            },
            [](py::tuple t) {
                omni::isaac::utils::MagicJointProperties props;
                std::string str = t[0].cast<std::string>();
                std::vector<char> cstr(str.c_str(), str.c_str() + str.size() + 1);
                props.d6JointPath = cstr.data();
                str = t[1].cast<std::string>();
                std::vector<char> cstr2(str.c_str(), str.c_str() + str.size() + 1);
                props.parentPath = cstr2.data();
                props.offset.p = { t[2].cast<float>(), t[3].cast<float>(), t[4].cast<float>() };
                props.offset.r = { t[5].cast<float>(), t[6].cast<float>(), t[7].cast<float>(), t[8].cast<float>() };
                props.gripThreshold = t[9].cast<float>();
                props.forceLimit = t[10].cast<float>();
                props.torqueLimit = t[11].cast<float>();

                return props;
            }));

    auto magic_joint = py::class_<MagicJoint>(magic_joints, "Magic_Joint")
                           .def(py::init([](DynamicControl* dc) { return new MagicJoint(dc); }))
                           .def("initialize", &MagicJoint::initialize)
                           .def("close", &MagicJoint::close)
                           .def("open", &MagicJoint::open)
                           .def("update", &MagicJoint::update)
                           .def("is_closed", &MagicJoint::isClosed);


    auto math = m.def_submodule("math");
    // Basic operations between types (Add, Sub, Mul)
    math.def("mul", [](const carb::Float3& a, float x) { return a * x; }, py::is_operator());
    math.def("mul", [](const carb::Float4& a, float x) { return a * x; }, py::is_operator());
    math.def("mul", [](const carb::Float4& a, carb::Float4& x) { return a * x; }, py::is_operator());
    math.def("mul", [](const DcTransform& a, DcTransform& x) { return a * x; }, py::is_operator());
    math.def("add", [](const carb::Float3& a, carb::Float3& x) { return a + x; }, py::is_operator());

    // Vector and transform operations
    math.def("cross", &omni::isaac::utils::math::cross);
    math.def("dot", py::overload_cast<const carb::Float3&, const carb::Float3&>(&omni::isaac::utils::math::dot));
    math.def("dot", py::overload_cast<const carb::Float4&, const carb::Float4&>(&omni::isaac::utils::math::dot));
    math.def("inverse", py::overload_cast<const carb::Float4&>(&omni::isaac::utils::math::inverse));
    math.def("inverse", py::overload_cast<const DcTransform&>(&omni::isaac::utils::math::inverse));
    math.def("normalize", py::overload_cast<const carb::Float3&>(&omni::isaac::utils::math::normalize));
    math.def("normalize", py::overload_cast<const carb::Float4&>(&omni::isaac::utils::math::normalize));
    math.def("rotate", omni::isaac::utils::math::rotate);
    math.def("transform_inv",
             py::overload_cast<const DcTransform&, const DcTransform&>(&omni::isaac::utils::math::transformInv));
    math.def("transform_inv", py::overload_cast<const pxr::GfTransform&, const pxr::GfTransform&>(
                                  &omni::isaac::utils::math::transformInv));


    // Utility functions
    math.def("get_basis_vector_x", &omni::isaac::utils::math::getBasisVectorX);
    math.def("get_basis_vector_y", &omni::isaac::utils::math::getBasisVectorY);
    math.def("get_basis_vector_z", &omni::isaac::utils::math::getBasisVectorZ);

    math.def("lerp",
             py::overload_cast<const carb::Float3&, const carb::Float3&, const float>(&omni::isaac::utils::math::lerp));
    math.def("lerp",
             py::overload_cast<const carb::Float4&, const carb::Float4&, const float>(&omni::isaac::utils::math::lerp));
    math.def("lerp",
             py::overload_cast<const DcTransform&, const DcTransform&, const float>(&omni::isaac::utils::math::lerp));
    math.def("slerp",
             py::overload_cast<const carb::Float4&, const carb::Float4&, const float>(&omni::isaac::utils::math::slerp));
    math.def("slerp",
             py::overload_cast<const DcTransform&, const DcTransform&, const float>(&omni::isaac::utils::math::slerp));
    // {
    //     using namespace omni::isaac::utils::conversions;
    //     math.def("look_at", [](const carb::Float3& a, carb::Float3& b, carb::Float3& c) {
    //         return asCarbFloat4(omni::isaac::utils::math::lookAt(asGfVec3f(a), asGfVec3f(b), asGfVec3f(c)));
    //     });
    // }
    // Conversion functions
    // {
    //     using namespace omni::isaac::utils::conversions;
    //     auto convert = m.def_submodule("convert");
    //     convert.def("as_gf_transform", py::overload_cast<const DcTransform&>(&asGfTransform));
    //     convert.def("as_gf_transform", py::overload_cast<const carb::Float3&, const carb::Float4&>(&asGfTransform));
    //     convert.def("as_gf_matrix", &asGfMatrix4f);
    //     convert.def("as_gf_matrix_t", &asGfMatrix4fT);
    // }
}
}
