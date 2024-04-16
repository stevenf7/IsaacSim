import sys
import os 

from pprint import pprint

import yaml

import collections


def parse_image_list(src_dir = None):

  ret = {}

  for i in os.listdir(src_dir):
    full_path = os.path.join(src_dir, i)

    if(not os.path.isfile(full_path)):
      continue 
    if(not(full_path.endswith('yaml') or
           full_path.endswith('yml'))):
      continue

    for img in _load_images_from_yaml(full_path):
      ret[img.name] = img

  return(ret)


def _load_images_from_yaml(f):
  ret = []

  for i in _parse_yaml(f):
    img = collections.namedtuple('ImageListItem', 
                                     ['name', 'full_name'])
    img.name = i['name']
    img.full_name = i['full_name']
    ret.append(img)

  return(ret)

def _parse_yaml(f):
  with open(f, 'r') as h:
    y_str = h.read()
  return(yaml.load(y_str, Loader=yaml.FullLoader))
