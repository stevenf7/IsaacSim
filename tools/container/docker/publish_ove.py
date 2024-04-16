#!/usr/bin/env python3.10

################################################################################
## Libs
################################################################################

import sys
import os 

bin_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(bin_path, "common/lib"))
sys.path.append(os.path.join(bin_path, "lib"))

import nvidia.config
import nvidia.docker.registry.argparse

from nvidia.die import die

from nvidia.sysutils import push_dir_pos, pop_dir_pos
import argparse
import logging
import nvidia.git as git

from pprint import pprint

################################################################################
## Configuration
################################################################################

config_defaults = """
  versions: 
    core: 0.0.0
    disco: 0.0.0
    auth: 0.0.0
    search: 0.0.0
    thumbs: 0.0.0
    tags: 0.0.0
    nav: 0.0.0
    ingress: 0.0.0

  repos:
    core: backend
    disco: nucleus/discovery
    auth:  nucleus/auth
    search:  nucleus/search
    thumbs:  nucleus/thumbnails
    tags:  nucleus/tagging
    nav:  nucleus/navigator
    ingress:  nucleus/ingress-router

  settings:
    publish_tool: docker/tools/republish.py
    source_registry: nvcr.io/omniverse/cesspool
    server: stagevm-6.ov.nvidia.com
"""

################################################################################
## Globals
################################################################################

description =( "Publish slates of stuff to NGC " + 
               "(set OMNI_CONFIG_PATH for services' config)")

args = None
config = None

################################################################################
## Init
################################################################################

def init():
  logging.basicConfig(format="%(message)s", level=logging.INFO)
  parse_args()

  global config
  config = nvidia.config.configure(config_defaults)

################################################################################
## Main
################################################################################

def main():
  services = []
  if('_all') in args.services:
    services = config.repos._asdict().keys()
  else: 
    services = args.services

  for service in services:
    repo = config.repos._asdict().get(service)
    version = config.versions._asdict().get(service)


    logging.info("-"*20)
    logging.info(f"-- {service} --")
    logging.info(f"repo: {repo}")
    logging.info(f"version: {version}")

    svc_dir = os.path.join(args.base_dir, repo)
    git.fetch(svc_dir)
    git.checkout(svc_dir, version)
    git.initmods(svc_dir)

    if(args.do_it):
      logging.info("Publishing!")
      push_dir_pos(svc_dir)
      cmd = [ config.settings.publish_tool, 
              "-sr", config.settings.source_registry, 
              "-s", config.settings.server, 
              "-r", args.registry, 
              "-st", version, 
              "--yes",
              "docker/image_configs/*",
            ]

      cmd_s = " ".join(cmd)
      logging.info(cmd_s)
      ret = os.system(cmd_s) >> 8 
      if(ret):
        die(f"Failed with {ret}")

              

################################################################################
## Functions
################################################################################

def parse_args():
  #TODO add command line arguments here
  argparser = argparse.ArgumentParser(description=description)

  argparser.add_argument("services", metavar="service", nargs='+', 
                         default=[],
                         help="Services to publish (`_all` supported)")

  argparser.add_argument("-b", "--base-dir", metavar="dir",
                         required=1,
                         dest="base_dir", 
                         help="Base dir with repos"
                        )

  argparser.add_argument("--do", 
                          default=False, action='store_true',
                          dest="do_it", 
                          help="Actually publish")

  nvidia.docker.registry.argparse.add_registry_args(argparser, "registry")

  global args
  args = argparser.parse_args()

  err = nvidia.docker.registry.argparse.parse_registry_args(args, "registry")

  if(err):
    logging.error(err)
    sys.exit(1)


################################################################################
## Execute
################################################################################

init()
main()



