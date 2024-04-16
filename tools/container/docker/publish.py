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

import json 

################################################################################
## Globals
################################################################################

description = "Publishes Images to Registries"
args = None

docker = None

VERSION = "1.2.0"

class defaults:
  version_file = os.path.abspath(os.path.join(bin_path, "../../VERSION.md"))


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
  images_to_upload = get_images_list()

  publish_report = {
      "images_from": args.server if args.server else "__local__",
      "publish_py_version": VERSION, 
      "command_line": " ".join(sys.argv),
      "target_registry": args.registry, 
      "images": []
    }

  logging.info("The following images will be published")
  logging.info("--------------------------------------")
  for entry in images_to_upload:
    i = entry['image']

    report_entry = dict(entry.items())
    report_entry['published_tags'] = []
    report_entry['published_urls'] = []

    logging.info(i)
    if(args.extra_tags):
      (n, t) = i.split(":")
      report_entry['published_tags'].append(t)
      report_entry['published_urls'].append(f"{args.registry}/{i}")

      for t in args.extra_tags:
        logging.info(f"  +{n}:{t}")
        report_entry['published_tags'].append(t)
        report_entry['published_urls'].append(f"{args.registry}/{n}:{t}")

    publish_report['images'].append(report_entry)

  logging.info("--------------------------------------")
  logging.info("Target registry:")
  logging.info("--------------------------------------")
  logging.info(args.registry)
  logging.info("--------------------------------------")
  if not(yesno("Proceed? ")):
    sys.exit(1)

  for entry in images_to_upload:
    i = entry['image']
    logging.info('-'*79)
    logging.info(i)
    logging.info('-'*79)
    docker.push_image(i, args.registry, 
                      dots=1, 
                      additional_tags=args.extra_tags)
  
  if(args.update_chart):
    update_chart()

  if(args.generate_report):
    print(json.dumps(publish_report, indent=2))

################################################################################
## Functions
################################################################################

def update_chart():
  logging.info("--------------------------------------")
  values_file = os.path.join(args.chart_path, "_images.yaml")
  logging.info(f"Updating chart's images at {values_file}")
  tag = args.extra_tags[0]
  logging.info(f"Using tag `{tag}`")

  values_str = f"""
image: 
  registry: {args.registry}
  tag: {tag}
"""
  with open(values_file, 'w') as h:
    h.write(values_str)

  logging.info("done.")
  logging.info("--------------------------------------")

def get_most_recent_list():
  logging.info("Loading most recent image list...")
  ret = []

  files = [ _ for _ in  os.listdir(bin_path) 
              if _.startswith("__most_recent_image_") ]

  for f in files:
    image_name = rf(os.path.join(bin_path, f))

    logging.info(f"> found marker file at: {f}")
    logging.info(f" > {image_name}")
    
    if(not docker.image_exists(full_name=image_name)):
      logging.error("  not found, can't proceed")
      sys.exit(1)
    else:
      logging.info("  found")
      
    if not(args.publish_all):
      if(not yesno("  would you like to add it to the list?  ")):
        continue

    ret.append(image_name)
    
  return(ret)

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



def get_images_list():
  ret = []

  if('@' in args.images):
    ret = get_most_recent_list()
    return(make_image_list(ret))

  if('-' in args.images):
    ret = get_list_from_stdin()
    return(ret)

  for i in args.images:

    logging.info(f"Parsing '{i}'")
    image_name = get_image_name(i)

    if(docker.image_exists(full_name=image_name)):
      logging.info(f"  > found {image_name}")
      ret.append(image_name)
    else:
      logging.error("Can't find image corresponding to this arg")
      sys.exit(1)

  return(make_image_list(ret))

def make_image_list(images):
  ret = []
  for i in images:
    ret.append({ "service_name": "__unknown__", 
                 "image_id": "__unknown__", 
                 "image": i })

  return(ret)
    

def get_list_from_stdin():
  logging.info("Loading list of images from STDIN...")
  logging.warn("!!! NOTE !!! Interactive prompts disabled")
  ret = []

  info = json.load(sys.stdin)

  ret = info.get('images', [])

  for i in ret:
    name = i['image']
    if(docker.image_exists(full_name=name)):
      logging.info(f"  > found  {name}")
#      ret.append(name)
    else:
      logging.info(f"  > {name} not found, can't proceed")

  return(ret)

def get_image_name(s):
#  if(args.use_last_name_spec):
#    return(load_last_image_name(s))
#  else:
    return(s)

def load_last_image_name(s):
  mri_file = os.path.join(bin_path, f"__most_recent_image_{s}")
  if(os.path.isfile(mri_file)):
    return(rf(mri_file))
  else:
    logging.error(f"Most recent image entry for '{s}' not found")
    logging.error(f"(looked in {mri_file})")
    sys.exit(1)

def rf(f):
    ret = ''
    with open(f, 'r') as h:
      ret  = h.read()
    return(ret)


def parse_args():
  argparser = argparse.ArgumentParser(description=description)

  argparser.add_argument("images", metavar="image", nargs='+', default=None,
                         help="Images to publish. @ means all last built " + 
                              "ones, and will interactively ask if to "+
                              "publish each one."
                        )

  argparser.add_argument("-s", "--server", metavar="server",
                          default=None,
                          dest="server", 
                          help="Docker server to use (defaults to environment)")

  argparser.add_argument("--ssh", 
                          default=False, action='store_true',
                          dest="ssh", 
                          help="Use SSH to connect to Docker"
                        )

  argparser.add_argument("-dv", "--add-default-version-tag", 
                         action='store_true', 
                         default=False,
                         dest="add_default_version_tag", 
                         help=f"Add version tag from {defaults.version_file}"
                        )

  argparser.add_argument("-t", "--tag", 
                          action='append',
                          metavar="<tag>",
                          default=[],
                          dest="extra_tags", 
                          help="Add extra tags (multiples okay)",
                        )

  argparser.add_argument("-uc", "--update-chart", 
                          action='store_true',
                          default=0,
                          dest="update_chart", 
                          help= ( "If chart is present, update registry and "
                                  "tag information in it's _images.yaml" )
                        )

  argparser.add_argument("--report", 
                         default=0, 
                         action="store_true", 
                         dest="generate_report", 
                         help="Produce report on published images to " + 
                             f"STDOUT in JSON",
                        )


  chart_path = os.path.realpath(f"{bin_path}/../helm/chart")
  argparser.add_argument("--chart-path",  metavar="dir",
                          default=chart_path,
                          dest="chart_path", 
                          help=f"Path to Helm chart (default {chart_path})")

  argparser.add_argument("--yes", 
                          default=False, action='store_true',
                          dest="yes", 
                          help="Do not ask for confirmations"
                        )

  argparser.add_argument("--all", 
                          default=False, action='store_true',
                          dest="publish_all", 
                          help="Publish all images w/o asking about each one "+
                               "!!dangerous!!")

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

  if('@' in args.images and len(args.images) != 1):
    logging.error("You can't provide other image args if using @")
    sys.exit(1)

  if('-' in args.images and len(args.images) != 1):
    logging.error("You can't provide other image args if using -")
    sys.exit(1)

  if(args.add_default_version_tag):
    args.extra_tags.append(load_default_version())

  if(args.update_chart):
    if(not(len(args.extra_tags))):
      logging.error("You asked me to update the Chart, but haven't provided")
      logging.error("any common tags to use for images. Can't do that.")
      sys.exit(1)
    if(not(os.path.isfile(f"{args.chart_path}/Chart.yaml"))):
      logging.error(f"Chart.yaml not found at {args.chart_path}")
      logging.error("Chart path seems to be incorrect - can't update")
      logging.error("chart's images.")
      sys.exit(1)

def load_default_version():
  logging.info("Attempting to load default version from " +
               defaults.version_file)

  if not(os.path.isfile(defaults.version_file)):
    logging.error("File not found, can't continue")
    sys.exit(1)

  with open(defaults.version_file, 'r') as h:
    version = h.read().rstrip().lstrip()


  if not(len(version)):
    logging.error("Read an empty string, can't continue")
    sys.exit(1)

  logging.info(f"  > {version}")

  return(version)
  
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
