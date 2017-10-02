#coding=utf-8

import os
import shutil

#目的:
#将子目录下的执行程序复制到一个共同的目录下 


#----------------------------------------------------------------------
def move_binary(source_sub_dir,target_dir):
    """
    remove the binary from each sub directories to a total directory
    """
    for item in os.listdir(source_sub_dir):
        if "."==item:
            continue
        binary_name=item
        bianry_dir=os.path.join(source_sub_dir,item)
        binary_path=os.path.join(bianry_dir,binary_name)
        binary_patched_path=os.path.join(bianry_dir,binary_name+"_patched")
        if os.path.exists(binary_path) and os.path.exists(binary_patched_path):
            try:
                shutil.copy(binary_path, target_dir)
                shutil.copy(binary_patched_path, target_dir)
            except Exeception as e:
                print("some thing is error with %s" % (binary_name))
        else:
            print("has no binary: %s"% binary_name)
            continue

if __name__ == '__main__':
    print("start")
    # each sub direcotry
    source_sub_dir="/home/xiaosatianyu/workspace/git/fuzz/cb-multios/build/challenges"
    # targe total directory
    target_dir="/home/xiaosatianyu/workspace/git/fuzz/cb-multios/binary-clang"
    move_binary(source_sub_dir,target_dir)
    print("successs")
