# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import unittest
import omni.kit

import omni.isaac.gym.tests.utils as utils

CHECK_ITERATIONS = 100
NUM_RUNS = 3


def _check_determinism(task, sim_device, pipeline, dr=False):
    prev_reward = -1
    for i in range(NUM_RUNS):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, task, "cpu", "cpu", CHECK_ITERATIONS, dr)
        log_data = utils._retrieve_logs(experiment_name)
        reward = log_data["rewards/iter"][-1][1]
        if i > 0:
            if reward != prev_reward:
                return False
        else:
            prev_reward = reward

    return True


class TestOmniIsaacGymEnvsDeterminismCC(omni.kit.test.AsyncTestCase):
    @classmethod
    def setUpClass(self):
        # set up OIGE repo
        utils._setup_OIGE()

    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_cartpole_determinism_cc(self):
        self.assertTrue(_check_determinism("Cartpole", "cpu", "cpu"))

    async def test_ant_determinism_cc(self):
        self.assertTrue(_check_determinism("Ant", "cpu", "cpu"))

    async def test_humanoid_determinism_cc(self):
        self.assertTrue(_check_determinism("Humanoid", "cpu", "cpu"))

    async def test_anymal_determinism_cc(self):
        self.assertTrue(_check_determinism("Anymal", "cpu", "cpu"))

    async def test_anymal_terrain_determinism_cc(self):
        self.assertTrue(_check_determinism("AnymalTerrain", "cpu", "cpu"))

    async def test_ball_balance_determinism_cc(self):
        self.assertTrue(_check_determinism("BallBalance", "cpu", "cpu"))

    async def test_franka_cabinet_determinism_cc(self):
        self.assertTrue(_check_determinism("FrankaCabinet", "cpu", "cpu"))

    async def test_ingenuity_determinism_cc(self):
        self.assertTrue(_check_determinism("Ingenuity", "cpu", "cpu"))

    async def test_quadcopter_determinism_cc(self):
        self.assertTrue(_check_determinism("Quadcopter", "cpu", "cpu"))

    async def test_crazyflie_determinism_cc(self):
        self.assertTrue(_check_determinism("Crazyflie", "cpu", "cpu"))

    async def test_allegro_hand_determinism_cc(self):
        self.assertTrue(_check_determinism("AllegroHand", "cpu", "cpu"))

    async def test_shadow_hand_determinism_cc(self):
        self.assertTrue(_check_determinism("ShadowHand", "cpu", "cpu"))

    async def test_shadow_hand_dr_determinism_cc(self):
        self.assertTrue(_check_determinism("ShadowHand", "cpu", "cpu", True))

    async def test_shadow_hand_openai_ff_determinism_cc(self):
        self.assertTrue(_check_determinism("ShadowHandOpenAI_FF", "cpu", "cpu"))

    async def test_shadow_hand_openai_lstm_determinism_cc(self):
        self.assertTrue(_check_determinism("ShadowHandOpenAI_LSTM", "cpu", "cpu"))


class TestOmniIsaacGymEnvsDeterminismGC(omni.kit.test.AsyncTestCase):
    @classmethod
    def setUpClass(self):
        # set up OIGE repo
        utils._setup_OIGE()

    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_cartpole_determinism_gc(self):
        self.assertTrue(_check_determinism("Cartpole", "gpu", "cpu"))

    async def test_ant_determinism_gc(self):
        self.assertTrue(_check_determinism("Ant", "gpu", "cpu"))

    async def test_humanoid_determinism_gc(self):
        self.assertTrue(_check_determinism("Humanoid", "gpu", "cpu"))

    async def test_anymal_determinism_gc(self):
        self.assertTrue(_check_determinism("Anymal", "gpu", "cpu"))

    # async def test_anymal_terrain_determinism_gc(self):
    #     self.assertTrue(_check_determinism("AnymalTerrain", "gpu", "cpu"))

    async def test_ball_balance_determinism_gc(self):
        self.assertTrue(_check_determinism("BallBalance", "gpu", "cpu"))

    async def test_franka_cabinet_determinism_gc(self):
        self.assertTrue(_check_determinism("FrankaCabinet", "gpu", "cpu"))

    async def test_ingenuity_determinism_gc(self):
        self.assertTrue(_check_determinism("Ingenuity", "gpu", "cpu"))

    async def test_quadcopter_determinism_gc(self):
        self.assertTrue(_check_determinism("Quadcopter", "gpu", "cpu"))

    async def test_crazyflie_determinism_gc(self):
        self.assertTrue(_check_determinism("Crazyflie", "gpu", "cpu"))

    async def test_allegro_hand_determinism_gc(self):
        self.assertTrue(_check_determinism("AllegroHand", "gpu", "cpu"))

    async def test_shadow_hand_determinism_gc(self):
        self.assertTrue(_check_determinism("ShadowHand", "gpu", "cpu"))

    async def test_shadow_hand_dr_determinism_gc(self):
        self.assertTrue(_check_determinism("ShadowHand", "gpu", "cpu", True))

    async def test_shadow_hand_openai_ff_determinism_gc(self):
        self.assertTrue(_check_determinism("ShadowHandOpenAI_FF", "gpu", "cpu"))

    async def test_shadow_hand_openai_lstm_determinism_gc(self):
        self.assertTrue(_check_determinism("ShadowHandOpenAI_LSTM", "gpu", "cpu"))


class TestOmniIsaacGymEnvsDeterminismGG(omni.kit.test.AsyncTestCase):
    @classmethod
    def setUpClass(self):
        # set up OIGE repo
        utils._setup_OIGE()

    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_cartpole_determinism_gg(self):
        self.assertTrue(_check_determinism("Cartpole", "gpu", "gpu"))

    async def test_ant_determinism_gg(self):
        self.assertTrue(_check_determinism("Ant", "gpu", "gpu"))

    async def test_humanoid_determinism_gg(self):
        self.assertTrue(_check_determinism("Humanoid", "gpu", "gpu"))

    async def test_anymal_determinism_gg(self):
        self.assertTrue(_check_determinism("Anymal", "gpu", "gpu"))

    async def test_anymal_terrain_determinism_gg(self):
        self.assertTrue(_check_determinism("AnymalTerrain", "gpu", "gpu"))

    async def test_ball_balance_determinism_gg(self):
        self.assertTrue(_check_determinism("BallBalance", "gpu", "gpu"))

    async def test_franka_cabinet_determinism_gg(self):
        self.assertTrue(_check_determinism("FrankaCabinet", "gpu", "gpu"))

    async def test_ingenuity_determinism_gg(self):
        self.assertTrue(_check_determinism("Ingenuity", "gpu", "gpu"))

    async def test_quadcopter_determinism_gg(self):
        self.assertTrue(_check_determinism("Quadcopter", "gpu", "gpu"))

    async def test_crazyflie_determinism_gg(self):
        self.assertTrue(_check_determinism("Crazyflie", "gpu", "gpu"))

    async def test_allegro_hand_determinism_gg(self):
        self.assertTrue(_check_determinism("AllegroHand", "gpu", "gpu"))

    async def test_shadow_hand_determinism_gg(self):
        self.assertTrue(_check_determinism("ShadowHand", "gpu", "gpu"))

    async def test_shadow_hand_dr_determinism_gg(self):
        self.assertTrue(_check_determinism("ShadowHand", "gpu", "gpu", True))

    async def test_shadow_hand_openai_ff_determinism_gg(self):
        self.assertTrue(_check_determinism("ShadowHandOpenAI_FF", "gpu", "gpu"))

    async def test_shadow_hand_openai_lstm_determinism_gg(self):
        self.assertTrue(_check_determinism("ShadowHandOpenAI_LSTM", "gpu", "gpu"))
