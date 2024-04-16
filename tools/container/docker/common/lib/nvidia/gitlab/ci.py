#!/usr/bin/python3.6

import sys
import os
from nvidia.die import die
import nvidia.git

def is_ci_env():
  if(os.getenv('GITLAB_CI', None)):
    return(1)
  else:
    return(0)

def get_project_url():
  assert(is_ci_env())
  return(os.getenv('CI_PROJECT_URL'))


def get_branch_name(path):
  mr = os.getenv('CI_MERGE_REQUEST_IID', None)
  tag = os.getenv('CI_COMMIT_TAG', None)
  branch_name = os.getenv('CI_COMMIT_REF_NAME', None)

  if(mr and tag):
    die("Both Merge Request and Tag env vars are set. Something's wrong")

  if(mr):
    return(f"mr{mr}")
  elif(tag):
    return(f"tag-{tag}")
  elif(branch_name):
    return(branch_name)
  else:
    return(nvidia.git.get_cur_branch(path))



