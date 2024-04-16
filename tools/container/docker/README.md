# Introduction 

This is a band-aid generic toolchain to build and deploy series of Docker Images, 
composing Stacks of Docker Containers. 

This is what we use at the moment to build and run Omniverse and related services. 

## Terminology

* **OV**: I use that sometimes as a short for Omniverse.

* **Docker**: a system to "orchestrate" (build, deploy, run, manage, stop)
  Images, Containers and related stuff (ie, virtual networks) 

* **Container**: think of it as your software "statically linked" against a full OS 
  stack being executed. It's not a VM (hardware is not abstracted); but it's not
  just a "build" either, because it carries literally *everything* your program
  needs. For Linux guys, think of a container as chroot on steroids. 

* **Image**: Containers are runtime objects: Images are "static". Think of it as a
  build. You use an Image to start a Container.

* **Stack**: a set of containers and misc. stuff (ie, configs, data volumes,
  virtual networks) that together make your application. A stack can include
  one or more  *microservices*, each one of which runs in it's own container. 

  For example, OV Stack consists of multiple Redisii, OV API Websockets service,
  Delta Server, et al. 

  One Docker server can run multiple Stacks. 

* **Release**: a string identifying the release (typically, an assigned version). Defaults to `private`.

* **Family**: a string identifying your "line of builds". This toolchain is set
  up such that Stacks are named after your Family, to ensure that you're not
  messing with someone else's Stacks. By default, Family is set to
  `username-hostname`.

* **Author**: "I", "me", etc in this README refers to Fedor 'Fidot' Fomichev :)
  Ping me on Slack or call for questions or issues. 

## What You Need

You will need a couple things before you can begin. 

### Docker Itself 

We run **Stable channel, Community Edition version 18.09.6**. If you're using 
newer versions, you should be fine though things might NOT work as expected, especially 
if you're running a Docker Server. Docker Client versions are less important. 

If you're on Linux, things are easy:

* **Ubuntu**: https://docs.docker.com/install/linux/docker-ce/ubuntu/
* **CentOS**: https://docs.docker.com/install/linux/docker-ce/centos/

Note: do not install default packages of Docker from your distro -- they are old! 

On Windows, a couple options:

* **Docker Toolbox**: https://docs.docker.com/toolbox/toolbox_install_windows/
* **Docker for Windows**: https://docs.docker.com/docker-for-windows/install/

In either case, on Windows, **make sure docker.exe is in PATH**. Also, unless 
you're planning to be deploying to a local machine (99% you won't need that), use 
Docker Toolbox. Read below a note on Windows. 

#### A Word on Windows

On Windows, Docker cheats by running a Linux VM in which it runs it's daemon. 
Docker for Windows does that with HyperV; which is a nice thing, until you realise 
that that converts your *host* OS into a kind of a VM as well, and breaks 
VirtualBox.

Docker Toolbox comes with VirtualBox and supposedly works. I didn't try it, because
my VirtualBox setup is my main work tool and I don't want external programs screwing
with it. Replace this paragraph with your experience if you end up doing that. 

At any rate, you do not *need* the Docker Daemon to build Omniverse -- you can 
just build directly on the sandbox server, which in fact is what I recommend. 
You just need the exe that can talk to the daemon (docker.exe). 

But, my recommendation is to use Linux, regardless. You are an Omniverse Developer, 
aren't you? Your software *will run on Linux*, so why not develop it on Linux to 
begin with, given all the subtle differences in network stacks, IPC, etc? 

In this day and age, VMs are great for having multiple OSs: I have two-three Linux
VMs running on my Windows 10 box pretty much at all times these days.

### Python 3.6

Self explanatory :) **Make sure it's 3.6. If scripts are failing with syntax errors,
that means you're running something else** (verify with *python -V*). 

### py-docker

Just `pip install docker` or `python -m pip install docker`. 

## General Notes

* Make sure that what you're about to build and deploy runs fine locally. I have
  had a lot of grief while setting up this toolchain trying to deploy OV with 
  syn errors - that's not fun (it just never comes up :)). 

* Do not try to use this for debugging things, unless what you're debugging is
  related to Docker / infrastructure / ...

* See the tail of this README for couple of Docker tricks that might help

# Target Servers

Options include:

* Set up your own

* You might already have one allocated by me

# Tools

All tools can (and should) be run with `-h` option to obtain the help screen. 

* **build.py** for building
* **deploy.py** for deploying

# Quick Flow Covering 99% of Situations

    # Point Docker to ov-stage for docker commands.
    # On Windows, use 'set' instead of 'export'

    export DOCKER_HOST=ov-stage:2375
     
    # Build all images 

    python build.py -s ov-stage ~/my_project/docker/image_configs/* #... or wherever they are

    # Check them out

    docker image ls

    # Deploy a setup with just built images

    python deploy.py -c ~/my_project/docker/stack_config/myproject.py -s ov-stage @

    # Check things out

    docker ps
    docker stack ls
    docker service ls

# Building

Building something involves creating a series of images, one per *service*. 
The script in this toolchain is called `build.py`.

Depending on how your project is deployed, you will need a subset or all services 
built. 

Image configs for services would be located with the project you're trying to build.
Check it's READMEs.

If you don't know, you probably need all the images built. 

To build with defaults, just run `python build.py <list of image config files>`. 
Shell wildcards are supported (ie, `python build.py <dir>/*`). 

This will produce a series of images on the server you're
building against, one per config. 

There are options to save images into .tar files for later upload, but that
is not necessary in most cases. 

Note that with all default environment and no other command line options, it will 
try to build locally. 

## Building Using a Remote Docker Daemon

It's much more convenient to build on a remote server. In fact, your typical 
workflow  should be building against the server you're planning to deploy to. 

The only other way would be downloading a just build image (`--save` option) 
and then uploading it to the target server when deploying, which takes time. 

Note that when doing building with remote Docker,  you're still running the
script locally -- it just connects to the remote server to Do The Magic. 

To build against a remote server, you can use `-s <server>` option to the build script, or set `DOCKER_HOST` environment variable to `<server>:2375`.

Setting the environment variable will not only affect `build.py`, but native Docker commands as well, should you be running them. 

Note that there are more command line options -- use `-h` to read about them. 

## Notes to Folks used to `-r`, `-f`,  and `-b` options of `build.py`

With OmniFlow, we're taking a tighter control of versioning.

- Your Release name will be determined from the VERSION.md file located in the root of your repo + branch name 
- Your Build Number will be automatically assigned 
- Your Family will be automatically assigned by the CI system.
  
  - Note: `-f` and `-no` options (`family` and `build number`) options are intended for CI use ONLY. 
    If you are not building a CI pipeline, you should not be using them. 

In other words, do not use these options anymore. 

# Deploying

Deploying will run your set of services in a Stack. Default Stack Name
will be `<stack name>-<stack suffix>`, where Stack Name comes from Stack Config
file provided with a project, and Suffix is the Image Family. 

Deploying is done with `deploy.py`. 

Note that this script **does not honor DOCKER_HOST environment var**.

Similarly to `build.py` requiring image configs, `deploy.py` requires
a Stack Config - which defines what to deploy and how. Check the project you're trying to deploy for where this might be.  

If the target Stack already exists, it will shut old one down first, and reuse the
ports (since we can have multiple Stacks on one Docker Host, different Stacks
will use different Host Ports to expose OV services).

To successfully deploy your instance, you will need at least images for all the 
required services, and specify them when deploying. If you're not sure 
which ones you need, you probably want to build and deploy all services. 

Simple invocation is `python deploy.py -c <stack config> -s <server> <image list>`.
`-t` option will run unit tests after the Stack comes up, if configured in Stack
Config. `<image list>` should be a space-separated
list of image names or .tar files (mixing is okay). Note that if you specify 
multiple images for the same service, `deploy.py` will fail. 

To use a set of images you built most recently (which will be 99% of the time), 
use `@` (ie, `python deploy.py -c <config> -s <server> @`). Note that you
can *still* specify other images as well in addition to `@`.

If you want to destroy old data when deploying new version of your Stack, use `-r`. 

Unless you know exactly what you're trying to do, **do not deploy to any VMs categorized as 'production'**. Be careful and nice to others. There are no ACLs. 

Note that there are more command line options -- use `-h` to read about them. 

# Docker Tricks

Before trying to go lower-level and debug stuff in Docker, make sure you're
doing that against the right server (DOCKER_HOST env var set properly). 

If you have your own setup (you are on Linux, right? ;) ), do it there. 

* `docker ps` lists all running containers. First item in line is container ID -
  you will need it if you want to "get in". To find your OV container, look for
  "omniverse:YOUR_FAMILY" in IMAGE column, or grep for it. 

* `docker exec -it <container ID>  bash` will put you into bash inside
  the container with CONTAINER_ID. This is helpful when you want to try to debug 
  things or look around. Note that a lot of things you're used to might be missing -
  use whatever package manager is used by the base image to install them. 

* `docker images` lists all images. List will be long, so grep (or head; newer 
  images will be at the top of the list). You will need your image ID for below. 

* If your container doesn't start (ie, you're sitting with deploy.py 
  waiting for your container to come up for minutes), you can try running it 
  manually with bash inside and seeing what's wrong. 
  Use `docker run -it <image ID> bash` will start a container from 
  `<image ID>` and run bash in it.

* `docker stack ls` lists all stacks. 

* `docker stack rm <stack name>` will stop all containers, services, networks
  in that stack. This is a good way to "start from scratch" if the deploy.py 
  can't handle stopping that stack (unlikely; but possible). Note that it takes a 
  while to stop a stack (keep running `docker ps` and wait till everything
  pertaining to your stack is gone)

# Making your own Image and Stack Configs

Both `build.py` and `deploy.py` are generic - meaning they don't care about what 
they build or deploy. They're essentially nice wrappers to Dockerfiles and
Docker Compose files and Docker commands, implementing certain 'policies'
(ie, where data comes from, how things are named, etc etc etc) and automating 
things for you. 

They're also nice for *users* that want to deploy their own stuff - users can 
use these with virtually no Docker knowledge. 

**If you do not know what Stack Compose, and Dockerfiles, are, you need to brush up
a bit on Docker. Not fundamentally understanding what's going on will cause lots
of grief.** Below assumes you know your way around Docker at least a bit. 

## Image Configs for build.py

The main goal of an Image Config is to produce a Dockerfile.

* Defines `service_name` - this will become Image Name, and Service, and will
  be used by Deploy, too
* Defines code root
* Defines which files from Code Root should be copied to build context 
  (we're trying to keep those minimal) 
* Defines `dockerfile()` function that should return a Dockerfile string

## Stack Configs for deploy.py

Ultimate purpose of a Stack Config is to provide the Compose file for the stack, 
and the `test()` function. 

* Defines which services (images) are Required, Optional, and BuiltIn
* Defines Stack Name (it will be essentially the name *prefix*, with suffix being the Family by default)
* Defines which host ports can be mapped to Services needing them 
* Defines which dirs to create on the host, in the dir allocated for this Stack
* Defines `get_compose()` that should return the Compose string
* Defines `wait_for_ping()` which does a quick check of things to make sure they
  bootstrap fine
* Defines `test()` which can be a heavy post-deploy test (ie, run unit tests)
* Defines `print_welcome()` that's useful for end users - ie, how to connect 
  to things 

## Samples

* Simple HTTP server written in Python in `samples/simple_http_server` of this repo. Image and stack configs in `conf/`.
* A sophisticated example is the  Omniverse API Server (`omniverse/backend` repo, `docker/image_configs` and `docker/stack_configs`.

### Notes on Builtin vs. Required Services

Stack Config can contain both, and there might be some confusion for why there
are two kinds. 

They are both *required* for the Stack to be deployed, but they come from different
sources.

This is historic, and still very useful. 

* A Required service would be one of the services coming as an artifact of `build.py`. That would be one of your microservices, ie, an API Backend server, or something similar. This would be a service that gets re-built often and has it's code changing.
* A Built-in is something that's typically coming verbatim from Docker Hub, ie, 
  in the  case of Omniverse, Redis would be a built-in. Yes, I still need a 
  `redis.conf` for it; but I can do that via the `config:` Compose option
  rather than having to build "my own Redis" with a 2-line Dockerfile. 

Another way to look at it is Images for Built-Ins are provided as a part of the 
Stack Config, while Images for Required Services are provided on command line to 
`deploy.py`.

On the high level, something that changes all the time should be a Required 
(or Optional) service, with image coming on the command line to `deploy.py`. 
Something that's "default", or changes very rarely, can be a Built-In. 

BTW, by default `deploy.py` doesn't know how to obtain built-ins if they're 
missing, and will just fail, even if it's just a simple pull. To fix this, define
`builtins_bootstrap_funcs` in your Stack Config with function hooks to obtain them. Omniverse Backend's `docker/stack_configs/omniverse.py` is a very good example 
of that, where one bootstrap function downloads an image, and another actually builds it. 
