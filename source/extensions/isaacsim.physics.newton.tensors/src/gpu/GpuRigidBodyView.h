// SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "base/BaseRigidBodyView.h"

#include <cuda_runtime.h>

namespace isaacsim
{
namespace physics
{
namespace newton
{
namespace tensors
{

/// GPU rigid body view. Implements getters via CUDA gather kernels with D2H staging,
/// and setters via fused CUDA scatter kernels. Supports GC configuration.
class GpuRigidBodyView : public BaseRigidBodyView
{
public:
    GpuRigidBodyView(py::object newtonStage, const std::vector<pxr::SdfPath>& bodyPaths, int deviceOrdinal);
    ~GpuRigidBodyView() override;

    bool getTransforms(const TensorDesc* dstTensor) const override;
    bool getVelocities(const TensorDesc* dstTensor) const override;
    bool getMasses(const TensorDesc* dstTensor) const override;
    bool getInvMasses(const TensorDesc* dstTensor) const override;
    bool getCOMs(const TensorDesc* dstTensor) const override;
    bool getInertias(const TensorDesc* dstTensor) const override;
    bool getInvInertias(const TensorDesc* dstTensor) const override;

    bool setTransforms(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setVelocities(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setMasses(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setCOMs(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool setInertias(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;

    bool applyForces(const TensorDesc* srcTensor, const TensorDesc* indexTensor) override;
    bool applyForcesAndTorquesAtPosition(const TensorDesc* srcForceTensor,
                                         const TensorDesc* srcTorqueTensor,
                                         const TensorDesc* srcPositionTensor,
                                         const TensorDesc* indexTensor,
                                         bool isGlobal) override;

private:
    int m_deviceOrdinal;

    int* m_deviceBodyIndices = nullptr; ///< Device copy of body index mapping.
    int* m_deviceFreeJointQStartIndices = nullptr; ///< Device copy of free-joint q offsets.
    int* m_deviceIndexScratch = nullptr; ///< Scratch buffer for H2D staging of CPU index tensors.
    float* m_stagingBuffer = nullptr; ///< Reusable device buffer for D2H/H2D staging.
    size_t m_stagingMaxFloats = 0;

    void _uploadMappingsToGpu();
    void _allocateStagingBuffer();
};

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
