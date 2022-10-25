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


class TestOmniIsaacGymEnvsTrainThresholdMinimalGG(omni.kit.test.AsyncTestCase):
    @classmethod
    def setUpClass(self):
        # set up OIGE repo
        utils._setup_OIGE()

    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    def _test_cartpole_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 400.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(train_time <= 60.0)

    def _test_ant_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 4500.0)
        self.assertTrue(ep_len >= 900.0)
        self.assertTrue(train_time <= 4.0 * 60)

    def _test_humanoid_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 4300.0)
        self.assertTrue(ep_len >= 850.0)
        self.assertTrue(train_time <= 12.0 * 60)

    def _test_anymal_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 35.0)
        self.assertTrue(ep_len >= 2000.0)
        self.assertTrue(train_time <= 10 * 60.0)

    def _test_anymal_terrain_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        terrain_level = utils._extract_feature(log_data, "Episode/terrain_level")

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)
        print("terrain_level:", terrain_level)

        self.assertTrue(reward >= 8.0)
        self.assertTrue(ep_len >= 600.0)
        self.assertTrue(train_time <= 60 * 60.0)
        self.assertTrue(terrain_level >= 3.0)

    def _test_ball_balance_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 350.0)
        self.assertTrue(ep_len >= 400.0)
        self.assertTrue(train_time <= 5 * 60.0)

    def _test_franka_cabinet_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 2000.0)
        self.assertTrue(ep_len >= 480.0)
        self.assertTrue(train_time <= 7 * 60.0)

    def _test_ingenuity_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 4000.0)
        self.assertTrue(ep_len >= 1900.0)
        self.assertTrue(train_time <= 5 * 60.0)

    def _test_quadcopter_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 1000.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(train_time <= 7 * 60.0)

    def _test_crazyflie_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 1000.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(train_time <= 10 * 60.0)

    def _test_allegro_hand_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)
        print("success:", consecutive_successes)

        self.assertTrue(reward >= 1500.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(train_time <= 120 * 60.0)
        self.assertTrue(consecutive_successes >= 5)

    def _test_shadow_hand_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)
        print("success:", consecutive_successes)

        self.assertTrue(reward >= 6000.0)
        self.assertTrue(ep_len >= 500.0)
        self.assertTrue(train_time <= 60 * 60.0)
        self.assertTrue(consecutive_successes >= 20)

    async def test_cartpole_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Cartpole", "gpu", "gpu", 75)
        self._test_cartpole_train(experiment_name)

    async def test_ant_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Ant", "gpu", "gpu", 300)
        self._test_ant_train(experiment_name)

    async def test_humanoid_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Humanoid", "gpu", "gpu", 500)
        self._test_humanoid_train(experiment_name)

    async def test_anymal_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Anymal", "gpu", "gpu", 500)
        self._test_anymal_train(experiment_name)

    async def test_anymal_terrain_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "AnymalTerrain", "gpu", "gpu", 800)
        self._test_anymal_terrain_train(experiment_name)

    async def test_ball_balance_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "BallBalance", "gpu", "gpu", 250)
        self._test_ball_balance_train(experiment_name)

    async def test_franka_cabinet_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "FrankaCabinet", "gpu", "gpu", 300)
        self._test_franka_cabinet_train(experiment_name)

    async def test_ingenuity_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Ingenuity", "gpu", "gpu", 400)
        self._test_ingenuity_train(experiment_name)

    async def test_quadcopter_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Quadcopter", "gpu", "gpu", 500)
        self._test_quadcopter_train(experiment_name)

    async def test_crazyflie_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Crazyflie", "gpu", "gpu", 500)
        self._test_crazyflie_train(experiment_name)

    async def test_allegro_hand_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "AllegroHand", "gpu", "gpu", 2000)
        self._test_allegro_hand_train(experiment_name)

    async def test_shadow_hand_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "ShadowHand", "gpu", "gpu", 1000)
        self._test_shadow_hand_train(experiment_name)


class TestOmniIsaacGymEnvsTrainThresholdGG(omni.kit.test.AsyncTestCase):
    @classmethod
    def setUpClass(self):
        # set up OIGE repo
        utils._setup_OIGE()

    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    def _test_cartpole_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 400.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(train_time <= 60.0)

    def _test_ant_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 4500.0)
        self.assertTrue(ep_len >= 900.0)
        self.assertTrue(train_time <= 4.0 * 60)

    def _test_humanoid_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 4300.0)
        self.assertTrue(ep_len >= 850.0)
        self.assertTrue(train_time <= 12.0 * 60)

    def _test_anymal_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 35.0)
        self.assertTrue(ep_len >= 2000.0)
        self.assertTrue(train_time <= 10 * 60.0)

    def _test_anymal_terrain_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        terrain_level = utils._extract_feature(log_data, "Episode/terrain_level")

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)
        print("terrain_level:", terrain_level)

        self.assertTrue(reward >= 8.0)
        self.assertTrue(ep_len >= 600.0)
        self.assertTrue(train_time <= 60 * 60.0)
        self.assertTrue(terrain_level >= 3.0)

    def _test_ball_balance_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 350.0)
        self.assertTrue(ep_len >= 400.0)
        self.assertTrue(train_time <= 5 * 60.0)

    def _test_franka_cabinet_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 2000.0)
        self.assertTrue(ep_len >= 480.0)
        self.assertTrue(train_time <= 7 * 60.0)

    def _test_ingenuity_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 4000.0)
        self.assertTrue(ep_len >= 1900.0)
        self.assertTrue(train_time <= 5 * 60.0)

    def _test_quadcopter_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 1000.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(train_time <= 7 * 60.0)

    def _test_crazyflie_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 1000.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(train_time <= 10 * 60.0)

    def _test_allegro_hand_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)
        print("success:", consecutive_successes)

        self.assertTrue(reward >= 1500.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(train_time <= 120 * 60.0)
        self.assertTrue(consecutive_successes >= 5)

    def _test_shadow_hand_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)
        print("success:", consecutive_successes)

        self.assertTrue(reward >= 6000.0)
        self.assertTrue(ep_len >= 500.0)
        self.assertTrue(train_time <= 60 * 60.0)
        self.assertTrue(consecutive_successes >= 20)

    def _test_shadow_hand_dr_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)
        print("success:", consecutive_successes)

        self.assertTrue(reward >= 3000.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(train_time <= 1.2 * 60 * 60.0)
        self.assertTrue(consecutive_successes >= 10)

    def _test_shadow_hand_openai_ff_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)
        print("success:", consecutive_successes)

        self.assertTrue(reward >= 2500.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(train_time <= 3 * 60 * 60.0)
        self.assertTrue(consecutive_successes >= 10)

    def _test_shadow_hand_openai_lstm_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)
        print("success:", consecutive_successes)

        self.assertTrue(reward >= 6500.0)
        self.assertTrue(ep_len >= 1300.0)
        self.assertTrue(train_time <= 3.5 * 60 * 60.0)
        self.assertTrue(consecutive_successes >= 25)

    async def test_cartpole_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Cartpole", "gpu", "gpu", 75)
        self._test_cartpole_train(experiment_name)

    async def test_ant_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Ant", "gpu", "gpu", 300)
        self._test_ant_train(experiment_name)

    async def test_humanoid_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Humanoid", "gpu", "gpu", 500)
        self._test_humanoid_train(experiment_name)

    async def test_anymal_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Anymal", "gpu", "gpu", 500)
        self._test_anymal_train(experiment_name)

    async def test_anymal_terrain_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "AnymalTerrain", "gpu", "gpu", 800)
        self._test_anymal_terrain_train(experiment_name)

    async def test_ball_balance_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "BallBalance", "gpu", "gpu", 250)
        self._test_ball_balance_train(experiment_name)

    async def test_franka_cabinet_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "FrankaCabinet", "gpu", "gpu", 300)
        self._test_franka_cabinet_train(experiment_name)

    async def test_ingenuity_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Ingenuity", "gpu", "gpu", 400)
        self._test_ingenuity_train(experiment_name)

    async def test_quadcopter_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Quadcopter", "gpu", "gpu", 500)
        self._test_quadcopter_train(experiment_name)

    async def test_crazyflie_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Crazyflie", "gpu", "gpu", 500)
        self._test_crazyflie_train(experiment_name)

    async def test_allegro_hand_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "AllegroHand", "gpu", "gpu", 2000)
        self._test_allegro_hand_train(experiment_name)

    async def test_shadow_hand_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "ShadowHand", "gpu", "gpu", 1000)
        self._test_shadow_hand_train(experiment_name)

    async def test_shadow_hand_dr_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "ShadowHand", "gpu", "gpu", 1000, True)
        self._test_shadow_hand_dr_train(experiment_name)

    async def test_shadow_hand_openai_ff_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "ShadowHandOpenAI_FF", "gpu", "gpu", 2000)
        self._test_shadow_hand_openai_ff_train(experiment_name)

    async def test_shadow_hand_openai_lstm_train_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "ShadowHandOpenAI_LSTM", "gpu", "gpu", 2000)
        self._test_shadow_hand_openai_lstm_train(experiment_name)


class TestOmniIsaacGymEnvsTrainThresholdGGMT(omni.kit.test.AsyncTestCase):
    @classmethod
    def setUpClass(self):
        # set up OIGE repo
        utils._setup_OIGE()

    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    def _test_cartpole_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 400.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(train_time <= 60.0)

    def _test_ant_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 4500.0)
        self.assertTrue(ep_len >= 900.0)
        self.assertTrue(train_time <= 4.0 * 60)

    def _test_humanoid_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 4000.0)
        self.assertTrue(ep_len >= 850.0)
        self.assertTrue(train_time <= 12.0 * 60)

    def _test_anymal_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 35.0)
        self.assertTrue(ep_len >= 2000.0)
        self.assertTrue(train_time <= 10 * 60.0)

    def _test_anymal_terrain_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        terrain_level = utils._extract_feature(log_data, "Episode/terrain_level")

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)
        print("terrain_level:", terrain_level)

        self.assertTrue(reward >= 8.0)
        self.assertTrue(ep_len >= 600.0)
        self.assertTrue(train_time <= 60 * 60.0)
        self.assertTrue(terrain_level >= 3.0)

    def _test_ball_balance_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 350.0)
        self.assertTrue(ep_len >= 400.0)
        self.assertTrue(train_time <= 5 * 60.0)

    def _test_franka_cabinet_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 2000.0)
        self.assertTrue(ep_len >= 480.0)
        self.assertTrue(train_time <= 7 * 60.0)

    def _test_ingenuity_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 4000.0)
        self.assertTrue(ep_len >= 1900.0)
        self.assertTrue(train_time <= 5 * 60.0)

    def _test_quadcopter_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 1000.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(train_time <= 7 * 60.0)

    def _test_crazyflie_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)

        self.assertTrue(reward >= 1000.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(train_time <= 10 * 60.0)

    def _test_allegro_hand_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)
        print("success:", consecutive_successes)

        self.assertTrue(reward >= 1500.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(train_time <= 120 * 60.0)
        self.assertTrue(consecutive_successes >= 5)

    def _test_shadow_hand_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)
        print("success:", consecutive_successes)

        self.assertTrue(reward >= 6000.0)
        self.assertTrue(ep_len >= 500.0)
        self.assertTrue(train_time <= 60 * 60.0)
        self.assertTrue(consecutive_successes >= 20)

    def _test_shadow_hand_dr_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)
        print("success:", consecutive_successes)

        self.assertTrue(reward >= 3000.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(train_time <= 1.2 * 60 * 60.0)
        self.assertTrue(consecutive_successes >= 10)

    def _test_shadow_hand_openai_ff_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)
        print("success:", consecutive_successes)

        self.assertTrue(reward >= 2500.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(train_time <= 3 * 60 * 60.0)
        self.assertTrue(consecutive_successes >= 10)

    def _test_shadow_hand_openai_lstm_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        print("reward:", reward)
        print("ep len:", ep_len)
        print("train_time:", train_time)
        print("success:", consecutive_successes)

        self.assertTrue(reward >= 6500.0)
        self.assertTrue(ep_len >= 1300.0)
        self.assertTrue(train_time <= 3.5 * 60 * 60.0)
        self.assertTrue(consecutive_successes >= 25)

    async def test_cartpole_train_mt_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_MT_SCRIPT, "Cartpole", "gpu", "gpu", 75)
        self._test_cartpole_train(experiment_name)

    async def test_ant_train_mt_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_MT_SCRIPT, "Ant", "gpu", "gpu", 300)
        self._test_ant_train(experiment_name)

    async def test_humanoid_train_mt_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_MT_SCRIPT, "Humanoid", "gpu", "gpu", 500)
        self._test_humanoid_train(experiment_name)

    async def test_anymal_train_mt_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_MT_SCRIPT, "Anymal", "gpu", "gpu", 500)
        self._test_anymal_train(experiment_name)

    async def test_anymal_terrain_train_mt_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_MT_SCRIPT, "AnymalTerrain", "gpu", "gpu", 800)
        self._test_anymal_terrain_train(experiment_name)

    async def test_ball_balance_train_mt_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_MT_SCRIPT, "BallBalance", "gpu", "gpu", 250)
        self._test_ball_balance_train(experiment_name)

    async def test_franka_cabinet_train_mt_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_MT_SCRIPT, "FrankaCabinet", "gpu", "gpu", 300)
        self._test_franka_cabinet_train(experiment_name)

    async def test_ingenuity_train_mt_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_MT_SCRIPT, "Ingenuity", "gpu", "gpu", 400)
        self._test_ingenuity_train(experiment_name)

    async def test_quadcopter_train_mt_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_MT_SCRIPT, "Quadcopter", "gpu", "gpu", 500)
        self._test_quadcopter_train(experiment_name)

    async def test_crazyflie_train_mt_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_MT_SCRIPT, "Crazyflie", "gpu", "gpu", 500)
        self._test_crazyflie_train(experiment_name)

    async def test_allegro_hand_train_mt_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_MT_SCRIPT, "AllegroHand", "gpu", "gpu", 2000)
        self._test_allegro_hand_train(experiment_name)

    async def test_shadow_hand_train_mt_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_MT_SCRIPT, "ShadowHand", "gpu", "gpu", 1000)
        self._test_shadow_hand_train(experiment_name)

    async def test_shadow_hand_dr_train_mt_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_MT_SCRIPT, "ShadowHand", "gpu", "gpu", 1000, True)
        self._test_shadow_hand_dr_train(experiment_name)

    async def test_shadow_hand_openai_ff_train_mt_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_MT_SCRIPT, "ShadowHandOpenAI_FF", "gpu", "gpu", 2000)
        self._test_shadow_hand_openai_ff_train(experiment_name)

    async def test_shadow_hand_openai_lstm_train_mt_gg(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_MT_SCRIPT, "ShadowHandOpenAI_LSTM", "gpu", "gpu", 2000)
        self._test_shadow_hand_openai_lstm_train(experiment_name)


class TestOmniIsaacGymEnvsTrainThresholdGC(omni.kit.test.AsyncTestCase):
    @classmethod
    def setUpClass(self):
        # set up OIGE repo
        utils._setup_OIGE()

    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    def _test_cartpole_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 400.0)
        self.assertTrue(ep_len >= 450.0)

    def _test_ant_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 4500.0)
        self.assertTrue(ep_len >= 900.0)

    def _test_humanoid_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 4300.0)
        self.assertTrue(ep_len >= 850.0)

    def _test_anymal_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 35.0)
        self.assertTrue(ep_len >= 2000.0)

    def _test_anymal_terrain_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        terrain_level = utils._extract_feature(log_data, "Episode/terrain_level")

        self.assertTrue(reward >= 8.0)
        self.assertTrue(ep_len >= 600.0)
        self.assertTrue(terrain_level >= 3.0)

    def _test_ball_balance_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 350.0)
        self.assertTrue(ep_len >= 400.0)

    def _test_franka_cabinet_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 2000.0)
        self.assertTrue(ep_len >= 480.0)

    def _test_ingenuity_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 4000.0)
        self.assertTrue(ep_len >= 1900.0)

    def _test_quadcopter_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 1000.0)
        self.assertTrue(ep_len >= 450.0)

    def _test_crazyflie_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 1000.0)
        self.assertTrue(ep_len >= 450.0)

    def _test_allegro_hand_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        self.assertTrue(reward >= 1500.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(consecutive_successes >= 5)

    def _test_shadow_hand_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        self.assertTrue(reward >= 6000.0)
        self.assertTrue(ep_len >= 500.0)
        self.assertTrue(consecutive_successes >= 20)

    def _test_shadow_hand_dr_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        self.assertTrue(reward >= 3000.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(consecutive_successes >= 10)

    def _test_shadow_hand_openai_ff_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        self.assertTrue(reward >= 2500.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(consecutive_successes >= 10)

    def _test_shadow_hand_openai_lstm_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        self.assertTrue(reward >= 6500.0)
        self.assertTrue(ep_len >= 1300.0)
        self.assertTrue(consecutive_successes >= 25)

    async def test_cartpole_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Cartpole", "gpu", "cpu", 75)
        self._test_cartpole_train(experiment_name)

    async def test_ant_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Ant", "gpu", "cpu", 300)
        self._test_ant_train(experiment_name)

    async def test_humanoid_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Humanoid", "gpu", "cpu", 500)
        self._test_humanoid_train(experiment_name)

    async def test_anymal_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Anymal", "gpu", "cpu", 500)
        self._test_anymal_train(experiment_name)

    async def test_anymal_terrain_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "AnymalTerrain", "gpu", "cpu", 800)
        self._test_anymal_terrain_train(experiment_name)

    async def test_ball_balance_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "BallBalance", "gpu", "cpu", 250)
        self._test_ball_balance_train(experiment_name)

    async def test_franka_cabinet_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "FrankaCabinet", "gpu", "cpu", 300)
        self._test_franka_cabinet_train(experiment_name)

    async def test_ingenuity_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Ingenuity", "gpu", "cpu", 400)
        self._test_ingenuity_train(experiment_name)

    async def test_quadcopter_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Quadcopter", "gpu", "cpu", 500)
        self._test_quadcopter_train(experiment_name)

    async def test_crazyflie_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "Crazyflie", "gpu", "cpu", 500)
        self._test_crazyflie_train(experiment_name)

    async def test_allegro_hand_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "AllegroHand", "gpu", "cpu", 2000)
        self._test_allegro_hand_train(experiment_name)

    async def test_shadow_hand_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "ShadowHand", "gpu", "cpu", 1000)
        self._test_shadow_hand_train(experiment_name)

    async def test_shadow_hand_dr_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "ShadowHand", "gpu", "cpu", 1000, True)
        self._test_shadow_hand_dr_train(experiment_name)

    async def test_shadow_hand_openai_ff_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "ShadowHandOpenAI_FF", "gpu", "cpu", 2000)
        self._test_shadow_hand_openai_ff_train(experiment_name)

    async def test_shadow_hand_openai_lstm_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT, "ShadowHandOpenAI_LSTM", "gpu", "cpu", 2000)
        self._test_shadow_hand_openai_lstm_train(experiment_name)


class TestOmniIsaacGymEnvsTrainThresholdGCMT(omni.kit.test.AsyncTestCase):
    @classmethod
    def setUpClass(self):
        # set up OIGE repo
        utils._setup_OIGE()

    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    def _test_cartpole_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 400.0)
        self.assertTrue(ep_len >= 450.0)

    def _test_ant_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 4500.0)
        self.assertTrue(ep_len >= 900.0)

    def _test_humanoid_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 4000.0)
        self.assertTrue(ep_len >= 850.0)

    def _test_anymal_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 35.0)
        self.assertTrue(ep_len >= 2000.0)

    def _test_anymal_terrain_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        terrain_level = utils._extract_feature(log_data, "Episode/terrain_level")

        self.assertTrue(reward >= 8.0)
        self.assertTrue(ep_len >= 600.0)
        self.assertTrue(terrain_level >= 3.0)

    def _test_ball_balance_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 350.0)
        self.assertTrue(ep_len >= 400.0)

    def _test_franka_cabinet_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 2000.0)
        self.assertTrue(ep_len >= 480.0)

    def _test_ingenuity_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 4000.0)
        self.assertTrue(ep_len >= 1900.0)

    def _test_quadcopter_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 1000.0)
        self.assertTrue(ep_len >= 450.0)

    def _test_crazyflie_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)

        self.assertTrue(reward >= 1000.0)
        self.assertTrue(ep_len >= 450.0)

    def _test_allegro_hand_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        self.assertTrue(reward >= 1500.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(consecutive_successes >= 5)

    def _test_shadow_hand_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        self.assertTrue(reward >= 6000.0)
        self.assertTrue(ep_len >= 500.0)
        self.assertTrue(consecutive_successes >= 20)

    def _test_shadow_hand_dr_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        self.assertTrue(reward >= 3000.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(consecutive_successes >= 10)

    def _test_shadow_hand_openai_ff_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        self.assertTrue(reward >= 2500.0)
        self.assertTrue(ep_len >= 450.0)
        self.assertTrue(consecutive_successes >= 10)

    def _test_shadow_hand_openai_lstm_train(self, experiment_name):
        log_data = utils._retrieve_logs(experiment_name)
        reward = utils._extract_reward(log_data)
        ep_len = utils._extract_episode_length(log_data)
        train_time = utils._extract_time(log_data)
        consecutive_successes = utils._extract_feature(log_data, "consecutive_successes/iter")

        self.assertTrue(reward >= 6500.0)
        self.assertTrue(ep_len >= 1300.0)
        self.assertTrue(consecutive_successes >= 25)

    async def test_cartpole_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT_MT, "Cartpole", "gpu", "cpu", 75)
        self._test_cartpole_train(experiment_name)

    async def test_ant_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT_MT, "Ant", "gpu", "cpu", 300)
        self._test_ant_train(experiment_name)

    async def test_humanoid_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT_MT, "Humanoid", "gpu", "cpu", 500)
        self._test_humanoid_train(experiment_name)

    async def test_anymal_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT_MT, "Anymal", "gpu", "cpu", 500)
        self._test_anymal_train(experiment_name)

    async def test_anymal_terrain_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT_MT, "AnymalTerrain", "gpu", "cpu", 800)
        self._test_anymal_terrain_train(experiment_name)

    async def test_ball_balance_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT_MT, "BallBalance", "gpu", "cpu", 250)
        self._test_ball_balance_train(experiment_name)

    async def test_franka_cabinet_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT_MT, "FrankaCabinet", "gpu", "cpu", 300)
        self._test_franka_cabinet_train(experiment_name)

    async def test_ingenuity_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT_MT, "Ingenuity", "gpu", "cpu", 400)
        self._test_ingenuity_train(experiment_name)

    async def test_quadcopter_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT_MT, "Quadcopter", "gpu", "cpu", 500)
        self._test_quadcopter_train(experiment_name)

    async def test_crazyflie_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT_MT, "Crazyflie", "gpu", "cpu", 500)
        self._test_crazyflie_train(experiment_name)

    async def test_allegro_hand_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT_MT, "AllegroHand", "gpu", "cpu", 2000)
        self._test_allegro_hand_train(experiment_name)

    async def test_shadow_hand_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT_MT, "ShadowHand", "gpu", "cpu", 1000)
        self._test_shadow_hand_train(experiment_name)

    async def test_shadow_hand_dr_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT_MT, "ShadowHand", "gpu", "cpu", 1000, True)
        self._test_shadow_hand_dr_train(experiment_name)

    async def test_shadow_hand_openai_ff_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT_MT, "ShadowHandOpenAI_FF", "gpu", "cpu", 2000)
        self._test_shadow_hand_openai_ff_train(experiment_name)

    async def test_shadow_hand_openai_lstm_train_gc(self):
        experiment_name = utils._run_rlgames_train(utils.RLGAMES_SCRIPT_MT, "ShadowHandOpenAI_LSTM", "gpu", "cpu", 2000)
        self._test_shadow_hand_openai_lstm_train(experiment_name)
