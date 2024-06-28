// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "../core/BaseSensorComponent.h"

#include <extensions/PxSceneQueryExt.h>
#include <isaacSensorSchema/isaacLightBeamSensor.h>
#include <omni/physx/IPhysx.h>
#include <omni/usd/UsdUtils.h>
#include <omni/usd/UtilsIncludes.h>
#include <pxr/usd/usd/inherits.h>
#include <usdrt/gf/matrix.h>
#include <usdrt/gf/vec.h>

#include <IsaacSensor.h>
#include <vector>

namespace omni
{
namespace isaac
{
namespace sensor
{
class LightBeamSensor : public IsaacBaseSensorComponent
{

public:
    LightBeamSensor(omni::physx::IPhysx* PhysXInterface) : IsaacBaseSensorComponent()
    {
        mPhysx = PhysXInterface;
    };
    virtual ~LightBeamSensor(){};

    virtual void preTick(){};
    virtual void tick(){};
    virtual void onStop(){};

    virtual void onPhysicsStep();

    void onComponentChange();

    int getNumRays() const
    {
        return mNumRays;
    }

    std::vector<uint8_t>& getBeamHitData()
    {
        return mBeamHit;
    }

    // get most recent linear depth data
    std::vector<float>& getLinearDepthData()
    {
        return mLinearDepth;
    }

    // get most recent hit pos data
    std::vector<carb::Float3>& getHitPosData()
    {
        return mHitPos;
    }

    // get transform of sensor
    void getTransformData(omni::math::linalg::matrix4d& matrixOutput)
    {
        // quatd is i,j,k,w, but constructor is quatd(w, i, j, k)
        omni::math::linalg::vec3d pos{ mWorldTranslation.x, mWorldTranslation.y, mWorldTranslation.z };
        omni::math::linalg::quatd rot{ mWorldRotation.w, mWorldRotation.x, mWorldRotation.y, mWorldRotation.z };
        matrixOutput.SetIdentity();
        matrixOutput.SetRotateOnly(rot);
        matrixOutput.SetTranslateOnly(pos);
    }

    // get array of beam origins
    std::vector<carb::Float3>& getBeamOrigins()
    {
        return mBeamOrigins;
    }

    // get array of beam end points
    std::vector<carb::Float3>& getBeamEndPoints()
    {
        return mBeamEndPoints;
    }

private:
    void scan(const ::physx::PxVec3& origin, const ::physx::PxQuat& worldRotation);

    float mCurtainLength = 0.0f;
    int mNumRays = 1;
    pxr::GfVec3f mForwardAxis;
    pxr::GfVec3f mCurtainAxis;
    float mMinRange = 0.4f;
    float mMaxRange = 100.0f;
    float mMetersPerUnit = 1.0f;
    ::physx::PxVec3 mWorldTranslation;
    ::physx::PxQuat mWorldRotation;
    bool mPreviousEnabled = true;
    // we use uint8_t instead of bool because C++ doesn't support bool* pointer
    std::vector<uint8_t> mBeamHit; // 0 false, 1 true
    std::vector<carb::Float3> mBeamOrigins;
    std::vector<carb::Float3> mBeamEndPoints;

    // for ray cast
    float mMinDepth = 0.0f;
    float mMaxDepth = 1e8;
    std::vector<float> mLinearDepth;
    omni::physx::IPhysx* mPhysx = nullptr;
    ::physx::PxScene* mPxScene = nullptr;
    std::vector<carb::Float3> mHitPos;
    const ::physx::PxHitFlags mHitFlags = ::physx::PxHitFlag::eDEFAULT | ::physx::PxHitFlag::eMESH_BOTH_SIDES;
};


} // sensor
} // isaac
} // omni
