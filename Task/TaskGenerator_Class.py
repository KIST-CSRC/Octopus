#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [TaskGenerator] TaskGenerator file
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# @version  3_2   
# TEST 2021-11-21
# TEST 2022-04-11
# TEST 2024-06-14
import copy
import json


class TaskGenerator:
    """
    TaskGenerator class get task sequence, allocate each task's value in json file (recipe)

    class Template --> has template of recipe
    class TCP_Class --> to request hardware information (pump) to use flexible system when we change our solution location or type, kinds

    # Variables
    ------------
    :param TaskLogger_obj (TaskLogger_obj): set logging object
    :param ResourceManager_obj (object): resource manager object
    """
    def __init__(self, TaskLogger_obj:object, ResourceManager_obj:object):
        self.TaskLogger_obj=TaskLogger_obj
        self.component_name="TaskGenerator"

        self.ResourceManager_obj=ResourceManager_obj
        self.task_device_info_dict = self.ResourceManager_obj.task_device_info_dict
        with open(f"Task/Template_module.json", 'r', encoding='utf-8') as f:
            self.Template_base=json.load(f)

    def _allocateTaskInfo(self, big_process_module_dict:dict, task_templates:dict, task_device_action_dict:dict, input_task_name:str, integrated_parameter_dict:dict):
        """
        allocate some value in recipe template

        :param big_process_module_dict (dict): 
        :param task_templates (dict)
        :param task_device_action_dict (dict)
        :param input_task_name (str): BatchSynthesis_AddSolution=AgNO3 or BatchSynthesis_Stir...ElectroAnalysis_Electrochemical... etc...
        :param integrated_parameter_dict (dict) --> dict(parameter_dict, **fixed_params_dict)

        :return: template (dict), 
        """
        ###############################
        # split module name, task name, task content
        ###############################
        module_name=""
        task_name=""
        task_content=""
        if "=" in input_task_name:
            module_task_name, task_content = input_task_name.split("=")
            # input_task_name="BatchSynthesis_AddSolution=AgNO3"
                # module_task_name="BatchSynthesis_AddSolution"
                # task_content="AgNO3"
        else:
            module_task_name=input_task_name
        # module_task_name --> BatchSynthesisModule_AddSolution
        module_name, task_name = module_task_name.split("_")
        # module_name --> BatchSynthesisModule // task_name --> AddSolution
        
        ###############################
        # extract task template
        ###############################
        task_template=task_templates[module_task_name]
        ###############################
        # extract device information 
        ###############################
        # print(task_device_action_dict)
        task_deviceaction_list=list(task_device_action_dict[module_task_name])
        device_info_dict={}
        # print("self.task_device_info_dict[module_name]", self.task_device_info_dict[module_name])
        try:
            for task_deviceaction in task_deviceaction_list:
                device_name, action_type = task_deviceaction.split("_")
                # print("device_name, action_type", device_name, action_type)
                device_info_dict[device_name]=self.task_device_info_dict[module_name][device_name]
        except KeyError as e:
            print(f"module name keys :{list(self.task_device_info_dict.keys())} --> {module_name}")
            print(f"module devices keys :{list(self.task_device_info_dict[module_name].keys())} --> {device_name}")
            print(f"We don't have {module_name} or {device_name}")
            raise KeyError(e)
        # print("device_info_dict", device_info_dict)
        ##############################################
        # allocate task information in task template #
        ##############################################
        # print("task_content", task_content)
        splitted_task=task_content.split("_")
        # print("splitted_task:", splitted_task)
        ##############################################
        # allocate task information in task template-1
        # no hyperparameter, material name
        ##############################################
        if splitted_task==['']:
            for key, value in task_template["Data"].items():
                if key=="Device":
                    task_template["Data"]["Device"]=device_info_dict
                else:
                    if isinstance(value, dict):
                        task_template["Data"][key]["Value"]=integrated_parameter_dict[module_name+"_"+task_name+"="+key]
                    else:
                        raise ValueError(f"Please check parameter dict:{list(integrated_parameter_dict.keys())} --> key of parameter dict:{module_name}_{task_name}={key}")
        ##############################################
        # allocate task information in task template-2
        # has hyperparameter, material name
        ##############################################
        else:
            material = splitted_task[0]
            for key, value in task_template["Data"].items():
                if key=="Device":
                    task_template["Data"]["Device"]=device_info_dict
                elif key=="Material":
                    task_template["Data"][key]["Type"]=material
                else:
                    if isinstance(value, dict): # {"Value":0, "Dimension":"mL"}
                        task_template["Data"][key]["Value"]=integrated_parameter_dict[module_name+"_"+task_name+f"={material}_"+key]
                    else:
                        raise ValueError(f"Please check parameter dict:{list(integrated_parameter_dict.keys())} --> key of parameter dict:{module_name}_{task_name}={material}_{key}")
            # if mid_key=="Hyperparameter":
            #     for key, value in task_template["Data"].items():
            #         if key=="Device":
            #             task_template["Data"]["Device"]=device_info_dict
            #         else:
            #             if isinstance(value, str):
            #                 task_template["Data"][mid_key]=integrated_parameter_dict[module_name+"_"+task_name+"="+key]
            #             elif isinstance(value, dict): # mid_key="Hyperparameter", condition_name="WavelengthMin"...etc
            #                 for bottom_key in task_template["Data"][mid_key].keys():
            #                     task_template["Data"][mid_key][bottom_key]=integrated_parameter_dict[module_name+"_"+task_name+f"={mid_key}_"+bottom_key]
            #             else:
            #                 raise ValueError(f"Please check parameter dict:{list(integrated_parameter_dict.keys())} --> key of parameter dict:{module_name}_{task_name}={mid_key}_{bottom_key}")
            # else:
                # for key, value in task_template["Data"].items():
                #     if key=="Device":
                #         task_template["Data"]["Device"]=device_info_dict
                #     else:
                #         if isinstance(value, str): # material
                #             task_template["Data"][key]=mid_key
                #         elif isinstance(value, dict): # {"Value":0, "Dimension":"mL"}
                #             task_template["Data"][key]["Value"]=integrated_parameter_dict[module_name+"_"+task_name+f"={mid_key}_"+condition_name]
                #         else:
                #             raise ValueError(f"Please check parameter dict:{list(integrated_parameter_dict.keys())} --> key of parameter dict:{module_name}_{task_name}={mid_key}_{condition_name}")
        return task_template

    def generateRecipe(self, recipe_dict:dict, input_next_point:dict={}):
        """
        allocate synthesis sequence process in json file (recipe) depending on each task_sequence_list
        
        :param recipe_dict (dict) : recipe information in config file
        ex)
        process_dict = {
            "Synthesis":{
                "BatchSynthesis":
                {
                    "Sequence":["BatchSynthesisModule_AddSolution=Citrate","BatchSynthesisModule_AddSolution=NaBH4","BatchSynthesisModule_Stir","BatchSynthesisModule_Heat","BatchSynthesisModule_Mix", "BatchSynthesisModule_AddSolution=AgNO3", "BatchSynthesisModule_React"],
                    "fixedParams":
                    {
                        "BatchSynthesisModule_AddSolution=Citrate_Concentration" : 20,
                        "BatchSynthesisModule_AddSolution=Citrate_Volume" : 1200,
                        "BatchSynthesisModule_AddSolution=Citrate_Injectionrate" : 200,
                        "BatchSynthesisModule_AddSolution=NaBH4_Concentration" : 10,
                        "BatchSynthesisModule_AddSolution=NaBH4_Volume" : 3000,
                        "BatchSynthesisModule_AddSolution=NaBH4_Injectionrate" : 200,

                        "BatchSynthesisModule_Stir=StirRate":1000,
                        "BatchSynthesisModule_Heat=Temperature":25,
                        "BatchSynthesisModule_Mix=Time":300,
                        "BatchSynthesisModule_React=Time":1200
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
                    "Sequence":["UVVisModule_GetAbs"],
                    "fixedParams":
                    {
                        "UVVisModule_GetAbs=Hyperparameter_WavelengthMin":300, 
                        "UVVisModule_GetAbs=Hyperparameter_WavelengthMax":849, 
                        "UVVisModule_GetAbs=Hyperparameter_BoxCarSize":10, 
                        "UVVisModule_GetAbs=Hyperparameter_Prominence":0.01, 
                        "UVVisModule_GetAbs=Hyperparameter_PeakWidth":20
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
        with open(f"Task/Template_module.json", 'r', encoding='utf-8') as f:
            temp_process_template=json.load(f)["process"]
        """
        temp_process_template= {
            "Synthesis":[], 
            "Preprocess":[], 
            "Characterization":[],
            "Evaluation":[]
        }
        """
        module_seq_list=[]
        big_process_module_dict={
            "Synthesis":[], 
            "Preprocess":[], 
            "Characterization":[],
            "Evaluation":[]
        }
        for big_process_name, big_process_dict in recipe_dict.items():
            for module_name, module_dict in big_process_dict.items():
                if len(module_dict)!=0:
                    module_seq_list.append(module_name)
                    big_process_module_dict[big_process_name].append(module_name)
        for big_process_name, big_process_dict in recipe_dict.items(): # big_process_name = "Synthesis", "Preprocess", "Characterization", "Evaluation":
            count=0
            for module_name, module_dict in big_process_dict.items(): # module_name = "BatchSynthesis" or "FlowSynthesis"
                if len(module_dict)!=0:
                    integrated_parameter_dict = dict(input_next_point, **module_dict["fixedParams"])
                    integrated_parameter_dict=copy.deepcopy(integrated_parameter_dict)
                    ##########################
                    # upload module template #
                    ##########################
                    with open(f"Task/Template_module.json", 'r', encoding='utf-8') as f:
                        module_template=json.load(f)[module_name]
                    ###############################
                    # extract task template
                    ###############################
                    with open(f"Task/Template/{module_name}.json", 'r', encoding='utf-8') as f:
                        task_templates=json.load(f)
                    ###############################
                    # extract device information 
                    ###############################
                    with open(f"Task/ActionSequence/{module_name}.json", 'r', encoding='utf-8') as f:
                        task_device_action_dict=json.load(f)
                    ########################################
                    # allocate task depending on sequences #
                    ########################################
                    module_task_list=[]
                    try:
                        for task_name in module_dict["Sequence"]: # Allocate task_name according to the Sequence within the module.
                            temp_each_task_template=self._allocateTaskInfo(big_process_module_dict, task_templates, task_device_action_dict, task_name, integrated_parameter_dict)
                            module_task_list.append(temp_each_task_template)
                    except KeyError as e:
                        print(e)
                        raise KeyError("integrated_parameter_dict has no module_sequences")
                    ##########################################
                    # attach task_list in template
                    ##########################################
                    module_template["Data"]=module_task_list
                    temp_process_template[big_process_name].append(module_template)
                else: # process is empty
                    count+=1
            # if empty_process -> delete
            if count==len(list(big_process_dict.keys())):
                del temp_process_template[big_process_name]

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