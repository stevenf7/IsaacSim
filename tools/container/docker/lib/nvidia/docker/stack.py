#!/usr/bin/env python

import os
import re
import subprocess
import sys
from pprint import pprint

import docker
import nvidia.docker

from .service import Service


class Stack:

  name = None
  __conn = None
  __services = None

  ##############
  ### Public
  ##############
 

  def __init__(self, conn, name, **kwargs):
    self.name = name
    self.__conn = conn

  def services(self):
    if self.__services is None:
      self.refresh()

    return(self.__services)

  ##############
  ### Private
  ##############

  def refresh(self):
    self.__services = []

    services_info = self.get_service_info() 
    if not len(services_info):
      return

    id_len = len(services_info[0]['id'])

    docker_services = dict((s.id[:id_len], s) 
                            for s in self.__conn.api.services.list())

    

    for svc_info in services_info:
      self.__services.append(Service(self.__conn,
                                     docker_services[svc_info['id']], 
                                     **svc_info))

    return

  def get_service_info(self):
    svc_enum_cmd = self.__conn.docker_cmd + ['stack', 'services', self.name]

    ret = subprocess.run(svc_enum_cmd, stdout=subprocess.PIPE)
    if(ret.returncode):
      raise Exception(f"Enumerating services failed with non-zero "
                       "exit code ({ret.returncode})")

    svcs = []
    length = None

    for ln in (ret.stdout.decode('ascii').split("\n")[1:]):
      if(re.match("^ *$", ln)):
        continue

#      (svc_id, name, mode, replicas, image, ports) = re.split(" +", ln)
      split = re.split(" +", ln) 
      svc_id = split[0]
      name = split[1]
      mode = split[2]
      replicas = split[3]
      image = split[4]
      (up_cnt, tot_cnt) = replicas.split("/")

      svc = {
             'id': svc_id,        
             'name': name, 
             'mode': mode,
             'n_up': int(up_cnt),
             'n_required': int(tot_cnt), 
             'image_name':  image, 
            }
      svcs.append(svc)

    return(svcs)
