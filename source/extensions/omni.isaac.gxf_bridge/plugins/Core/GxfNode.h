// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once
#include "Core/GxfPoseTreeMap.h"
#include "Core/GxfStructs.h"
#include "gxf/core/gxf.h"
#include "omni/isaac/gxf_bridge/GxfBridge.h"
#include "omni/isaac/utils/BaseResetNode.h"

#include <carb/Defines.h>
#include <carb/Types.h>
#include <carb/events/EventsUtils.h>

#include <gxf/core/entity.hpp>
#include <gxf/core/expected.hpp>
#include <gxf/std/clock.hpp>
#include <gxf/std/double_buffer_receiver.hpp>
#include <gxf/std/double_buffer_transmitter.hpp>
#include <gxf/std/tensor.hpp>
#include <gxf/std/timestamp.hpp>
#include <gxf/std/unbounded_allocator.hpp>
#include <omni/isaac/core_nodes/CoreNodes.h>
#include <omni/usd/UsdContextIncludes.h>
//
#include "GxfContext.h"

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
        mCoreNodeFramework = carb::getCachedInterface<omni::isaac::core_nodes::CoreNodes>();
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
        auto maybe_pub_cid = getComponentCid(entity, component);
        if (!maybe_pub_cid)
        {
            return maybe_pub_cid.error();
        }
        auto pub_handle =
            nvidia::gxf::Handle<nvidia::gxf::DoubleBufferReceiver>::Create(getGxfContext(), maybe_pub_cid.value());

        if ((result = pub_handle.value()->push_abi(data.eid())))
        {
            CARB_LOG_ERROR("push_abi, %s", GxfResultStr(result));
            return result;
        }
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
        auto maybe_rec_cid = getComponentCid(entity, component);
        if (!maybe_rec_cid)
        {
            return maybe_rec_cid.error();
        }
        auto sub_handle =
            nvidia::gxf::Handle<nvidia::gxf::DoubleBufferReceiver>::Create(getGxfContext(), maybe_rec_cid.value());
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
            auto message = nvidia::gxf::Entity::Own(getGxfContext(), uid);
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
     * @brief Retrieves GXF component uid from current GXF context.
     *
     * @param entity Name of entity
     * @param component Name of component
     * @return gxf_result_t
     */
    nvidia::gxf::Expected<gxf_uid_t> getComponentCid(const std::string& entity_name, const std::string& component_name)
    {
        gxf_result_t result;
        gxf_uid_t eid;
        if (entity_name.size() == 0)
        {
            CARB_LOG_ERROR("Entity name not set.");
            return nvidia::gxf::Unexpected{ GXF_FAILURE };
        }
        if (component_name.size() == 0)
        {
            CARB_LOG_ERROR("Component name not set.");
            return nvidia::gxf::Unexpected{ GXF_FAILURE };
        }
        if ((result = GxfEntityFind(getGxfContext(), entity_name.c_str(), &eid)))
        {
            CARB_LOG_ERROR("Error in GxfEntityFind for %s: %s", entity_name.c_str(), GxfResultStr(result));
            return nvidia::gxf::Unexpected{ GXF_FAILURE };
        }
        gxf_tid_t tid;
        if ((result = GxfComponentTypeId(
                 getGxfContext(), nvidia::TypenameAsString<nvidia::gxf::DoubleBufferReceiver>(), &tid)))
        {
            CARB_LOG_ERROR("Error in GxfComponentTypeId: %s", GxfResultStr(result));
            return nvidia::gxf::Unexpected{ GXF_FAILURE };
        }
        gxf_uid_t cid;
        if ((result = GxfComponentFind(getGxfContext(), eid, tid, component_name.c_str(), nullptr, &cid)))
        {
            CARB_LOG_ERROR("Cannot find component %s in entity %s: %s", component_name.c_str(), entity_name.c_str(),
                           GxfResultStr(result));
            return nvidia::gxf::Unexpected{ GXF_FAILURE };
        }
        return cid;
    }


    // virtual void setPoseTreeMap(GxfPoseTreeMap* poseTreeMap)
    // {
    //     // CARB_LOG_WARN("setPoseTreeMap");
    //     mPoseTreeMap = poseTreeMap;
    // }
    //**

    /**
     * @brief Get the Gxf Context object
     *
     * @return gxf_context_t
     */
    gxf_context_t getGxfContext()
    {
        if (mContext && mContext->get())
        {
            return (*mContext)->gxfContext();
        }
        else
        {
            return nullptr;
        }
    }
    /**
     * @brief Set the Gxf Context object
     *
     * @param context
     * @return gxf_result_t
     */
    virtual gxf_result_t setGxfContext(uint64_t contexthandle = 0)
    {
        if (contexthandle)
        {
            void* voidPtr = mCoreNodeFramework->getHandle(contexthandle);
            if (voidPtr == nullptr)
            {
                // CARB_LOG_WARN("CONTEXT DOES NOT EXIST");
                return GXF_FAILURE;
            }

            mContext = reinterpret_cast<std::shared_ptr<omni::isaac::gxf_bridge::GxfContext>*>(voidPtr);
        }
        else
        {
            if (mGxfBridge->getDefaultContextHandle())
            {
                mContext = reinterpret_cast<std::shared_ptr<omni::isaac::gxf_bridge::GxfContext>*>(
                    mGxfBridge->getDefaultContextHandle());
            }
            else
            {
                CARB_LOG_WARN("GXF app not started");
                return GXF_FAILURE;
            }
        }
        // If the app is running then we should have found all of the components and the gxf context can be used.
        if ((*mContext)->isRunning())
        {
            mAllocator = std::move((*mContext)->allocator());
            mAtlas = std::move((*mContext)->atlas());
            mClock = std::move((*mContext)->clock());
            return GXF_SUCCESS;
        }
        else
        {
            CARB_LOG_WARN("GXF app not started");
            return GXF_FAILURE;
        }
    }
    /**
     * @brief Given a frame, find it in the atlas instance attached to the context
     *
     * @param frame
     * @return uint64_t
     */
    uint64_t findFrameUid(const char* frame)
    {
        auto maybe_frame = mAtlas->pose_tree().findFrame(frame);
        if (!maybe_frame)
        {
            CARB_LOG_ERROR("Atlas frame %s not found", frame);
            return 0;
        }
        else
        {
            return maybe_frame.value();
        }
    }

private:
protected:
    omni::isaac::gxf_bridge::GxfBridge* mGxfBridge = nullptr;
    std::shared_ptr<omni::isaac::gxf_bridge::GxfContext>* mContext = nullptr;

    nvidia::gxf::Handle<nvidia::gxf::UnboundedAllocator> mAllocator;
    nvidia::gxf::Handle<nvidia::gxf::Clock> mClock;
    nvidia::gxf::Handle<nvidia::isaac::AtlasFrontend> mAtlas;

    int64_t mTimeDifferenceNanoSeconds = 0;
    int64_t mComponentTimeOffsetNanoSeconds = 0;
    double mTimeSeconds = 0; // current time in seconds
    int64_t mTimeNanoSeconds = 0; // current time in nano seconds
    double mTimeDelta = 0; // delta time for current tick

    omni::isaac::core_nodes::CoreNodes* mCoreNodeFramework;
};
}
}
}
