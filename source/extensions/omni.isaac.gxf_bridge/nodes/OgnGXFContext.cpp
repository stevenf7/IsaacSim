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
            // Parse GXF app YAML strings
            const auto& graph = db.inputs.graph();
            std::vector<std::string> graphStrings;
            if (graph.type().baseType == BaseDataType::eUChar && graph.type().arrayDepth == 1)
            {
                auto val = db.inputs.graph().template get<uint8_t[]>();
                if (!val)
                {
                    db.logError("Failed to resolve input type, expecting string.");
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
                        db.logError("Failed to resolve input type, expecting token.");
                        return false;
                    }
                    graphStrings.push_back(std::string(db.tokenToString(*val)));
                }
                else if (graph.type().arrayDepth == 1)
                {
                    auto val = db.inputs.graph().template get<OgnToken[]>();
                    if (!val)
                    {
                        db.logError("Failed to resolve input type, expecting 1d token[].");
                        return false;
                    }
                    const auto graphTokens = *val;
                    graphStrings.resize(graphTokens.size());
                    std::transform(graphTokens.begin(), graphTokens.end(), graphStrings.begin(),
                                   [&db](auto t) { return db.tokenToString(t); });
                }
                else if (graph.type().arrayDepth == 2)
                {
                    db.logError("Failed to resolve input, 2d token[][] not supported");
                    return false;
                }
            }
            else
            {
                db.logError("Type must be string, token or token[]");
                return false;
            }

            // Parse GXF context severity
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
            else if (db.inputs.severity() == db.tokens.verbose)
            {
                severity = gxf_severity_t::GXF_SEVERITY_VERBOSE;
            }

            // Create GXF context
            gxf_result_t result;
            result = state.mContext->create();
            if (result)
            {
                db.logError("Failed to create GXF context.");
                state.mContext->destroy();
                return false;
            }

            // Set GXF context severity
            state.mContext->setSeverity(severity);

            // Load GXF manifest
            result = state.mContext->loadManifest(state.mExtensionPath + "/lib", "manifest.yaml");
            if (result)
            {
                db.logError("Failed to load GXF manifest.");
                state.mContext->destroy();
                return false;
            }

            // Load GXF graphs from strings
            result = state.mContext->loadGraphsFromString(graphStrings);
            if (result)
            {
                db.logError("Failed to load specified GXF graph(s).");
                state.mContext->destroy();
                return false;
            }

            // Load internal graphs - allocator used to build composite messages
            std::vector<std::string> internalGraphs;
            internalGraphs.push_back(state.mExtensionPath + "/data/config/isaac_sim_allocator.yaml");
            result = state.mContext->loadGraphsFromFile(internalGraphs);
            if (result)
            {
                db.logError("Failed to load isaac_sim_allocator.yaml.");
                state.mContext->destroy();
                return false;
            }

            // Start GXF application
            result = state.mContext->start(db.inputs.clockEntity(), db.inputs.clockComponent(), db.inputs.atlasEntity(),
                                           db.inputs.atlasComponent());
            if (result)
            {
                db.logError("Failed to start GXF application.");
                state.mContext->stop();
                state.mContext->destroy();
                return false;
            }
            state.mHandle = state.mCoreNodeFramework->addHandle(&state.mContext);
            db.outputs.context() = state.mHandle;
            return true;
        }
        return false;
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
