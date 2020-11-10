#pragma once

#include <chrono>
#include <iostream>
#include <string>

namespace omni
{
namespace isaac
{
namespace utils
{
class ScopedTimer
{
public:
    ScopedTimer(const std::string& message)
    {
        mMessage = message;
        mStart = std::chrono::steady_clock::now();
    }

    ~ScopedTimer()
    {
        mStop = std::chrono::steady_clock::now();
        std::chrono::duration<double, std::milli> diff = mStop - mStart;
        std::cout << mMessage << " : " << diff.count() << std::endl;
    }

private:
    std::chrono::time_point<std::chrono::steady_clock> mStart;
    std::chrono::time_point<std::chrono::steady_clock> mStop;
    std::string mMessage;
};

}
}
}
