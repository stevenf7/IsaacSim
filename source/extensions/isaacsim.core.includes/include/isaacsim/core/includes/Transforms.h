// SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#pragma once

// #include <carb/filesystem/IFileSystem.h>

#include <DynamicControl.h>
// clang-format off
#include <omni/usd/UtilsIncludes.h>
#include <omni/usd/UsdUtils.h>
// clang-format on

#include <isaacsim/core/includes/Conversions.h>

namespace isaacsim
{
namespace core
{
namespace includes
{

/**
 * @namespace transforms
 * @brief Utilities for manipulating transforms of USD prims and physics objects.
 * @details
 * Provides functions for modifying transforms of objects in the scene, handling both:
 * - Physics-based objects (articulations and rigid bodies)
 * - Regular USD prims
 *
 * Features:
 * - Transform setting with physics state preservation
 * - Scale manipulation with physics constraints
 * - Automatic physics state management (wake/sleep)
 * - Proper handling of local vs. world space transforms
 */
namespace transforms
{

using omni::isaac::dynamic_control::DcHandle;
using omni::isaac::dynamic_control::DcObjectType;
using omni::isaac::dynamic_control::DcTransform;

/**
 * @brief Sets the transform (position and rotation) of a USD prim.
 * @details
 * Handles different types of objects appropriately:
 * 1. For articulated objects:
 *    - Wakes up the articulation
 *    - Sets root body pose
 *    - Resets velocities
 * 2. For rigid bodies:
 *    - Wakes up the body
 *    - Sets pose directly
 *    - Resets velocities
 * 3. For regular prims:
 *    - Computes and sets local transform
 *    - Handles parent space correctly
 *
 * @param[in,out] prim USD prim to transform
 * @param[in] pxBodyTranslation New position in world space
 * @param[in] pxBodyRotation New rotation in world space
 *
 * @note For physics objects, this function only works during simulation
 * @warning Resets linear and angular velocities to zero for physics objects
 */
inline void setTransform(pxr::UsdPrim& prim, pxr::GfVec3f pxBodyTranslation, pxr::GfQuatf pxBodyRotation)
{
    // TODO: Handle world rotation as well
    // NOTE: reverting this for now, rigid body sink publishes global so teleport should be global too
    // auto newTranslation = pxBodyTranslation; // + parentToWorldMat.ExtractTranslation();
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr =
        carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();
    omni::isaac::dynamic_control::DcTransform t =
        isaacsim::core::includes::conversions::asDcTransform(pxBodyTranslation, pxBodyRotation);

    if (mDynamicControlPtr->isSimulating())
    {
        DcObjectType primType = mDynamicControlPtr->peekObjectType(prim.GetPath().GetString().c_str());
        if (primType == omni::isaac::dynamic_control::eDcObjectArticulation)
        {
            DcHandle artculationHandle = mDynamicControlPtr->getArticulation(prim.GetPath().GetString().c_str());
            mDynamicControlPtr->wakeUpArticulation(artculationHandle);
            DcHandle rigidBodyHandle = mDynamicControlPtr->getArticulationRootBody(artculationHandle);
            mDynamicControlPtr->setRigidBodyPose(rigidBodyHandle, t);
            mDynamicControlPtr->setRigidBodyLinearVelocity(rigidBodyHandle, { 0, 0, 0 });
            mDynamicControlPtr->setRigidBodyAngularVelocity(rigidBodyHandle, { 0, 0, 0 });
            mDynamicControlPtr->setRigidBodyPose(rigidBodyHandle, t);
            mDynamicControlPtr->setRigidBodyLinearVelocity(rigidBodyHandle, { 0, 0, 0 });
            mDynamicControlPtr->setRigidBodyAngularVelocity(rigidBodyHandle, { 0, 0, 0 });
            return;
        }
        else if (primType == omni::isaac::dynamic_control::eDcObjectRigidBody)
        {
            DcHandle rigidBodyHandle = mDynamicControlPtr->getRigidBody(prim.GetPath().GetString().c_str());
            mDynamicControlPtr->wakeUpRigidBody(rigidBodyHandle);
            mDynamicControlPtr->setRigidBodyPose(rigidBodyHandle, t);
            mDynamicControlPtr->setRigidBodyLinearVelocity(rigidBodyHandle, { 0, 0, 0 });
            mDynamicControlPtr->setRigidBodyAngularVelocity(rigidBodyHandle, { 0, 0, 0 });
            return;
        }
    }
    // In case we are not simulating or the object was a regular prim, go down this path
    {
        pxr::GfTransform usdBodyPose;
        usdBodyPose.SetTranslation(pxBodyTranslation);
        usdBodyPose.SetRotation(pxr::GfRotation(pxBodyRotation));
        // Pose is global so offset by parent pose
        pxr::GfMatrix4d parentToWorldMat =
            pxr::UsdGeomXformable(prim).ComputeParentToWorldTransform(pxr::UsdTimeCode::Default());
        omni::usd::UsdUtils::setLocalTransformMatrix(prim, usdBodyPose.GetMatrix() * parentToWorldMat.GetInverse());
    }
}

/**
 * @brief Sets the scale of a USD prim.
 * @details
 * Applies scaling to the prim's local transform, with special handling for physics objects:
 * - Only scales non-physics objects during simulation
 * - Preserves existing transform components
 * - Applies scale in local space
 *
 * @param[in,out] prim USD prim to scale
 * @param[in] pxBodyScale Scale factors for x, y, and z axes
 *
 * @note During simulation, only non-physics objects can be scaled
 * @warning Scaling physics objects during simulation may have unexpected results
 */
inline void setScale(pxr::UsdPrim& prim, pxr::GfVec3f pxBodyScale)
{
    omni::isaac::dynamic_control::DynamicControl* mDynamicControlPtr =
        carb::getCachedInterface<omni::isaac::dynamic_control::DynamicControl>();
    bool doScale = true;

    if (mDynamicControlPtr->isSimulating())
    {
        DcObjectType primType = mDynamicControlPtr->peekObjectType(prim.GetPath().GetString().c_str());
        doScale = (primType == omni::isaac::dynamic_control::eDcObjectNone);
    }
    if (doScale)
    {
        auto currentTransformMat = omni::usd::UsdUtils::getLocalTransformMatrix(prim);
        pxr::GfMatrix4d scaleMat;
        scaleMat.SetScale(pxBodyScale);
        auto scaledTransformMat = scaleMat * currentTransformMat;
        omni::usd::UsdUtils::setLocalTransformMatrix(prim, scaledTransformMat);
    }
}

} // namespace transforms
} // namespace includes
} // namespace core
} // namespace isaacsim
