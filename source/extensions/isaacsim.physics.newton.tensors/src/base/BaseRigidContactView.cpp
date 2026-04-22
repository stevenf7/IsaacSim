// SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

#include "BaseRigidContactView.h"

#include "utils/TensorOps.h"
#include "utils/WarpInterop.h"

#include <carb/logging/Log.h>

#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include <algorithm>
#include <cstring>

namespace isaacsim
{
namespace physics
{
namespace newton
{
namespace tensors
{

using namespace omni::physics::tensors;

BaseRigidContactView::BaseRigidContactView(py::object newtonStage,
                                           const std::vector<std::string>& sensorPaths,
                                           const std::vector<std::vector<std::string>>& filterPaths,
                                           uint32_t maxContactDataCount)
    : m_newtonStage(newtonStage),
      m_maxContactDataCount(maxContactDataCount > 0 ? maxContactDataCount : 1000),
      m_sensorPaths(sensorPaths),
      m_filterPaths(filterPaths)
{
    py::gil_scoped_acquire gil;

    m_model = m_newtonStage.attr("model");

    int bodyCount = m_model.attr("body_count").cast<int>();
    m_worldBodyIndex = bodyCount;
    m_bodyCount = bodyCount + 1;
    m_rigidContactMax = m_model.attr("rigid_contact_max").cast<int>();

    py::list bodyLabel = m_model.attr("body_label").cast<py::list>();
    m_bodyLabels.reserve(static_cast<size_t>(py::len(bodyLabel)));
    for (auto item : bodyLabel)
        m_bodyLabels.push_back(py::str(item));

    std::vector<std::string> shapeLabels;
    std::vector<int> shapeBodyArr;
    if (py::hasattr(m_model, "shape_label"))
    {
        py::list sl = m_model.attr("shape_label").cast<py::list>();
        for (auto item : sl)
            shapeLabels.push_back(py::str(item));
    }
    if (py::hasattr(m_model, "shape_body"))
    {
        py::object sb = m_model.attr("shape_body");
        py::array_t<int> sbNp = sb.attr("numpy")().cast<py::array_t<int>>();
        auto sbData = sbNp.unchecked<1>();
        shapeBodyArr.resize(sbData.shape(0));
        for (py::ssize_t i = 0; i < sbData.shape(0); ++i)
            shapeBodyArr[i] = sbData(i);
    }

    m_sensorCount = static_cast<uint32_t>(m_sensorPaths.size());
    m_hostBodySensorMap.assign(m_bodyCount, -1);

    m_sensorNames.reserve(m_sensorCount);
    for (uint32_t si = 0; si < m_sensorCount; ++si)
    {
        pxr::SdfPath sdfPath(m_sensorPaths[si]);
        m_sensorNames.push_back(sdfPath.GetName());

        for (size_t bi = 0; bi < m_bodyLabels.size(); ++bi)
        {
            if (m_bodyLabels[bi] == m_sensorPaths[si])
            {
                m_hostBodySensorMap[bi] = static_cast<int>(si);
                break;
            }
        }
    }

    m_filterCount = 0;
    for (const auto& fp : m_filterPaths)
    {
        if (fp.size() > m_filterCount)
            m_filterCount = static_cast<uint32_t>(fp.size());
    }

    m_filterNames.resize(m_sensorCount);
    for (uint32_t si = 0; si < m_sensorCount; ++si)
    {
        if (si < m_filterPaths.size())
        {
            for (const auto& fp : m_filterPaths[si])
            {
                pxr::SdfPath sdfPath(fp);
                m_filterNames[si].push_back(sdfPath.GetName());
            }
        }
    }

    m_hostBodyFilterMap.assign(static_cast<size_t>(m_sensorCount) * m_bodyCount, -1);
    for (uint32_t si = 0; si < m_sensorCount; ++si)
    {
        if (si >= m_filterPaths.size())
            continue;
        for (uint32_t fi = 0; fi < static_cast<uint32_t>(m_filterPaths[si].size()); ++fi)
        {
            const std::string& filterPath = m_filterPaths[si][fi];
            if (filterPath.empty())
                continue;

            bool resolved = false;
            for (size_t bi = 0; bi < m_bodyLabels.size(); ++bi)
            {
                if (m_bodyLabels[bi] == filterPath)
                {
                    m_hostBodyFilterMap[si * m_bodyCount + bi] = static_cast<int>(fi);
                    resolved = true;
                    break;
                }
            }
            if (resolved)
                continue;

            int bestBi = -1;
            size_t bestLen = 0;
            for (size_t bi = 0; bi < m_bodyLabels.size(); ++bi)
            {
                std::string prefix = m_bodyLabels[bi] + "/";
                if (filterPath.rfind(prefix, 0) == 0 && m_bodyLabels[bi].size() > bestLen)
                {
                    bestBi = static_cast<int>(bi);
                    bestLen = m_bodyLabels[bi].size();
                }
            }
            if (bestBi >= 0)
            {
                m_hostBodyFilterMap[si * m_bodyCount + bestBi] = static_cast<int>(fi);
                continue;
            }

            for (size_t shi = 0; shi < shapeLabels.size() && shi < shapeBodyArr.size(); ++shi)
            {
                const std::string& sl = shapeLabels[shi];
                if (shapeBodyArr[shi] != -1)
                    continue;
                if (sl == filterPath || filterPath.rfind(sl + "/", 0) == 0 || sl.rfind(filterPath + "/", 0) == 0)
                {
                    m_hostBodyFilterMap[si * m_bodyCount + m_worldBodyIndex] = static_cast<int>(fi);
                    resolved = true;
                    break;
                }
            }
        }
    }

    size_t maxScratch = static_cast<size_t>(m_sensorCount) * std::max(m_filterCount, 1u);
    m_scratchCounts.resize(maxScratch, 0);
    m_scratchStartIndices.resize(maxScratch, 0);
    m_scratchFillCounts.resize(maxScratch, 0);

    _cacheStaticPointers();
    _refreshContactPointers();
}

BaseRigidContactView::~BaseRigidContactView()
{
}

void BaseRigidContactView::_cacheStaticPointers()
{
    py::gil_scoped_acquire gil;
    m_cachedShapeBody = warpArrayFromPython<int>(m_model.attr("shape_body")).data;
}

void BaseRigidContactView::_refreshContactPointers() const
{
    py::gil_scoped_acquire gil;

    try
    {
        uint64_t gen = m_newtonStage.attr("simulation_timestamp").cast<uint64_t>();
        if (gen == m_lastRefreshedGeneration)
            return;
        m_lastRefreshedGeneration = gen;
    }
    catch (...)
    {
    }

    auto ptr = [](py::object arr) -> float* { return warpArrayFromPython<float>(arr).data; };
    auto iptr = [](py::object arr) -> int* { return warpArrayFromPython<int>(arr).data; };

    py::object contacts = m_newtonStage.attr("contacts");
    if (contacts.is_none())
        return;

    m_cachedContactCount = iptr(contacts.attr("rigid_contact_count"));
    m_cachedShape0 = iptr(contacts.attr("rigid_contact_shape0"));
    m_cachedShape1 = iptr(contacts.attr("rigid_contact_shape1"));
    m_cachedContactNormal = ptr(contacts.attr("rigid_contact_normal"));
    m_cachedBodyQ = ptr(m_newtonStage.attr("state_0").attr("body_q"));

    py::object spatialForce = py::none();
    if (py::hasattr(contacts, "force"))
        spatialForce = contacts.attr("force");
    if (!spatialForce.is_none())
    {
        m_cachedSpatialForce = ptr(spatialForce);
        m_hasSpatialForce = true;
        m_cachedContactForce = nullptr;
    }
    else
    {
        m_cachedSpatialForce = nullptr;
        m_hasSpatialForce = false;
        py::object rcForce = py::none();
        if (py::hasattr(contacts, "rigid_contact_force"))
            rcForce = contacts.attr("rigid_contact_force");
        m_cachedContactForce = rcForce.is_none() ? nullptr : ptr(rcForce);
    }

    m_cachedContactPoint0 = nullptr;
    m_cachedContactPoint1 = nullptr;
    m_cachedThickness0 = nullptr;
    m_cachedThickness1 = nullptr;
    if (py::hasattr(contacts, "rigid_contact_point0") && !contacts.attr("rigid_contact_point0").is_none())
        m_cachedContactPoint0 = ptr(contacts.attr("rigid_contact_point0"));
    if (py::hasattr(contacts, "rigid_contact_point1") && !contacts.attr("rigid_contact_point1").is_none())
        m_cachedContactPoint1 = ptr(contacts.attr("rigid_contact_point1"));
    if (py::hasattr(contacts, "rigid_contact_thickness0") && !contacts.attr("rigid_contact_thickness0").is_none())
        m_cachedThickness0 = ptr(contacts.attr("rigid_contact_thickness0"));
    if (py::hasattr(contacts, "rigid_contact_thickness1") && !contacts.attr("rigid_contact_thickness1").is_none())
        m_cachedThickness1 = ptr(contacts.attr("rigid_contact_thickness1"));
}

float BaseRigidContactView::_getPhysicsDtScale(float) const
{
    return 1.0f;
}

uint32_t BaseRigidContactView::getSensorCount() const
{
    return m_sensorCount;
}
uint32_t BaseRigidContactView::getFilterCount() const
{
    return m_filterCount;
}
uint32_t BaseRigidContactView::getMaxContactDataCount() const
{
    return m_maxContactDataCount;
}

bool BaseRigidContactView::check() const
{
    return true;
}
void BaseRigidContactView::release()
{
    delete this;
}

const char* BaseRigidContactView::getUsdPrimPath(uint32_t sensorIdx) const
{
    return (sensorIdx < m_sensorPaths.size()) ? m_sensorPaths[sensorIdx].c_str() : "";
}
const char* BaseRigidContactView::getUsdPrimName(uint32_t sensorIdx) const
{
    return (sensorIdx < m_sensorNames.size()) ? m_sensorNames[sensorIdx].c_str() : "";
}
const char* BaseRigidContactView::getFilterUsdPrimPath(uint32_t sensorIdx, uint32_t filterIdx) const
{
    if (sensorIdx < m_filterPaths.size() && filterIdx < m_filterPaths[sensorIdx].size())
        return m_filterPaths[sensorIdx][filterIdx].c_str();
    return "";
}
const char* BaseRigidContactView::getFilterUsdPrimName(uint32_t sensorIdx, uint32_t filterIdx) const
{
    if (sensorIdx < m_filterNames.size() && filterIdx < m_filterNames[sensorIdx].size())
        return m_filterNames[sensorIdx][filterIdx].c_str();
    return "";
}

bool BaseRigidContactView::getFrictionData(
    const TensorDesc*, const TensorDesc*, const TensorDesc*, const TensorDesc*, float) const
{
    return false;
}

void BaseRigidContactView::getOtherActorPathsFromIds(const TensorDesc* otherActorIdsTensor,
                                                     std::vector<std::string>& outPaths) const
{
    if (!otherActorIdsTensor || !otherActorIdsTensor->data)
        return;

    uint32_t n = static_cast<uint32_t>(getTensorTotalSize(*otherActorIdsTensor));
    std::vector<uint64_t> hostIds(n);

    if (otherActorIdsTensor->device >= 0)
    {
        cudaMemcpy(hostIds.data(), otherActorIdsTensor->data, n * sizeof(uint64_t), cudaMemcpyDeviceToHost);
    }
    else
    {
        std::memcpy(hostIds.data(), otherActorIdsTensor->data, n * sizeof(uint64_t));
    }

    outPaths.resize(n);
    for (uint32_t i = 0; i < n; ++i)
    {
        uint64_t bodyIdx = hostIds[i];
        if (bodyIdx == static_cast<uint64_t>(m_worldBodyIndex))
        {
            outPaths[i] = "world";
        }
        else if (bodyIdx < m_bodyLabels.size())
        {
            outPaths[i] = m_bodyLabels[bodyIdx];
        }
        else
        {
            outPaths[i] = "";
        }
    }
}

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
