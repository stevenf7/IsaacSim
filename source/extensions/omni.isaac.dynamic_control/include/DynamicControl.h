// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include "DynamicControlTypes.h"

namespace omni
{
namespace isaac
{
namespace dynamic_control
{

struct DynamicControl
{
    CARB_PLUGIN_INTERFACE("omni::isaac::dynamic_control::DynamicControl", 0, 1);


    // DcContext*(CARB_ABI* createContext)(const char* scenePath);
    // void(CARB_ABI* destroyContext)(DcContext* ctx);

    // call at end of frame
    // void(CARB_ABI* updateContext)(DcContext* ctx);

    // Return true if simulating
    bool(CARB_ABI* isSimulating)();

    //===== Actors =====//

    DcHandle(CARB_ABI* getRigidBody)(const char* usdPath);
    DcHandle(CARB_ABI* getJoint)(const char* usdPath);
    DcHandle(CARB_ABI* getDof)(const char* usdPath);
    DcHandle(CARB_ABI* getArticulation)(const char* usdPath);
    DcHandle(CARB_ABI* getD6Joint)(const char* usdPath);

    // generic objects and types
    DcHandle(CARB_ABI* getObject)(const char* usdPath);
    DcObjectType(CARB_ABI* peekObjectType)(const char* usdPath);
    DcObjectType(CARB_ABI* getObjectType)(DcHandle handle);
    const char*(CARB_ABI* getObjectTypeName)(DcHandle handle);

    // int(CARB_ABI* getArticulationCount)(const DcContext* ctx);
    // int(CARB_ABI* getArticulations)(DcContext* ctx, DcArticulation** userBuffer, int bufferSize);

    bool(CARB_ABI* wakeUpRigidBody)(DcHandle bodyHandle);
    bool(CARB_ABI* wakeUpArticulation)(DcHandle artHandle);

    bool(CARB_ABI* sleepRigidBody)(DcHandle bodyHandle);
    bool(CARB_ABI* sleepArticulation)(DcHandle artHandle);

    //===== Articulations =====//

    const char*(CARB_ABI* getArticulationName)(DcHandle artHandle);
    const char*(CARB_ABI* getArticulationPath)(DcHandle artHandle);

    //! Gets number of rigid bodies for an actor
    /*!
     *  \param[in] actor the actor.
     *  \return number of rigid bodies in actor
     */
    size_t(CARB_ABI* getArticulationBodyCount)(DcHandle artHandle);

    //! Gets actor rigid body given its index
    /*!
     *  \param[in] actor the actor.
     *  \param[in] bodyIdx index of the rigid body.
     *  \return handle for rigid body
     */
    DcHandle(CARB_ABI* getArticulationBody)(DcHandle artHandle, size_t bodyIdx);

    //! Finds actor rigid body given its name
    /*!
     *  \param[in] actor the actor.
     *  \param[in] bodyName name of the rigid body.
     *  \return handle for rigid body
     */
    DcHandle(CARB_ABI* findArticulationBody)(DcHandle artHandle, const char* bodyName);

    // find index in articulation body array, -1 on error
    int(CARB_ABI* findArticulationBodyIndex)(DcHandle artHandle, const char* bodyName);

    //! Get the root rigid body of an actor
    /*!
     *  \param actor the actor
     *  \return root body handle
     */
    DcHandle(CARB_ABI* getArticulationRootBody)(DcHandle artHandle);

    //! Get array of an actor's rigid body states
    /*!
     *  \param actor the actor.
     *  \param flags flags for the state to obtain (kDcStatePos, kDcStateVel, or kDcStateAll)
     */
    DcRigidBodyState*(CARB_ABI* getArticulationBodyStates)(DcHandle artHandle, const DcStateFlags& flags);

    // //! Sets states for an actor's rigid bodies.
    // /*!
    //  *  \param actor the actor.
    //  *  \param states the states to set.
    //  *  \param flags flags for the state to obtain (kDcStatePos, kDcStateVel, or kDcStateAll)
    //  */
    // bool(CARB_ABI* setArticulationBodyStates)(DcHandle artHandle, const DcRigidBodyState* states, DcStateFlags
    // flags);

    //! Get properties for articulation
    /*!
     *  \param artHandle the handle to the articulation.
     *  \param properties articulation properties.
     */
    bool(CARB_ABI* getArticulationProperties)(DcHandle artHandle, DcArticulationProperties* properties);
    //! Set properties for articulation
    /*!
     *  \param artHandle the handle to the articulation.
     *  \param properties articulation properties.
     */
    bool(CARB_ABI* setArticulationProperties)(DcHandle artHandle, const DcArticulationProperties& properties);

    //===== Articulation joints =====//

    size_t(CARB_ABI* getArticulationJointCount)(DcHandle artHandle);
    DcHandle(CARB_ABI* getArticulationJoint)(DcHandle artHandle, size_t jointIdx);
    DcHandle(CARB_ABI* findArticulationJoint)(DcHandle artHandle, const char* jointName);

    //===== Articulation DOFs (degrees of freedom) =====//

    //! Gets number of degrees-of-freedom for an actor
    /*!
     *  \param[in] actor the actor.
     *  \return number of degrees-of-freedom in actor
     */
    size_t(CARB_ABI* getArticulationDofCount)(DcHandle artHandle);

    //! Gets actor degree-of-freedom given its index
    /*!
     *  \param[in] actor the actor.
     *  \param[in] dofIdx index of the degree-of-freedom.
     *  \return handle for degree-of-freedom
     */
    DcHandle(CARB_ABI* getArticulationDof)(DcHandle artHandle, size_t dofIdx);

    //! Finds actor degree-of-freedom given its name
    /*!
     *  \param[in] actor the actor.
     *  \param[in] dofName name of the degree-of-freedom.
     *  \return handle for degree-of-freedom
     */
    DcHandle(CARB_ABI* findArticulationDof)(DcHandle artHandle, const char* dofName);

    // get index in articulation DOF array, -1 on error
    int(CARB_ABI* findArticulationDofIndex)(DcHandle artHandle, const char* dofName);

    //! Get array of an actor's degree-of-freedom properties
    /*!
     *  \param actor the actor.
     *  \param props destination property array
     */
    bool(CARB_ABI* getArticulationDofProperties)(DcHandle artHandle, DcDofProperties* props);

    //! Sets properties for an actor's degrees-of-freedom.
    /*!
     *  \param actor the actor.
     *  \param props the properties to set.
     */
    bool(CARB_ABI* setArticulationDofProperties)(DcHandle artHandle, const DcDofProperties* props);

    //! Get array of an actor's degree-of-freedom states
    /*!
     *  \param actor the actor.
     *  \param flags flags for the state to obtain (kDcStatePos, kDcStateVel, or kDcStateAll)
     */
    DcDofState*(CARB_ABI* getArticulationDofStates)(DcHandle artHandle, const DcStateFlags& flags);

    //! Get array of an actor's degree-of-freedom state derivatives (dstate / dt)
    /*!
     *  \param artHandle the articulation handle
     *  \param states (of DoFs) at which derivatives are evaluated at. Indexed using find_articulation_dof_index.
     *  \param efforts (of DoFs) at which derivatives are evaluated at. Indexed using find_articulation_dof_index.
     *
     *  \note Sets the articulation DoFs and efforts to the values provided
     */
    DcDofState*(CARB_ABI* getArticulationDofStateDerivatives)(DcHandle artHandle,
                                                              const DcDofState* states,
                                                              const float* efforts);

    //! Sets states for an actor's degrees-of-freedom.
    /*!
     *  \param actor the actor.
     *  \param states the states to set.
     *  \param flags flags for the state to obtain (kDcStatePos, kDcStateVel, or kDcStateAll)
     */
    bool(CARB_ABI* setArticulationDofStates)(DcHandle artHandle, const DcDofState* states, const DcStateFlags& flags);

    //! Sets an actor's degree-of-freedom position targets.
    /*!
     *  \param actor the actor.
     *  \param states the targets to set.
     */
    bool(CARB_ABI* setArticulationDofPositionTargets)(DcHandle artHandle, const float* targets);

    //! Gets an actor's degree-of-freedom position targets.
    /*!
     *  \param actor the actor.
     *  \param states the targets to get.
     */
    bool(CARB_ABI* getArticulationDofPositionTargets)(DcHandle artHandle, float* targets);


    //! Sets an actor's degree-of-freedom velocity targets.
    /*!
     *  \param actor the actor.
     *  \param states the targets to set.
     */
    bool(CARB_ABI* setArticulationDofVelocityTargets)(DcHandle artHandle, const float* targets);

    //! Gets an actor's degree-of-freedom velocity targets.
    /*!
     *  \param actor the actor.
     *  \param states the targets to get.
     */
    bool(CARB_ABI* getArticulationDofVelocityTargets)(DcHandle artHandle, float* targets);


    //! Applies efforts to an actor's degrees-of-freedom.
    /*!
     *  \param artHandle the actor.
     *  \param efforts the efforts to set.
     */
    bool(CARB_ABI* setArticulationDofEfforts)(DcHandle artHandle, const float* efforts);

    //! Get efforts applied to an actor's degrees-of-freedom.
    /*!
     *  \param artHandle the actor.
     *  \param efforts the current efforts.
     */
    bool(CARB_ABI* getArticulationDofEfforts)(DcHandle artHandle, float* efforts);


    //! Get effective masses for articulation dofs
    /*!
     *  \param artHandle the handle to the articulation.
     *  \param masses articulation masses.
     */
    bool(CARB_ABI* getArticulationDofMasses)(DcHandle artHandle, float* masses);


    // rigid bodies

    const char*(CARB_ABI* getRigidBodyName)(DcHandle bodyHandle);
    const char*(CARB_ABI* getRigidBodyPath)(DcHandle bodyHandle);

    DcHandle(CARB_ABI* getRigidBodyParentJoint)(DcHandle bodyHandle);
    size_t(CARB_ABI* getRigidBodyChildJointCount)(DcHandle bodyHandle);
    DcHandle(CARB_ABI* getRigidBodyChildJoint)(DcHandle bodyHandle, size_t jointIdx);

    DcTransform(CARB_ABI* getRigidBodyPose)(DcHandle bodyHandle);
    carb::Float3(CARB_ABI* getRigidBodyLinearVelocity)(DcHandle bodyHandle);
    carb::Float3(CARB_ABI* getRigidBodyLocalLinearVelocity)(DcHandle bodyHandle);
    carb::Float3(CARB_ABI* getRigidBodyAngularVelocity)(DcHandle bodyHandle);

    /**
     * @brief enables or disables the force of gravity from the given body
     *  \param bodyHandle.
     *  \param disableGravity.
     */
    bool(CARB_ABI* setRigidBodyDisableGravity)(DcHandle bodyHandle, const bool disableGravity);

    /**
     * @brief enables or disables Simulation of a given rigid body
     *  \param bodyHandle.
     *  \param disableSimulation.
     */
    bool(CARB_ABI* setRigidBodyDisableSimulation)(DcHandle bodyHandle, const bool disableSimulation);

    bool(CARB_ABI* setRigidBodyPose)(DcHandle bodyHandle, const DcTransform& pose);
    bool(CARB_ABI* setRigidBodyLinearVelocity)(DcHandle bodyHandle, const carb::Float3& linvel);
    bool(CARB_ABI* setRigidBodyAngularVelocity)(DcHandle bodyHandle, const carb::Float3& angvel);

    bool(CARB_ABI* applyBodyForce)(DcHandle bodyHandle,
                                   const carb::Float3& force,
                                   const carb::Float3& pos,
                                   const bool globalCoordinates);

    bool(CARB_ABI* applyBodyTorque)(DcHandle bodyHandle, const carb::Float3& torque, const bool globalCoordinates);


    bool(CARB_ABI* getRelativeBodyPoses)(DcHandle parentHandle,
                                         size_t numBodies,
                                         const DcHandle* bodyHandles,
                                         DcTransform* bodyTransforms);

    bool(CARB_ABI* getRigidBodyProperties)(DcHandle bodyHandle, DcRigidBodyProperties* props);

    //! Set properties for rigid body
    /*!
     *  \param bodyHandle the handle to the rigid body.
     *  \param properties properties for rigid body.
     */
    bool(CARB_ABI* setRigidBodyProperties)(DcHandle bodyHandle, const DcRigidBodyProperties& properties);
    // joints

    const char*(CARB_ABI* getJointName)(DcHandle jointHandle);
    const char*(CARB_ABI* getJointPath)(DcHandle jointHandle);

    DcJointType(CARB_ABI* getJointType)(DcHandle jointHandle);

    size_t(CARB_ABI* getJointDofCount)(DcHandle jointHandle);
    DcHandle(CARB_ABI* getJointDof)(DcHandle jointHandle, size_t dofIdx);

    DcHandle(CARB_ABI* getJointParentBody)(DcHandle jointHandle);
    DcHandle(CARB_ABI* getJointChildBody)(DcHandle jointHandle);

    // dofs

    const char*(CARB_ABI* getDofName)(DcHandle dofHandle);
    const char*(CARB_ABI* getDofPath)(DcHandle dofHandle);

    DcDofType(CARB_ABI* getDofType)(DcHandle dofHandle);

    DcHandle(CARB_ABI* getDofJoint)(DcHandle dofHandle);

    DcHandle(CARB_ABI* getDofParentBody)(DcHandle dofHandle);
    DcHandle(CARB_ABI* getDofChildBody)(DcHandle dofHandle);

    DcDofState(CARB_ABI* getDofState)(DcHandle dofHandle, const DcStateFlags& flags);
    bool(CARB_ABI* setDofState)(DcHandle dofHandle, const DcDofState* state, const DcStateFlags& flags);

    float(CARB_ABI* getDofPosition)(DcHandle dofHandle);
    bool(CARB_ABI* setDofPosition)(DcHandle dofHandle, float pos);

    float(CARB_ABI* getDofVelocity)(DcHandle dofHandle);
    bool(CARB_ABI* setDofVelocity)(DcHandle dofHandle, float vel);

    bool(CARB_ABI* getDofProperties)(DcHandle dofHandle, DcDofProperties* props);
    bool(CARB_ABI* setDofProperties)(DcHandle dofHandle, const DcDofProperties* props);

    bool(CARB_ABI* setDofPositionTarget)(DcHandle dofHandle, float target);
    bool(CARB_ABI* setDofVelocityTarget)(DcHandle dofHandle, float target);
    float(CARB_ABI* getDofPositionTarget)(DcHandle dofHandle);
    float(CARB_ABI* getDofVelocityTarget)(DcHandle dofHandle);
    bool(CARB_ABI* setDofEffort)(DcHandle dofHandle, float effort);
    float(CARB_ABI* getDofEffort)(DcHandle dofHandle);

    // attractors

    //! Creates Rigid Body Attractor
    /*!
     * Creates an attractor for the selected environment
     * using the properties defined.
     * \param props the properties in the attractor, see DcAttractorProperties.
     * \return the handle for the created attractor
     */

    // DcAttractor*(CARB_ABI* createRigidBodyAttractor)(DcContext* ctx, const DcAttractorProperties* props);

    DcHandle(CARB_ABI* createRigidBodyAttractor)(const DcAttractorProperties* props);

    bool(CARB_ABI* destroyRigidBodyAttractor)(DcHandle attHandle);

    //! Get properties of the selected attractor.
    /*!
     *  \param attractor The attractor.
     *  \param[out] props Properties of the specified attractor.
     *  \return true if succesful in obtaining properties, false if attractor handle is invalid.
     */
    bool(CARB_ABI* getAttractorProperties)(DcHandle attHandle, DcAttractorProperties* props);

    //! Modifies properties of the selected attractor.
    /*!
     *  Modifies the properties of an attractor given by its handle and the environment selected.
     *  for modifying only the attractor target, see setAttractorTarget.
     *  \param attractor The attractor to be modified.
     *  \param props the new properties for the attractor.
     */
    bool(CARB_ABI* setAttractorProperties)(DcHandle attHandle, const DcAttractorProperties* props);

    //! Modifies target of the selected attractor.
    /*!
     *  \param attractor The attractor to be modified.
     *  \param target, attractor target pose, in global coordinate.
     */
    bool(CARB_ABI* setAttractorTarget)(DcHandle attHandle, const DcTransform& target);

    // General D6 Joint

    //! Creates D6 Joint between two rigid bodies
    /*!
     * Creates a Joint for the selected environment
     * using the properties defined.
     * \param props the properties in the joint, see DcD6JointProperties.
     * \return the handle for the created joint
     */

    DcHandle(CARB_ABI* createD6Joint)(const DcD6JointProperties* props);

    bool(CARB_ABI* destroyD6Joint)(DcHandle jointHandle);

    //! Get properties of the selected joint.
    /*!
     *  \param joint The joint.
     *  \param[out] props Properties of the specified attractor.
     *  \return true if succesful in obtaining properties, false if attractor handle is invalid.
     */
    bool(CARB_ABI* getD6JointProperties)(DcHandle jointHandle, DcD6JointProperties* props);

    //! Get whether the joint constraint is broken
    /*!
     *  \param joint The joint.
     *  \return true if joint constraint is broken
     */
    bool(CARB_ABI* getD6JointConstraintIsBroken)(DcHandle jointHandle);

    //! Modifies properties of the selected joint.
    /*!
     *  Modifies the properties of an joint given by its handle and the environment selected.
     *  \param joint The joint to be modified.
     *  \param props the new properties for the joint.
     */
    bool(CARB_ABI* setD6JointProperties)(DcHandle jointHandle, const DcD6JointProperties* props);

    bool(CARB_ABI* setOriginOffset)(DcHandle handle, const carb::Float3& origin);

    //! Checks for a collision  ranging from the origin to the given direction.
    /*!
     * \param origin point of origin to the ray cast
     * \param direction unit vector with the direction the ray will be cast
     * \param max_distance how far the ray cast will travel before returning a hit
     */
    DcRayCastResult(CARB_ABI* rayCast)(const carb::Float3& origin, const carb::Float3& direction, float max_distrance);

#if 0
    DcShape(CARB_ABI* createShape)(int ndims, ...);

    DcTensor* createTensor(const DcShape& shape, DcDtype dtype);
#endif
};

}
}
}
