# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import datetime
import os
import yaml


class Logger:
    """ For logging parameter samples and dataset generation metadata. """

    # Static variables set outside class
    verbose = None
    content_log_dir = None

    def start_log_item(index):
        """ Initialize a sample's log message. """

        Logger.log_item = {}
        Logger.log_item["index"] = index
        Logger.log_item["metadata"] = {}
        Logger.log_item["metadata"]["timestamp"] = str(datetime.datetime.now())
        Logger.print("\n")

    def finish_log_item():
        """ Output a sample's log message to the end of the content log. """

        content_log_file = os.path.join(Logger.content_log_dir, "content_log.yaml")
        with open(content_log_file, "a") as f:
            yaml.dump(Logger.log_item, f)

    def write_parameter(key, val, sampled=False, group=None):
        """ Record a sample parameter value. """

        param_dict = {}
        param_dict["parameter"] = key
        param_dict["val"] = str(val)
        param_dict["sampled"] = sampled
        param_dict["group"] = group

        Logger.log_item["metadata"]["params"] = Logger.log_item["metadata"].get("params", []) + [param_dict]

    def print(line, force_print=False):
        """ Record a string and potentially print string to console. """

        Logger.log_item["metadata"].get("lines", []).append(line)

        if Logger.verbose or force_print:
            line = str(line)
            print(line)
