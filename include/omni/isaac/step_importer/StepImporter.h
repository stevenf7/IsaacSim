
#pragma once

#include <carb/Interface.h>
#include <carb/Types.h>

#include <step_reader/step_reader.hpp>

#include <vector>
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
    std::string name;
};

struct MeshProperties
{
    std::string name;
    step_reader::float3 com{ 0.0f, 0.0f, 0.0f };
    float volume;
    float inertiaMatrix[6]; // diagonal matrix with inertia (Ixx, Ixy, Iyy, Ixz, Iyz, Izz)
    float density;
};

struct Mesh
{
    std::vector<step_reader::float3> vertices; // Position of each vertex
    std::vector<size_t> triangles; // index of vertices that make up each mesh (length: 3*size)
    std::vector<step_reader::float3> face_normals;
    std::vector<step_reader::float3> vertex_normals;
    std::vector<step_reader::float2> vertex_UVs;
    std::vector<size_t> face_materials;
};

struct Part
{
    std::vector<Assembly> assemblies;
    std::vector<MeshProperties> meshes_properties;
    std::vector<step_reader::Visual_Material> materials;
};

typedef int32_t SiHandle;

struct StepImporter
{
    CARB_PLUGIN_INTERFACE("omni::isaac::step_importer::StepImporter", 0, 1);

    SiHandle(CARB_ABI* loadStepFile)(const char* fileName);
    void(CARB_ABI* releaseStepFile)(const SiHandle step_file);
    bool(CARB_ABI* getAssemblyStructure)(const SiHandle step_file, Part& part);
    bool(CARB_ABI* getMesh)(const SiHandle step_file,
                            size_t mesh_key,
                            step_reader::Tesselation_Properties props,
                            omni::isaac::step_importer::Mesh& out);
};
}
}
}
