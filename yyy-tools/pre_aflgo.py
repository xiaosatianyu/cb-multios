#coding=utf-8

#target:
#get the CFG CG and the distance



import os
import shutil
import subprocess


#the flow
#0. 记录所有target的程序(通过遍历crash目录),即需要测试的程序jobs
#1. 遍历jobs源码目录,往需要测试的程序下的CMakeList.txt添加预编译内容
#2. 进行预编译,输出结果, 运行build.sh就行
#3. 计算每个子程序的distance,对每个output目录下的内容进行计算
#4. 重新修改每个程序下的CMakeList.txt添加,距离插桩译内容
#5. 重新运行build.sh
#6. 收集到插桩的二进制程序   

########################################################################
class AFLGo:
    """"""

    #----------------------------------------------------------------------
    def __init__(self,source_dir,crash_dir,out_put_dir):
        """Constructor"""
        self.source_dir=source_dir
        self.crash_dir=crash_dir
        self.out_put_dir=out_put_dir
        self.build_script_path="/home/xiaosatianyu/workspace/git/fuzz/cb-multios/build.sh"
        self.jobs=[]
        self.get_jobs()
      
    #----------------------------------------------------------------------
    def set_config(self):
        """"""
               
    #----------------------------------------------------------------------
    def get_jobs(self):
        """"""
        for item in os.listdir(self.crash_dir):
            binary=item
            if "BBtargets.txt" not in os.listdir(os.path.join(self.crash_dir,binary)):
                continue
            self.jobs.append(binary)
        
    #----------------------------------------------------------------------
    def add_targets_each(self,binary,cmakelist_path):
        """""" 
        target=os.path.join(self.crash_dir,binary,"BBtargets.txt")
        outdir=os.path.join(self.out_put_dir,binary)
        content=[]
        with open(cmakelist_path,"rt") as f:
            for line in f.readlines():
                content.append(line)
                
        newcommand_CFlag="set(CMAKE_C_FLAGS \"${CMAKE_CXX_FLAGS} -targets="+target+"  -outdir="+outdir+" -flto -fuse-ld=gold -Wl,-plugin-opt=save-temps\")\n"
        newcommand_CXXFlag="set(CMAKE_CXX_FLAGS \"${CMAKE_CXX_FLAGS} -targets="+target+"  -outdir="+outdir+" -flto -fuse-ld=gold -Wl,-plugin-opt=save-temps\")\n"
        content.insert(-1, newcommand_CFlag)
        content.insert(-1, newcommand_CXXFlag)
        
        # save the old
        if not os.path.exists(cmakelist_path+"-old"):
            shutil.copy(cmakelist_path, cmakelist_path+"-old")
        with open(cmakelist_path,"wt") as f:
            for line in content:
                f.write(line)
        
    #----------------------------------------------------------------------
    def add_targets_all(self):
        """
        add the  target compiler parameter to all the jobs to be tested
        """
        for item in self.jobs:
            binary=item
            cmakelist_path=os.path.join(self.source_dir,item,"CMakeLists.txt")
            if  not os.path.exists(cmakelist_path):
                print("there is no cmakelist.txt in %S"%item)
                continue
            self.add_targets_each(binary,cmakelist_path)
        return 
    #----------------------------------------------------------------------
    def add_distance_each(self):
        """"""
        pass
    #----------------------------------------------------------------------
    def add_distance_all(self):
        """"""
        pass
    #----------------------------------------------------------------------
    def compiler_all(self):
        """"""
        pass
        
        
    #----------------------------------------------------------------------
    def reset_cmakelist_all(self):
        """
        return to the old CMakeList.txt
        """
        pass
    #----------------------------------------------------------------------
    def build_cb(self,aflgo):
        """"""
        if aflgo:
            args = [self.build_script_path, "aflgo"]
            p = subprocess.Popen(args)  
            ret=p.wait()
        else:
            args = [self.build_script_path]
            p = subprocess.Popen(args,shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)  
            ret=p.wait()    
            print "a"
        
        
         
    

if __name__ == '__main__':
    print("start")
    #all_source
    source_dir="/home/xiaosatianyu/workspace/git/fuzz/cb-multios/challenges"
    #the crash information, save the BBtargets.txt
    crash_dir="/home/xiaosatianyu/workspace/git/fuzz/cb-multios/crash"
    #the output
    out_put_dir="/home/xiaosatianyu/workspace/git/fuzz/cb-multios/output"  
    
    process=AFLGo(source_dir, crash_dir, out_put_dir)
    #process.add_targets_all()
    process.build_cb(False)
    print("successs")
