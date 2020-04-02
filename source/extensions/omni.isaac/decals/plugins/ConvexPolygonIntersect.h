// Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <stddef.h>
#include <stdint.h>

namespace omni
{

struct IVec2
{
    int32_t x, y;
};

/**
    Intersects polygons given by verts1 and verts2, assumed to be
    given in ccw winding order and of size count1 and count2,
    respectively.  The result is written to the user-supplied
    array 'result', which must have count1 + count2 elements.
    The number of vertices written to 'result' is returned by
    the function.
*/
size_t intersectIntPolygons(IVec2* result, const IVec2* verts1, size_t count1, const IVec2* verts2, size_t count2);

} // namespace omni
