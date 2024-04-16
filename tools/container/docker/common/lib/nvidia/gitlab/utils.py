import os
import sys

import logging

import nvidia.git

from nvidia.die import die

from pprint import pprint

import urllib


def get_gitlab_registry_url(path=None, log_prefix=''):
  if(not path):
    path = os.getcwd()

  logging.info(f"{log_prefix}  > attempting to determine if {path} is a GIT" + 
                " repo")

  if(not nvidia.git.is_git_repo_path(path)):
    die("not a repo path, can't continue")

  origin_url = urllib.parse.urlparse(nvidia.git.get_origin_url(path))

  ret = f"{origin_url.hostname}:5005{origin_url.path}"
  if(ret.endswith('.git')):
    ret = ret[:-4]

  logging.info(f"{log_prefix}  > guessing {ret} is it's Registry")
  
  return(ret)

  
