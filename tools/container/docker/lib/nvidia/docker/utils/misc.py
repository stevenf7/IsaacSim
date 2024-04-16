#!/usr/bin/python3.10

import logging
import os
import sys
from pprint import pprint

from nvidia.die import die


def get_images_list(args=[], tools_ctx=None, docker=None, skips=[]):
  assert(len(args))
#  assert(tools_ctx is not None)

  if('@' in args):
    if(len(args) != 1):
      die("You can't provide other image args if using @")

  if('-' in args and len(args) != 1):
    die("You can't provide other image args if using -")

  ret = []

  if('@' in args):
    ret = get_most_recent_list(tools_ctx)
    return(ret)

  if('-' in args):
    ret = get_list_from_stdin(docker, skips)
    return(ret)

  for i in args:
    logging.info(f"Parsing '{i}'")
    image_name = i

    if(docker.image_exists(full_name=image_name)):
      logging.info(f"  > found {image_name}")
      ret.append(image_name)
    else:
      logging.error("Can't find image corresponding to this arg")
      sys.exit(1)

  return(ret)

def get_most_recent_list(tools_ctx=None, docker=None):
  assert(tools_ctx)
  assert(docker)
  assert(os.path.isdir(tools_ctx))

  logging.info("Loading most recent image list from {tools_ctx}...")
  ret = []

  files = [ _ for _ in  os.listdir(tools_ctx) 
              if _.startswith("__most_recent_image_") ]

  for f in files:
    image_name = rf(os.path.join(tools_ctx, f))

    logging.info(f"> found marker file at: {f}")
    logging.info(f" > {image_name}")
    
    if(not docker.image_exists(full_name=image_name)):
      die("  not found, can't proceed")
    else:
      logging.info("  found")
      
    ret.append(image_name)
  return(ret)

def rf(f):
    ret = ''
    with open(f, 'r') as h:
      ret  = h.read().lstrip().rstrip()
    return(ret)

def get_list_from_stdin(docker, skips=[]):
  logging.info("Loading list of images from STDIN...")
  ret = []

  import json 
  info = json.load(sys.stdin)

  errors = 0
  
  for i in info.get('images', []):
    name = i['image']
    if(i['service_name'] in skips):
      logging.info(f"  > skipping {name}")
      continue
    elif(docker.image_exists(full_name=name)):
      logging.info(f"  > found  {name}")
      ret.append(name)
    else:
      logging.info(f"  > {name} not found")
      errors += 1
    
  if(errors):
    die("Some images weren't found, can't proceed")
  return(ret)

