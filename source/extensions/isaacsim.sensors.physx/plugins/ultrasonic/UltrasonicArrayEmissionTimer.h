// Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once
#include "USSEnvelope.h"

#include <iostream>
#include <sstream>
#include <vector>

class UltrasonicArrayEmissionTimer
{

public:
    UltrasonicArrayEmissionTimer(const size_t numEmitters, const double pulse_gap_delta, const double pulse_duration)
        : mDeltaTSuccessivePulses(std::vector<double>(numEmitters, pulse_gap_delta)),
          mPulseDuration(std::vector<double>(numEmitters, pulse_duration)),
          mTimeSinceLastPulse(std::vector<double>(numEmitters, 0.)),
          mShouldEmit(std::vector<bool>(numEmitters, false)),
          mTimeSincePulseStarted(std::vector<double>(numEmitters, 0.)),
          mDelay(std::vector<double>(numEmitters, 0.)),
          mNumEmitters(numEmitters)
    {
        ;
    }

    void update(double deltaT)
    {
        for (size_t i = 0; i < mNumEmitters; i++)
        {
            mTimeSinceLastPulse[i] += deltaT;
            // std::cout << "mTimeSinceLastPulse[ " << i << "] = " << mTimeSinceLastPulse[i] << std::endl;
            // std::cout << "mDeltaTSuccessivePulses[ " << i << "] = " << mDeltaTSuccessivePulses[i] << std::endl;
            if (mTimeSinceLastPulse[i] >= mDeltaTSuccessivePulses[i])
            {
                mTimeSinceLastPulse[i] = 0.;
                mShouldEmit[i] = true;
                mTimeSincePulseStarted[i] = 0.;
            }
            else if (mShouldEmit[i] && ((mTimeSincePulseStarted[i] + deltaT) >= mPulseDuration[i]))
            {
                mShouldEmit[i] = false;
                mTimeSincePulseStarted[i] = 0.; // reset
            }
            else if (mShouldEmit[i] && ((mTimeSincePulseStarted[i] + deltaT) < mPulseDuration[i]))
            {
                mTimeSincePulseStarted[i] += deltaT; // now emitting, update the duration
            }
            else
            {
                ; // should not be emitting now, mShouldEmit[i] = false
            }
        }
    }
    bool shouldEmit(size_t index)
    {
        if (index < mShouldEmit.size())
        {
            return mShouldEmit[index];
        }
        else
        {
            printf("Queried a USS emitter that does not exist. %zu >= %zu\n", index, mNumEmitters);
            return false;
        }
    }
    void setEmitterDelay(size_t index, double delay)
    {
        // std::cout << "delay = " << delay << std::endl;
        // std::cout << "mTimeSinceLastPulse[index] before: " << mTimeSinceLastPulse[index];
        mTimeSinceLastPulse[index] -= delay;
        // std::cout << ", after: " << mTimeSinceLastPulse[index] << std::endl;
    }


private:
    // all times are in milliseconds
    const std::vector<double> mDeltaTSuccessivePulses;
    const std::vector<double> mPulseDuration;
    std::vector<double> mTimeSinceLastPulse;
    std::vector<bool> mShouldEmit;
    std::vector<double> mTimeSincePulseStarted;
    std::vector<double> mDelay;
    size_t mNumEmitters = 0;
};
