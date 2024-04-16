#!/usr/bin/env python3.6

# Copyright (c) 2018-2019, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

################################################################################
## Libs
################################################################################

# standard library modules
import argparse
import logging
import os 
import re
import subprocess
import sys
import time
from typing import List

# local/proprietary modules
bin_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, bin_path + "/../pylib")
import nvidia.docker 

################################################################################
## Globals
################################################################################

description = "Smart Docker cleanup tool"
args = None

keep_images = set(['centos:7', 
                  'tailon2:latest', 
                  'ubuntu:16.04',
                  'redis:4.0',
                  ]
                 )

conn = None

gigs = 1048576 # df outputs in KILOBYTES

################################################################################
## Init
################################################################################

def init():
  logging.basicConfig(format="%(message)s", level=logging.INFO)
  parse_args()

  global conn
  conn = nvidia.docker.Docker(server=args.server, docker_exe=args.docker)


################################################################################
## Main
################################################################################

def main():
  purge_docker_entities("service ls", "service rm")
  purge_docker_entities("ps", "container stop")
  purge_docker_entities("config ls", "config rm")
  purge_docker_entities("container ls -a", "container rm")

  disk_info = conn._host_diskinfo()
  free = disk_info['available'] / gigs

  logging.info("Free space available: %.2f gigs" % (free))

  while(free < args.target_freespace):
    to_clean = args.target_freespace - free
    cleaned = False

    logging.info("Need to clean up %.2f gigs" % ( to_clean ))

    image_info = get_image_info()

    for (im_id, sz) in image_info:
      logging.info(f"  > deleting {im_id} (%.2f GB)" % (sz))
      cmd = _get_docker_cmd()
      cmd.extend(['image', 'rm', im_id])
      ret = subprocess.call(cmd)
      if(ret):
        # Could fail with "image has dependent child images"
        # This isn't a fatal error, keep trying to remove other images
        logging.warn(f"Cmd {cmd} failed with {ret}")
      else:
        to_clean -= sz
        cleaned = True
      if(to_clean <= 0):
        break 

    free = conn._host_diskinfo()['available'] / gigs

    if (free < args.target_freespace) and not(cleaned):
      raise Exception("Cleaned everything we could, but still not enough free space")

  logging.info("Done.")

################################################################################
## Functions
################################################################################

def get_image_info():
  cmd = _get_docker_cmd()
  cmd.extend(['images',
#         '-a', 
         '--format','{{.ID}} {{.Repository}} {{.Tag}} {{.Size}}'
        ])
  ret = subprocess.run(cmd, stdout=subprocess.PIPE)
  if(ret.returncode):
    raise Exception(f"{cmd} terminated with {ret.returncode}")

  out = ret.stdout.decode('ascii').split("\n")
  out.pop() # Last \n in the list generates an empty item in the list
  out = list(reversed(out))

  dividers = { 
              'KB': 1048576, 
              'MB': 1024, 
              'GB': 1,
             }
  
  ret = []

  for item in out:
    (im_id, im, tag, sz) = item.split(" ")
    im_name = f"{im}:{tag}"

    if(im_name in keep_images):
      continue

    match = re.match("(\d+)(\.\d+)?", sz)
    sz_no = match.group()

    match = re.match(".*\d+(\w+)$", sz)
    sz_divider = match.group(1)

    if(sz_divider not in dividers):
      raise Exception(f"Divider for '{sz_divider}' unknown")
    
    ret.append( (im_id,  float(sz_no) / dividers[sz_divider] ) )

  return(ret)

def purge_docker_entities(enum, rm):
  logging.info(f"Purging entities enumerated by 'docker {enum}'")

  docker_cmd_str = ' '.join(_get_docker_cmd())

  while(1):
    ret = run_cmd_with_stdout(f"{docker_cmd_str} {enum} -q")
    if (not ret):
      break

    subprocess.call(f"{docker_cmd_str} {enum} -q | xargs {docker_cmd_str} {rm}", shell=1)
    time.sleep(0.5)

def run_cmd_with_stdout(cmd):
  cmd = cmd.split(' ')
#  cmd.append('-q')
  ret = subprocess.run(cmd, stdout=subprocess.PIPE)
  if(ret.returncode):
    raise Exception(f"{cmd} terminated with {ret.returncode}")

  return(ret.stdout.decode('ascii'))

def parse_args():
  argparser = argparse.ArgumentParser(description=description)

  argparser.add_argument("--free", metavar="GIGS", 
                         default=None,
                         required=1,
                         dest="target_freespace",
                         help="Amount of gigs of free space required")

  argparser.add_argument("--docker", metavar="docker_client",
                          default="docker",
                          dest="docker",
                          help='Path to docker client (defaults to "docker")')

  argparser.add_argument("-s", "--server", metavar="server",
                          default=None,
                          dest="server",
                          help="Docker server to use (defaults to environment)")

  global args
  args = argparser.parse_args()
  args.target_freespace = float(args.target_freespace)


def _get_docker_cmd() -> List[str]:
  cmd = [args.docker]
  if args.server:
    cmd.extend(['-H', args.server])
  return cmd


################################################################################
## Execute
################################################################################

init()
main()



