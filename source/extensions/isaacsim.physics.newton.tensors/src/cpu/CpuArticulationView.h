// SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#pragma once

#include "base/BaseArticulationView.h"

namespace isaacsim
{
namespace physics
{
namespace newton
{
namespace tensors
{

/// CPU articulation view. Implements getters/setters using host-side gather/scatter loops.
/// Reusable scratch vectors (m_scratchSourceOffset, m_scratchDestinationIndex) avoid per-call heap allocation.
class CpuArticulationView : public BaseArticulationView
{
public:
    CpuArticulationView(py::object newtonStage, const std::vector<pxr::SdfPath>& articulationPaths);
    ~CpuArticulationView() override = default;

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
    mutable std::vector<int> m_scratchSourceOffset;
    mutable std::vector<int> m_scratchDestinationIndex;
};

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
