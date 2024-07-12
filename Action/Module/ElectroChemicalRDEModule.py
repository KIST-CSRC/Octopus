# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [ElectroChemicalRDEModule] ElectroChemicalRDEModule class file
# author Hyuk Jun Yoo (yoohj9475@kist.re.kr)
# GENEREATION 2024-06-26 13:51:49

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
from Task.Pydantic.ElectroChemicalRDEModule import *


class ElectroChemicalRDEModule(ActionExecutor):
    """
    [ElectroChemicalRDEModule] ElectroChemicalRDEModule class 

    # Variable
    :param module_name="ElectroChemicalRDEModule" (str): set module name
    :param ResourceManager_obj=object (object): set resource manager object

    # Device : Actions
    {'RobotArm': ['Grasp', 'Release', 'Move', 'Rotate', 'Swivel', 'Extend', 'Retract', 'Position'], 'LinearActuator': ['Extend', 'Retract', 'Stop', 'Position', 'Push', 'Pull'], 'Pump': ['Start', 'Stop', 'Increase', 'Decrease', 'Reverse'], 'Pipette': ['Draw', 'Dispense', 'Mix'], 'Rde': ['Rotate', 'Stop', 'ApplyVoltage'], 'RdeRotator': ['Start', 'Stop', 'SetSpeed'], 'Sonication': ['Sonicate', 'Stop', 'Pulse'], 'Humidifier': ['Humidify', 'Stop', 'Dry'], 'Potentiostat': ['SetPotential', 'RunTest', 'Stop'], 'Cell': ['Culture', 'Incubate', 'Harvest'], 'IrRamp': ['Heat', 'Cool', 'Stabilize'], 'MillingMachine': ['Mill', 'Stop', 'ChangeTool'], 'GasRegulator': ['RegulateFlow', 'StopFlow', 'Purge']}

    # Task --> device_action list
    {'ElectroChemicalRDEModule_SetupElectrode': ['RobotArm_Grasp', 'RobotArm_Move', 'RobotArm_Release', 'Rde_ApplyVoltage'], 'ElectroChemicalRDEModule_Calibrate': ['Potentiostat_SetPotential', 'RdeRotator_SetSpeed'], 'ElectroChemicalRDEModule_LoadSample': ['Pipette_Draw', 'Pipette_Dispense'], 'ElectroChemicalRDEModule_AdjustRotation': ['RdeRotator_Start', 'RdeRotator_SetSpeed', 'RdeRotator_Stop'], 'ElectroChemicalRDEModule_ApplyPotential': ['Potentiostat_SetPotential'], 'ElectroChemicalRDEModule_RecordCurrent': ['Potentiostat_RunTest'], 'ElectroChemicalRDEModule_PerformCV': ['Potentiostat_RunTest'], 'ElectroChemicalRDEModule_PerformLPR': ['Potentiostat_RunTest'], 'ElectroChemicalRDEModule_PerformEIS': ['Potentiostat_RunTest'], 'ElectroChemicalRDEModule_ChangeSolution': ['Pump_Start', 'Pump_Stop'], 'ElectroChemicalRDEModule_CleanElectrode': ['Sonication_Sonicate', 'Sonication_Stop'], 'ElectroChemicalRDEModule_AnalyzeData': [], 'ElectroChemicalRDEModule_PerformanceTest': ['Potentiostat_RunTest']}

    # function
        
    1. ElectroChemicalRDEModule_SetupElectrode(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    2. ElectroChemicalRDEModule_Calibrate(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    3. ElectroChemicalRDEModule_LoadSample(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    4. ElectroChemicalRDEModule_AdjustRotation(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    5. ElectroChemicalRDEModule_ApplyPotential(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    6. ElectroChemicalRDEModule_RecordCurrent(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    7. ElectroChemicalRDEModule_PerformCV(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    8. ElectroChemicalRDEModule_PerformLPR(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    9. ElectroChemicalRDEModule_PerformEIS(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    10. ElectroChemicalRDEModule_ChangeSolution(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    11. ElectroChemicalRDEModule_CleanElectrode(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    12. ElectroChemicalRDEModule_AnalyzeData(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')
    13. ElectroChemicalRDEModule_PerformanceTest(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')

    """
    def __init__(self,module_name="ElectroChemicalRDEModule", ResourceManager_obj=object):
        ActionExecutor.__init__(self,)
        self.__ElectroChemicalRDEModule_name= module_name
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
        
    def ElectroChemicalRDEModule_SetupElectrode(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"ElectroChemicalRDEModule_SetupElectrode","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Start "+current_func_name+" Queue")
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
            TaskLogger_obj.current_module_name=self.__ElectroChemicalRDEModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = ElectroChemicalRDEModule_SetupElectrode_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['RobotArm_Grasp', 'RobotArm_Move', 'RobotArm_Release', 'Rde_ApplyVoltage']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "ElectroChemicalRDEModule_SetupElectrode",
    "Data": {
        "ElectrodeType": {
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
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"RobotArm","Grasp","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"RobotArm","Move","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"RobotArm","Release","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"Rde","ApplyVoltage","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)
        
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def ElectroChemicalRDEModule_Calibrate(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"ElectroChemicalRDEModule_Calibrate","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Start "+current_func_name+" Queue")
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
            TaskLogger_obj.current_module_name=self.__ElectroChemicalRDEModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = ElectroChemicalRDEModule_Calibrate_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['Potentiostat_SetPotential', 'RdeRotator_SetSpeed']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "ElectroChemicalRDEModule_Calibrate",
    "Data": {
        "CalibrationStandard": {
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
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"Potentiostat","SetPotential","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"RdeRotator","SetSpeed","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)
        
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def ElectroChemicalRDEModule_LoadSample(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"ElectroChemicalRDEModule_LoadSample","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Start "+current_func_name+" Queue")
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
            TaskLogger_obj.current_module_name=self.__ElectroChemicalRDEModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = ElectroChemicalRDEModule_LoadSample_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['Pipette_Draw', 'Pipette_Dispense']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "ElectroChemicalRDEModule_LoadSample",
    "Data": {
        "SampleVolume": {
            "Value": 0,
            "Dimension": "μL"
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
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"Pipette","Draw","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"Pipette","Dispense","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)
        
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def ElectroChemicalRDEModule_AdjustRotation(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"ElectroChemicalRDEModule_AdjustRotation","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Start "+current_func_name+" Queue")
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
            TaskLogger_obj.current_module_name=self.__ElectroChemicalRDEModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = ElectroChemicalRDEModule_AdjustRotation_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['RdeRotator_Start', 'RdeRotator_SetSpeed', 'RdeRotator_Stop']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "ElectroChemicalRDEModule_AdjustRotation",
    "Data": {
        "RotationSpeed": {
            "Value": 0,
            "Dimension": "rpm"
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
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"RdeRotator","Start","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"RdeRotator","SetSpeed","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"RdeRotator","Stop","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)
        
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def ElectroChemicalRDEModule_ApplyPotential(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"ElectroChemicalRDEModule_ApplyPotential","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Start "+current_func_name+" Queue")
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
            TaskLogger_obj.current_module_name=self.__ElectroChemicalRDEModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = ElectroChemicalRDEModule_ApplyPotential_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['Potentiostat_SetPotential']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "ElectroChemicalRDEModule_ApplyPotential",
    "Data": {
        "Potential": {
            "Value": 0,
            "Dimension": "V"
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
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"Potentiostat","SetPotential","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)
        
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def ElectroChemicalRDEModule_RecordCurrent(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"ElectroChemicalRDEModule_RecordCurrent","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Start "+current_func_name+" Queue")
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
            TaskLogger_obj.current_module_name=self.__ElectroChemicalRDEModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = ElectroChemicalRDEModule_RecordCurrent_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['Potentiostat_RunTest']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "ElectroChemicalRDEModule_RecordCurrent",
    "Data": {
        "Duration": {
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
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"Potentiostat","RunTest","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            result, each_calculate_res_dict=calculateData(current_func_name, data_dict) 
            TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "{} result : {}".format(task_idx, result))
            task_dict["Data"]=each_calculate_res_dict
            result_list.append(task_dict)

            self.ResourceManager_obj.updateStatus(current_func_name, False)
        
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Finish "+current_func_name+" Queue")

        return result_list
            
    def ElectroChemicalRDEModule_PerformCV(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"ElectroChemicalRDEModule_PerformCV","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Start "+current_func_name+" Queue")
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
            TaskLogger_obj.current_module_name=self.__ElectroChemicalRDEModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = ElectroChemicalRDEModule_PerformCV_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['Potentiostat_RunTest']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "ElectroChemicalRDEModule_PerformCV",
    "Data": {
        "ScanRate": {
            "Value": 0,
            "Dimension": "V/s"
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
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"Potentiostat","RunTest","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            result, each_calculate_res_dict=calculateData(current_func_name, data_dict) 
            TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "{} result : {}".format(task_idx, result))
            task_dict["Data"]=each_calculate_res_dict
            result_list.append(task_dict)

            self.ResourceManager_obj.updateStatus(current_func_name, False)
        
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Finish "+current_func_name+" Queue")

        return result_list
            
    def ElectroChemicalRDEModule_PerformLPR(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"ElectroChemicalRDEModule_PerformLPR","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Start "+current_func_name+" Queue")
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
            TaskLogger_obj.current_module_name=self.__ElectroChemicalRDEModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = ElectroChemicalRDEModule_PerformLPR_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['Potentiostat_RunTest']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "ElectroChemicalRDEModule_PerformLPR",
    "Data": {
        "ScanRate": {
            "Value": 0,
            "Dimension": "V/s"
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
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"Potentiostat","RunTest","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            result, each_calculate_res_dict=calculateData(current_func_name, data_dict) 
            TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "{} result : {}".format(task_idx, result))
            task_dict["Data"]=each_calculate_res_dict
            result_list.append(task_dict)

            self.ResourceManager_obj.updateStatus(current_func_name, False)
        
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Finish "+current_func_name+" Queue")

        return result_list
            
    def ElectroChemicalRDEModule_PerformEIS(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"ElectroChemicalRDEModule_PerformEIS","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Start "+current_func_name+" Queue")
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
            TaskLogger_obj.current_module_name=self.__ElectroChemicalRDEModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = ElectroChemicalRDEModule_PerformEIS_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['Potentiostat_RunTest']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "ElectroChemicalRDEModule_PerformEIS",
    "Data": {
        "FrequencyRange": {
            "Value": 0,
            "Dimension": "Hz"
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
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"Potentiostat","RunTest","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            result, each_calculate_res_dict=calculateData(current_func_name, data_dict) 
            TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "{} result : {}".format(task_idx, result))
            task_dict["Data"]=each_calculate_res_dict
            result_list.append(task_dict)

            self.ResourceManager_obj.updateStatus(current_func_name, False)
        
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Finish "+current_func_name+" Queue")

        return result_list
            
    def ElectroChemicalRDEModule_ChangeSolution(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"ElectroChemicalRDEModule_ChangeSolution","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Start "+current_func_name+" Queue")
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
            TaskLogger_obj.current_module_name=self.__ElectroChemicalRDEModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = ElectroChemicalRDEModule_ChangeSolution_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['Pump_Start', 'Pump_Stop']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "ElectroChemicalRDEModule_ChangeSolution",
    "Data": {
        "NewSolution": {
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
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"Pump","Start","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"Pump","Stop","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)
        
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def ElectroChemicalRDEModule_CleanElectrode(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"ElectroChemicalRDEModule_CleanElectrode","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Start "+current_func_name+" Queue")
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
            TaskLogger_obj.current_module_name=self.__ElectroChemicalRDEModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = ElectroChemicalRDEModule_CleanElectrode_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['Sonication_Sonicate', 'Sonication_Stop']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "ElectroChemicalRDEModule_CleanElectrode",
    "Data": {
        "CleaningMethod": {
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
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"Sonication","Sonicate","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"Sonication","Stop","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)
        
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Finish "+current_func_name+" Queue")

        return res_msg
            
    def ElectroChemicalRDEModule_AnalyzeData(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"ElectroChemicalRDEModule_AnalyzeData","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Start "+current_func_name+" Queue")
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
            TaskLogger_obj.current_module_name=self.__ElectroChemicalRDEModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = ElectroChemicalRDEModule_AnalyzeData_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=[]
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "ElectroChemicalRDEModule_AnalyzeData",
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
        #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            result, each_calculate_res_dict=calculateData(current_func_name, data_dict) 
            TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "{} result : {}".format(task_idx, result))
            task_dict["Data"]=each_calculate_res_dict
            result_list.append(task_dict)

            self.ResourceManager_obj.updateStatus(current_func_name, False)
        
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Finish "+current_func_name+" Queue")

        return result_list
            
    def ElectroChemicalRDEModule_PerformanceTest(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"ElectroChemicalRDEModule_PerformanceTest","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Start "+current_func_name+" Queue")
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
            TaskLogger_obj.current_module_name=self.__ElectroChemicalRDEModule_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = ElectroChemicalRDEModule_PerformanceTest_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)=['Potentiostat_RunTest']
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={
    "Task": "ElectroChemicalRDEModule_PerformanceTest",
    "Data": {
        "TestType": {
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
            data_dict=self.executeAction(self.__ElectroChemicalRDEModule_name,jobID,"Potentiostat","RunTest","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            result, each_calculate_res_dict=calculateData(current_func_name, data_dict) 
            TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "{} result : {}".format(task_idx, result))
            task_dict["Data"]=each_calculate_res_dict
            result_list.append(task_dict)

            self.ResourceManager_obj.updateStatus(current_func_name, False)
        
        TaskLogger_obj.debug(self.__ElectroChemicalRDEModule_name, "Finish "+current_func_name+" Queue")

        return result_list
            