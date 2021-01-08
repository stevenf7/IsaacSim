// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto.  Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "USSEnvelope.h"
#include "UltrasonicArrayEmissionTimer.h"
#include "doctest/doctest.h"

#include <string>

TEST_CASE("main")
{
    SUBCASE("Check Envelope")
    {
        int numBins = 10;
        // maxDist is in meters
        float maxDist = 7.;
        USSEnvelope ussEnv(numBins, maxDist);
        std::vector<float> envelope1 = ussEnv.getEnvelope();
        CHECK(ussEnv.getEnvelope().size() == 10);

        std::vector<float> distances;
        distances.push_back(6.99f);
        distances.push_back(0.1f);
        bool res = ussEnv.updateEnvelope(distances);
        CHECK(res == true);

        std::vector<float> envelope2 = ussEnv.getEnvelope();
        CHECK(envelope2.back() == doctest::Approx(1.f));
        CHECK(envelope2.at(3) == doctest::Approx(0.f));
        CHECK(envelope2.front() == doctest::Approx(1.f));

        distances.push_back(7.4f);
        CHECK_THROWS(ussEnv.updateEnvelope(distances));
    }

    SUBCASE("Check Emitter")
    {
        UltrasonicArrayEmissionTimer emitter;
        size_t emitterIdx = 3;
        double deltaT = 0.4;
        emitter.update(deltaT);
        CHECK(emitter.shouldEmit(emitterIdx) == false);

        double deltaT2 = 0.6;
        emitter.update(deltaT2);
        CHECK(emitter.shouldEmit(emitterIdx) == true);

        double deltaT3 = 0.5;
        emitter.update(deltaT3);
        CHECK(emitter.shouldEmit(emitterIdx) == false);
    }

    SUBCASE("Check Emitter Delay")
    {
        UltrasonicArrayEmissionTimer emitter;
        size_t emitterIdx0 = 0;
        size_t emitterIdx3 = 3;
        double delay = 2.0;
        emitter.setEmitterDelay(emitterIdx0, delay);
        double deltaT = 1.0;
        emitter.update(deltaT);
        CHECK(emitter.shouldEmit(emitterIdx0) == false);
        CHECK(emitter.shouldEmit(emitterIdx3) == true);
    }

    SUBCASE("Check Real data")
    {
        int numBins = 224;
        float maxDist = 100.;
        USSEnvelope ussEnv(numBins, maxDist);
        std::vector<float> distances{ 100.f,      100.f,      100.f,      100.f,      100.f,      100.f,
                                      100.f,      100.f,      100.f,      100.f,      100.f,      100.f,
                                      100.f,      100.f,      100.f,      100.f,      100.f,      100.f,
                                      2.8684325f, 2.8684325f, 2.8684325f, 2.8684325f, 2.8684325f, 2.8684325f,
                                      14.324773f, 14.324775f, 14.32477f,  14.324772f, 14.324768f, 14.324773f,
                                      1.5981145f, 1.5981146f, 1.5981146f, 1.5981146f, 1.5981147f, 1.5981146f };
        ussEnv.updateEnvelope(distances);
        std::vector<float>& envelope = ussEnv.getEnvelope();

        // equality with an int hacks off after the decimal?
        CHECK(envelope[3] == 6);
        CHECK(envelope[0] == 0);
        CHECK(envelope[223] == 0);

        // check the state is the same after a second update
        ussEnv.updateEnvelope(distances);
        CHECK(envelope[3] == 6);
    }
}
