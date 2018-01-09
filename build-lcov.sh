#!/usr/bin/env bash

set -e

export SPLIT_SWITCHES=1
export TRANSFORM_COMPARES=1
export SPLIT_COMPARES=1
export STRCPY_EXPAND=1

# Root cb-multios directory
DIR=$(cd "$(dirname ${BASH_SOURCE[0]})" && pwd)
TOOLS="$DIR/tools"

# Install necessary python packages
if ! /usr/bin/env python -c "import xlsxwriter; import Crypto" 2>/dev/null; then
    echo "Please install required python packages" >&2
    echo "  $ sudo pip install xlsxwriter pycrypto" >&2
    exit 1
fi

echo "Creating build directory"
mkdir -p ${DIR}/build-lcov
cd ${DIR}/build-lcov


echo "Creating Makefiles"
CMAKE_OPTS="-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"

# Honor CC and CXX environment variables, default to clang otherwise
CC=clang
CXX=clang++

CMAKE_OPTS="$CMAKE_OPTS -DCMAKE_C_COMPILER=$CC"
CMAKE_OPTS="$CMAKE_OPTS -DCMAKE_ASM_COMPILER=$CC"
CMAKE_OPTS="$CMAKE_OPTS -DCMAKE_CXX_COMPILER=$CXX"

LINK=${LINK:-SHARED}
case $LINK in
    SHARED) CMAKE_OPTS="$CMAKE_OPTS -DBUILD_SHARED_LIBS=ON -DBUILD_STATIC_LIBS=OFF";;
    STATIC) CMAKE_OPTS="$CMAKE_OPTS -DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC_LIBS=ON";;
esac

# Prefer ninja over make, if it is available
if which ninja 2>&1 >/dev/null; then
  CMAKE_OPTS="-G Ninja $CMAKE_OPTS"
  BUILD_FLAGS=
else
  BUILD_FLAGS="-- -j$(getconf _NPROCESSORS_ONLN)"
fi

cmake $CMAKE_OPTS ..

cmake --build . $BUILD_FLAGS
