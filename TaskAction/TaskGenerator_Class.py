#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [TaskGenerator] TaskGenerator file
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# @version  1_2   
# TEST 2021-11-21
# TEST 2022-04-11

from queue import Queue
import os, sys
import json
import copy
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from collections import OrderedDict
from TaskAction.ActionExecutor import ActionExecutor

class Template:
    def __init__(self,):
        """
        Data format
        """
        self.all_data_template={
            "metadata":{},
            "algorithm":{},
            "process":{},
            "result":{}
        }
        
        """
        Process (High part: Process)
        """
        self.process_template= {
            "Synthesis":[], 
            "Preprocess":[], 
            "Characterization":[],
            "Evaluation":[],
        }
        
        """
        Process (Middle part: Module)
        """
        self.BatchSynthesis_template={
            "Module":"BatchSynthesis",
            "Data":[]  
        }
        self.FlowSynthesis_template={
            "Module":"FlowSynthesis",
            "Data":[]
        }
        
        self.Washing_template={
            "Module":"Washing",
            "Data":[]
        }
        self.Ink_template={
            "Module":"Ink",
            "Data":[]
        }
        
        self.RDE_template={
            "Module":"RDE",
            "Data":[]
        }
        self.Electrode_template={
            "Module":"Electrode",
            "Data":[]
        }

        self.UV_template={
            "Module":"UV",
            "Data":[]
        }
        
        """
        Process (bottom part: Task)
        """
        # Robot
        self.MoveContainer_template={
            "Task":"MoveContainer",
            "Data":{
                    "From":"",
                    "To":"",
                    "Container":"",
                    "Device":{}
                }
        }

        # Batch
        self.PrepareContainer_template={
            "Task":"PrepareContainer",
            "Data":{
                    "From":"",
                    "To":"",
                    "Container":"",
                    "Device":{}
                }
        }
        self.PrepareSolution_template={
            "Task":"PrepareSolution",
            "Data":{
                # "To":"",
                "Solution":"",
                "Volume":{
                    "Value":0,"Dimension":"μL"
                    },
                "Concentration":{
                    "Value":0,"Dimension":"mM"
                    },
                "Device":{}
            }
        }
        self.AddSolution_template={
            "Task":"AddSolution",
            "Data":{
                # "To":"",
                "Solution":"",
                "Volume":{
                    "Value":0,"Dimension":"μL"
                    },
                "Concentration":{
                    "Value":0,"Dimension":"mM"
                    },
                "Injectionrate":{
                    "Value":0,"Dimension":"μL/s"
                    },
                "Device":{}
            } 
        }
        self.Stir_template={
            "Task": "Stir",
            "Data": {
                # "To": "",
                "StirRate": {
                    "Value": 0,
                    "Dimension": "rpm"
                },
                "Device":{}
            }
        }
        self.Heat_template={
            "Task": "Heat",
            "Data": {
                # "To": "",
                "Temperature": {
                    "Value": 0,
                    "Dimension": "ºC"
                },
                "Device":{}
            }
        }
        self.Mix_template={
            "Task": "Mix",
            "Data": {
                # "To": "",
                "Time": {
                    "Value": 0,
                    "Dimension": "sec"
                },
                "Device":{}
            }
        }
        self.React_template={
            "Task": "React",
            "Data": {
                # "To": "",
                "Time": {
                    "Value": 0,
                    "Dimension": "sec"
                },
                "Device":{}
            }
        }
        
        # Preprocess (add later)
        self.Sonication_template={
            "Task": "Sonication",
            "Data": {
                # "To": "",
                "Power":{
                    "Value": 0,
                    "Dimension": "kHz"
                },
                "Time": {
                    "Value": 0,
                    "Dimension": "sec"
                },
                "Device":{}
            }
        }
        self.Centrifugation_template={
            "Task": "Centrifugation",
            "Data": {
                # "To": "",
                "Power":{
                    "Value": 0,
                    "Dimension": "rpm"
                },
                "Time": {
                    "Value": 0,
                    "Dimension": "sec"
                },
                "Device":{}
            }
        }
        
        # UV-VIS
        self.GetAbs_template={
            "Task":"GetAbs",
            "Data":{
                "Device":{},
                "Hyperparameter":{
                    "WavelengthMin":{
                        "Description":"WavelengthMin=300 (int): slice wavlength section depending on wavelength_min and wavelength_max",
                        "Value": 300,
                        "Dimension": "nm"
                    },
                    "WavelengthMax":{
                        "Description":"WavelengthMax=849 (int): slice wavlength section depending on wavelength_min and wavelength_max",
                        "Value": 849,
                        "Dimension": "nm"
                    },
                    "BoxCarSize":{
                        "Description":"BoxCarSize=10 (int): smooth strength",
                        "Value": 10,
                        "Dimension": "None"
                    },
                    "Prominence":{
                        "Description":"Prominence=0.01 (float): minimum peak Intensity for detection",
                        "Value": 0.01,
                        "Dimension":"None"
                    },
                    "PeakWidth":{
                        "Description":"PeakWidth=20 (int): minumum peak width for detection",
                        "Value": 20,
                        "Dimension": "nm"
                    }
                }
            },
        }


class TaskGenerator(Template,ActionExecutor):
    """
    TaskGenerator class get task sequence, allocate each task's value in json file (recipe)

    class Template --> has template of recipe
    class ActionExecutor --> to request hardware information (pump) to use flexible system when we change our solution location or type, kinds

    # Variables
    ------------
    :param TaskLogger_obj (TaskLogger_obj): set logging object
    :param metadata_dict (dict): 
        ex) "metadata" : 
        "metadata" : 
            {
                "subject":"Take scneario",
                "group":"KIST_CSRC",
                "userName":"USER_HJ",
                "researcherId":"yoohj9475@kist.re.kr",
                "researcherPwd":"1234",
                "element":"Ag",
                "experimentType":"automatic",
                "logLevel":"INFO",
                "modeType":"real",
                "todayIterNum":1
            },
    """
    def __init__(self, TaskLogger_obj:object, ResourceManager_obj:object):
        """
        sequence_list=[["MoveContainer","AddSolution","Stir","Heat","Mix","AddSolution","Mix","MoveContainer"],....]
        soliution_list=[{'AgNO3': 2400.0, 'NaBH4': 2400.0, 'H2O2': 1200.0, 'H2O': 2400.0, "PVP55":2000.0, "Citrate":2000.0}, ...]
        """
        Template.__init__(self,)
        ActionExecutor.__init__(self,)
        self.TaskLogger_obj=TaskLogger_obj
        self.platform_name="TaskGenerator"

        self.ResourceManager_obj=ResourceManager_obj
        self.task_hardware_info_dict = self.ResourceManager_obj.task_hardware_info_dict

    def __allocateTaskSequence(self, task_type:str, integrated_parameter_dict:dict):
        """
        allocate some value in recipe template

        :param task_type (str or dict): AddSolution or Stir...Electrochemical... etc...
        :param integrated_parameter_dict = dict(parameter_dict, **fixed_params_dict)
        :return: template (dict), 
        """
        if "AddSolution" in task_type:
            empty_template=copy.deepcopy(self.AddSolution_template)
            # AddSolution의 solution type을 delete
            empty_template["Task"]="AddSolution"
            ####################################################
            # AddSolution include pump and pipette
            ####################################################
            # print("####################################################")
            # print(self.task_hardware_info_dict)
            # print("####################################################")
            pump_hardware_info=self.task_hardware_info_dict["BatchSynthesis"]["Pump"]
            pipette_hardware_info=self.task_hardware_info_dict["BatchSynthesis"]["Pipette"]
            solution_hardware_info = dict(pump_hardware_info, **pipette_hardware_info)
            
            # print("****************************************************")
            # print("solution_hardware_info", solution_hardware_info)
            # print("****************************************************")

            ####################################################
            # self.solution_name_list == pump solution name in BatchSynthesisPlatform
            # self.solution_Device_list == pump Device in BatchSynthesisPlatform
            ####################################################
            solution_name_list_in_platform=list(solution_hardware_info.keys()) # ["AgNO3", "H2O", "PVP55"... ]

            ####################################################
            # solution_name_in_job == wanted solution name in job script
            # solution_index_list == pump solution index in BatchSynthesisPlatform
            # filter_solution_name_list == wanted solution name & match pump Device in BatchSynthesisPlatform
            #   (If this solution can use in platform?)
            ####################################################
            solution_name_in_job=task_type[12:] # AddSolution={solution_name_ValueName} separate --> solution_name in jobscript 
            solution_index_list = [i for i, sol_name in enumerate(solution_name_list_in_platform) if sol_name==solution_name_in_job] # solution name is equal
            filter_solution_name_list=[solution_name_list_in_platform[idx] for idx in solution_index_list]
            
            if solution_name_in_job in filter_solution_name_list:
                empty_template["Data"]["Solution"]=solution_name_in_job # add solution name
                empty_template["Data"]["Volume"]["Value"]=integrated_parameter_dict["AddSolution="+solution_name_in_job+"_Volume"] # Volume 추가
                empty_template["Data"]["Concentration"]["Value"]=integrated_parameter_dict["AddSolution="+solution_name_in_job+"_Concentration"] # Concentration 추가
                empty_template["Data"]["Injectionrate"]["Value"]=integrated_parameter_dict["AddSolution="+solution_name_in_job+"_Injectionrate"] # Injection rate
                empty_template["Data"]["Device"]=solution_hardware_info[solution_name_in_job]
            else:
                KeyError("[{}] {} vs filter_solution_name_list : {} is different".format(self.platform_name, solution_name_in_job, filter_solution_name_list))
            template=empty_template
            
            return template

        elif "Stir" in task_type:
            empty_template = copy.deepcopy(self.Stir_template)
            empty_template["Data"]["StirRate"]["Value"]=integrated_parameter_dict["Stir=StirRate"] # upload in job script file
            hardware_info=self.task_hardware_info_dict["BatchSynthesis"]["Stirrer"] # upload in hardware Device
            empty_template["Data"]["Device"]=hardware_info
            
            template=empty_template
            return template

        elif "Heat" in task_type:
            empty_template = copy.deepcopy(self.Heat_template)
            empty_template["Data"]["Temperature"]["Value"]=integrated_parameter_dict["Heat=Temperature"] # upload in job script file
            hardware_info=self.task_hardware_info_dict["BatchSynthesis"]["Stirrer"] # upload in hardware Device
            empty_template["Data"]["Device"]=hardware_info
            
            template=empty_template
            return template

        elif "Mix" in task_type:
            empty_template = copy.deepcopy(self.Mix_template)
            empty_template["Data"]["Time"]["Value"]=integrated_parameter_dict["Mix=Time"] # upload in job script file
            hardware_info=self.task_hardware_info_dict["BatchSynthesis"]["Stirrer"] # upload in hardware Device
            empty_template["Data"]["Device"]=hardware_info
            
            template=empty_template
            return template

        elif "React" in task_type:
            empty_template = copy.deepcopy(self.React_template)
            empty_template["Data"]["Time"]["Value"]=integrated_parameter_dict["React=Time"] # upload in job script file
            hardware_info=self.task_hardware_info_dict["BatchSynthesis"]["Stirrer"] # upload in hardware Device
            empty_template["Data"]["Device"]=hardware_info
            
            template=empty_template
            return template

        # elif type(task_type)==dict: # The characterization varies depending on what value it is intended to reflect.
        elif "GetAbs" in task_type:
            empty_template=copy.deepcopy(self.GetAbs_template)
            
            uv_hyperparameter_include_parameter_name_list=[]
            parameter_name_list=list(integrated_parameter_dict.keys())
            for parameter_name in parameter_name_list:
                if "Hyperparameter" in parameter_name and "GetAbs" in parameter_name:
                    uv_hyperparameter_include_parameter_name_list.append(parameter_name)
                    _, hyperparameter_name=parameter_name.split("_")
                    empty_template["Data"]["Hyperparameter"][hyperparameter_name]["Value"]=integrated_parameter_dict[parameter_name] # add Volume
            hardware_info=self.task_hardware_info_dict["UV"]
            empty_template["Data"]["Device"]=hardware_info
            
            template=empty_template
            return template
            
        elif "RDE" in task_type: # add later
            template = copy.deepcopy(self.RDE_template)
            return template
        
        elif "MoveContainer" in task_type:
            _, task_content = task_type.split("=")
            empty_template=copy.deepcopy(self.MoveContainer_template) # "Since batch always places the vial first, storage_empty_to_stirrer remains fixed initially."
            if task_content == "storage_empty_to_stirrer" or task_content == "stirrer_to_holder":
                move_from, move_to = task_content.split("_to_")
                empty_template["Data"]["From"]=move_from
                empty_template["Data"]["To"]=move_to
                
                empty_template["Data"]["Container"]="Vial"
                
                hardware_info=self.task_hardware_info_dict["BatchSynthesis"]["DS_B"]
                empty_template["Data"]["Device"]=hardware_info
            
            template=empty_template
            return template

        elif "PrepareContainer" in task_type:
            _, task_content = task_type.split("=")
            empty_template=copy.deepcopy(self.PrepareContainer_template) # "Since batch always places the vial first, storage_empty_to_stirrer remains fixed initially."
            move_from, move_to = task_content.split("_to_")
            empty_template["Data"]["From"]=move_from
            empty_template["Data"]["To"]=move_to
            
            empty_template["Data"]["Container"]="Vial"
            
            hardware_info=self.task_hardware_info_dict["BatchSynthesis"]["DS_B"]
            empty_template["Data"]["Device"]=hardware_info
            
            template=empty_template
            return template

        else:
            raise IndexError("There is no task type in here : {}".format(task_type))

    def generateRecipe(self, recipe_dict:dict, input_next_point={}):
        """
        allocate synthesis sequence process in json file (recipe) depending on each task_sequence_list
        
        :param recipe_dict (dict) : recipe information in config file
        ex)
        process_dict = {
            "Synthesis":{
                "BatchSynthesis":
                {
                    "fixedParams":
                    {
                        "BatchSynthesis=Sequence":["AddSolution_Citrate","AddSolution_NaBH4","Stir","Heat","Mix", "AddSolution_AgNO3", "React"],

                        "AddSolution=Citrate_Concentration" : 20,
                        "AddSolution=Citrate_Volume" : 1200,
                        "AddSolution=Citrate_Injectionrate" : 200,
                        "AddSolution=NaBH4_Concentration" : 10,
                        "AddSolution=NaBH4_Volume" : 3000,
                        "AddSolution=NaBH4_Injectionrate" : 200,

                        "Stir=StirRate":1000,
                        "Heat=Temperature":25,
                        "Mix=Time":300,
                        "React=Time":1200
                    }
                },
                "FlowSynthesis":{}
            },
            "Preprocess":{
                "Washing":{},
                "Ink":{}
            },
            "Characterization":{
                "UV":
                {
                    "fixedParams":
                    {
                        "UV=Sequence":["GetAbs"],
                        "UV=Hyperparameter_WavelengthMin":300, 
                        "UV=Hyperparameter_WavelengthMax":849, 
                        "UV=Hyperparameter_BoxCarSize":10, 
                        "UV=Hyperparameter_Prominence":0.01, 
                        "UV=Hyperparameter_PeakWidth":20
                    }
                }
            },
            "Evaluation":{
                "RDE":{},
                "Electrode":{}
            }
        }
        :param input_next_point (dict) :result of algorithm value dict
        
        :return temp_process_template (dict): total process_template
        """
        temp_process_template= copy.deepcopy(self.process_template)
        """
        self.process_template= {
            "Synthesis":[], 
            "Preprocess":[], 
            "Characterization":[],
            "Evaluation":[]
        }
        """
        final_big_process_name=""
        final_module_name=""
        for big_process_name, big_process_dict in recipe_dict.items(): # big_process_name = "Synthesis", "Preprocess", "Characterization", "Evaluation":
            count=0
            for module_name, module_dict in big_process_dict.items(): # module_name = "BatchSynthesis" or "FlowSynthesis"
                if len(module_dict)!=0:
                    temp_template=copy.deepcopy(getattr(self, module_name+"_template"))
                    integrated_parameter_dict = dict(input_next_point, **module_dict["fixedParams"])
                    integrated_parameter_dict=copy.deepcopy(integrated_parameter_dict)
                    each_task_list=[]
                    ##########################################
                    # if need to additional task in module
                    ##########################################
                    if module_name=="BatchSynthesis":
                        integrated_parameter_dict[module_name+"=Sequence"].insert(0, "PrepareContainer=storage_empty_to_stirrer") # "Batch always places vial first, so storage_empty_to_stirrer remains fixed initially."
                        # integrated_parameter_dict[module_name+"=Sequence"].append("MoveContainer=stirrer_to_holder") # "Batch always retrieves the vial after the reaction is complete, so stirrer_to_holder remains fixed at the end."
                    elif module_name=="FlowSynthesis":
                        # later
                        pass
                    elif module_name=="Washing":
                        # later
                        pass
                    elif module_name=="Ink":
                        # later
                        pass
                    elif module_name=="UV":
                        pass
                    ##########################################
                    # allocate task depending on sequences
                    ##########################################
                    try:
                        for task_type in integrated_parameter_dict[module_name+"=Sequence"]: # Allocate task_type according to the Sequence within the module.
                            temp_each_task_template=self.__allocateTaskSequence(task_type, integrated_parameter_dict)
                            each_task_list.append(temp_each_task_template)
                    except KeyError as e:
                        print(e)
                        raise KeyError("integrated_parameter_dict has no module_sequences")
                    ##########################################
                    # attach task_list in template
                    ##########################################
                    temp_template["Data"]=each_task_list
                    temp_process_template[big_process_name].append(temp_template)
                    final_module_name=module_name # "Add a template to save to storage after every process completion."
                    final_big_process_name=big_process_name
                else: # process is empty
                    count+=1
            # if empty_process -> delete
            if count==len(list(big_process_dict.keys())):
                del temp_process_template[big_process_name]
        ###############################################################
        # "Add a template to save to storage after every platform and process completion."
        ###############################################################
        temp_MoveContainer_template=copy.deepcopy(self.MoveContainer_template)
        temp_MoveContainer_template["Data"]["Container"]="Vial"
        temp_MoveContainer_template["Data"]["From"]="vialholder_{}".format(final_module_name)
        temp_MoveContainer_template["Data"]["To"]="storage_filled"
        hardware_info=self.task_hardware_info_dict["BatchSynthesis"]["DS_B"]
        temp_MoveContainer_template["Data"]["Device"]=hardware_info
        temp_process_template[final_big_process_name][-1]["Data"].append(temp_MoveContainer_template)

        return temp_process_template


if __name__ == "__main__":
    from Log.Logging_Class import TaskLogger
    input_next_point={
        "AddSolution=AgNO3_Concentration" : 0.375,
        "AddSolution=AgNO3_Volume" : 1200,
        "AddSolution=AgNO3_Injectionrate" : 200
    }
    metadata_dict={
        "subject":"Take_scneario",
        "group":"KIST_CSRC",
        "logLevel":"INFO",
        "modeType":"real",
        "todayIterNum":1,
        "userName":"HJ",
        "jobID":0,
        "jobFileName":"USER/HJ/job_script/20230516_autonomous_test.json",
        "batchSize":8
    }
    recipe_dict={
        "Synthesis":{
            "BatchSynthesis":
            {
                "fixedParams":
                {
                    "BatchSynthesis=Sequence":["AddSolution_Citrate","AddSolution_H2O2", "AddSolution_NaBH4","Stir","Heat","Mix", "AddSolution_AgNO3", "React"],
                    
                    "AddSolution=H2O2_Concentration" : 0.375,
                    "AddSolution=H2O2_Volume" : 1200,
                    "AddSolution=H2O2_Injectionrate" : 200,
                    "AddSolution=Citrate_Concentration" : 0.02,
                    "AddSolution=Citrate_Volume" : 1200,
                    "AddSolution=Citrate_Injectionrate" : 200,
                    "AddSolution=NaBH4_Concentration" : 0.01,
                    "AddSolution=NaBH4_Volume" : 3000,
                    "AddSolution=NaBH4_Injectionrate" : 200,

                    "Stir=StirRate":800,
                    "Heat=Temperature":25,
                    "Wait=Time":1,
                    "React=Time":1
                },
            },
            "FlowSynthesis":{}
        },
        "Preprocess":{
            "Washing":{},
            "Ink":{}
        },
        "Characterization":{
            "UV":
            {
                "fixedParams":
                {
                    "UV=Sequence":["GetAbs"]
                },
            }
        },
        "Evaluation":{
            "RDE":{},
            "Electrode":{}
        }
    }
    TaskLogger_obj=TaskLogger(metadata_dict)
    TaskGenerator_obj=TaskGenerator(TaskLogger_obj)
    import time
    for i in range(2):
        dict_obj = TaskGenerator_obj.allocateTaskSequence(recipe_dict, input_next_point)
        time.sleep(2)
        TaskGenerator_obj.saveRecipeToJSON(dict_obj=dict_obj, file_name="1234_{}.json".format(i), mode_type="virtual")
