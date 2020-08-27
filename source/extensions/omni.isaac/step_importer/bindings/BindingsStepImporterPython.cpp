// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <carb/BindingsPythonUtils.h>

#include <omni/isaac/step_importer/StepImporter.h>
#include <pybind11/pybind11/chrono.h>
#include <pybind11/pybind11/functional.h>
#include <pybind11/pybind11/numpy.h>
#include <pybind11/pybind11/pybind11.h>
#include <step_reader/step_reader.hpp>

CARB_BINDINGS("omni.isaac.step_importer.python")

PYBIND11_DECLARE_HOLDER_TYPE(T, T*);

// PYBIND11_MAKE_OPAQUE(step_reader::Mesh);
// PYBIND11_MAKE_OPAQUE(step_reader::Assembly);
// PYBIND11_MAKE_OPAQUE(step_reader::Component);
// PYBIND11_MAKE_OPAQUE(step_reader::float3);
// PYBIND11_MAKE_OPAQUE(step_reader::float4);
namespace omni
{
namespace isaac
{
namespace step_importer
{
}
}
}


namespace
{

namespace py = pybind11;


PYBIND11_MODULE(_step_importer, m)
{
    using namespace carb;
    using namespace omni::isaac::step_importer;
    // using namespace step_reader;
    // We use carb data types, must import bindings for them
    auto carb_module = py::module::import("carb");
    py::module numpy = py::module::import("numpy");

    PYBIND11_NUMPY_DTYPE(step_reader::color, r, g, b, a);
    PYBIND11_NUMPY_DTYPE(step_reader::float4, x, y, z, w);
    PYBIND11_NUMPY_DTYPE(step_reader::float3, x, y, z);
    PYBIND11_NUMPY_DTYPE(step_reader::Transform, p, r);
    PYBIND11_NUMPY_DTYPE(step_reader::Component, id, pose);
    PYBIND11_NUMPY_DTYPE(step_reader::Visual_Material, roughness, metallic, rgba_color, emmissive);


    m.doc() = "Isaac STEP importer bindings";

    py::class_<step_reader::float2>(m, "float2", "vector of size 2")
        .def(py::init<>())
        .def_readwrite("x", &step_reader::float2::x)
        .def_readwrite("y", &step_reader::float2::y);

    py::class_<step_reader::float3>(m, "float3", "vector of size 3")
        .def(py::init<>())
        .def_readwrite("x", &step_reader::float3::x)
        .def_readwrite("y", &step_reader::float3::y)
        .def_readwrite("z", &step_reader::float3::z);

    py::class_<step_reader::float4>(m, "float4", "vector of size 4")
        .def(py::init<>())
        .def_readwrite("x", &step_reader::float4::x)
        .def_readwrite("y", &step_reader::float4::y)
        .def_readwrite("z", &step_reader::float4::z)
        .def_readwrite("w", &step_reader::float4::w);

    py::class_<step_reader::color>(m, "color", "rgba color")
        .def(py::init<>())
        .def_readwrite("r", &step_reader::color::r)
        .def_readwrite("g", &step_reader::color::g)
        .def_readwrite("b", &step_reader::color::b)
        .def_readwrite("a", &step_reader::color::a)
        .def(py::pickle([](const step_reader::color& c) { return py::make_tuple(c.r, c.g, c.b, c.a); },
                        [](py::tuple t) {
                            step_reader::color c;
                            c.r = t[0].cast<float>();
                            c.g = t[0].cast<float>();
                            c.b = t[0].cast<float>();
                            c.a = t[0].cast<float>();
                            return c;
                        }));

    py::class_<step_reader::Visual_Material>(m, "Visual_Material", "Holds the visual properties of a PBR material")
        .def(py::init<>())
        .def_property_readonly_static("dtype",
                                      [](const py::object&) {
                                          return py::dtype::of<step_reader::Visual_Material>(); // return the numpy
                                                                                                // structured dtype
                                      })
        .def_readwrite("roughness", &step_reader::Visual_Material::roughness, "surface roughness")
        .def_readwrite("metallic", &step_reader::Visual_Material::metallic, "metallic reflection")
        .def_readwrite("rgba_color", &step_reader::Visual_Material::rgba_color, "surface base color")
        .def_readwrite("emmissive", &step_reader::Visual_Material::emmissive, "emmissive RGB color and intensity")
        .def(py::pickle(
            [](const step_reader::Visual_Material& mat) {
                return py::make_tuple(mat.roughness, mat.metallic, mat.rgba_color.r, mat.rgba_color.g, mat.rgba_color.b,
                                      mat.rgba_color.a, mat.emmissive.r, mat.emmissive.b, mat.emmissive.b,
                                      mat.emmissive.a);
            },
            [](py::tuple t) {
                step_reader::Visual_Material mat;
                mat.roughness = t[0].cast<float>();
                mat.metallic = t[1].cast<float>();
                mat.rgba_color.r = t[2].cast<float>();
                mat.rgba_color.g = t[3].cast<float>();
                mat.rgba_color.b = t[4].cast<float>();
                mat.rgba_color.a = t[5].cast<float>();
                mat.emmissive.r = t[6].cast<float>();
                mat.emmissive.g = t[7].cast<float>();
                mat.emmissive.b = t[8].cast<float>();
                mat.emmissive.a = t[9].cast<float>();

                return mat;
            }));


    py::class_<step_reader::Transform>(m, "Transform", "Position and orientation of an element")
        .def(py::init<>())
        .def_property_readonly_static("dtype",
                                      [](const py::object&) {
                                          return py::dtype::of<step_reader::Transform>(); // return the numpy structured
                                                                                          // dtype
                                      })
        .def_readwrite("p", &step_reader::Transform::p, "position")
        .def_readwrite("r", &step_reader::Transform::r, "orientation")
        .def(py::pickle(
            [](const step_reader::Transform& t) {
                return py::make_tuple(t.p.x, t.p.y, t.p.z, t.r.x, t.r.y, t.r.z, t.r.w);
            },
            [](py::tuple t) {
                step_reader::Transform out;
                out.p.x = t[0].cast<float>();
                out.p.y = t[1].cast<float>();
                out.p.z = t[2].cast<float>();
                out.r.x = t[3].cast<float>();
                out.r.y = t[4].cast<float>();
                out.r.z = t[5].cast<float>();
                out.r.w = t[6].cast<float>();

                return out;
            }));

    py::class_<MeshProperties>(m, "MeshProperties", "Contains properties of the meshes")
        .def(py::init<>())
        .def_readwrite("name", &MeshProperties::name, "Name")
        .def_readwrite("com", &MeshProperties::com, "Center of Mass")
        .def_readwrite("volume", &MeshProperties::volume, "Volume")
        .def_readwrite("density", &MeshProperties::density, "Density")
        .def("get_inertia_diag_matrix",
             [](MeshProperties& self) { return py::array_t<float>({ 6 }, self.inertiaMatrix); },
             "Diagonal matrix with inertia (Ixx, Ixy, Iyy, Ixz, Iyz, Izz)");

    py::class_<Mesh>(m, "Mesh", "Holds a Mesh made of vertices and triangles")
        .def(py::init<>())
        .def("get_vertices",
             [](Mesh& self) {
                 return py::array_t<float>(
                     { self.vertices.size(), (size_t)3 }, reinterpret_cast<float*>(self.vertices.data()));
             })
        .def("get_triangles",
             [](Mesh& self) { return py::array_t<size_t>({ self.triangles.size() }, self.triangles.data()); })
        .def("get_face_materials",
             [](Mesh& self) { return py::array_t<size_t>({ self.face_materials.size() }, self.face_materials.data()); })
        .def("get_vertex_normals",
             [](Mesh& self) {
                 return py::array_t<float>(
                     { self.vertices.size(), (size_t)3 }, reinterpret_cast<float*>(self.vertex_normals.data()));
             })
        .def("get_vertex_UVs",
             [](Mesh& self) {
                 return py::array_t<float>(
                     { self.vertex_UVs.size(), (size_t)2 }, reinterpret_cast<float*>(self.vertex_UVs.data()));
             })
        .def("get_triangles_normals", [](Mesh& self) {
            return py::array_t<float>(
                { self.triangles.size(), (size_t)3 }, reinterpret_cast<float*>(self.face_normals.data()));
        });

    py::class_<step_reader::Component>(
        m, "Component", "Describes a component of an Assembly, it may be either a Mesh or a sub-assembly")
        .def(py::init<>())
        .def_property_readonly_static("dtype",
                                      [](const py::object&) {
                                          return py::dtype::of<step_reader::Component>(); // return the numpy structured
                                                                                          // dtype
                                      })
        .def_readwrite("id", &step_reader::Component::id, "Index on the Assembly list")
        .def_readwrite("pose", &step_reader::Component::pose, "Relative Pose on the Assembly of the component")
        .def(py::pickle(
            [](const step_reader::Component& t) {
                return py::make_tuple(
                    t.id, t.pose.p.x, t.pose.p.y, t.pose.p.z, t.pose.r.x, t.pose.r.y, t.pose.r.z, t.pose.r.w);
            },
            [](py::tuple t) {
                step_reader::Component out;
                out.id = t[0].cast<int>();
                out.pose.p.x = t[1].cast<float>();
                out.pose.p.y = t[2].cast<float>();
                out.pose.p.z = t[3].cast<float>();
                out.pose.r.x = t[4].cast<float>();
                out.pose.r.y = t[5].cast<float>();
                out.pose.r.z = t[6].cast<float>();
                out.pose.r.w = t[7].cast<float>();

                return out;
            }));

    py::class_<Assembly>(m, "Assembly", "A group of Meshes and sub-assemblies that form an object")
        .def(py::init<>())
        .def_readwrite("name", &Assembly::name, "Assembly name")
        .def_readwrite("sub_assemblies", &Assembly::sub_assemblies, "Sub assemblies that are part of the assembly")
        .def_readwrite("meshes", &Assembly::meshes, "Meshes that are part of the Assembly");

    py::class_<Part>(
        m, "Part",
        "Full imported assembly from the CAD file. Every assembly, mesh and material is listed only once, and referred by indexes on the assemblies that use that element. The first element at the Assembly list is the root of the part.")
        .def(py::init<>())
        .def_readwrite("assemblies", &Part::assemblies, "unique list of assemblies")
        .def_readwrite("meshes_properties", &Part::meshes_properties, "unique list of meshes")
        .def_readwrite("materials", &Part::materials, "unique list of assemblies");
    // .def("get_assemblies",
    //      [](Part& self) { return py::array_t<Assembly>({ self.assemblies.size() }, self.assemblies.data()); })
    // .def("get_meshes", [](Part& self) { return py::array_t<Mesh>({ self.meshes.size() }, self.meshes.data()); })
    // .def("get_material", [](Part& self) {
    //     return py::array_t<step_reader::Visual_Material>({ self.materials.size() }, self.materials.data());
    // });

    py::class_<step_reader::Tesselation_Properties>(
        m, "Tesselation_Properties",
        "Properties of the Tesselation process that transform the drawings into triangular meshes")
        .def(py::init<>())
        .def_readwrite("max_linear_offset", &step_reader::Tesselation_Properties::max_linear_offset,
                       "Distance tesselation can deviate from original surface, measured by triangle normal")
        .def_readwrite("max_angular_offset", &step_reader::Tesselation_Properties::max_angular_offset,
                       "Absolute angular offset surface normal can deviate from original surface")
        .def_readwrite("min_surface", &step_reader::Tesselation_Properties::min_surface,
                       "Minimum triangle surface. negative values implie no limit.")
        .def_readwrite("use_relative_offset", &step_reader::Tesselation_Properties::use_relative_offset,
                       "If true, linear offset is multiplied by the edge length for triangle.")
        .def_readwrite("use_internal_vertices", &step_reader::Tesselation_Properties::use_internal_vertices,
                       "Flags if should take internal vertices into account")
        .def_readwrite("volumetric_center_meshes", &step_reader::Tesselation_Properties::volumetric_center_meshes,
                       "Recenter the extracted meshes to its volumetric center")
        .def(py::pickle(
            [](const step_reader::Tesselation_Properties& t) {
                return py::make_tuple(t.max_linear_offset, t.max_angular_offset, t.min_surface, t.use_relative_offset,
                                      t.use_internal_vertices, t.volumetric_center_meshes);
            },
            [](py::tuple t) {
                step_reader::Tesselation_Properties out;
                out.max_linear_offset = t[0].cast<float>();
                out.max_angular_offset = t[1].cast<float>();
                out.min_surface = t[2].cast<float>();
                out.use_relative_offset = t[3].cast<bool>();
                out.use_internal_vertices = t[4].cast<bool>();
                out.volumetric_center_meshes = t[5].cast<bool>();

                return out;
            }));


    defineInterfaceClass<StepImporter>(m, "StepImporter", "acquire_interface", "release_interface")
        .def("load_step_file", wrapInterfaceFunction(&StepImporter::loadStepFile))
        .def("release_step_file", wrapInterfaceFunction(&StepImporter::releaseStepFile))
        .def("get_assembly_structure", wrapInterfaceFunction(&StepImporter::getAssemblyStructure))
        .def("get_mesh", wrapInterfaceFunction(&StepImporter::getMesh));
}
}
