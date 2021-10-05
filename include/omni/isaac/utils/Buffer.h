#include <carb/cuda/CudaRuntime.h>

#include <cuda.h>
#include <vector>

namespace omni
{
namespace isaac
{
namespace buffer
{
enum class eMemoryType
{
    Host = 0,
    Device = 1,
};


class Buffer
{
public:
    virtual ~Buffer()
    {
    }
    virtual void resize(size_t size) = 0;
    virtual uint8_t* data() const = 0;
    virtual size_t size() const = 0;
    virtual eMemoryType type() const
    {
        return mMemoryType;
    }

protected:
    eMemoryType mMemoryType;
};

class DeviceBuffer : public Buffer
{
public:
    DeviceBuffer(size_t size = 0)
    {
        mMemoryType = eMemoryType::Device;
        resize(size);
    }
    virtual ~DeviceBuffer()
    {
        CUDA_CHECK(cudaFree(mBuffer));
        mBuffer = nullptr;
    }
    virtual void resize(size_t size)
    {
        if (size != mSize)
        {
            if (mBuffer)
            {
                CUDA_CHECK(cudaFree(mBuffer));
                mBuffer = nullptr;
            }
            if (size > 0)
            {
                CUDA_CHECK(cudaMalloc(&mBuffer, size));
            }
            mSize = size;
        }
    }
    virtual uint8_t* data() const
    {
        return mBuffer;
    }
    virtual size_t size() const
    {
        return mSize;
    }

private:
    uint8_t* mBuffer = nullptr;
    size_t mSize = 0;
};

class HostBuffer : public Buffer
{
public:
    HostBuffer(size_t size = 0)
    {
        mMemoryType = eMemoryType::Host;
        resize(size);
    }
    virtual void resize(size_t size)
    {
        mBuffer.resize(size);
    }
    virtual uint8_t* data() const
    {
        return (uint8_t*)mBuffer.data();
    }
    virtual size_t size() const
    {
        return mBuffer.size();
    }

    std::vector<uint8_t> mBuffer;
};
}
}
}
