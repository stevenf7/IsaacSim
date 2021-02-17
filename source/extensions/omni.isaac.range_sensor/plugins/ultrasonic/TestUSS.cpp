// Copyright (c) 2018-2021, NVIDIA CORPORATION. All rights reserved.
//
// NVIDIA CORPORATION and its licensors retain all intellectual property
// and proprietary rights in and to this software, related documentation
// and any modifications thereto. Any use, reproduction, disclosure or
// distribution of this software and related documentation without an express
// license agreement from NVIDIA CORPORATION is strictly prohibited.
//

#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "USSEnvelope.h"
#include "UltrasonicArrayEmissionTimer.h"
#include "UltrasonicReceiver.h"
#include "UltrasonicReceiverArray.h"
//#include "FiringGroupUtils.h"
//#include <pxr/base/gf/vec2i.h>
//#include <pxr/usd/usd/inherits.h>
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
        distances.push_back(6.99f * 2.f);
        distances.push_back(0.1f * 2.f);

        std::vector<float> intensities;
        intensities.push_back(1.f);
        intensities.push_back(1.f);
        bool res = ussEnv.updateEnvelope(distances, intensities);
        CHECK(res == true);

        std::vector<float> envelope2 = ussEnv.getEnvelope();
        CHECK(envelope2.back() == doctest::Approx(1.f));
        CHECK(envelope2.at(3) == doctest::Approx(0.f));
        CHECK(envelope2.front() == doctest::Approx(1.f));
    }

    SUBCASE("Check Emitter")
    {
        UltrasonicArrayEmissionTimer emitter(12, 1.0, 0.5);
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
        UltrasonicArrayEmissionTimer emitter(12, 1.0, 0.5);
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

        std::vector<float> totalDistances;
        std::vector<float> intensities;
        std::cout << "distances.size() = " << distances.size() << std::endl;
        for (size_t i = 0; i < distances.size(); i++)
        {
            totalDistances.push_back(distances[i] * 2.f);
            intensities.push_back(1.f);
        }
        std::cout << "updating envelope" << std::endl;
        ussEnv.updateEnvelope(totalDistances, intensities);
        std::cout << "updated envelope" << std::endl;
        std::vector<float>& envelope = ussEnv.getEnvelope();

        // equality with an int hacks off after the decimal?
        CHECK(envelope[3] == 6);
        CHECK(envelope[0] == 0);
        CHECK(envelope[223] == 0);

        // check the state is the same after a second update
        ussEnv.updateEnvelope(totalDistances, intensities);
        CHECK(envelope[3] == 6);
    }
    SUBCASE("Check indirect modelling")
    {
        ::physx::PxVec3 emitterCenter({ 1.f, 1.f, 0.f });
        ::physx::PxVec3 receiverCenter1({ 4.f, 1.f, 0.f });

        ::physx::PxVec3 surfacePoint({ 2.f, 5.f, 0.f });
        std::vector<::physx::PxVec3> surfacePoints;
        surfacePoints.push_back(surfacePoint);

        UltrasonicReceiver receiver1(receiverCenter1);
        std::vector<float> intens1 = receiver1.getIndirectIntensities(emitterCenter, surfacePoints);
        float cosTheta = 14.f;
        float mag = 18.439088914585774f;
        CHECK(intens1[0] == doctest::Approx(cosTheta / mag));

        ::physx::PxVec3 receiverCenter2({ 8.f, 1.f, 0.f });
        UltrasonicReceiver receiver2(receiverCenter2);
        std::vector<float> intens2 = receiver2.getIndirectIntensities(emitterCenter, surfacePoints);
        std::cout << "intens2[0] = " << intens2[0] << std::endl;
        // larger angle, smaller response
        CHECK(intens1[0] > intens2[0]);
    }

    SUBCASE("Check envelope addition throws")
    {
        int numBins = 10;
        // maxDist is in meters
        float maxDist = 7.;
        USSEnvelope ussEnv1(numBins, maxDist);
        USSEnvelope ussEnv2(numBins + 1, maxDist);

        CHECK_THROWS(ussEnv1 + ussEnv2);
    }

    SUBCASE("Check envelope addition")
    {
        int numBins = 10;
        // maxDist is in meters
        float maxDist = 7.;
        USSEnvelope ussEnv1(numBins, maxDist);
        std::vector<float> totalDist1(2, 2.f);
        std::vector<float> intens1(2, 3.f);
        ussEnv1.updateEnvelope(totalDist1, intens1);

        USSEnvelope ussEnv2 = ussEnv1 + ussEnv1;
        CHECK(ussEnv2.getEnvelope()[0] == doctest::Approx(0.f));
        CHECK(ussEnv2.getEnvelope()[1] == doctest::Approx(12.f));
    }

    SUBCASE("Check indirect path lengths")
    {
        ::physx::PxVec3 emitterCenter({ 1.f, 1.f, 0.f });
        ::physx::PxVec3 receiverCenter({ 5.f, 1.f, 0.f });

        ::physx::PxVec3 surfacePoint({ 3.f, 5.f, 0.f });
        UltrasonicReceiver receiver(receiverCenter);
        std::vector<::physx::PxVec3> surfacePoints;
        surfacePoints.push_back(surfacePoint);
        std::vector<float> len = receiver.getTotalPathLength(emitterCenter, surfacePoints);
        // res is 2 * sqrt(20)
        CHECK(len[0] == doctest::Approx(8.94427190999916f));
    }

    SUBCASE("Check indirect path lengths")
    {
        ::physx::PxVec3 emitterCenter({ 1.f, 1.f, 0.f });
        ::physx::PxVec3 receiverCenter({ 5.f, 1.f, 0.f });

        ::physx::PxVec3 surfacePoint({ 3.f, 5.f, 0.f });
        UltrasonicReceiver receiver(receiverCenter);
        std::vector<::physx::PxVec3> surfacePoints;
        surfacePoints.push_back(surfacePoint);
        std::vector<float> len = receiver.getTotalPathLength(emitterCenter, surfacePoints);
        // res is 2 * sqrt(20)
        CHECK(len[0] == doctest::Approx(8.94427190999916f));
    }

    SUBCASE("Check ultrasonic receiver array")
    {
        std::vector<::physx::PxVec3> emitterCenters{ { 1.f, 1.f, 0.f }, { 5.f, 1.f, 0.f }, { 8.f, 1.f, 0.f } };

        std::vector<std::vector<::physx::PxVec3>> worldPoints{
            { { 1.f, 5.f, 0.f }, { 5.f, 5.f, 0.f }, { 8.f, 5.f, 0.f } }, {}, {}
        };

        std::vector<::physx::PxVec3> receiverCenters{ { 1.f, 1.f, 0.f }, { 5.f, 1.f, 0.f }, { 8.f, 1.f, 0.f } };

        std::vector<std::vector<uint8_t>> adjacency{ { 0, 1 }, // adjacency for receiver zero
                                                     { 0, 1, 2 }, // adjacency for receiver one
                                                     { 1, 2 } }; // adjacency for receiver two

        std::vector<bool> isFiring{ true, false, false };
        std::vector<bool> isReceiving{ false, true, true };

        UltrasonicReceiverArray receiverArr;
        uint8_t receiverIndex = 1; // one is receiving
        uint8_t emitterIndex = 0; // zero
        CHECK(receiverArr.shouldProduceEnvelope(adjacency, isFiring, isReceiving, receiverIndex, emitterIndex));

        emitterIndex = 0; // zero is emitting, but
        receiverIndex = 0; // zero is not receiving
        CHECK(!receiverArr.shouldProduceEnvelope(adjacency, isFiring, isReceiving, receiverIndex, emitterIndex));

        emitterIndex = 0; // zero is emitting, but
        receiverIndex = 2; // two is receiving but isn't adjacent
        CHECK(!receiverArr.shouldProduceEnvelope(adjacency, isFiring, isReceiving, receiverIndex, emitterIndex));
    }
    SUBCASE("Check single emitter/receiver")
    {
        std::vector<::physx::PxVec3> emitterCenters{ { 1.f, 1.f, 0.f } };

        std::vector<std::vector<::physx::PxVec3>> worldPoints{ { { 1.f, 2.f, 0.f } } };

        std::vector<::physx::PxVec3> receiverCenters{ { 1.f, 1.f, 0.f } };

        std::vector<std::vector<uint8_t>> adjacency{ { 0 } }; // adjacent to itself

        std::vector<bool> isFiring{ true };
        std::vector<bool> isReceiving{ true };
        UltrasonicReceiverArray receiverArr;
        auto distances = receiverArr.getAdjacentDistances(
            adjacency, isFiring, isReceiving, emitterCenters, receiverCenters, worldPoints);
        uint8_t emitterIndex = 0;
        uint8_t receiverIndex = 0;
        CHECK(doctest::Approx(distances[receiverIndex][emitterIndex][0]) == 2.f);
    }

    SUBCASE("Check multi emitter/receiver")
    {
        std::vector<::physx::PxVec3> emitterCenters{ { 1.f, 1.f, 0.f }, { 2.f, 1.f, 0.f }, { 3.f, 1.f, 0.f } };

        std::vector<std::vector<::physx::PxVec3>> worldPoints{ { { 2.f, 2.f, 0.f }, { 3.f, 3.f, 0.f } }, {}, {} };

        std::vector<::physx::PxVec3> receiverCenters{ { 1.f, 1.f, 0.f }, { 2.f, 1.f, 0.f }, { 3.f, 1.f, 0.f } };

        std::vector<std::vector<uint8_t>> adjacency{ { 0, 1 }, // adjacency for receiver zero
                                                     { 0, 1, 2 }, // adjacency for receiver one
                                                     { 1, 2 } }; // adjacency for receiver two

        std::vector<bool> isFiring{ true, false, false };
        std::vector<bool> isReceiving{ false, true, true };
        UltrasonicReceiverArray receiverArr;
        auto distances = receiverArr.getAdjacentDistances(
            adjacency, isFiring, isReceiving, emitterCenters, receiverCenters, worldPoints);
        for (size_t i = 0; i < distances[1].size(); i++)
        {
            CHECK(distances[0][i].size() == 0);
            CHECK(distances[2][i].size() == 0);
        }
        CHECK(doctest::Approx(distances[1][0][0]) == 2.4142135f);
        CHECK(doctest::Approx(distances[1][0][1]) == 5.06449510224598f);

        int numBins = 10;
        float maxDist = 3.0; // not roundtrip
        auto envelopeList = receiverArr.getCombinedEnvelopeList(
            numBins, maxDist, adjacency, isFiring, isReceiving, emitterCenters, receiverCenters, worldPoints);
        int receiverIndex = 1;
        CHECK(envelopeList[receiverIndex].getEnvelope()[8] == 1);
        CHECK(envelopeList[receiverIndex].getEnvelope()[4] == 1);
        for (size_t i = 0; i < envelopeList.size(); i++)
        {
            std::cout << envelopeList[i] << std::endl;
        }
    }
}
