#!/usr/bin/env python3.8

################################################################################
## Libs
################################################################################

import sys
import os 

bin_path = os.path.dirname(os.path.realpath(__file__))

sys.path.append(f"{bin_path}/lib")
sys.path.append(f"{bin_path}/common/lib")

import argparse

import logging

import shutil

from pprint import pprint

import nvidia.docker.registry.argparse

from nvidia.die import die
from nvidia.helm import Helm
from nvidia.helm.chart import Chart, is_chart_dir
from nvidia.sysutils import reset_dir

import nvidia.build.versioning
from nvidia.build.versioning import make_kube_compliant_version

################################################################################
## Globals
################################################################################

description = "HELM Chart dependencies' update tool"
args = None

#work_dir = f"{bin_path}/__helm_publish"

#class defaults:
#  family = 'local'
#  no_version = 'no_version'
#  default_release="private"
#  default_version_file="../../../VERSION.md" # relative to HELM chart
#  repo_root_rel="../../.." # relative to HELM chart

helm = None 

################################################################################
## Init
################################################################################

def init():
  nvidia.die.log_instead_of_stderr()

  logging.basicConfig(format="%(message)s", level=logging.INFO)

  global helm 
  helm = Helm()

  parse_args()

################################################################################
## Main
################################################################################

def main():
  if(not is_chart_dir(args.chart_path)):
    die(f"{args.chart_path} is not a Helm chart!")

  logging.info(f"Updating dependencies in: {args.chart_path}")
  chart = Chart(path=args.chart_path)
  res = helm.update_deps(chart, user=args.user, pwd=args.password)
  if(res is None):
    logging.info("    > chart has no dependencies") 
  else:
    logging.info(f"    > updated {res} dependencies")
        
################################################################################
## Functions
################################################################################

def parse_args():
  argparser = argparse.ArgumentParser(description=description)

  argparser.add_argument("chart_path", metavar="path", default=None,
                         help="Chart location")

  argparser.add_argument("-u", "--user", metavar="username",
                         default='$oauthtoken',
                         dest="user", 
                         required=0,
                         help=f"Username (login) for registry, default "
                              f"$oauthtoken " + 
                              f"(can also use OMNI_HP_USER)"
                        )

  argparser.add_argument("-p", "--password", metavar="password",
                         default=None,
                         dest="password", 
                         required=0,
                         help=f"Password for registry " + 
                              f"(can also use OMNI_HP_PASSWORD)"
                        )

  global args
  args = argparser.parse_args()

  if(not args.user):
    args.user = os.getenv('OMNI_HP_USER', None)

  if(not args.password):
    args.password = os.getenv('OMNI_HP_PASSWORD', None)


################################################################################
## Execute
################################################################################

init()
main()



