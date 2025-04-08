#!/bin/bash
# Copyright (c) 2025 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd "${SCRIPT_DIR}"

git describe --tags --dirty --always --abbrev=6 > VERSION.tmp

docker build -t emfuzzer .

rm VERSION.tmp
