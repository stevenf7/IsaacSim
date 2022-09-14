// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../utils/BaseResetNode.h"
#include "Core/GxfPoseTreeMap.h"
#include "Core/GxfStructs.h"
#include "GxfBridge.h"
#include "gxf/core/gxf.h"

#include <carb/Defines.h>
#include <carb/Types.h>
#include <carb/events/EventsUtils.h>

#include <gxf/core/entity.hpp>
#include <gxf/std/double_buffer_receiver.hpp>
#include <gxf/std/double_buffer_transmitter.hpp>
#include <gxf/std/tensor.hpp>
#include <gxf/std/timestamp.hpp>
#include <gxf/std/unbounded_allocator.hpp>
#include <omni/usd/UsdContextIncludes.h>
//
#include <omni/usd/UsdContext.h>

namespace omni
{
namespace isaac
{
namespace gxf_bridge
{


/**
 * @brief Base class for all ROS1 bridge nodes. It handles the lifetime of the internal ROS node handle automatically.
 *
 */
class GxfNode : public BaseResetNode
{

public:
    /**
     * @brief Construct a new Ros Node object
     *
     */
    GxfNode()
    {
        mGxfBridge = carb::getFramework()->acquireInterface<omni::isaac::gxf_bridge::GxfBridge>();
    }
    /**
     * @brief Destroy the Ros Node object
     *
     */
    ~GxfNode()
    {
        reset();
    }

    /**
     * @brief Reset the node handle
     * Should be called by all derived classes after they reset any publishers/subscribers attached to the node
     *
     */
    virtual void reset()
    {
        mContext = nullptr;
    }
    /**
     * @brief
     *
     * @param entity
     * @param component
     * @param data
     * @return gxf_result_t
     */
    gxf_result_t publish(const std::string& entity, const std::string& component, const nvidia::gxf::Entity& data)
    {
        gxf_result_t result;
        gxf_uid_t tcp_eid;
        if ((result = GxfEntityFind(mContext, entity.c_str(), &tcp_eid)))
        {
            CARB_LOG_ERROR("GxfEntityFind %s, %s", entity.c_str(), GxfResultStr(result));
            return result;
        }
        gxf_tid_t pub_tid;
        if ((result = GxfComponentTypeId(
                 mContext, nvidia::TypenameAsString<nvidia::gxf::DoubleBufferTransmitter>(), &pub_tid)))
        {
            CARB_LOG_ERROR("GxfComponentTypeId Transmitter, %s", GxfResultStr(result));
            return result;
        }
        gxf_uid_t pub_cid;
        if ((result = GxfComponentFind(mContext, tcp_eid, pub_tid, component.c_str(), nullptr, &pub_cid)))
        {
            CARB_LOG_ERROR("GxfComponentFind %s, %s", component.c_str(), GxfResultStr(result));
            return result;
        }
        auto pub_handle = nvidia::gxf::Handle<nvidia::gxf::DoubleBufferTransmitter>::Create(mContext, pub_cid);

        if ((result = pub_handle.value()->push_abi(data.eid())))
        {
            CARB_LOG_ERROR("push_abi, %s", GxfResultStr(result));
            return result;
        }
        // CARB_LOG_WARN("Publish to %s/%s", entityName.c_str(), transmitterName.c_str());
        return gxf_result_t::GXF_SUCCESS;
    }

    /**
     * @brief
     *
     * @param entity
     * @param component
     * @param data
     * @return gxf_result_t
     */
    gxf_result_t receive(const std::string& entity,
                         const std::string& component,
                         nvidia::gxf::Expected<nvidia::gxf::Entity>& data)
    {
        gxf_result_t result;
        gxf_uid_t tcp_eid;
        if ((result = GxfEntityFind(mContext, entity.c_str(), &tcp_eid)))
        {
            CARB_LOG_ERROR("GxfEntityFind: %s, %s", entity.c_str(), GxfResultStr(result));
            return result;
        }
        gxf_tid_t pub_tid;
        if ((result =
                 GxfComponentTypeId(mContext, nvidia::TypenameAsString<nvidia::gxf::DoubleBufferReceiver>(), &pub_tid)))
        {
            CARB_LOG_ERROR("GxfComponentTypeId, %s", GxfResultStr(result));
            return result;
        }
        gxf_uid_t pub_cid;
        if ((result = GxfComponentFind(mContext, tcp_eid, pub_tid, component.c_str(), nullptr, &pub_cid)))
        {
            CARB_LOG_ERROR("GxfComponentFind: %s, %s", component.c_str(), GxfResultStr(result));
            return result;
        }
        auto sub_handle = nvidia::gxf::Handle<nvidia::gxf::DoubleBufferReceiver>::Create(mContext, pub_cid);
        if ((result = sub_handle.value()->sync_abi()))
        {
            CARB_LOG_ERROR("sync_abi, %s", GxfResultStr(result));
            return result;
        }

        // No message
        if (sub_handle.value()->size() == 0)
        {
            return gxf_result_t::GXF_FAILURE;
        }

        gxf_uid_t uid;
        const gxf_result_t code = sub_handle.value()->pop_abi(&uid);

        if (code == gxf_result_t::GXF_SUCCESS)
        {
            auto message = nvidia::gxf::Entity::Own(mContext, uid);
            data = std::move(message);
            return gxf_result_t::GXF_SUCCESS;
        }
        else
        {
            auto message = nvidia::gxf::Unexpected{ code };
            data = std::move(message);
            return gxf_result_t::GXF_FAILURE;
        }
    }

    /**
     * @brief Set the Gxf Context
     *
     * @param gxfContext
     */
    virtual void setGxfContext(const gxf_context_t& gxfContext)
    {
        // CARB_LOG_WARN("setGxfContext");
        mContext = gxfContext;
    }
    virtual void setGxfAllocator(const nvidia::gxf::Handle<nvidia::gxf::Allocator>& allocator)
    {
        // CARB_LOG_WARN("setGxfAllocator");
        mAllocator = allocator;
    }
    virtual void setPoseTreeMap(GxfPoseTreeMap* poseTreeMap)
    {
        // CARB_LOG_WARN("setPoseTreeMap");
        mPoseTreeMap = poseTreeMap;
    }

    virtual void updateTimestamp(double timeStamp, int64_t timeOffset)
    {

        mTimeDelta = timeStamp - mTimeSeconds;
        mTimeSeconds = timeStamp;
        mTimeNanoSeconds = mTimeSeconds * 1e9;
        mComponentTimeOffsetNanoSeconds = timeOffset;

        mTimeDifferenceNanoSeconds = 0;
        // (mIsaacCApiPtr->isaac_get_external_time_difference)(mAppHandle, mTimeSeconds, &mTimeDifferenceNanoSeconds);
    }

    virtual gxf_result_t setGxfContext(int64_t context = 0)
    {
        if (context)
        {
            mContext = reinterpret_cast<void*>(context);
        }
        else
        {
            if (mGxfBridge->getDefaultContextHandle())
            {
                mContext = reinterpret_cast<void*>(mGxfBridge->getDefaultContextHandle());
            }
            else
            {
                CARB_LOG_ERROR("GXF app not started");
                return GXF_FAILURE;
            }
        }

        {
            gxf_uid_t eid;
            GxfEntityFind(mContext, "isaac_sim_allocator", &eid);
            gxf_tid_t tid;
            GxfComponentTypeId(mContext, nvidia::TypenameAsString<nvidia::gxf::UnboundedAllocator>(), &tid);
            gxf_uid_t cid;
            GxfComponentFind(mContext, eid, tid, "allocator", nullptr, &cid);
            auto allocator = nvidia::gxf::Handle<nvidia::gxf::Allocator>::Create(mContext, cid);
            if (!allocator)
            {
                CARB_LOG_ERROR("isaac_sim_allocator entity not found");
                return nvidia::gxf::ToResultCode(allocator);
            }
            mAllocator = std::move(allocator.value());
        }

        {
            gxf_uid_t eid;
            GxfEntityFind(mContext, "atlas", &eid);
            gxf_tid_t tid;
            GxfComponentTypeId(mContext, nvidia::TypenameAsString<nvidia::isaac::AtlasFrontend>(), &tid);
            gxf_uid_t cid;
            GxfComponentFind(mContext, eid, tid, "frontend", nullptr, &cid);
            auto atlas = nvidia::gxf::Handle<nvidia::isaac::AtlasFrontend>::Create(mContext, cid);
            if (!atlas)
            {
                CARB_LOG_ERROR("atlas entity not found");
                return nvidia::gxf::ToResultCode(atlas);
            }
            mAtlas = std::move(atlas.value());
        }

        return GXF_SUCCESS;
    }

private:
protected:
    omni::isaac::gxf_bridge::GxfBridge* mGxfBridge = nullptr;
    gxf_context_t mContext = nullptr;
    nvidia::gxf::Handle<nvidia::gxf::Allocator> mAllocator;
    nvidia::gxf::Handle<nvidia::isaac::AtlasFrontend> mAtlas;
    gxf_result_t mError = gxf_result_t::GXF_SUCCESS;

    int64_t mTimeDifferenceNanoSeconds = 0;
    int64_t mComponentTimeOffsetNanoSeconds = 0;
    double mTimeSeconds = 0; // current time in seconds
    int64_t mTimeNanoSeconds = 0; // current time in nano seconds
    double mTimeDelta = 0; // delta time for current tick
    GxfPoseTreeMap* mPoseTreeMap;
};
}
}
}
