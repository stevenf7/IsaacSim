#!/usr/bin/env python3.6


################################################################################
## Libs
################################################################################

import sys
import os 


from pprint import pprint

bin_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, bin_path + "/../pylib")

import nvidia.docker 

import argparse

################################################################################
## Globals
################################################################################

description = "Simple Docker pinger"
args = None

#docker_server = None

################################################################################
## Init
################################################################################

def init():
  parse_args()

################################################################################
## Main
################################################################################

def main():
  # do something
  print(f"Trying to connect to {args.server}...")

  try:
    conn = nvidia.docker.Docker(server=args.server)
    conn.image_exists(full_name="something")
  except Exception as e:
    print(f"Failed to connect to {args.server}")
    print("@@@DOCKER_FAILURE@@@")
    sys.exit(1)

  print("Seems okay...")
  sys.exit(0)

################################################################################
## Functions
################################################################################

def parse_args():
  argparser = argparse.ArgumentParser(description=description)

  argparser.add_argument("server", metavar="server", default=None,
                         help="Docker server to 'ping'")

  global args
  args = argparser.parse_args()

################################################################################
## Execute
################################################################################

init()
main()



