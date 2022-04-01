# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from omni.isaac.gym.vec_env import VecEnvBase

import queue


class TaskStopException(Exception):
    pass


# VecEnv Wrapper for RL training
class VecEnvMT(VecEnvBase):
    def initialize(self, action_queue, data_queue):
        self._action_queue = action_queue
        self._data_queue = data_queue
        self._stop = False
        self._first_frame = True
        self._timeout = 30

    def get_actions(self, block=True):
        if not self._stop:
            try:
                actions = self._action_queue.get(block, self._timeout)
                if actions is None:
                    self._stop = True
                    self._action_queue.task_done()
                    raise TaskStopException()
                else:
                    actions = actions.clone()
                self._action_queue.task_done()
            except (queue.Full, queue.Empty) as e:
                print("Getting actions: timeout occurred.")
                actions = None
                self._stop = True
        else:
            actions = None

        return actions

    def send_actions(self, actions, block=True):
        if not self._stop:
            try:
                self._action_queue.put(actions, block, self._timeout)
            except (queue.Full, queue.Empty) as e:
                print("Sending actions: timeout occurred.")
                self._stop = True

    def get_data(self, block=True):
        if not self._stop:
            try:
                if self._first_frame:
                    data = self._data_queue.get(block)
                    self._first_frame = False
                else:
                    data = self._data_queue.get(block, self._timeout)
                if data is None:
                    self._stop = True
                    raise TaskStopException()
                else:
                    self._parse_data(data)
                self._data_queue.task_done()
            except (queue.Full, queue.Empty) as e:
                print("Getting states: timeout occurred.")
                self._stop = True
                data = None
        else:
            data = None

        return data

    def send_data(self, data, block=True):
        if not self._stop:
            try:
                self._data_queue.put(data, block, self._timeout)
            except (queue.Full, queue.Empty) as e:
                print("Sending states: timeout occurred.")
                self._stop = True

    def clear_queues(self):
        while not self._action_queue.empty():
            self._action_queue.get_nowait()
            self._action_queue.task_done()
        while not self._data_queue.empty():
            self._data_queue.get_nowait()
            self._data_queue.task_done()
