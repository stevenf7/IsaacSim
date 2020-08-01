// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#define CARB_EXPORTS

#include "StepImporter.h"

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
std::unique_ptr<omni::isaac::step_importer::SiContext> g_ctx = nullptr;

using namespace omni::isaac::step_importer;
void fromStepReader(step_reader::Mesh& m, Mesh& out)
{
    out.vertices.assign(m.vertices, m.vertices + m.vertex_size);
    out.triangles.assign(m.triangles, m.triangles + m.triangles_size * 3);
    out.face_normals.assign(m.face_normals, m.face_normals + m.triangles_size);
    out.vertex_normals.assign(m.vertex_normals, m.vertex_normals + m.vertex_size);
    out.vertex_UVs.assign(m.vertex_UVs, m.vertex_UVs + m.vertex_size);
    out.face_materials.assign(m.face_mats, m.face_mats + m.triangles_size);
}

void fromStepReader(step_reader::Assembly& m, Assembly& out)
{
    out.sub_assemblies.assign(m.sub_assemblies, m.sub_assemblies + m.num_sub_assemblies);
    out.meshes.assign(m.meshes, m.meshes + m.num_meshes);
    out.name.assign(m.name);
}

void fromStepReader(step_reader::MeshProperties& m, MeshProperties& out)
{
    out.name.assign(m.name);
    out.com.x = m.com.x;
    out.com.y = m.com.y;
    out.com.z = m.com.z;
    out.volume = m.volume;
    memcpy(out.inertiaMatrix, m.inertiaMatrix, sizeof(float) * 6);
    out.density = m.density;
}
void fromStepReader(step_reader::Part& p, omni::isaac::step_importer::Part& out)
{
    out.assemblies.resize(p.num_assemblies);
    out.meshes_properties.resize(p.num_meshes);
    for (int i = 0; i < p.num_meshes; ++i)
    {
        fromStepReader(p.meshProperties[i], out.meshes_properties[i]);
    }
    for (int i = 0; i < p.num_assemblies; ++i)
    {

        fromStepReader(p.assemblies[i], out.assemblies[i]);
    }
    // out.assemblies.assign(p.assemblies, p.assemblies + p.num_assemblies);
    out.materials.assign(p.materials, p.materials + p.num_materials);
}

SiHandle SiLoadStepFile(const char* step_file)
{
    SiContext* ctx = g_ctx.get();
    if (!ctx)
    {
        return -1;
    }
    step_reader::StepReader* sr = step_reader::LoadStepFile(step_file);
    return ctx->addStepReader(sr);
}

bool CARB_ABI SiGetAssemblyStructure(SiHandle step_reader_handle, omni::isaac::step_importer::Part& out)
{
    SiContext* ctx = g_ctx.get();
    if (!ctx)
    {
        return false;
    }
    step_reader::StepReader* step_reader = ctx->getStepReader(step_reader_handle);
    if (!step_reader)
    {
        return false;
    }
    step_reader::Part p = step_reader::GetAssemblyStructure(step_reader);
    fromStepReader(p, out);
    step_reader::DestroyPart(p);
    return true;
}

bool CARB_ABI SiGetMesh(SiHandle step_reader_handle, size_t mesh_key, step_reader::Tesselation_Properties props, Mesh& mesh)
{
    SiContext* ctx = g_ctx.get();
    if (!ctx)
    {
        return false;
    }
    step_reader::StepReader* step_reader = ctx->getStepReader(step_reader_handle);
    if (!step_reader)
    {
        return false;
    }
    step_reader::Mesh m;
    if (step_reader::GetMesh(step_reader, mesh_key, m, props))
    {
        fromStepReader(m, mesh);
        step_reader::DestroyMesh(m);
        return true;
    }
    return false;
}

void CARB_ABI SiReleaseStepFile(const SiHandle step_reader_handle)
{
    SiContext* ctx = g_ctx.get();
    if (!ctx)
    {
        return;
    }
    step_reader::StepReader* step_reader = ctx->getStepReader(step_reader_handle);
    if (!step_reader)
    {
        return;
    }
    CARB_LOG_INFO("Removing Reader %d", step_reader_handle);
    ctx->removeStepReader(step_reader_handle);
    CARB_LOG_INFO("Done");
}

}

CARB_EXPORT void carbOnPluginStartup()
{
    CARB_LOG_INFO("Startup Step Importer Extension");

    // Get app interface using Carbonite Framework
    g_framework = carb::getFramework();
    if (g_ctx.get() == nullptr)
        g_ctx = std::make_unique<omni::isaac::step_importer::SiContext>();
    if (g_stepImporter.get() == nullptr)
        g_stepImporter = std::make_unique<omni::isaac::step_importer::StepImporter>();
}


CARB_EXPORT void carbOnPluginShutdown()
{
    CARB_LOG_INFO("Shutting Down SI Interface");

    g_ctx.get()->clearStepReaders();
    CARB_LOG_INFO("  Deleting SI Context");
    g_ctx.reset(nullptr);
    CARB_LOG_INFO("  Deleting interface");
    g_stepImporter.reset(nullptr);
    CARB_LOG_INFO("Done");
}


void fillInterface(omni::isaac::step_importer::StepImporter& iface)
{
    using namespace omni::isaac::step_importer;
    CARB_LOG_INFO("Filling SI Interface");
    memset(&iface, 0, sizeof(iface));

    iface.loadStepFile = SiLoadStepFile;
    iface.releaseStepFile = SiReleaseStepFile;
    iface.getAssemblyStructure = SiGetAssemblyStructure;
    iface.getMesh = SiGetMesh;
}
