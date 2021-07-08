// Copyright (c) 2020-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#include <algorithm>

namespace omni
{
namespace isaac
{
namespace utils
{


class PIDController
{
public:
    PIDController(const float P, const float I, const float D)
    {
        mP = P;
        mI = I;
        mD = D;
        mErrorSum = 0;
        mError = 0;
    }

    float update(const float commanded, const float current, const float previous)
    {
        float error = commanded - current;
        float Poutput = mP * error;
        float Ioutput = mI * mErrorSum;
        float Doutput = -mD * (current - previous);


        if (mMaxI != 0)
        {
            Ioutput = std::max(-mMaxI, std::min(Ioutput, mMaxI));
        }

        mErrorSum += error;

        return 1.0f * commanded + Poutput + Ioutput + Doutput;
    }

    void setMaxI(const float maxI)
    {
        mMaxI = maxI;
    }


private:
    float mP = 0, mI = 0, mD = 0;
    float mErrorSum = 0;
    float mError = 0;
    float mMaxI = 0;
};
}
}
}
