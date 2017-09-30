#!/usr/bin/env bash

set -e

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
mkdir -p ${DIR}/build
cd ${DIR}/build

echo "Creating Makefiles"
#表示导出编译flag CMake会把当前的编译flag全部导出到一个json数据库, 在当前目录下(build目录)的compile_commands.json
CMAKE_OPTS="-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"

# Honor CC and CXX environment variables, default to clang otherwise
#如果没有定义,就为clang
CC=${CC:-clang}
CXX=${CXX:-clang++}

#CC="/home/xiaosatianyu/infomation/git-2/For_aflgo/aflgo/afl-clang-fast"
#CXX="/home/xiaosatianyu/infomation/git-2/For_aflgo/aflgo/afl-clang-fast++"


#添加编译信息,通过 -D
CMAKE_OPTS="$CMAKE_OPTS -DCMAKE_C_COMPILER=$CC"
CMAKE_OPTS="$CMAKE_OPTS -DCMAKE_ASM_COMPILER=$CC"
CMAKE_OPTS="$CMAKE_OPTS -DCMAKE_CXX_COMPILER=$CXX"
#控制动态编译还是静态编译,这里采用动态编译
LINK=${LINK:-SHARED}
case $LINK in
    SHARED) CMAKE_OPTS="$CMAKE_OPTS -DBUILD_SHARED_LIBS=ON -DBUILD_STATIC_LIBS=OFF";;
    STATIC) CMAKE_OPTS="$CMAKE_OPTS -DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC_LIBS=ON";;
esac

# Prefer ninja over make, if it is available
#强制用make
if not which ninja 2>&1 >/dev/null; then
  CMAKE_OPTS="-G Ninja $CMAKE_OPTS"
  BUILD_FLAGS=
else
  BUILD_FLAGS="-- -j$(getconf _NPROCESSORS_ONLN)" #后面是得到核心数量
fi

#根据CMakeList.txt 和设定的一些参数 生成makefile
cmake $CMAKE_OPTS ..

cmake --build . $BUILD_FLAGS  #直接编译了, 不用在输入ninja或者make了
