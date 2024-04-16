
#!/usr/bin/env python

import sys
import docker
import os
import subprocess
import nvidia.docker

import re

from pprint import pprint

class Service:
  ##############
  ### Public
  ##############

  def __init__(self, conn, svc, **kwargs):
    self.__conn = conn
    self.api = svc
    self.info = kwargs
    self.__ports = None
    self.__ports_map = None

  def ports(self):
    if self.__ports is None:
      self._load_ports()

    return(self.__ports)

  def ports_map(self):
    if not self.__ports_map:
      self._load_ports_map()

    return(self.__ports_map)

  ##############
  ### Private
  ##############

  def _load_ports_map(self):
    self.__ports_map = {}

    if('Endpoint' in self.api.attrs):
      endpoint = self.api.attrs['Endpoint']

      for port in endpoint.get('Ports', []):
        if('PublishedPort' in port and 'TargetPort' in port):
          self.__ports_map[int(port['TargetPort'])] = int(port['PublishedPort'])
#      if('Ports' in endpoint):
#        for(port in endpoint.[
#        source = 
#        self.__ports_m +=  [int(p['PublishedPort'])
#                                for p in endpoint['Ports']
#                                  if 'PublishedPort' in p  ] 
  
  def _load_ports(self):
    self.__ports = []

    if('Endpoint' in self.api.attrs):
      endpoint = self.api.attrs['Endpoint']

      if('Ports' in endpoint):
        self.__ports +=  [int(p['PublishedPort'])
                                for p in endpoint['Ports']
                                  if 'PublishedPort' in p  ] 
