// Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
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

#include <omni/ext/ExtensionsUtils.h>
#include <omni/isaac/core_nodes/CoreNodes.h>
#include <omni/isaac/utils/BaseResetNode.h>
#include <omni/kit/IApp.h>
#include <plugins/Core/GxfContext.h>

#include <OgnGXFContextDatabase.h>
class OgnGXFContext : public BaseResetNode
{
public:
    static void initialize(const GraphContextObj& contextObj, const NodeObj& nodeObj)
    {
        auto& state = OgnGXFContextDatabase::sInternalState<OgnGXFContext>(nodeObj);
        state.mContext = std::make_shared<omni::isaac::gxf_bridge::GxfContext>();
        state.mCoreNodeFramework = carb::getCachedInterface<omni::isaac::core_nodes::CoreNodes>();

        omni::kit::IApp* app = carb::getCachedInterface<omni::kit::IApp>();
        if (!app)
        {
            CARB_LOG_ERROR("Failed to acquire omni::kit::IApp");
            return;
        }
        omni::ext::ExtensionManager* extManager = app->getExtensionManager();
        if (!extManager)
        {
            CARB_LOG_ERROR("Failed to get ExtensionManager");
            return;
        }
        state.mExtensionPath = getExtensionPath(extManager, getEnabledExtensionId(extManager, "omni.isaac.gxf_bridge"));
    }
    static bool compute(OgnGXFContextDatabase& db)
    {
        auto& state = db.internalState<OgnGXFContext>();
        if (state.mCleanup)
        {
            state.mContext->destroy();
            state.mCleanup = false;
        }
        if (!state.mContext->isActivated())
        {
            const auto& graph = db.inputs.graph();
            std::vector<std::string> graphStrings;
            if (graph.type().baseType == BaseDataType::eUChar && graph.type().arrayDepth == 1)
            {
                auto val = db.inputs.graph().template get<uint8_t[]>();
                if (!val)
                {
                    db.logError("Unable to resolve input type");
                    return false;
                }

                auto charData = val->data();
                graphStrings.push_back(std::string(charData, charData + val->size()));
            }
            else if (graph.type().baseType == BaseDataType::eToken)
            {
                if (graph.type().arrayDepth == 0)
                {
                    auto val = db.inputs.graph().template get<OgnToken>();
                    if (!val)
                    {
                        db.logError("Unable to resolve input type");
                        return false;
                    }
                    graphStrings.push_back(std::string(db.tokenToString(*val)));
                }
                else if (graph.type().arrayDepth == 1)
                {
                    auto val = db.inputs.graph().template get<OgnToken[]>();
                    if (!val)
                    {
                        db.logError("Unable to resolve input type");
                        return false;
                    }
                    const auto graphTokens = *val;
                    graphStrings.resize(graphTokens.size());
                    std::transform(graphTokens.begin(), graphTokens.end(), graphStrings.begin(),
                                   [&db](auto t) { return db.tokenToString(t); });
                }
                else if (graph.type().arrayDepth == 2)
                {
                    db.logError("array of array as input not supported");
                    return false;
                }
            }
            else
            {
                db.logError("Type must be string, token or roken[]");
                return false;
            }
            gxf_severity_t severity = gxf_severity_t::GXF_SEVERITY_INFO;

            if (db.inputs.severity() == db.tokens.none)
            {
                severity = gxf_severity_t::GXF_SEVERITY_NONE;
            }
            else if (db.inputs.severity() == db.tokens.error)
            {
                severity = gxf_severity_t::GXF_SEVERITY_ERROR;
            }
            else if (db.inputs.severity() == db.tokens.warning)
            {
                severity = gxf_severity_t::GXF_SEVERITY_WARNING;
            }
            else if (db.inputs.severity() == db.tokens.info)
            {
                severity = gxf_severity_t::GXF_SEVERITY_INFO;
            }
            else if (db.inputs.severity() == db.tokens.debug)
            {
                severity = gxf_severity_t::GXF_SEVERITY_DEBUG;
            }
            else if (db.inputs.severity() == db.tokens.debug)
            {
                severity = gxf_severity_t::GXF_SEVERITY_VERBOSE;
            }
            gxf_result_t result;
            if (result = state.mContext->create())
            {
                db.logError("Graph not created");
                state.mContext->destroy();
                return false;
            }
            state.mContext->setSeverity(severity);

            if (result = state.mContext->loadManifest(state.mExtensionPath + "/lib", "manifest.yaml"))
            {
                db.logError("manifest not loaded");
                state.mContext->destroy();
                return false;
            }
            if (result = state.mContext->loadGraphsFromString(graphStrings))
            {
                db.logError("specified graphs not loaded");
                state.mContext->destroy();
                return false;
            }
            std::vector<std::string> internalGraphs;
            internalGraphs.push_back(state.mExtensionPath + "/data/config/isaac_sim_allocator.yaml");

            if (result = state.mContext->loadGraphsFromFile(internalGraphs))
            {
                db.logError("isaac_sim_allocator graph not loaded");
                state.mContext->destroy();
                return false;
            }

            if (result = state.mContext->start(db.inputs.clockEntity(), db.inputs.clockComponent(),
                                               db.inputs.atlasEntity(), db.inputs.atlasComponent()))
            {
                db.logError("graph not started");
                state.mContext->stop();
                state.mContext->destroy();
                return false;
            }
            state.mHandle = state.mCoreNodeFramework->addHandle(&state.mContext);
            db.outputs.context() = state.mHandle;
            return true;
        }
    }
    static void release(const NodeObj& nodeObj)
    {
        auto& state = OgnGXFContextDatabase::sInternalState<OgnGXFContext>(nodeObj);
        state.reset();
        state.mContext.reset();
    }

    virtual void reset()
    {
        if (mContext->isRunning())
        {
            mContext->stop();
        }
        mCoreNodeFramework->removeHandle(mHandle);
        // We cannot actually destroy the context here because downstream nodes would fail
        // Instead perform cleanup on next frame
        mCleanup = true;
    }


private:
    std::shared_ptr<omni::isaac::gxf_bridge::GxfContext> mContext = nullptr;
    bool mCleanup = false;
    std::string mExtensionPath;
    uint64_t mHandle;
    omni::isaac::core_nodes::CoreNodes* mCoreNodeFramework;
};

REGISTER_OGN_NODE()
