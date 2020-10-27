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

#include <omni/isaac/utils/SurfaceGripper.h>
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
    // We use carb data types, must import bindings for them
    auto carb_module = py::module::import("carb");

    auto surface_grippers = m.def_submodule("surface_grippers");

    surface_grippers.doc() =
        R"pbdoc( 

        Surface Grippers
        -----------------

        This submodule provides a Helper to create a Surface Gripper joint using a PhysxD6Joint. 
        
        Example:
            To create a surface gripper you need to aquire the :obj:`omni.isaac.dynamic_control`, interface import this submodule, create a Surface_Gripper_Properties, and then create a Surface Gripper:

            ::

                from omni.isaac.utils._isaac_utils.surface_grippers import Surface_Gripper
                from omni.isaac.utils._isaac_utils.surface_grippers import Surface_Gripper_Properties
                from omni.isaac.dynamic_control import _dynamic_control

                # Create surface gripper
                _dc = _dynamic_control.acquire_interface()
                surface_gripper = Surface_Gripper(_dc)
                
                sgp = Surface_Gripper_Properties()

                # Configure the Gripper Properties here

                #Initialize the gripper with the properties
                surface_gripper.initialize(sgp)
            
        
        )pbdoc";

    py::class_<omni::isaac::utils::SurfaceGripperProperties>(
        surface_grippers, "Surface_Gripper_Properties", R"pbdoc(Properties for the Surface Gripper)pbdoc")
        .def(py::init<>())
        .def_readwrite("d6JointPath", &omni::isaac::utils::SurfaceGripperProperties::d6JointPath,
                       R"pbdoc(USD path to joint (:obj:`str`))pbdoc")
        .def_readwrite("parentPath", &omni::isaac::utils::SurfaceGripperProperties::parentPath,
                       R"pbdoc(USD Path to parent body (:obj:`str`))pbdoc")
        .def_readwrite(
            "offset", &omni::isaac::utils::SurfaceGripperProperties::offset,
            R"pbdoc(Transform from parent body to joint (:obj:`omni.isaac.dynamic_control._dynamic_control.Transform`))pbdoc")
        .def_readwrite("gripThreshold", &omni::isaac::utils::SurfaceGripperProperties::gripThreshold,
                       R"pbdoc(Threshold distance the gripper will respond to closing (:obj:`float`))pbdoc")
        .def_readwrite("forceLimit", &omni::isaac::utils::SurfaceGripperProperties::forceLimit,
                       R"pbdoc(Force Breaking limit (:obj:`float`))pbdoc")
        .def_readwrite("torqueLimit", &omni::isaac::utils::SurfaceGripperProperties::torqueLimit,
                       R"pbdoc(Torque Breaking limit (:obj:`float`))pbdoc")
        .def_readwrite("bendAngle", &omni::isaac::utils::SurfaceGripperProperties::bendAngle,
                       R"pbdoc(maximum bend angle for the gripper(:obj:`float`))pbdoc")
        .def_readwrite("stiffness", &omni::isaac::utils::SurfaceGripperProperties::stiffness,
                       R"pbdoc(Gripper Stiffness(:obj:`float`))pbdoc")
        .def_readwrite("damping", &omni::isaac::utils::SurfaceGripperProperties::damping,
                       R"pbdoc(Gripper Damping(:obj:`float`))pbdoc")
        .def_readwrite("disableGravity", &omni::isaac::utils::SurfaceGripperProperties::disableGravity,
                       R"pbdoc(Flag to disable gravity on selected object to compensate for its mass(:obj:`bool`))pbdoc")

        .def(py::pickle(
            [](const omni::isaac::utils::SurfaceGripperProperties& props) {
                return py::make_tuple(props.d6JointPath, props.parentPath, props.offset.p.x, props.offset.p.y,
                                      props.offset.p.z, props.offset.r.x, props.offset.r.y, props.offset.r.z,
                                      props.offset.r.w, props.gripThreshold, props.forceLimit, props.torqueLimit,
                                      props.bendAngle, props.stiffness, props.damping, props.disableGravity);
            },
            [](py::tuple t) {
                omni::isaac::utils::SurfaceGripperProperties props;
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
                props.bendAngle = t[12].cast<float>();
                props.stiffness = t[13].cast<float>();
                props.damping = t[14].cast<float>();
                props.disableGravity = t[15].cast<bool>();

                return props;
            }));

    auto surface_gripper =
        py::class_<SurfaceGripper>(surface_grippers, "Surface_Gripper")
            .def(py::init([](DynamicControl* dc) { return new SurfaceGripper(dc); }),
                 R"pbdoc(
                Creates a Surface Gripper, that connects two rigid bodies when it's actuated in close proximity

                Args:
                    arg0: dynamic control interface

            )pbdoc")
            .def("initialize", &SurfaceGripper::initialize,
                 R"pbdoc(
                Initializes the surface gripper object, setting the given properties

                Args:
                    arg0: surface gripper properties

                Returns:

                    `True` if initialization is succesful, `False` otherwise.

            )pbdoc")
            .def("close", &SurfaceGripper::close,
                 R"pbdoc(
                Attempts to close the gripper.

                Returns:

                    `True` if any object is within the gripper threshold and it closes, `False` otherwise.
                
                )pbdoc")
            .def("open", &SurfaceGripper::open,
                 R"pbdoc(
                     
                Attempts to open the gripper.

                Returns:

                    `True` if gripper was closed and it was succesfully open, `False` otherwise.
                    
                )pbdoc")
            .def("update", &SurfaceGripper::update,
                 R"pbdoc(Updates the internal status of the gripper. This must be called on every step the gripper is closed to verify the gripper did not break contact with the gripped object.

            )pbdoc")
            .def("is_closed", &SurfaceGripper::isClosed,
                 R"pbdoc(
                Returns:

                    `True` if gripper is closed, `False` otherwise.

                )pbdoc");


    auto math = m.def_submodule("math");

    math.doc() =
        R"pbdoc( 
            
        Math Utils
        -----------

        This submodule provides math bindings for vector operations, and other facilitators such as `lerp` functions.
            
        
        )pbdoc";

    // Basic operations between types (Add, Sub, Mul)
    math.def("mul", [](const carb::Float3& a, float x) { return a * x; }, py::is_operator(),
             R"pbdoc( Scales a 3D vector by a given value
        
        Args:
            arg0 (:obj:`carb.Float3`): 3D vector

            arg1 (:obj:`float`): scale factor

        Returns:
            :obj:`carb.Float3`: scaled vector.
        )pbdoc");
    math.def("mul", [](const carb::Float4& a, float x) { return a * x; }, py::is_operator(),
             R"pbdoc( Scales a 4D vector by a given value
        
        Args:
            arg0 (:obj:`carb.Float4`): 4D vector

            arg1 (:obj:`float`): scale factor

        Returns:
            :obj:`carb.Float4`: scaled vector.
        )pbdoc");
    math.def("mul", [](const carb::Float4& a, carb::Float4& x) { return a * x; }, py::is_operator(),
             R"pbdoc( Performs a Quaternion rotation between two 4D vectors
        
        Args:
            arg0 (:obj:`carb.Float4`): first 4D quaternion vector

            arg1 (:obj:`carb.Float4`): second 4D quaternion vector

        Returns:
            :obj:`carb.Float4`: rotated 4D quaternion vector.
        )pbdoc");
    math.def("mul", [](const DcTransform& a, DcTransform& x) { return a * x; }, py::is_operator(),
             R"pbdoc( Performs a Forward Transform multiplication between the transforms
        
        Args:
            arg0 (:obj:`omni.isaac.dynamic_control._dynamic_control.Transform`): First Transform

            arg1 (:obj:`omni.isaac.dynamic_control._dynamic_control.Transform`): Second Transform

        Returns:

            :obj:`omni.isaac.dynamic_control._dynamic_control.Transform`: ``arg0 * arg1``
        )pbdoc");
    math.def("add", [](const carb::Float3& a, carb::Float3& x) { return a + x; }, py::is_operator(),
             R"pbdoc( 
        Args:
            arg0 (:obj:`carb.Float3`): 3D vector

            arg1 (:obj:`carb.Float3`): 3D vector

        Returns:

            :obj:`carb.Float3`: ``arg0 + arg1``.
        )pbdoc");

    // Vector and transform operations
    math.def("cross", &omni::isaac::utils::math::cross,
             R"pbdoc(
             Performs Cross product between 3D vectors
             Args:
                 arg0 (:obj:`carb.Float3`): 3D vector

                 arg1 (:obj:`carb.Float3`): 3D vector

             Returns:

                :obj:`carb.Float3`: cross poduct ``arg0 x arg1``.
             )pbdoc");

    math.def("dot", py::overload_cast<const carb::Float3&, const carb::Float3&>(&omni::isaac::utils::math::dot),
             R"pbdoc(Performs Dot product between 3D vectors
             Args:
                 arg0 (:obj:`carb.Float3`): 3D vector

                 arg1 (:obj:`carb.Float3`): 3D vector

             Returns:

                 :obj:`carb.Float3`: dot poduct ``arg0 * arg1``.
             )pbdoc");

    math.def("dot", py::overload_cast<const carb::Float4&, const carb::Float4&>(&omni::isaac::utils::math::dot),
             R"pbdoc(Performs Dot product between 4D vectors
             Args:
                 arg0 (:obj:`carb.Float4`): 4D vector

                 arg1 (:obj:`carb.Float4`): 4D vector

             Returns:

                 :obj:`carb.Float4`: dot poduct ``arg0 * arg1``.

             )pbdoc");
    math.def("inverse", py::overload_cast<const carb::Float4&>(&omni::isaac::utils::math::inverse),
             R"pbdoc(
                Gets Inverse Quaternion

                Args:

                    arg0 (:obj:`carb.Float4`): quaternion
                Returns:

                    :obj:`carb.Float4`: The inverse quaternion

                )pbdoc");
    math.def("inverse", py::overload_cast<const DcTransform&>(&omni::isaac::utils::math::inverse),
             R"pbdoc(
                Gets Inverse Transform

                Args:

                    arg0 (:obj:`omni.isaac.dynamic_control._dynamic_control.Transform`): Transform

                Returns:

                    :obj:`omni.isaac.dynamic_control._dynamic_control.Transform`: The inverse Inverse Transform

                )pbdoc");
    math.def("normalize", py::overload_cast<const carb::Float3&>(&omni::isaac::utils::math::normalize),
             R"pbdoc(
                Gets normalized 3D vector

                Args:

                    arg0 (:obj:`carb.Float3`): 3D Vector

                Returns:

                    :obj:`carb.Float3`: Normalized 3D Vector
                    
                )pbdoc");
    math.def("normalize", py::overload_cast<const carb::Float4&>(&omni::isaac::utils::math::normalize),
             R"pbdoc(
                Gets normalized 4D vector
                Args:

                    arg0 (:obj:`carb.Float4`): 4D Vector
                    
                Returns:

                    :obj:`carb.Float4`: Normalized 4D Vector
                )pbdoc");
    math.def("rotate", omni::isaac::utils::math::rotate,
             R"pbdoc(
                rotates the 3D vector arg1 by the quaternion `arg0`

                Args:
                
                    arg0 (:obj:`carb.Float4`): quaternion

                    arg1 (:obj:`carb.Float3`): 3D Vector

                Returns:

                    :obj:`carb.Float3`: Rotated 3D Vector
                )pbdoc");
    math.def("transform_inv",
             py::overload_cast<const DcTransform&, const DcTransform&>(&omni::isaac::utils::math::transformInv),
             R"pbdoc(
                Computes local Transform of arg1 with respect to arg0: `inv(arg0)*arg1`

                Args:
                
                    arg0 (`omni.isaac.dynamic_control._dynamic_control.Transform`): origin Transform

                    arg1 (`omni.isaac.dynamic_control._dynamic_control.Transform`): Transform

                Returns:

                    :obj:`omni.isaac.dynamic_control._dynamic_control.Transform`: resulting transform of ``inv(arg0)*arg1``
                )pbdoc");
    math.def("transform_inv",
             py::overload_cast<const pxr::GfTransform&, const pxr::GfTransform&>(&omni::isaac::utils::math::transformInv),
             R"pbdoc(
                Computes local Transform of arg1 with respect to arg0: `inv(arg0)*arg1`

                Args:
                
                    arg0 (`pxr.Transform`): origin Transform

                    arg1 (`pxr.Transform`): Transform

                Returns:

                    :obj:`oxr.Transform`: resulting transform of ``inv(arg0)*arg1``
                )pbdoc");


    // Utility functions
    math.def("get_basis_vector_x", &omni::isaac::utils::math::getBasisVectorX,
             R"pbdoc(
                Gets Basis vector X of quaternion

                Args:

                    arg0 (:obj:`carb.Float4`): Quaternion

                Returns:

                    :obj:`carb.Float3`: Basis Vector X
                    
                )pbdoc");
    math.def("get_basis_vector_y", &omni::isaac::utils::math::getBasisVectorY,
             R"pbdoc(
                Gets Basis vector Y of quaternion

                Args:

                    arg0 (:obj:`carb.Float4`): Quaternion

                Returns:

                    :obj:`carb.Float3`: Basis Vector Y
                    
                )pbdoc");
    math.def("get_basis_vector_z", &omni::isaac::utils::math::getBasisVectorZ,
             R"pbdoc(
                Gets Basis vector Z of quaternion

                Args:

                    arg0 (:obj:`carb.Float4`): Quaternion

                Returns:

                    :obj:`carb.Float3`: Basis Vector Z
                    
                )pbdoc");

    math.def("lerp",
             py::overload_cast<const carb::Float3&, const carb::Float3&, const float>(&omni::isaac::utils::math::lerp),
             R"pbdoc(
                Performs Linear interpolation between points arg0 and arg1

                Args:

                    arg0 (:obj:`carb.Float3`): Point

                    arg1 (:obj:`carb.Float3`): Point

                    arg2 (:obj:`float`): distance from 0 to 1, where 0 is closest to arg0, and 1 is closest to arg1

                Returns:

                    :obj:`carb.Float3`: Interpolated point
                    
                )pbdoc");
    math.def("lerp",
             py::overload_cast<const carb::Float4&, const carb::Float4&, const float>(&omni::isaac::utils::math::lerp),
             R"pbdoc(
                Performs Linear interpolation between quaternions arg0 and arg1

                Args:

                    arg0 (:obj:`carb.Float4`): Quaternion

                    arg1 (:obj:`carb.Float4`): Quaternion

                    arg2 (:obj:`float`): distance from 0 to 1, where 0 is closest to arg0, and 1 is closest to arg1

                Returns:

                    :obj:`carb.Float4`: Interpolated quaternion
                    
                )pbdoc");
    math.def("lerp",
             py::overload_cast<const DcTransform&, const DcTransform&, const float>(&omni::isaac::utils::math::lerp),
             R"pbdoc(
                Performs Linear interpolation between points arg0 and arg1

                Args:

                    arg0 (:obj:`omni.isaac.dynamic_control._dynamic_control.Transform`): Transform

                    arg1 (:obj:`omni.isaac.dynamic_control._dynamic_control.Transform`): Transform

                    arg2 (:obj:`float`): distance from 0 to 1, where 0 is closest to arg0, and 1 is closest to arg1

                Returns:

                    :obj:`omni.isaac.dynamic_control._dynamic_control.Transform`: Interpolated transform
                    
                )pbdoc");
    math.def("slerp",
             py::overload_cast<const carb::Float4&, const carb::Float4&, const float>(&omni::isaac::utils::math::slerp),
             R"pbdoc(
                Performs Spherical Linear interpolation between quaternions arg0 and arg1

                Args:

                    arg0 (:obj:`carb.Float4`): Quaternion

                    arg1 (:obj:`carb.Float4`): Quaternion

                    arg2 (:obj:`float`): distance from 0 to 1, where 0 is closest to arg0, and 1 is closest to arg1

                Returns:

                    :obj:`carb.Float4`: Interpolated quaternion
                    
                )pbdoc");
    math.def("slerp",
             py::overload_cast<const DcTransform&, const DcTransform&, const float>(&omni::isaac::utils::math::slerp),
             R"pbdoc(
                Performs Spherical Linear interpolation between points arg0 and arg1

                Args:

                    arg0 (:obj:`omni.isaac.dynamic_control._dynamic_control.Transform`): Transform

                    arg1 (:obj:`omni.isaac.dynamic_control._dynamic_control.Transform`): Transform

                    arg2 (:obj:`float`): distance from 0 to 1, where 0 is closest to arg0, and 1 is closest to arg1

                Returns:

                    :obj:`omni.isaac.dynamic_control._dynamic_control.Transform`: Interpolated transform
                    
                )pbdoc");
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
