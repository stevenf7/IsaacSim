// Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//
#pragma once

#include <omni/sensors/cuda/CudaHelperMath.h>
#include <omni/sensors/lidar/LidarProfileTypes.h>
#include <omni/sensors/materials/MaterialProperties.h>

namespace omni
{
namespace sensors
{
namespace lidar
{


template <typename T>
NV_HOSTDEVICE inline T mapIntensityBigStep(const float* intensityMap,
                                           const uint32_t intensityMapElCount,
                                           const float intensity,
                                           const float scale = 255.f)
{
    const uint32_t idx{ static_cast<uint32_t>(intensity * (kMaxIntensityMapElements - 1)) };
    return intensityMapElCount > 0 ? static_cast<T>(scale * (intensity + intensityMap[idx])) :
                                     static_cast<T>(scale * intensity); // 0 means there was no intensity map
}


template <typename T>
NV_HOSTDEVICE inline T mapIntensitySmallStep(const float* intensityMap,
                                             const uint32_t intensityMapElCount,
                                             const float intensity,
                                             const float scale = 255.f)
{
    const uint32_t idx{ static_cast<uint32_t>(intensity * (static_cast<float>(intensityMapElCount) - 1.f)) };
    return intensityMapElCount > idx ? static_cast<T>(scale * intensityMap[idx]) : static_cast<T>(scale * intensity);
}

template <typename T>
NV_HOSTDEVICE inline T mapIntensity(const float* intensityMap,
                                    const uint32_t mapCount,
                                    const float intensity,
                                    const float scale)
{
    return mapCount < scale ? mapIntensityBigStep<T>(intensityMap, mapCount, intensity, scale) :
                              mapIntensitySmallStep<T>(intensityMap, mapCount, intensity, scale);
}

template <typename T>
NV_HOSTDEVICE inline T mapIntensity(const LidarBaseProfile& profile, const float intensity, const bool decoding)
{
    T result{ static_cast<T>(intensity * profile.intensityScalePercent) };
    if (decoding && (profile.intensityMapping == LidarIntensityMapping::NONLINEAR ||
                     profile.intensityMapping == LidarIntensityMapping::NONLINEAR_DECODING_ONLY))
    {
        result = mapIntensity<T>(
            profile.intensityMapDecoding, profile.intensityMapElCountDec, intensity, profile.intensityScalePercent);
    }
    else if (!decoding && (profile.intensityMapping == LidarIntensityMapping::NONLINEAR ||
                           profile.intensityMapping == LidarIntensityMapping::NONLINEAR_ENCODING_ONLY))
    {
        result = mapIntensity<T>(
            profile.intensityMapEncoding, profile.intensityMapElCountEnc, intensity, profile.intensityScalePercent);
    }
    return result;
}

} // namespace lidar
} // namespace sensors
} // namespace omni
