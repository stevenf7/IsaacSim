#!/usr/bin/env python

# Copyright (c) 2018-2019, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import sys
import docker
import os
import subprocess
import time

import re

import io
import logging

from .tarimage import TarImage
from .stack import Stack

from pprint import pprint

from nvidia.sysutils import push_dir_pos, pop_dir_pos
from nvidia.die import die


class Docker:
 
  server = None
  api = None
  docker_cmd = None

  def __init__(self, **kwargs):
    if 'HTTP_PROXY' in os.environ:
      del os.environ['HTTP_PROXY']
    if(('server' in kwargs) and (kwargs['server'])):
      self.server = kwargs['server']
      if(  (self.server == 'localhost') or
           (self.server.startswith('127.'))):
        die(f"You specified `{self.server}` as the server: targeting " + 
            f"loopback will break things. Use proper hostname resolvable " + 
            f"to a real IP.")
      else:
        logging.info(f"Using >{self.server}< Docker server")
    else:
      logging.info(f"Using whatever Docker server is set up in env")

    if('docker_exe' in kwargs):
      docker_exe = kwargs['docker_exe']
    else:
      docker_exe = None

    self._setup_docker_exe(docker_exe)
    self._setup_api()
    self._use_buildkit = not(kwargs.get('no_buildkit', 0))

  ##############
  ### Public
  ##############
 
  def image_exists(self, **kwargs):
    image_name = None

    if('full_name' in kwargs):
      image_name = kwargs['full_name']
    elif(('name' in kwargs) and ('tag' in kwargs)):
      image_name = "%s:%s" %(kwargs['name'], kwargs['tag'])
    else:
      raise Exception("Wrong arguments to image_exists()")

    try:
      image = self.api.images.get(image_name)
      if(image):
        return(True)
    except(docker.errors.ImageNotFound):
      return(False)

  def build_image(self, image_name, cache_from=[],  **kwargs):

    enable_buildkit = not kwargs.get('no_buildkit', 0)
    if(enable_buildkit):
      logging.info(" > enabling Docker BuildKit")
      docker_version_minimum = "19.03"
      docker_version = self.api.version()['Version']
      if tuple(map(int, docker_version.split('.'))) >= tuple(map(int, docker_version_minimum.split('.'))):
        os.environ["DOCKER_BUILDKIT"] = '1'
      else:
        raise Exception(f"Docker version {self.api.version()['Version']}: " + 
                        f"we only support BuildKit in version {docker_version_minimum} and higher")
    else:
      logging.info(" > Docker BuildKit disabled")

    if(kwargs['build_in']):
      push_dir_pos(kwargs['build_in'])

    if(enable_buildkit and kwargs.get('plain_progress', None)):
      os.environ["BUILDKIT_PROGRESS"] = "plain"

    build_cmd = self.docker_cmd + [ 'build', 
                                    '-t', image_name, ]

    if(os.getenv("CI", None)):
      logging.info("  > CI env detected, adding CI variable to the build") 
      build_cmd.extend(['--build-arg', 'CI=true'])

    if(enable_buildkit):
      build_cmd.extend(['--build-arg', 'BUILDKIT_INLINE_CACHE=1'])

      # Image(s) to use as a cache for docker layers, used when the
      # image might not be recognized by docker as a match
      # (if you pulled an image from a previous build)

      for i in cache_from:
          build_cmd.extend(['--cache-from', i])

    dockerfile_fn = None

    if(kwargs['dockerfile']):

      dockerfile_fn = "Dockerfile.%i" % (os.getpid())

      with open(dockerfile_fn, "w") as dfh:
        dfh.write(kwargs['dockerfile'])

      build_cmd.extend(['-f', dockerfile_fn])

    build_cmd.append('.')
    logging.info(f"Docker build command: {' '.join(build_cmd)}")

    ret = subprocess.call(build_cmd, stdout=sys.stderr)

    if(dockerfile_fn and (not (kwargs['keep_dockerfile']))):
      os.unlink(dockerfile_fn)

    if(ret):
      raise Exception(f"Build failed with non-zero exit code ({ret})")

    if(kwargs['build_in']):
      pop_dir_pos()

  def cmd(self, no_log=0, *args):
    cmd = list(self.docker_cmd)
    cmd.extend([*args])
    ret = subprocess.call(cmd, stdout=sys.stderr)
    if(ret):
      die(f"Docker failed with {ret}")

  def cmd_ng(self, args=[], no_log=0):
    cmd = list(self.docker_cmd)
    cmd.extend(args)

    if(no_log):
      pass
    else:
      logging.info(f"Running custom docker command")
      logging.info(f"  > {' '.join([*args])}")

    ret = subprocess.call(cmd, stdout=sys.stderr)

    if(ret):
      die(f"Docker failed with {ret}")

  def copy_from_image(self, image, src, dest):
    cmd = list(self.docker_cmd)
    cmd.extend(['run', 
                '-e', 'ACCEPT_EULA=1', 
                '--entrypoint', '/bin/bash',
                '-d', image, 
                '-c', 'sleep 100000'])
    logging.info(f"    > launching {image}")
    container_id = subprocess.check_output(cmd).decode('ascii').rstrip()
    logging.info(f"    > container `{container_id}`")

    logging.info(f"    > copying")
    self.cmd_ng(['cp', f"{container_id}:{src}", dest], no_log=1)
    logging.info(f"    > killing container")
    self.cmd_ng(['kill', container_id], no_log=1)

  def save_image(self, image_name, out_path):

    # Note: Docker API's version of save() is broken: it doesn't include 
    # Note: repository tag in image's metadata.json file. 
    # Note: 
    # Note: This is why I had to do this via command line
    # Note:                     - Fidot, March 9 '18

    if not (self.image_exists(full_name=image_name)):
      raise Exception(f"Image {image_name} not found")

    save_cmd = self.docker_cmd +  ['image', 'save', image_name, '-o', out_path]
    ret = subprocess.call(save_cmd)
    if(ret):
      raise Exception(f"Save failed with non-zero exit code ({ret})")
    
  def upload_image(self, path, **kwargs):

    if not (os.path.isfile(path)):
      raise Exception(f"{path} is not a file")

    tar_image = TarImage(path)

    if(self.image_exists(full_name=tar_image.tag())):
      if(kwargs['return_existing']):
        return self.api.images.get(tar_image.tag())
      else:
        raise Exception(f"Image with tag {tag} already exists")
      
    upload_cmd = self.docker_cmd + ['image', 'load', '-i',  path]
    ret = subprocess.call(upload_cmd)
    if(ret):
      raise Exception(f"Load failed with non-zero exit code ({ret})")

    return self.api.images.get(tar_image.tag())

  def push_image(self, image_name, dest_registry, dots=0, additional_tags=[]):
    dest_registry = dest_registry.rstrip('/')
    image = self.api.images.get(image_name)
    registry_tags = [  "/".join([dest_registry, image_name]) ]
    if(len(additional_tags)):
      (n,t) = image_name.split(':')
      for _ in additional_tags:
        registry_tags.append("/".join([dest_registry, f"{n}:{_}"]))

    for registry_tag in registry_tags:
      image.tag(registry_tag)
      already_printed = {}
      for status in self.api.images.push(registry_tag, stream=1, decode=1):
        if('status' in status):
          msg = f"{status['status']} {status.get('id', '')}"
          if(msg not in already_printed):
            logging.info(f" [D] {msg}")

          already_printed[msg] = msg
        elif('error' in status):
          logging.error(f" [D] ERROR: {status['error']}")
          raise docker.errors.APIError(status['errorDetail'])
        else:
          pass
#          logging.info(status)
        
      self.api.images.remove(image=registry_tag)

  def deploy_stack(self, **kwargs):
    deploy_cmd = self.docker_cmd + ['stack', 'deploy', kwargs['name'], 
                                    '-c', kwargs['compose_file'], 
                                    '--prune']

    ret = subprocess.call(deploy_cmd)
    if(ret):
      raise Exception(f"Deploying stack failed with non-zero exit code ({ret})")

  # This is a fairly dirty func... but it works. 
  def remove_stack(self, name, **kwargs):
    stacks = self.get_stacks()
    target_stack = None

    def default_print(*arg):
      pass

    print_func = default_print;
    if('print_callback' in kwargs):
      print_func = kwargs['print_callback']

    for s in stacks:
     if(s.name == name):
       target_stack = s
       break

    if not target_stack:
      return

    containers = []
    for s in  target_stack.services():
      for t in s.api.tasks(): 
        con_status = t['Status'].get('ContainerStatus', None)
        if(con_status and ('ContainerID' in con_status)):
          container_id =  t['Status']['ContainerStatus']['ContainerID']
          containers.append( self.api.containers.get(container_id))

    networks = []
    networks = [ n for n in self.api.networks.list()
                      if (n.attrs['Labels']) and
                         ('com.docker.stack.namespace' in n.attrs['Labels']) and 
                         (n.attrs['Labels']['com.docker.stack.namespace'] == name) 
               ]

    rmstack_cmd = self.docker_cmd + ['stack', 'rm', name ]
    ret = subprocess.call(rmstack_cmd)
    if(ret):
      raise Exception(f"Removing stack failed with non-zero exit code ({ret})")

    for c in containers:
      print_func(f"  > Waiting for {c.name} to stop")
      exit = None
      try:
        exit = c.wait()
      except docker.errors.NotFound:
        print_func("   >> already stopped")

      if(exit):
        if((type(exit) is dict)):
          print_func(f"   >> {exit['StatusCode']}, err: '{exit['Error']}'")
        elif((type(exit) is int)):
          print_func(f"   >> INT exit code: {exit}")
        else:
          print_func( "   >> can't process this type")

    for n in networks: 
      print_func(f"  > Waiting for {c.name} to shut down")

      while(1):
        try:
          n.reload()
        except docker.errors.NotFound:
          break

        time.sleep(1)

  def get_stacks(self):
    stack_enum_cmd = self.docker_cmd + ['stack', 'ls']
    ret = subprocess.run(stack_enum_cmd, stdout=subprocess.PIPE)
    if(ret.returncode):
      raise Exception(f"Listing stacks failed with non-zero "
                       "exit code ({ret.returncode})")

    stacks = []
    for ln in (ret.stdout.decode('ascii').split("\n")[1:]):
      if(re.match("^ *$", ln)):
        continue
      stack_name = re.split(" +", ln)[0]
      stacks.append(Stack(self, stack_name))

    return(stacks)

  def _delete_hostdir(self, dirs, **kwargs):
    to_delete = []

    if(isinstance(dirs, list)):
      to_delete = dirs
    else:
      to_delete.append(dirs)

    del_cmd = self.docker_cmd + ['run',
#                                 '-it', 
                                 '-v', '/:/_host', 
                                 'centos:7', 
                                'rm', '-rf'] + [f"/_host/{x}" for x in to_delete] 

    ret = subprocess.call(del_cmd)
    if(ret):
      raise OSError(f"Deleting failed with non-zero exit code: {ret}")

  def _create_hostdir(self, dirs, **kwargs):

    to_create = []

    if(isinstance(dirs, list)):
      to_create = dirs
    else:
      to_create.append(dirs)

    mkdir_script = [f"mkdir -p /_host/{x}; chmod 777 /_host/{x}" for x in to_create]

    mkdir_cmd = self.docker_cmd + ['run',
#                                   '-it', 
                                   '-v', '/:/_host', 
                                   'centos:7', 
                                   'sh', '-c', 
                                   "; ".join(mkdir_script), 
                                   ]

    ret = subprocess.call(mkdir_cmd)
    if(ret):
      raise OSError(f"Creating failed with non-zero exit code: {ret}")

  def _host_diskinfo(self):
    df_cmd = self.docker_cmd + ['run',
#                                   '-it', 
                                 '-v', '/var/lib/docker:/_docker', 
                                 'centos:7', 
                                 'df', '/_docker',
                               ]

    ret = subprocess.run(df_cmd, stdout=subprocess.PIPE)
    if(ret.returncode):
      raise Exception(f"Reading disk info failed with non-zero exit " + 
                       "code: {ret.returncode}")

    ln = ret.stdout.decode('ascii').split("\n")[1]
    info = re.split(" +", ln)

    ret = { "total": int(info[1]), 
            "used": int(info[2]), 
            "available": int(info[3])
          }

    return(ret)

  ###############
  ### Private
  ###############

  def _setup_api(self):
    if(self.server):
      url = ''
      if(self.server.startswith('ssh://')):
        url = self.server
      else:
        url = f"tcp://{self.server}:2375"

      self.api = docker.DockerClient(base_url=url)
      self.docker_cmd += ['-H', url]
    else:
      self.api = docker.from_env()


  def _setup_docker_exe(self, docker_exe):
    docker_exe_env = os.getenv("NV_DOCKER_EXE", None)
    if(docker_exe_env):
      logging.info(f"Using Docker exe from NV_DOCKER_EXE: {docker_exe_env}")
      self.docker_cmd = [docker_exe_env]
    elif(docker_exe):
      logging.info(f"Using Docker exe: {docker_exe}")
      self.docker_cmd = [docker_exe]
    else:
      self.docker_cmd = ['docker']


