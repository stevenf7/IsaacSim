#!/usr/bin/python3.6

################################################################################
## Libs
################################################################################

import logging
import os
import sys
from pprint import pprint

################################################################################
## Globals
################################################################################

class Defaults:
  prefixes = { "docker": 'nvcr.io', 
               "helm":   'https://helm.ngc.nvidia.com'
             }

  def __init__(self, type="docker"):
    prefix = self.prefixes[type]

    self.cesspool_reg = f"{prefix}/omniverse/cesspool"
    self.all_cesspool_regs = dict(
          [ (t, f"{self.prefixes[t]}/omniverse/cesspool") 
                                            for t in self.prefixes.keys() ])

    self.internal_reg = f"{prefix}/omniverse/internal"
    self.all_internal_regs = dict(
          [ (t, f"{self.prefixes[t]}/omniverse/internal") 
                                            for t in self.prefixes.keys() ])

    self.public_reg = f"{prefix}/omniverse/public"
    self.all_public_regs = dict(
          [ (t, f"{self.prefixes[t]}/omniverse/public") 
                                            for t in self.prefixes.keys() ])


    self.prerel_reg = f"{prefix}/omniverse/prerel"
    self.all_prerel_regs = dict(
          [ (t, f"{self.prefixes[t]}/omniverse/prerel") 
                                            for t in self.prefixes.keys() ])

    self.ove_reg = f"{prefix}/nvidia/omniverse"
    self.all_ove_regs = dict(
          [ (t, f"{self.prefixes[t]}/nvidia/omniverse") 
                                            for t in self.prefixes.keys() ])

    self.ops_reg = f"{prefix}/omniverse/ops"
    self.all_ops_regs = dict(
          [ (t, f"{self.prefixes[t]}/omniverse/ops") 
                                            for t in self.prefixes.keys() ])


def add_registry_args(argparser, target_arg=None, type="docker", **kwargs):
  assert(target_arg is not None)

  defaults = Defaults(type=type)

  argparser.add_argument("-r", "--registry", metavar="URL",
                          default=None,
                          dest=target_arg, 
                          help="Registry URL")

  argparser.add_argument("-ri", "--internal",
                          default=False, action='store_true',
                          dest="__use_internal_reg", 
                          help="Use default Internal Releases registry: " + 
                               defaults.internal_reg)

  argparser.add_argument("-rp", "--public",
                          default=False, action='store_true',
                          dest="__use_public_reg", 
                          help="Use default Public Releases registry: " +   
                                defaults.public_reg)

  argparser.add_argument("-rc", "--cesspool",
                          default=False, action='store_true',
                          dest="__use_cesspool_reg", 
                          help="Use default Cesspool registry: "  +     
                               defaults.cesspool_reg)

  argparser.add_argument("-rpre", "--prerel",
                          default=False, action='store_true',
                          dest="__use_prerel_reg", 
                          help="Use default PreRel registry: "  +     
                               defaults.prerel_reg)

  argparser.add_argument("-rove", "--public-ove",
                          default=False, action='store_true',
                          dest="__use_ove_reg", 
                          help="Use default Public OVE registry: "  +     
                               defaults.ove_reg)

  argparser.add_argument("-ro", "--ops",
                          default=False, action='store_true',
                          dest="__use_ops_reg", 
                          help="Use default Ops registry: "  +     
                               defaults.ops_reg)

def parse_registry_args(args, target_arg=None, type="docker",
                        registry_by_type_target=None, **kwargs):
  assert(target_arg is not None)

  defaults = Defaults(type=type)

  total_default_registries = 0
  if(args.__use_internal_reg):
    total_default_registries += 1
  if(args.__use_cesspool_reg):
    total_default_registries += 1
  if(args.__use_public_reg):
    total_default_registries += 1
  if(args.__use_ops_reg):
    total_default_registries += 1
  if(args.__use_ove_reg):
    total_default_registries += 1
  if(args.__use_prerel_reg):
    total_default_registries += 1

  if(total_default_registries and getattr(args, target_arg)): 
    return("You have provided both a registry URL as well as "+ 
            "requested to use a default registry. Please fix")

  if(total_default_registries > 1):
    return("You have requested to use multiple registries. " + 
            "You can only pick one.")

  selected_reg = getattr(args, target_arg)
  selected_reg_all_types = None

  if(args.__use_internal_reg):
    selected_reg = defaults.internal_reg
    selected_reg_all_types = defaults.all_internal_regs
  elif(args.__use_public_reg):
    selected_reg = defaults.public_reg
    selected_reg_all_types = defaults.all_public_regs
  elif(args.__use_cesspool_reg):
    selected_reg = defaults.cesspool_reg
    selected_reg_all_types = defaults.all_cesspool_regs
  elif(args.__use_ops_reg):
    selected_reg = defaults.ops_reg
    selected_reg_all_types = defaults.all_ops_regs
  elif(args.__use_ove_reg):
    selected_reg = defaults.ove_reg
    selected_reg_all_types = defaults.all_ove_regs
  elif(args.__use_prerel_reg):
    selected_reg = defaults.prerel_reg
    selected_reg_all_types = defaults.all_prerel_regs
  
  setattr(args, target_arg, selected_reg)

  if(registry_by_type_target):
    setattr(args, registry_by_type_target, selected_reg_all_types)

  return(None)
