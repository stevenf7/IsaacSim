// SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "utils/ViewUtils.h"

#include <omni/physics/tensors/IRigidBodyView.h>
#include <pxr/usd/sdf/path.h>
#include <pybind11/pybind11.h>

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

using omni::physics::tensors::IRigidBodyView;
using omni::physics::tensors::TensorDesc;

/// Base rigid body view implementing IRigidBodyView for Newton.
///
/// Resolves USD body paths to Newton model body indices, identifies free-joint bodies for
/// root transform writes, and caches Warp array pointers for body_q, body_qd, mass,
/// inertia, and force arrays. Getter/setter methods are pure virtual and implemented by
/// CpuRigidBodyView and GpuRigidBodyView.
class BaseRigidBodyView : public IRigidBodyView
{
public:
    BaseRigidBodyView(py::object newtonStage, const std::vector<pxr::SdfPath>& bodyPaths);
    ~BaseRigidBodyView() override;

    uint32_t getCount() const override;
    uint32_t getMaxShapes() const override;
    const char* getUsdPrimPath(uint32_t rbIdx) const override;

    // Stubs — unsupported by Newton
    bool setKinematicTargets(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setKinematicTargetsMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool getDisableGravities(const TensorDesc* dstTensor) const override;
    bool getDisableSimulations(const TensorDesc* dstTensor) const override;
    bool setDisableGravities(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setDisableSimulations(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setDisableGravitiesMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setDisableSimulationsMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool wakeUp(const TensorDesc* indexTensor) override;

    // Masked variants — delegate to indexed
    bool setTransformsMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setVelocitiesMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool applyForcesMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool applyForcesAndTorquesAtPositionMasked(const TensorDesc* srcForceTensor,
                                               const TensorDesc* srcTorqueTensor,
                                               const TensorDesc* srcPositionTensor,
                                               const TensorDesc* maskTensor,
                                               bool isGlobal) override;
    bool setMassesMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setCOMsMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;
    bool setInertiasMasked(const TensorDesc* srcTensor, const TensorDesc* maskTensor) override;

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

    bool check() const override;
    void release() override;

protected:
    void _evalForwardKinematics();
    void _evalInverseKinematics();
    void _updateInverseMasses();
    void _updateInverseInertias();

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

    void _buildScatterMappings(const std::vector<uint32_t>& viewIndices,
                               int elemSize,
                               std::vector<int>& srcOffsets,
                               std::vector<int>& dstIndices) const;

    py::object m_newtonStage;
    py::object m_model;

    uint32_t m_count;
    uint32_t m_maxShapes;

    std::vector<int> m_bodyIndices; ///< [count] → model body index for each view body.
    std::vector<std::string> m_primPaths;
    std::vector<int> m_freeJointQStartIndices; ///< [count] → joint_q offset for free joints, -1 if fixed.

    mutable std::vector<uint32_t> m_scratchViewIndices;

    bool m_cacheValid = false;
    int m_modelDeviceOrdinal = -1;
    size_t m_totalBodyCount = 0;

    mutable float* m_cachedJointQ = nullptr;
    mutable float* m_cachedBodyQ = nullptr;
    mutable float* m_cachedBodyQd = nullptr;
    mutable float* m_cachedBodyQdd = nullptr; ///< Nullable; only available when body_qdd is requested.
    mutable float* m_cachedBodyF = nullptr;
    float* m_cachedBodyMass = nullptr;
    float* m_cachedBodyInverseMass = nullptr;
    float* m_cachedBodyInertia = nullptr;
    float* m_cachedBodyInverseInertia = nullptr;
    float* m_cachedBodyCenterOfMass = nullptr;

    std::vector<float> m_cachedComOrientation; ///< [count * 4] cached COM quaternion (xyzw), write-through from
                                               ///< setCOMs.

    void _cacheWarpPointers();
};

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
