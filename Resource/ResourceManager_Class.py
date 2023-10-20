import time
import os, sys
import json, copy
import socket
# import numpy as np
import threading
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from more_itertools import locate
from Task.TCP import TCP_Class

class ResourceManager(TCP_Class):
    """
    ResourceManager class check status of devices, and update device information from NodeManager
    
    # function
    """
    def __init__(self, serverLogger_obj:object):
        TCP_Class.__init__(self,)
        self.serverLogger_obj=serverLogger_obj
        self.platform_name="ResourceManager"
        self.task_hardware_status_dict={
            "Batch_RoboticArm":False,
            "Batch_VialStorage":False,
            "Batch_LinearAcutator":False,
            "Batch_Pump":False,
            "UV_RoboticArm":False,
            "UV_Pipette":False,
            "UV_Spectroscopy":False
        }
        self.task_hardware_location_dict={
            "BatchSynthesis":{ 
                "Stirrer":["?"]*8,
                "vialHolder":["?"]*8
            },
            "UV":{ 
                "vialHolder":["?"]*8
            }
        }
        # protect for collision between each devices
        self.task_hardware_mask_dict={
            "PrepareContainer":["Batch_RoboticArm","Batch_VialStorage","Batch_LinearAcutator","UV_RoboticArm"],
            "AddSolution":["Batch_LinearAcutator","Batch_Pump"],
            "React":["Batch_RoboticArm","Batch_LinearAcutator","UV_RoboticArm"],
            "PrepareCuvette":["Batch_RoboticArm", "UV_RoboticArm", "UV_Pipette"],
            "GetAbs":["UV_RoboticArm", "UV_Pipette", "UV_Spectroscopy"],
            "StoreCuvette":["Batch_RoboticArm", "UV_RoboticArm", "UV_Pipette"],
            "MoveContainer":["Batch_RoboticArm","Batch_VialStorage","Batch_LinearAcutator","UV_RoboticArm"],
        }
        self.task_hardware_info_dict = self.requestHardwareInfo()

    def requestHardwareInfo(self):
        """
        request to all of platform to get detailed information about each devices.
        We use this function to map recipe based on config file. 
        (config file--> only set "AddSolution_Metal", recipe file 
            --> write more detail, ex) "AddSolution":{"Solution":"AgNO3"}
        
            (ex.Batch : pump 0 --> AgNO3, Pump 1 --> DI water... 
                Preprocess : Pipette --> 2-propanol, DI water...)

        total_hardware_info_dict={
            "BatchSynthesis":{
                "Pump":{
                    "AgNO3":
                        {"SolutionType":"Metal",
                        "PumpAddress":0,
                        "PumpUsbAddr":"COM8",
                        "Resolution:1814000
                        "DeviceName":"CavroCentris"
                        },
                    ...
                },
                "Pipette", {
                    "PVP55":
                        {"SolutionType":"CA",
                        "PumpAddress":5,
                        "PumpUsbAddr":"COM7",
                        "DeviceName":"20-200μL"}
                },
                "Stirrer:{
                    "Stirrer_0":{
                        "Address":0,
                        "Port":"COM5",
                        "DeviceName":"IKA_RET",
                        "Temperature":25
                    },
                    "Stirrer_1":{
                        "Address":0,
                        "Port":"COM6",
                        "DeviceName":"IKA_RET",
                        "Temperature":25
                    }
                },
                "LinearActuator":{
                },
                "VialStorage":{
                },
            },
            "UV":{
                "Spectrometer":{
                    "DeviceName":"USB2000+",
                    "DetectionRange":"200-850nm",
                    "Solvent":{
                        "Solution":"H2O",
                        "Value": 2000,
                        "Dimension": "μL"
                    }
                "LightSource":{
                    "DeviceName":"DH-2000-BAL",
                    }
                }
            }
        }
        :return: total_hardware_info_dict (dict), 
        """
        try:
            total_hardware_info_dict={}
            total_hardware_info_dict["BatchSynthesis"] = json.loads(self.callServer_BATCH())
            self.serverLogger_obj.info(self.platform_name,"receive information of BatchSynthesis")
            total_hardware_info_dict["UV"]=json.loads(self.callServer_UV())
            self.serverLogger_obj.info(self.platform_name,"receive information of UV-Vis")
            # total_hardware_info_dict["FLOW"] = self.callServer_BATCH()
            # total_hardware_info_dict["Washing"] = self.callServer_BATCH()
            # total_hardware_info_dict["Preprocess"] = self.callServer_BATCH()
            # total_hardware_info_dict["RDE"] = self.callServer_BATCH()
            # total_hardware_info_dict["Electrode"] = self.callServer_BATCH()
            # total_hardware_info_dict["UV"] = self.callServer_BATCH()
        except Exception as e:
            raise ConnectionError("Each hardware server cannot connect each device --> error message : {}".format(e))
        
        return total_hardware_info_dict
            
    def __find_indexes(self, lst:list, value:int):
        """
        extract index in lst, matching with value
        
        Examples
        ----------------
        >>> lst=[0,0,"?","?","?",0,0,0]
        >>> jobID=0
        >>> index_list = self.__find_indexes(lst, jobID)
        >>> print(index_list)
        [0,1,5,6,7] 
        """
        return list(locate(lst, lambda x: x == value))
        
    def allocateLocation(self, module_type:str, jobID:int, total_recipe_template_list:list):
        """
        :param module_type: "BatchSynthesis", "FlowSynthesis", "UV" ... 
        :param jobID: allocate jobID in location_dict
        :param total_recipe_template_list: reflect recipe information in hardware location
        """
        # allocate location information in self.location_dict depending on temperature 
        if module_type == "BatchSynthesis":

            Stirrer_set_temperature_list=[]
            for stirrer_value in list(self.task_hardware_info_dict["BatchSynthesis"]["Stirrer"].values()): # upload tempearture setting of stirrer
                Stirrer_set_temperature_list.append(stirrer_value["Temperature"])

            # search each temperature and stirrate setting in total_recipe_template_list
            temperature_in_recipe_list=[]
            # stirrate_list=[] # if we control stir, activate this
            for recipe in total_recipe_template_list:
                task_dict_list=[]
                for process_info in recipe["Synthesis"]:
                    if process_info["Module"]=="BatchSynthesis": # if locate BatchSynthesis in first
                        task_dict_list=process_info["Data"]
                for task_dict in task_dict_list:
                    if task_dict["Task"]=="Heat": # we split depending on temperature (differenet temperature --> different stirrer)
                        temperature_in_recipe_list.append(task_dict["Data"]["Temperature"]["Value"])
                    # if task_dict["Task"]!="Stir": # if we control stir, activate this
                    #     stirrate_list.append(task_dict["Data"]["StirRate"]["Value"])
                    else: # exclude AddSolution, Wait, React, Pipette...
                        pass

            if 50 in temperature_in_recipe_list: # mix some temperature include 50
                empty_stirrer_0_hole_index=[]
                empty_stirrer_1_hole_index=[]
                empty_vialHolder_index=[]
                while True: # while satisfy "if" condition
                    empty_stirrer_0_hole_index=self.__find_indexes(self.task_hardware_location_dict[module_type]["Stirrer"][:8], "?") # "?" == empty, calculate "?" or not
                    empty_stirrer_1_hole_index=self.__find_indexes(self.task_hardware_location_dict[module_type]["Stirrer"][8:], "?") # "?" == empty, calculate "?" or not
                    empty_vialHolder_index=self.__find_indexes(self.task_hardware_location_dict[module_type]["vialHolder"],"?") # "?" == empty
                    # match recipe information with spare location of stirrer
                    if temperature_in_recipe_list.count(25) <= len(empty_stirrer_0_hole_index) and \
                        temperature_in_recipe_list.count(50) <= len(empty_stirrer_1_hole_index) and \
                        len(temperature_in_recipe_list) <= len(empty_vialHolder_index):
                        break
                popped_stirrer_hole_index_list=[]
                popped_vialHolder_index_list=[]
                for idx, temperature in enumerate(temperature_in_recipe_list):
                    if temperature == 25:
                        popped_stirrer_hole_index=empty_stirrer_0_hole_index.pop(0) # pop first element in list
                        self.task_hardware_location_dict[module_type]["Stirrer"][popped_stirrer_hole_index]=jobID
                        popped_stirrer_hole_index_list.append(popped_stirrer_hole_index)
                    elif temperature == 50:
                        popped_stirrer_hole_index=empty_stirrer_1_hole_index.pop(0) # pop first element in list
                        self.task_hardware_location_dict[module_type]["Stirrer"][popped_stirrer_hole_index]=jobID
                        popped_stirrer_hole_index_list.append(popped_stirrer_hole_index) 
                    popped_vialHolder_index=empty_vialHolder_index.pop(0) # pop first element in list
                    self.task_hardware_location_dict[module_type]["vialHolder"][popped_vialHolder_index]=jobID
                    popped_vialHolder_index_list.append(popped_vialHolder_index)
            
            else: # all temperature set 25 (RT)
                empty_stirrer_hole_index=[]
                empty_vialHolder_index=[]
                while True: # while satisfy "if" condition
                    empty_stirrer_hole_index=self.__find_indexes(self.task_hardware_location_dict[module_type]["Stirrer"], "?") # "?" == empty
                    empty_vialHolder_index=self.__find_indexes(self.task_hardware_location_dict[module_type]["vialHolder"],"?") # "?" == empty
                    if temperature_in_recipe_list.count(25) <= len(empty_stirrer_hole_index) and len(temperature_in_recipe_list) <= len(empty_vialHolder_index):
                        break
                popped_stirrer_hole_index_list=[]
                popped_vialHolder_index_list=[]
                for idx in range(len(temperature_in_recipe_list)):

                    popped_stirrer_hole_index=empty_stirrer_hole_index.pop(0) # pop first element in list
                    self.task_hardware_location_dict[module_type]["Stirrer"][popped_stirrer_hole_index]=jobID
                    popped_stirrer_hole_index_list.append(popped_stirrer_hole_index)

                    popped_vialHolder_index=empty_vialHolder_index.pop(0) # pop first element in list
                    self.task_hardware_location_dict[module_type]["vialHolder"][popped_vialHolder_index]=jobID
                    popped_vialHolder_index_list.append(popped_vialHolder_index)

            task_location_dict={
                "Stirrer":popped_stirrer_hole_index_list,
                "vialHolder":popped_vialHolder_index_list
            }

        elif module_type=="UV":
            # empty_vialHolder_index_list=self.__find_indexes(self.task_hardware_location_dict[module_type]["vialHolder"], "?")
            # popped_vialHolder_index_list=[]
            # while True: # while satisfy "if" condition
            #     if len(total_recipe_template_list) <= len(empty_vialHolder_index_list):
            #         break
            # for idx in range(len(total_recipe_template_list)):
            #     popped_vialHolder_index=empty_vialHolder_index_list.pop(0) # pop first element in list
            #     self.task_hardware_location_dict[module_type]["vialHolder"][popped_vialHolder_index]=jobID
            #     popped_vialHolder_index_list.append(popped_vialHolder_index)
            # task_location_dict={
            #     "vialHolder":popped_vialHolder_index_list
            # }
            popped_vialHolder_index_list=[]
            while True: # while satisfy "if" condition
                empty_vialHolder_index_list=self.__find_indexes(self.task_hardware_location_dict[module_type]["vialHolder"], "?")
                if len(total_recipe_template_list) <= len(empty_vialHolder_index_list):
                    break
            for idx in range(len(total_recipe_template_list)):
                popped_vialHolder_index=empty_vialHolder_index_list.pop(0) # pop first element in list
                self.task_hardware_location_dict[module_type]["vialHolder"][popped_vialHolder_index]=jobID
                popped_vialHolder_index_list.append(popped_vialHolder_index)
            task_location_dict={
                "vialHolder":popped_vialHolder_index_list
            }

        return task_location_dict

    def notifyNumbersOfTasks(self, total_recipe_template_list:list):
        """
        :param total_recipe_template_list: reflect recipe information in hardware location

        :return iter_num (int) : return minmum iter_num due to ClosedPacking scheduling
        """
        module_seq_list = [] # need this var to implement in location_dict
        iter_num=0
        for key, values in total_recipe_template_list[0].items():
            for value in values:
                if "Module" in value:
                    module_seq_list.append(value["Module"])
        # "The reason for looking at module_seq_list[0]: I'll be dealing with the later processes anyway.". 
        # "If the process that needs to start immediately is available, go ahead and run it."
        if "BatchSynthesis"==module_seq_list[0]:
            while True: # while satisfy "if" condition
                empty_stirrer_index_list=self.__find_indexes(self.task_hardware_location_dict[module_seq_list[0]]["Stirrer"], "?")
                empty_vialHolder_index_list=self.__find_indexes(self.task_hardware_location_dict[module_seq_list[0]]["vialHolder"], "?")
                if len(empty_stirrer_index_list)!=0 and len(empty_vialHolder_index_list)!=0:
                    break
            iter_num_list=[len(total_recipe_template_list), len(empty_stirrer_index_list), len(empty_vialHolder_index_list)]
        elif "UV"==module_seq_list[0]:
            while True: # while satisfy "if" condition
                empty_vialHolder_index_list=self.__find_indexes(self.task_hardware_location_dict[module_seq_list[0]]["vialHolder"], "?")
                if len(empty_vialHolder_index_list)!=0:
                    break
            iter_num_list=[len(total_recipe_template_list), len(empty_vialHolder_index_list)]
        iter_num=min(iter_num_list) # return minmum iter_num due to ClosedPacking scheduling
        return iter_num
    
    def refreshModuleLocation(self, module_type:str, jobID:int):
        """
        :param module_type (str): reflect process information of hardware location in module (BatchSynthesis, UV)
        :param jobID (int) : return job id

        :return self.task_hardware_location_dict[module_type] (dict)
        """
        for device_type, device_values in self.task_hardware_location_dict[module_type].items():
            location_index_list=self.__find_indexes(device_values, jobID)
            for location_index in location_index_list:
                self.task_hardware_location_dict[module_type][device_type][location_index]="?"
        return self.task_hardware_location_dict[module_type]

    def refreshTotalLocation(self, jobID:int):
        """
        :param jobID (int) : return job id

        :return self.task_hardware_location_dict (dict)

        ex) self.task_hardware_location_dict={
            "BatchSynthesis":{ 
                "Stirrer":["?","?","?","?","?","?","?","?"], # "?"==empty
                "vialHolder":["?","?","?","?","?","?","?","?"]
            },
            "UV":{ 
                "vialHolder":["?","?","?","?","?","?","?","?"]
            }
        }
        """
        for module_type in self.task_hardware_location_dict.keys():
            self.refreshModuleLocation(module_type, jobID)
            # for device_type, device_values in module_values.items():
            #     location_index_list=self.__find_indexes(device_values, jobID)
            #     for location_index in location_index_list:
            #         self.task_hardware_location_dict[module_type][device_type][location_index]="?"
        return self.task_hardware_location_dict
    
    def updateStatus(self, task_name:str, status:bool):
        """
        :param task_name (str) : task name that you want to update 
        :return self.task_hardware_location_dict (dict)

        ex) self.task_hardware_status_dict={
            "Batch_RoboticArm":False,
            "Batch_VialStorage":False,
            "Batch_LinearAcutator":False,
            "Batch_Pump":False,
            "UV_RoboticArm":False,
            "UV_Pipette":False,
            "UV_Spectroscopy":False
        }
        self.task_hardware_mask_dict={
            "PrepareContainer":["Batch_RoboticArm","Batch_VialStorage","Batch_LinearAcutator","UV_RoboticArm"],
            "AddSolution":["Batch_RoboticArm","Batch_LinearAcutator","Batch_Pump"],
            "React":["Batch_RoboticArm","Batch_LinearAcutator","UV_RoboticArm"],
            "GetAbs":["Batch_RoboticArm", "UV_RoboticArm", "UV_Pipette", "UV_Spectroscopy"],
            "MoveContainer":["Batch_RoboticArm","Batch_VialStorage","Batch_LinearAcutator","UV_RoboticArm"],
        }
        """
        # self.serverLogger_obj.debug(self.platform_name,"start to update status")
        time.sleep(1)
        hardware_criterion_list=self.task_hardware_mask_dict[task_name]
        
        # thread function
        def update_status_each(input_hardware_name, input_status):
            self.task_hardware_status_dict[input_hardware_name]=input_status # UV_RoboticArm is okay. (not disturb in AddSolution task)
        # define thread
        thread_list=[]
        for hardware_name in hardware_criterion_list:
            thread = threading.Thread(target=update_status_each, args=(hardware_name, status))
            thread_list.append(thread)
        # start thread
        for thread in thread_list: 
            thread.start()
        # main thread wait thread termination
        for thread in thread_list:
            thread.join()
        # self.serverLogger_obj.debug(self.platform_name,"finish to update status")

    def checkStatus(self, task_name:str):
        """
        :param task_name (str) : task name that you want to update 
        while True:
            if len(criterion_count_list)==len(hardware_criterion_list) and all(not item for item in criterion_count_list):
                break
        
        :return: int(delay_time)
        """
        # self.serverLogger_obj.debug(self.platform_name,"start to check status")
        start_wait_time=time.time()
        finish_wait_time=start_wait_time
        while True:
            time.sleep(2)
            criterion_count_list=[]
            hardware_criterion_list=self.task_hardware_mask_dict[task_name]
            # thread function
            def countCriterion(hardware_name):
                criterion_count_list.append(self.task_hardware_status_dict[hardware_name])
            # define thread
            thread_list=[]
            for hardware_name in hardware_criterion_list:
                thread = threading.Thread(target=countCriterion, args=(hardware_name,))
                thread_list.append(thread)
            # start thread
            for thread in thread_list: 
                thread.start()
            # main thread wait thread termination
            for thread in thread_list:
                thread.join()
            if len(criterion_count_list)==len(hardware_criterion_list) and all(not item for item in criterion_count_list):
                finish_wait_time=time.time()
                break
        # self.serverLogger_obj.debug(self.platform_name,"finish to check status")
        if round(finish_wait_time-start_wait_time, 2) < 5:
            delay_time=0
        else:
            delay_time=round(finish_wait_time-start_wait_time, 2)
        return delay_time