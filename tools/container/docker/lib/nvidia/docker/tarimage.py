
#!/usr/bin/env python

import sys
import docker
import os
import subprocess

import tarfile

import json

from pprint import pprint

class TarImage:
  
  path = None

  metadata_json = None
  config_json = None

  _tag = None
  _labels = None

  populated = False

  def __init__(self, path, **kwargs):
    self.path = path

  def tag(self):
    self.populate()
    return self._tag

  def labels(self):
    self.populate()
    return self._labels

  def label(self, name):
    self.populate()
    return self._labels[name]

  def populate(self):
    if(self.populated):
      return

    with tarfile.open(self.path, 'r') as image_tar:
      metadata = json.loads(image_tar.extractfile('manifest.json').read())[0]

      tags = metadata['RepoTags']
      if(len(tags) != 1):
        raise Exception("Looks like this tarball has more than one RepoTags. " +
                        "I don't know how to process these.")

      self._tag = tags[0]

      config = json.loads(image_tar.extractfile(metadata['Config']).read())

      self._labels = config['config']['Labels']

    self.populated = True

