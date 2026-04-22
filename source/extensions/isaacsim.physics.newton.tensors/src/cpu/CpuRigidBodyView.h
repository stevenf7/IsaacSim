// SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "base/BaseRigidBodyView.h"

namespace isaacsim
{
namespace physics
{
namespace newton
{
namespace tensors
{

/// CPU rigid body view. Implements getters/setters using host-side gather/scatter loops.
class CpuRigidBodyView : public BaseRigidBodyView
{
public:
    CpuRigidBodyView(py::object newtonStage, const std::vector<pxr::SdfPath>& bodyPaths);
    ~CpuRigidBodyView() override = default;

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
    mutable std::vector<int> m_scratchSourceOffset;
    mutable std::vector<int> m_scratchDestinationIndex;
};

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
