#!/usr/bin/python3.6

# Copyright (c) 2019, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import logging
import os
import sys
import atexit

import fcntl
from fcntl import LOCK_EX, LOCK_NB, LOCK_UN

from pprint import pprint

lock_file_path = None
lock_file_fd = None


def grab_lock_or_exit():
    temp = get_temp()
    lock_file = get_lockfile()

    global lock_file_path
    lock_file_path = os.path.join(temp, lock_file)

    logging.info(f"Attempting to grab lock at {lock_file_path}")

    global lock_file_fd
    lock_file_fd = open(lock_file_path, "a+")
    lock_file_fd.seek(0)

    try:
        fcntl.lockf(lock_file_fd, LOCK_EX | LOCK_NB)
    except:
        logging.info(f"Locking failed")
        pid = lock_file_fd.read()
        lock_file_fd.close()
        logging.info(f"Looks like locked by another PID {pid}...")
        sys.exit(1)

    atexit.register(unlock)
    lock_file_fd.write(str(os.getpid()))
    lock_file_fd.flush()
    os.fsync(lock_file_fd)


def unlock():
    logging.info(f"Unlocking {lock_file_path}")
    fcntl.lockf(lock_file_fd, LOCK_UN)
    lock_file_fd.close()
    os.remove(lock_file_path)


def get_lockfile():
    basename = os.path.basename(sys.argv[0])
    return(f"{basename}.p_lock")


def get_temp():

    env_vars = ['TMP', 'TEMP']

    for var in env_vars:
        v = os.getenv(var, None)
        if not v:
            continue
        elif(not os.path.isdir(v)):
            continue
        else:
            return(v)

    if(os.path.isdir('/tmp')):
        return('/tmp')

    raise Exception("Can't find a suitable temp dir")

################################################################################
##
################################################################################
