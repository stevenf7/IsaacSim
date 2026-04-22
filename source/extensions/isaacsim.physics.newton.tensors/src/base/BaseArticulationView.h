// SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "ArticulationMetatype.h"
#include "utils/ViewUtils.h"

#include <omni/physics/tensors/IArticulationView.h>
#include <pxr/usd/sdf/path.h>
#include <pybind11/pybind11.h>

#include <limits>
#include <string>
#include <vector>

namespace py = pybind11;

namespace isaacsim
{
namespace physics
{
namespace newton
{
namespace tensors
{

using omni::physics::tensors::IArticulationMetatype;
using omni::physics::tensors::IArticulationView;
using omni::physics::tensors::TensorDesc;

/// Base articulation view implementing IArticulationView for Newton.
///
/// Parses the Newton model at construction to build DOF, link, and root index mappings.
/// Caches raw Warp array pointers for joint_q, joint_qd, body_q, body_qd, and property
/// arrays (stiffness, damping, limits, etc.) to avoid repeated Python lookups.
/// Getter/setter methods are pure virtual and implemented by CpuArticulationView and
/// GpuArticulationView.
class BaseArticulationView : public IArticulationView
{
public:
    /// Parses model.joint_q_start, joint_qd_start, joint_type, body_label, and joint_label
    /// to build all index mappings and construct per-articulation ArticulationMetatype objects.
    BaseArticulationView(py::object newtonStage, const std::vector<pxr::SdfPath>& articulationPaths);
    ~BaseArticulationView() override;

    uint32_t getCount() const override;
    uint32_t getMaxLinks() const override;
    uint32_t getMaxDofs() const override;
    uint32_t getMaxShapes() const override;
    uint32_t getMaxFixedTendons() const override;
    uint32_t getMaxSpatialTendons() const override;

    bool isHomogeneous() const override;
    const IArticulationMetatype* getSharedMetatype() const override;
    const IArticulationMetatype* getMetatype(uint32_t artiIdx) const override;

    const char* getUsdPrimPath(uint32_t artiIdx) const override;
    const char* getUsdDofPath(uint32_t artiIdx, uint32_t dofIdx) const override;
    const char* getUsdLinkPath(uint32_t artiIdx, uint32_t linkIdx) const override;

    // Stubs
    bool getLinkAccelerations(const TensorDesc* dstTensor) const override;
    bool getDofProjectedJointForces(const TensorDesc* dstTensor) const override;
    bool getDofMotions(const TensorDesc* dstTensor) const override;
    bool getDriveTypes(const TensorDesc* dstTensor) const override;
    bool getDofDriveModelProperties(const TensorDesc* dstTensor) const override;
    bool getDofFrictionCoefficients(const TensorDesc* dstTensor) const override;
    bool getDofFrictionProperties(const TensorDesc* dstTensor) const override;
    bool getDisableGravities(const TensorDesc* dstTensor) const override;
    bool setDisableGravities(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setDisableGravitiesMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool getArticulationMassCenter(const TensorDesc* dstTensor, bool localFrame) const override;
    bool getArticulationCentroidalMomentum(const TensorDesc* dstTensor) const override;
    bool getJacobianShape(uint32_t* numRows, uint32_t* numCols) const override;
    bool getJacobians(const TensorDesc* dstTensor) const override;
    bool getGeneralizedMassMatrixShape(uint32_t* numRows, uint32_t* numCols) const override;
    bool getGeneralizedMassMatrices(const TensorDesc* dstTensor) const override;
    bool getCoriolisAndCentrifugalCompensationForces(const TensorDesc* dstTensor) const override;
    bool getGravityCompensationForces(const TensorDesc* dstTensor) const override;
    bool getLinkIncomingJointForce(const TensorDesc* dstTensor) const override;
    bool setDofDriveModelProperties(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setDofFrictionCoefficients(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setDofFrictionProperties(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;

    // Masked variants
    bool setDofLimitsMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setDofStiffnessesMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setDofDampingsMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setDofMaxForcesMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setDofDriveModelPropertiesMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setDofFrictionCoefficientsMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setDofFrictionPropertiesMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setDofMaxVelocitiesMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setDofArmaturesMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setDofPositionsMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setDofVelocitiesMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setDofActuationForcesMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setDofPositionTargetsMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setDofVelocityTargetsMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setMassesMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setCOMsMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setInertiasMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setRootTransformsMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setRootVelocitiesMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool applyForcesAndTorquesAtPositionMasked(const TensorDesc* srcForceTensor,
                                               const TensorDesc* srcTorqueTensor,
                                               const TensorDesc* srcPositionTensor,
                                               const TensorDesc* maskTensor,
                                               bool isGlobal) override;

    // Material/shape stubs
    bool getMaterialProperties(const TensorDesc* dstTensor) const override;
    bool getCompliantMaterialProperties(const TensorDesc* dstTensor,
                                        const TensorDesc* dstCombineModeTensor) const override;
    bool getRestOffsets(const TensorDesc* dstTensor) const override;
    bool getContactOffsets(const TensorDesc* dstTensor) const override;
    bool setMaterialProperties(const TensorDesc* srcTensor, const TensorDesc* indexTensor) const override;
    bool setCompliantMaterialProperties(const TensorDesc* srcTensor,
                                        const TensorDesc* srcCombineTensor,
                                        const TensorDesc* indexTensor) const override;
    bool setRestOffsets(const TensorDesc* srcTensor, const TensorDesc* indexTensor) const override;
    bool setContactOffsets(const TensorDesc* srcTensor, const TensorDesc* indexTensor) const override;
    bool setMaterialPropertiesMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) const override;
    bool setCompliantMaterialPropertiesMasked(const TensorDesc* srcTensor,
                                              const TensorDesc* srcCombineTensor,
                                              const TensorDesc* maskTensor) const override;
    bool setRestOffsetsMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) const override;
    bool setContactOffsetsMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) const override;

    // Tendon stubs
    bool getFixedTendonStiffnesses(const TensorDesc* dstTensor) const override;
    bool getFixedTendonDampings(const TensorDesc* dstTensor) const override;
    bool getFixedTendonLimitStiffnesses(const TensorDesc* dstTensor) const override;
    bool getFixedTendonLimits(const TensorDesc* dstTensor) const override;
    bool getFixedTendonfixedSpringRestLengths(const TensorDesc* dstTensor) const override;
    bool getFixedTendonOffsets(const TensorDesc* dstTensor) const override;
    bool getSpatialTendonStiffnesses(const TensorDesc* dstTensor) const override;
    bool getSpatialTendonDampings(const TensorDesc* dstTensor) const override;
    bool getSpatialTendonLimitStiffnesses(const TensorDesc* dstTensor) const override;
    bool getSpatialTendonOffsets(const TensorDesc* dstTensor) const override;
    bool setFixedTendonProperties(const TensorDesc* stiffnesses,
                                  const TensorDesc* dampings,
                                  const TensorDesc* limitStiffnesses,
                                  const TensorDesc* limits,
                                  const TensorDesc* restLengths,
                                  const TensorDesc* offsets,
                                  const TensorDesc* indexTensor) const override;
    bool setSpatialTendonProperties(const TensorDesc* stiffnesses,
                                    const TensorDesc* dampings,
                                    const TensorDesc* limitStiffnesses,
                                    const TensorDesc* offsets,
                                    const TensorDesc* indexTensor) const override;
    bool setFixedTendonPropertiesMasked(const TensorDesc* stiffnesses,
                                        const TensorDesc* dampings,
                                        const TensorDesc* limitStiffnesses,
                                        const TensorDesc* limits,
                                        const TensorDesc* restLengths,
                                        const TensorDesc* offsets,
                                        const TensorDesc* maskTensor) const override;
    bool setSpatialTendonPropertiesMasked(const TensorDesc* stiffnesses,
                                          const TensorDesc* dampings,
                                          const TensorDesc* limitStiffnesses,
                                          const TensorDesc* offsets,
                                          const TensorDesc* maskTensor) const override;

    bool check() const override;
    void release() override;

protected:
    /// Notifies the Newton model that joint DOF properties have been modified externally.
    void _notifyJointDofPropertiesChanged();
    /// Syncs CTRL_DIRECT actuator gains from the cached stiffness/damping arrays.
    void _syncCtrlDirectActuatorGains();
    /// Syncs CTRL_DIRECT position targets from the cached target array.
    void _syncCtrlDirectPositionTargets();
    /// Runs Newton forward kinematics to propagate joint_q changes to body_q.
    void _evalForwardKinematics();
    /// Runs Newton inverse kinematics to propagate body_q/body_qd changes back to joint_q/joint_qd.
    void _evalInverseKinematics();
    /// Recomputes inverse mass array from the forward mass array.
    void _updateInverseMasses();
    /// Recomputes inverse inertia array from the forward inertia array.
    void _updateInverseInertias();

    /// Resolves an index tensor to a list of articulation indices, writing into the
    /// pre-allocated m_scratchViewIndices member to avoid per-call allocation.
    const std::vector<uint32_t>& _resolveIndices(const TensorDesc* indexTensor) const
    {
        resolveViewIndices(indexTensor, m_count, m_scratchViewIndices);
        return m_scratchViewIndices;
    }
    isaacsim::physics::newton::tensors::GpuIndexGuard _resolveGpuIndices(const TensorDesc* indexTensor,
                                                                         int* devScratch = nullptr) const
    {
        return resolveGpuViewIndices(indexTensor, m_count, devScratch);
    }
    void _buildDofScatterMappings(const std::vector<uint32_t>& artiIndices,
                                  const std::vector<int>& dofIndices,
                                  std::vector<int>& srcOffsets,
                                  std::vector<int>& dstIndices) const;
    void _buildLinkScatterMappings(const std::vector<uint32_t>& artiIndices,
                                   int elemSize,
                                   std::vector<int>& srcOffsets,
                                   std::vector<int>& dstIndices) const;
    void _buildRootScatterMappings(const std::vector<uint32_t>& artiIndices,
                                   int elemSize,
                                   std::vector<int>& srcOffsets,
                                   std::vector<int>& dstIndices) const;

    py::object m_newtonStage;
    py::object m_model;

    uint32_t m_count; ///< Number of articulations in the view.
    uint32_t m_maxLinks; ///< Maximum link count across all articulations.
    uint32_t m_maxDofs; ///< Maximum DOF count across all articulations.
    uint32_t m_maxShapes;

    std::vector<int> m_articulationIndices; ///< Root body index for each articulation.
    std::vector<int> m_dofPosIndices; ///< [count * maxDofs] → model.joint_q index, -1 = padding.
    std::vector<int> m_dofVelIndices; ///< [count * maxDofs] → model.joint_qd index, -1 = padding.
    std::vector<int> m_dofAxisIndices; ///< [count * maxDofs] → model.joint_axis index, -1 = padding.
    std::vector<int> m_rootBodyIndices; ///< [count] → model body index for each root body.
    std::vector<int> m_rootJointIndices; ///< [count] → model joint index for each root joint.
    std::vector<int> m_rootJointQStartIndices; ///< [count] → joint_q_start offset for root joint.
    std::vector<std::vector<int>> m_linkIndicesPerArticulation;
    std::vector<int> m_linkFlatIndices; ///< [count * maxLinks] → model body index, -1 = padding.

    std::vector<std::string> m_articulationPrimPaths;
    std::vector<std::vector<std::string>> m_articulationPaths;

    std::vector<ArticulationMetatype*> m_metatypes;
    std::vector<uint8_t> m_hostDofTypes;

    mutable std::vector<uint32_t> m_scratchViewIndices;

    bool m_cacheValid = false; ///< True after _cacheWarpPointers() succeeds.
    int m_modelDeviceOrdinal = -1; ///< Device of the Newton model's Warp arrays.
    size_t m_totalBodyCount = 0; ///< Total body count in the Newton model.

    // Cached raw pointers into Warp arrays from state_0 and the model.
    mutable float* m_cachedJointQ = nullptr;
    mutable float* m_cachedJointQd = nullptr;
    mutable float* m_cachedBodyQ = nullptr;
    mutable float* m_cachedBodyQd = nullptr;
    mutable float* m_cachedBodyF = nullptr;
    float* m_cachedJointTargetKe = nullptr;
    float* m_cachedJointTargetKd = nullptr;
    float* m_cachedJointEffortLimit = nullptr;
    float* m_cachedJointVelocityLimit = nullptr;
    float* m_cachedJointArmature = nullptr;
    float* m_cachedJointLimitLower = nullptr;
    float* m_cachedJointLimitUpper = nullptr;
    mutable float* m_cachedCtrlTargetPos = nullptr;
    mutable float* m_cachedCtrlTargetVel = nullptr;
    mutable float* m_cachedJointTorques = nullptr;
    float* m_cachedBodyMass = nullptr;
    float* m_cachedBodyInverseMass = nullptr;
    float* m_cachedBodyInertia = nullptr;
    float* m_cachedBodyInverseInertia = nullptr;
    float* m_cachedBodyCenterOfMass = nullptr;

    /// Extracts and caches raw float*/int* pointers from all relevant Warp arrays in the
    /// Newton model and state. Called lazily before the first getter/setter access.
    void _cacheWarpPointers();
};

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
