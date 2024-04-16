#!/usr/bin/env python


################################################################################
## Libs
################################################################################

import os
import sys

bin_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, bin_path + "/../../common/pylib")
sys.path.insert(0, bin_path + "/../../pylib")

import argparse
import subprocess
from pprint import pprint

import nvidia.docker

################################################################################
## Globals
################################################################################

always_keep = dict(map(lambda x: (x,x), [ 'centos', 'ubuntu', 'redis', 'tailon']))
docker = None

l_svc = 'com.nvidia.omniverse.service'
l_ver = 'com.nvidia.omniverse.build.version'
l_fam = 'com.nvidia.omniverse.build.family'

################################################################################
## Init
################################################################################

def init():
  global docker
  docker = nvidia.docker.Docker(server=None)

################################################################################
## Main
################################################################################

def main():
  prune_containers()
  prune_images()

  remove_old_images()
    
################################################################################
## Functions
################################################################################

def prune_containers():
  print("Pruning unused containers...")
  subprocess.call(["docker", "container", "prune", "-f"])

def prune_images():
  print("Pruning unused images...")
  subprocess.call(["docker", "image", "prune", "-f"])

def remove_old_images():
  images = docker.api.images.list()

  images_to_delete = []
  images_by_service = {}

  # Load all images by service
  for i in images:
    if(l_svc in i.labels):
      if((l_ver in i.labels) and (l_fam in i.labels)):
        svc = i.labels[l_svc] 
        fam = i.labels[l_fam] 
        ver = i.labels[l_ver] 

        image_entry = { 'id': i.id, 
                        'version': ver, 
                        'tag' : "-".join((svc,fam,ver)) }

        if svc not in images_by_service:
          images_by_service[svc] = {}

        if fam not in images_by_service[svc]:
          images_by_service[svc][fam] = []

        images_by_service[svc][fam].append(image_entry)
      else:
        image_name = i.tags[0]
        print(f"{image_name}: weird labels, will delete")
        images_to_delete.append({ 'id' : i.id, 'tag' : image_name })
    else:
      if(len(i.tags)):
        print(f"Skipping {i.tags[0]}: not an OV service image")
      else:
        print(f"Skipping {i.short_id}: not an OV image")

  # Sort, exclude the first image in each one of the svc-family combo, and 
  # put the rest of them in the "to delete" list 

  for svc in images_by_service.keys():
    for fam in images_by_service[svc]: 
       images = sorted(images_by_service[ svc ][ fam ], 
                       key = lambda k: k['version'], reverse=True)
       popped = images.pop(0)

       print(f"Skipping {popped['tag']}: most recent image of {svc}-{fam}")
       images_to_delete.extend(images)

  for i in images_to_delete:
    print(f"Deleting {i['tag']}")
    try:
      docker.api.images.remove(image=i['id'])
    except:
      print("   ... failed")
      


################################################################################
## Execute
################################################################################

init()
main()



