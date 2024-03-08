// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <UsdPCH.h>
// clang-format on

#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/utils/Conversions.h>
#include <omni/isaac/utils/Math.h>
#include <omni/isaac/utils/Transforms.h>

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
    using namespace carb;
    using namespace omni::isaac::utils::math;
    using namespace omni::isaac::utils;
    using namespace omni::isaac::dynamic_control;
    // We use carb data types, must import bindings for them
    auto carb_module = py::module::import("carb");

    auto math = m.def_submodule("math");

    math.doc() =
        R"pbdoc( 
            
        Math Utils
        -----------

        This submodule provides math bindings for vector operations, and other facilitators such as `lerp` functions.
            
        
        )pbdoc";

    // Basic operations between types (Add, Sub, Mul)
    math.def(
        "mul", [](const carb::Float3& a, float x) { return a * x; }, py::is_operator(),
        R"pbdoc( Scales a 3D vector by a given value
        
        Args:
            arg0 (:obj:`carb.Float3`): 3D vector

            arg1 (:obj:`float`): scale factor

        Returns:
            :obj:`carb.Float3`: scaled vector.
        )pbdoc");
    math.def(
        "mul", [](const carb::Float4& a, float x) { return a * x; }, py::is_operator(),
        R"pbdoc( Scales a 4D vector by a given value
        
        Args:
            arg0 (:obj:`carb.Float4`): 4D vector

            arg1 (:obj:`float`): scale factor

        Returns:
            :obj:`carb.Float4`: scaled vector.
        )pbdoc");
    math.def(
        "mul", [](const carb::Float4& a, carb::Float4& x) { return a * x; }, py::is_operator(),
        R"pbdoc( Performs a Quaternion rotation between two 4D vectors
        
        Args:
            arg0 (:obj:`carb.Float4`): first 4D quaternion vector

            arg1 (:obj:`carb.Float4`): second 4D quaternion vector

        Returns:
            :obj:`carb.Float4`: rotated 4D quaternion vector.
        )pbdoc");
    math.def(
        "mul", [](const DcTransform& a, DcTransform& x) { return a * x; }, py::is_operator(),
        R"pbdoc( Performs a Forward Transform multiplication between the transforms
        
        Args:
            arg0 (:obj:`omni.isaac.dynamic_control._dynamic_control.Transform`): First Transform

            arg1 (:obj:`omni.isaac.dynamic_control._dynamic_control.Transform`): Second Transform

        Returns:

            :obj:`omni.isaac.dynamic_control._dynamic_control.Transform`: ``arg0 * arg1``
        )pbdoc");
    math.def(
        "add", [](const carb::Float3& a, carb::Float3& x) { return a + x; }, py::is_operator(),
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
             R"pbdoc(Gets Inverse Quaternion
             Args:

                 arg0 (:obj:`carb.Float4`): quaternion

             Returns:
             
                 :obj:`carb.Float4`: The inverse quaternion

             )pbdoc");
    math.def("inverse", py::overload_cast<const DcTransform&>(&omni::isaac::utils::math::inverse),
             R"pbdoc(Gets Inverse Transform
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
    auto transforms = m.def_submodule("transforms");

    transforms.def(
        "set_transform",
        [](const long int stageId, const std::string primPath, const carb::Float3& translation,
           const carb::Float4& rotation)
        {
            pxr::UsdStageWeakPtr stage =
                pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            pxr::UsdPrim prim = stage->GetPrimAtPath(pxr::SdfPath(primPath));

            if (prim)
            {

                omni::isaac::utils::transforms::setTransform(prim,
                                                             omni::isaac::utils::conversions::asGfVec3f(translation),
                                                             omni::isaac::utils::conversions::asGfQuatf(rotation));
            }
            else
            {
                CARB_LOG_ERROR("Set Transform Prim %s Not Valid", primPath.c_str());
            }
        },
        R"pbdoc(
                Set transform for an object in the stage, handles physics objects if simulation is running using dynamic control

                Args:

                    arg0 (:obj:`omni.isaac.dynamic_control._dynamic_control`): handle to dynamic control api

                    arg1 (:obj:`int`): Stage ID

                    arg2 (:obj:`carb::Float3`): translation
                    arg2 (:obj:`carb::Float4`): rotation
                    
                )pbdoc");

    transforms.def(
        "set_scale",
        [](const long int stageId, const std::string primPath, const carb::Float3& scale)
        {
            pxr::UsdStageWeakPtr stage =
                pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            pxr::UsdPrim prim = stage->GetPrimAtPath(pxr::SdfPath(primPath));

            if (prim)
            {

                omni::isaac::utils::transforms::setScale(prim, omni::isaac::utils::conversions::asGfVec3f(scale));
            }
            else
            {
                CARB_LOG_ERROR("Set Scale Prim %s Not Valid", primPath.c_str());
            }

            // return new
            // // MapGenerator(physXPtr, stage);
        },
        R"pbdoc(
                Set scale for an object in the stage

                Args:

                    arg0 (:obj:`omni.isaac.dynamic_control._dynamic_control`): handle to dynamic control api

                    arg1 (:obj:`int`): Stage ID

                    arg2 (:obj:`carb::Float3`): scale
                    
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
