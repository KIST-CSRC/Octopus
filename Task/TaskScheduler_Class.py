#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [TaskScheduler] TaskScheduler file
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
from Action.ActionTranslator_Class import ActionTranslator


class TaskScheduler(ActionTranslator):
    """
    TaskScheduler class read recipe file (json), and allocate & link each task to proper devices
    
    # function
    def _get_data_by_module(self,module_key, module_dict)
    def _task2Device (action_type, task_info_list)
    def _scheduleAllTask(self, total_recipe_template_list:list, jobID:int, TaskLogger_obj:object, mode_type:str)
    def scheduleAlltask (total_recipe_template_list)
    """
    def __init__(self, serverLogger_obj:object, ResourceManager_obj:object, schedule_mode:str):
        ActionTranslator.__init__(self, serverLogger_obj, ResourceManager_obj, schedule_mode)
        self.serverLogger_obj=serverLogger_obj
        self.ResourceManager_obj=ResourceManager_obj
        self.schedule_mode=schedule_mode
        self.module_name="TaskScheduler"

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
        if isinstance(return_value,str): # if action_type don't return some chemical data (AddSolution, Stir...)
            return return_value
        elif isinstance(return_value,list): # if action_type return some chemical data (measurement, calcination, UV...),
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

        TaskLogger_obj.info(self.module_name, "check location: {}".format(self.ResourceManager_obj.task_device_location_dict))
        for module_idx, module_type in enumerate(module_seq_list):
            # module_type : Batch, Flow, Washing, Ink, UV, RDE, Electrode // if not --> pass!
            batch_num = len(total_recipe_template_list) # 배치가 8개면 8개
            # if module_idx+1 != len(module_seq_list):
                # location_dict=getattr(self.ResourceManager_obj, self.schedule_mode)(module_type, module_seq_list[module_idx+1], jobID, total_recipe_template_list)
            location_dict=self.ResourceManager_obj.allocateLocation(module_type, jobID, total_recipe_template_list)
            TaskLogger_obj.info(self.module_name, "{} is started, allocate location: {}".format(module_type, location_dict))
            TaskLogger_obj.info(self.module_name, "check location after allocation: {}".format(self.ResourceManager_obj.task_device_location_dict))
            
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
            TaskLogger_obj.currentExperimentNum=TaskLogger_obj.currentExperimentNum+len(total_recipe_template_list)
            TaskLogger_obj.status="{}/{}:{}".format(TaskLogger_obj.currentExperimentNum, TaskLogger_obj.totalExperimentNum, TaskLogger_obj.current_module_name) # in execution system
            total_result_lists_in_list=self._scheduleAllTask(total_recipe_template_list, jobID, TaskLogger_obj, mode_type)
        
        elif self.schedule_mode=="ClosedPacking":
            count_experiments_num=0
            total_experiments_num=len(total_recipe_template_list) # total numbers of experiments
            copied_total_recipe_template_list=list(copy.deepcopy(total_recipe_template_list)) # popped version
            while True:
                if count_experiments_num==total_experiments_num:
                    break
                # calculate possibile numbers of tasks based on present task_device_location_dict
                throughput_num=self.ResourceManager_obj.notifyNumbersOfTasks(copied_total_recipe_template_list)
                # set current experiment num
                TaskLogger_obj.currentExperimentNum=TaskLogger_obj.currentExperimentNum+throughput_num
                TaskLogger_obj.status="{}/{}:{}".format(TaskLogger_obj.currentExperimentNum, TaskLogger_obj.totalExperimentNum, TaskLogger_obj.current_module_name) # in execution system
                # pop possibile numbers of tasks based on present task_device_location_dict
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
        
        # refresh location information of self.task_device_location_dict (0 or 1 or 2 ... (jobID) --> ?)            
        self.ResourceManager_obj.refreshTotalLocation(jobID)
        TaskLogger_obj.info(self.module_name, "refresh location: {}".format(self.ResourceManager_obj.task_device_location_dict))

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