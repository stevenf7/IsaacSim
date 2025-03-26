// SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: LicenseRef-NvidiaProprietary
//
// NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
// property and proprietary rights in and to this material, related
// documentation and any modifications thereto. Any use, reproduction,
// disclosure or distribution of this material and related documentation
// without an express license agreement from NVIDIA CORPORATION or
// its affiliates is strictly prohibited.

#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

namespace isaacsim
{
namespace core
{
namespace includes
{
/**
 * @namespace color
 * @brief Provides color conversion and gradient utility functions
 * @details
 * Contains utility functions for generating color gradients and converting between
 * different color formats. Useful for data visualization and UI applications.
 */
namespace color
{

/**
 * @brief Converts a ratio value to a 32-bit RGBA color
 * @details
 * Generates a color from the rainbow color spectrum (ROYGBIV) based on the input ratio.
 * The ratio is mapped to six color regions, creating a smooth gradient transition between them.
 *
 * @param[in] ratio A value between 0.0 and 1.0 representing position in the color gradient
 * @param[in] bigEndian Whether to use big endian byte order for the resulting color
 * @return 32-bit RGBA color value with an alpha of 255 (fully opaque)
 *
 * @note The implementation is adapted from a StackOverflow solution
 */
// taken from https://stackoverflow.com/questions/40629345/fill-array-dynamicly-with-gradient-color-c
static inline uint32_t distToColor(double ratio, bool bigEndian)
{
    // we want to normalize ratio so that it fits in to 6 regions
    // where each region is 256 units long
    int normalized = static_cast<int>(ratio * 256 * 6);

    // find the distance to the start of the closest region
    int x = normalized % 256;

    int alpha = 255, grn = 0, red = 0, blu = 0;


    switch (normalized / 256)
    {
    case 0:
        red = 255;
        grn = x;
        blu = 0;
        break; // red
    case 1:
        red = 255 - x;
        grn = 255;
        blu = 0;
        break; // yellow
    case 2:
        red = 0;
        grn = 255;
        blu = x;
        break; // green
    case 3:
        red = 0;
        grn = 255 - x;
        blu = 255;
        break; // cyan
    case 4:
        red = x;
        grn = 0;
        blu = 255;
        break; // blue
    case 5:
        red = 255;
        grn = 0;
        blu = 255 - x;
        break; // magenta
    }

    return blu + (grn << 8) + (red << 16) + (alpha << 24);
}

/**
 * @brief Converts a ratio value to a carb::ColorRgba struct
 * @details
 * Generates a color from the rainbow color spectrum (ROYGBIV) based on the input ratio.
 * The ratio is mapped to six color regions, creating a smooth gradient transition between them.
 * Similar to distToColor() but returns a different format.
 *
 * @param[in] ratio A value between 0.0 and 1.0 representing position in the color gradient
 * @return carb::ColorRgba struct with values normalized to [0.0, 1.0] and alpha set to 1.0
 */
static inline carb::ColorRgba distToRgba(double ratio)
{
    // we want to normalize ratio so that it fits in to 6 regions
    // where each region is 256 units long
    int normalized = static_cast<int>(ratio * 256 * 6);

    // find the distance to the start of the closest region
    int x = normalized % 256;

    int grn = 0, red = 0, blu = 0;


    switch (normalized / 256)
    {
    case 0:
        red = 255;
        grn = x;
        blu = 0;
        break; // red
    case 1:
        red = 255 - x;
        grn = 255;
        blu = 0;
        break; // yellow
    case 2:
        red = 0;
        grn = 255;
        blu = x;
        break; // green
    case 3:
        red = 0;
        grn = 255 - x;
        blu = 255;
        break; // cyan
    case 4:
        red = x;
        grn = 0;
        blu = 255;
        break; // blue
    case 5:
        red = 255;
        grn = 0;
        blu = 255 - x;
        break; // magenta
    }
    return carb::ColorRgba({ red / 255.0f, grn / 255.0f, blu / 255.0f, 1.0f });
}

}
}
}
}
