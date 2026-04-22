// SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

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

/// CPU simulation view. Reports device ordinal -1 and creates Cpu* child views.
class CpuSimulationView : public BaseSimulationView
{
public:
    explicit CpuSimulationView(SimViewInit&& init);
    ~CpuSimulationView() override = default;

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

private:
    static constexpr int kCpuDeviceOrdinal = -1;
};

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
