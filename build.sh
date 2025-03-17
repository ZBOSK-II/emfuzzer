#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd "${SCRIPT_DIR}"

git describe --tags --dirty --always --abbrev=6 > VERSION.tmp

docker build -t coapper .

rm VERSION.tmp
