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

#include "base/BaseRigidContactView.h"

namespace isaacsim
{
namespace physics
{
namespace newton
{
namespace tensors
{

/// CPU contact view. Iterates the contact buffer on the host to compute net forces,
/// force matrices, and per-contact data. Uses host-side zero buffers as fallbacks when
/// optional contact arrays (point0/1, thickness0/1) are not present.
class CpuRigidContactView : public BaseRigidContactView
{
public:
    CpuRigidContactView(py::object newtonStage,
                        const std::vector<std::string>& sensorPaths,
                        const std::vector<std::vector<std::string>>& filterPaths,
                        uint32_t maxContactDataCount);
    ~CpuRigidContactView() override = default;

    bool getNetContactForces(const TensorDesc* dstTensor, float dt) const override;
    bool getContactForceMatrix(const TensorDesc* dstTensor, float dt) const override;
    bool getContactData(const TensorDesc* contactForceTensor,
                        const TensorDesc* contactPointTensor,
                        const TensorDesc* contactNormalTensor,
                        const TensorDesc* contactSeparationTensor,
                        const TensorDesc* contactCountTensor,
                        const TensorDesc* contactStartIndicesTensor,
                        float dt) const override;
    bool getRawContactData(const TensorDesc* contactForceTensor,
                           const TensorDesc* contactPointTensor,
                           const TensorDesc* contactNormalTensor,
                           const TensorDesc* contactSeparationTensor,
                           const TensorDesc* contactCountTensor,
                           const TensorDesc* contactStartIndicesTensor,
                           const TensorDesc* otherActorIdsTensor,
                           float dt) const override;

private:
    const float* _resolveContactForce() const;
    const float* _getContactPoint0() const;
    const float* _getContactPoint1() const;
    const float* _getThickness0() const;
    const float* _getThickness1() const;

    std::vector<float> m_hostZeroVec3Buffer;
    std::vector<float> m_hostZeroFloatBuffer;
};

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
