# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from env import JetBotGymEnv

my_env = JetBotGymEnv(observation_mode="camera")
my_env.reset()

for _ in range(20):
    my_env.reset()
    for _ in range(10000):
        obs, reward, done, info = my_env.step(my_env.action_space.sample())
        # my_env.render() Only used if observation_mode is structured for performance

my_env.close()
