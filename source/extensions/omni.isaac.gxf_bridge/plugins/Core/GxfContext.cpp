// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
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

#include "GxfContext.h"


namespace omni
{
namespace isaac
{
namespace gxf_bridge
{

GxfContext::GxfContext()
{
}

GxfContext::~GxfContext()
{
    stop();
    destroy();
}
gxf_result_t GxfContext::create()
{
    if (!mContext)
    {

        gxf_result_t result = GXF_SUCCESS;
        gxf_context_t contextPtr;
        if ((result = GxfContextCreate(&contextPtr)))
        {
            CARB_LOG_ERROR("GxfContextCreate failed");
            mContext.reset();
            return GXF_FAILURE;
        }
        mContext = std::make_shared<gxf_context_t>(contextPtr);
        return GXF_SUCCESS;
    }
    return GXF_FAILURE;
}

gxf_result_t GxfContext::destroy()
{
    gxf_result_t result = GXF_SUCCESS;
    if (mContext)
    {
        if ((result = GxfContextDestroy(*mContext.get())))
        {
            CARB_LOG_ERROR("GxfContextDestroy %s", GxfResultStr(result));
        }
    }
    mContext.reset();
    return GXF_FAILURE;
}

gxf_result_t GxfContext::loadManifest(const std::string& basePath, const std::string& manifestFile)
{
    if (mContext)
    {

        CARB_LOG_WARN("Loading: %s %s", basePath.c_str(), manifestFile.c_str());
        const char* manifest_filename = manifestFile.c_str();
        const char* base_path = basePath.c_str();
        const GxfLoadExtensionsInfo load_ext_info{ nullptr, 0, &manifest_filename, 1, base_path };
        gxf_result_t result;

        if ((result = GxfLoadExtensions(*mContext.get(), &load_ext_info)))
        {
            CARB_LOG_ERROR("GxfLoadExtensions failed");
            return GXF_FAILURE;
        }
    }
    else
    {
        CARB_LOG_WARN("Create context before attempting to load manifest.");
    }
    return GXF_SUCCESS;
}

gxf_result_t GxfContext::loadGraphsFromFile(const std::vector<std::string>& graphFiles)
{
    if (mContext)
    {
        gxf_result_t result;
        for (auto& graph : graphFiles)
        {
            CARB_LOG_INFO("Loading graph: %s", graph.c_str());
            if ((result = GxfGraphLoadFile(*mContext.get(), graph.c_str())))
            {
                CARB_LOG_ERROR("GxfLoadGraph failed");
                return GXF_FAILURE;
            }
        }
    }
    else
    {
        CARB_LOG_WARN("Create context before attempting to load graphs.");
    }
    return GXF_SUCCESS;
}

gxf_result_t GxfContext::loadGraphsFromString(const std::vector<std::string>& graphStrings)
{
    if (mContext)
    {
        gxf_result_t result;
        for (auto& graph : graphStrings)
        {
            CARB_LOG_INFO("Parsing graph: %s", graph.c_str());
            if ((result = GxfGraphParseString(*mContext.get(), graph.c_str())))
            {
                CARB_LOG_ERROR("GxfGraphParseString failed.");
                return GXF_FAILURE;
            }
        }
    }
    else
    {
        CARB_LOG_WARN("Create context before attempting to load graphs.");
    }
    return GXF_SUCCESS;
}

gxf_result_t GxfContext::setSeverity(const gxf_severity_t& severity)
{
    if (mContext)
    {
        gxf_result_t result;

        if ((result = GxfSetSeverity(*mContext.get(), severity)))
        {
            CARB_LOG_ERROR("GxfGraphParseString failed");
            return GXF_FAILURE;
        }
    }
    else
    {
        CARB_LOG_WARN("Create context first");
    }
    return GXF_SUCCESS;
}

gxf_result_t GxfContext::start(const std::string& clockEntity,
                               const std::string& clockComponent,
                               const std::string& atlastEntity,
                               const std::string& atlasComponent)
{
    gxf_result_t result;
    if (mRunning == false)
    {
        mActivated = false;
        mRunning = false;
        if ((result = GxfGraphActivate(*mContext.get())))
        {
            CARB_LOG_ERROR("GxfGraphActivate failed");
            return GXF_FAILURE;
        }
        mActivated = true;

        if ((result = GxfGraphRunAsync(*mContext.get())))
        {
            CARB_LOG_ERROR("GxfGraphRunAsync failed");
            return GXF_FAILURE;
        }
        if (findComponent<nvidia::gxf::UnboundedAllocator>("isaac_sim_allocator", "allocator", mAllocator))
        {
            return GXF_FAILURE;
        }
        if (findComponent<nvidia::gxf::SyntheticClock>(clockEntity.c_str(), clockComponent.c_str(), mClock))
        {
            return GXF_FAILURE;
        }
        if (findComponent<nvidia::isaac::AtlasFrontend>(atlastEntity.c_str(), atlasComponent.c_str(), mAtlas))
        {
            return GXF_FAILURE;
        }

        mRunning = true;
    }
    else
    {
        CARB_LOG_WARN("Context already running");
    }

    return GXF_SUCCESS;
}

gxf_result_t GxfContext::stop()
{
    gxf_result_t result;
    if (mActivated == true)
    {


        // mPoseTreeMap.clear();
        if (mRunning)
        {
            if ((result = GxfGraphInterrupt(*mContext.get())))
            {
                CARB_LOG_ERROR("GxfGraphInterrupt %s", GxfResultStr(result));
                mContext.reset();
                return GXF_FAILURE;
            }
            if ((result = GxfGraphWait(*mContext.get())))
            {
                CARB_LOG_ERROR("GxfGraphWait %s", GxfResultStr(result));
                mContext.reset();
                return GXF_FAILURE;
            }
        }
        if ((result = GxfGraphDeactivate(*mContext.get())))
        {
            CARB_LOG_ERROR("GxfGraphDeactivate %s", GxfResultStr(result));
            mContext.reset();
            return GXF_FAILURE;
        }
        mActivated = false;
        mRunning = false;
    }
    else
    {
        CARB_LOG_WARN("Context already stopped");
        return GXF_FAILURE;
    }
    return GXF_SUCCESS;
}

bool GxfContext::isRunning()
{
    return mRunning;
}

bool GxfContext::isActivated()
{
    return mActivated;
}

nvidia::gxf::Handle<nvidia::gxf::UnboundedAllocator> GxfContext::allocator()
{
    return mAllocator;
};
nvidia::gxf::Handle<nvidia::gxf::SyntheticClock> GxfContext::clock()
{
    return mClock;
};
nvidia::gxf::Handle<nvidia::isaac::AtlasFrontend> GxfContext::atlas()
{
    return mAtlas;
};
gxf_context_t GxfContext::gxfContext()
{
    // check if context ptr was initialized
    if (mContext)
    {
        return *(mContext.get());
    }
    else
    {
        return kNullContext;
    }
};

}
}
}
