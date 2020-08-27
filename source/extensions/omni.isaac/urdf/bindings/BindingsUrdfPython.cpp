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
#include <pybind11/pybind11/stl.h>
#include <pybind11/pybind11/stl_bind.h>

CARB_BINDINGS("omni.isaac.urdf.python")
PYBIND11_MAKE_OPAQUE(std::map<std::string, omni::isaac::urdf::UrdfMaterial>);

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
// Helper function that creates a python type for a std::map with a string key and a custom value type
template <class T>
void declare_map(py::module& m, const std::string typestr)
{
    py::class_<std::map<std::string, T>>(m, typestr.c_str())
        .def(py::init<>())
        .def("__getitem__",
             [](const std::map<std::string, T>& map, std::string key) {
                 try
                 {
                     return map.at(key);
                 }
                 catch (const std::out_of_range&)
                 {
                     throw py::key_error("key '" + key + "' does not exist");
                 }
             })
        .def("__iter__",
             [](std::map<std::string, T>& items) { return py::make_key_iterator(items.begin(), items.end()); },
             py::keep_alive<0, 1>())

        .def("items", [](std::map<std::string, T>& items) { return py::make_iterator(items.begin(), items.end()); },
             py::keep_alive<0, 1>())
        .def("__len__", [](std::map<std::string, T>& items) { return items.size(); });
}

PYBIND11_MODULE(_urdf, m)
{
    using namespace carb;
    using namespace omni::isaac::urdf;

    m.doc() = "Isaac URDF Utils bindings";


    py::class_<ImportConfig>(m, "ImportConfig")
        .def(py::init<>())
        .def_readwrite("merge_fixed_joints", &ImportConfig::mergeFixedJoints,
                       "Consolidating links that are connected by fixed joints")
        .def_readwrite("convex_decomp", &ImportConfig::convexDecomp,
                       "Decompose a convex mesh into smaller pieces for a closer fit")
        .def_readwrite("import_inertia_tensor", &ImportConfig::importInertiaTensor,
                       "Import inertia tensor from urdf, if not specified in urdf it will import as identity")
        .def_readwrite("fix_base", &ImportConfig::fixBase, "Create fix joint for base link")
        .def_readwrite("self_collision", &ImportConfig::selfCollision, "Self collisions between links in the articulation")
        .def_readwrite("density", &ImportConfig::density, "default density used for links")
        .def_readwrite("default_drive_type", &ImportConfig::defaultDriveType, "default drive type used for joints")
        .def_readwrite(
            "default_drive_stiffness", &ImportConfig::defaultDriveStiffness, "default drive stiffness used for joints")
        .def_readwrite("distance_scale", &ImportConfig::distanceScale,
                       "Set the unit scaling factor, 1.0 means meters, 100.0 means cm")
        .def_readwrite("up_vector", &ImportConfig::upVector, "Up vector used for import")
        .def_readwrite(
            "create_physics_scene", &ImportConfig::createPhysicsScene, "add a physics scene to the stage on import")
        .def_readwrite("make_default_prim", &ImportConfig::makeDefaultPrim, "set imported robot as default prim")
        // setters for each property
        .def("set_merge_fixed_joints", [](ImportConfig& config, const bool value) { config.mergeFixedJoints = value; })
        .def("set_convex_decomp", [](ImportConfig& config, const bool value) { config.convexDecomp = value; })
        .def("set_import_inertia_tensor",
             [](ImportConfig& config, const bool value) { config.importInertiaTensor = value; })
        .def("set_fix_base", [](ImportConfig& config, const bool value) { config.fixBase = value; })
        .def("set_self_collision", [](ImportConfig& config, const bool value) { config.selfCollision = value; })
        .def("set_density", [](ImportConfig& config, const float value) { config.density = value; })
        .def("set_default_drive_type",
             [](ImportConfig& config, const int value) {
                 config.defaultDriveType = static_cast<UrdfJointTargetType>(value);
             })
        .def("set_default_drive_stiffness",
             [](ImportConfig& config, const float value) { config.defaultDriveStiffness = value; })
        .def("set_distance_scale", [](ImportConfig& config, const float value) { config.distanceScale = value; })
        .def("set_up_vector",
             [](ImportConfig& config, const float x, const float y, const float z) {
                 config.upVector = { x, y, z };
             })
        .def("set_create_physics_scene",
             [](ImportConfig& config, const bool value) { config.createPhysicsScene = value; })
        .def("set_make_default_prim", [](ImportConfig& config, const bool value) { config.makeDefaultPrim = value; });

    py::class_<UrdfOrigin>(m, "UrdfOrigin", "")
        .def_readwrite("x", &UrdfOrigin::x, "")
        .def_readwrite("y", &UrdfOrigin::y, "")
        .def_readwrite("z", &UrdfOrigin::z, "")
        .def_readwrite("roll", &UrdfOrigin::roll, "")
        .def_readwrite("pitch", &UrdfOrigin::pitch, "")
        .def_readwrite("yaw", &UrdfOrigin::yaw, "")
        .def(py::init<>());

    py::class_<UrdfInertia>(m, "UrdfInertia", "")
        .def_readwrite("ixx", &UrdfInertia::ixx, "")
        .def_readwrite("ixy", &UrdfInertia::ixy, "")
        .def_readwrite("ixz", &UrdfInertia::ixz, "")
        .def_readwrite("iyy", &UrdfInertia::iyy, "")
        .def_readwrite("iyz", &UrdfInertia::iyz, "")
        .def_readwrite("izz", &UrdfInertia::izz, "")
        .def(py::init<>());

    py::class_<UrdfInertial>(m, "UrdfInertial", "")
        .def_readwrite("origin", &UrdfInertial::origin, "")
        .def_readwrite("mass", &UrdfInertial::mass, "")
        .def_readwrite("inertia", &UrdfInertial::inertia, "")
        .def_readwrite("has_origin", &UrdfInertial::hasOrigin, "")
        .def_readwrite("has_mass", &UrdfInertial::hasMass, "")
        .def_readwrite("has_inertia", &UrdfInertial::hasInertia, "")
        .def(py::init<>());

    py::class_<UrdfAxis>(m, "UrdfAxis", "")
        .def_readwrite("x", &UrdfAxis::x, "")
        .def_readwrite("y", &UrdfAxis::y, "")
        .def_readwrite("z", &UrdfAxis::z, "")
        .def(py::init<>());

    py::class_<UrdfColor>(m, "UrdfColor", "")
        .def_readwrite("r", &UrdfColor::r, "")
        .def_readwrite("g", &UrdfColor::g, "")
        .def_readwrite("b", &UrdfColor::b, "")
        .def_readwrite("a", &UrdfColor::a, "")
        .def(py::init<>());

    py::enum_<UrdfJointType>(m, "UrdfJointType", py::arithmetic(), "")
        .value("JOINT_REVOLUTE", UrdfJointType::REVOLUTE)
        .value("JOINT_CONTINUOUS", UrdfJointType::CONTINUOUS)
        .value("JOINT_PRISMATIC", UrdfJointType::PRISMATIC)
        .value("JOINT_FIXED", UrdfJointType::FIXED)
        .value("JOINT_FLOATING", UrdfJointType::FLOATING)
        .value("JOINT_PLANAR", UrdfJointType::PLANAR)
        .export_values();

    py::enum_<UrdfJointTargetType>(m, "UrdfJointTargetType", py::arithmetic(), "")
        .value("JOINT_DRIVE_NONE", UrdfJointTargetType::NONE)
        .value("JOINT_DRIVE_POSITION", UrdfJointTargetType::POSITION)
        .value("JOINT_DRIVE_VELOCITY", UrdfJointTargetType::VELOCITY)
        .export_values();

    py::enum_<UrdfJointDriveType>(m, "UrdfJointDriveType", py::arithmetic(), "")
        .value("JOINT_DRIVE_ACCELERATION", UrdfJointDriveType::ACCELERATION)
        .value("JOINT_DRIVE_FORCE", UrdfJointDriveType::FORCE)
        .export_values();

    py::class_<UrdfDynamics>(m, "UrdfDynamics", "")
        .def_readwrite("damping", &UrdfDynamics::damping, "")
        .def_readwrite("friction", &UrdfDynamics::friction, "")
        .def_readwrite("stiffness", &UrdfDynamics::stiffness, "")
        .def(py::init<>());

    py::class_<UrdfJointDrive>(m, "UrdfJointDrive", "")
        .def_readwrite("target", &UrdfJointDrive::target, "")
        .def_readwrite("target_type", &UrdfJointDrive::targetType, "")
        .def_readwrite("drive_type", &UrdfJointDrive::driveType, "")
        .def(py::init<>());

    py::class_<UrdfLimit>(m, "UrdfLimit", "")
        .def_readwrite("lower", &UrdfLimit::lower, "")
        .def_readwrite("upper", &UrdfLimit::upper, "")
        .def_readwrite("effort", &UrdfLimit::effort, "")
        .def_readwrite("velocity", &UrdfLimit::velocity, "")
        .def(py::init<>());

    py::enum_<UrdfGeometryType>(m, "UrdfGeometryType", py::arithmetic(), "")
        .value("GEOMETRY_BOX", UrdfGeometryType::BOX)
        .value("GEOMETRY_CYLINDER", UrdfGeometryType::CYLINDER)
        .value("GEOMETRY_SPHERE", UrdfGeometryType::SPHERE)
        .value("GEOMETRY_MESH", UrdfGeometryType::MESH)
        .export_values();

    py::class_<UrdfGeometry>(m, "UrdfGeometry", "")
        .def_readwrite("type", &UrdfGeometry::type, "")
        .def_readwrite("size_x", &UrdfGeometry::size_x, "")
        .def_readwrite("size_y", &UrdfGeometry::size_y, "")
        .def_readwrite("size_z", &UrdfGeometry::size_z, "")
        .def_readwrite("radius", &UrdfGeometry::radius, "")
        .def_readwrite("length", &UrdfGeometry::length, "")
        .def_readwrite("scale_x", &UrdfGeometry::scale_x, "")
        .def_readwrite("scale_y", &UrdfGeometry::scale_y, "")
        .def_readwrite("scale_z", &UrdfGeometry::scale_z, "")
        .def_readwrite("mesh_file_path", &UrdfGeometry::meshFilePath, "")

        .def(py::init<>());


    py::class_<UrdfMaterial>(m, "UrdfMaterial", "")
        .def_readwrite("name", &UrdfMaterial::name, "")
        .def_readwrite("color", &UrdfMaterial::color, "")
        .def_readwrite("texture_file_path", &UrdfMaterial::textureFilePath, "")
        .def(py::init<>());


    py::class_<UrdfVisual>(m, "UrdfVisual", "")
        .def_readwrite("name", &UrdfVisual::name, "")
        .def_readwrite("origin", &UrdfVisual::origin, "")
        .def_readwrite("geometry", &UrdfVisual::geometry, "")
        .def_readwrite("material", &UrdfVisual::material, "")
        .def(py::init<>());

    py::class_<UrdfCollision>(m, "UrdfCollision", "")
        .def_readwrite("name", &UrdfCollision::name, "")
        .def_readwrite("origin", &UrdfCollision::origin, "")
        .def_readwrite("geometry", &UrdfCollision::geometry, "")
        .def(py::init<>());

    py::class_<UrdfLink>(m, "UrdfLink", "")
        .def_readwrite("name", &UrdfLink::name, "")
        .def_readwrite("inertial", &UrdfLink::inertial, "")
        .def_readwrite("visuals", &UrdfLink::visuals, "")
        .def_readwrite("collisions", &UrdfLink::collisions, "")
        .def(py::init<>());

    py::class_<UrdfJoint>(m, "UrdfJoint", "")
        .def_readwrite("name", &UrdfJoint::name, "")
        .def_readwrite("type", &UrdfJoint::type, "")
        .def_readwrite("origin", &UrdfJoint::origin, "")
        .def_readwrite("parent_link_name", &UrdfJoint::parentLinkName, "")
        .def_readwrite("child_link_name", &UrdfJoint::childLinkName, "")
        .def_readwrite("axis", &UrdfJoint::axis, "")
        .def_readwrite("dynamics", &UrdfJoint::dynamics, "")
        .def_readwrite("limit", &UrdfJoint::limit, "")
        .def_readwrite("drive", &UrdfJoint::drive, "")
        .def(py::init<>());

    py::class_<UrdfRobot>(m, "UrdfRobot", "")
        .def_readwrite("name", &UrdfRobot::name, "")
        .def_readwrite("links", &UrdfRobot::links, "")
        .def_readwrite("joints", &UrdfRobot::joints, "")
        .def_readwrite("materials", &UrdfRobot::materials, "")
        .def(py::init<>());

    declare_map<UrdfLink>(m, std::string("UrdfLinkMap"));
    declare_map<UrdfJoint>(m, std::string("UrdfJointMap"));
    declare_map<UrdfMaterial>(m, std::string("UrdfMaterialMap"));


    defineInterfaceClass<Urdf>(m, "Urdf", "acquire_urdf_interface", "release_urdf_interface")
        .def("parse_urdf", wrapInterfaceFunction(&Urdf::parseUrdf))
        .def("import_robot", wrapInterfaceFunction(&Urdf::importRobot))
        .def("get_kinematic_chain", wrapInterfaceFunction(&Urdf::getKinematicChain));
}
}
