// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "GxfStructs.h"
#include "gxf/core/gxf.h"
#include "plugins/core/Component.h"
#include "plugins/core/UsdUtilities.h"

#include <carb/profiler/Profile.h>

#include <engine/core/time.hpp>
#include <gxf/core/entity.hpp>
#include <gxf/std/double_buffer_receiver.hpp>
#include <gxf/std/tensor.hpp>
#include <gxf/std/timestamp.hpp>
#include <packages/engine_c_api/isaac_c_api_error.h>
#include <robotEngineBridgeSchema/robotEngineBridgeComponent.h>

#include <inttypes.h>
#include <string>
#include <vector>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{
namespace gxf_bridge
{
/**
 * @brief Base class which exchanges data with an Isaac SDK application.
 * This class provides helper functions to facilitate the data exchange.
 */
template <typename PrimType>
class GxfComponentBase : public utils::ComponentBase<PrimType>
{
public:
    /**
     * @brief Initialize various pointers and handles in the component
     * Must be called after creation, can be overridden to initialize subcomponents
     *
     * @param gxfContext
     * @param prim
     * @param stage
     */

    virtual void initialize(const gxf_context_t& gxfContext,
                            const nvidia::gxf::Handle<nvidia::gxf::Allocator>& allocator,
                            const PrimType& prim,
                            pxr::UsdStageWeakPtr stage)
    {
        utils::ComponentBase<PrimType>::initialize(prim, stage);
        mContext = gxfContext;
        mAllocator = allocator;

        // gxf_uid_t eid;
        // GxfEntityCreate(mContext, &eid);
        // gxf_tid_t tid;
        // GxfComponentTypeId(mContext, "nvidia::gxf::UnboundedAllocator", &tid);
        // gxf_uid_t cid;
        // GxfComponentAdd(mContext, eid, tid, "allocator", &cid);
        // GxfParameterSetInt32(mContext, cid, "storage_type", 0);
        // GxfParameterSetBool(mContext, cid, "do_not_use_cuda_malloc_host", true);
        // void* pointer;
        // GxfComponentPointer(mContext, cid, tid, &pointer);
        // nvidia::gxf::Allocator* allocator = static_cast<nvidia::gxf::Allocator*>(pointer);
        // allocator->initialize();
    }
    /**
     * @brief Function that runs after start is pressed
     *
     */
    virtual void onStart()
    {
    }
    /**
     * @brief Function that runs after stop is pressed
     *
     */
    virtual void onStop()
    {
    }
    /**
     * @brief Called every frame
     *
     */
    virtual void tick(){};

    /**
     * @brief Publish any Messages
     *
     */
    virtual void publishAllMessages(){};

    /**
     * @brief Called every time the Prim is changed
     *
     */
    virtual void onComponentChange()
    {
        isaac::utils::safeGetAttribute(this->mPrim.GetNodeNameAttr(), mNodeName);
        isaac::utils::safeGetAttribute(this->mPrim.GetEnabledAttr(), this->mEnabled);
        double timeOffset = 0;
        isaac::utils::safeGetAttribute(this->mPrim.GetTimeOffsetAttr(), timeOffset);
        mComponentTimeOffsetNanoSeconds = static_cast<int64_t>(timeOffset);
    }

    /**
     * @brief Update timestamps for component
     *
     * @param timeSeconds
     * @param dt
     * @param timeNano
     * @param timeDifferenceNano
     */
    virtual void updateTimestamp(double timeSeconds, double dt, int64_t timeNano, int64_t timeDifferenceNano)
    {
        this->mTimeNanoSeconds = timeNano;
        mTimeDifferenceNanoSeconds = timeDifferenceNano;
        this->mTimeSeconds = timeSeconds;
        this->mTimeDelta = dt;
    }


    /**
     * @brief Returns true if the error code is set to success.
     *
     * @param code
     * @return true
     * @return false
     */
    bool checkErrorCode(const gxf_result_t& code)
    {
        return code == gxf_result_t::GXF_SUCCESS;
    }

    /**
     * @brief Publishes serialized JSON string. Used for messages whose json data can be cached.
     *
     * @tparam T
     * @param component
     * @param channel
     * @param data
     * @param protoId
     * @param buffers
     * @return true
     * @return false
     */
    gxf_result_t publish(const std::string& component, const std::string& channel, const nvidia::gxf::Entity& data)
    {
        // Component //mNodeName
        // Entity //component
        // Channel //channel


        // // Get memory allocator (can I make this instead of accessing the existing one?)
        // gxf_uid_t tcp_eid;
        // GxfEntityFind(mContext, mNodeName, &tcp_eid);
        // gxf_tid_t allocator_tid;
        // GxfComponentTypeId(mContext, nvidia::TypenameAsString<nvidia::gxf::BlockMemoryPool>(), &allocator_tid);
        // gxf_uid_t allocator_cid;
        // GxfComponentFind(mContext, tcp_eid, allocator_tid, "allocator", nullptr, &allocator_cid);
        // auto allocator_ = nvidia::gxf::Handle<nvidia::gxf::Allocator>::Create(mContext, allocator_cid);
        // //TODO Handle case where allocator is not found


        // // Create a new message
        // auto message = nvidia::gxf::Entity::New(mContext);
        // auto timestamp = message.value().add<nvidia::gxf::Timestamp>("timestamp");
        // timestamp.value()->acqtime =
        //     this->mTimeNanoSeconds + mComponentTimeOffsetNanoSeconds; // TODO:  + mTimeDifferenceNanoSeconds;
        // // auto struct = message.value().add<data>(channel.c_str());


        // publish this tensor

        gxf_result_t result;
        gxf_uid_t tcp_eid;
        if ((result = GxfEntityFind(mContext, mNodeName.c_str(), &tcp_eid)))
        {
            CARB_LOG_ERROR("GxfEntityFind, %s", GxfResultStr(result));
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
            CARB_LOG_ERROR("GxfComponentFind, %s", GxfResultStr(result));
            return result;
        }
        auto pub_handle = nvidia::gxf::Handle<nvidia::gxf::DoubleBufferReceiver>::Create(mContext, pub_cid);

        if ((result = pub_handle.value()->push_abi(data.eid())))
        {
            CARB_LOG_ERROR("push_abi, %s", GxfResultStr(result));
            return result;
        }
        // CARB_LOG_ERROR("receiver size: %lu %lu", pub_handle.value()->size_abi(),
        // pub_handle.value()->back_size_abi());
        if ((result = pub_handle.value()->sync_abi()))
        {
            CARB_LOG_ERROR("sync_abi, %s", GxfResultStr(result));
            return result;
        }

        return gxf_result_t::GXF_SUCCESS;
    }

    /**
     * @brief General receive function without buffers
     *
     * @tparam T
     * @param component
     * @param channel
     * @param header
     * @param data
     * @return true
     * @return false
     */
    template <class T>
    gxf_result_t receive()
    {
        return gxf_result_t::GXF_SUCCESS;
    }

    // /**
    //  * @brief General receive function with buffers
    //  *
    //  * @tparam T
    //  * @param component
    //  * @param channel
    //  * @param header
    //  * @param data
    //  * @param buffers
    //  * @return true
    //  * @return false
    //  */
    // template <class T>
    // gxf_result_t receive()
    // {
    //     return gxf_result_t::GXF_SUCCESS;
    // }

    /**
     * @brief Set the Gxf Context
     *
     * @param gxfContext
     */
    virtual void setGxfContext(const gxf_context_t& gxfContext)
    {
        CARB_LOG_WARN("setGxfContext");
        mContext = gxfContext;
    }
    virtual void setGxfAllocator(const nvidia::gxf::Handle<nvidia::gxf::Allocator>& allocator)
    {
        CARB_LOG_WARN("setGxfAllocator");
        mAllocator = allocator;
    }

protected:
    gxf_context_t mContext = nullptr;
    nvidia::gxf::Handle<nvidia::gxf::Allocator> mAllocator;
    std::string mNodeName = "interface";
    gxf_result_t mError = gxf_result_t::GXF_SUCCESS;
    int64_t mTimeDifferenceNanoSeconds = 0;
    int64_t mComponentTimeOffsetNanoSeconds = 0;
};


typedef GxfComponentBase<pxr::RobotEngineBridgeSchemaRobotEngineBridgeComponent> GxfComponent;

}
}
}
}
