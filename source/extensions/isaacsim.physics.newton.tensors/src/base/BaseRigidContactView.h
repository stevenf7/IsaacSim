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

#include "utils/ViewUtils.h"

#include <omni/physics/tensors/IRigidContactView.h>
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

using omni::physics::tensors::IRigidContactView;
using omni::physics::tensors::TensorDesc;

/// Base contact view implementing IRigidContactView for Newton.
///
/// Builds sensor-to-body and filter-to-body mapping tables from USD paths. Caches
/// contact data pointers (forces, normals, shape indices, points) from the Newton
/// contacts object, refreshing lazily when the simulation timestamp changes.
/// Pre-allocates scratch buffers for contact counting and indexing.
class BaseRigidContactView : public IRigidContactView
{
public:
    BaseRigidContactView(py::object newtonStage,
                         const std::vector<std::string>& sensorPaths,
                         const std::vector<std::vector<std::string>>& filterPaths,
                         uint32_t maxContactDataCount);
    ~BaseRigidContactView() override;

    uint32_t getSensorCount() const override;
    uint32_t getFilterCount() const override;
    uint32_t getMaxContactDataCount() const override;

    bool getFrictionData(const TensorDesc* frictionForceTensor,
                         const TensorDesc* contactPointTensor,
                         const TensorDesc* contactCountTensor,
                         const TensorDesc* contactStartIndicesTensor,
                         float dt) const override;

    void getOtherActorPathsFromIds(const TensorDesc* otherActorIdsTensor,
                                   std::vector<std::string>& outPaths) const override;

    bool check() const override;
    void release() override;

    const char* getUsdPrimPath(uint32_t sensorIdx) const override;
    const char* getUsdPrimName(uint32_t sensorIdx) const override;
    const char* getFilterUsdPrimPath(uint32_t sensorIdx, uint32_t filterIdx) const override;
    const char* getFilterUsdPrimName(uint32_t sensorIdx, uint32_t filterIdx) const override;

protected:
    /// Caches shape_body pointer (static across simulation lifetime).
    void _cacheStaticPointers();
    /// Re-reads contact data pointers from Newton if the simulation timestamp has advanced.
    void _refreshContactPointers() const;
    float _getPhysicsDtScale(float userDt) const;

    py::object m_newtonStage;
    py::object m_model;

    uint32_t m_sensorCount;
    uint32_t m_filterCount;
    uint32_t m_maxContactDataCount;
    int m_rigidContactMax;
    int m_worldBodyIndex;
    int m_bodyCount;

    std::vector<std::string> m_sensorPaths;
    std::vector<std::string> m_sensorNames;
    std::vector<std::vector<std::string>> m_filterPaths;
    std::vector<std::vector<std::string>> m_filterNames;

    std::vector<int> m_hostBodySensorMap; ///< [numBodies] → sensor index, -1 if not a sensor.
    std::vector<int> m_hostBodyFilterMap; ///< [sensorCount * numBodies] → filter index per sensor, -1 if no match.

    mutable int* m_cachedContactCount = nullptr;
    mutable int* m_cachedShape0 = nullptr;
    mutable int* m_cachedShape1 = nullptr;
    mutable float* m_cachedContactNormal = nullptr;
    mutable float* m_cachedContactForce = nullptr;
    mutable float* m_cachedContactPoint0 = nullptr;
    mutable float* m_cachedContactPoint1 = nullptr;
    mutable float* m_cachedThickness0 = nullptr;
    mutable float* m_cachedThickness1 = nullptr;
    int* m_cachedShapeBody = nullptr;
    mutable float* m_cachedBodyQ = nullptr;

    mutable float* m_cachedSpatialForce = nullptr;
    mutable bool m_hasSpatialForce = false;

    std::vector<std::string> m_bodyLabels;

    mutable uint64_t m_lastRefreshedGeneration = UINT64_MAX; ///< Last-seen simulation_timestamp.
    float m_physicsDt = 0.0f; ///< Physics dt from SimulationManager for force-to-impulse scaling.
    mutable bool m_contactPointsInWorldSpace = false; ///< True when contact points are MuJoCo world-space positions.

    // Pre-allocated scratch buffers for contact counting (sized to sensorCount * max(filterCount, 1)).
    mutable std::vector<uint32_t> m_scratchCounts;
    mutable std::vector<uint32_t> m_scratchStartIndices;
    mutable std::vector<uint32_t> m_scratchFillCounts;
};

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
