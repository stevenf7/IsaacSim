// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

#include <carb/BindingsPythonUtils.h>

#include <isaacsim/core/experimental/prims/IPrimDataReader.h>
#include <isaacsim/core/experimental/prims/IPrimDataReaderManager.h>
#include <pybind11/functional.h>
#include <pybind11/stl.h>

CARB_BINDINGS("isaacsim.core.experimental.prims.python")

namespace
{

namespace py = pybind11;

PYBIND11_MODULE(_prims_reader, m)
{
    using namespace isaacsim::core::experimental::prims;

    m.doc() = "C++ read-only prim data reader interface for Isaac Sim";

    // Base view type
    py::class_<IXformDataView>(m, "IXformDataView")
        .def("get_world_positions",
             [](IXformDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getWorldPositions(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_world_orientations",
             [](IXformDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getWorldOrientations(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_local_translations",
             [](IXformDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getLocalTranslations(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_local_orientations",
             [](IXformDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getLocalOrientations(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_local_scales",
             [](IXformDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getLocalScales(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_world_positions_host",
             [](IXformDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getWorldPositionsHost(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_world_orientations_host",
             [](IXformDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getWorldOrientationsHost(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_local_translations_host",
             [](IXformDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getLocalTranslationsHost(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_local_orientations_host",
             [](IXformDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getLocalOrientationsHost(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_local_scales_host",
             [](IXformDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getLocalScalesHost(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("update", &IXformDataView::update)
        .def("allocate_buffer", &IXformDataView::allocateBuffer, py::arg("field_name"), py::arg("count"),
             py::arg("element_size"))
        .def("get_buffer_ptr", &IXformDataView::getBufferPtr, py::arg("field_name"))
        .def("get_buffer_size", &IXformDataView::getBufferSize, py::arg("field_name"))
        .def("get_buffer_device", &IXformDataView::getBufferDevice)
        .def("register_field_callback", &IXformDataView::registerFieldCallback, py::arg("field_name"),
             py::arg("callback"));

    // RigidBody view (inherits IXformDataView bindings)
    py::class_<IRigidBodyDataView, IXformDataView>(m, "IRigidBodyDataView")
        .def("get_linear_velocities",
             [](IRigidBodyDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getLinearVelocities(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_angular_velocities",
             [](IRigidBodyDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getAngularVelocities(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_linear_velocities_host",
             [](IRigidBodyDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getLinearVelocitiesHost(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_angular_velocities_host",
             [](IRigidBodyDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getAngularVelocitiesHost(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             });

    // Articulation view (inherits IXformDataView bindings)
    py::class_<IArticulationDataView, IXformDataView>(m, "IArticulationDataView")
        .def("get_dof_positions",
             [](IArticulationDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getDofPositions(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_dof_velocities",
             [](IArticulationDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getDofVelocities(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_dof_efforts",
             [](IArticulationDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getDofEfforts(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_root_transforms",
             [](IArticulationDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getRootTransforms(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_root_velocities",
             [](IArticulationDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getRootVelocities(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_dof_positions_host",
             [](IArticulationDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getDofPositionsHost(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_dof_velocities_host",
             [](IArticulationDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getDofVelocitiesHost(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_dof_efforts_host",
             [](IArticulationDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getDofEffortsHost(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_root_transforms_host",
             [](IArticulationDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getRootTransformsHost(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_root_velocities_host",
             [](IArticulationDataView& self)
             {
                 int count = 0;
                 const float* ptr = self.getRootVelocitiesHost(&count);
                 return std::make_tuple(reinterpret_cast<uintptr_t>(ptr), count);
             })
        .def("get_dof_index", &IArticulationDataView::getDofIndex, py::arg("dof_prim_path"));

    // Factory (Carbonite interface)
    carb::defineInterfaceClass<IPrimDataReader>(
        m, "IPrimDataReader", "acquire_prim_data_reader_interface", "release_prim_data_reader_interface")
        .def("initialize", &IPrimDataReader::initialize, py::arg("stage_id"), py::arg("device_ordinal"))
        .def("shutdown", &IPrimDataReader::shutdown)
        .def(
            "create_xform_view",
            [](IPrimDataReader& self, const std::string& viewId, const std::vector<std::string>& paths,
               const std::string& engineType)
            {
                std::vector<const char*> cStringPaths;
                cStringPaths.reserve(paths.size());
                for (auto& p : paths)
                    cStringPaths.push_back(p.c_str());
                return self.createXformView(viewId.c_str(), cStringPaths.data(), paths.size(), engineType.c_str());
            },
            py::arg("view_id"), py::arg("paths"), py::arg("engine_type"), py::return_value_policy::reference)
        .def(
            "create_rigid_body_view",
            [](IPrimDataReader& self, const std::string& viewId, const std::vector<std::string>& paths,
               const std::string& engineType)
            {
                std::vector<const char*> cStringPaths;
                cStringPaths.reserve(paths.size());
                for (auto& p : paths)
                    cStringPaths.push_back(p.c_str());
                return self.createRigidBodyView(viewId.c_str(), cStringPaths.data(), paths.size(), engineType.c_str());
            },
            py::arg("view_id"), py::arg("paths"), py::arg("engine_type"), py::return_value_policy::reference)
        .def(
            "create_articulation_view",
            [](IPrimDataReader& self, const std::string& viewId, const std::vector<std::string>& paths,
               const std::string& engineType)
            {
                std::vector<const char*> cStringPaths;
                cStringPaths.reserve(paths.size());
                for (auto& p : paths)
                    cStringPaths.push_back(p.c_str());
                return self.createArticulationView(viewId.c_str(), cStringPaths.data(), paths.size(), engineType.c_str());
            },
            py::arg("view_id"), py::arg("paths"), py::arg("engine_type"), py::return_value_policy::reference)
        .def("remove_view", &IPrimDataReader::removeView, py::arg("view_id"))
        .def("get_generation", &IPrimDataReader::getGeneration)
        .def("get_stage_id", &IPrimDataReader::getStageId)
        .def("get_device_ordinal", &IPrimDataReader::getDeviceOrdinal);

    carb::defineInterfaceClass<IPrimDataReaderManager>(m, "IPrimDataReaderManager",
                                                       "acquire_prim_data_reader_manager_interface",
                                                       "release_prim_data_reader_manager_interface")
        .def("ensure_initialized", &IPrimDataReaderManager::ensureInitialized, py::arg("stage_id"),
             py::arg("device_ordinal"))
        .def("get_reader", &IPrimDataReaderManager::getReader, py::return_value_policy::reference)
        .def("get_generation", &IPrimDataReaderManager::getGeneration);
}

} // anonymous namespace
