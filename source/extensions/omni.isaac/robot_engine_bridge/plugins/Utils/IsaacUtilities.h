#pragma once

#include "../Core/IsaacComponent.h"

#include <carb/filesystem/IFileSystem.h>

#include <omni/isaac/dynamic_control/DynamicControl.h>
#include <omni/usd/UsdUtils.h>

namespace omni
{
namespace isaac
{
namespace robot_engine_bridge
{
/**
 * @brief Set the transform of the object
 *
 * @param mDynamicControlPtr
 * @param prim
 * @param pxBodyTranslation
 * @param pxBodyRotation
 */
static void setTransform(omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr,
                         pxr::UsdPrim& prim,
                         pxr::GfVec3f pxBodyTranslation,
                         pxr::GfVec4f pxBodyRotation)
{
    omni::isaac::dynamic_control::DcTransform t;
    t.p = { pxBodyTranslation[0], pxBodyTranslation[1], pxBodyTranslation[2] };
    t.r = { pxBodyRotation[0], pxBodyRotation[1], pxBodyRotation[2], pxBodyRotation[3] };

    omni::isaac::dynamic_control::DcObjectType primType =
        mDynamicControlPtr->peekObjectType(prim.GetPath().GetString().c_str());
    if (primType == omni::isaac::dynamic_control::eDcObjectArticulation)
    {
        omni::isaac::dynamic_control::DcHandle artculationHandle =
            mDynamicControlPtr->getArticulation(prim.GetPath().GetString().c_str());
        omni::isaac::dynamic_control::DcHandle rigidBodyHandle =
            mDynamicControlPtr->getArticulationRootBody(artculationHandle);
        mDynamicControlPtr->setRigidBodyPose(rigidBodyHandle, t);
    }
    else if (primType == omni::isaac::dynamic_control::eDcObjectRigidBody)
    {
        omni::isaac::dynamic_control::DcHandle rigidBodyHandle =
            mDynamicControlPtr->getRigidBody(prim.GetPath().GetString().c_str());
        mDynamicControlPtr->setRigidBodyPose(rigidBodyHandle, t);
    }
    else
    {
        pxr::GfTransform usdBodyPose;
        usdBodyPose.SetTranslation(pxBodyTranslation);
        usdBodyPose.SetRotation(
            pxr::GfRotation(pxr::GfQuatf(pxBodyRotation[3], pxBodyRotation[0], pxBodyRotation[1], pxBodyRotation[2])));
        omni::usd::UsdUtils::setLocalTransformMatrix(prim, usdBodyPose.GetMatrix());
    }
}
/**
 * @brief Sets the scale of the object
 *
 * @param prim
 * @param pxBodyScale
 */
static void setScale(pxr::UsdPrim& prim, pxr::GfVec3d pxBodyScale)
{
    auto currentTransformMat = omni::usd::UsdUtils::getLocalTransformMatrix(prim);
    pxr::GfMatrix4d scaleMat;
    scaleMat.SetScale(pxBodyScale);
    auto scaledTransformMat = scaleMat * currentTransformMat;
    omni::usd::UsdUtils::setLocalTransformMatrix(prim, scaledTransformMat);
}
}
}
}
