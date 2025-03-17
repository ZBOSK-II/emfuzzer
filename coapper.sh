#!/bin/bash

docker run \
       --rm \
       -v "$PWD:$PWD" \
       -v /data:/data \
       -w "$PWD" \
       -u $(id -u):$(id -g) \
       coapper coapper $@
