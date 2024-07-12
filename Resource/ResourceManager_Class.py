import time
import os, sys
import json, copy
import socket
# import numpy as np
import threading
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from more_itertools import locate
from Action.ActionExecutor_Class import ActionExecutor
from Resource.ResourceAllocator_Class import ResourceAllocator

class ResourceManager(ActionExecutor, ResourceAllocator):
    """
    ResourceManager class check status of devices, and update device information from NodeManager
    
    # function
    def requestDeviceInfo():
    def notifyNumbersOfTasks(total_recipe_template_list:list):
    def refreshDeviceLocation(module_type:str, device_type:str, jobID:int):
    def refreshModuleLocation(module_type:str, jobID:int):
    def refreshTotalLocation(jobID:int):
    def updateStatus(task_name:str, status:bool):
    def checkStatus(task_name:str):
    def allocateLocation(module_idx:int, module_type:str, jobID:int, total_recipe_template_list:list):
    """
    def __init__(self, module_list:list, serverLogger_obj:object):
        ActionExecutor.__init__(self,)
        ResourceAllocator.__init__(self,)
        self.serverLogger_obj=serverLogger_obj
        self.module_list=module_list
        self.component_name="ResourceManager"
        ################################
        # upload device location
        ################################
        with open(f"Resource/device_location.json", 'r', encoding='utf-8') as f:
            self.task_device_location_dict=json.load(f)
        ################################
        # upload device status
        ################################
        with open(f"Resource/device_status.json", 'r', encoding='utf-8') as f:
            self.task_device_status_dict=json.load(f)
        ##############################################################
        # upload masking table --> protect for collision between each devices
        ##############################################################
        with open(f"Resource/device_masking_table.json", 'r', encoding='utf-8') as f:
            self.task_device_mask_dict=json.load(f)
        ##############################################################
        # download device information (setting) and all devices action from module node
        ##############################################################
        self.task_device_info_dict, self.total_module_device_action_dict= self.requestDeviceInfo()

    def requestDeviceInfo(self):
        """
        request to all of platform to get detailed information about each devices.
        We use this function to map recipe based on config file. 
        (config file--> only set "AddSolution_Metal", recipe file 
            --> write more detail, ex) "AddSolution":{"Solution":"AgNO3"}
        
            (ex.Batch : pump 0 --> AgNO3, Pump 1 --> DI water... 
                Preprocess : Pipette --> 2-propanol, DI water...)
        total_device_info_dict=
        {
            "BatchSynthesis":{
                "Pump":{
                    "AgNO3":
                        {"SolutionType":"Metal",
                        "PumpAddress":1, # 0->1
                        "PumpUsbAddr":"/dev/ttyPUMP2",
                        "Resolution":1814000,
                        "Concentration":0.00125,
                        "SyringeVolume":5000,
                        "DeviceName":"CavroCentris"
                        },
                    "NaBH4":
                        {"SolutionType":"Reductant",
                        "PumpAddress":2,
                        "PumpUsbAddr":"/dev/ttyPUMP2",
                        "Resolution":1814000,
                        "Concentration":0.01,
                        "SyringeVolume":5000,
                        "DeviceName":"CavroCentris"
                        },
                    "H2O2":
                        {"SolutionType":"Oxidant",
                        "PumpAddress":3,
                        "PumpUsbAddr":"/dev/ttyPUMP1",
                        "Resolution":1814000,
                        "Concentration":0.375,
                        "Density":1.45,
                        "MolarMass":34.0147,
                        "SyringeVolume":5000,
                        "DeviceName":"CavroCentris"
                        },
                    "Citrate":
                        {"SolutionType":"CA",
                        "PumpAddress":4,
                        "PumpUsbAddr":"/dev/ttyPUMP1",
                        "Resolution":1814000,
                        "Concentration":0.02,
                        "SyringeVolume":5000,
                        "DeviceName":"CavroCentris"
                        },
                },
                "Pipette": {
                    "PVP55":
                        {"SolutionType":"CA",
                        "PumpAddress":5,
                        "PumpUsbAddr":"COM7",
                        "DeviceName":"20-200μL"}
                },
                "Stirrer":{
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
            ...
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
        :return: total_device_info_dict (dict), 
        """
        try:
            total_device_info_dict={}
            total_module_device_action_dict={}
            for module_name in self.module_list:
                total_device_info_dict[module_name] = json.loads(self.transferDeviceCommand(module_name, "None/{}/INFO/None/virtual".format(module_name)))
                total_module_device_action_dict[module_name] = json.loads(self.transferDeviceCommand(module_name, "None/{}/ACTION/None/virtual".format(module_name)))
                self.serverLogger_obj.info(self.component_name,"receive information of {}".format(module_name))
        except Exception as e:
            raise ConnectionError("Each module node cannot connect each device --> error message : {}".format(e))
        
        return total_device_info_dict, total_module_device_action_dict
    
    ##################################################
    # module로 옮기기  #
    ##################################################
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
    
    def notifyNumbersOfTasks(self, total_recipe_template_list:list):
        """
        :param total_recipe_template_list: reflect recipe information in device location

        :return iter_num (int) : return minmum iter_num due to ClosedPacking scheduling
        """
        module_seq_list = [] # need this var to implement in location_dict
        iter_num=0
        for values in total_recipe_template_list[0].values():
            for value in values:
                if "Module" in value:
                    module_seq_list.append(value["Module"])
        remained_resource_dict={}
        remained_resource_len_list=[]
        while True: # while satisfy "if" condition
            for device_name, device_resource_dict in self.task_device_location_dict[module_seq_list[0]].items():
                empty_resource_list=self.__find_indexes(device_resource_dict, "?")
                remained_resource_dict[device_name]=empty_resource_list
                remained_resource_len_list.append(len(empty_resource_list))
            if 0 not in remained_resource_len_list:
                break
        remained_resource_len_list.append(len(total_recipe_template_list))
        iter_num=min(remained_resource_len_list) # return minmum iter_num due to ClosedPacking scheduling
        return iter_num
    
    ##################################################
    # transfer를 하나로 만들어서 paramater에서 받기  #
    ##################################################
    def refreshDeviceLocation(self, module_type:str, device_type:str, jobID:int):
        """
        :param module_type (str): reflect process information of device location in module (BatchSynthesis, UV)
        :param jobID (int) : return job id

        :return self.task_device_location_dict[module_type] (dict)
        """
        device_values=self.task_device_location_dict[module_type][device_type]
        location_index_list=self.__find_indexes(device_values, jobID)
        for location_index in location_index_list:
            self.task_device_location_dict[module_type][device_type][location_index]="?"
        return self.task_device_location_dict[module_type]
    
    def refreshModuleLocation(self, module_type:str, jobID:int):
        """
        :param module_type (str): reflect process information of device location in module (BatchSynthesis, UV)
        :param jobID (int) : return job id

        :return self.task_device_location_dict[module_type] (dict)
        """
        for device_type, device_values in self.task_device_location_dict[module_type].items():
            location_index_list=self.__find_indexes(device_values, jobID)
            for location_index in location_index_list:
                self.task_device_location_dict[module_type][device_type][location_index]="?"
        return self.task_device_location_dict[module_type]

    ##################################################
    # transfer를 하나로 만들어서 paramater에서 받기  #
    ##################################################
    def refreshTotalLocation(self, jobID:int):
        """
        :param jobID (int) : return job id

        :return self.task_device_location_dict (dict)

        ex) self.task_device_location_dict={
            "BatchSynthesis":{ 
                "Stirrer":["?","?","?","?","?","?","?","?"], # "?"==empty
                "vialHolder":["?","?","?","?","?","?","?","?"]
            },
            "UV":{ 
                "vialHolder":["?","?","?","?","?","?","?","?"]
            }
        }
        """
        for module_type in self.task_device_location_dict.keys():
            self.refreshModuleLocation(module_type, jobID)
        return self.task_device_location_dict
    
    def updateStatus(self, task_name:str, status:bool):
        """
        :param task_name (str) : task name that you want to update 
        :return self.task_device_location_dict (dict)

        ex) 
        self.task_device_status_dict={
            "BatchSynthesisModule":{
                "BatchSynthesisModule_RoboticArm":False,
                "BatchSynthesisModule_VialStorage":False,
                "BatchSynthesisModule_LinearAcutator":True,
                "BatchSynthesisModule_Pump":False
            },
            "UVVisModule":{
                "UVVisModule_RoboticArm":False,
                "UVVisModule_Pipette":False,
                "UVVisModule_Spectroscopy":False
            }
        }
        self.task_device_mask_dict={
            "BatchSynthesisModule":{
                "BatchSynthesisModule_PrepareContainer":["BatchSynthesisModule_RoboticArm","BatchSynthesisModule_VialStorage","BatchSynthesisModule_LinearAcutator","UVVisModule_RoboticArm"],
                "BatchSynthesisModule_AddSolution":["BatchSynthesisModule_RoboticArm","BatchSynthesisModule_LinearAcutator","BatchSynthesisModule_Pump"],
                "BatchSynthesisModule_React":["BatchSynthesisModule_RoboticArm","BatchSynthesisModule_LinearAcutator","UVVisModule_RoboticArm"],
                "BatchSynthesisModule_MoveContainer":["BatchSynthesisModule_RoboticArm","BatchSynthesisModule_VialStorage","BatchSynthesisModule_LinearAcutator","UVVisModule_RoboticArm"],
            }
            "UVVisModule":{
                "UVVisModule_GetAbs":["BatchSynthesisModule_RoboticArm", "UVVisModule_RoboticArm", "UVVisModule_Pipette", "UVVisModule_Spectroscopy"],
            }
        }
        """
        # self.serverLogger_obj.debug(self.component_name,"start to update status")
        time.sleep(1)
        module_name, _=task_name.split("_")
        device_criterion_list=self.task_device_mask_dict[module_name][task_name]
        # thread function
        def update_status_each(input_device_name, input_status):
            split_module_name, _=input_device_name.split("_")
            self.task_device_status_dict[split_module_name][input_device_name]=input_status # UV_RoboticArm is okay. (not disturb in AddSolution task)
        # define thread
        thread_list=[]
        for device_name in device_criterion_list:
            thread = threading.Thread(target=update_status_each, args=(device_name, status))
            thread_list.append(thread)
        # start thread
        for thread in thread_list: 
            thread.start()
        # main thread wait thread termination
        for thread in thread_list:
            thread.join()
        # self.serverLogger_obj.debug(self.component_name,"finish to update status")

    def checkStatus(self, task_name:str):
        """
        :param task_name (str) : task name that you want to update 
        while True:
            if len(criterion_count_list)==len(device_criterion_list) and all(not item for item in criterion_count_list):
                break
        
        :return: int(delay_time)
        """
        # self.serverLogger_obj.debug(self.component_name,"start to check status")
        start_wait_time=time.time()
        finish_wait_time=start_wait_time
        while True:
            time.sleep(2)
            criterion_count_list=[]
            module_name, _=task_name.split("_")
            device_criterion_list=self.task_device_mask_dict[module_name][task_name]
            # thread function
            def countCriterion(input_device_name):
                split_module_name, _=input_device_name.split("_")
                criterion_count_list.append(self.task_device_status_dict[split_module_name][input_device_name])
            # define thread
            thread_list=[]
            for device_name in device_criterion_list:
                thread = threading.Thread(target=countCriterion, args=(device_name,))
                thread_list.append(thread)
            # start thread
            for thread in thread_list: 
                thread.start()
            # main thread wait thread termination
            for thread in thread_list:
                thread.join()
            if len(criterion_count_list)==len(device_criterion_list) and all(not item for item in criterion_count_list):
                finish_wait_time=time.time()
                break
        # self.serverLogger_obj.debug(self.component_name,"finish to check status")
        if round(finish_wait_time-start_wait_time, 2) < 5:
            delay_time=0
        else:
            delay_time=round(finish_wait_time-start_wait_time, 2)
        return delay_time
    
    def allocateLocation(self, module_name:str, jobID:int, total_recipe_template_list:list):
        """
        :param module_name: "BatchSynthesisModule", "FlowSynthesisModule", "UVVisModule" ... 
        :param jobID: allocate jobID in location_dict
        :param total_recipe_template_list: reflect recipe information in device location
        
        self.task_device_location_dict (dict)

        ex) self.task_device_location_dict={
                "Stirrer":["?","?","?","?","?","?","?","?"], # "?"==empty
                "vialHolder":["?","?","?","?","?","?","?","?"]
            }
        }
        """
        # allocate location information in self.location_dict depending on temperature 
        return_task_device_location_dict, self.task_device_location_dict = getattr(self, f"get{module_name}Resource")(module_name, jobID, total_recipe_template_list, self.task_device_location_dict)
        
        return return_task_device_location_dict
    

if __name__ == "__main__":
    ################################
    # upload device location
    ################################
    with open(f"Resource/device_location.json", 'r', encoding='utf-8') as f:
        task_device_location_dict=json.load(f)
    ################################
    # upload device status
    ################################
    with open(f"Resource/device_status.json", 'r', encoding='utf-8') as f:
        task_device_status_dict=json.load(f)
    ##############################################################
    # upload masking table --> protect for collision between each devices
    ##############################################################
    with open(f"Resource/device_masking_table.json", 'r', encoding='utf-8') as f:
        task_device_mask_dict=json.load(f)

    print(task_device_location_dict)
    print(task_device_status_dict)
    print(task_device_mask_dict)

    test=ResourceManager([], object)
    print(dir(test))