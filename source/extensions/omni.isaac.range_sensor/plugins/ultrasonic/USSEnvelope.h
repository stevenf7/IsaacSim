// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

#include <algorithm>
#include <cstddef>
#include <numeric>
#include <sstream>
#include <utility>
#include <vector>

template <typename T>
bool almostEqual(T x, T y, int ulp = 1000)
{
    T prec = std::numeric_limits<T>::epsilon() * ulp;
    return std::abs(x - y) < prec || std::abs((x - y) / std::max(x, y)) < prec;
}

class USSEnvelope
{

public:
    // envelope is initialized to be all zeroes
    USSEnvelope(const int numBins, const float maxDist)
        : m_numBins(numBins),
          m_maxDist(maxDist),
          m_maxDistRoundTrip(maxDist * 2.f),
          m_maxTimestamp(m_maxDistRoundTrip / C),
          m_binWidth(m_maxTimestamp / m_numBins),
          m_binnedEcho(numBins, std::vector<float>()),
          m_envelope(numBins, 0){};
    // linearDepth is distance in meters
    bool updateEnvelope(const std::vector<float>& linearDepth)
    {
        std::vector<float> echo;
        for (size_t i = 0; i < linearDepth.size(); i++)
        {
            // do not include echoes of equal to maxDist
            if (!almostEqual(m_maxDist, linearDepth[i]))
            {
                // convert from distance to echo
                echo.push_back(linearDepth[i] * 2.f / C);
            }
        }
        for (size_t i = 0; i < m_binnedEcho.size(); i++)
        {
            m_binnedEcho[i].clear();
        }

        std::vector<float> sortedEcho(echo);
        sort(sortedEcho.begin(), sortedEcho.end());
        float rightBinBoundary = m_binWidth;
        size_t currentBin = 1;
        for (size_t i = 0; i < sortedEcho.size(); i++)
        {
            while ((sortedEcho[i] > rightBinBoundary) && currentBin < m_numBins)
            {
                rightBinBoundary += m_binWidth;
                currentBin++;
            }

            // use m_maxTimestamp not final rightBinBoundary as a guard because of accumulation of error on sum
            if ((sortedEcho[i] > m_maxTimestamp) || (sortedEcho[i] < 0))
            {
                std::stringstream ss;
                ss << "Reflected point is outside of ray boundaries: rightBinBoundary = " << rightBinBoundary
                   << ", sortedEcho[i] = " << sortedEcho[i] << ", i= " << i << ", currentBin = " << currentBin
                   << ", m_numBins = " << m_numBins << std::endl;
                throw std::invalid_argument(ss.str());
            }
            else
            {
                m_binnedEcho[currentBin - 1].push_back(m_intensityPerRay);
            }
        }
        for (size_t i = 0; i < m_binnedEcho.size(); i++)
        {
            m_envelope[i] = std::accumulate(m_binnedEcho[i].begin(), m_binnedEcho[i].end(), 0.0f);
        }
        return true;
    };

    std::vector<float>& getEnvelope()
    {
        return m_envelope;
    }

private:
    size_t m_numBins;
    float m_maxDist;
    // max dist is 7m * 2 (roundtrip)
    float m_maxDistRoundTrip;
    // speed of sound is 343. m/s
    const float C = 343.f;
    float m_maxTimestamp;
    float m_binWidth;
    std::vector<std::vector<float>> m_binnedEcho;
    std::vector<float> m_envelope;
    float m_intensityPerRay = 1.f;
};
