// Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include <include/Ros2Bridge.h>
#include <include/Ros2Factory.h>
#include <omni/isaac/utils/BaseResetNode.h>

#include <CoreNodes.h>
#include <OgnROS2ContextDatabase.h>

using namespace isaacsim::ros2::bridge;

class OgnROS2Context : public BaseResetNode
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2ContextDatabase::sPerInstanceState<OgnROS2Context>(nodeObj, instanceId);
        state.m_coreNodeFramework = carb::getCachedInterface<isaacsim::core::nodes::CoreNodes>();
        Ros2Bridge* ros2Bridge = carb::getCachedInterface<Ros2Bridge>();
        Ros2Factory* factory = ros2Bridge->getFactory();
        state.m_contextHandle = factory->createContextHandle();
    }

    static bool compute(OgnROS2ContextDatabase& db)
    {
        auto& state = db.perInstanceState<OgnROS2Context>();

        // If the domain id has changed, reset the context
        if (state.m_contextHandle->isValid() && state.m_cleanUp && db.inputs.domain_id() != state.m_domainId)
        {
            state.m_contextHandle->shutdown("Omnigraph ROS2 Context node resetting");
            state.m_cleanUp = false;
        }

        if (!state.m_contextHandle->isValid())
        {
            // Set the Domain ID of the context
            state.m_domainId = db.inputs.domain_id();
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
                    state.m_domainId = strtoul(domain_id_str, NULL, 0);

                    if (state.m_domainId == (std::numeric_limits<uint32_t>::max)())
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
                    CARB_LOG_INFO("ROS_DOMAIN_ID not found. Using input value of %zd", state.m_domainId);
                }
            }

            state.m_contextHandle->init(0, nullptr, true, state.m_domainId);
            // We cast the shared ptr directly (and not the pointer inside of it)
            // This allows us to keep track of the shared pointer properly.
            state.m_contextHandleAddr = state.m_coreNodeFramework->addHandle(&state.m_contextHandle);
            db.outputs.context() = state.m_contextHandleAddr;
            return true;
        }
        return true;
    }
    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state = OgnROS2ContextDatabase::sPerInstanceState<OgnROS2Context>(nodeObj, instanceId);
        state.reset();
        state.m_contextHandle.reset();
        state.m_coreNodeFramework->removeHandle(state.m_contextHandleAddr);
    }

    virtual void reset()
    {
        // We cannot actually destroy the context here because downstream nodes would fail.
        // Instead perform cleanup on next frame
        m_cleanUp = true;
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
    std::shared_ptr<Ros2ContextHandle> m_contextHandle = nullptr;
    bool m_cleanUp = false;
    size_t m_domainId = 0;
    uint64_t m_contextHandleAddr;
    isaacsim::core::nodes::CoreNodes* m_coreNodeFramework;
};

REGISTER_OGN_NODE()
