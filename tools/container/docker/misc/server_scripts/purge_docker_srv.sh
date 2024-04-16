#!/bin/sh 

clean_docker_entities()  {
  LIST_CMD=$1
  RM_CMD=$2
  SLEEP_FOR=$3

  if [ -z $SLEEP_FOR ] 
   then
    SLEEP_FOR=1
  fi


  echo $LIST_CMD $RM_CMD $SLEEP_FOR

  while [ `$LIST_CMD -q | wc -l` -gt 0 ]
  do
    $LIST_CMD
    $LIST_CMD -q | xargs $RM_CMD
    sleep $SLEEP_FOR
  done
}


clean_docker_entities "docker service ls" "docker service rm" 
clean_docker_entities "docker ps" "docker container stop" 
clean_docker_entities "docker config ls" "docker config rm" 
clean_docker_entities "docker container ls -a" "docker container rm" 
clean_docker_entities "docker image ls" "docker image rm -f" 
