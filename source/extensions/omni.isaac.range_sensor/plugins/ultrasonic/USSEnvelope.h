// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
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
    USSEnvelope(const size_t numBins, const float maxDist)
        : m_numBins(numBins),
          m_maxDist(maxDist),
          m_maxDistRoundTrip(maxDist * 2.f),
          m_maxTimestamp(m_maxDistRoundTrip / C),
          m_binWidth(m_maxTimestamp / m_numBins),
          m_binnedEcho(numBins, std::vector<float>()),
          m_envelope(numBins, 0.0f){};
    // linearDepth is distance in meters
    bool updateEnvelope(const std::vector<float>& totalRayLength, std::vector<float>& rayIntensity)
    {
        std::vector<float> echo;
        for (size_t i = 0; i < totalRayLength.size(); i++)
        {
            // only include echoes of equal to maxDist
            if (totalRayLength[i] < m_maxDistRoundTrip)
            {
                // convert from distance to echo
                echo.push_back(totalRayLength[i] / C);
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
                   << ", m_numBins = " << m_numBins << ", m_maxDist = " << m_maxDist << ", " << std::endl;
                throw std::invalid_argument(ss.str());
            }
            else
            {
                m_binnedEcho[currentBin - 1].push_back(rayIntensity[i]);
            }
        }
        for (size_t i = 0; i < m_binnedEcho.size(); i++)
        {
            m_envelope[i] = std::accumulate(m_binnedEcho[i].begin(), m_binnedEcho[i].end(), 0.0f);
        }
        return true;
    };

    bool isValid = true;

    std::vector<float>& getEnvelope()
    {
        return m_envelope;
    }

    size_t size() const
    {
        return m_envelope.size();
    }

    // Overload + operator to add two USSEnvelope objects.
    USSEnvelope operator+(const USSEnvelope& b)
    {
        USSEnvelope env(m_numBins, m_maxDist);
        if (b.size() == m_envelope.size())
        {
            for (size_t i = 0; i < m_envelope.size(); i++)
            {
                env.m_envelope[i] = m_envelope[i] + b.m_envelope[i];
            }
        }
        else
        {
            std::stringstream ss;
            ss << "Size of b (" << b.size() << ") must equal size of this object's envelope on addition ("
               << m_envelope.size() << ")." << std::endl;
            throw std::invalid_argument(ss.str());
        }
        return env;
    }

    USSEnvelope& operator=(const USSEnvelope& b)
    {
        USSEnvelope env(m_numBins, m_maxDist);
        if (b.size() == m_envelope.size())
        {
            for (size_t i = 0; i < m_envelope.size(); i++)
            {
                m_envelope[i] = b.m_envelope[i];
            }
        }
        else
        {
            std::stringstream ss;
            ss << "Size of b (" << b.size() << ") must equal size of this object's envelope when assigning ("
               << m_envelope.size() << ")." << std::endl;
            throw std::invalid_argument(ss.str());
        }
        return *this;
    }

    friend std::ostream& operator<<(std::ostream& stream, const USSEnvelope& env)
    {
        for (size_t i = 0; i < env.m_envelope.size(); i++)
        {
            stream << env.m_envelope[i] << " ";
        }
        stream << std::endl;
        return stream;
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
};
