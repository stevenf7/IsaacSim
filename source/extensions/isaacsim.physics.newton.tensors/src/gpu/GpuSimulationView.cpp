// SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

#include "GpuSimulationView.h"

#include "GpuArticulationView.h"
#include "GpuRigidBodyView.h"
#include "GpuRigidContactView.h"

namespace isaacsim
{
namespace physics
{
namespace newton
{
namespace tensors
{

using namespace omni::physics::tensors;

GpuSimulationView::GpuSimulationView(SimViewInit&& init) : BaseSimulationView(std::move(init))
{
}

int GpuSimulationView::getDeviceOrdinal() const
{
    return m_simDeviceOrdinal;
}

int GpuSimulationView::getParamDeviceOrdinal() const
{
    return m_simDeviceOrdinal;
}

void* GpuSimulationView::getCudaContext() const
{
    return nullptr;
}

IArticulationView* GpuSimulationView::_makeArticulationView(py::object newtonStage, const std::vector<pxr::SdfPath>& paths)
{
    return new GpuArticulationView(newtonStage, paths, m_simDeviceOrdinal);
}

IRigidBodyView* GpuSimulationView::_makeRigidBodyView(py::object newtonStage, const std::vector<pxr::SdfPath>& paths)
{
    return new GpuRigidBodyView(newtonStage, paths, m_simDeviceOrdinal);
}

IRigidContactView* GpuSimulationView::_makeRigidContactView(py::object newtonStage,
                                                            const std::vector<std::string>& sensorPaths,
                                                            const std::vector<std::vector<std::string>>& filterPaths,
                                                            uint32_t maxContactDataCount)
{
    return new GpuRigidContactView(newtonStage, sensorPaths, filterPaths, maxContactDataCount, m_simDeviceOrdinal);
}

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
