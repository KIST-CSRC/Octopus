#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [Scheduler] Scheduler file
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# @version  1_2   
# TEST 2021-11-01
# TEST 2022-04-11

from queue import Queue
import time
import os, sys
import json, copy
import threading
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Task.TCP import TCP_Class
from Analysis import AnalysisUV
from Log.DigitalSecretary import AlertMessage


class RobotMovModule(TCP_Class):
    """
    [RobotMovModule] RobotMovModule inherited doosan robot library

    # Variable
    :param module_name="Robot module" (str): set robot module name (log name)
    :param mode_type="virtual" (str): set virtual or real mode

    # function
    1. __initVialTop(self):
    2. _popVialNum(self):
    3. MoveContainer(self, task_info_list):
    """
    def __init__(self, module_name="Robot", ResourceManager_obj={}):

        self.robot_module_name = "{}".format(module_name) 
        TCP_Class.__init__(self,)
        self.vial_top_queue = Queue()
        self.the_number_of_vial = 80
        self.__initVialTop()
        self.ResourceManager_obj=ResourceManager_obj

    def __initVialTop(self):
        """
        initialize vial number depending on Queue.

        :return: None: 
        """
        for num in range(self.the_number_of_vial):
            self.vial_top_queue.put(num)  

    def __popVialNum(self):
        """
        pop vial number depending on Queue.

        :return: vial_num (int): get vial number in vial_top_queue
        """
        # print("previous : ",self.vial_top_queue.qsize())
        empty_true = self.vial_top_queue.empty()
        # print("empty_true : ",empty_true)
        if empty_true==True:
            self.__initVialTop()
        vial_num=self.vial_top_queue.get()
        # print("later : ",self.vial_top_queue.qsize())

        return vial_num

    def __alertVialNum(self, TaskLogger_obj, mode_type="virtual"):
        text_content="[{}] vial number ({}) is not enough, please move vial to another where".format(self.robot_module_name, self.vial_top_queue.qsize())
        if self.vial_top_queue.qsize() <=10:
            AlertMessage(text_content=text_content, key_path="./Log", message_module_list=["dooray"], mode_type=mode_type)
        else:
            pass
    
    def __countVialTop_LineTopNum(self, vial_num):
        """
        counts on vial_num and line_num depending on the number of TaskLogger_obj.

        :return: None 
        """
        # count the number of vials in vial_top_queue
        vial_num_list=[]
        line_num_list=[]
        for _ in range(vial_num): # for each vial
            vial_num=self.__popVialNum()
            vial_num_list.append(vial_num)
            line_num_list.append(vial_num//16) # same with previous "cycle_num"

        return vial_num_list, line_num_list

    def MoveContainer(self, task_info_list, jobID, location_dict, TaskLogger_obj, mode_type="virtual"):
        """
        allocate MoveContainer depending on task_info_list.

        :param task_info_list (list): "Task":"MoveContainer","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode

        task_info_list = [
                {
                    "Task": "MoveContainer",
                    "Data": {
                        "From": "vialholder_UV",
                        "To": "storage_filled",
                        "Container": "Vial",
                        "Device": {
                            "Id": "dsr01",
                            "Model": "m0609",
                            "NETWORK": "192.168.137.100",
                            "WorkRange": 900
                        }
                    }
                }
            ]
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        vial_num_list=[]
        line_num_list=[]
        
        # check & update status of hardware --> DON'T MIX EACH EXPERIMENT VIALS
        taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
        delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
        taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
        delay_time_str="{}~{}".format(taskStartTime, taskFinishTime)
        TaskLogger_obj.addDelayTime(delay_time)
        TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
        self.ResourceManager_obj.updateStatus(current_func_name, True) # Already use !
        
        for task_idx, move_dict in enumerate(task_info_list): # for each vial
            # update status of hardware every batch
            TaskLogger_obj.current_module_name="{}-->{}".format(self.robot_module_name, "MoveContainer")
            TaskLogger_obj.status="{}_{}/{}:{}".format(len(task_info_list), task_idx, TaskLogger_obj.totalExperimentNum, TaskLogger_obj.current_module_name) # in execution system
            # execute task
            move_type="{}_to_{}".format(move_dict["From"], move_dict["To"])
            msg = "Batch motion ({}) is started.".format(move_type)
            TaskLogger_obj.debug(self.robot_module_name, "Start Robot Queue : "+msg)
            
            if move_type == "vialholder_UV_to_storage_filled" or move_type=="vialholder_BatchSynthesis_to_storage_filled":
                if task_idx==0: # vial 채우기 전, stepper motor initialize
                    vial_num_list, line_num_list= self.__countVialTop_LineTopNum(len(task_info_list))
                    TaskLogger_obj.debug(self.robot_module_name, "vial_num_list:{}".format(vial_num_list))
                    TaskLogger_obj.debug(self.robot_module_name, "line_num_list:{}".format(line_num_list))
                    TaskLogger_obj.debug(self.robot_module_name, "vialHolder_list:{}".format(location_dict["vialHolder"]))
                    time.sleep(2)
                    command_str=self.packetFormatter(jobID,"STORAGE","open",line_num_list[task_idx]+5,mode_type)
                    res_msg=self.callServer_BATCH(command_str=command_str)
                    time.sleep(2)
                
                # self.ResourceManager_obj.updateStatus(current_func_name, True) # Already use !
                command_str=self.packetFormatter(jobID,"LA","center","null",mode_type)
                res_msg=self.callServer_BATCH(command_str=command_str)

                # self.ResourceManager_obj.updateStatus(current_func_name, True) # Already use !
                command_str=self.packetFormatter(jobID,"DS_B",move_type,[location_dict["vialHolder"][task_idx],line_num_list[task_idx]],mode_type)
                res_msg=self.callServer_BATCH(command_str=command_str)    
                
                
                if task_idx+1 == len(task_info_list): # vial 채울 때는 마지막 task이 끝날 때만 vial storage 모터 내리기
                    time.sleep(2)
                    self.ResourceManager_obj.updateStatus(current_func_name, True) # Already use !
                    command_str=self.packetFormatter(jobID,"STORAGE","open",line_num_list[task_idx]+5,mode_type)
                    res_msg=self.callServer_BATCH(command_str=command_str)
                    
            msg = "Batch motion ({}) is done.".format(move_type)   
            TaskLogger_obj.debug(self.robot_module_name, "Finish Robot Queue : "+msg)

        self.ResourceManager_obj.updateStatus(current_func_name, False) # Already use !

        self.__alertVialNum(TaskLogger_obj)

        return res_msg


class BatchSynthesisModule(TCP_Class):
    """
    [BatchSynthesisModule] BatchSynthesisModule inherited Linear actuator, stirrer, syringe pump class

    # Variable
    :param module_name="Batch Synthesis module" (str): set log name (log name)
    :param mode_type="virtual" (str): set virtual or real mode

    # function
    1. _initializeDevice():
    2. _AllocateTecanAddress(solution_dict):
    3. _AllocateTecanUSBAddress(tecan_addr):
    4. _allocateAddress(stirrer_name):
    5. AddSolution(task_info_list):
    6. Stir(task_info_list):
    7. Heat(task_info_list):
    8. Mix(task_info_list):
    9. React(task_info_list):
    """
    def __init__(self,module_name="BatchSynthesis", ResourceManager_obj={}):
        TCP_Class.__init__(self,)
        self.batch_module_name= "{}".format(module_name)
        self.vial_bottom_queue = Queue()
        self.the_number_of_vial = 80
        self.__initVialBottom()
        self.ResourceManager_obj=ResourceManager_obj
    
    def _allocateAddress(self, stirrer_hole_location):
        """
        allocate pump bus usb address depending on soluition_dict

        :param device_name (str): "Stirrer_0-0" or "Stirrer_1-7"...etc (depending on stirrer addreess in IKA RET)

        return int(stirrer_hole_location//8)
        """
        return int(stirrer_hole_location//8)

    def __initVialBottom(self):
        """
        initialize vial number depending on Queue.

        :return: None: 
        """
        for num in range(self.the_number_of_vial):
            self.vial_bottom_queue.put(num)  

    def __popVialBottom(self):
        """
        pop vial number depending on Queue.

        :return: vial_num (int): get vial number in vial_bottom_queue
        """
        empty_true = self.vial_bottom_queue.empty()
        if empty_true==True:
            self.__initVialBottom()
        vial_num=self.vial_bottom_queue.get()

        return vial_num

    def __alertVialNum(self, TaskLogger_obj, mode_type="virtual"):
        text_content="[{}] vial number ({}) is not enough, please fill vial".format(self.robot_module_name, self.vial_bottom_queue.qsize())
        if self.vial_bottom_queue.qsize() <=10:
            AlertMessage(text_content=text_content, key_path="./Log", message_module_list=["dooray"], mode_type=mode_type)
        else:
            pass
    
    def __countVialBottom_LineBottomNum(self, vial_num):
        """
        counts on vial_num and line_num depending on the number of TaskLogger_obj.
        :return: None 
        """
        # count the number of vials in robot_queue
        vial_num_list=[]
        line_num_list=[]
        for _ in range(vial_num): # for each vial
            vial_num=self.__popVialBottom()
            vial_num_list.append(vial_num)
            line_num_list.append(vial_num//16) # same with previous "cycle_num"
        
        return vial_num_list, line_num_list

    def PrepareContainer(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        allocate MoveContainer depending on task_info_list.

        :param task_info_list (list): "Task":"MoveContainer","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode

        task_info_list = [
                {
                    "Task": "PrepareContainer",
                    "Data": {
                        "From": "storage_empty",
                        "To": "stirrer",
                        "Container": "Vial",
                        "Setting": {
                            "Id": "dsr01",
                            "Model": "m0609",
                            "NETWORK": "192.168.137.100",
                            "WorkRange": 900
                        }
                },
                {
                    "Task": "PrepareContainer",
                    "Data": {
                        "From": "storage_empty",
                        "To": "stirrer",
                        "Container": "Vial",
                        "Setting": {
                            "Id": "dsr01",
                            "Model": "m0609",
                            "NETWORK": "192.168.137.100",
                            "WorkRange": 900
                        }
                    }
                },
                ...
            ]
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        vial_num_list=[]
        line_num_list=[]
        
        for task_idx, move_dict in enumerate(task_info_list): # for each vial
            # check & update status of hardware
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str="{}~{}".format(taskStartTime, taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            # update status of hardware every batch
            TaskLogger_obj.current_module_name="{}-->{}".format(self.batch_module_name, "PrepareContainer")
            TaskLogger_obj.status="{}_{}/{}:{}".format(len(task_info_list), task_idx, TaskLogger_obj.totalExperimentNum, TaskLogger_obj.current_module_name) # in execution system
            # execute task
            move_type="{}_to_{}".format(move_dict["From"], move_dict["To"])
            msg = "{} is started.".format(move_type)
            TaskLogger_obj.debug(self.batch_module_name, msg)
            # separate robot task
            if task_idx==0:
                vial_num_list, line_num_list= self.__countVialBottom_LineBottomNum(len(task_info_list))
                TaskLogger_obj.debug(self.batch_module_name, "vial_num_list: {}".format(vial_num_list))
                TaskLogger_obj.debug(self.batch_module_name, "line_num_list: {}".format(line_num_list))
                TaskLogger_obj.debug(self.batch_module_name, "vialHolder_list: {}".format(location_dict["vialHolder"]))
            # execute real task
            TaskLogger_obj.debug(self.batch_module_name, "Start Robot Queue : "+msg)
            command_str=self.packetFormatter(jobID,"LA","center","null",mode_type) # initialize LinearActuato
            TaskLogger_obj.debug("LA", "move center-->Start!")
            res_msg=self.callServer_BATCH(command_str=command_str)
            TaskLogger_obj.debug("LA", "move center-->Done!")
            
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            command_str=self.packetFormatter(jobID,"STORAGE","open",line_num_list[task_idx],mode_type)
            TaskLogger_obj.debug("STORAGE", "open-->Start!")
            res_msg=self.callServer_BATCH(command_str=command_str)
            TaskLogger_obj.debug("STORAGE", "open-->Done!")
            time.sleep(2) # due to delay of vial storage

            self.ResourceManager_obj.updateStatus(current_func_name, True)
            command_str=self.packetFormatter(jobID,"DS_B",move_type,[line_num_list[task_idx],location_dict["Stirrer"][task_idx]],mode_type)
            TaskLogger_obj.debug("DS_B", "prepare container-->Start!")
            res_msg = self.callServer_BATCH(command_str=command_str)
            TaskLogger_obj.debug("DS_B", "prepare container-->Done!")
            
            msg = "{} is done.".format(move_type)   
            TaskLogger_obj.debug(self.batch_module_name, "Finish Robot Queue : "+msg)

            # initialize status of hardware
            self.ResourceManager_obj.updateStatus(current_func_name, False)

        self.__alertVialNum(TaskLogger_obj)

        return res_msg

    def AddSolution(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"AddSolution","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode

        :(inside) pump_dict : { "To":"Stirrer_1","Data":[] }
        :(inside) pump_dict["Data"] : 
            [
                {
                    "Solution":"AgNO3",
                    "Volume":
                    {
                        "Value":1500,
                        "Dimension":"ul"
                    },
                    "Concentration":
                    {
                        "Value":20,
                        "Dimension":"mM"
                    },
                    "Injectionrate":
                    {
                        "Value":1000,
                        "Dimension":"ul/s"
                    }
                },
                ...
            
            ex) total_solution_queue :  [
                {'Solution': 'H2O2', 
                'Volume': {'Value': 1200, 'Dimension': 'μL'}, 
                'Concentration': {'Value': 0.375, 'Dimension': 'mM'}, 
                'Injectionrate': {'Value': 200, 'Dimension': 'μL/s'}, 
                'Setting': {'SolutionType': 'Oxidant', 'PumpAddress': 3, 'PumpUsbAddr': '/dev/ttyUSB0', 'Resolution': 1814000, 
                'Concentration': 0.75, 'Density': 1.45, 'MolarMass': 34.0147, 'SyringeVolume': 5000, 'DeviceName': 'CavroCentris'}}]
            ]
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        for vial_task_idx, pump_dict in enumerate(task_info_list): # for each vial
            # check & update status of hardware
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str="{}~{}".format(taskStartTime, taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            
            # update status of hardware every batch
            TaskLogger_obj.current_module_name="{}-->{}".format(self.batch_module_name, "AddSolution")
            TaskLogger_obj.status="{}_{}/{}:{}".format(len(task_info_list), vial_task_idx, TaskLogger_obj.totalExperimentNum, TaskLogger_obj.current_module_name) # in execution system

            total_solution_queue = [pump_dict]
            process_number = len(total_solution_queue)

            # execute Preparing task
            # for _,solution_dict in enumerate(total_solution_queue) : # matching 1 vial --> 1 task
            #     action_type="single" # 1개의 용액 (not 1개의 pump)
            #     solution_name=solution_dict["Solution"]
            #     concentration=solution_dict["Concentration"]["Value"]
            #     flush_volume = 500 # modify later
            #     flush_inecjtion_rate= 200
            #     mode_type=mode_type
            #     TaskLogger_obj.debug(self.batch_module_name, "Prepare Injection Queue --> {},{}mM,{}uL,{}uL/s".format(solution_name, concentration, flush_volume, flush_inecjtion_rate))
            # command_str=#     self.packetFormatter(jobID,"PUMP",action_type,solution_name,flush_volume,concentration,flush_inecjtion_rate,mode_type)
            #     TaskLogger_obj.debug("PUMP", "prepare solution-->Start!")
            #     # res_msg=self.callServer_BATCH(command_str=command_str)
            #     TaskLogger_obj.debug("PUMP", "prepare solution-->Done!")
            
            # Real Injection
            # self.ResourceManager_obj.updateStatus(current_func_name, True)
            command_str=self.packetFormatter(jobID,"LA","down",location_dict["Stirrer"][vial_task_idx],mode_type)
            TaskLogger_obj.debug("LA", "move down-->Start!")
            res_msg=self.callServer_BATCH(command_str=command_str)
            TaskLogger_obj.debug("LA", "move down-->Done!")
            # if process_number==1: # 만약 process number=1, 즉 solution 1개만 토출할 경우
            for _,solution_dict in enumerate(total_solution_queue) : # matching 1 vial --> 1 task
                action_type="single" # 1개의 용액 (not 1개의 pump)
                solution_name=solution_dict["Solution"]
                concentration=solution_dict["Concentration"]["Value"]
                concentration_dimension=solution_dict["Concentration"]["Dimension"]
                volume=solution_dict["Volume"]["Value"]
                volume_dimension=solution_dict["Volume"]["Dimension"]
                injection_rate=solution_dict["Injectionrate"]["Value"]
                injection_rate_dimension=solution_dict["Injectionrate"]["Dimension"]
                mode_type=mode_type
                TaskLogger_obj.debug(self.batch_module_name, "Start Injection Queue --> {},{}{},{}{},{}{}".format(solution_name, concentration, concentration_dimension, volume, volume_dimension, injection_rate, injection_rate_dimension))
                command_str=self.packetFormatter(jobID,"PUMP",action_type,[solution_name,volume,concentration,injection_rate],mode_type)
                TaskLogger_obj.debug("PUMP", "prepare solution-->Start!")
                res_msg=self.callServer_BATCH(command_str=command_str)
                TaskLogger_obj.debug("PUMP", "prepare solution-->Done!")
            # self.ResourceManager_obj.updateStatus(current_func_name, False)
            
            # elif process_number>1: # 만약 process number>1, 즉 solution 2개 이상 토출할 경우
            #     action_type="multi" # 여러개의 용액 (not 여러개의 pump)
            #     solution_name_list=[]
            #     volume_list=[]
            #     flow_rate_list=[]
            #     mode_type=mode_type
            #     for task_idx,solution_dict in enumerate(total_solution_queue): # matching 1 vial --> 1 task
            #         solution_name_list.append(solution_dict["Solution"])
            #         volume_list.append(solution_dict["Volume"]["Value"])
            #         flow_rate_list.append(solution_dict["Injectionrate"]["Value"])
            #     solution_name_str=""
            #     for i, solution_name in enumerate(solution_name_list):
            #         solution_name_str+=solution_name
            #         if i+1 == len(solution_name_list):
            #             break
            #         solution_name_str+=","
            #     volume_list_str=str(volume_list)[1:-1]
            #     flow_rate_list_str=str(flow_rate_list)[1:-1]
            # command_str=#     self.packetFormatter(jobID,"PUMP",action_type,solution_name_str,volume_list_str,flow_rate_list_str,mode_type)
            #     res_msg=self.callServer_PUMP(command_str=command_str)

            # self.ResourceManager_obj.updateStatus(current_func_name, True)
            command_str=self.packetFormatter(jobID,"LA","up",location_dict["Stirrer"][vial_task_idx],mode_type)
            TaskLogger_obj.debug("LA", "move up-->Start!")
            res_msg=self.callServer_BATCH(command_str=command_str)
            TaskLogger_obj.debug("LA", "move up-->Done!")
            # self.ResourceManager_obj.updateStatus(current_func_name, False)
            
            # self.ResourceManager_obj.updateStatus(current_func_name, True)
            command_str=self.packetFormatter(jobID,"LA","center","null",mode_type)
            TaskLogger_obj.debug("LA", "move center-->Start!")
            res_msg=self.callServer_BATCH(command_str=command_str)
            TaskLogger_obj.debug("LA", "move center-->Done!")
            self.ResourceManager_obj.updateStatus(current_func_name, False)

            TaskLogger_obj.debug(self.batch_module_name, "Finish Injection Queue")
            
            # initialize status of hardware
            
            # # have some time interval to receive another jobs' task
            # time.sleep(2)
            
        return res_msg

    def Stir(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Stir our stirrer depending on stir_queue

        {
            "Task":"Stir",
            "Data":
            // task_dict is here!
            {
                "Data":
                [
                    {
                        "StirRate":400,
                    }
                ]
            }
        }

        :param task_info_list (list): queue of stiirer stir work

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        for task_idx,task_dict in enumerate(task_info_list):
            # update status of hardware every batch
            TaskLogger_obj.current_module_name="{}-->{}".format(self.batch_module_name, "Stir")
            TaskLogger_obj.status="{}_{}/{}:{}".format(len(task_info_list), task_idx, TaskLogger_obj.totalExperimentNum, TaskLogger_obj.current_module_name) # in execution system
            # execute task
            TaskLogger_obj.debug(self.batch_module_name, "Start Stir Queue {} (Stirrer)".format(task_idx))
            stirrer_addr = self._allocateAddress(location_dict["Stirrer"][task_idx])
            stir_rate = task_dict["StirRate"]["Value"] # StirRate : rpm
            command_str=self.packetFormatter(jobID,"STIRRER","stir",[stirrer_addr,stir_rate],mode_type)
            res_msg = self.callServer_BATCH(command_str=command_str)
        for task_idx,task_dict in enumerate(task_info_list): # log 따로 작성하려고 일부러 만듬
            TaskLogger_obj.debug(self.batch_module_name, "Finish Stir Queue {} (Stirrer)".format(task_idx))

        return res_msg

    def Heat(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Heat our stirrer depending on task_info_list

        {
            "Task":"Heat",
            "Data":

            // this part is task_info_list //
                [
                    {
                        "Temperature":60,
                    }
                ]
            // this part is task_info_list //
        }

        :param task_info_list (list): queue of stiirer heat work

        return res_msg (str): response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        for task_idx,task_dict in enumerate(task_info_list):
            # update status of hardware every batch
            TaskLogger_obj.current_module_name="{}-->{}".format(self.batch_module_name, "Heat")
            TaskLogger_obj.status="{}_{}/{}:{}".format(len(task_info_list), task_idx, TaskLogger_obj.totalExperimentNum, TaskLogger_obj.current_module_name) # in execution system
            # execute task
            TaskLogger_obj.debug(self.batch_module_name, "Start Heat Queue {} (Stirrer)".format(task_idx))
            stirrer_addr = self._allocateAddress(location_dict["Stirrer"][task_idx])
            temperature = task_dict["Temperature"]["Value"] # Temperature : Celsius
            command_str=self.packetFormatter(jobID,"STIRRER","heat",[stirrer_addr,temperature],mode_type)
            res_msg = self.callServer_BATCH(command_str=command_str)
        for task_idx,task_dict in enumerate(task_info_list):
            TaskLogger_obj.debug(self.batch_module_name, "Finish Heat Queue {} (Stirrer)".format(task_idx))

        return res_msg

    def Mix(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        mix for secondes depending on mix queue

        {
            "Task": "Mix",
            "Data": 
            // this part is task_info_list //
            [
                {
                    "To": "Stirrer_0",
                        // this part is mix queue
                    "Data": {
                        "Time": 300
                    }
                }
            ]
            // this part is task_info_list //
        }

        :param task_info_list (list): queue of stiirer heat work

        :return res_msg (str): response message from Windows10 
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        mix_time=0
        # define waitTime function
        def mixTime(input_TaskLogger_obj, input_module_name, input_mix_time, input_task_idx, input_mode_type):
            # update status of hardware every batch
            TaskLogger_obj.current_module_name="{}-->{}".format(self.batch_module_name, "Mix")
            TaskLogger_obj.status="{}_{}/{}:{}".format(len(task_info_list), input_task_idx, TaskLogger_obj.totalExperimentNum, TaskLogger_obj.current_module_name) # in execution system
            # execute task
            input_TaskLogger_obj.debug(input_module_name, "Start Mix:{}s".format(input_mix_time))
            if input_mode_type == "real":
                time.sleep(input_mix_time)
            elif input_mode_type == "virtual":
                input_TaskLogger_obj.debug(input_module_name, "check Mix:{}s".format(input_mix_time))
            input_TaskLogger_obj.debug(input_module_name, "Finish Mix:{}s".format(input_mix_time))
        # generate thread
        thread_list=[]
        for task_idx, task_dict in enumerate(task_info_list):
            mix_time = task_dict["Time"]["Value"]
            thread = threading.Thread(target=mixTime, args=(TaskLogger_obj, self.batch_module_name, mix_time, task_idx, mode_type))
            thread_list.append(thread)
        # start thread
        for thread in thread_list: 
            thread.start()
        # main thread Mix thread termination
        for thread in thread_list:
            thread.join()

        res_msg = "Finish Mix:{}s".format(mix_time)
        
        return res_msg
    
    def React(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        React for secondes depending on react queue

        {
            "Task": "React",
            "Data": 
            // this part is task_info_list //
            [
                {
                    "To": "Stirrer_0",
                        // this part is react queue
                    "Data": {
                        "Time": 300
                    }
                }
            ]
            // this part is task_info_list //
        }

        :param task_info_list (list): queue of stiirer heat work

        :return res_msg (str): response message from Windows10 
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name

        # define Start jobExecution function
        def startReact(input_TaskLogger_obj, input_module_name, input_react_time, input_jobID, input_location_dict, input_task_idx, input_mode_type):
            # update status of hardware every batch
            input_TaskLogger_obj.current_module_name="{}-->{}".format(self.batch_module_name, "React")
            input_TaskLogger_obj.status="{}_{}/{}:{}".format(input_TaskLogger_obj.currentExperimentNum, input_task_idx, input_TaskLogger_obj.totalExperimentNum, input_TaskLogger_obj.current_module_name) # in execution system
            # execute task
            input_TaskLogger_obj.debug(input_module_name, "Start React:{}s".format(input_react_time))
            # stirrer_addr = self._allocateAddress(input_location_dict["Stirrer"][input_task_idx])
            if mode_type == "real":
                # initialize status of hardware
                self.ResourceManager_obj.updateStatus(current_func_name, False)
                time.sleep(input_react_time)
            elif input_mode_type == "virtual":
                time.sleep(10)
                # time.sleep(input_react_time)
                input_TaskLogger_obj.debug(input_module_name, "check React:{}s".format(input_react_time))
            
            # record our delay time
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str="{}~{}".format(taskStartTime, taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            
            # check & update status of hardware
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            command_str=self.packetFormatter(input_jobID,"LA","center","null",input_mode_type)
            TaskLogger_obj.debug("LA", "move center-->Start!")
            res_msg=self.callServer_BATCH(command_str=command_str)
            TaskLogger_obj.debug("LA", "move center-->Done!")

            self.ResourceManager_obj.updateStatus(current_func_name, True)
            command_str=self.packetFormatter(input_jobID,"DS_B",'stirrer_to_vialholder_batchsynthesis',[input_location_dict["Stirrer"][input_task_idx],input_location_dict["vialHolder"][input_task_idx]],input_mode_type)
            # command_str=input_self.packetFormatter(input_jobID,"DS_B",'stirrer_to_holder',input_location_dict["Stirrer"][input_task_idx],input_location_dict["vialHolder"][input_task_idx],input_mode_type)
            TaskLogger_obj.debug("DS_B", "stirrer_to_holder-->Start!")
            res_msg = self.callServer_BATCH(command_str=command_str)
            TaskLogger_obj.debug("DS_B", "stirrer_to_holder-->Done!")
            
            input_TaskLogger_obj.debug(self.batch_module_name, "Finish React:{}s".format(input_react_time))

            # initialize status of hardware
            self.ResourceManager_obj.updateStatus(current_func_name, False)
        
        # generate thread
        thread_list=[]
        react_time_list=[]
        for task_idx, task_dict in enumerate(task_info_list):
            react_time = task_dict["Time"]["Value"]
            react_time_list.append(react_time)
        for task_idx, react_time in enumerate(react_time_list):
            thread = threading.Thread(target=startReact, args=(TaskLogger_obj, self.batch_module_name, react_time, jobID, location_dict, task_idx, mode_type))
            thread_list.append(thread)
        # start thread
        for thread in thread_list: 
            thread.start()
        # main thread wait thread termination
        for thread in thread_list:
            thread.join()

        # command_str=# self.packetFormatter("STIRRER","stop",stirrer_addr,mode_type)
        # res_msg=self.callServer_BATCH(command_str=command_str)

        return res_msg


class UVModule(TCP_Class):
    """
    [UVModule] UVModule Class inherited UV and Pipette class

    # Variable
    :param module_name="UV Characterization module" (str): set UV Characterization module name (log name)
    :param mode_type="virtual" (str): set virtual or real mode

    # function
    1. _Cuvette2ExtractSolution(cycle_num, vialHolder_loc=0):
    2. GetUVdata(task_info_list):
    """
    def __init__(self,module_name="UV-Vis", ResourceManager_obj={}):
        self.uv_module_name = "{}".format(module_name) 
        TCP_Class.__init__(self,)
        self.UV_queue = Queue()
        self.the_number_of_tip = 96
        self.__initTipNum()
        self.ResourceManager_obj=ResourceManager_obj

    def __initTipNum(self):
        """
        initialize tip number depending on Queue.

        :return: None: 
        """
        for num in range(self.the_number_of_tip):
            self.UV_queue.put(num)  

    def __popTipNum(self):
        """
        pop tip number depending on Queue.

        :return: vial_num (int): get vial number in UV_queue
        """
        empty_true = self.UV_queue.empty()
        if empty_true==True:
            self.__initTipNum()
        tip_num=self.UV_queue.get()

        return tip_num    

    def __alertTipNum(self, TaskLogger_obj, mode_type="virtual"):
        text_content="[{}] tip number ({}) is not enough, please fill tip".format(self.uv_module_name, self.UV_queue.qsize())
        if self.UV_queue.qsize() <=10:
            AlertMessage(text_content=text_content, key_path="./Log", message_module_list=["dooray"], mode_type=mode_type)
        else:
            pass

    def _Cuvette2ExtractSolution(self, jobID, vialHolder_loc, tip_num, TaskLogger_obj, mode_type="virtual"):
        """
        extract solution into vial to cuvette

        :param vialHolder_loc (int): vialHolder's locations Number
        :param tip_num (int): tip_line//8 Number
        
        :(previous) param row_num (int): tip_line//8 Number
        :(previous) param column_num (int): tip_line%8 Number

        :return: res (str)
        """
        TaskLogger_obj.debug(self.uv_module_name, debug_msg="Start UV sample preparation")
        command_str=self.packetFormatter(jobID, "PIPETTE", "sample", ["20-200", 2, tip_num, vialHolder_loc, 0, 3], mode_type)
        res_msg=self.callServer_UV(command_str=command_str)
        # command_str=self.packetFormatter(jobID, "UVPIPETTE", "sample", "20-200", 2, tip_num, vialHolder_loc, 0, 3, mode_type)
        # res_msg=self.callServer_BATCH(command_str=command_str)
        TaskLogger_obj.debug(self.uv_module_name, debug_msg="Finish UV sample preparation")
        # TaskLogger_obj.debug(self.uv_module_name, debug_msg="Start UV sample preparation")
        # row_num=tip_num//8 # same  cycle_num
        # column_num=tip_num%8
        # command_str=self.packetFormatter("PIPETTE","sample",vialHolder_loc,str(chr(ord('A') + column_num) + str(row_num+1+1)),mode_type)
        # res_msg=self.callServer_BATCH(command_str=command_str)
        # TaskLogger_obj.debug(self.uv_module_name, debug_msg="Finish UV sample preparation")

        return res_msg

    def GetAbs(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        get UV data included _Cuvette2ExtractSolution() func

        :param task_info_list =
        [
            {
                "Setting": {
                    "Spectrometer": {
                        "DeviceName": "USB2000+",
                        "DetectionRange": "200-850nm",
                        "Solvent": {
                                "Solution": "H2O",
                                "Value": 2000,
                                "Dimension": "\u03bcL"
                        }
                    },
                    "LightSource": {
                        "DeviceName": "DH-2000-BAL",
                        "DetectionRange": "210-2500nm",
                        "Lamp": "deuterium(25W) and halogen lamps(20W)"
                    }
                }
            },
            ...
            ...
        ]
        :return: result_list (dict in list) ex) [{'Property': ['MaxAbsorbance', 'FWHM']}, ...]
        """
        # [{'Property': ['MaxAbsorbance', 'FWHM']}, ...]
        res_msg=""
        result_list=[]
        current_func_name=sys._getframe().f_code.co_name
        
        for task_idx, task_dict in enumerate(task_info_list):
            # check & update status of hardware
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus("PrepareCuvette") # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str="{}~{}".format(taskStartTime, taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            self.ResourceManager_obj.updateStatus("PrepareCuvette", True)
            
            # update status of hardware every batch
            TaskLogger_obj.current_module_name="{}-->{}".format(self.uv_module_name, "GetAbs")
            TaskLogger_obj.status="{}_{}/{}:{}".format(len(task_info_list), task_idx, TaskLogger_obj.totalExperimentNum, TaskLogger_obj.current_module_name) # in execution system
            # execute task
            TaskLogger_obj.debug(self.uv_module_name, "Trasfer colloid NP to UV vialholder")
            # calculate tip_num & column_num (=cycle_num)
            tip_num=self.__popTipNum()
            # row_num=tip_num//8 # same  cycle_num
            # column_num=tip_num%8
            
            # move cuvette_storage_to_cuvette_holder
            # command_str=self.packetFormatter(jobID,"DS_B",'vialholder_batchsynthesis_to_vialholder_UV', tip_num, location_dict["vialHolder"][task_idx], mode_type)
            # TaskLogger_obj.debug("DS_B", "vialholder_batchsynthesis_to_vialholder_UV-->Start!")
            # res_msg=self.callServer_BATCH(command_str=command_str)
            # TaskLogger_obj.debug("DS_B", "vialholder_batchsynthesis_to_vialholder_UV-->Done!")
            
            # execute task
            TaskLogger_obj.debug(self.uv_module_name, "Prepare UV-VIS container")
            # move cuvette_storage_to_cuvette_holder
            command_str=self.packetFormatter(jobID,"DS_B",'cuvette_storage_to_cuvette_holder', [tip_num, location_dict["vialHolder"][task_idx]], mode_type)
            TaskLogger_obj.debug("DS_B", "cuvette_storage_to_cuvette_holder-->Start!")
            res_msg=self.callServer_BATCH(command_str=command_str)
            TaskLogger_obj.debug("DS_B", "cuvette_storage_to_cuvette_holder-->Done!")

            # move Cuvette_holder_to_UV
            command_str=self.packetFormatter(jobID,"DS_B",'cuvette_holder_to_UV',[location_dict["vialHolder"][task_idx],0],mode_type)
            TaskLogger_obj.debug("DS_B", "cuvette_holder_to_UV-->Start!")
            res_msg=self.callServer_BATCH(command_str=command_str)
            TaskLogger_obj.debug("DS_B", "cuvette_holder_to_UV-->Done!")
            self.ResourceManager_obj.updateStatus("PrepareCuvette", False)

            # # Get Reference peaks
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            command_str=self.packetFormatter(jobID,"ABS","Reference","H2O",mode_type)
            TaskLogger_obj.debug("DS_B", "UV-VIS Characterization-->Start!")
            reference_str=self.callServer_UV(command_str=command_str)
            reference_dict=json.loads(reference_str)
            TaskLogger_obj.debug("DS_B", "UV-VIS Characterization-->Done!")

            # Sampling solution using pipetting machine
            # self.ResourceManager_obj.updateStatus(current_func_name, True)
            TaskLogger_obj.debug("DS_B", "Cuvette2ExtractSolution-->Start!")
            self._Cuvette2ExtractSolution(jobID=jobID,vialHolder_loc=location_dict["vialHolder"][task_idx], tip_num=tip_num+1, TaskLogger_obj=TaskLogger_obj, mode_type=mode_type)
            TaskLogger_obj.debug("DS_B", "Cuvette2ExtractSolution-->Done!")

            # Get Absorbance peaks
            # self.ResourceManager_obj.updateStatus(current_func_name, True)
            TaskLogger_obj.debug(self.uv_module_name, "Start UV-VIS Characterization")
            command_str=self.packetFormatter(jobID,"ABS","Abs","AgNP",mode_type)
            TaskLogger_obj.debug("DS_B", "UV-VIS Characterization-->Start!")
            absorbance_str=self.callServer_UV(command_str=command_str)
            absorbance_dict=json.loads(absorbance_str)
            TaskLogger_obj.debug("DS_B", "UV-VIS Characterization-->Done!")
            self.ResourceManager_obj.updateStatus(current_func_name, False)

            # move UV_to_Cuvette_storage
            self.ResourceManager_obj.updateStatus("StoreCuvette", True)
            command_str=self.packetFormatter(jobID,"DS_B",'UV_to_cuvette_storage',[0,tip_num],mode_type)
            TaskLogger_obj.debug("DS_B", "UV_to_cuvette_storage-->Start!")
            res_msg=self.callServer_BATCH(command_str=command_str)
            TaskLogger_obj.debug("DS_B", "UV_to_cuvette_storage-->Done!")

            # Caculate peaks
            WavelengthMin=task_dict["Hyperparameter"]["WavelengthMin"]["Value"]
            WavelengthMax=task_dict["Hyperparameter"]["WavelengthMax"]["Value"]
            BoxCarSize=task_dict["Hyperparameter"]["BoxCarSize"]["Value"]
            Prominence=task_dict["Hyperparameter"]["Prominence"]["Value"]
            PeakWidth=task_dict["Hyperparameter"]["PeakWidth"]["Value"]
            UV_result, each_calculate_res_dict=AnalysisUV.calculateUV_Data(absorbance_dict, reference_dict, WavelengthMin, WavelengthMax, BoxCarSize, Prominence, PeakWidth) 
            # UV_result --> OrderedDict([('lambdamax', [391.39295]), ('Intensity', [0.01058083862181636]), ('FWHM', [49.33331611590667])])"""
            TaskLogger_obj.debug(self.uv_module_name, "{} result : {}".format(task_idx, UV_result))
            # integrated_res_dict={
            #     "Setting":task_dict,
            #     "Data":each_calculate_res_dict
            # }
            task_dict["Data"]=each_calculate_res_dict
            result_list.append(task_dict)

            TaskLogger_obj.debug(self.uv_module_name, "Finish UV-VIS Characterization")

            # initialize status of hardware
            self.ResourceManager_obj.updateStatus("StoreCuvette", False)
        
        self.__alertTipNum(TaskLogger_obj, mode_type)

        return result_list


class TaskScheduler(RobotMovModule, BatchSynthesisModule, UVModule):
    """
    TaskScheduler class read recipe file (json), and allocate & link each task to proper devices
    
    # function
    def _get_data_by_module(self,module_key, module_dict)
    def _task2Device (action_type, task_info_list)
    def _scheduleAllTask(self, total_recipe_template_list:list, jobID:int, TaskLogger_obj:object, mode_type:str)
    def scheduleAlltask (total_recipe_template_list)
    """
    def __init__(self, serverLogger_obj:object, ResourceManager_obj:object, schedule_mode:str):
        self.serverLogger_obj=serverLogger_obj
        self.ResourceManager_obj=ResourceManager_obj

        self.module_name="TaskScheduler"
        self.schedule_mode=schedule_mode

        RobotMovModule.__init__(self, "RobotArm", self.ResourceManager_obj)
        BatchSynthesisModule.__init__(self, "Batch", self.ResourceManager_obj)
        UVModule.__init__(self, "UV-Vis", self.ResourceManager_obj)

        # Mobilemodule.__init__(self, "Mobile Robot module") # change later

        # print("self.task_hardware_status_dict",id(self.task_hardware_status_dict))
        # print("self.ResourceManager_obj.task_hardware_status_dict",id(self.ResourceManager_obj.task_hardware_status_dict))
    
    def _get_data_by_module(self,module_key, module_dict):
        for module_list in module_dict.values():
            for module_item in module_list:
                if module_item["Module"] == module_key:
                    return module_item["Data"]
        return None

    def _task2Device(self, action_type:str, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type:str):
        """
        allocate task to each hardware depending on task_info_list
        ***Caution : initialize syringe pump before we start*** 
        
        :param action_type (str): ex) "AddSolution", "Heat"...
        :param task_info_list (dicts in list): 

        :return: list(empty) or list(in characterization cases)
        """
        return_value = getattr(self, action_type)(task_info_list, jobID, location_dict, TaskLogger_obj, mode_type)
        if type(return_value) == str: # if action_type don't return some chemical data (AddSolution, Stir...)
            return return_value
        elif type(return_value) == list: # if action_type return some chemical data (measurement, calcination, UV...),
            return_result_list=[]
            for result_dict in return_value:
                temp_dict = {action_type:result_dict}
                return_result_list.append(temp_dict)
            return return_result_list

    def _scheduleAllTask(self, total_recipe_template_list:list, jobID:int, TaskLogger_obj:object, mode_type:str):
        total_result_lists_in_list=[]
        
        module_seq_list = [] # need this var to implement in location_dict
        for key, values in total_recipe_template_list[0].items(): 
            # key -> Synthesis, Preprocess, Evaluation, Characterization
            # values -> {"Module":[...]},{"Module":[...]},...
            for value in values:
                if "Module" in value:
                    module_seq_list.append(value["Module"])

        TaskLogger_obj.info(self.module_name, "check location: {}".format(self.ResourceManager_obj.task_hardware_location_dict))
        for module_idx, module_type in enumerate(module_seq_list):
            # module_type : Batch, Flow, Washing, Ink, UV, RDE, Electrode // if not --> pass!
            batch_num = len(total_recipe_template_list) # 배치가 8개면 8개
            # if module_idx+1 != len(module_seq_list):
                # location_dict=getattr(self.ResourceManager_obj, self.schedule_mode)(module_type, module_seq_list[module_idx+1], jobID, total_recipe_template_list)
            location_dict=self.ResourceManager_obj.allocateLocation(module_type, jobID, total_recipe_template_list)
            TaskLogger_obj.info(self.module_name, "{} is started, allocate location: {}".format(module_type, location_dict))
            TaskLogger_obj.info(self.module_name, "check location after allocation: {}".format(self.ResourceManager_obj.task_hardware_location_dict))
            
            # integrate and make matrix of recipe
            total_task_list=[]
            for each_recipe in total_recipe_template_list:
                each_task_list=self._get_data_by_module(module_type, each_recipe)
                total_task_list.append(each_task_list)

            # extract task depending on sequence --> allocate task to device
            batch_task_seq_num = len(total_task_list[0]) # the number of task sequence
            for each_batch_task_seq_idx in range(batch_task_seq_num): # each batch task 시퀀스 대로 for문 돌려서 batch 합성 진행
                action_type=""
                task_dict_list=[]# each task을 choose
                for each_batch_num in range(batch_num): # each vial 합성 시작
                    action_type=total_task_list[each_batch_num][each_batch_task_seq_idx]["Task"]
                    task_dict_list.append(total_task_list[each_batch_num][each_batch_task_seq_idx]["Data"])
                each_result_list=self._task2Device(action_type, task_dict_list, jobID, location_dict, TaskLogger_obj, mode_type)
                if type(each_result_list) == str: # return str excluding characterization & evaluation
                    pass
                elif type(each_result_list) == list: # return dict in list including characterization & evaluation
                    if len(each_result_list) > 0:
                        total_result_lists_in_list.append(each_result_list)
                    else: # nothing return
                        raise ValueError("There is no value in scheduler. Please check our node server.")
            location_dict=self.ResourceManager_obj.refreshModuleLocation(module_type, jobID)
            TaskLogger_obj.info(self.module_name, "{} is finished, location: {}".format(module_type, location_dict))
        
        return total_result_lists_in_list

    def scheduleAllTask(self, total_recipe_template_list:list, jobID:int, TaskLogger_obj:object, mode_type:str):
        """
        schdule all task using _task2Device func (큰 task들의 칸 수는 정해져있다고 가정... 나중에 병렬처리 가능할 때 새로운 scheduling 하는 function 만들기)

        :param total_recipe_template_list (list): total json in list // ex) if our batch size=8, it will be composed of [{},{},{},{},{},{},{},{}] each recipe

        --> total_result_lists_in_list (list (in dicts) of list)
        ex) [
                [{"GetAbs":{}},{"GetAbs":{}}, ...],
                [{"GetOverpotential":{}},{"GetOverpotential":{}} ...],...
            ]
        """
        total_result_lists_in_list=[] # 여기에 분석 결과를 저장

        # select task schedule mode
        if self.schedule_mode == "FCFS" or self.schedule_mode == "BackFill":
            # currentExperimentNum=TaskLogger_obj.currentExperimentNum
            TaskLogger_obj.currentExperimentNum(TaskLogger_obj.currentExperimentNum+len(total_recipe_template_list))
            TaskLogger_obj.status="{}/{}:{}".format(TaskLogger_obj.currentExperimentNum, TaskLogger_obj.totalExperimentNum, TaskLogger_obj.current_module_name) # in execution system
            total_result_lists_in_list=self._scheduleAllTask(total_recipe_template_list, jobID, TaskLogger_obj, mode_type)
        
        elif self.schedule_mode=="ClosedPacking":
            count_experiments_num=0
            total_experiments_num=len(total_recipe_template_list) # total numbers of experiments
            copied_total_recipe_template_list=list(copy.deepcopy(total_recipe_template_list)) # popped version
            while True:
                if count_experiments_num==total_experiments_num:
                    break
                # calculate possibile numbers of tasks based on present task_hardware_location_dict
                throughput_num=self.ResourceManager_obj.notifyNumbersOfTasks(copied_total_recipe_template_list)
                # set current experiment num
                TaskLogger_obj.currentExperimentNum=TaskLogger_obj.currentExperimentNum+throughput_num
                TaskLogger_obj.status="{}/{}:{}".format(TaskLogger_obj.currentExperimentNum, TaskLogger_obj.totalExperimentNum, TaskLogger_obj.current_module_name) # in execution system
                # pop possibile numbers of tasks based on present task_hardware_location_dict
                execute_recipe_list=[]
                for i in range(throughput_num):
                    popped_recipe=copied_total_recipe_template_list.pop(0)
                    execute_recipe_list.append(popped_recipe)
                return_result_lists_in_list=self._scheduleAllTask(execute_recipe_list, jobID, TaskLogger_obj, mode_type)
                if count_experiments_num!=0:
                    for module_idx, module_result_list in enumerate(return_result_lists_in_list):
                        total_result_lists_in_list[module_idx].extend(module_result_list)
                else:
                    total_result_lists_in_list=return_result_lists_in_list
                count_experiments_num+=throughput_num
        
        # refresh location information of self.task_hardware_location_dict (0 or 1 or 2 ... (jobID) --> ?)            
        self.ResourceManager_obj.refreshTotalLocation(jobID)
        TaskLogger_obj.info(self.module_name, "refresh location: {}".format(self.ResourceManager_obj.task_hardware_location_dict))

        # separate result data
        """
        ex) [
                [{"GetUVdata":{}},{"GetUVdata":{}}, ...],
                [{"GetElectrochemicaldata":{}},{"GetElectrochemicaldata":{}} ...],
                ...
            ]
        -->
            [
                [{"GetUVdata":{}},{"GetElectrochemicaldata":{}}, ...],
                [{"GetUVdata":{}},{"GetElectrochemicaldata":{}}, ...],
                ...
            ]
        """
        result_num=len(total_result_lists_in_list)
        batch_size=len(total_recipe_template_list)

        return_result_list_to_algorithm=[]
        for batch_idx in range(batch_size): # batch_size
            temp_dict={}
            for result_idx in range(result_num): # 분석 갯수
                temp_dict.update(total_result_lists_in_list[result_idx][batch_idx])
            return_result_list_to_algorithm.append(temp_dict)

        return return_result_list_to_algorithm