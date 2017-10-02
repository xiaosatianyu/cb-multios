#!/usr/bin/env python
# coding=utf-8

import os
import sys
import logging
import time
import shutil
import tempfile
import subprocess
import signal
import angr
import json
import hashlib

l = logging.getLogger("driller.collect_crash")



##配置-----------------------------



        
########################################################################
class Collect():
    """"""

    #----------------------------------------------------------------------
    def __init__(self,crash_source_dir,crash_dir,binary_path):
        """Constructor"""
        self.crash_source_dir=crash_source_dir
        self.crash_dir=crash_dir
        self.binary_path=binary_path
        self.set_config(self.crash_source_dir, self.crash_dir,self.binary_path)
        
    
    ##各种函数------------------------------------------------------------------------------
    #判断唯一性                
    def run(self,test_path):
        test_from="crash"
        input_from="stdin"
       
        #筛选测试用例
        input_data_path=test_path
        #返回信号和崩溃点
        cur_signal,crash_address=self.dynamic_trace(input_data_path,test_from,input_from)
        cur_signal=str(cur_signal)
        return (cur_signal, crash_address)
    
    def dynamic_trace(self,input_path,test_from,input_from,add_env=None):
            '''
            record the executed BBs of a testcase
            @param input_from: read from file or stdin 
            '''
            cur_signal=0 #默认正常退出
            lname = tempfile.mktemp(dir="/dev/shm/", prefix="tracer-")
            args = [self.tracer_qemu]
            
            is_crash_case = False  # 处理crash时的flag,只记录崩溃处的基本块 ba
            crash_addr=[]
            args += ["-d", "exec", "-D", lname, self.binary_path]
            if input_from=="file":
                args += [input_path]
            elif input_from=="stdin":
                pass 
            else:
                l.error("input_from is error")   
            
            with open('/dev/null', 'wb') as devnull:
                stdout_f = devnull  # 扔掉输出
                p = subprocess.Popen(
                        args,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=devnull
                        )
                        
                #如果是stdin程序 
                if input_from=="stdin":
                    f=open(input_path, 'rb')
                    input_stdin=f.read()
                    f.close()
                    _,_= p.communicate(input_stdin)#读取测试用例,输入 加'\n'后可以多次
                    
                ret = p.wait() #等待返回结果
                
                # did a crash occur?
                if ret < 0:
                    #if abs(ret) == signal.SIGSEGV  or abs(ret) == signal.SIGILL:
                    #所有负数都要
                    if 1:
                        l.info("input caused a crash (signal %d)\
                                during dynamic tracing", abs(ret))
                        cur_signal=abs(ret)
                        l.info("entering crash mode")
                        is_crash_case =True #表示这是一个crash测试用例
                        #print input_path
    
                stdout_f.close()
            # end 得到一个轨迹
            
            #开始处理执行轨迹
            with open(lname, 'rb') as f:
                trace = f.read() #得到轨迹
    #         addrs = [int(v.split('[')[1].split(']')[0], 16)
    #                  for v in trace.scrash_block_setplit('\n')
    #                  if v.startswith('Trace')]  # 得到所有的基本块地址 int类型
            
    #         addrs = [v.split('[')[1].split(']')[0]
    #                  for v in trace.split('\n')
    #                  if v.startswith('Trace')] # 得到所有的基本块地址,删掉了别的内容 str类型
                if len(trace)==0:
                    return (cur_signal,None) # None 表示没有收集到路径 ，[]表示没有奔溃点
            #addrs = [v.split('[')[1].split(']')[0] for v in trace.split('\n') if v.startswith('Trace')] # 得到所有的基本块地址,这里保留函数名称 str类型
            #addrs_set=set()
            #addrs_set.update(addrs)  # 去掉重复的轨迹
            
            # grab the faulting address
            if is_crash_case:
                #crash_addr = int(trace.split('\n')[-2].split('[')[1].split(']')[0],16) #最后一个基本块 address
                #print trace
                #print trace.split('\n')[-2]
                #print trace.split('\n')[-1]#这个是空格
                crash_addr = [ trace.split('\n')[-2].split('[')[1].split(']')[0] ]         #最后一个基本块 address 奔溃点的地址  
            os.remove(lname)#删除记录测试用例轨迹的临时文件
            return (cur_signal,crash_addr)  #
    
    
    def filter_out(self,subdir,tc_path):
	cur_signal,crash_address=self.run(tc_path)
        tc=os.path.basename(tc_path)
        self.binary_crash_dir=os.path.join(self.crash_dir,self.binary)
        if cur_signal == '0':
            return #表示没有崩溃
        
        Unique="error-to-judge"
        CrashAddress="error-to-get"
        #如果不能收集奔溃点
        if crash_address is None:
            tag="no_address" 
            new_path=os.path.join(self.binary_crash_dir,tag,cur_signal,tc[0:9])+'_'+subdir+'_'+self.binary #重命名
            if not os.path.exists(os.path.dirname(new_path)):
                os.makedirs(os.path.dirname(new_path)) #创建多层目录 
            shutil.copyfile(tc_path, new_path) #copy to the tmp dir
        #如果可以收集崩溃点，且是新的
        elif len(crash_address)>0 and not crash_address[0] in self.crash_block_set:
            if not os.path.exists(os.path.join(self.binary_crash_dir,cur_signal)):
                os.makedirs(os.path.join(self.binary_crash_dir,cur_signal))
            new_path=os.path.join(self.binary_crash_dir,cur_signal,tc[0:9])+'_'+subdir+'_'+self.binary #重命名
            if os.path.exists(new_path): #是否已经存在了   
                return
            self.crash_block_set.update(crash_address) #记录的是崩溃处的地址
            shutil.copyfile(tc_path, new_path) #copy to the tmp dir 
            Unique="true"
            CrashAddress=crash_address[0]
        #如果可以收集崩溃点，但是重复的   
        elif  crash_address[0] in self.crash_block_set:
            tag="redundant"
            new_path=os.path.join(self.binary_crash_dir,tag,cur_signal,tc[0:9])+'_'+subdir+'_'+self.binary #重命名
            tmp_path=os.path.join(self.binary_crash_dir,cur_signal,tc[0:9])+'_'+self.binary+'_traffic' #如果已经放在uniqe目录了
            # 如果已经收集过了,既有对应文件了
            if os.path.exists(new_path) or os.path.exists(tmp_path):
                return
            
            if not os.path.exists(os.path.dirname(new_path)):
                os.makedirs(os.path.dirname(new_path)) #创建多层目录
                 
            shutil.copyfile(tc_path, new_path) #copy to the tmp dir
            Unique="false"
            CrashAddress=crash_address[0]
            
        #对应的information中添加信息
        Cur_Signal=cur_signal
        #计算hash
        with open(new_path,'rb') as f:
            md5obj = hashlib.md5()
            md5obj.update(f.read())
            Hash = md5obj.hexdigest()
        CrashTime=time.strftime('%H:%M:%S',time.localtime(time.time()))
        CrashFileName=new_path
        
        crash_item = {
                    "CrashTime": CrashTime,
                    "Signal": Cur_Signal,
                    "CrashAddress": CrashAddress,
                    "Hash": Hash,
                    "Unique":Unique,
                    "CrashFile": CrashFileName,
                    "Engine":"AFL"
        }
        self.info_dict["Crashes"].append(crash_item)#增加一个
        
    
    
    def get_crashes(self):
        
        # 记录已经测试过的测试用例目录加文件名称
        self.cache_list=set()
        
        #遍历新的目录
        for subdir in sorted(os.listdir(self.crash_source_dir)):
            if "driller" in subdir or "traffic" in subdir:
                continue
            sub_crash_path=os.path.join(self.crash_source_dir,subdir,"crashes")
            if not os.path.exists(sub_crash_path):
                time.sleep(10)
            #遍历crash
            for tc in sorted(os.listdir(sub_crash_path)):
                if 'README' in tc :
                    continue
                #mark the tag
                tc_path=os.path.join(sub_crash_path,tc)
                tc_tag=os.path.join(subdir,tc) #放在 cache_list 中的 换个进程就没有了,重跑方式会有太多的重复
                if tc_tag in self.cache_list:
                    continue
                else:
                    self.cache_list.update([tc_tag])
                #筛选
                self.filter_out(subdir,tc_path)
        
        #save the json
        with open(self.json_path,"wt") as f:
            #f.write(json.dumps(information_dict))
            json.dump(self.info_dict,f) #ok
            
        #save the crash点
        with open(self.crash_address_path,"wt") as f:
            for address in self.crash_block_set:
                f.write(address)
                f.write('\n')
            
    #----------------------------------------------------------------------
    def set_config(self,crash_source_dir,crash_dir,binary_path):
        ''' 
        listen for new inputs produced by driller
        :param crash_source_dir: directory to places new inputs
        :param crash_binary_dir: redis crash_binary_dir on which the new inputs will be arriving
        '''
        #arg1
        #完整的目录,有很多fuzzing引擎
        print ("crash_source_dir is %s " % crash_source_dir)
        if not os.path.exists(crash_source_dir):
            l.error("not source dir")
        #arg2
        #总的目录
        if not os.path.exists(crash_dir):
            os.mkdir(crash_dir)
        print ("crash_dir is %s" % crash_dir)
        #arg3
        self.binary=os.path.basename(binary_path).strip()
        
        #the target to copy
        crash_binary=os.path.join(crash_dir,self.binary) 
        print   ("crash_binary is %s" % crash_binary)
        if not os.path.exists(crash_binary):
            os.mkdir(crash_binary)
        
        #从对应的json读取信息, 用来保存每个cb的crash信息
        self.info_dict=dict()
        self.json_path=os.path.join(crash_dir ,self.binary+'.json') #每个目标程序下
        #如果有,则从原来的json中读取
        try:
            if os.path.exists(self.json_path):
                f=open(self.json_path,'rt')
                self.info_dict=json.load(f)#是一个字典
                f.close()
        except Exception as e:
            pass        
            
        #读取目标程序的目录
        #默认配置信息
        Round= 0
        ChallengeID=65
        CB=binary_path
        PullTime="time here",
        ReadAddress="0xdeadbeaf"
        WriteAddress="0xdeadbeaf"
        WriteValue="0xdeadbeaf"
        OWEIP="0xdeadbeaf"
        
        #准备目标程序的json
        #第一次生成 BasicInfo
        if not self.info_dict.has_key("BasicInfo"):
            self.info_dict["BasicInfo"]={
                            "Round": Round,
                            "ChallengeID": ChallengeID,
                            "CB": CB,
                            "PullTime": PullTime,
                            "ReadAddress": ReadAddress,
                            "WriteAddress": WriteAddress,
                            "WriteValue": WriteValue,
                            "OWEIP": OWEIP
                }
        #第一次生成Crashes
        if not self.info_dict.has_key("Crashes"):
            self.info_dict["Crashes"]=list() #针对当前程序，新建一个字典
        
        #读取crash point
        self.crash_address_path=os.path.join(crash_binary,"crash_address") #保存crash点的文件
        self.crash_block_set=set()
        #读取已有崩溃点信息
        if os.path.exists(self.crash_address_path):
            with open(self.crash_address_path,"r") as f:
                while 1:
                    line= f.readline().split('\n')[0]
                    if not line :
                        break
                    if len(line)>0 :
                        self.crash_block_set.update([line])
           
        #configure
        #配置对应的qemu
        qemu_dir="/home/xiaosatianyu/workspace/git/driller-yyy/shellphish-qemu/shellphish_qemu/bin" #来自于tracer
        #自适应
        p = angr.Project(binary_path)
        self.platform = p.arch.qemu_name
        if self.platform == 'i386':
            self.tracer_qemu = os.path.join(qemu_dir, "shellphish-qemu-linux-i386")
        elif self.platform == 'x86_64': 
            self.tracer_qemu = os.path.join(qemu_dir, "shellphish-qemu-linux-x86_64")
        elif self.platform == 'cgc': 
            self.tracer_qemu = os.path.join(qemu_dir, "shellphish-qemu-cgc-tracer")
        else:
            print "no qemu\n"
        ##结束配置    
        
    


if __name__ == '__main__':
    print("start to collect crash")
    
    # the way to save the crash
    crash_dir="/home/xiaosatianyu/Desktop/driller-desk/CRASH"
    

    # go through all the 
    afl_out_dir="/home/xiaosatianyu/Desktop/server/cgcc-tmp/driller"
    binary_dir="/home/xiaosatianyu/workspace/git/fuzz/cb-multios/binary-clang"
    for item in os.listdir(afl_out_dir):
	binary=item
	bianry_path=os.path.join(binary_dir,binary)
	sub_crash_dir=os.path.join(afl_out_dir,binary,"sync")

	collect=Collect(sub_crash_dir, crash_dir, bianry_path)
	collect.get_crashes()	
	
   
    print("successs")