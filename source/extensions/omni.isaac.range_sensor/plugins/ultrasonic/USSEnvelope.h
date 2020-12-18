#pragma once

#include <carb/Defines.h>
#include <carb/Types.h>

#include <algorithm>
#include <cstddef>
#include <numeric>
#include <utility>
#include <vector>


class USSEnvelope
{

public:
    // envelope is initialized to be all zeroes
    USSEnvelope(const int numBins, const float maxDist)
        : m_numBins(numBins),
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
            // convert from distance to echo
            echo.push_back(linearDepth[i] / C * 2.f);
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
            if ((sortedEcho[i] > rightBinBoundary) || (sortedEcho[i] < 0))
            {
                throw std::invalid_argument("Reflected point is outside of valid ray boundaries");
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
    // max dist is 7m * 2 (roundtrip)
    float m_maxDistRoundTrip; // = 7. * 2.;
    // speed of light is 343. m/s
    const float C = 343.f;
    float m_maxTimestamp;
    // const float MAX_TIMESTAMP = m_maxDistRoundTrip; // / C;
    float m_binWidth;
    std::vector<std::vector<float>> m_binnedEcho;
    std::vector<float> m_envelope;
    float m_intensityPerRay = 1.f;
};
