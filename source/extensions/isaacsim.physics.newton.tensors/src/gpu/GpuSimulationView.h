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

#include "base/BaseSimulationView.h"

namespace isaacsim
{
namespace physics
{
namespace newton
{
namespace tensors
{

using omni::physics::tensors::IArticulationView;
using omni::physics::tensors::IRigidBodyView;
using omni::physics::tensors::IRigidContactView;

/// GPU simulation view. Reports the CUDA device ordinal and creates Gpu* child views.
class GpuSimulationView : public BaseSimulationView
{
public:
    explicit GpuSimulationView(SimViewInit&& init);
    ~GpuSimulationView() override = default;

    int getDeviceOrdinal() const override;
    int getParamDeviceOrdinal() const override;
    void* getCudaContext() const override;

protected:
    IArticulationView* _makeArticulationView(py::object newtonStage, const std::vector<pxr::SdfPath>& paths) override;
    IRigidBodyView* _makeRigidBodyView(py::object newtonStage, const std::vector<pxr::SdfPath>& paths) override;
    IRigidContactView* _makeRigidContactView(py::object newtonStage,
                                             const std::vector<std::string>& sensorPaths,
                                             const std::vector<std::vector<std::string>>& filterPaths,
                                             uint32_t maxContactDataCount) override;
};

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
