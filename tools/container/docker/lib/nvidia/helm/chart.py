import logging
import os
import sys
from pprint import pprint

import ruamel.yaml
from nvidia.die import die
from nvidia.helm import Helm
from nvidia.kube.helpers import is_valid_label_value
from ruamel.yaml import YAML


def is_chart_dir(dir=None):
  assert(dir)
  return(os.path.isfile(os.path.join(dir, 'Chart.yaml')))


class Chart:
  def __init__(self, path=None):
    assert(path)

    if(not(is_chart_dir(path))):
      die(f"{path} is not a Helm  chart")

    self.path = path
    self.values_file = f"{path}/values.yaml"
    self.chart_def_file = f"{path}/Chart.yaml"

#    self._helm = Helm()

  def app_name(self):
   (p, c) = self._read_yaml(self.chart_def_file)
   return(c['name'])

  def set_version(self, version=None, app_version=None):
    assert(version)

    if(not app_version):
      app_version = version

    (p, c) = self._read_yaml(self.chart_def_file)
    c['version'] = version
    c['appVersion'] = app_version
    self._save_yaml(self.chart_def_file, p, c)

  def set_version_full(self, version=None):
    assert(version)

    (p, c) = self._read_yaml(self.chart_def_file)
    c['annotations']['long_version'] = version
    self._save_yaml(self.chart_def_file, p, c)


  def set_images_tag(self, tag=None):
    assert(tag)
#    fixups = self._replace(self.values_file, '__no_tag__', tag)
    (p, v) = self._read_yaml(self.values_file)
    fixups = self._walk_and_replace(v, '__no_tag__', tag)

#    pprint(v)
#    sys.exit(1)
    self._save_yaml(self.values_file, p, v)
    return(fixups)

  def set_registry(self, registry=None):
    assert(registry)

#    return(self._replace(self.values_file, '__no_registry__', registry))

    (p, v) = self._read_yaml(self.values_file)
    fixups = self._walk_and_replace(v, '__no_registry__', registry)
    self._save_yaml(self.values_file, p, v)

    return(fixups)

  def dependencies(self):
    (p,v) = self._read_yaml(self.chart_def_file)
    if('dependencies' not in v):
      return(None)

    ret = []

    for dep in v['dependencies']:
      ret.append({ 'repo': dep.get('repository', None), 
                   'version': dep['version'],
                   'name': dep['name']
                 }
                )
    return(ret)                   

  def deps_dir(self):
    return(os.path.join(self.path, 'charts'))
    
  def dep_repo_urls(self):
    (p, v) = self._read_yaml(self.chart_def_file)
    if('dependencies' not in v):
      return(None)

    ret = {}

    for dep in v['dependencies']:
      ret[dep['repository']] = 1

    return(ret.keys())

  def _walk_and_replace(self, yaml, what, with_what):
    count = 0
    for (k, v) in yaml.items():
      if(isinstance(v, ruamel.yaml.comments.CommentedMap)):
        count += self._walk_and_replace(v, what, with_what)
      elif(isinstance(v, ruamel.yaml.comments.CommentedSeq)):
        for i in v:
          if(i == what):
            die(f"Found a list element set to `{what}`, this is not supported!")
      else:
        if(v == what):
          yaml[k] = with_what
          count += 1

    return(count)

  def _save_yaml(self, f, parser, y):
    with open(f, 'w') as h:
      parser.dump(y, h)

  def _read_yaml(self, f):
    s = ''
    with open(f, 'r') as h:
      s = h.read()

    parser = YAML()
    parser.preserve_quotes = 1
    return(parser, parser.load(s))

  def _replace(self, f, src_str, repl_str):
    assert(f); assert(src_str); assert(len(repl_str))

    ret = 0
    new_file = ''

    with open(f, 'r') as h:
      while(line := h.readline()):
        if(src_str in line):
          ret += 1
          new_file += line.replace(src_str, repl_str)
        else:
          new_file += line

    with open(f, 'w') as h:
      h.write(new_file)

    return(ret)
