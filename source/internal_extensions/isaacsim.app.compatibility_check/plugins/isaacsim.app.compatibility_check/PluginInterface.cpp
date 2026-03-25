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

#define CARB_EXPORTS

#include <carb/PluginUtils.h>
#include <carb/graphics/Graphics.h>
#include <carb/settings/ISettings.h>

#include <gpu/foundation/Foundation.h>
#include <isaacsim/app/compatibility_check/ICompatibilityCheck.h>
#include <omni/kit/renderer/IGpuFoundation.h>

#include <iomanip>

/**
 * @brief Plugin descriptor for the compatibility check plugin.
 * @details
 * Defines metadata for the compatibility check plugin including name, description,
 * and hot reload capability.
 */
const struct carb::PluginImplDesc g_kPluginDesc = { "isaacsim.app.compatibility_check.plugin",
                                                    "Isaac Sim compatibility check", "NVIDIA",
                                                    carb::PluginHotReload::eDisabled, "dev" };

namespace isaacsim
{
namespace app
{
namespace compatibility_check
{

/**
 * @class CompatibilityCheck
 * @brief Implementation of the ICompatibilityCheckInterface interface.
 * @details
 * This class provides functionality to check the compatibility of the system with Isaac Sim.
 */
class CompatibilityCheck : public ICompatibilityCheckInterface
{
public:
    bool getRtxGpuInfo(std::vector<RtxGpuInfo>& rtxGpuInfos, const bool& createGpuFoundation) override
    {
        omni::kit::renderer::IGpuFoundation* kitFoundationFactory = nullptr;
        gpu::foundation::IGpuFoundationFactory* gpuFoundationFactory = nullptr;
        gpu::foundation::IGpuFoundation* gpuFoundation = nullptr;
        gpu::foundation::GpuDevices* gpuDevices = nullptr;
        carb::graphics::Device* device = nullptr;
        carb::graphics::Graphics* graphics = nullptr;

        // get carb framework
        carb::Framework* framework = carb::getFramework();
        if (!framework)
        {
            CARB_LOG_WARN("Failed to acquire carb framework");
            return false;
        }

        // create carb graphics
        graphics = _createCarbGraphics(framework);

        // create GPU foundation and devices
        if (createGpuFoundation)
        {
            // get cached GPU foundation factory plugin
            gpuFoundationFactory = carb::getCachedInterface<gpu::foundation::IGpuFoundationFactory>();
            if (!gpuFoundationFactory)
            {
                CARB_LOG_WARN("Failed to acquire GPU foundation plugin");
                return false;
            }

            gpu::foundation::GpuFoundationDesc gpuFoundationDesc = {};
            gpuFoundationDesc.graphics = graphics;
            gpuFoundation = gpuFoundationFactory->createGpuFoundation(gpuFoundationDesc);
            if (!gpuFoundation)
            {
                CARB_LOG_WARN("Failed to create GPU foundation");
                return false;
            }

            gpu::foundation::GpuDeviceDesc deviceDesc = {};
            deviceDesc.deviceFlags = gpu::foundation::kDeviceFlagRaytracing;
            deviceDesc.deviceEnumFlags = gpu::foundation::kDeviceEnumFlagAllowNonRtCoreDiscreteGpu;
            deviceDesc.deviceEnumFlags |= gpu::foundation::kDeviceEnumFlagAllowLinkedDisplayAdapter;

            gpuDevices = gpuFoundation->createDevices(deviceDesc);
            if (!gpuDevices)
            {
                CARB_LOG_WARN("Failed to create devices");
                return false;
            }
        }
        // get GPU foundation and devices
        else
        {
            // get cached GPU foundation factory plugin
            kitFoundationFactory = carb::getCachedInterface<omni::kit::renderer::IGpuFoundation>();
            if (!kitFoundationFactory)
            {
                CARB_LOG_WARN("Failed to acquire GPU foundation plugin");
                return false;
            }

            gpuFoundation = kitFoundationFactory->getGpuFoundation();
            if (!gpuFoundation)
            {
                CARB_LOG_WARN("Failed to get GPU foundation");
                return false;
            }

            gpuDevices = kitFoundationFactory->getGpuFoundationDevices();
            if (!gpuDevices)
            {
                CARB_LOG_WARN("Failed to get devices");
                return false;
            }
        }

        // get GPU foundation device info
        gpu::foundation::DeviceInfo deviceInfo = {};
        gpu::GfResult gfResult = gpuFoundation->getDeviceInfo(gpuDevices, &deviceInfo);
        if (!(gfResult == gpu::GfResult::eSuccess && deviceInfo.deviceGroup->getDeviceCount() != 0))
        {
            CARB_LOG_WARN("Failed to get device info");
            return false;
        }

        for (uint32_t i = 0; i < deviceInfo.deviceGroup->getDeviceCount(); ++i)
        {
            RtxGpuInfo rtxGpuInfo;
            // get device
            device = deviceInfo.deviceGroup->getDevice(i);
            // get RTX flags
            const carb::graphics::DeviceCaps deviceCaps = graphics->getDeviceCaps(device);
            rtxGpuInfo.raytracingSupported = deviceCaps.raytracingSupported;
            rtxGpuInfo.raytracingShaderFeature =
                (deviceCaps.shaderFeatures & carb::graphics::kShaderFeatureFlagRayTraceExt);
            // get device UUID
            const carb::graphics::PhysicalDeviceDesc& physicalDeviceDesc =
                graphics->getPhysicalDeviceDesc(graphics->getPhysicalDevice(device));
            rtxGpuInfo.deviceUUID =
                _uint8ArrayToHexString(physicalDeviceDesc.deviceProperties.deviceUuid, OMNI_UUID_SIZE);
            // get other identifiers
            rtxGpuInfo.pciBusId = _uint32ToHexString(physicalDeviceDesc.deviceProperties.pciBusId);
            rtxGpuInfo.deviceId = _uint32ToHexString(physicalDeviceDesc.deviceId);
            rtxGpuInfo.vendorId = _uint32ToHexString(physicalDeviceDesc.vendorId);
            rtxGpuInfo.subSysId = _uint32ToHexString(physicalDeviceDesc.subSysId);
            // store info
            rtxGpuInfos.push_back(rtxGpuInfo);
        }

        // release resources
        if (createGpuFoundation)
        {
            gpuFoundation->releaseDevices(gpuDevices);
            gpuFoundation->release();
        }

        return true;
    }

private:
    std::string _uint8ArrayToHexString(const uint8_t* array, const size_t length)
    {
        std::stringstream stringStream;
        for (size_t i = 0; i < length; i++)
        {
            stringStream << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(array[i]);
        }
        return stringStream.str();
    }

    std::string _uint32ToHexString(const uint32_t value)
    {
        std::stringstream stringStream;
        stringStream << std::hex << std::setw(2) << std::setfill('0') << value;
        return stringStream.str();
    }

    carb::graphics::Graphics* _createCarbGraphics(carb::Framework* framework)
    {
        carb::settings::ISettings* settings = framework->acquireInterface<carb::settings::ISettings>();
        // get graphics API
        settings->setDefaultString("/app/graphics/api", "direct3d");
        std::string graphicsApi = settings->getStringBuffer("/app/graphics/api");
#if CARB_PLATFORM_WINDOWS
        bool useVulkan = _stricmp(graphicsApi.c_str(), "vulkan") == 0;
#else
        bool useVulkan = true;
#endif
        // acquire graphics plugin
        carb::graphics::Graphics* graphics = framework->acquireInterface<carb::graphics::Graphics>(
            useVulkan ? "carb.graphics-vulkan.plugin" : "carb.graphics-direct3d.plugin");
        CARB_FATAL_UNLESS(graphics != nullptr, "Failed to acquire graphics");
        return graphics;
    }
};

} // namespace compatibility_check
} // namespace app
} // namespace isaacsim

CARB_PLUGIN_IMPL(g_kPluginDesc, isaacsim::app::compatibility_check::CompatibilityCheck)
CARB_PLUGIN_IMPL_DEPS(carb::graphics::Graphics, carb::settings::ISettings)

/**
 * @brief Fills the interface with function pointers.
 * @details
 * This function is called by the Carbonite plugin system to initialize
 * the plugin interface.
 *
 * @param[in,out] iface The interface instance to be filled.
 */
void fillInterface(isaacsim::app::compatibility_check::CompatibilityCheck& iface)
{
}
