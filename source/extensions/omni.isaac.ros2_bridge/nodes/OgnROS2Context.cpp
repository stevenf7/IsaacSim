// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#include <include/Ros2Bridge.h>
#include <include/Ros2Factory.h>
#include <omni/isaac/utils/BaseResetNode.h>

#include <CoreNodes.h>
#include <OgnROS2ContextDatabase.h>

class OgnROS2Context : public BaseResetNode
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2ContextDatabase::sPerInstanceState<OgnROS2Context>(nodeObj, instanceId);
        state.mCoreNodeFramework = carb::getCachedInterface<omni::isaac::core_nodes::CoreNodes>();
        omni::isaac::ros2_bridge::Ros2Bridge* mRos2Bridge =
            carb::getCachedInterface<omni::isaac::ros2_bridge::Ros2Bridge>();
        Ros2Factory* mFactory = mRos2Bridge->getFactory();
        state.mContext = mFactory->CreateHandle();
    }
    static bool compute(OgnROS2ContextDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2Context>();

        // if the domain id has changed, reset the context
        if (state.mContext->is_valid() && state.mCleanup && db.inputs.domain_id() != state.mDomain)
        {
            state.mContext->shutdown("Omnigraph ROS2 Context node resetting");
            state.mCleanup = false;
        }

        if (!state.mContext->is_valid())
        {

            // Set the Domain ID of the context
            state.mDomain = db.inputs.domain_id();
            const bool useDomainIDEnvVar = db.inputs.useDomainIDEnvVar();

            if (useDomainIDEnvVar)
            {
                char* domain_id_str = nullptr;

#ifdef _MSC_VER

                size_t sz = 0;
                _dupenv_s(&domain_id_str, &sz, "ROS_DOMAIN_ID");
#else
                domain_id_str = getenv("ROS_DOMAIN_ID");
#endif

                if (domain_id_str != NULL)
                {
                    state.mDomain = strtoul(domain_id_str, NULL, 0);

                    if (state.mDomain == (std::numeric_limits<uint32_t>::max)())
                    {

                        CARB_LOG_INFO("ROS_DOMAIN_ID: %s could not be interpreted as a legal number", domain_id_str);
#ifdef _MSC_VER
                        free(domain_id_str);
#endif
                        return false;
                    }
#ifdef _MSC_VER
                    free(domain_id_str);
#endif
                }
                else
                {
                    CARB_LOG_INFO("ROS_DOMAIN_ID not found. Using input value of %zd", state.mDomain);
                }
            }

            state.mContext->init(0, nullptr, true, state.mDomain);
            // We cast the shared ptr directly (and not the pointer inside of it)
            // This allows us to keep track of the shared pointer properly.
            state.mHandle = state.mCoreNodeFramework->addHandle(&state.mContext);
            // CARB_LOG_WARN("GEN CONTEXT %" PRIu64 "\n", state.mHandle);

            db.outputs.context() = state.mHandle;
            return true;
        }
        return true;
    }
    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2ContextDatabase::sPerInstanceState<OgnROS2Context>(nodeObj, instanceId);
        state.reset();
        state.mContext.reset();
        state.mCoreNodeFramework->removeHandle(state.mHandle);
    }

    virtual void reset()
    {
        // We cannot actually destroy the context here because downstream nodes would fail
        // Instead perform cleanup on next frame
        mCleanup = true;
    }
    static bool updateNodeVersion(const GraphContextObj& context, const NodeObj& nodeObj, int oldVersion, int newVersion)
    {
        if (oldVersion < newVersion)
        {
            if (oldVersion == 1)
            {
                // We added inputs:useDomainIDEnvVar, to maintain previous behavior we should set this to false
                const bool val{ false };
                nodeObj.iNode->createAttribute(nodeObj, "inputs:useDomainIDEnvVar", Type(BaseDataType::eBool), &val,
                                               nullptr, kAttributePortType_Input, kExtendedAttributeType_Regular,
                                               nullptr);
            }
            return true;
        }
        return false;
    }

private:
    std::shared_ptr<Ros2HandleBase> mContext = nullptr;
    bool mCleanup = false;
    size_t mDomain = 0;
    uint64_t mHandle;
    omni::isaac::core_nodes::CoreNodes* mCoreNodeFramework;
};

REGISTER_OGN_NODE()
