// Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <pybind11/pybind11/numpy.h>

CARB_BINDINGS("omni.isaac.dynamic_control.python")

namespace omni
{
namespace isaac
{
namespace dynamic_control
{
/*
// pacify pybind11 about undefined types
struct DcContext
{
};
struct DcArticulation
{
};
struct DcRigidBody
{
};
struct DcDof
{
};
struct DcAttractor
{
};
*/
}
}
}

namespace
{
PYBIND11_MODULE(_dynamic_control, m)
{
    using namespace carb;
    using namespace omni::isaac::dynamic_control;

    m.doc() = "Dynamic Control bindings";

    m.attr("INVALID_HANDLE") = py::int_(kDcInvalidHandle);

    // state flags
    m.attr("STATE_NONE") = py::int_(kDcStateNone);
    m.attr("STATE_POS") = py::int_(kDcStatePos);
    m.attr("STATE_VEL") = py::int_(kDcStateVel);
    m.attr("STATE_ALL") = py::int_(kDcStateAll);

    // axis flags
    m.attr("AXIS_NONE") = py::int_(kDcAxisNone);
    m.attr("AXIS_X") = py::int_(kDcAxisX);
    m.attr("AXIS_Y") = py::int_(kDcAxisY);
    m.attr("AXIS_Z") = py::int_(kDcAxisZ);
    m.attr("AXIS_TWIST") = py::int_(kDcAxisTwist);
    m.attr("AXIS_SWING_1") = py::int_(kDcAxisSwing1);
    m.attr("AXIS_SWING_2") = py::int_(kDcAxisSwing2);
    m.attr("AXIS_ALL_TRANSLATION") = py::int_(kDcAxisAllTranslation);
    m.attr("AXIS_ALL_ROTATION") = py::int_(kDcAxisAllRotation);
    m.attr("AXIS_ALL") = py::int_(kDcAxisAll);

    py::enum_<DcJointType>(m, "JointType", py::arithmetic(), "Types of joint")
        .value("JOINT_NONE", DcJointType::eNone, "invalid/unknown/uninitialized joint type")
        .value("JOINT_FIXED", DcJointType::eFixed)
        .value("JOINT_REVOLUTE", DcJointType::eRevolute)
        .value("JOINT_PRISMATIC", DcJointType::ePrismatic)
        .value("JOINT_SPHERICAL", DcJointType::eSpherical)
        .export_values();

    py::enum_<DcDofType>(m, "DofType", py::arithmetic(), "Types of degree of freedom")
        .value("DOF_NONE", DcDofType::eNone, "invalid/unknown/uninitialized DOF type")
        .value("DOF_ROTATION", DcDofType::eRotation, "The degrees of freedom correspond to a rotation between bodies")
        .value("DOF_TRANSLATION", DcDofType::eTranslation,
               "The degrees of freedom correspond to a translation between bodies.")
        .export_values();

    py::enum_<DcDriveMode>(m, "DriveMode", py::arithmetic(), "DOF drive mode")
        .value("DRIVE_NONE", DcDriveMode::eNone, "No drive")
        .value("DRIVE_POS", DcDriveMode::ePositionTarget, "Position target drive")
        .value("DRIVE_VEL", DcDriveMode::eVelocityTarget, "Velocity target drive")
        //.value("DRIVE_EFFORT", DcDriveMode::eEffort, "Effort drive")
        .export_values();

    py::enum_<DcObjectType>(m, "ObjectType", py::arithmetic(), "Types of Object")
        .value("OBJECT_NONE", DcObjectType::eDcObjectNone, "invalid/unknown/uninitialized object type")
        .value("OBJECT_RIGIDBODY", DcObjectType::eDcObjectRigidBody)
        .value("OBJECT_JOINT", DcObjectType::eDcObjectJoint)
        .value("OBJECT_DOF", DcObjectType::eDcObjectDof)
        .value("OBJECT_ARTICULATION", DcObjectType::eDcObjectArticulation)
        .value("OBJECT_ATTRACTOR", DcObjectType::eDcObjectAttractor)
        .value("OBJECT_D6JOINT", DcObjectType::eDcObjectD6Joint)
        .export_values();

    // opaque types
    /*
    py::class_<DcContext>(m, "Context");
    py::class_<DcArticulation>(m, "Articulation");
    py::class_<DcRigidBody>(m, "RigidBody");
    py::class_<DcDof>(m, "Dof");
    py::class_<DcAttractor>(m, "Attractor");
    */

#if 0
    py::class_<carb::Float3>(m, "Vec3")
        .def_readwrite("x", &carb::Float3::x)
        .def_readwrite("y", &carb::Float3::y)
        .def_readwrite("z", &carb::Float3::z)
        .def(py::init<float, float, float>(), py::arg("x") = 0.0f, py::arg("y") = 0.0f, py::arg("z") = 0.0f)
        .def_property_readonly_static("dtype",
                                      [](const py::object&) {
                                          return py::dtype::of<carb::Float3>(); // return the numpy structured dtype
                                      })
        .def_static("from_buffer",
                    [](py::buffer buf) -> py::object {
                        py::buffer_info info = buf.request();
                        if (info.ptr != nullptr)
                        {
                            if (info.itemsize == 3 * sizeof(float) ||
                                info.itemsize == sizeof(float) && info.ndim > 0 && info.shape[info.ndim - 1] >= 3)
                            {
                                float* data = (float*)info.ptr;
                                return py::cast(carb::Float3{ data[0], data[1], data[2] });
                            }
                        }
                        return py::none();
                    })
        .def("__str__",
             [](const carb::Float3& self) {
                 return "Vec3(" + std::to_string(self.x) + ", " + std::to_string(self.y) + ", " +
                        std::to_string(self.z) + ")";
             })
        .def("__add__",
             [](const carb::Float3& self, const carb::Float3& other) {
                 return carb::Float3{ self.x + other.x, self.y + other.y, self.z + other.z };
             })
        .def("__sub__",
             [](const carb::Float3& self, const carb::Float3& other) {
                 return carb::Float3{ self.x - other.x, self.y - other.y, self.z - other.z };
             })
        .def("__mul__",
             [](const carb::Float3& self, float s) {
                 return carb::Float3{ self.x * s, self.y * s, self.z * s };
             })
        .def("__truediv__",
             [](const carb::Float3& self, float s) {
                 return carb::Float3{ self.x / s, self.y / s, self.z / s };
             })
        .def("__neg__",
             [](const carb::Float3& self) {
                 return carb::Float3{ -self.x, -self.y, -self.z };
             })
        /*
        .def("length", [](const carb::Float3& self) { return Length((const Vec3&)self); })
        .def("length_sq", [](const carb::Float3& self) { return LengthSq((const Vec3&)self); })
        .def("normalize",
             [](const carb::Float3& self) {
                 Vec3 result = Normalize((const Vec3&)self);
                 return carb::Float3{ result.x, result.y, result.z };
             })
        .def("dot", [](const carb::Float3& self,
                       const carb::Float3& other) { return Dot((const Vec3&)self, (const Vec3&)other); })
        .def("cross",
             [](const carb::Float3& self, const carb::Float3& other) {
                 Vec3 result = Cross((const Vec3&)self, (const Vec3&)other);
                 return carb::Float3{ result.x, result.y, result.z };
             })
        */
        .def(py::pickle([](const carb::Float3& v) { return py::make_tuple(v.x, v.y, v.z); },
                        [](py::tuple t) {
                            return carb::Float3{ t[0].cast<float>(), t[1].cast<float>(), t[2].cast<float>() };
                        }));

    py::class_<carb::Float4>(m, "Quat")
        .def_readwrite("x", &carb::Float4::x)
        .def_readwrite("y", &carb::Float4::y)
        .def_readwrite("z", &carb::Float4::z)
        .def_readwrite("w", &carb::Float4::w)
        .def(py::init<float, float, float, float>(), py::arg("x") = 0.0f, py::arg("y") = 0.0f, py::arg("z") = 0.0f,
             py::arg("w") = 1.0f)
        .def_property_readonly_static("dtype",
                                      [](const py::object&) {
                                          return py::dtype::of<carb::Float4>(); // return the numpy structured dtype
                                      })
        .def_static("from_buffer",
                    [](py::buffer buf) -> py::object {
                        py::buffer_info info = buf.request();
                        if (info.ptr != nullptr)
                        {
                            if (info.itemsize == 4 * sizeof(float) ||
                                info.itemsize == sizeof(float) && info.ndim > 0 && info.shape[info.ndim - 1] >= 4)
                            {
                                float* data = (float*)info.ptr;
                                return py::cast(carb::Float4{ data[0], data[1], data[2], data[3] });
                            }
                        }
                        return py::none();
                    })
        .def("__str__",
             [](const carb::Float4& self) {
                 return "Quat(" + std::to_string(self.x) + ", " + std::to_string(self.y) + ", " +
                        std::to_string(self.z) + ", " + std::to_string(self.w) + ")";
             })
        /*
        .def("__mul__",
             [](const carb::Float4& self, const carb::Float4& other) {
                 Quat result = (const Quat&)self * (const Quat&)other;
                 return carb::Float4{ result.x, result.y, result.z, result.w };
             })
        .def("rotate",
             [](const carb::Float4& self, const carb::Float3& v) {
                 Vec3 result = Rotate((const Quat&)self, (const Vec3&)v);
                 return carb::Float3{ result.x, result.y, result.z };
             })
        .def("normalize",
             [](const carb::Float4& self) {
                 Quat result = Normalize((const Quat&)self);
                 return carb::Float4{ result.x, result.y, result.z, result.w };
             })
        .def("inverse",
             [](const carb::Float4& self) {
                 Quat result = Inverse((const Quat&)self);
                 return carb::Float4{ result.x, result.y, result.z, result.w };
             })
        .def_static("from_axis_angle",
                    [](const carb::Float3& axis, float angle) {
                        Quat result = QuatFromAxisAngle((const Vec3&)axis, angle);
                        return carb::Float4{ result.x, result.y, result.z, result.w };
                    })
        .def_static("from_rpy",
                    [](float roll, float pitch, float yaw) {
                        Quat result = QuatFromRollPitchYaw(roll, pitch, yaw);
                        return carb::Float4{ result.x, result.y, result.z, result.w };
                    })
        .def("to_rpy",
             [](const carb::Float4& self) {
                 float roll, pitch, yaw;
                 RollPitchYawFromQuat((const Quat&)self, roll, pitch, yaw);
                 return std::make_tuple(roll, pitch, yaw);
             })
        */
        .def(py::pickle(
            [](const carb::Float4& v) { return py::make_tuple(v.x, v.y, v.z, v.w); },
            [](py::tuple t) {
                return carb::Float4{ t[0].cast<float>(), t[1].cast<float>(), t[2].cast<float>(), t[3].cast<float>() };
            }));
#endif

    py::class_<DcTransform>(m, "Transform", "Represents a transform in the system")
        .def_readwrite("p", &DcTransform::p, "Position, in meters")
        .def_readwrite(
            "r", &DcTransform::r,
            R"pbdoc(Rotation Quaternion, represented in the format :math:`x\hat{i} + y\hat{j} + z\hat{k} + w`)pbdoc")
        .def("__init__",
             [](DcTransform& self, const carb::Float3* p, const carb::Float4* r) {
                 self.p = p ? *p : carb::Float3{ 0.0f, 0.0f, 0.0f };
                 self.r = r ? *r : carb::Float4{ 0.0f, 0.0f, 0.0f, 1.0f };
             },
             py::arg("p") = nullptr, py::arg("r") = nullptr)
        .def_property_readonly_static("dtype",
                                      [](const py::object&) {
                                          return py::dtype::of<DcTransform>(); // return the numpy structured dtype
                                      })
        .def_static("from_buffer",
                    [](py::buffer buf) -> py::object {
                        py::buffer_info info = buf.request();
                        if (info.ptr != nullptr)
                        {
                            if ((info.itemsize == 7 * sizeof(float)) ||
                                (info.itemsize == sizeof(float) && info.ndim > 0 && info.shape[info.ndim - 1] >= 7))
                            {
                                float* data = (float*)info.ptr;
                                DcTransform tx;
                                tx.p = carb::Float3{ data[0], data[1], data[2] };
                                tx.r = carb::Float4{ data[3], data[4], data[5], data[6] };
                                return py::cast(tx);
                            }
                        }
                        return py::none();
                    })
        /*
        .def("__mul__",
             [](const DcTransform& self, const DcTransform& other) {
                 DcTransform result;
                 (Transform&)result = (const Transform&)self * (const Transform&)other;
                 return result;
             })
        .def("inverse",
             [](const DcTransform& self) {
                 DcTransform result;
                 (Transform&)result = Inverse((const Transform&)self);
                 return result;
             },
             R"pbdoc(
                 Returns:
                    :obj:`carbongym.gymapi.Transform`: the inverse of this transform.
                )pbdoc")
        .def("transform_point",
             [](const DcTransform& self, const carb::Float3& v) {
                 Vec3 result = TransformPoint((const Transform&)self, (const Vec3&)v);
                 return carb::Float3{ result.x, result.y, result.z };
             },
             R"pbdoc(
                Rotates point by transform quatertnion and adds transform offset

                Args:
                    param1 (:obj:`carbongym.gymapi.Vec3`): Point to transform.

                Returns:
                    :obj:`carbongym.gymapi.Vec3`: The transformed point.
             )pbdoc")
        .def("transform_points",
             [](const DcTransform& self, py::array_t<carb::Float3, py::array::c_style> points) {
                 py::buffer_info info = points.request();
                 py::array_t<carb::Float3, py::array::c_style> result(info.shape);
                 const carb::Float3* src = points.data();
                 carb::Float3* dst = result.mutable_data();
                 for (int i = 0; i < points.size(); i++)
                 {
                     (Vec3&)dst[i] = TransformPoint((const Transform&)self, (const Vec3&)src[i]);
                 }
                 return result;
             },
             R"pbdoc(
                Rotates points by transform quatertnion and adds transform offset

                Args:
                    param1 (:obj:`numpy.ndarray` of :obj:`carbongym.gymapi.Vec3`): Points to transform.

                Returns:
                    numpy.ndarray[:obj:`carbongym.gymapi.Vec3`]: The transformed points.
             )pbdoc")
        .def("transform_vector",
             [](const DcTransform& self, const carb::Float3& v) {
                 Vec3 result = TransformVector((const Transform&)self, (const Vec3&)v);
                 return carb::Float3{ result.x, result.y, result.z };
             },
             R"pbdoc(
                Rotates vector by transform quatertnion

                Args:
                    param1 (:obj:`carbongym.gymapi.Vec3`): Vector to transform.

                Returns:
                    :obj:`carbongym.gymapi.Vec3`: The transformed vector.
             )pbdoc")
        .def("transform_vectors",
             [](const DcTransform& self, py::array_t<carb::Float3, py::array::c_style> vecs) {
                 py::buffer_info info = vecs.request();
                 py::array_t<carb::Float3, py::array::c_style> result(info.shape);
                 const carb::Float3* src = vecs.data();
                 carb::Float3* dst = result.mutable_data();
                 for (int i = 0; i < vecs.size(); i++)
                 {
                     (Vec3&)dst[i] = TransformVector((const Transform&)self, (const Vec3&)src[i]);
                 }
                 return result;
             },
             R"pbdoc(
                Rotates vectors by transform quatertnion

                Args:
                    param1 (:obj:`numpy.ndarray` of :obj:`carbongym.gymapi.Vec3`): Vectors to transform.

                Returns:
                    numpy.ndarray[:obj:`carbongym.gymapi.Vec3`]: The transformed vectors.
             )pbdoc")
        */
        .def(py::pickle(
            [](const DcTransform& tx) { return py::make_tuple(tx.p.x, tx.p.y, tx.p.z, tx.r.x, tx.r.y, tx.r.z, tx.r.w); },
            [](py::tuple t) {
                DcTransform tx;
                tx.p = { t[0].cast<float>(), t[1].cast<float>(), t[2].cast<float>() };
                tx.r = { t[3].cast<float>(), t[4].cast<float>(), t[5].cast<float>(), t[6].cast<float>() };
                return tx;
            }));

    py::class_<DcVelocity>(m, "Velocity", "Linear and angular velocity")
        .def_readwrite("linear", &DcVelocity::linear, "Linear velocity")
        .def_readwrite("angular", &DcVelocity::angular, "Angular velocity")
        .def("__init__",
             [](DcVelocity& self, const carb::Float3* linear, const carb::Float3* angular) {
                 self.linear = linear ? *linear : carb::Float3{ 0.0f, 0.0f, 0.0f };
                 self.angular = angular ? *linear : carb::Float3{ 0.0f, 0.0f, 0.0f };
             },
             py::arg("linear") = nullptr, py::arg("angular") = nullptr)
        .def_property_readonly_static("dtype",
                                      [](const py::object&) {
                                          // return the numpy structured dtype
                                          return py::dtype::of<DcVelocity>();
                                      })
        .def(py::pickle(
            [](const DcVelocity& v) {
                return py::make_tuple(v.linear.x, v.linear.y, v.linear.z, v.angular.x, v.angular.y, v.angular.z);
            },
            [](py::tuple t) {
                DcVelocity v;
                v.linear = { t[0].cast<float>(), t[1].cast<float>(), t[2].cast<float>() };
                v.angular = { t[3].cast<float>(), t[4].cast<float>(), t[5].cast<float>() };
                return v;
            }));

    py::class_<DcRigidBodyState>(m, "RigidBodyState", "Containing states to get/set for a rigid body in the simulation")
        .def_readwrite("pose", &DcRigidBodyState::pose, "Transform with position and orientation of rigid body")
        .def_readwrite("vel", &DcRigidBodyState::vel, "Linear and angular velocities of rigid body")
        .def("__init__",
             [](DcRigidBodyState& self, const DcTransform* pose, const DcVelocity* vel) {
                 self.pose = pose ? *pose : kTransformIdentity;
                 self.vel = vel ? *vel : kVelocityZero;
             },
             py::arg("pose") = nullptr, py::arg("vel") = nullptr)
        .def_property_readonly_static("dtype",
                                      [](const py::object&) {
                                          return py::dtype::of<DcRigidBodyState>(); // return the numpy structured dtype
                                      })
        .def(py::pickle(
            [](const DcRigidBodyState& s) {
                return py::make_tuple(s.pose.p.x, s.pose.p.y, s.pose.p.z, s.pose.r.x, s.pose.r.y, s.pose.r.z,
                                      s.pose.r.w, s.vel.linear.x, s.vel.linear.y, s.vel.linear.z, s.vel.angular.x,
                                      s.vel.angular.y, s.vel.angular.z);
            },
            [](py::tuple t) {
                DcRigidBodyState s;
                s.pose.p = { t[0].cast<float>(), t[1].cast<float>(), t[2].cast<float>() };
                s.pose.r = { t[3].cast<float>(), t[4].cast<float>(), t[5].cast<float>(), t[6].cast<float>() };
                s.vel.linear = { t[7].cast<float>(), t[8].cast<float>(), t[9].cast<float>() };
                s.vel.angular = { t[10].cast<float>(), t[11].cast<float>(), t[12].cast<float>() };
                return s;
            }));

    py::class_<DcDofState>(m, "DofState", "States of a Degree of Freedom in the Asset architecture")
        .def_readwrite("pos", &DcDofState::pos,
                       "DOF position, in radians if it's a revolute DOF, or meters, if it's a prismatic DOF")
        .def_readwrite("vel", &DcDofState::vel,
                       "DOF velocity, in radians/s if it's a revolute DOF, or m/s, if it's a prismatic DOF")
        .def("__init__",
             [](DcDofState& self, const float* pos, const float* vel) {
                 self.pos = pos ? *pos : 0.0f;
                 self.vel = vel ? *vel : 0.0f;
             },
             py::arg("pos") = nullptr, py::arg("vel") = nullptr)
        .def_property_readonly_static("dtype",
                                      [](const py::object&) {
                                          return py::dtype::of<DcDofState>(); // return the numpy structured dtype
                                      })
        .def(py::pickle([](const DcDofState& s) { return py::make_tuple(s.pos, s.vel); },
                        [](py::tuple t) {
                            return DcDofState{ t[0].cast<float>(), t[1].cast<float>() };
                        }));

    py::class_<DcDofProperties>(m, "DofProperties")
        .def(py::init<>())
        //.def_readonly("type", &DcDofProperties::type)
        .def_readwrite("type", &DcDofProperties::type)
        .def_readwrite("has_limits", &DcDofProperties::hasLimits)
        .def_readwrite("lower", &DcDofProperties::lower)
        .def_readwrite("upper", &DcDofProperties::upper)
        .def_readwrite("drive_mode", &DcDofProperties::driveMode)
        .def_readwrite("max_velocity", &DcDofProperties::maxVelocity)
        .def_readwrite("max_effort", &DcDofProperties::maxEffort)
        .def_readwrite("stiffness", &DcDofProperties::stiffness)
        .def_readwrite("damping", &DcDofProperties::damping)
        .def(py::pickle(
            [](const DcDofProperties& props) {
                return py::make_tuple(props.type, props.hasLimits, props.lower, props.upper, props.driveMode,
                                      props.maxVelocity, props.maxEffort, props.stiffness, props.damping);
            },
            [](py::tuple t) {
                DcDofProperties props;
                props.type = t[0].cast<DcDofType>();
                props.hasLimits = t[1].cast<bool>();
                props.lower = t[2].cast<float>();
                props.upper = t[3].cast<float>();
                props.driveMode = t[4].cast<DcDriveMode>();
                props.maxVelocity = t[5].cast<float>();
                props.maxEffort = t[6].cast<float>();
                props.stiffness = t[7].cast<float>();
                props.damping = t[8].cast<float>();
                return props;
            }));

    py::class_<DcAttractorProperties>(
        m, "AttractorProperties",
        "The Attractor is used to pull a rigid body towards a pose. Each pose axis can be individually selected.")
        .def(py::init<>())
        .def_readwrite("body", &DcAttractorProperties::rigidBody, "Rigid body to set the attractor to")
        .def_readwrite(
            "axes", &DcAttractorProperties::axes,
            "Axes to set the attractor, using DcAxisFlags. Multiple axes can be selected using bitwise combination of each axis flag. if axis flag is set to zero, the attractor will be disabled and won't impact in solver computational complexity.")
        .def_readwrite("target", &DcAttractorProperties::target, "Target pose to attract to.")
        .def_readwrite(
            "offset", &DcAttractorProperties::offset, "Offset from rigid body origin to set the attractor pose.")
        .def_readwrite(
            "stiffness", &DcAttractorProperties::stiffness,
            "Stiffness to be used on attraction for solver. Stiffness value should be larger than the largest agent kinematic chain stifness")
        .def_readwrite("damping", &DcAttractorProperties::damping, "Damping to be used on attraction solver.")
        .def_readwrite("force_limit", &DcAttractorProperties::forceLimit, "Maximum force to be applied by drive.")
        .def(py::pickle(
            [](const DcAttractorProperties& props) {
                return py::make_tuple(props.rigidBody, props.axes, props.target.p.x, props.target.p.y, props.target.p.z,
                                      props.target.r.x, props.target.r.y, props.target.r.z, props.target.r.w,
                                      props.offset.p.x, props.offset.p.y, props.offset.p.z, props.offset.r.x,
                                      props.offset.r.y, props.offset.r.z, props.offset.r.w, props.stiffness,
                                      props.damping, props.forceLimit);
            },
            [](py::tuple t) {
                DcAttractorProperties props;
                props.rigidBody = t[0].cast<DcHandle>();
                props.axes = t[1].cast<DcAxisFlags>();
                props.target.p = { t[2].cast<float>(), t[3].cast<float>(), t[4].cast<float>() };
                props.target.r = { t[5].cast<float>(), t[6].cast<float>(), t[7].cast<float>(), t[8].cast<float>() };
                props.offset.p = { t[9].cast<float>(), t[10].cast<float>(), t[11].cast<float>() };
                props.offset.r = { t[12].cast<float>(), t[13].cast<float>(), t[14].cast<float>(), t[15].cast<float>() };
                props.stiffness = t[16].cast<float>();
                props.damping = t[17].cast<float>();
                props.forceLimit = t[18].cast<float>();
                return props;
            }));


    py::class_<DcD6JointProperties>(m, "D6JointProperties", "Creates  a general D6 Joint between two rigid Bodies.")
        .def(py::init<>())
        .def_readwrite("name", &DcD6JointProperties::name, "Joint Name")
        .def_readwrite("body0", &DcD6JointProperties::body0, "parent body")
        .def_readwrite("body1", &DcD6JointProperties::body1, "parent body")
        .def_readwrite(
            "axes", &DcD6JointProperties::axes,
            "Axes to set the attractor, using DcAxisFlags. Multiple axes can be selected using bitwise combination of each axis flag. if axis flag is set to zero, the attractor will be disabled and won't impact in solver computational complexity.")
        .def_readwrite("pose0", &DcD6JointProperties::pose0, "Transform from body 0 to joint.")
        .def_readwrite("pose1", &DcD6JointProperties::pose1, "Transform from body 1 to joint.")
        .def_readwrite("stiffness", &DcD6JointProperties::stiffness,
                       "Joint Stiffness. Stiffness value should be larger than the largest agent kinematic chain stifness")
        .def_readwrite("damping", &DcD6JointProperties::damping, "Joint Damping.")
        .def_readwrite("force_limit", &DcD6JointProperties::forceLimit, "Maximum force to be applied by drive.")
        .def(py::pickle(
            [](const DcD6JointProperties& props) {
                return py::make_tuple(props.name, props.body0, props.body1, props.axes, props.pose0.p.x,
                                      props.pose0.p.y, props.pose0.p.z, props.pose0.r.x, props.pose0.r.y,
                                      props.pose0.r.z, props.pose0.r.w, props.pose1.p.x, props.pose1.p.y,
                                      props.pose1.p.z, props.pose1.r.x, props.pose1.r.y, props.pose1.r.z,
                                      props.pose1.r.w, props.stiffness, props.damping, props.forceLimit);
            },
            [](py::tuple t) {
                DcD6JointProperties props;
                std::string str = t[0].cast<std::string>().c_str();
                std::vector<char> cstr(str.c_str(), str.c_str() + str.size() + 1);
                props.name = cstr.data();
                props.body0 = t[1].cast<DcHandle>();
                props.body1 = t[2].cast<DcHandle>();
                props.axes = t[3].cast<DcAxisFlags>();
                props.pose0.p = { t[4].cast<float>(), t[5].cast<float>(), t[6].cast<float>() };
                props.pose0.r = { t[7].cast<float>(), t[8].cast<float>(), t[9].cast<float>(), t[10].cast<float>() };
                props.pose1.p = { t[11].cast<float>(), t[12].cast<float>(), t[13].cast<float>() };
                props.pose1.r = { t[14].cast<float>(), t[15].cast<float>(), t[16].cast<float>(), t[17].cast<float>() };
                props.stiffness = t[18].cast<float>();
                props.damping = t[19].cast<float>();
                props.forceLimit = t[20].cast<float>();
                return props;
            }));

    // numpy dtypes
    PYBIND11_NUMPY_DTYPE(carb::Float2, x, y);
    PYBIND11_NUMPY_DTYPE(carb::Float3, x, y, z);
    PYBIND11_NUMPY_DTYPE(carb::Float4, x, y, z, w);
    PYBIND11_NUMPY_DTYPE(DcTransform, p, r);
    PYBIND11_NUMPY_DTYPE(DcVelocity, linear, angular);
    PYBIND11_NUMPY_DTYPE(DcRigidBodyState, pose, vel);
    PYBIND11_NUMPY_DTYPE(DcDofState, pos, vel);
    PYBIND11_NUMPY_DTYPE(
        DcDofProperties, type, hasLimits, lower, upper, driveMode, maxVelocity, maxEffort, stiffness, damping);

    defineInterfaceClass<DynamicControl>(
        m, "DynamicControl", "acquire_dynamic_control_interface", "release_dynamic_control_interface")

        .def("hello", wrapInterfaceFunction(&DynamicControl::hello))

        //.def("create_context", wrapInterfaceFunction(&DynamicControl::createContext),
        // py::return_value_policy::reference) .def("destroy_context",
        // wrapInterfaceFunction(&DynamicControl::destroyContext)) .def("update_context",
        // wrapInterfaceFunction(&DynamicControl::updateContext))

        .def("get_rigid_body", wrapInterfaceFunction(&DynamicControl::getRigidBody))
        .def("get_joint", wrapInterfaceFunction(&DynamicControl::getJoint))
        .def("get_dof", wrapInterfaceFunction(&DynamicControl::getDof))
        .def("get_articulation", wrapInterfaceFunction(&DynamicControl::getArticulation))
        .def("get_d6_joint", wrapInterfaceFunction(&DynamicControl::getD6Joint))

        .def("get_object", wrapInterfaceFunction(&DynamicControl::getObject))
        .def("get_object_type", wrapInterfaceFunction(&DynamicControl::getObjectType))
        .def("get_object_type_name", wrapInterfaceFunction(&DynamicControl::getObjectTypeName),
             py::return_value_policy::reference)
        .def("peek_object_type", wrapInterfaceFunction(&DynamicControl::peekObjectType))

        .def("wake_up_rigid_body", wrapInterfaceFunction(&DynamicControl::wakeUpRigidBody))
        .def("wake_up_articulation", wrapInterfaceFunction(&DynamicControl::wakeUpArticulation))

        .def("get_articulation_name", wrapInterfaceFunction(&DynamicControl::getArticulationName),
             py::return_value_policy::reference)
        .def("get_articulation_path", wrapInterfaceFunction(&DynamicControl::getArticulationPath),
             py::return_value_policy::reference)

        .def("get_articulation_body_count", wrapInterfaceFunction(&DynamicControl::getArticulationBodyCount))
        .def("get_articulation_body", wrapInterfaceFunction(&DynamicControl::getArticulationBody))
        .def("find_articulation_body", wrapInterfaceFunction(&DynamicControl::findArticulationBody))
        .def("find_articulation_body_index", wrapInterfaceFunction(&DynamicControl::findArticulationBodyIndex))
        .def("get_articulation_root_body", wrapInterfaceFunction(&DynamicControl::getArticulationRootBody))

        .def("get_articulation_body_states",
             [](const DynamicControl* dc, DcHandle artHandle, DcStateFlags flags) -> py::object {
                 if (dc)
                 {
                     int numBodies = dc->getArticulationBodyCount(artHandle);
                     DcRigidBodyState* states = dc->getArticulationBodyStates(artHandle, flags);
                     if (numBodies > 0 && states != nullptr)
                     {
                         auto capsule = py::capsule(states, [](void*) {}); // avoid copy
                         return py::array_t<DcRigidBodyState, py::array::c_style>(numBodies, states, capsule);
                     }
                 }
                 return py::none();
             })

        .def("set_articulation_body_states",
             [](const DynamicControl* dc, DcHandle artHandle,
                const py::array_t<DcRigidBodyState, py::array::c_style>& states, DcStateFlags flags) {
                 if (dc)
                 {
                     if (states.size() >= ssize_t(dc->getArticulationBodyCount(artHandle)))
                     {
                         return dc->setArticulationBodyStates(artHandle, states.data(), flags);
                     }
                 }
                 return false;
             })

        .def("get_articulation_joint_count", wrapInterfaceFunction(&DynamicControl::getArticulationJointCount))
        .def("get_articulation_joint", wrapInterfaceFunction(&DynamicControl::getArticulationJoint))
        .def("find_articulation_joint", wrapInterfaceFunction(&DynamicControl::findArticulationJoint))

        .def("get_articulation_dof_count", wrapInterfaceFunction(&DynamicControl::getArticulationDofCount))
        .def("get_articulation_dof", wrapInterfaceFunction(&DynamicControl::getArticulationDof),
             py::return_value_policy::reference)
        .def("find_articulation_dof", wrapInterfaceFunction(&DynamicControl::findArticulationDof),
             py::return_value_policy::reference)
        .def("find_articulation_dof_index", wrapInterfaceFunction(&DynamicControl::findArticulationDofIndex))

        .def("get_articulation_dof_properties",
             [](const DynamicControl* dc, DcHandle artHandle) -> py::object {
                 if (dc)
                 {
                     int numDofs = dc->getArticulationDofCount(artHandle);
                     if (numDofs > 0)
                     {
                         auto arr = py::array_t<DcDofProperties, py::array::c_style>(numDofs);
                         if (dc->getArticulationDofProperties(artHandle, arr.mutable_data()))
                         {
                             return arr;
                         }
                     }
                 }
                 return py::none();
             })

        .def("set_articulation_dof_properties",
             [](const DynamicControl* dc, DcHandle artHandle,
                const py::array_t<DcDofProperties, py::array::c_style>& props) {
                 if (dc)
                 {
                     if (props.size() >= ssize_t(dc->getArticulationDofCount(artHandle)))
                     {
                         return dc->setArticulationDofProperties(artHandle, props.data());
                     }
                 }
                 return false;
             })

        .def("get_articulation_dof_states",
             [](const DynamicControl* dc, DcHandle artHandle, DcStateFlags flags) -> py::object {
                 if (dc)
                 {
                     int numDofs = dc->getArticulationDofCount(artHandle);
                     if (numDofs > 0)
                     {
                         DcDofState* states = dc->getArticulationDofStates(artHandle, flags);
                         if (states != nullptr)
                         {
                             auto capsule = py::capsule(states, [](void*) {}); // avoid copy
                             return py::array_t<DcDofState, py::array::c_style>(numDofs, states, capsule);
                         }
                     }
                 }
                 return py::none();
             })

        .def("get_articulation_dof_state_derivatives",
             [](const DynamicControl* dc, DcHandle artHandle, const py::array_t<DcDofState, py::array::c_style>& states,
                const py::array_t<float, py::array::c_style>& efforts) -> py::object {
                 if (dc)
                 {
                     const ssize_t numDofs{ static_cast<ssize_t>(dc->getArticulationDofCount(artHandle)) };
                     // check input dims
                     if (states.size() >= numDofs && efforts.size() >= numDofs)
                     {
                         DcDofState* stateDeriv =
                             dc->getArticulationDofStateDerivatives(artHandle, states.data(), efforts.data());
                         if (stateDeriv != nullptr)
                         {
                             auto capsule = py::capsule(stateDeriv, [](void*) {}); // avoid copy
                             return py::array_t<DcDofState, py::array::c_style>(numDofs, stateDeriv, capsule);
                         }
                     }
                 }
                 return py::none();
             })

        .def("set_articulation_dof_states",
             [](const DynamicControl* dc, DcHandle artHandle, const py::array_t<DcDofState, py::array::c_style>& states,
                DcStateFlags flags) {
                 if (dc)
                 {
                     if (states.size() >= ssize_t(dc->getArticulationDofCount(artHandle)))
                     {
                         return dc->setArticulationDofStates(artHandle, states.data(), flags);
                     }
                 }
                 return false;
             })

        .def("set_articulation_dof_position_targets",
             [](const DynamicControl* dc, DcHandle artHandle, const py::array_t<float, py::array::c_style>& targets) {
                 if (dc)
                 {
                     if (targets.size() >= ssize_t(dc->getArticulationDofCount(artHandle)))
                     {
                         return dc->setArticulationDofPositionTargets(artHandle, targets.data());
                     }
                 }
                 return false;
             })

        .def("set_articulation_dof_velocity_targets",
             [](const DynamicControl* dc, DcHandle artHandle, const py::array_t<float, py::array::c_style>& targets) {
                 if (dc)
                 {
                     if (targets.size() >= ssize_t(dc->getArticulationDofCount(artHandle)))
                     {
                         return dc->setArticulationDofVelocityTargets(artHandle, targets.data());
                     }
                 }
                 return false;
             })

        .def("apply_articulation_dof_efforts",
             [](const DynamicControl* dc, DcHandle artHandle, const py::array_t<float, py::array::c_style>& efforts) {
                 if (dc)
                 {
                     if (efforts.size() >= ssize_t(dc->getArticulationDofCount(artHandle)))
                     {
                         return dc->applyArticulationDofEfforts(artHandle, efforts.data());
                     }
                 }
                 return false;
             })

        // rigid bodies

        .def("get_rigid_body_name", wrapInterfaceFunction(&DynamicControl::getRigidBodyName),
             py::return_value_policy::reference)
        .def("get_rigid_body_path", wrapInterfaceFunction(&DynamicControl::getRigidBodyPath),
             py::return_value_policy::reference)
        .def("get_rigid_body_parent_joint", wrapInterfaceFunction(&DynamicControl::getRigidBodyParentJoint))
        .def("get_rigid_body_child_joint_count", wrapInterfaceFunction(&DynamicControl::getRigidBodyChildJointCount))
        .def("get_rigid_body_child_joint", wrapInterfaceFunction(&DynamicControl::getRigidBodyChildJoint))
        .def("get_rigid_body_pose", wrapInterfaceFunction(&DynamicControl::getRigidBodyPose))
        .def("set_rigid_body_pose", wrapInterfaceFunction(&DynamicControl::setRigidBodyPose))
        .def("set_rigid_body_disable_gravity", wrapInterfaceFunction(&DynamicControl::setRigidBodyDisableGravity))
        .def("set_rigid_body_disable_simulation", wrapInterfaceFunction(&DynamicControl::setRigidBodyDisableSimulation))
        .def("get_rigid_body_linear_velocity", wrapInterfaceFunction(&DynamicControl::getRigidBodyLinearVelocity))
        .def("set_rigid_body_linear_velocity", wrapInterfaceFunction(&DynamicControl::setRigidBodyLinearVelocity))
        .def("get_rigid_body_angular_velocity", wrapInterfaceFunction(&DynamicControl::getRigidBodyAngularVelocity))
        .def("set_rigid_body_angular_velocity", wrapInterfaceFunction(&DynamicControl::setRigidBodyAngularVelocity))
        .def("apply_body_force", wrapInterfaceFunction(&DynamicControl::applyBodyForce))
        .def("get_relative_body_poses",
             [](const DynamicControl* dc, DcHandle parentHandle, const std::vector<DcHandle>& bodyHandles) {
                 const size_t numBodies = bodyHandles.size();
                 std::vector<DcTransform> outputTransforms(numBodies);
                 dc->getRelativeBodyPoses(parentHandle, numBodies, bodyHandles.data(), outputTransforms.data());
                 return outputTransforms;
             })

        // joints

        .def("get_joint_name", wrapInterfaceFunction(&DynamicControl::getJointName), py::return_value_policy::reference)
        .def("get_joint_path", wrapInterfaceFunction(&DynamicControl::getJointPath), py::return_value_policy::reference)
        .def("get_joint_type", wrapInterfaceFunction(&DynamicControl::getJointType))
        .def("get_joint_dof_count", wrapInterfaceFunction(&DynamicControl::getJointDofCount))
        .def("get_joint_dof", wrapInterfaceFunction(&DynamicControl::getJointDof))
        .def("get_joint_parent_body", wrapInterfaceFunction(&DynamicControl::getJointParentBody))
        .def("get_joint_child_body", wrapInterfaceFunction(&DynamicControl::getJointChildBody))

        // dofs

        .def("get_dof_name", wrapInterfaceFunction(&DynamicControl::getDofName), py::return_value_policy::reference)
        .def("get_dof_path", wrapInterfaceFunction(&DynamicControl::getDofPath), py::return_value_policy::reference)
        .def("get_dof_type", wrapInterfaceFunction(&DynamicControl::getDofType))
        .def("get_dof_joint", wrapInterfaceFunction(&DynamicControl::getDofJoint))
        .def("get_dof_parent_body", wrapInterfaceFunction(&DynamicControl::getDofParentBody))
        .def("get_dof_child_body", wrapInterfaceFunction(&DynamicControl::getDofChildBody))
        .def("get_dof_state", wrapInterfaceFunction(&DynamicControl::getDofState))
        .def("set_dof_state", wrapInterfaceFunction(&DynamicControl::setDofState))
        .def("get_dof_position", wrapInterfaceFunction(&DynamicControl::getDofPosition))
        .def("set_dof_position", wrapInterfaceFunction(&DynamicControl::setDofPosition))
        .def("get_dof_velocity", wrapInterfaceFunction(&DynamicControl::getDofVelocity))
        .def("set_dof_velocity", wrapInterfaceFunction(&DynamicControl::setDofVelocity))
        .def("get_dof_properties", wrapInterfaceFunction(&DynamicControl::getDofProperties))
        .def("set_dof_properties", wrapInterfaceFunction(&DynamicControl::setDofProperties))
        .def("set_dof_position_target", wrapInterfaceFunction(&DynamicControl::setDofPositionTarget))
        .def("set_dof_velocity_target", wrapInterfaceFunction(&DynamicControl::setDofVelocityTarget))
        .def("apply_dof_effort", wrapInterfaceFunction(&DynamicControl::applyDofEffort))

        // attractors

        .def("create_rigid_body_attractor", wrapInterfaceFunction(&DynamicControl::createRigidBodyAttractor),
             py::return_value_policy::reference)
        .def("destroy_rigid_body_attractor", wrapInterfaceFunction(&DynamicControl::destroyRigidBodyAttractor))
        .def("set_attractor_properties", wrapInterfaceFunction(&DynamicControl::setAttractorProperties))
        .def("set_attractor_target", wrapInterfaceFunction(&DynamicControl::setAttractorTarget))
        .def("get_attractor_properties",
             [](const DynamicControl* dc, DcHandle attHandle) -> py::object {
                 if (dc)
                 {
                     DcAttractorProperties props;
                     if (dc->getAttractorProperties(attHandle, &props))
                     {
                         return py::cast(props);
                     }
                 }
                 return py::none();
             })

        .def("create_d6_joint", wrapInterfaceFunction(&DynamicControl::createD6Joint), py::return_value_policy::reference)
        .def("destroy_d6_joint", wrapInterfaceFunction(&DynamicControl::destroyD6Joint))
        .def("set_d6_joint_properties", wrapInterfaceFunction(&DynamicControl::setD6JointProperties))

        .def("set_origin_offset", wrapInterfaceFunction(&DynamicControl::setOriginOffset))

        ;
}
}
