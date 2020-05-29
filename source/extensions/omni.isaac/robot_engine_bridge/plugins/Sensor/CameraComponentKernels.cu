// Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <cuda.h>


__global__ void rgbaToRgbKernel(uint8_t *dest, const uint8_t *src, int width, int height, int srcStride)
{

    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= width*height)
        return;

	int row = idx / width;
	int col = idx % width;

	dest[idx*3] = src[row*srcStride + col*4];
	dest[idx*3+1] = src[row*srcStride + col*4+1];
	dest[idx*3+2] = src[row*srcStride + col*4+2];

}

extern "C" void rgbaToRgb(uint8_t *dest, const uint8_t *src, int width, int height, int srcStride)
{

	const int num = width*height;
    const int nt = 256;
    const int nb = (num + nt - 1) / nt;

    rgbaToRgbKernel<<<nb, nt>>>(dest, src, width, height, srcStride);

}



__global__ void uint32ToUint16Kernel(uint16_t *dest, const uint32_t *src, int width, int height, int srcStride)
{

    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= width*height)
        return;

	int row = idx / width;
	int col = idx % width;

	uint32_t *srcRow = (uint32_t*)((uint8_t*)src + row * srcStride);

	dest[idx] = srcRow[col];

}

extern "C" void uint32ToUint16(uint16_t *dest, const uint32_t *src, int width, int height, int srcStride)
{

	const int num = width*height;
    const int nt = 256;
    const int nb = (num + nt - 1) / nt;

    uint32ToUint16Kernel<<<nb, nt>>>(dest, src, width, height, srcStride);

}


// TODO : Refactor with the UINT16 version
__global__ void uint32ToUint8Kernel(uint8_t *dest, const uint32_t *src, int width, int height, int srcStride)
{

    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= width*height)
        return;

	int row = idx / width;
	int col = idx % width;

	uint32_t *srcRow = (uint32_t*)((uint8_t*)src + row * srcStride);

	dest[idx] = srcRow[col];

}

extern "C" void uint32ToUint8(uint8_t *dest, const uint32_t *src, int width, int height, int srcStride)
{

	const int num = width*height;
    const int nt = 256;
    const int nb = (num + nt - 1) / nt;

    uint32ToUint8Kernel<<<nb, nt>>>(dest, src, width, height, srcStride);

}

