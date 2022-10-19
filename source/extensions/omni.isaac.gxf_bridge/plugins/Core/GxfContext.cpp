
// Copyright (c) 2021-2022, NVIDIA CORPORATION. All rights reserved.
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

#include <gxf/std/unbounded_allocator.hpp>

namespace omni
{
namespace isaac
{
namespace gxf_bridge
{

GxfContext::GxfContext(omni::isaac::dynamic_control::DynamicControl* dynamicControlPtr)
{
    mDynamicControlPtr = dynamicControlPtr;
    mViewportInterface = carb::getCachedInterface<omni::kit::IViewport>();
    mViewportManager = std::make_unique<utils::ViewportManager>(mViewportInterface);
}

GxfContext::~GxfContext()
{
}
gxf_result_t GxfContext::create(const std::string& basePath,
                                const std::string& manifestFile,
                                const std::vector<std::string>& graphFiles)
{
    if (!mContext)
    {

        CARB_LOG_WARN("Loading: %s %s", basePath.c_str(), manifestFile.c_str());
        const char* manifest_filename = manifestFile.c_str();
        const char* base_path = basePath.c_str();
        const GxfLoadExtensionsInfo load_ext_info{ nullptr, 0, &manifest_filename, 1, base_path };
        gxf_result_t result;
        gxf_context_t contextPtr;
        if ((result = GxfContextCreate(&contextPtr)))
        {
            CARB_LOG_ERROR("GxfContextCreate failed");
            return result;
        }
        mContext = std::make_shared<gxf_context_t>(contextPtr);
        if ((result = GxfLoadExtensions(*mContext.get(), &load_ext_info)))
        {
            CARB_LOG_ERROR("GxfLoadExtensions failed");
            return result;
        }
        for (auto& graph : graphFiles)
        {
            CARB_LOG_WARN("Loading Graph: %s", graph.c_str());
            if ((result = GxfGraphLoadFile(*mContext.get(), graph.c_str())))
            {
                CARB_LOG_ERROR("GxfLoadGraph failed");
                return result;
            }
        }
    }
    else
    {
        CARB_LOG_WARN("Context already exists");
    }
    return GXF_SUCCESS;
}
gxf_result_t GxfContext::start()
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

        mActivate = true;
        if ((result = GxfGraphActivate(*mContext.get())))
        {
            CARB_LOG_ERROR("GxfGraphActivate");
            return result;
        }
        if ((result = GxfGraphRunAsync(*mContext.get())))
        {
            CARB_LOG_ERROR("GxfGraphRunAsync");
            return result;
        }
        {
            gxf_uid_t eid;
            GxfEntityFind(*mContext.get(), "isaac_sim_allocator", &eid);
            gxf_tid_t tid;
            GxfComponentTypeId(*mContext.get(), nvidia::TypenameAsString<nvidia::gxf::UnboundedAllocator>(), &tid);
            gxf_uid_t cid;
            GxfComponentFind(*mContext.get(), eid, tid, "allocator", nullptr, &cid);
            auto allocator = nvidia::gxf::Handle<nvidia::gxf::Allocator>::Create(*mContext.get(), cid);
            if (!allocator)
            {
                CARB_LOG_ERROR("Allocator not found");
                return nvidia::gxf::ToResultCode(allocator);
            }
            mAllocator = std::move(allocator.value());
        }
        {
            gxf_uid_t eid;
            GxfEntityFind(*mContext.get(), "clock", &eid);
            gxf_tid_t tid;
            GxfComponentTypeId(*mContext.get(), nvidia::TypenameAsString<nvidia::gxf::Clock>(), &tid);
            gxf_uid_t cid;
            GxfComponentFind(*mContext.get(), eid, tid, "default", nullptr, &cid);
            auto clock = nvidia::gxf::Handle<nvidia::gxf::Clock>::Create(*mContext.get(), cid);
            if (!clock)
            {
                CARB_LOG_ERROR("Clock not found");
                return nvidia::gxf::ToResultCode(clock);
            }
            mClock = std::move(clock.value());
        }
        {
            gxf_uid_t eid;
            GxfEntityFind(*mContext.get(), "atlas", &eid);
            gxf_tid_t tid;
            GxfComponentTypeId(*mContext.get(), nvidia::TypenameAsString<nvidia::isaac::AtlasFrontend>(), &tid);
            gxf_uid_t cid;
            GxfComponentFind(*mContext.get(), eid, tid, "frontend", nullptr, &cid);
            auto atlas = nvidia::gxf::Handle<nvidia::isaac::AtlasFrontend>::Create(*mContext.get(), cid);
            if (!atlas)
            {
                CARB_LOG_ERROR("AtlasFrontend not found");
                return nvidia::gxf::ToResultCode(atlas);
            }
            mAtlas = std::move(atlas.value());
        }

        // mPoseTreeMap.setAtlas(mAtlas);
        // mPoseTreeMap.clear();
        mRunning = true;
    }
    else
    {
        CARB_LOG_WARN("Context already running");
    }

    return GXF_SUCCESS;
}
void GxfContext::tick(double dt)
{
    CARB_PROFILE_ZONE(0, "REB GxfContext Tick");
    if (!mContext)
    {
        return;
    }
}
gxf_result_t GxfContext::stop()
{
    gxf_result_t result;
    if (mActivate == true)
    {
        mActivate = false;
        mRunning = false;
        // mPoseTreeMap.clear();
        if ((result = GxfGraphInterrupt(*mContext.get())))
        {
            CARB_LOG_ERROR("GxfGraphInterrupt %s", GxfResultStr(result));
            mContext.reset();
            return result;
        }
        if ((result = GxfGraphWait(*mContext.get())))
        {
            CARB_LOG_ERROR("GxfGraphWait %s", GxfResultStr(result));
            mContext.reset();
            return result;
        }
        if ((result = GxfGraphDeactivate(*mContext.get())))
        {
            CARB_LOG_ERROR("GxfGraphDeactivate %s", GxfResultStr(result));
            mContext.reset();
            return result;
        }
    }
    else
    {
        CARB_LOG_WARN("Context already stopped");
        return GXF_FAILURE;
    }
    return GXF_SUCCESS;
}
gxf_result_t GxfContext::destroy()
{
    gxf_result_t result = GXF_SUCCESS;
    if ((result = GxfContextDestroy(*mContext.get())))
    {
        CARB_LOG_ERROR("GxfContextDestroy %s", GxfResultStr(result));
    }
    mContext.reset();
    return result;
}

void GxfContext::onStop()
{
}

uint64_t GxfContext::getContextHandle()
{
    if (mContext)
    {
        return reinterpret_cast<uint64_t>(&mContext);
    }
    else
    {
        return 0;
    }
}

}
}
}
