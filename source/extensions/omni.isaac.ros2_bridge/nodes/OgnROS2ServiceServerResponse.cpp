// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
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

#include "OgnROS2Utils.h"
#include "omni/isaac/utils/UsdUtilities.h"

#include <carb/Framework.h>
#include <carb/Types.h>

#include <include/Ros2Node.h>
#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/utils/Math.h>

#include <CoreNodes.h>
#include <OgnROS2ServiceServerResponseDatabase.h>


class OgnROS2ServiceServerResponse : public Ros2Node
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS2ServiceServerResponseDatabase::sPerInstanceState<OgnROS2ServiceServerResponse>(nodeObj, instanceId);
        state.mNodeObj = nodeObj;
        AttributeObj attrMessagePackageObj = nodeObj.iNode->getAttribute(nodeObj, "inputs:messagePackage");
        AttributeObj attrMessageSubfolderObj = nodeObj.iNode->getAttribute(nodeObj, "inputs:messageSubfolder");
        AttributeObj attrMessageNameObj = nodeObj.iNode->getAttribute(nodeObj, "inputs:messageName");
        AttributeObj attrHandle = nodeObj.iNode->getAttribute(nodeObj, "inputs:serverHandle");
        attrMessagePackageObj.iAttribute->registerValueChangedCallback(attrMessagePackageObj, onPackageChanged, true);
        attrMessageSubfolderObj.iAttribute->registerValueChangedCallback(attrMessageSubfolderObj, onPackageChanged, true);
        attrMessageNameObj.iAttribute->registerValueChangedCallback(attrMessageNameObj, onPackageChanged, true);
        attrHandle.iAttribute->registerValueChangedCallback(attrHandle, onServiceChanged, true);
        state.mCoreNodeFramework = carb::getCachedInterface<omni::isaac::core_nodes::CoreNodes>();
    }

    static bool compute(OgnROS2ServiceServerResponseDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();
        auto& state = db.perInstanceState<OgnROS2ServiceServerResponse>();
        const auto& nodeObj = db.abi_node();
        // spin once calls reset automatically if it was not successful
        if (!state.spinOnce(
                std::string(nodeObj.iNode->getPrimPath(nodeObj)), db.inputs.nodeNamespace(), db.inputs.context()))
        {
            return false;
        }

        auto messagePackage = std::string(db.inputs.messagePackage());
        auto messageSubfolder = std::string(db.inputs.messageSubfolder());
        auto messageName = std::string(db.inputs.messageName());
        uint64_t serverHandle = db.inputs.serverHandle();

        if (messagePackage.size() == 0 || messageSubfolder.size() == 0 || messageName.size() == 0)
        {
            db.logWarning("messagePackage [%s] or messageSubfolder [%s] or messageName [%s] empty, skipping compute",
                          messagePackage.c_str(), messageSubfolder.c_str(), messageName.c_str());
            return false;
        }

        if (messagePackage != state.mMessagePackage)
        {
            state.mIsMessageUpdateNeeded = true;
            state.mMessagePackage = messagePackage;
        }
        if (messageSubfolder != state.mMessageSubfolder)
        {
            state.mIsMessageUpdateNeeded = true;
            state.mMessageSubfolder = messageSubfolder;
        }
        if (messageName != state.mMessageName)
        {
            state.mIsMessageUpdateNeeded = true;
            state.mMessageName = messageName;
        }
        if (serverHandle != state.mServerHandle || !state.mServiceServer)
        {
            if (db.inputs.serverHandle())
            {
                void* voidPtr = state.mCoreNodeFramework->getHandle(db.inputs.serverHandle());
                if (voidPtr == nullptr)
                {
                    // CARB_LOG_WARN("CONTEXT DOES NOT EXIST");
                    return false;
                }
                state.mIsMessageUpdateNeeded = true;
                state.mServerHandle = serverHandle;
                state.mServiceServer = *reinterpret_cast<std::shared_ptr<Ros2Service>*>(voidPtr);
            }
        }

        // update message and node attributes
        if (state.mIsMessageUpdateNeeded)
        {
            state.updateNodeState<false>(db, nodeObj, state.mMessagePackage, state.mMessageSubfolder, state.mMessageName);
            state.mIsMessageUpdateNeeded = false;
        }

        // ServiceServer was not valid, create a new one
        if (state.mServiceServer)
        {
            return state.serviceServer(db, context);
        }
        return false;
    }


    bool serviceServer(OgnROS2ServiceServerResponseDatabase& db, const GraphContextObj& context)
    {
        auto& state = db.perInstanceState<OgnROS2ServiceServerResponse>();

        // Check if all sub-message size match size of actuators before setting data
        if (!state.mServiceServer->isValid())
        {
            db.logWarning("service is invalid");
            return false;
        }
        // CARB_LOG_ERROR("Server: writeMessageDataFromNode ...");
        // write response of the node from the input to the message
        OgnDynamicMesssageUtils::writeMessageDataFromNode(db, state.mMessageResponse, "Response:", false);
        state.mServiceServer->sendResponse(state.mMessageResponse->ptr());

        // only if the server received a request
        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

    static void releaseInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnROS2ServiceServerResponseDatabase::sPerInstanceState<OgnROS2ServiceServerResponse>(nodeObj, instanceId);
        state.reset();
    }

    virtual void reset()
    {
        mServiceServer.reset(); // This should be reset before we reset the handle.
        Ros2Node::reset();
    }

private:
    std::shared_ptr<Ros2Service> mServiceServer = nullptr;
    std::shared_ptr<Ros2Message> mMessageResponse = nullptr;

    bool mIsMessageUpdateNeeded = true;
    NodeObj mNodeObj;
    uint64_t mServerHandle = 0;
    std::string mMessagePackage;
    std::string mMessageSubfolder;
    std::string mMessageName;

    omni::isaac::core_nodes::CoreNodes* mCoreNodeFramework;

    template <bool removeAttributes>
    void updateNodeState(OgnROS2ServiceServerResponseDatabase& db,
                         const NodeObj& nodeObj,
                         std::string messagePackage,
                         std::string messageSubfolder,
                         std::string messageName)
    {
        CARB_LOG_WARN("service package information changed. Updating OgnROS2ServiceServerResponse node interface.");
        auto& state = db.perInstanceState<OgnROS2ServiceServerResponse>();

        if (removeAttributes)
        {
            if (!OgnDynamicMesssageUtils::removeDynamicAttributes<true, true>(nodeObj))
            {
                db.logError("Unable to remove existing attributes from the node");
                return;
            }
        }

        if (messagePackage.size() == 0 || messageSubfolder.size() == 0 || messageName.size() == 0)
        {
            db.logWarning("messagePackage [%s] or messageSubfolder [%s] or messageName [%s] empty, skipping compute",
                          messagePackage.c_str(), messageSubfolder.c_str(), messageName.c_str());
            return;
        }

        // build message attributes
        state.mMessageResponse = state.mFactory->createDynamicMessage(
            messagePackage, messageSubfolder, messageName, BackendMessageType::eResponse);
        OgnDynamicMesssageUtils::createOgAttributesForMessage<OgnROS2ServiceServerResponseDatabase, false, false>(
            db, nodeObj, messagePackage, messageSubfolder, messageName, state.mMessageResponse, "Response:");
    }

    static void onPackageChanged(AttributeObj const& attrObj, void const* userData)
    {
        // get message package, subfolder and name
        NodeObj nodeObj = attrObj.iAttribute->getNode(attrObj);
        auto db = OgnROS2ServiceServerResponseDatabase(nodeObj);
        auto& state = db.perInstanceState<OgnROS2ServiceServerResponse>();
        std::string messagePackage = std::string(db.inputs.messagePackage());
        std::string messageSubfolder = std::string(db.inputs.messageSubfolder());
        std::string messageName = std::string(db.inputs.messageName());
        state.updateNodeState<true>(db, nodeObj, messagePackage, messageSubfolder, messageName);
        state.mIsMessageUpdateNeeded = true;
    }

    static void onServiceChanged(AttributeObj const& attrObj, void const* userData)
    {
        // get message package, subfolder and name
        NodeObj nodeObj = attrObj.iAttribute->getNode(attrObj);
        auto db = OgnROS2ServiceServerResponseDatabase(nodeObj);
        auto& state = db.perInstanceState<OgnROS2ServiceServerResponse>();
        uint64_t serverHandle = db.inputs.serverHandle();
        if (serverHandle != state.mServerHandle)
        {
            if (serverHandle)
            {
                void* voidPtr = state.mCoreNodeFramework->getHandle(serverHandle);
                if (voidPtr == nullptr)
                {
                    // CARB_LOG_WARN("CONTEXT DOES NOT EXIST");
                    return;
                }

                state.mServiceServer = *reinterpret_cast<std::shared_ptr<Ros2Service>*>(voidPtr);
                state.mServerHandle = serverHandle;
                state.updateNodeState<true>(
                    db, nodeObj, state.mMessagePackage, state.mMessageSubfolder, state.mMessageName);
            }
        }
    }
};

REGISTER_OGN_NODE()
