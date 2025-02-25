// Copyright (c) 2021-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <carb/BindingsPythonUtils.h>

#include <isaacsim/robot/surface_gripper/SurfaceGripper.h>


CARB_BINDINGS("isaacsim.robot.surface_gripper.python")

namespace isaacsim
{
namespace robot
{
namespace surface_gripper
{
} // namespace surface_gripper
} // namespace robot
} // namespace isaacsim

namespace
{

namespace py = pybind11;

PYBIND11_MODULE(_surface_gripper, m)
{
    using namespace carb;
    using namespace isaacsim::robot::surface_gripper;
    // We use carb data types, must import bindings for them
    auto carbModule = py::module::import("carb");


    m.doc() =
        R"pbdoc( 

        Surface Grippers
        -----------------

        This submodule provides a Helper to create a breakable joint using a PhysxD6Joint. 
        The surface gripper is useful to approximate suction style grippers.
        
        Example:
            To create a surface gripper you need to import this submodule, create a Surface_Gripper_Properties, and then create a Surface Gripper:

            .. code-block:: python

                from isaacsim.robot.surface_gripper._surface_gripper import Surface_Gripper
                from isaacsim.robot.surface_gripper._surface_gripper import Surface_Gripper_Properties
                import numpy as np

                # Create surface gripper
                surface_gripper = Surface_Gripper()
                sgp = Surface_Gripper_Properties()

                # Configure the Gripper Properties here (Example configuration below)
                sgp.d6JointPath = ""
                sgp.parentPath = "/GripperCone"
                sgp.offset = _dc.Transform()
                sgp.offset.p.x = 0
                sgp.offset.p.z = -30.01
                sgp.offset.r = [0, 0.7171, 0, 0.7171]  # Rotate to point gripper in Z direction
                sgp.gripThreshold = 2
                sgp.forceLimit = 1.0e4
                sgp.torqueLimit = 1.0e5
                sgp.bendAngle = np.pi / 4
                sgp.stiffness = 1.0e4
                sgp.damping = 1.0e3

                # Initialize the gripper with the properties
                surface_gripper.initialize(sgp)


        Then, on every simulation step, the gripper must be updated to check if the joint has been broken due to external forces, and update its status, by calling the ``gripper.update()`` method.

        In order to grip an object, the user should call ``gripper.close()``, which will return whether it was successful at gripping something.

        If you want to check if the gripper is holding an object, you can use the method ``gripper.is_closed()``, which returns its status.

        To release the gripped object, call ``gripper.release()``
        
        )pbdoc";

    py::class_<SurfaceGripperProperties>(
        m, "Surface_Gripper_Properties", R"pbdoc(Properties for the Surface Gripper)pbdoc")
        .def(py::init<>())
        .def_readwrite(
            "d6JointPath", &SurfaceGripperProperties::d6JointPath, R"pbdoc(USD path to joint (:obj:`str`))pbdoc")
        .def_readwrite(
            "parentPath", &SurfaceGripperProperties::parentPath, R"pbdoc(USD Path to parent body (:obj:`str`))pbdoc")
        .def_readwrite("offset", &SurfaceGripperProperties::offset,
                       R"pbdoc(Transform from parent body to joint (:obj:`omni.physics.tensors.Transform`))pbdoc")
        .def_readwrite("gripThreshold", &SurfaceGripperProperties::gripThreshold,
                       R"pbdoc(Threshold distance the gripper will respond to closing (:obj:`float`))pbdoc")
        .def_readwrite(
            "forceLimit", &SurfaceGripperProperties::forceLimit, R"pbdoc(Force Breaking limit (:obj:`float`))pbdoc")
        .def_readwrite(
            "torqueLimit", &SurfaceGripperProperties::torqueLimit, R"pbdoc(Torque Breaking limit (:obj:`float`))pbdoc")
        .def_readwrite("bendAngle", &SurfaceGripperProperties::bendAngle,
                       R"pbdoc(maximum bend angle for the gripper(:obj:`float`))pbdoc")
        .def_readwrite("stiffness", &SurfaceGripperProperties::stiffness, R"pbdoc(Gripper Stiffness(:obj:`float`))pbdoc")
        .def_readwrite("damping", &SurfaceGripperProperties::damping, R"pbdoc(Gripper Damping(:obj:`float`))pbdoc")
        .def_readwrite("disableGravity", &SurfaceGripperProperties::disableGravity,
                       R"pbdoc(Flag to disable gravity on selected object to compensate for its mass(:obj:`bool`))pbdoc")
        .def_readwrite(
            "retryClose", &SurfaceGripperProperties::retryClose,
            R"pbdoc(Flag to indicate if gripper should keep attempting to close until it grips some object(:obj:`bool`))pbdoc")

        .def(py::pickle(
            [](const SurfaceGripperProperties& props)
            {
                return py::make_tuple(props.d6JointPath, props.parentPath, props.offset.p.x, props.offset.p.y,
                                      props.offset.p.z, props.offset.r.x, props.offset.r.y, props.offset.r.z,
                                      props.offset.r.w, props.gripThreshold, props.forceLimit, props.torqueLimit,
                                      props.bendAngle, props.stiffness, props.damping, props.disableGravity);
            },
            [](py::tuple t)
            {
                SurfaceGripperProperties props;
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

    auto surfaceGripper = py::class_<SurfaceGripper>(m, "Surface_Gripper")
                              .def(py::init([]() { return new SurfaceGripper(); }),
                                   R"pbdoc(
                Creates a Surface Gripper helper for suction-style object manipulation

                The surface gripper creates and manages breakable joints between rigid bodies
                when activated. Requires proper initialization before use.
                )pbdoc")
                              .def("initialize", &SurfaceGripper::initialize,
                                   R"pbdoc(
                Configure the gripper with specified properties

                Args:
                    properties: Surface_Gripper_Properties containing configuration parameters

                Returns:
                    bool: True if initialization succeeded, False otherwise
                )pbdoc")
                              .def("close", &SurfaceGripper::close,
                                   R"pbdoc(
                Attempt to grip nearby objects within threshold distance

                Returns: 
                    bool: True if successfully closed and attached to an object,
                          False if no valid target found
                )pbdoc")
                              .def("open", &SurfaceGripper::open,
                                   R"pbdoc(
                Release any attached object and reset gripper state

                Returns:
                    bool: True if gripper was closed and released successfully,
                          False if already open or not initialized
                )pbdoc")
                              .def("update", &SurfaceGripper::update,
                                   R"pbdoc(
                Update gripper state (must be called regularly during simulation)

                Checks for broken joints and handles automatic retry logic when enabled.
                Should be called every simulation step for proper operation.
                )pbdoc")
                              .def("is_attempting_close", &SurfaceGripper::isAttemptingClose,
                                   R"pbdoc(
                Check if gripper is in retry mode attempting to find targets

                Returns:
                    bool: True if gripper is actively searching for attachable objects,
                          False if in idle state
                )pbdoc")
                              .def("is_closed", &SurfaceGripper::isClosed,
                                   R"pbdoc(
                Check current gripper closure status

                Returns:
                    bool: True if gripper is actively maintaining a joint connection,
                          False otherwise
                )pbdoc");
}
}
