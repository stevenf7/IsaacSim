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

#include <carb/Defines.h>
#include <carb/Types.h>
#include <carb/events/EventsUtils.h>
#include <carb/logging/Logger.h>

#include <isaacsim/core/utils/BaseResetNode.h>
#include <isaacsim/core/utils/Conversions.h>
#include <isaacsim/core/utils/UsdUtilities.h>
#include <omni/fabric/FabricUSD.h>
#include <omni/usd/UsdContext.h>
#include <omni/usd/UsdContextIncludes.h>

#include <CoreNodes.h>
#include <DynamicControl.h>
#include <OgnIsaacJointNameResolverDatabase.h>
#include <unordered_map>

namespace isaacsim
{
namespace core
{
namespace nodes
{

class OgnIsaacJointNameResolver : public BaseResetNode
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnIsaacJointNameResolverDatabase::sPerInstanceState<OgnIsaacJointNameResolver>(nodeObj, instanceId);

        state.m_dynamicControlPtr = carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();

        if (!state.m_dynamicControlPtr)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::dynamic_control interface");
            return;
        }
        state.m_robotPath = "";
    }

    static bool compute(OgnIsaacJointNameResolverDatabase& db)
    {
        const GraphContextObj& context = db.abi_context();

        auto& state = db.perInstanceState<OgnIsaacJointNameResolver>();
        if (state.m_firstFrame)
        {

            const auto& prim = db.inputs.targetPrim();
            state.m_robotPath = std::string(db.inputs.robotPath()).c_str();

            // if robotPath field is empty
            if (std::strcmp(state.m_robotPath.c_str(), "") == 0)
            {

                // if targetPrim field is populated
                if (prim.size() > 0)
                {

                    state.m_robotPath = omni::fabric::toSdfPath(prim[0]).GetText();
                }
                else
                {
                    db.logError("OmniGraph Error: no articulation root prim found");
                    return false;
                }
            }


            state.m_firstFrame = false;
            // Find our stage
            long stageId = context.iContext->getStageId(context);
            auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));

            if (!stage)
            {
                db.logError("Could not find USD stage %ld", stageId);
                return false;
            }

            pxr::UsdPrim startPrim = stage->GetPrimAtPath(pxr::SdfPath(state.m_robotPath));

            if (!startPrim.IsValid())
            {
                db.logError("%s prim is invalid", state.m_robotPath);
                return false;
            }

            auto type = state.m_dynamicControlPtr->peekObjectType(state.m_robotPath.c_str());

            // Checking we have a valid articulation
            if (type == omni::isaac::dynamic_control::eDcObjectArticulation)
            {
                state.m_articulationHandle = state.m_dynamicControlPtr->getArticulation(state.m_robotPath.c_str());
                if (!state.m_articulationHandle)
                {
                    db.logError("Articulation not found for prim %s", state.m_robotPath);
                    return false;
                }
            }
            else
            {
                db.logError("%s prim is not a articulation root", state.m_robotPath);
                return false;
            }

            // Traverse from the starting prim
            for (const pxr::UsdPrim& prim : pxr::UsdPrimRange(startPrim))
            {

                std::string primNameOverride = isaacsim::core::utils::GetName(prim);
                std::string primName = prim.GetName();
                if (primNameOverride != primName)
                {
                    state.m_nameOverrideMap.insert({ primNameOverride, prim });
                }
            }
        }

        state.resolvePrims(db);

        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

    void resolvePrims(OgnIsaacJointNameResolverDatabase& db)
    {
        // Check if the input string is a key in the dictionary
        std::vector<std::string> resultList;

        db.outputs.jointNames.resize(db.inputs.jointNames().size());

        for (size_t i = 0; i < db.inputs.jointNames().size(); i++)
        {
            std::string primNameString = db.tokenToString(db.inputs.jointNames()[i]);
            auto it = m_nameOverrideMap.find(primNameString);
            if (it != m_nameOverrideMap.end())
            {
                // Add dictionary value if key exists
                db.outputs.jointNames().at(i) = db.stringToToken(it->second.GetName().GetText());
            }
            else
            {
                // Add original string if key doesn't exist
                db.outputs.jointNames().at(i) = db.stringToToken(primNameString.c_str());
            }
        }

        db.outputs.robotPath() = m_robotPath;
    }

    virtual void reset()
    {
        m_firstFrame = true;
        m_robotPath = "";
        m_nameOverrideMap.clear();
    }

private:
    omni::isaac::dynamic_control::DcHandle m_articulationHandle = omni::isaac::dynamic_control::kDcInvalidHandle;
    std::unordered_map<std::string, pxr::UsdPrim> m_nameOverrideMap;
    bool m_firstFrame = true;
    std::string m_robotPath;
    omni::isaac::dynamic_control::DynamicControl* m_dynamicControlPtr = nullptr;
};

REGISTER_OGN_NODE()
}
}
}
