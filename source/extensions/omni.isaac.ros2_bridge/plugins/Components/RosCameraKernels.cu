// Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
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

typedef struct __align__(16) {
    float x;
    float y;
    float z;
} PointXYZ;

__global__ void depthToPCLKernel(PointXYZ *dest, const float *src, int width, int height, float fx, float fy, float cx, float cy)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;

    if (idx >= width*height)
        return;
    int row = idx / (width);
	int col = idx % (width);

    float z = src[idx];
    
    PointXYZ point;

    if (z != 0){
        point.x = (float)(z * (col - cx) / fx);
        point.y = (float)(z * (row - cy) / fy);
        point.z = z;
    }

    else{
        point.x = nanf("1");
        point.y = nanf("2");
        point.z = nanf("3");
    }
    dest[idx] = point;

}

extern "C" void depthToPCL(PointXYZ *dest, const float *src, int width, int height, float fx, float fy, float cx, float cy)
{

	const int num = width*height;
    const int nt = 256;
    const int nb = (num + nt - 1) / nt;

    depthToPCLKernel<<<nb, nt>>>(dest, src, width, height, fx, fy, cx, cy);

}
