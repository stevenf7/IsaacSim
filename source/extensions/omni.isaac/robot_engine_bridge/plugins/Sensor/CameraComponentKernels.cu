// Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

__global__ void rgbaToRgbKernel(unsigned char *dest, const unsigned char *src, int width, int height, int srcStride)
{

    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= width*height)
        return;

	int row = idx / width;
	int col = idx % width;

	dest[idx*3] = src[row*srcStride + col*4];
	dest[idx*3+1] = src[row*srcStride + col*4+1];
	dest[idx*3+2] = src[row*srcStride + col*4+2];

};

extern "C" void rgbaToRgb(unsigned char *dest, const unsigned char *src, int width, int height, int srcStride)
{

	const int num = width*height;
    const int nt = 256;
    const int nb = (num + nt - 1) / nt;

    rgbaToRgbKernel<<<nb, nt>>>(dest, src, width, height, srcStride);

}
