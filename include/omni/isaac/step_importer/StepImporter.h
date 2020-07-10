
#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

#include <step_reader/step_reader.hpp>
namespace omni
{
namespace isaac
{
namespace step_importer
{

struct Assembly
{
    std::vector<step_reader::Component> sub_assemblies;
    std::vector<step_reader::Component> meshes; // reference to meshes used on assembly, and transform from assembly
                                                // origin
    char* name;
};

struct Mesh
{
    char* name;
    std::vector<step_reader::float3> vertices; // Position of each vertex
    std::vector<size_t> triangles; // index of vertices that make up each mesh (length: 3*size)
    std::vector<step_reader::float3> face_normals;
    std::vector<step_reader::float3> vertex_normals;
    std::vector<size_t> face_materials;
};

struct Part
{
    std::vector<Assembly> assemblies;
    std::vector<Mesh> meshes;
    std::vector<step_reader::Visual_Material> materials;
};

struct StepImporter
{
    CARB_PLUGIN_INTERFACE("omni::isaac::step_importer::StepImporter", 0, 1);

    void(CARB_ABI* importStepFile)(char* fileName,
                                   step_reader::Tesselation_Properties props,
                                   omni::isaac::step_importer::Part& out);
};
}
}
}
