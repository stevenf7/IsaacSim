// Copyright (c) 2023-2025, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
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
//
// SPDX-License-Identifier: Apache-2.0

#ifndef IPC_BUFFER_MANAGER_HPP_
#define IPC_BUFFER_MANAGER_HPP_

#include <sys/syscall.h>
#include <sys/types.h>

#include <cuda.h>
#include <cuda_runtime_api.h>
#include <stdio.h>
#include <unistd.h>
#include <vector>

/**
 * @class IPCBufferManager
 * @brief Manages CUDA device memory buffers for inter-process communication (IPC).
 * @details
 * This class creates and manages a pool of CUDA device memory buffers that can be
 * shared between processes using POSIX file descriptors. It handles the allocation,
 * mapping, and access control for these buffers, as well as cycling through them
 * for use in communication scenarios.
 */
class IPCBufferManager
{
public:
    IPCBufferManager() = default;

    /**
     * @brief Constructor that creates device memory buffers and exports them to file descriptors.
     * @details
     * Allocates a specified number of CUDA device memory buffers and exports them as
     * POSIX file descriptors for inter-process communication. The buffers are set up
     * with read/write access permissions.
     *
     * @param[in] size Number of buffers to create in the pool.
     * @param[in] buffer_step Size of each buffer in bytes.
     */
    IPCBufferManager(size_t size, size_t buffer_step)
    {
        buffer_size_ = size;
        buffer_step_ = buffer_step;

        CUmemAllocationProp prop = {};
        prop.type = CU_MEM_ALLOCATION_TYPE_PINNED;
        prop.location.type = CU_MEM_LOCATION_TYPE_DEVICE;
        prop.location.id = 0;
        prop.requestedHandleTypes = CU_MEM_HANDLE_TYPE_POSIX_FILE_DESCRIPTOR;
        size_t granularity = 0;
        auto cuda_err = cuMemGetAllocationGranularity(&granularity, &prop, CU_MEM_ALLOC_GRANULARITY_MINIMUM);
        if (CUDA_SUCCESS != cuda_err)
        {
            const char* error_str = NULL;
            cuGetErrorString(cuda_err, &error_str);
            fprintf(stderr, "[Error] IPCBufferManager: Failed to call cuMemGetAllocationGranularity %s\n", error_str);
        }
        alloc_size_ = buffer_step - (buffer_step % granularity) + granularity;

        for (size_t i = 0; i < buffer_size_; i++)
        {
            CUmemGenericAllocationHandle generic_allocation_handle;
            auto cuda_err = cuMemCreate(&generic_allocation_handle, alloc_size_, &prop, 0);
            if (CUDA_SUCCESS != cuda_err)
            {
                const char* error_str = NULL;
                cuGetErrorString(cuda_err, &error_str);
                fprintf(stderr, "[Error] IPCBufferManager: Failed to call cuMemCreate %s\n", error_str);
            }

            int fd = -1;
            cuda_err = cuMemExportToShareableHandle(
                reinterpret_cast<void*>(&fd), generic_allocation_handle, CU_MEM_HANDLE_TYPE_POSIX_FILE_DESCRIPTOR, 0);
            if (CUDA_SUCCESS != cuda_err)
            {
                const char* error_str = NULL;
                cuGetErrorString(cuda_err, &error_str);
                fprintf(stderr, "[Error] IPCBufferManager: Failed to cuMemExportToShareableHandle %s\n", error_str);
            }

            CUdeviceptr d_ptr = 0ULL;
            cuda_err = cuMemAddressReserve(&d_ptr, alloc_size_, 0, 0, 0);
            if (CUDA_SUCCESS != cuda_err)
            {
                const char* error_str = NULL;
                cuGetErrorString(cuda_err, &error_str);
                fprintf(stderr, "[Error] IPCBufferManager: Failed to call cuMemAddressReserve %s\n", error_str);
            }

            cuda_err = cuMemMap(d_ptr, alloc_size_, 0, generic_allocation_handle, 0);
            if (CUDA_SUCCESS != cuda_err)
            {
                const char* error_str = NULL;
                cuGetErrorString(cuda_err, &error_str);
                fprintf(stderr, "[Error] IPCBufferManager: Failed to call cuMemMap %s\n", error_str);
            }

            CUmemAccessDesc accessDesc = {};
            accessDesc.location.type = CU_MEM_LOCATION_TYPE_DEVICE;
            accessDesc.location.id = 0;
            accessDesc.flags = CU_MEM_ACCESS_FLAGS_PROT_READWRITE;
            cuda_err = cuMemSetAccess(d_ptr, alloc_size_, &accessDesc, 1);
            if (CUDA_SUCCESS != cuda_err)
            {
                const char* error_str = NULL;
                cuGetErrorString(cuda_err, &error_str);
                fprintf(stderr, "[Error] IPCBufferManager: Failed to call cuMemSetAccess %s\n", error_str);
            }

            buffer_ptrs_.push_back(d_ptr);
            shareable_handles_.push_back({ getpid(), fd });
            generic_handles.push_back(generic_allocation_handle);
        }
    }

    // Destructor, free the alloacted device memory pool
    ~IPCBufferManager()
    {
        for (size_t i = 0; i < buffer_size_; i++)
        {
            cuMemRelease(generic_handles[i]);
            cuMemUnmap(buffer_ptrs_[i], alloc_size_);
        }
    }

    /**
     * @brief Advances to the next available device memory buffer in the pool.
     * @details
     * Increments the current buffer index, wrapping around to the beginning
     * when the end of the buffer pool is reached. This implements a circular
     * buffer pattern for cycling through available memory blocks.
     */
    void next()
    {
        current_handle_index_ += 1;
        if (current_handle_index_ == buffer_size_)
        {
            current_handle_index_ = 0;
        }
    }

    /**
     * @brief Retrieves the device pointer to the current memory buffer.
     * @details
     * Returns the CUDA device pointer for the currently selected buffer
     * in the pool, which can be used for CUDA operations.
     *
     * @return CUdeviceptr Device pointer to the current buffer.
     */
    CUdeviceptr get_cur_buffer_ptr()
    {
        return buffer_ptrs_[current_handle_index_];
    }

    /**
     * @brief Retrieves the IPC handle for the current memory buffer.
     * @details
     * Returns a reference to the vector containing the process ID and file descriptor
     * for the currently selected buffer, which can be used for inter-process communication.
     *
     * @return std::vector<int>& Reference to the vector containing the process ID and file descriptor.
     */
    std::vector<int>& get_cur_ipc_mem_handle()
    {
        return shareable_handles_[current_handle_index_];
    }

private:
    size_t buffer_size_;
    size_t buffer_step_;
    size_t current_handle_index_ = 0;
    size_t alloc_size_;

    std::vector<std::vector<int>> shareable_handles_;
    std::vector<CUmemGenericAllocationHandle> generic_handles;
    std::vector<CUdeviceptr> buffer_ptrs_;
};

#endif // IPC_BUFFER_MANAGER_HPP_
