#coding=utf-8

#target:
#get the CFG CG and the distance



import os
import shutil
import subprocess
import copy
import time


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
        self.script_path_get_distance="/home/xiaosatianyu/infomation/git-2/For_aflgo/aflgo/scripts/genDistance.sh"
        self.jobs=[]
        self.exclude=[]
        self._get_jobs()
        
        self.extendion_num=5
        self._extend_crash_to_target()
        

    #----------------------------------------------------------------------
    def _get_jobs(self):
        """
        get the jobs from crash_dir
        """
        for item in os.listdir(self.crash_dir):
            binary=item
            self.jobs.append(binary)
        self._mkoutput()
    #----------------------------------------------------------------------
    def _mkoutput(self):
        """build the output dir"""
        for item in self.jobs:
            output_path=os.path.join(self.out_put_dir,item)
            if not os.path.exists(output_path):
                os.makedirs(output_path)
        
    #----------------------------------------------------------------------
    def _add_targets_each(self,binary,cmakelist_path):
        """""" 
        target=os.path.join(self.crash_dir,binary,"BBtargets.txt")
        outdir=os.path.join(self.out_put_dir,binary)
        content=[]
        with open(cmakelist_path,"rt") as f:
            for line in f.readlines():
                content.append(line)
                
        newcommand_CFlag="set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -targets="+target+"  -outdir="+outdir+" -flto -fuse-ld=gold -Wl,-plugin-opt=save-temps\")\n"
        newcommand_CXXFlag="set(CMAKE_CXX_FLAGS \"${CMAKE_CXX_FLAGS} -targets="+target+"  -outdir="+outdir+" -flto -fuse-ld=gold -Wl,-plugin-opt=save-temps\")\n"
        if not newcommand_CFlag in content:
            content.insert(-1, newcommand_CFlag)
        if not newcommand_CXXFlag in content:
            content.insert(-1, newcommand_CXXFlag)
        
        # save the old
        if not os.path.exists(cmakelist_path+"-old"):
            shutil.copy(cmakelist_path, cmakelist_path+"-old")
        with open(cmakelist_path,"wt") as f:
            for line in content:
                f.write(line)
        
   
    #----------------------------------------------------------------------
    def _add_distance_each(self,binary,cmakelist_path):
        """"""
        pass
    
    #----------------------------------------------------------------------
    def _build_cb(self,aflgo):
        """
        @param: aflgo: true mean use afl-clang-fast,falst means use clang, it is setted in build.sh
        """
        with open("/tmp/cb-build.log","wt") as f:
            if aflgo:
                self.build_dir=os.path.dirname(self.build_script_path)+"/build-aflgo"
                args = [self.build_script_path+ " aflgo"]
                p = subprocess.Popen(args,shell=True, stdout=f, stderr=subprocess.STDOUT)            
                ret=p.wait()
                print "--------------------------------------------------------------------"
                if ret ==0:
                    print "build with aflgo-clang sucess"
                    return True
                else:
                    print "build with aflgo-clang fail"
                    return False
                print "--------------------------------------------------------------------"
            else:
                self.build_dir=os.path.dirname(self.build_script_path)+"/build"
                args = [self.build_script_path]
                p = subprocess.Popen(args,shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)  
                ret=p.wait() 
                print "--------------------------------------------------------------------"
                if ret ==0:
                    print "build with clang sucess"
                    return True
                else:
                    print "build with clang fail"
                    return False
                print "--------------------------------------------------------------------"
                
        
    #----------------------------------------------------------------------
    def _extend_crash_to_target(self):
        """
        extent the crash line to BBtargets 
        """
        for item in self.jobs:
            crash_line_path=os.path.join(self.crash_dir,item,"crash_line")
            binary=item
            BBtarget_path=os.path.join(self.crash_dir,item,"BBtargets.txt")
            if not os.path.exists(crash_line_path):
                continue
            content=[]
            with open(crash_line_path,"rt") as f:
                for line in f.readlines():
                    content.append(line)
            new_content= copy.deepcopy(content)
            for lines in content:
                if "\n" ==lines:
                    continue
                file_name=lines.split(":")[0]
                loc_num  =int(lines.split(":")[1])
                for j in xrange(self.extendion_num):
                    new_loc1=str(loc_num+j)
                    new_loc2=str(loc_num-j)
                    new_target1=file_name+":"+new_loc1+"\n"
                    new_target2=file_name+":"+new_loc2+"\n"
                    if not new_target1 in new_content:
                        new_content.append(new_target1)
                    if not new_target2 in new_content:
                        new_content.append(new_target2)
            new_content.sort()
            with open(BBtarget_path,"wt") as f:
                for line in new_content:
                    f.write(line)   
                    
            #move the BBtargets to the sub_output dir  
            self._move_each_BBtargets_to_outdir(BBtarget_path, binary)
        print "crash_line extend to BBtargets.txt end----------------" 
        
    #----------------------------------------------------------------------
    def _move_each_BBtargets_to_outdir(self,BBtarget_path,binary):
        """"""
        sub_out_dir=os.path.join(self.out_put_dir,binary)
        if not os.path.exists(sub_out_dir):
            os.makedirs(sub_out_dir)
        shutil.copy(BBtarget_path, sub_out_dir)
        
        
    #----------------------------------------------------------------------
    def _cal_distance_each(self,sub_out_dir,binary):
        """"""
        sub_build_path=os.path.join(self.build_dir,"challenges",binary)
        args = [self.script_path_get_distance+" "+sub_build_path+" "+sub_out_dir+" "+binary]
        print "calculate the distance of %s"%binary
        with open("/tmp/getdistance.log","wt") as f:
            p = subprocess.Popen(args,shell=True, stdout=f, stderr=subprocess.STDOUT)            
            ret=p.wait()
            time.sleep(1)
            if ret ==0:
                print "calculate distance with aflgo sucess: %s"%binary
            else:
                self.exclude.append(binary)
                shutil.rmtree(sub_out_dir)
                print "calculate distance with aflgo fail: %s"%binary
        
              
        
    
    # interface -----------------------------------------------------------
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
            self._add_targets_each(binary,cmakelist_path)
        return     
    #----------------------------------------------------------------------
    def add_distance_all(self):
        """"""
        for item in self.jobs:
            binary=item
            cmakelist_path=os.path.join(self.source_dir,item,"CMakeLists.txt")
            if  not os.path.exists(cmakelist_path):
                print("there is no cmakelist.txt in %S"%item)
                continue
            self._add_distance_each(binary,cmakelist_path)
        return      
    #----------------------------------------------------------------------
    def build_aflgo_with_targets(self):
        """"""
        self.reset_cmakelist_all()
        self.add_targets_all()
        if not self._build_cb(aflgo=True):
            print "build error"
            return
    #----------------------------------------------------------------------
    def reset_cmakelist_all(self):
        """
        return to the old CMakeList.txt
        """
        for item in self.jobs:
            binary=item
            cmakelist_path=os.path.join(self.source_dir,item,"CMakeLists.txt")
            cmakelist_old_path=os.path.join(self.source_dir,item,"CMakeLists.txt-old")
            if os.path.exists(cmakelist_old_path):
                shutil.copy(cmakelist_old_path, cmakelist_path)
        return     
    #----------------------------------------------------------------------
    def calculate_distance_all(self):
        """"""
        self.jobs.sort()
        for item in self.jobs:
            binary=item
            if binary in self.exclude:
                continue
            sub_out_dir=os.path.join(self.out_put_dir,binary)
            self._cal_distance_each(sub_out_dir,binary)
        
        
if __name__ == '__main__':
    print("start")
    #all_source
    source_dir="/home/xiaosatianyu/workspace/git/fuzz/cb-multios/challenges"
    #the crash information, save the BBtargets.txt
    crash_dir="/home/xiaosatianyu/workspace/git/fuzz/cb-multios/crash"
    #the output
    out_put_dir="/home/xiaosatianyu/workspace/git/fuzz/cb-multios/output"  
    
    process=AFLGo(source_dir, crash_dir, out_put_dir)
    process.build_aflgo_with_targets()
    process.calculate_distance_all()
    
    print("successs")
