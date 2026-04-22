// SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <omni/physics/tensors/ISimulationBackend.h>

namespace isaacsim
{
namespace physics
{
namespace newton
{
namespace tensors
{

using omni::physics::tensors::ISimulationBackend;
using omni::physics::tensors::ISimulationView;

/// Newton tensor backend entry point.
///
/// Registered as an omni.physics.tensors plugin. Creates either a CpuSimulationView or
/// GpuSimulationView depending on the Newton model's simulation device.
class SimulationBackend : public ISimulationBackend
{
public:
    SimulationBackend();
    ~SimulationBackend() override;

    /// Initializes Newton via pybind11, detects the simulation device, and returns
    /// a CpuSimulationView (device ordinal -1) or GpuSimulationView (ordinal >= 0).
    ISimulationView* createSimulationView(long stageId = -1) override;
    void reset() override;
};

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
