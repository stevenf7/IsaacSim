// Copyright (c) 2021-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include "../core/RangeSensorComponent.h"
#include "UltrasonicArrayEmissionTimer.h"
#include "omni/isaac/utils/UsdUtilities.h"

#include <omni/usd/UtilsIncludes.h>
//
#include <omni/usd/UsdUtils.h>
//
#include <pxr/base/gf/vec2i.h>
#include <pxr/usd/usd/inherits.h>
#include <rangeSensorSchema/ultrasonicFiringGroup.h>

#include <RangeSensorInterface.h>
#include <vector>

namespace omni
{
namespace isaac
{
namespace range_sensor
{

class UltrasonicFiringGroup : public utils::ComponentBase<pxr::RangeSensorUltrasonicFiringGroup>
{
public:
    UltrasonicFiringGroup() : mIsReceiving(2, std::vector<bool>()), mIsFiring(2, std::vector<bool>())
    {
    }


    void initialize(const pxr::RangeSensorUltrasonicFiringGroup& prim, pxr::UsdStageWeakPtr stage, const size_t numEmitters)
    {
        utils::ComponentBase<pxr::RangeSensorUltrasonicFiringGroup>::initialize(prim, stage);
        mNumEmitters = numEmitters;

        onComponentChange();
    }


    void onStart()
    {
    }

    void tick()
    {
    }

    void onComponentChange()
    {
        isaac::utils::safeGetAttribute(mPrim.GetEmitterModesAttr(), mEmitterModes);
        isaac::utils::safeGetAttribute(mPrim.GetReceiverModesAttr(), mReceiverModes);

        mIsFiring[mFreqIdLow] = modesToBooleanVector(mEmitterModes, mFreqIdLow, mNumEmitters);
        mIsFiring[mFreqIdHigh] = modesToBooleanVector(mEmitterModes, mFreqIdHigh, mNumEmitters);
        mIsReceiving[mFreqIdLow] = modesToBooleanVector(mReceiverModes, mFreqIdLow, mNumEmitters);
        mIsReceiving[mFreqIdHigh] = modesToBooleanVector(mReceiverModes, mFreqIdHigh, mNumEmitters);
    }

    pxr::VtArray<pxr::GfVec2i> mEmitterModes;
    pxr::VtArray<pxr::GfVec2i> mReceiverModes;

    std::vector<std::vector<bool>> mIsReceiving;
    std::vector<std::vector<bool>> mIsFiring;

private:
    // List of (emitter index, firing mode) pairs for each sensor in this group to emit from
    std::vector<bool> modesToBooleanVector(const pxr::VtArray<pxr::GfVec2i>& modes,
                                           const size_t current_mode,
                                           const size_t num_emitters)
    {
        std::vector<bool> modeVector(modes.size(), false);
        for (size_t i = 0; i < modes.size(); i++)
        {
            if (static_cast<size_t>(modes[i][1]) == current_mode)
            {
                if ((static_cast<size_t>(modes[i][0]) >= 0) && (static_cast<size_t>(modes[i][0]) < num_emitters))
                {
                    // modes[i][0] is the emitter/receiver index
                    modeVector[modes[i][0]] = true;
                }
                else
                {
                    printf("Mode contained an emitter that does not exist: (%d, %d)\n", modes[i][0], modes[i][1]);
                }
            }
        }
        return modeVector;
    }


    const size_t mFreqIdLow = 0;
    const size_t mFreqIdHigh = 1;
    size_t mNumEmitters = 0;
};
}
}
}
