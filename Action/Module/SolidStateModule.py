# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [SolidStateModule] SolidStateModule class file
# author Hyuk Jun Yoo (yoohj9475@kist.re.kr)
# GENEREATION 2024-07-12 14:14:10

from queue import Queue
import time
import os, sys
import json, copy
import threading
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pydantic import ValidationError
from Analysis.Analysis import calculateData
from Log.DigitalSecretary import AlertMessage
from Action.ActionExecutor_Class import ActionExecutor
from Task.Pydantic.SolidStateModule import *


class SolidStateModule(ActionExecutor):
    """
    [SolidStateModule] SolidStateModule class 

    # Variable
    :param module_name="SolidStateModule" (str): set module name
    :param ResourceManager_obj=object (object): set resource manager object

    # Device : Actions
    {'RobotArm': ['Move', 'Rotate', 'Lift', 'Lower', 'Grasp', 'Release', 'Position', 'Retrieve', 'Place'], 'Pipette': ['Aspirate', 'Dispense', 'Rinse', 'Mix', 'Eject', 'Calibrate'], 'Pump': ['Start', 'Stop', 'Increase', 'Decrease', 'Reverse'], 'Stirrer': ['Stir', 'Stop'], 'PowderDispenser': ['Dispense', 'Stop'], 'WeighingMachine': ['Weigh', 'Tare', 'Stop'], 'Heater': ['Heat', 'Cool', 'Stop']}

    # Task --> device_action list
    {'SolidStateModule_LoadSample': ['RobotArm_Move', 'RobotArm_Grasp', 'RobotArm_Place'], 'SolidStateModule_AddPowder': ['RobotArm_Move', 'RobotArm_Grasp', 'PowderDispenser_Dispense', 'RobotArm_Release'], 'SolidStateModule_MixPowders': ['Stirrer_Stir'], 'SolidStateModule_PressPowder': ['RobotArm_Move', 'RobotArm_Grasp', 'RobotArm_Position', 'RobotArm_Release'], 'SolidStateModule_Heat': ['Heater_Heat'], 'SolidStateModule_Cool': ['Heater_Cool'], 'SolidStateModule_Grind': ['RobotArm_Move', 'RobotArm_Grasp', 'RobotArm_Position', 'RobotArm_Release'], 'SolidStateModule_Pelletize': ['RobotArm_Move', 'RobotArm_Grasp', 'RobotArm_Position', 'RobotArm_Release'], 'SolidStateModule_Weigh': ['WeighingMachine_Tare', 'WeighingMachine_Weigh'], 'SolidStateModule_Transfer': ['RobotArm_Move', 'RobotArm_Grasp', 'RobotArm_Position', 'RobotArm_Release'], 'SolidStateModule_Wash': ['Pipette_Aspirate', 'Pipette_Dispense', 'Pipette_Rinse'], 'SolidStateModule_Dry': ['Heater_Heat']}

    # function
        
    1. SolidStateModule_LoadSample(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    2. SolidStateModule_AddPowder(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    3. SolidStateModule_MixPowders(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    4. SolidStateModule_PressPowder(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    5. SolidStateModule_Heat(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    6. SolidStateModule_Cool(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    7. SolidStateModule_Grind(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    8. SolidStateModule_Pelletize(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    9. SolidStateModule_Weigh(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    10. SolidStateModule_Transfer(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    11. SolidStateModule_Wash(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    12. SolidStateModule_Dry(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')

    """
    def __init__(self,module_name="SolidStateModule", ResourceManager_obj=object):
        ActionExecutor.__init__(self,)
        self.__SolidStateModule_name= module_name
        self.ResourceManager_obj=ResourceManager_obj

    def executeAction(self, module_name:str, jobID:int, device_name:str, action_type:str, action_data:Union[str, int, list], mode_type:str, TaskLogger_obj:object, data_dict:dict):
        TaskLogger_obj.debug(device_name, f"{action_type}-->Start!")
        command_str=self.packetFormatter(jobID,device_name,action_type,action_data,mode_type)
        TaskLogger_obj.debug(device_name, f"{action_type}-->Done!")
        res_msg = self.transferDeviceCommand(module_name, command_str=command_str)
        try:
            res_dict=json.loads(res_msg)
            data_dict[action_type]=res_dict
        except json.decoder.JSONDecodeError:
            pass
        return data_dict
        
    def SolidStateModule_LoadSample(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"SolidStateModule_LoadSample","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__SolidStateModule_name, "Start "+current_func_name+" Queue")
        result_list=[]
        
        for task_idx, task_dict in enumerate(task_info_list): # for each vial
            
            # check & update status of device
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str=str(taskStartTime)+"~"+str(taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            # update status of device every batch
            TaskLogger_obj.current_module_name=self.__SolidStateModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = SolidStateModule_LoadSample_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['RobotArm_Move', 'RobotArm_Grasp', 'RobotArm_Place']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "SolidStateModule_LoadSample",
    "Data": {
        "Device": {},
        "Material": {
            "Type": ""
        }
    }
}
            4. task_idx
            """
            data_dict=dict()
            # data_dict["Reference"]=reference_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
            # data_dict["Absorbance"]=absorbance_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
        
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Move","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Grasp","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Place","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)

        TaskLogger_obj.debug(self.__SolidStateModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def SolidStateModule_AddPowder(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"SolidStateModule_AddPowder","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__SolidStateModule_name, "Start "+current_func_name+" Queue")
        result_list=[]
        
        for task_idx, task_dict in enumerate(task_info_list): # for each vial
            
            # check & update status of device
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str=str(taskStartTime)+"~"+str(taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            # update status of device every batch
            TaskLogger_obj.current_module_name=self.__SolidStateModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = SolidStateModule_AddPowder_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['RobotArm_Move', 'RobotArm_Grasp', 'PowderDispenser_Dispense', 'RobotArm_Release']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
                "Task": "SolidStateModule_AddPowder",
                "Data": {
                    "Material": {
                        "Type": ""
                    },
                    "Amount": {
                        "Value": 0,
                        "Dimension": "g"
                    },
                    "Device": {}
                }
            }
            4. task_idx
            """
            data_dict=dict()
            # data_dict["Reference"]=reference_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
            # data_dict["Absorbance"]=absorbance_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
        
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            action_data=location_dict["Stirrer"][task_idx]
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Move",action_data,mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            action_data="None"
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Grasp",action_data,mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            action_data=[task_dict["Material"], task_dict["Amount"]["Value"], task_dict["Amount"]["Dimension"]]
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"PowderDispenser","Dispense",action_data,mode_type,TaskLogger_obj,data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            action_data="None"
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Release",action_data,mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)

        TaskLogger_obj.debug(self.__SolidStateModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def SolidStateModule_MixPowders(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"SolidStateModule_MixPowders","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__SolidStateModule_name, "Start "+current_func_name+" Queue")
        result_list=[]
        
        for task_idx, task_dict in enumerate(task_info_list): # for each vial
            
            # check & update status of device
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str=str(taskStartTime)+"~"+str(taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            # update status of device every batch
            TaskLogger_obj.current_module_name=self.__SolidStateModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = SolidStateModule_MixPowders_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['Stirrer_Stir']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "SolidStateModule_MixPowders",
    "Data": {
        "Time": {
            "Value": 0,
            "Dimension": "sec"
        },
        "Device": {}
    }
}
            4. task_idx
            """
            data_dict=dict()
            # data_dict["Reference"]=reference_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
            # data_dict["Absorbance"]=absorbance_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
        
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"Stirrer","Stir","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)

        TaskLogger_obj.debug(self.__SolidStateModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def SolidStateModule_PressPowder(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"SolidStateModule_PressPowder","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__SolidStateModule_name, "Start "+current_func_name+" Queue")
        result_list=[]
        
        for task_idx, task_dict in enumerate(task_info_list): # for each vial
            
            # check & update status of device
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str=str(taskStartTime)+"~"+str(taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            # update status of device every batch
            TaskLogger_obj.current_module_name=self.__SolidStateModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = SolidStateModule_PressPowder_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['RobotArm_Move', 'RobotArm_Grasp', 'RobotArm_Position', 'RobotArm_Release']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "SolidStateModule_PressPowder",
    "Data": {
        "Pressure": {
            "Value": 0,
            "Dimension": "Pa"
        },
        "Device": {}
    }
}
            4. task_idx
            """
            data_dict=dict()
            # data_dict["Reference"]=reference_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
            # data_dict["Absorbance"]=absorbance_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
        
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Move","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Grasp","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Position","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Release","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)

        TaskLogger_obj.debug(self.__SolidStateModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def SolidStateModule_Heat(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"SolidStateModule_Heat","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__SolidStateModule_name, "Start "+current_func_name+" Queue")
        result_list=[]
        
        for task_idx, task_dict in enumerate(task_info_list): # for each vial
            
            # check & update status of device
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str=str(taskStartTime)+"~"+str(taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            # update status of device every batch
            TaskLogger_obj.current_module_name=self.__SolidStateModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = SolidStateModule_Heat_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['Heater_Heat']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "SolidStateModule_Heat",
    "Data": {
        "Temperature": {
            "Value": 0,
            "Dimension": "ºC"
        },
        "Device": {}
    }
}
            4. task_idx
            """
            data_dict=dict()
            # data_dict["Reference"]=reference_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
            # data_dict["Absorbance"]=absorbance_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
        
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"Heater","Heat","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)

        TaskLogger_obj.debug(self.__SolidStateModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def SolidStateModule_Cool(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"SolidStateModule_Cool","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__SolidStateModule_name, "Start "+current_func_name+" Queue")
        result_list=[]
        
        for task_idx, task_dict in enumerate(task_info_list): # for each vial
            
            # check & update status of device
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str=str(taskStartTime)+"~"+str(taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            # update status of device every batch
            TaskLogger_obj.current_module_name=self.__SolidStateModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = SolidStateModule_Cool_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['Heater_Cool']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "SolidStateModule_Cool",
    "Data": {
        "Temperature": {
            "Value": 0,
            "Dimension": "ºC"
        },
        "Device": {}
    }
}
            4. task_idx
            """
            data_dict=dict()
            # data_dict["Reference"]=reference_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
            # data_dict["Absorbance"]=absorbance_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
        
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"Heater","Cool","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)

        TaskLogger_obj.debug(self.__SolidStateModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def SolidStateModule_Grind(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"SolidStateModule_Grind","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__SolidStateModule_name, "Start "+current_func_name+" Queue")
        result_list=[]
        
        for task_idx, task_dict in enumerate(task_info_list): # for each vial
            
            # check & update status of device
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str=str(taskStartTime)+"~"+str(taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            # update status of device every batch
            TaskLogger_obj.current_module_name=self.__SolidStateModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = SolidStateModule_Grind_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['RobotArm_Move', 'RobotArm_Grasp', 'RobotArm_Position', 'RobotArm_Release']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "SolidStateModule_Grind",
    "Data": {
        "Time": {
            "Value": 0,
            "Dimension": "sec"
        },
        "Device": {}
    }
}
            4. task_idx
            """
            data_dict=dict()
            # data_dict["Reference"]=reference_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
            # data_dict["Absorbance"]=absorbance_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
        
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Move","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Grasp","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Position","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Release","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)

        TaskLogger_obj.debug(self.__SolidStateModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def SolidStateModule_Pelletize(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"SolidStateModule_Pelletize","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__SolidStateModule_name, "Start "+current_func_name+" Queue")
        result_list=[]
        
        for task_idx, task_dict in enumerate(task_info_list): # for each vial
            
            # check & update status of device
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str=str(taskStartTime)+"~"+str(taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            # update status of device every batch
            TaskLogger_obj.current_module_name=self.__SolidStateModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = SolidStateModule_Pelletize_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['RobotArm_Move', 'RobotArm_Grasp', 'RobotArm_Position', 'RobotArm_Release']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "SolidStateModule_Pelletize",
    "Data": {
        "Pressure": {
            "Value": 0,
            "Dimension": "Pa"
        },
        "Device": {}
    }
}
            4. task_idx
            """
            data_dict=dict()
            # data_dict["Reference"]=reference_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
            # data_dict["Absorbance"]=absorbance_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
        
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Move","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Grasp","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Position","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Release","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)

        TaskLogger_obj.debug(self.__SolidStateModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def SolidStateModule_Weigh(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"SolidStateModule_Weigh","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__SolidStateModule_name, "Start "+current_func_name+" Queue")
        result_list=[]
        
        for task_idx, task_dict in enumerate(task_info_list): # for each vial
            
            # check & update status of device
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str=str(taskStartTime)+"~"+str(taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            # update status of device every batch
            TaskLogger_obj.current_module_name=self.__SolidStateModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = SolidStateModule_Weigh_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['WeighingMachine_Tare', 'WeighingMachine_Weigh']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "SolidStateModule_Weigh",
    "Data": {
        "Method": {
            "Type": ""
        },
        "Device": {}
    }
}
            4. task_idx
            """
            data_dict=dict()
            # data_dict["Reference"]=reference_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
            # data_dict["Absorbance"]=absorbance_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
        
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"WeighingMachine","Tare","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"WeighingMachine","Weigh","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)

        TaskLogger_obj.debug(self.__SolidStateModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def SolidStateModule_Transfer(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"SolidStateModule_Transfer","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__SolidStateModule_name, "Start "+current_func_name+" Queue")
        result_list=[]
        
        for task_idx, task_dict in enumerate(task_info_list): # for each vial
            
            # check & update status of device
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str=str(taskStartTime)+"~"+str(taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            # update status of device every batch
            TaskLogger_obj.current_module_name=self.__SolidStateModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = SolidStateModule_Transfer_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['RobotArm_Move', 'RobotArm_Grasp', 'RobotArm_Position', 'RobotArm_Release']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "SolidStateModule_Transfer",
    "Data": {
        "FromTo": {
            "Type": ""
        },
        "Device": {}
    }
}
            4. task_idx
            """
            data_dict=dict()
            # data_dict["Reference"]=reference_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
            # data_dict["Absorbance"]=absorbance_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
        
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Move","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Grasp","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Position","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Release","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)

        TaskLogger_obj.debug(self.__SolidStateModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def SolidStateModule_Wash(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"SolidStateModule_Wash","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__SolidStateModule_name, "Start "+current_func_name+" Queue")
        result_list=[]
        
        for task_idx, task_dict in enumerate(task_info_list): # for each vial
            
            # check & update status of device
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str=str(taskStartTime)+"~"+str(taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            # update status of device every batch
            TaskLogger_obj.current_module_name=self.__SolidStateModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = SolidStateModule_Wash_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['Pipette_Aspirate', 'Pipette_Dispense', 'Pipette_Rinse']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "SolidStateModule_Wash",
    "Data": {
        "Solvent": {
            "Type": ""
        },
        "Volume": {
            "Value": 0,
            "Dimension": "mL"
        },
        "Device": {}
    }
}
            4. task_idx
            """
            data_dict=dict()
            # data_dict["Reference"]=reference_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
            # data_dict["Absorbance"]=absorbance_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
        
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"Pipette","Aspirate","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"Pipette","Dispense","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"Pipette","Rinse","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)

        TaskLogger_obj.debug(self.__SolidStateModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def SolidStateModule_Dry(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"SolidStateModule_Dry","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__SolidStateModule_name, "Start "+current_func_name+" Queue")
        result_list=[]
        
        for task_idx, task_dict in enumerate(task_info_list): # for each vial
            
            # check & update status of device
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str=str(taskStartTime)+"~"+str(taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            # update status of device every batch
            TaskLogger_obj.current_module_name=self.__SolidStateModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = SolidStateModule_Dry_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['Heater_Heat']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "SolidStateModule_Dry",
    "Data": {
        "Temperature": {
            "Value": 0,
            "Dimension": "ºC"
        },
        "Time": {
            "Value": 0,
            "Dimension": "sec"
        },
        "Device": {}
    }
}
            4. task_idx
            """
            data_dict=dict()
            # data_dict["Reference"]=reference_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
            # data_dict["Absorbance"]=absorbance_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
        
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"Heater","Heat","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)

        TaskLogger_obj.debug(self.__SolidStateModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            