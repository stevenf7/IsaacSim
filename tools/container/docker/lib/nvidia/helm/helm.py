
import sys
import os

from pprint import pprint 
import logging 

from nvidia.die import die

from nvidia.sysutils import reset_dir

import subprocess
import packaging.version
import tempfile
import shutil
from hashlib import md5


MIN_HELM_VERSION = "3.8"

class Helm:
  
  def __init__(self):
    self._check_helm_version()
    self._init_repo_config_dir()


  def publish_chart(self, chart, target_reg, user, pwd):
    cmd = ['cm-push', '-f', chart.path, target_reg]
    if(user):
      cmd.extend(['-u', user])
    if(pwd):
      cmd.extend(['-p', pwd])

    ret = self._helm_cmd(cmd)
    if(ret):
      die(f"helm terminated with {ret}")

  def update_deps(self, chart, user, pwd):
    if(not pwd):
      die("  password needs to be provided!")

    deps = chart.dependencies()

    if(deps is None):
      return(None)

#    logging.info(f"    > resetting {chart.deps_dir()}") 
#    reset_dir(chart.deps_dir())

    for dep in deps:
      if(not dep['repo']):
        logging.info(f"    > skipping {dep['name']}: no repo provided")
        continue

      chart_filename = f"{dep['name']}-{dep['version']}.tgz"
      url = f"{dep['repo']}/charts/{chart_filename}"
      cmd = ['fetch', url, 
              '--username', user, 
              '--password', pwd,
              '-d', chart.deps_dir(), 
#              '--untar',
            ]
      logging.info(f"    > pulling {url}") 
      self._helm_cmd(cmd)
#      logging.info(f"    > cleaning up after helm") 
#      shutil.rmtree(os.path.join(chart.deps_dir(), chart_filename))
#      sys.exit()

    return(len(deps))

    # NOTE below disabled 'cause helm 
    # NOTE dependency update mechanism does NOT pick up
    # NOTE expecility specified versions sometimes, 
    # NOTE and is doing that silently. -- Fidot

    for repo in repos:
      logging.info(f"    > logging into {repo}") 
      self._repo_log_in(repo, user=user, pwd=pwd)

   
    cmd = ['dependency', 'update', chart.path,]
    cmd.extend(self._repo_cache_opts)
    self._helm_cmd(cmd)
    return(len(repos))
    
    
  def lint(self, chart):
    cmd = ['lint', '--quiet', chart.path]
    ret = self._helm_cmd(cmd)
    return(not ret)

  # Private
  def  _repo_log_in(self, repo, user, pwd):
    assert(repo) 

    cmd = ['repo', 'add', 
            self._namehash(repo), repo,
            '--username', user, 
            '--password', pwd ]

    cmd.extend(self._repo_cache_opts)
    self._helm_cmd(cmd)

  def  _namehash(self, s):
    return(md5(bytes(s.encode('ascii'))).hexdigest())

  def  _check_helm_version(self):
    version = self._helm_cmd(['version', "--template='{{.Version}}'"], 
                             grab_output = 1)
    version = version.lstrip("'").lstrip('v').rstrip("'")
    version = packaging.version.parse(version)

    if(version < packaging.version.parse(MIN_HELM_VERSION)):
      die(f"Only HELM versions {MIN_HELM_VERSION}+ are supported by " + 
          f"this library")

  def _helm_cmd(self, cmd, grab_output=0):
    to_run = [ 'helm' ]
    to_run.extend(cmd)

    ret = None

    try:
      if(grab_output):
        ret = subprocess.check_output(to_run)
      else:
        ret = subprocess.call(to_run)
    except FileNotFoundError:
      die(f"Couldn't execute `helm`: helm {MIN_HELM_VERSION}+ required in " + 
          f"$PATH")

    if(grab_output):
      ret = ret.decode('ascii')
    else:
      if(ret):
        die(f"Helm terminated with {ret}")

    return(ret)

  def _init_repo_config_dir(self):
    self._repo_config_dir = tempfile.mkdtemp()
    self._repo_cache_opts = [ '--repository-cache', 
                                f"{self._repo_config_dir}/repository",
                              '--repository-config',
                                f"{self._repo_config_dir}/repositories.yaml",
                              ]

  def __del__(self):
    shutil.rmtree(self._repo_config_dir)

