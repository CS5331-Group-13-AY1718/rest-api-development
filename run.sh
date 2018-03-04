#!/bin/bash

TEAMID=`md5sum README.md | cut -d' ' -f 1`
docker kill $(docker ps -q)
docker rm $(docker ps -a -q)
docker build . -t $TEAMID
docker run -p 80:80 -p 8080:8080 -t $TEAMID
