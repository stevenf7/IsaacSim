#!/usr/bin/python3.10

################################################################################
## Libs
################################################################################

import sys
import os 

bin_path = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(0, f"{bin_path}/common/lib")
sys.path.insert(0, bin_path + "/lib")

import argparse

import importlib.util

from pprint import pprint
import socket
import getpass
from time import localtime, strftime

import io
import shutil
import re
import subprocess

import glob

import nvidia.docker
import nvidia.docker.registry.argparse
import logging 
import subprocess

import nvidia.config_loader

from nvidia.die import die

import nvidia.gitlab.utils

################################################################################
## Globals
################################################################################

description = "Downloads images from one registry and publishes to another"
args = None

docker = None

class defaults:
  pass


################################################################################
## Init
################################################################################

def init():
  logging.basicConfig(format="%(message)s", level=logging.INFO)

  parse_args()

  global docker
  docker = init_docker_conn()


################################################################################
## Main
################################################################################

def main():
  source_registry = determine_source_registry()
  logging.info(f"Source registry: {source_registry}")

  image_list = get_image_list()

  logging.info("The following images will be processed:") 
  for i in image_list:
    logging.info(f"  > {i}:{args.source_tag}") 

  logging.info("Pulling images")

  to_publish = []

  for i in image_list:
    image_name_full = f"{i}:{args.source_tag}"
    to_pull = f"{source_registry}/{image_name_full}"
    logging.info(f"  > pulling {to_pull}")
    pulled = docker.api.images.pull(to_pull) 
    logging.info(f"  > retagging to local") 
    pulled.tag(i, args.source_tag)

    to_publish.append(image_name_full)

  logging.info("The following images will be published")
  logging.info("--------------------------------------")
  for i in to_publish:
    logging.info(i)
    if(args.extra_tags):
      (n, t) = i.split(":")
      for t in args.extra_tags:
        logging.info(f"  +{n}:{t}")
  logging.info("--------------------------------------")
  logging.info("Target registry:")
  logging.info(args.registry)
  logging.info("--------------------------------------")
  if not(yesno("Proceed? ")):
    sys.exit(1)

  for i in to_publish:
    logging.info('-'*79)
    logging.info(i)
    logging.info('-'*79)
    docker.push_image(i, args.registry, 
                      dots=1, 
                      additional_tags=args.extra_tags)

  sys.exit()

################################################################################
## Functions
################################################################################

def get_image_list():
  logging.info("Determining image list")

  ret = []

  for i in args.images:
    logging.info(f" > processing arg {i}")

    if(os.path.isdir(i)):
      logging.info(f"    > is a dir, skipping")
      continue

    if(os.path.isfile(i)):
      logging.info(f"    > is a file")

      if(not i.endswith("py")):
        logging.info(f"    > not an image config, skipping")
        continue
      
      logging.info(f"    > attempting to load as Image Config")

      config = nvidia.config_loader.get_configs([i])[0]

      if(not hasattr(config.config, 'service_name')):
        die("    > image config does not have 'service_name' in it")

      ret.append(config.config.service_name)
    else:
      logging.info(f"    > not a file, assuming image name")
      ret.append(i)

  return(ret)


def determine_source_registry():
  if(args.source_registry): 
    return(args.source_registry)
  else:
    logging.info("Source registry not specified, attempting to detect "  +
                 "default Gitlab registry")
    return(detect_gitlab_registry())

def detect_gitlab_registry():
  return(nvidia.gitlab.utils.get_gitlab_registry_url())

def yesno(msg):
  if(args.yes):
    return(1)
  if('-' in args.images):
    return(1)

  sys.stderr.write(msg)
  sys.stderr.write("[y/n] ")
  sys.stderr.flush()

  answ = input()

  if(not (answ.lower() == 'y') or
         (answ.lower() == 'yes') ):

    return(0)
  else:
    return(1)



def parse_args():
  argparser = argparse.ArgumentParser(description=description)

  argparser.add_argument("images", metavar="image", nargs='+', default=None,
                         help="Images to re-publish. Can supply names, " + 
                              "or image config paths"
                        )

  argparser.add_argument("-s", "--server", metavar="server",
                          default=None,
                          dest="server", 
                          help="Docker server to use (defaults to environment)")

  argparser.add_argument("-sr", "--source-registry", metavar="source_registry",
                          dest="source_registry", 
                          required = 0,
                          help="Registry to source images from. Default " +
                               "will attempt to determine local project's " + 
                               "registry on Gitlab. !!! If attempting " + 
                               "detection, CWD *has to be* your repo")

  argparser.add_argument("--ssh", 
                          default=False, action='store_true',
                          dest="ssh", 
                          help="Use SSH to connect to Docker"
                        )

  argparser.add_argument("--yes", 
                          default=False, action='store_true',
                          dest="yes", 
                          help="Do not ask for confirmations"
                        )

  argparser.add_argument("-st", "--source-tag", metavar="source_tag",
                          dest="source_tag", 
                          required = 1,
                          help="Source image tag")

  argparser.add_argument("-t", "--tag", 
                          action='append',
                          metavar="<tag>",
                          default=[],
                          dest="extra_tags", 
                          help="Add extra tags (multiples okay)",
                        )

  nvidia.docker.registry.argparse.add_registry_args(argparser, "registry")

  global args
  args = argparser.parse_args()

  err = nvidia.docker.registry.argparse.parse_registry_args(args, "registry")
  if(err):
    logging.error(err)
    sys.exit(1)

  if(not args.registry):
    logging.error("You did not provide target registry.")
    logging.error("Please review available options with `--help` arg, " +   
                  "and make a pick.") 
    sys.exit(1)
  
def init_docker_conn():
  server = None

  if(args.ssh):
    logging.info("Using SSH to connect to server")
    server = f"ssh://{args.server}"
  else:
    logging.info("Using TCP to connect to server")
    server = args.server

  conn = nvidia.docker.Docker(server=server)
  return(conn)

################################################################################
## Execute
################################################################################

init()
main()
