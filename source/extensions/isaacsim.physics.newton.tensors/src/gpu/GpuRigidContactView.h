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

#include <cuda_runtime.h>

namespace isaacsim
{
namespace physics
{
namespace newton
{
namespace tensors
{

/// GPU contact view. Uses CUDA kernels for net force, force matrix, and per-contact
/// data computation. Device-side zero buffers serve as fallbacks for optional contact arrays.
class GpuRigidContactView : public BaseRigidContactView
{
public:
    GpuRigidContactView(py::object newtonStage,
                        const std::vector<std::string>& sensorPaths,
                        const std::vector<std::vector<std::string>>& filterPaths,
                        uint32_t maxContactDataCount,
                        int deviceOrdinal);
    ~GpuRigidContactView() override;

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
    int m_deviceOrdinal;

    int* m_deviceBodySensorMap = nullptr; ///< Device copy of body-to-sensor mapping.
    int* m_deviceBodyFilterMap = nullptr; ///< Device copy of body-to-filter mapping.
    mutable float* m_deviceExtractedForce = nullptr; ///< Scratch for extracting vec3 from spatial_vector forces.

    float* m_deviceZeroVec3Buffer = nullptr; ///< Device zero buffer [rigidContactMax * 3], fallback for missing point
                                             ///< data.
    float* m_deviceZeroFloatBuffer = nullptr; ///< Device zero buffer [rigidContactMax], fallback for missing thickness
                                              ///< data.

    /// Allocates and uploads sensor/filter mapping tables to device memory.
    void _uploadMappingsToGpu();
    /// Allocates zero-filled fallback buffers on device for optional contact arrays.
    void _allocateFallbackBuffers();

    const float* _resolveContactForce() const;
    const float* _getContactPoint0() const;
    const float* _getContactPoint1() const;
    const float* _getThickness0() const;
    const float* _getThickness1() const;
};

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
