import sys
import os 

import getpass
import socket

from time import strftime,localtime

import nvidia.git

def default_family():
  return '-'.join([getpass.getuser(), socket.gethostname()])

def default_build(git_dir=None):
  assert(git_dir)
  time_str = strftime("%Y-%m-%d-%H%M%S", localtime())
  hash = nvidia.git.get_git_hash_short(git_dir)
  build = "-".join([time_str, hash])
  return(build)


