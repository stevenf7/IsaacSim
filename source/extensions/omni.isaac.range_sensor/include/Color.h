// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

namespace omni
{
namespace isaac
{
namespace utils
{
namespace color
{

// taken from https://stackoverflow.com/questions/40629345/fill-array-dynamicly-with-gradient-color-c
static inline uint32_t distToColor(double ratio, bool bigEndian)
{
    // we want to normalize ratio so that it fits in to 6 regions
    // where each region is 256 units long
    int normalized = int(ratio * 256 * 6);

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

static inline carb::ColorRgba distToRgba(double ratio)
{
    // we want to normalize ratio so that it fits in to 6 regions
    // where each region is 256 units long
    int normalized = int(ratio * 256 * 6);

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
