// Copyright (c) 2018-2020, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once
#include <iostream>
#include <sstream>
#include <vector>

class UltrasonicEmitter
{

public:
    UltrasonicEmitter()
        : mDeltaTSuccessivePulses(std::vector<double>(NUM_EMITTERS, PULSE_GAP_DELTA)),
          mPulseDuration(std::vector<double>(NUM_EMITTERS, PULSE_DURATION)),
          mTimeSinceLastPulse(std::vector<double>(NUM_EMITTERS, 0.)),
          mShouldEmit(std::vector<bool>(NUM_EMITTERS, false)),
          mTimeSincePulseStarted(std::vector<double>(NUM_EMITTERS, 0.)),
          mDelay(std::vector<double>(NUM_EMITTERS, 0.))
    {
        ;
    }

    void update(double deltaT)
    {
        for (size_t i = 0; i < NUM_EMITTERS; i++)
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
            std::stringstream errMsg;
            errMsg << "Queried an emitter that does not exist. " << index << " >= " << NUM_EMITTERS;
            throw std::out_of_range(errMsg.str());
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
    const double PULSE_DURATION = 0.5; // 2500.;
    const double PULSE_GAP_DELTA = 1.0; // 10000.;
    static const size_t NUM_EMITTERS = 8;
    // all times are in milliseconds
    const std::vector<double> mDeltaTSuccessivePulses;
    const std::vector<double> mPulseDuration;
    std::vector<double> mTimeSinceLastPulse;
    std::vector<bool> mShouldEmit;
    std::vector<double> mTimeSincePulseStarted;
    std::vector<double> mDelay;
};
