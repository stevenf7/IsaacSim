// Copyright (c) 2022, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include "rclcpp/rclcpp.hpp"

#include <omni/isaac/utils/BaseResetNode.h>

#include <OgnROS2ContextDatabase.h>

class OgnROS2Context : public BaseResetNode
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnROS2ContextDatabase::sInternalState<OgnROS2Context>(nodeObj);
        state.mContext = std::make_shared<rclcpp::Context>();
    }
    static bool compute(OgnROS2ContextDatabase& db)
    {
        auto& state = db.internalState<OgnROS2Context>();

        // if the domain id has changed, reset the context
        if (state.mContext->is_valid() && state.mCleanup && db.inputs.domain_id() != state.mDomain)
        {
            state.mContext->shutdown("Omnigraph ROS2 Context node resetting");
        }

        if (!state.mContext->is_valid())
        {
            rcl_init_options_t initOptions = rcl_get_zero_initialized_init_options();
            if (rcl_init_options_init(&initOptions, rcl_get_default_allocator()) != RCL_RET_OK)
            {
                return false;
            }
            // Set the Domain ID of the context
            state.mDomain = db.inputs.domain_id();
            if (rcl_init_options_set_domain_id(&initOptions, state.mDomain) != RCL_RET_OK)
            {
                return false;
            }
            state.mContext->init(0, nullptr, rclcpp::InitOptions(initOptions));
            // We cast the shared ptr directly (and not the pointer inside of it)
            // This allows us to keep track of the shared pointer properly.
            db.outputs.context() = reinterpret_cast<uint64_t>(&state.mContext);
            rcl_init_options_fini(&initOptions);
            return true;
        }
        return true;
    }
    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnROS2ContextDatabase::sInternalState<OgnROS2Context>(nodeObj);
        state.reset();
        state.mContext.reset();
    }

    virtual void reset()
    {
        // We cannot actually destroy the context here because downstream nodes would fail
        // Instead perform cleanup on next frame
        mCleanup = true;
    }

private:
    std::shared_ptr<rclcpp::Context> mContext = nullptr;
    bool mCleanup = false;
    size_t mDomain = 0;
};

REGISTER_OGN_NODE()
