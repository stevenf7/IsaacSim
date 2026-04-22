// SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

#include "CpuSimulationView.h"

#include "CpuArticulationView.h"
#include "CpuRigidBodyView.h"
#include "CpuRigidContactView.h"

namespace isaacsim
{
namespace physics
{
namespace newton
{
namespace tensors
{

using namespace omni::physics::tensors;

CpuSimulationView::CpuSimulationView(SimViewInit&& init) : BaseSimulationView(std::move(init))
{
}

int CpuSimulationView::getDeviceOrdinal() const
{
    return kCpuDeviceOrdinal;
}

int CpuSimulationView::getParamDeviceOrdinal() const
{
    return kCpuDeviceOrdinal;
}

void* CpuSimulationView::getCudaContext() const
{
    return nullptr;
}

IArticulationView* CpuSimulationView::_makeArticulationView(py::object newtonStage, const std::vector<pxr::SdfPath>& paths)
{
    return new CpuArticulationView(newtonStage, paths);
}

IRigidBodyView* CpuSimulationView::_makeRigidBodyView(py::object newtonStage, const std::vector<pxr::SdfPath>& paths)
{
    return new CpuRigidBodyView(newtonStage, paths);
}

IRigidContactView* CpuSimulationView::_makeRigidContactView(py::object newtonStage,
                                                            const std::vector<std::string>& sensorPaths,
                                                            const std::vector<std::vector<std::string>>& filterPaths,
                                                            uint32_t maxContactDataCount)
{
    return new CpuRigidContactView(newtonStage, sensorPaths, filterPaths, maxContactDataCount);
}

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
