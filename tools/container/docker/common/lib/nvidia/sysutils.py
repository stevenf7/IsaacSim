# Copyright (c) 2018, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os
import sys
import shutil

from pprint import pprint

import logging

_dir_pos_stack = []

def make_dir_if_not_present(d):
    if(not os.path.exists(d)):
      logging.info(f"Creating {d}")
      os.makedirs(d)


def reset_dir(d):
    if(os.path.exists(d)):
        shutil.rmtree(d)
    os.makedirs(d)


def push_dir_pos(d):
    _dir_pos_stack.append(os.getcwd())
    os.chdir(d)


def pop_dir_pos():
    if(len(_dir_pos_stack) == 0):
        raise Exception("No directories in stack")
    os.chdir(_dir_pos_stack.pop())

def fmd5(f):  
  import hashlib
  md5 = hashlib.md5()

  with open(f, "rb") as fh:
    while 1:
      data = fh.read(1048576)
      if(not data):
        break
      md5.update(data)

  return(md5.hexdigest())

def strmd5(data):
  import hashlib
  md5 = hashlib.md5()
  md5.update(data.encode('utf-8'))
  return(md5.hexdigest())
