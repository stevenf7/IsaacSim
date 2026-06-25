// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

// clang-format off
#include <pch/UsdPCH.h>
// clang-format on

#include "isaacsim/core/includes/BaseResetNode.h"
#include "isaacsim/core/includes/Buffer.h"

#include <OgnIsaacMapScalarsToColorsDatabase.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>

namespace isaacsim
{
namespace core
{
namespace nodes
{

// Maps a host buffer of scalar values (e.g. lidar distance) to an RGBA color per scalar, using a hue ramp.
class OgnIsaacMapScalarsToColors : public isaacsim::core::includes::BaseResetNode
{
public:
    void reset() override
    {
        m_colorBuffer.resize(0);
    }

    static bool compute(OgnIsaacMapScalarsToColorsDatabase& db)
    {
        auto& state = db.perInstanceState<OgnIsaacMapScalarsToColors>();

        // The scalar count is fully determined by the buffer size
        const size_t scalarCount = static_cast<size_t>(db.inputs.scalarBufferSize() / sizeof(float));
        // Nothing to map (e.g. a scalar field the sensor does not produce): clear the outputs and exit
        if (scalarCount == 0)
        {
            resetColorOutputs(db);
            return false;
        }

        // A nonzero buffer size with a null pointer is an inconsistent input
        const uint64_t scalarPtr = db.inputs.scalarPtr();
        if (scalarPtr == 0)
        {
            db.logError("Scalar buffer pointer must be nonzero when scalarBufferSize is nonzero.");
            resetColorOutputs(db);
            return false;
        }

        // Find the min/max to normalize against, over the finite values only, and count any
        // non-finite scalars (NaN / +-Inf) so they cannot corrupt the range.
        const auto* scalars = reinterpret_cast<const float*>(scalarPtr);
        float minScalar = 0.0f;
        float maxScalar = 0.0f;
        const size_t nonFiniteCount = computeScalarRange(scalars, scalarCount, minScalar, maxScalar);
        if (nonFiniteCount > 0)
        {
            db.logWarning(
                "IsaacMapScalarsToColors: %zu of %zu scalar values were non-finite; "
                "coloring those points with the fallback color.",
                nonFiniteCount, scalarCount);
        }

        // Map each scalar through the ramp into the persistent host buffer that colorsPtr exposes.
        state.m_colorBuffer.resize(scalarCount);
        pxr::GfVec4f* colorBuffer = state.m_colorBuffer.data();
        const bool logScaleMode = db.inputs.logScaleMode();
        const pxr::GfVec4f& baseColor = db.inputs.baseColor();
        const pxr::GfVec4f nonFiniteColor(0.0f, 0.0f, 0.0f, 1.0f);
        for (size_t index = 0; index < scalarCount; ++index)
        {
            const float scalar = scalars[index];
            if (!std::isfinite(scalar))
            {
                colorBuffer[index] = nonFiniteColor;
                continue;
            }
            const float normalized = normalizeScalar(scalar, minScalar, maxScalar);
            const float scaled = applyScaleMode(normalized, logScaleMode);
            colorBuffer[index] = convertNormalizedScalarToColor(scaled, baseColor);
        }

        // Expose the host color buffer as a pointer for the downstream node
        db.outputs.colorsPtr() = reinterpret_cast<uint64_t>(colorBuffer);
        db.outputs.colorsBufferSize() = scalarCount * sizeof(pxr::GfVec4f);

        db.outputs.execOut() = kExecutionAttributeStateEnabled;
        return true;
    }

private:
    isaacsim::core::includes::HostBufferBase<pxr::GfVec4f> m_colorBuffer;

    // Clear the color outputs (used on the no-data / error paths)
    static void resetColorOutputs(OgnIsaacMapScalarsToColorsDatabase& db)
    {
        db.outputs.colorsPtr() = 0;
        db.outputs.colorsBufferSize() = 0;
    }

    // Compute the min/max over the finite scalar values; return how many were non-finite.
    static size_t computeScalarRange(const float* scalars, const size_t scalarCount, float& minScalar, float& maxScalar)
    {
        minScalar = std::numeric_limits<float>::max();
        maxScalar = std::numeric_limits<float>::lowest();

        size_t nonFiniteCount = 0;
        for (size_t index = 0; index < scalarCount; ++index)
        {
            const float scalar = scalars[index];
            if (!std::isfinite(scalar))
            {
                ++nonFiniteCount;
                continue;
            }
            minScalar = std::min(minScalar, scalar);
            maxScalar = std::max(maxScalar, scalar);
        }
        return nonFiniteCount;
    }

    // Map a scalar into [0, 1] across the value range (1.0 when the range is empty)
    static float normalizeScalar(const float scalar, const float minScalar, const float maxScalar)
    {
        const double range = static_cast<double>(maxScalar) - static_cast<double>(minScalar);
        if (range == 0.0)
        {
            return 1.0f;
        }

        const double normalized = (static_cast<double>(scalar) - static_cast<double>(minScalar)) / range;
        return static_cast<float>(normalized);
    }

    // Optionally apply log scaling so nearer/smaller values get more color resolution
    static float applyScaleMode(const float normalized, const bool logScaleMode)
    {
        if (logScaleMode)
        {
            return std::log1p(normalized) / std::log1p(1.0f);
        }
        return normalized;
    }

    // Convert a normalized [0, 1] scalar to an RGBA color via the ramp, scaled by baseColor
    static pxr::GfVec4f convertNormalizedScalarToColor(const float normalized, const pxr::GfVec4f& baseColor)
    {
        struct Rgb
        {
            float red;
            float green;
            float blue;
        };

        // Low scalar (blue) to high scalar (red)
        constexpr Rgb kColorRamp[] = {
            { 0.0f, 0.0f, 1.0f }, { 0.0f, 1.0f, 1.0f }, { 0.0f, 1.0f, 0.0f },
            { 1.0f, 1.0f, 0.0f }, { 1.0f, 0.0f, 0.0f },
        };
        constexpr size_t kLastRampIndex = (sizeof(kColorRamp) / sizeof(kColorRamp[0])) - 1;

        // Clamp values at or beyond the ends to the ramp endpoints
        if (normalized <= 0.0f)
        {
            return pxr::GfVec4f(kColorRamp[0].red * baseColor[0], kColorRamp[0].green * baseColor[1],
                                kColorRamp[0].blue * baseColor[2], baseColor[3]);
        }
        if (normalized >= 1.0f)
        {
            return pxr::GfVec4f(kColorRamp[kLastRampIndex].red * baseColor[0],
                                kColorRamp[kLastRampIndex].green * baseColor[1],
                                kColorRamp[kLastRampIndex].blue * baseColor[2], baseColor[3]);
        }

        // Interpolate between the two adjacent ramp stops
        const float rampPosition = normalized * static_cast<float>(kLastRampIndex);
        const size_t rampIndex = static_cast<size_t>(rampPosition);
        const float segmentRatio = rampPosition - static_cast<float>(rampIndex);

        const Rgb& lowerColor = kColorRamp[rampIndex];
        const Rgb& upperColor = kColorRamp[rampIndex + 1];
        const float red = lowerColor.red + (upperColor.red - lowerColor.red) * segmentRatio;
        const float green = lowerColor.green + (upperColor.green - lowerColor.green) * segmentRatio;
        const float blue = lowerColor.blue + (upperColor.blue - lowerColor.blue) * segmentRatio;

        return pxr::GfVec4f(red * baseColor[0], green * baseColor[1], blue * baseColor[2], baseColor[3]);
    }
};

REGISTER_OGN_NODE()

}
}
}
