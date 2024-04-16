import os
import sys

import logging 

import nvidia.gitlab.ci
import nvidia.git
import re

from nvidia.kube.helpers import is_valid_label_value

NO_VERSION = 'no_version'
VERSION_FILE = 'VERSION.md'

def get_release(repo_root=None):
  assert(repo_root)

  logging.info("  > determining version (release) name")

  version = load_project_version(repo_root)

  ret = ''

  if(version):
    ret =  version 
  else:
    ret = NO_VERSION

  logging.info(f"  > version (release): `{ret}`")
  return(ret)

  branch = get_branch(build_config)

def load_project_version(repo_root):

  if(version := os.getenv('OMNI_VERSION', None)):
    logging.info(f"    > version loaded from env, {version}")
    return(version)

  version_file_path = os.getenv('OMNI_VERSION_FILE_PATH', VERSION_FILE)
  version_file_path = os.path.join(repo_root, version_file_path)
  version_file_path = os.path.abspath(version_file_path)

  logging.info(f"    > attempting to load from {version_file_path}")

  if(not os.path.isfile(version_file_path)):
    logging.info(f"    > not found")
    return(None)

  with open(version_file_path, 'r') as h:
    version = h.read()

  version = version.rstrip().lstrip()
  logging.info(f"  > loaded release version `{version}`")
  if not(len(version)):
    die("Loaded emptry string, can't continue") 

  return(version)

def get_branch(path):
  logging.info("  > determining branch") 
  logging.info(f"  > using path: {path}")

  branch = None

  if(nvidia.gitlab.ci.is_ci_env()):
    logging.info("    > looks like gitlab CI env, using " + 
                 "CI branch name detection") 

    branch = nvidia.gitlab.ci.get_branch_name(path)
  else: 
    logging.info("    > looks like regular env, using git branch name")
    branch = nvidia.git.get_cur_branch(path)

  logging.info(f"    > detected `{branch}`")
  branch = norm_string(branch)
  logging.info(f"    > normalized to `{branch}`")
  return(branch)

def norm_string(string):
  string = re.sub("[^a-zA-Z0-9.-]", "-", string)
  string = re.sub("-+", "-", string)
  return(string)

def get_build(path=None, build_no=None):
  assert(path)

  logging.info("  > determining build name")
  hash = nvidia.git.get_git_hash_short(path)

  logging.info(f"    > git hash: `{hash}`")

  ret = ''

  if(build_no):
    logging.info(f"    > build # `{build_no}` provided")
    ret = '.'.join([build_no, hash])
  else:
    ret = hash

  logging.info(f"  > build: `{ret}`")
  return(ret)

def get_version_full(release, family, build, branch):
  return(f"{release}+{branch}.{family}.{build}")

def get_docker_image_tag(release, family, build, branch):
  return(f"{release}_{branch}.{family}.{build}")

def make_kube_compliant_version(version_str):
  ret = version_str
  if('+' in ret):
    ret = ret.replace('+', '_')

  if(is_valid_label_value(ret)):
    return(ret)
  else:
    die(f"Can't make proper Kube compliant version out of `{version_str}`")
