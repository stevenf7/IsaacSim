// Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
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

#include "omni/isaac/utils/UsdUtilities.h"

#include <omni/fabric/FabricUSD.h>
#include <omni/isaac/utils/Conversions.h>
#include <pxr/base/gf/quatd.h>
#include <pxr/base/gf/vec3d.h>

#include <IsaacSensor.h>
#include <OgnIsaacReadLightBeamSensorDatabase.h>


namespace omni
{
namespace isaac
{
namespace sensor
{
class OgnIsaacReadLightBeamSensor
{
public:
    static void initInstance(NodeObj const& nodeObj, GraphInstanceID instanceId)
    {
        auto& state =
            OgnIsaacReadLightBeamSensorDatabase::sPerInstanceState<OgnIsaacReadLightBeamSensor>(nodeObj, instanceId);

        state.mLightBeamSensorInterface = carb::getCachedInterface<LightBeamSensorInterface>();

        if (!state.mLightBeamSensorInterface)
        {
            CARB_LOG_ERROR("Failed to acquire omni::isaac::sensor interface");
            return;
        }
    }

    static bool compute(OgnIsaacReadLightBeamSensorDatabase& db)
    {
        auto& state = db.perInstanceState<OgnIsaacReadLightBeamSensor>();

        // Find our stage
        const GraphContextObj& context = db.abi_context();
        long stageId = context.iContext->getStageId(context);
        auto stage = pxr::UsdUtilsStageCache::Get().Find(pxr::UsdStageCache::Id::FromLongInt(stageId));
        if (!stage)
        {
            db.logError("Could not find USD stage %ld", stageId);
            return false;
        }
        double unitScale = UsdGeomGetStageMetersPerUnit(stage);
        const auto& prim = db.inputs.lightbeamPrim();
        const char* primPath;

        if (prim.size() > 0)
        {
            primPath = omni::fabric::toSdfPath(prim[0]).GetText();
        }
        else
        {
            db.logError("Invalid Light Beam Sensor prim");
            return false;
        }

        uint8_t* beamHitData = state.mLightBeamSensorInterface->getBeamHitData(primPath);
        float* linearDepthData = state.mLightBeamSensorInterface->getLinearDepthData(primPath);
        carb::Float3* hitPosData = state.mLightBeamSensorInterface->getHitPosData(primPath);
        int numRays = state.mLightBeamSensorInterface->getNumRays(primPath);

        for (int i = 0; i < numRays; i++)
        {
            state.mBeamHitData.push_back(beamHitData[i]);
            state.mLinearDepthData.push_back(linearDepthData[i]);
            state.mHitPosData.push_back(omni::isaac::utils::conversions::asGfVec3f(hitPosData[i]) * unitScale);
        }

        // fill in outputs
        db.outputs.beamHitData().resize(state.mBeamHitData.size());
        db.outputs.hitPosData().resize(state.mHitPosData.size());
        db.outputs.linearDepthData().resize(state.mLinearDepthData.size());
        memcpy(db.outputs.beamHitData().data(), &state.mBeamHitData[0], state.mBeamHitData.size() * sizeof(bool));
        memcpy(db.outputs.hitPosData().data(), &state.mHitPosData[0], state.mHitPosData.size() * sizeof(GfVec3f));
        memcpy(db.outputs.linearDepthData().data(), &state.mLinearDepthData[0],
               state.mLinearDepthData.size() * sizeof(float));

        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

private:
    LightBeamSensorInterface* mLightBeamSensorInterface = nullptr;
    std::vector<GfVec3f> mHitPosData;
    std::vector<float> mLinearDepthData;
    std::vector<uint8_t> mBeamHitData;
};


REGISTER_OGN_NODE()
} // sensor
} // graph
} // omni
