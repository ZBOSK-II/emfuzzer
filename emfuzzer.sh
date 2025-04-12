#!/bin/bash
# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

docker run \
       --rm \
       -v "$PWD:$PWD" \
       -v /data:/data \
       -w "$PWD" \
       -u $(id -u):$(id -g) \
       emfuzzer $@
