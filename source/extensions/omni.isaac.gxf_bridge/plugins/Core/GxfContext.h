
// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//


#pragma once
#include "GxfPoseTreeMap.h"
#include "extensions/atlas/atlas_frontend.hpp"
#include "gxf/core/gxf.h"
#include "omni/isaac/bridge/BridgeApplication.h"
#include "omni/isaac/bridge/ViewportManager.h"

#include <gxf/std/clock.hpp>
#include <gxf/std/unbounded_allocator.hpp>
#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/kit/IViewport.h>

#include <string>

namespace omni
{
namespace isaac
{
namespace gxf_bridge
{

class GxfContext
{
public:
    GxfContext();
    ~GxfContext();
    gxf_result_t create();
    gxf_result_t destroy();

    gxf_result_t loadManifest(const std::string& basePath, const std::string& manifestFile);
    gxf_result_t loadGraphsFromFile(const std::vector<std::string>& graphStrings);
    gxf_result_t loadGraphsFromString(const std::vector<std::string>& graphStrings);
    gxf_result_t setSeverity(const gxf_severity_t& severity);

    gxf_result_t start(const std::string& clockEntity,
                       const std::string& clockComponent,
                       const std::string& atlastEntity,
                       const std::string& atlasComponent);
    gxf_result_t stop();

    bool isRunning();
    bool isActivated();

    nvidia::gxf::Handle<nvidia::gxf::UnboundedAllocator> allocator();
    nvidia::gxf::Handle<nvidia::gxf::Clock> clock();
    nvidia::gxf::Handle<nvidia::isaac::AtlasFrontend> atlas();
    gxf_context_t gxfContext();

    template <typename T>
    gxf_result_t findComponent(const char* entity, const char* component, nvidia::gxf::Handle<T>& handle)
    {
        if (mContext)
        {
            gxf_result_t result;
            gxf_uid_t eid;
            const char* type_name = nvidia::TypenameAsString<T>();
            if ((result = GxfEntityFind(*mContext.get(), entity, &eid)))
            {
                CARB_LOG_ERROR("GxfEntityFind failed for %s: %s", entity, GxfResultStr(result));
                return result;
            }
            gxf_tid_t tid;
            if ((result = GxfComponentTypeId(*mContext.get(), type_name, &tid)))
            {
                CARB_LOG_ERROR("GxfComponentTypeId failed to find type %s: %s", type_name, GxfResultStr(result));
                return result;
            }

            gxf_uid_t cid;
            if ((result = GxfComponentFind(*mContext.get(), eid, tid, component, nullptr, &cid)))
            {
                CARB_LOG_ERROR("GxfComponentFind failed to find component %s of type %s in entity %s: %s", component,
                               type_name, entity, GxfResultStr(result));

                return result;
            }
            auto gxfHandle = nvidia::gxf::Handle<T>::Create(*mContext.get(), cid);
            if (!gxfHandle)
            {
                CARB_LOG_WARN("entity %s with component of type %s with name %s not found", entity,
                              nvidia::TypenameAsString<T>(), component);
                return nvidia::gxf::ToResultCode(gxfHandle);
            }
            handle = std::move(gxfHandle.value());
            return GXF_SUCCESS;
        }
        else
        {
            CARB_LOG_WARN("Create context first");
            return GXF_FAILURE;
        }
    }

private:
    std::shared_ptr<gxf_context_t> mContext = nullptr;
    // GxfPoseTreeMap mPoseTreeMap;
    int64_t mTimeDifferenceNanoSeconds = 0;
    nvidia::gxf::Handle<nvidia::gxf::UnboundedAllocator> mAllocator;
    nvidia::gxf::Handle<nvidia::gxf::Clock> mClock;
    nvidia::gxf::Handle<nvidia::isaac::AtlasFrontend> mAtlas;
    bool mRunning = false;
    bool mActivated = false;
};
}
}
}
