// SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <omni/physics/tensors/ISimulationView.h>
#include <pxr/usd/sdf/path.h>
#include <pxr/usd/usd/prim.h>
#include <pxr/usd/usd/stage.h>
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

using omni::physics::tensors::IArticulationView;
using omni::physics::tensors::IDeformableBodyView;
using omni::physics::tensors::IDeformableMaterialView;
using omni::physics::tensors::IRigidBodyView;
using omni::physics::tensors::IRigidContactView;
using omni::physics::tensors::ISdfShapeView;
using omni::physics::tensors::ISimulationView;
using omni::physics::tensors::ObjectType;

/// Initialization data extracted from the Python Newton stage.
/// Produced by BaseSimulationView::initNewton() and consumed by Cpu/GpuSimulationView constructors.
struct SimViewInit
{
    py::object usdStage;
    py::object newtonStage;
    py::object model;
    int simDeviceOrdinal = -1; ///< -1 for CPU, >= 0 for GPU CUDA device ordinal.
    bool valid = false;
};

/// Base simulation view implementing ISimulationView for the Newton backend.
///
/// Holds the Python Newton stage and model references, implements shared logic for step,
/// gravity, object-type queries, and USD pattern matching. Factory methods for child views
/// (articulation, rigid body, rigid contact) resolve USD patterns and delegate to pure
/// virtual make*View() methods overridden by Cpu/GpuSimulationView.
class BaseSimulationView : public ISimulationView
{
public:
    /// Acquires the GIL, imports the Newton Python module, obtains the NewtonStage and model,
    /// and reads the simulation device ordinal.
    static SimViewInit initNewton(long stageId);

    ~BaseSimulationView() override;

    bool getValid() const override;
    void invalidate() override;
    bool check() const override;
    bool setSubspaceRoots(const char* pattern) override;

    void step(float dt) override;
    bool setGravity(const carb::Float3& gravity) override;
    bool getGravity(carb::Float3& gravity) override;

    ObjectType getObjectType(const char* path) override;
    void clearForces() override;
    bool flush() override;
    void updateArticulationsKinematic() override;
    void InitializeKinematicBodies() override;
    void enableGpuUsageWarnings(bool enable) override;
    void release(bool recursive) override;

    // Unsupported view stubs
    ISdfShapeView* createSdfShapeView(const char* pattern, uint32_t numSamplePoints) override;
    IDeformableBodyView* createVolumeDeformableBodyView(const char* pattern) override;
    IDeformableBodyView* createVolumeDeformableBodyView(const std::vector<std::string>& patterns) override;
    IDeformableBodyView* createSurfaceDeformableBodyView(const char* pattern) override;
    IDeformableBodyView* createSurfaceDeformableBodyView(const std::vector<std::string>& patterns) override;
    IDeformableMaterialView* createDeformableMaterialView(const char* pattern) override;
    IDeformableMaterialView* createDeformableMaterialView(const std::vector<std::string>& patterns) override;

    // Factory methods — shared logic in Base, delegates to newXxxView()
    IArticulationView* createArticulationView(const char* pattern) override;
    IArticulationView* createArticulationView(const std::vector<std::string>& patterns) override;

    IRigidBodyView* createRigidBodyView(const char* pattern) override;
    IRigidBodyView* createRigidBodyView(const std::vector<std::string>& patterns) override;

    IRigidContactView* createRigidContactView(const char* pattern,
                                              const char** filterPatterns,
                                              uint32_t numFilterPatterns,
                                              uint32_t maxContactDataCount) override;
    IRigidContactView* createRigidContactView(std::string pattern,
                                              const std::vector<std::string>& filterPatterns,
                                              uint32_t maxContactDataCount) override;
    IRigidContactView* createRigidContactView(const std::vector<std::string>& patterns,
                                              const std::vector<std::vector<std::string>>& filterPatterns,
                                              uint32_t maxContactDataCount) override;

    int getSimDeviceOrdinal() const
    {
        return m_simDeviceOrdinal;
    }
    py::object& getNewtonStage()
    {
        return m_newtonStage;
    }
    py::object& getModel()
    {
        return m_model;
    }

protected:
    explicit BaseSimulationView(SimViewInit&& init);

    /// Device-specific factory methods. Overridden by CpuSimulationView and GpuSimulationView
    /// to instantiate the appropriate Cpu* or Gpu* view class.
    virtual IArticulationView* _makeArticulationView(py::object newtonStage, const std::vector<pxr::SdfPath>& paths) = 0;
    virtual IRigidBodyView* _makeRigidBodyView(py::object newtonStage, const std::vector<pxr::SdfPath>& paths) = 0;
    virtual IRigidContactView* _makeRigidContactView(py::object newtonStage,
                                                     const std::vector<std::string>& sensorPaths,
                                                     const std::vector<std::vector<std::string>>& filterPaths,
                                                     uint32_t maxContactDataCount) = 0;

    void _findMatchingPaths(const std::string& pattern, std::vector<pxr::SdfPath>& pathsRet);
    void _findMatchingChildren(const pxr::UsdPrim& prim, const std::string& pattern, std::vector<pxr::UsdPrim>& matchesRet);

    py::object m_usdStage;
    py::object m_newtonStage;
    py::object m_model;
    int m_simDeviceOrdinal;
    bool m_valid;
    carb::Float3 m_gravity = { 0.0f, 0.0f, -9.81f };
};

} // namespace tensors
} // namespace newton
} // namespace physics
} // namespace isaacsim
