
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
        CARB_LOG_WARN("Create context first");
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
            CARB_LOG_INFO("Loading Graph: %s", graph.c_str());
            if ((result = GxfGraphLoadFile(*mContext.get(), graph.c_str())))
            {
                CARB_LOG_ERROR("GxfLoadGraph failed");
                return GXF_FAILURE;
            }
        }
    }
    else
    {
        CARB_LOG_WARN("Create context first");
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
            CARB_LOG_INFO("Parsing Graph: %s", graph.c_str());
            if ((result = GxfGraphParseString(*mContext.get(), graph.c_str())))
            {
                CARB_LOG_ERROR("GxfGraphParseString failed");
                return GXF_FAILURE;
            }
        }
    }
    else
    {
        CARB_LOG_WARN("Create context first");
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
        // // Create a host memory allocator
        // gxf_uid_t eid;
        // if ((result = GxfEntityCreate(mContext, &eid)))
        // {
        //     CARB_LOG_ERROR("GxfEntityCreate failed");
        // }
        // gxf_tid_t tid;
        // if ((result = GxfComponentTypeId(mContext, nvidia::TypenameAsString<nvidia::gxf::UnboundedAllocator>(),
        // &tid)))
        // {
        //     CARB_LOG_ERROR("GxfComponentTypeId");
        //     return result;
        // }
        // gxf_uid_t cid;
        // if ((result = GxfComponentAdd(mContext, eid, tid, "allocator", &cid)))
        // {
        //     CARB_LOG_ERROR("GxfComponentAdd");
        //     return result;
        // }
        // if ((result = GxfParameterSetInt32(mContext, cid, "storage_type", 0)))
        // {
        //     CARB_LOG_ERROR("GxfParameterSetInt32");
        //     return result;
        // }
        // if ((result = GxfParameterSetBool(mContext, cid, "do_not_use_cuda_malloc_host", true)))
        // {
        //     CARB_LOG_ERROR("GxfParameterSetBool");
        //     return result;
        // }
        // auto allocator = nvidia::gxf::Handle<nvidia::gxf::Allocator>::Create(mContext, cid);
        // if (!allocator)
        // {
        //     CARB_LOG_ERROR("mAllocator Not Valid %d", allocator.error());
        //     return allocator.error();
        // }
        // else
        // {
        //     mAllocator =allocator.value();
        //     if ((result = mAllocator.get()->initialize()))
        //     {
        //         CARB_LOG_ERROR("mAllocator Not initialized %d", result);
        //         return result;
        //     }
        // }
        // if (mAllocator.get())
        // {
        //     CARB_LOG_ERROR("CAN ALLOCATE A: %d", mAllocator.get()->is_available(100));
        // }
        // GxfEntityActivate(mContext, eid);
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
        if (findComponent<nvidia::gxf::Clock>(clockEntity.c_str(), clockComponent.c_str(), mClock))
        {
            return GXF_FAILURE;
        }
        if (findComponent<nvidia::isaac::AtlasFrontend>(atlastEntity.c_str(), atlasComponent.c_str(), mAtlas))
        {
            return GXF_FAILURE;
        }

        mRunning = true;

        // mPoseTreeMap.setAtlas(mAtlas);
        // mPoseTreeMap.clear();
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
nvidia::gxf::Handle<nvidia::gxf::Clock> GxfContext::clock()
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
