// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#define CARB_EXPORTS

#include <carb/Framework.h>
#include <carb/PluginUtils.h>
#include <carb/logging/Log.h>

#include <omni/isaac/step_importer/StepImporter.h>
#include <omni/kit/IApp.h>
#include <omni/kit/IStageUpdate.h>
#include <step_reader/step_reader.hpp>

const struct carb::PluginImplDesc kPluginImpl = { "omni.isaac.step_importer.plugin", "Isaac Step file Importer",
                                                  "NVIDIA", carb::PluginHotReload::eDisabled, "dev" };

CARB_PLUGIN_IMPL(kPluginImpl, omni::isaac::step_importer::StepImporter);
CARB_PLUGIN_IMPL_DEPS(omni::kit::IApp, carb::logging::ILogging)

namespace
{

carb::Framework* g_framework = nullptr;

std::unique_ptr<omni::isaac::step_importer::StepImporter> g_stepImporter = nullptr;


omni::isaac::step_importer::Mesh fromStepReader(step_reader::Mesh* m)
{
    std::vector<step_reader::float3> vertices(m->vertices, m->vertices + m->vertex_size);
    std::vector<size_t> triangles(m->triangles, m->triangles + m->triangles_size * 3);
    std::vector<step_reader::float3> face_normals(m->face_normals, m->face_normals + m->triangles_size);
    std::vector<step_reader::float3> vertex_normals(m->vertex_normals, m->vertex_normals + m->vertex_size);
    std::vector<step_reader::float2> vertex_UVs(m->vertex_UVs, m->vertex_UVs + m->vertex_size);
    std::vector<size_t> face_materials(m->face_mats, m->face_mats + m->triangles_size);
    return omni::isaac::step_importer::Mesh{ m->name,        vertices,   triangles,     face_normals,
                                             vertex_normals, vertex_UVs, face_materials };
}

omni::isaac::step_importer::Assembly fromStepReader(step_reader::Assembly* m)
{
    std::vector<step_reader::Component> sub_assemblies(m->sub_assemblies, m->sub_assemblies + m->num_sub_assemblies);
    std::vector<step_reader::Component> meshes(m->meshes, m->meshes + m->num_meshes);
    return omni::isaac::step_importer::Assembly{ sub_assemblies, meshes, m->name };
}

void fromStepReader(step_reader::Part* p, omni::isaac::step_importer::Part& out)
{
    std::vector<omni::isaac::step_importer::Assembly> assemblies(p->num_assemblies);
    for (size_t i = 0; i < p->num_assemblies; ++i)
    {
        out.assemblies.push_back(fromStepReader(&p->assemblies[i]));
    }
    std::vector<omni::isaac::step_importer::Mesh> meshes(p->num_meshes);
    for (size_t i = 0; i < p->num_meshes; ++i)
    {
        out.meshes.push_back(fromStepReader(&p->meshes[i]));
    }
    for (size_t i = 0; i < p->num_materials; ++i)
    {
        out.materials.push_back(p->materials[i]);
    }
    // return omni::isaac::step_importer::Part{ assemblies, meshes, materials };
}


void CARB_ABI SiImportStepFile(char* filename,
                               step_reader::Tesselation_Properties props,
                               omni::isaac::step_importer::Part& out)
{
    out.assemblies.clear();
    out.meshes.clear();
    out.materials.clear();
    step_reader::Part p = step_reader::GetAssemblyFromStep(filename, props);
    fromStepReader(&p, out);
    for (size_t i = 0; i < p.num_meshes; i++)
    {
        // std::unique_ptr<char[]> name_ptr(p.meshes[i].name);
        std::unique_ptr<step_reader::float3[]> vertices_ptr(p.meshes[i].vertices);
        std::unique_ptr<step_reader::float3[]> vertex_normals_ptr(p.meshes[i].vertex_normals);
        std::unique_ptr<step_reader::float3[]> face_normals_ptr(p.meshes[i].face_normals);
        std::unique_ptr<step_reader::float2[]> UVs_ptr(p.meshes[i].vertex_UVs);
        std::unique_ptr<size_t[]> triangles_ptr(p.meshes[i].triangles);
        std::unique_ptr<size_t[]> face_mats_ptr(p.meshes[i].face_mats);
    }
    for (size_t i = 0; i < p.num_assemblies; i++)
    {
        // std::unique_ptr<char[]> name_ptr(p.assemblies[i].name);
        std::unique_ptr<step_reader::Component[]> sub_assemblies_ptr(p.assemblies[i].sub_assemblies);
        std::unique_ptr<step_reader::Component[]> meshes_ptr(p.assemblies[i].meshes);
    }

    std::unique_ptr<step_reader::Mesh[]> meshes_ptr(p.meshes);
    std::unique_ptr<step_reader::Assembly[]> assemblies_ptr(p.assemblies);
    std::unique_ptr<step_reader::Visual_Material[]> mats_ptr(p.materials);
}
}


CARB_EXPORT void carbOnPluginStartup()
{
    CARB_LOG_INFO("Startup URDF Extension");

    // Get app interface using Carbonite Framework
    g_framework = carb::getFramework();
    g_stepImporter = std::make_unique<omni::isaac::step_importer::StepImporter>();
}


CARB_EXPORT void carbOnPluginShutdown()
{
    g_stepImporter = nullptr;
}


void fillInterface(omni::isaac::step_importer::StepImporter& iface)
{
    using namespace omni::isaac::step_importer;
    CARB_LOG_WARN("Filling SI Interface");
    memset(&iface, 0, sizeof(iface));

    iface.importStepFile = SiImportStepFile;
}
