// SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "base/BaseArticulationView.h"

#include <cuda_runtime.h>

namespace isaacsim
{
namespace physics
{
namespace newton
{
namespace tensors
{

/// GPU articulation view. Implements getters via CUDA gather kernels with D2H staging,
/// and setters via fused CUDA scatter kernels. Supports GC (GPU sim, CPU view tensors)
/// by staging CPU index/source data into pre-allocated device buffers.
class GpuArticulationView : public BaseArticulationView
{
public:
    GpuArticulationView(py::object newtonStage, const std::vector<pxr::SdfPath>& articulationPaths, int deviceOrdinal);
    ~GpuArticulationView() override;

    bool getDofPositions(const TensorDesc* dstTensor) const override;
    bool getDofVelocities(const TensorDesc* dstTensor) const override;
    bool setDofPositions(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setDofVelocities(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;

    bool getDofLimits(const TensorDesc* dstTensor) const override;
    bool getDofStiffnesses(const TensorDesc* dstTensor) const override;
    bool getDofDampings(const TensorDesc* dstTensor) const override;
    bool getDofArmatures(const TensorDesc* dstTensor) const override;
    bool getDofMaxForces(const TensorDesc* dstTensor) const override;
    bool getDofMaxVelocities(const TensorDesc* dstTensor) const override;
    bool getDofPositionTargets(const TensorDesc* dstTensor) const override;
    bool getDofVelocityTargets(const TensorDesc* dstTensor) const override;
    bool getDofActuationForces(const TensorDesc* dstTensor) const override;
    bool getDofTypes(const TensorDesc* dstTensor) const override;

    bool setDofLimits(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setDofStiffnesses(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setDofDampings(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setDofMaxForces(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setDofMaxVelocities(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setDofArmatures(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setDofActuationForces(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setDofPositionTargets(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setDofVelocityTargets(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;

    bool getRootTransforms(const TensorDesc* dstTensor) const override;
    bool getRootVelocities(const TensorDesc* dstTensor) const override;
    bool setRootTransforms(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setRootVelocities(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;

    bool getLinkTransforms(const TensorDesc* dstTensor) const override;
    bool getLinkVelocities(const TensorDesc* dstTensor) const override;

    bool getMasses(const TensorDesc* dstTensor) const override;
    bool getInvMasses(const TensorDesc* dstTensor) const override;
    bool setMasses(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool getCOMs(const TensorDesc* dstTensor) const override;
    bool setCOMs(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool getInertias(const TensorDesc* dstTensor) const override;
    bool getInvInertias(const TensorDesc* dstTensor) const override;
    bool setInertias(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;

    bool applyForcesAndTorquesAtPosition(const TensorDesc* srcForceTensor,
                                         const TensorDesc* srcTorqueTensor,
                                         const TensorDesc* srcPositionTensor,
                                         const TensorDesc* indexTensor,
                                         bool isGlobal) override;

private:
    int m_deviceOrdinal;

    // Device-side copies of index mappings (uploaded once at construction).
    int* m_deviceDofPositionIndices = nullptr;
    int* m_deviceDofVelocityIndices = nullptr;
    int* m_deviceDofAxisIndices = nullptr;
    int* m_deviceLinkFlatIndices = nullptr;
    int* m_deviceRootIndices = nullptr;
    int* m_deviceRootJointQStartIndices = nullptr;
    int* m_deviceFixedRootJointMapping = nullptr; ///< [count] artiIdx → rootJointIdx for fixed roots, -1 for free.
    int* m_deviceIndexScratch = nullptr; ///< Scratch buffer for H2D staging of CPU index tensors.
    float* m_stagingBuffer = nullptr; ///< Reusable device buffer for D2H getter output and H2D setter input.
    size_t m_stagingMaxFloats = 0; ///< Capacity of m_stagingBuffer in float elements.

    uint8_t* m_deviceDofTypes = nullptr;
    float* m_deviceComOrientation = nullptr; ///< Device-side COM orientation cache [count * maxLinks * 4].

    /// Allocates and uploads all host-side index arrays to device memory.
    void _uploadMappingsToGpu();
    /// Allocates m_stagingBuffer and m_deviceIndexScratch sized to the maximum needed.
    void _allocateStagingBuffer();
};

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
