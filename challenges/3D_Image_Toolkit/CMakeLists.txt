set( SERVICE_ID "00078" )
set( AUTHOR_ID "CROMU" )
add_compile_options( -O0 -g )

#预处理
#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -targets=/home/xiaosatianyu/infomation/git-2/For_aflgo/temp/BBtargets.txt -outdir=/home/xiaosatianyu/infomation/git-2/For_aflgo/temp -flto -fuse-ld=gold -Wl,-plugin-opt=save-temps") 
#set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -targets=/home/xiaosatianyu/infomation/git-2/For_aflgo/temp/BBtargets.txt -outdir=/home/xiaosatianyu/infomation/git-2/For_aflgo/temp -flto -fuse-ld=gold -Wl,-plugin-opt=save-temps")

#插桩处理
#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -targets=/home/xiaosatianyu/infomation/git-2/For_aflgo/temp/BBtargets.txt -outdir=/home/xiaosatianyu/infomation/git-2/For_aflgo/temp -flto -fuse-ld=gold -Wl,-plugin-opt=save-temps") 
#set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -targets=/home/xiaosatianyu/infomation/git-2/For_aflgo/temp/BBtargets.txt -outdir=/home/xiaosatianyu/infomation/git-2/For_aflgo/temp -flto -fuse-ld=gold -Wl,-plugin-opt=save-temps")


set( VULN_COUNT "1" )
buildCB()
