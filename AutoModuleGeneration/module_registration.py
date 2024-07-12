import openai
import re
import os, time
import ast
import json
import copy
from prettytable import PrettyTable
from pydantic import BaseModel
from typing import Literal
from datetime import datetime
from Action.ActionExecutor_Class import ActionExecutor

class ConfigValidation_ModuleNode(BaseModel):
    author:str
    module_name:str
    module_type: Literal["Synthesis", "Preprocess", "Evaluation", "Characterization"]
    module_description:str
    device_type:list
    task_type:list
    resource:dict    
    HOST:str # please implement your ip
    PORT:int
    task_type:list
    resource:dict
    gpt_on:bool
    gpt_api_key:str

def GPT_generate_task(input_module_name:str, description:str, task_list:list, deviceaction_type_dict:dict, api_key:str, gpt_on=False):

    openai.api_key = api_key

    task_str=""
    for idx, arg in enumerate(task_list):
        task_str+=arg
        if idx != len(task_list)-1:
            task_str+=", "
    
    device_list=list(deviceaction_type_dict.keys())
    device_str=""
    for idx, device in enumerate(device_list):
        device_str+=device.lower()
        if idx != len(task_list)-1:
            device_str+=", "
    
    action_type_list=list(deviceaction_type_dict.values())
    action_type_str=""
    for i, action_types in enumerate(action_type_list):
        for j, action_type in enumerate(action_types):
            action_type_str+=action_type.lower()
            if i != len(task_list)-1 and j!=len(action_types)-1:
                action_type_str+=", "
    
    print("###################")
    print("[GPT (TaskGenerator, ActionTranslator)]: task generation...")
    print("###################")
    
    if gpt_on==True:
        completion = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",  # 사용할 GPT 모델 엔진
            # prompt=question,
            # max_tokens=150,  # 생성할 응답의 최대 토큰 수
            # n=1,  # 생성할 응답 수
            # stop=None,  # 응답 생성 중단 시퀀스
            temperature=0,  # 응답의 창의성 (0.0~1.0)
            messages=[
                {
                    "role": "system",
                    "content": """You are administrator of autonomous laboratory, which control AI and robotics for chemical experiments, 
                    and your role is the task generation for chemical experiments execution with chemical devices.""",
                },
                {
                    "role": "user",
                    "content": f"""I am going to define tasks for a module, considering tasks as verbs representing experimental processes. 
                    For example, the tasks for the BatchSynthesis module include "MoveContainer", "AddSolution", "Stir", "Mix", "React", and "Pipette". 
                    All task name use verb with module name, such as 'BatchSynthesisModule_Stir', 'RDEEvaluationModule_Dispense
                    Now, please suggest tasks for the {input_module_name} as python list, including {task_str}.
                    If a specific task involves loading measurement or analysis or performance data, ensure the task name ends with "test".
                    {description}.
                    """
                },
            ]
            # This {input_module_name} include devices, such as {device_str}.
            # And this device has action types, such as {action_type_str}.
        )
        answer = completion.choices[0].message.content
        print(completion.usage)

        with open(f"AutoModuleGeneration/GPT_answer_registration/{input_module_name}_tasks.txt", 'w') as file:
            file.write(answer)
    else:
        with open(f'AutoModuleGeneration/GPT_answer_registration/{input_module_name}_tasks.txt', 'r', encoding='utf-8') as file:
            answer = file.read()
    return answer

def GPT_match_task_action_sequence(input_module_name:str, task_list:list, device_action_dict:dict, api_key:str, gpt_on=False):
    
    openai.api_key = api_key

    task_str=""
    for idx, arg in enumerate(task_list):
        task_str+=arg
        if idx == len(task_list)-1:
            task_str+=", "
    
    print("###################")
    print("[GPT (ActionTranslator)]: match action sequence for each task...")
    print("###################")
    
    if gpt_on==True:
        
        completion = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",  # 사용할 GPT 모델 엔진
            # prompt=question,
            # max_tokens=150,  # 생성할 응답의 최대 토큰 수
            # n=1,  # 생성할 응답 수
            # stop=None,  # 응답 생성 중단 시퀀스
            temperature=0,  # 응답의 창의성 (0.0~1.0)
            messages=[
                {
                    "role": "system",
                    "content": """You are administrator of autonomous laboratory, which control AI and robotics for chemical experiments, 
                    and your role is to construct action sequence of chemical task, followed by chemical devices and action type of chemical devices.""",
                },
                {
                    "role": "user",
                    "content": "I have a task list of {}, {}.\n".format(input_module_name, task_list)+
                    """
                    The types of chemical tasks we need to perform are listed below:{input_task_list}
                    The devices we have and the actions each device can perform are listed below in the form of a dictionary:{input_device_action_dict}
                    We called this dictionary, device_action_dictionary.
                    The types of devices we have are the keys of the device_action_dictionary.

                    Please identify the types of devices needed for each task to perform the chemical tasks.
                    The more detailed the device actions for each task and the accurate sequence of device actions, the higher the accuracy of the task.
                    Then, create a device_action_dictionary with the task name as the key and a list of strings as the value, 
                    where each string represents a device and its action concatenated with an underscore "_". 
                    If there are no devices required for the task, an empty list, [] could used.
                    But don't generate new action, must use prior action in {input_device_action_dict}.

                    For example, we have device_action_dictionary, as below.
                    {{
                        'RobotArm':['Grasp', 'Release', 'Move', 'Rotate', 'Extend', 'Retract', 'Stop'],
                        'Pipette':['Aspirate', 'Dispense', 'Wash', 'Mix', 'EjectTip', 'Stop'],
                        'Pump':['Start', 'Stop', 'Increase', 'Decrease', 'Reverse'],               
                        'Stirrer':['Stir', 'Heat', 'Stop'],                                           
                        'PowderDispenser'['Dispense', 'Stop'],                                               
                        'WeighingMachine'['Weigh', 'Tare', 'Stop'],                                          
                        'Heater':['Heat', 'Cool', 'Stop'],                                           
                    }}
                    When task name is 'BatchSynthesisModule_AddSolution', you recommend action sequence as 'RobotArm_Move', 'RobotArm_Grasp', 'Pipette_Aspirate', 'Pipette_Dispense', 'Pipette_EjectTip', 'RobotArm_Move', 'RobotArm_Release'.
                    When task name is 'BatchSynthesisModule_AddPowder', you recommend action sequence as 'RobotArm_Move', 'RobotArm_Grasp', 'RobotArm_Move', 'RobotArm_Release', 'PowderDispenser_Dispense', 'RobotArm_Move', 'RobotArm_Grasp', 'RobotArm_Move', 'RobotArm_Release'.
                    When task name is 'BatchSynthesisModule_Mix', you recommend action sequence as 'Stirrer_Stir'.
                    When task name is 'BatchSynthesisModule_Calcine', you recommend action sequence as 'Heater_Heat', 'Heater_Cool', 'Heater_Stop'.
                    When task name is 'BatchSynthesisModule_Grind', you recommend action sequence as 'RobotArm_Move', 'RobotArm_Grasp', 'RobotArm_Move', 'RobotArm_Release'.
                    When task name is 'BatchSynthesisModule_WeighPowder', you recommend action sequence as 'RobotArm_Move', 'RobotArm_Grasp', 'RobotArm_Move', 'RobotArm_Release', 'WeighingMachine_Tare', 'WeighingMachine_Weigh', 'RobotArm_Move', 'RobotArm_Grasp', 'RobotArm_Move', 'RobotArm_Release'.
                    

                    Please save device_action_dictionary as JSON format.
                    And, you must remove all annotations in json file.
                    """.format(input_task_list=task_list, input_device_action_dict=device_action_dict)
                }
            ]
        )
        answer = completion.choices[0].message.content
        print(completion.usage)

        with open(f"AutoModuleGeneration/GPT_answer_registration/{input_module_name}_actionsequence.txt", 'w') as file:
            file.write(answer)
    else:
        with open(f'AutoModuleGeneration/GPT_answer_registration/{input_module_name}_actionsequence.txt', 'r', encoding='utf-8') as file:
            answer = file.read()
    return answer

def GPT_generate_task_template(input_module_name:str, task_list:list, api_key:str, gpt_on=False):

    openai.api_key = api_key

    task_str=""
    for idx, arg in enumerate(task_list):
        task_str+=arg
        if idx == len(task_list)-1:
            task_str+=", "
    
    print("###################")
    print("[GPT]: task template generation...")
    print("###################")

    if gpt_on==True:
        task_template_prompt="I have a task list of {}, {}.\n".format(input_module_name, task_list)+"""
        And I need to specify the parameters for executing each task in the form of a dictionary template. 
        The number of hierarchy levels in template is limited to 3, and I won't create any more levels. 
        The first level in template will have keys "Task" and "Data", such as {"Task":"", "Data":{}}. 
        The key of second level in template will contain the necessary information for the task. 
        If some key of second level in template must include a quantitative value, the third level in template must use {"Value":0, "Dimension":""} this format. 
        Dimension must match with the chemical task. For example, AddSolution task should match "μL" or "mL", Press task should match "mPa", "Pa" or "atm".
        If some key of second level in template use material, powder, solution or gas, must add "Material" as key and {"Type":""} as value in the second level.
        Otherwise, other value of second level in template must include "Value" as key in template, such as {"Type":""}.
        If a specific task involves loading measurement, analysis or performance data, must use "Method" as key and {"Type":""} as value in the second level.

        More detailed information could increase the reliability of chemical task.
        Assign the task template names as variables for each task.
        Also, please define all task template without exception in task list.
        
        Define a pydantic class for each task, and don't skip some task, just define all of it. 
        Finally, you must save task template and pydantic class separately.

        if we set task list as BatchSynthesisModule_MoveContainer, BatchSynthesisModule_AddSolution, 
        BatchSynthesisModule_Stir, BatchSynthesisModule_Heat, BatchSynthesisModule_Mix,BatchSynthesisModule_React,
        answer may follow as below example script. Please refer below example code.

        **BatchSynthesisModule.json**
        ```python
        {
            "BatchSynthesisModule_MoveContainer":{
                "Task":"BatchSynthesisModule_MoveContainer",
                "Data":{
                        "FromTo":{"Type":""},
                        "Container":{"Type":""},
                        "Device":{}
                    }
            },
            "BatchSynthesisModule_AddSolution":{
                "Task":"BatchSynthesisModule_AddSolution",
                "Data":{
                    "Material":{"Type":""},
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
            },
            "BatchSynthesisModule_Heat":{
                "Task": "BatchSynthesisModule_Heat",
                "Data": {
                    "Temperature": {
                        "Value": 0,
                        "Dimension": "ºC"
                    },
                    "Device":{}
                }
            },
            "BatchSynthesisModule_Mix":{
                "Task": "BatchSynthesisModule_Mix",
                "Data": {
                    "Time": {
                        "Value": 0,
                        "Dimension": "sec"
                    },
                    "Device":{}
                }
            },
            "BatchSynthesisModule_Centrifugation":{
                "Task": "BatchSynthesisModule_Centrifugation",
                "Data": {
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
            },
            "BatchSynthesisModule_Sonication":{
                "Task": "BatchSynthesisModule_Sonication",
                "Data": {
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
        }
        ```
        In UVVisModule for characterization, if we set task list as UVVisModule_GetAbsorbanceTest, UVVisModule_GetFWHMTest, 
        answer may follow as below example script. Please refer below example code.

        **UVVisModule.json**
        ```python
        {
            "UVVisModule_GetAbsorbanceTest":{
                "Task": "UVVisModule_GetAbsorbanceTest",
                "Data": {
                    "Method":{
                        "Type":""
                    },
                    "Device":{}
                }
            },
            "UVVisModule_GetFWHMTest":{
                "Task": "UVVisModule_GetFWHMTest",
                "Data": {
                    "Method":{
                        "Type":""
                    }
                    "Device":{}
                }
            }
        }
        ```
        """
        completion_task_template = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",  # 사용할 GPT 모델 엔진
            # prompt=question,
            # max_tokens=150,  # 생성할 응답의 최대 토큰 수
            # n=1,  # 생성할 응답 수
            # stop=None,  # 응답 생성 중단 시퀀스
            temperature=0,  # 응답의 창의성 (0.0~1.0)
            messages=[
                {
                    "role": "system",
                    "content": """You are administrator of autonomous laboratory, which control AI and robotics for chemical experiments, 
                    and your role is the task template generation for chemical task.""",
                },
                {
                    "role": "user",
                    "content": task_template_prompt
                }
            ]
        )
        answer_template = completion_task_template.choices[0].message.content
        print("token :", completion_task_template.usage)

        with open(f"AutoModuleGeneration/GPT_answer_registration/{input_module_name}_task_template.txt", 'w') as file:
            file.write(answer_template)
    else:
        with open(f'AutoModuleGeneration/GPT_answer_registration/{input_module_name}_task_template.txt', 'r', encoding='utf-8') as file:
            answer_template = file.read()
    return answer_template

def GPT_generate_task_pydantic(input_module_name:str, task_list:list, input_answer_template:str, api_key:str, gpt_on=False):

    openai.api_key = api_key

    task_str=""
    for idx, arg in enumerate(task_list):
        task_str+=arg
        if idx == len(task_list)-1:
            task_str+=", "
    
    print("###################")
    print("[GPT]: task Pydantic generation...")
    print("###################")

    if gpt_on==True:
        task_template_prompt="I have a task list of {}, {}.\n".format(input_module_name, task_list)+"""
        And I need to specify the parameters for executing each task in the form of a dictionary template. 
        The number of hierarchy levels in template is limited to 3, and I won't create any more levels. 
        The first level in template will have keys "Task" and "Data", such as {"Task":"", "Data":{}}. 
        The key of second level in template will contain the necessary information for the task. 
        If some key of second level in template must include a quantitative value, the third level in template must use {"Value":0, "Dimension":""} this format. 
        Dimension must match with the chemical task. For example, AddSolution task should match "μL" or "mL", Press task should match "mPa", "Pa" or "atm".
        If some key of second level in template use material, powder, solution or gas, must add "Material" as key and {"Type":""} as value in the second level.
        Otherwise, other value of second level in template must include "Value" as key in template, such as {"Type":""}.
        If a specific task involves loading measurement, analysis or performance data, must use "Method" as key and {"Type":""} as value in the second level.

        More detailed information could increase the reliability of chemical task.
        Assign the task template names as variables for each task.
        Also, please define all task template without exception in task list.
        
        Define a pydantic class for each task, and don't skip some task, just define all of it. 
        Finally, you must save task template and pydantic class separately.

        if we set task list as BatchSynthesisModule_MoveContainer, BatchSynthesisModule_AddSolution, 
        BatchSynthesisModule_Stir, BatchSynthesisModule_Heat, BatchSynthesisModule_Mix,BatchSynthesisModule_React,
        answer may follow as below example script. Please refer below example code.

        **BatchSynthesisModule.json**
        ```python
        {
            "BatchSynthesisModule_MoveContainer":{
                "Task":"BatchSynthesisModule_MoveContainer",
                "Data":{
                        "FromTo":{"Type":""},
                        "Container":{"Type":""},
                        "Device":{}
                    }
            },
            "BatchSynthesisModule_AddSolution":{
                "Task":"BatchSynthesisModule_AddSolution",
                "Data":{
                    "Material":{"Type":""},
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
            },
            "BatchSynthesisModule_Heat":{
                "Task": "BatchSynthesisModule_Heat",
                "Data": {
                    "Temperature": {
                        "Value": 0,
                        "Dimension": "ºC"
                    },
                    "Device":{}
                }
            },
            "BatchSynthesisModule_Mix":{
                "Task": "BatchSynthesisModule_Mix",
                "Data": {
                    "Time": {
                        "Value": 0,
                        "Dimension": "sec"
                    },
                    "Device":{}
                }
            },
            "BatchSynthesisModule_Centrifugation":{
                "Task": "BatchSynthesisModule_Centrifugation",
                "Data": {
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
            },
            "BatchSynthesisModule_Sonication":{
                "Task": "BatchSynthesisModule_Sonication",
                "Data": {
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
        }
        ```
        In UVVisModule for characterization, if we set task list as UVVisModule_GetAbsorbanceTest, UVVisModule_GetFWHMTest, 
        answer may follow as below example script. Please refer below example code.

        **UVVisModule.json**
        ```python
        {
            "UVVisModule_GetAbsorbanceTest":{
                "Task": "UVVisModule_GetAbsorbanceTest",
                "Data": {
                    "Method":{
                        "Type":""
                    },
                    "Device":{}
                }
            },
            "UVVisModule_GetFWHMTest":{
                "Task": "UVVisModule_GetFWHMTest",
                "Data": {
                    "Method":{
                        "Type":""
                    }
                    "Device":{}
                }
            }
        }
        ```
        """
        task_pydantic_prompt="""Also, define a pydantic class followed by json file, and don't skip some task, just define all of it. 
        
        if we set task list as BatchSynthesisModule_MoveContainer, BatchSynthesisModule_AddSolution, 
        BatchSynthesisModule_Stir, BatchSynthesisModule_Heat, BatchSynthesisModule_Mix,BatchSynthesisModule_React,
        answer may follow as below example script. Please refer below example code.

        **BatchSynthesisModule.py**
        ```python
        from pydantic import BaseModel, Field
        from typing import Dict, Any, Optional, Union

        class BatchSynthesisModule_MoveContainer_FromTo(BaseModel):
            Type: str = ""

        class BatchSynthesisModule_MoveContainer_Container(BaseModel):
            Type: str = ""

        class BatchSynthesisModule_AddSolution_Material(BaseModel):
            Type: str = ""

        class BatchSynthesisModule_AddSolution_Volume(BaseModel):
            Value: Union[int, float] = 0
            Dimension: str = "μL"

        class BatchSynthesisModule_AddSolution_Concentration(BaseModel):
            Value: Union[int, float] = 0
            Dimension: str = "mM"
        
        class BatchSynthesisModule_AddSolution_Injectionrate(BaseModel):
            Value: Union[int, float] = 0
            Dimension: str = "μL/s"

        class BatchSynthesisModule_Heat_Temperature(BaseModel):
            Value: Union[int, float] = 0
            Dimension: str = "ºC"

        class BatchSynthesisModule_Mix_Time(BaseModel):
            Value: Union[int, float] = 0
            Dimension: str = "sec"

        class BatchSynthesisModule_Centrifugation_Power(BaseModel):
            Value: Union[int, float] = 0
            Dimension: str = "rpm"
        
        class BatchSynthesisModule_Centrifugation_Time(BaseModel):
            Value: Union[int, float] = 0
            Dimension: str = "sec"

        class BatchSynthesisModule_Sonication_Power(BaseModel):
            PowValue: Union[int, float] = 0
            Dimension: str = "kHz"

        class BatchSynthesisModule_Sonication_Time(BaseModel):
            Value: Union[int, float] = 0
            Dimension: str = "sec"
            
        class BatchSynthesisModule_MoveContainer_Data(BaseModel):
            FromTo: BatchSynthesisModule_MoveContainer_FromTo
            Container: BatchSynthesisModule_MoveContainer_Container
            Device: Dict[str, Any]

        class BatchSynthesisModule_AddSolution_Data(BaseModel):
            Material: BatchSynthesisModule_AddSolution_Material
            Volume: BatchSynthesisModule_AddSolution_Volume
            Concentration: BatchSynthesisModule_AddSolution_Concentration
            Injectionrate: BatchSynthesisModule_AddSolution_Injectionrate
            Device: Dict[str, Any]

        class BatchSynthesisModule_Heat_Data(BaseModel):
            Temperature: BatchSynthesisModule_Heat_Temperature
            Device: Dict[str, Any]

        class BatchSynthesisModule_Mix_Data(BaseModel):
            Time: BatchSynthesisModule_Mix_Time
            Device: Dict[str, Any]

        class BatchSynthesisModule_Centrifugation_Data(BaseModel):
            Power: BatchSynthesisModule_Centrifugation_Power
            Time: BatchSynthesisModule_Centrifugation_Time
            Device: Dict[str, Any]

        class BatchSynthesisModule_Sonication_Data(BaseModel):
            Power: BatchSynthesisModule_Sonication_Power
            Time: BatchSynthesisModule_Sonication_Time
            Device: Dict[str, Any]
        ```

        In UVVisModule for characterization, if we set task list as UVVisModule_GetAbsorbanceTest, UVVisModule_GetFWHMTest, 
        answer may follow as below example script. Please refer below example code.

        **UVVisModule.py**
        ```python
        from pydantic import BaseModel, Field
        from typing import Dict, Any, Optional, Union

        class UVVisModule_GetAbsorbanceTest_Method(BaseModel):
            Type: str = ""

        class UVVisModule_GetFWHMTest_Method(BaseModel):
            Type: str = ""

        class UVVisModule_GetAbsorbanceTest_Data(BaseModel):
            Method: UVVisModule_GetAbsorbanceTest_Method
            Device: Dict[str, Any]

        class UVVisModule_GetFWHMTest_Data(BaseModel):
            Method: UVVisModule_GetFWHMTest_Method
            Device: Dict[str, Any]
        ```
        """
        completion_pydantic_template = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",  # 사용할 GPT 모델 엔진
            # prompt=question,
            # max_tokens=150,  # 생성할 응답의 최대 토큰 수
            # n=1,  # 생성할 응답 수
            # stop=None,  # 응답 생성 중단 시퀀스
            temperature=0,  # 응답의 창의성 (0.0~1.0)
            messages=[
                {
                    "role": "system",
                    "content": """You are administrator of autonomous laboratory, which control AI and robotics for chemical experiments, 
                    and your role is the Pydantic generation for chemical task.""",
                },
                {
                    "role": "user",
                    "content": task_template_prompt
                },
                {
                    "role": "assistant",
                    "content": input_answer_template
                },
                {
                    "role": "user",
                    "content": task_pydantic_prompt
                }
            ]
        )
        answer_pydantic = completion_pydantic_template.choices[0].message.content
        print("token :", completion_pydantic_template.usage)

        with open(f"AutoModuleGeneration/GPT_answer_registration/{input_module_name}_task_pydantic.txt", 'w') as file:
            file.write(answer_pydantic)
    else:
        with open(f'AutoModuleGeneration/GPT_answer_registration/{input_module_name}_task_pydantic.txt', 'r', encoding='utf-8') as file:
            answer_pydantic = file.read()
    return answer_pydantic

def feedback_task_list(input_task_list:list):
    
    def display_task_list(task_list:list):
        print("\n###################")
        print("[Feedback system (task generation)]: current task List")
        print("###################")
        current_task_table = PrettyTable()
        current_task_table.field_names = ["idx", "current task name"]
        current_task_table.align = "l" 
        for i, task in enumerate(task_list):
            current_task_table.add_row([i+1, task])
        print(current_task_table)

    def get_user_input(task_list:list):
        while True:
            user_input = input("Enter the only task index to modify/delete (or 'done' to finish, 'back' to return): ").strip().lower()
            if user_input == 'done' or user_input == 'back':
                return user_input
            elif user_input.isdigit() and 1 <= int(user_input) <= len(task_list):
                return int(user_input)
            else:
                print("Invalid input, please try again.")
    
    while True:
        display_task_list(input_task_list)
        mode_type = input("Do you want to add, modify or delete this task? ('a'/'m'/'d') (or 'done' to finish): ").strip().lower()
        module_name, _=input_task_list[0].split("_")
        if mode_type == 'done':
            break
        elif mode_type == 'a':
            new_task = input("Enter the new task name ('back' to return): ").strip()
            if new_task == 'back':
                continue
            elif module_name not in new_task:
                input_task_list.append(f"{module_name}_{new_task.capitalize()}")
            else:
                input_task_list.append(new_task.capitalize())
        elif mode_type == 'm':
            user_input = get_user_input(input_task_list)
            if user_input == 'done':
                break
            elif user_input == 'back':
                continue
            else:
                index = user_input - 1
                new_task = input("Enter the new task name ('back' to return): ").strip()
                if new_task == 'back':
                    continue
                elif module_name not in new_task:
                    input_task_list[index]=f"{module_name}_{new_task.capitalize()}"
                else:
                    input_task_list[index] = new_task.capitalize()
        elif mode_type == 'd':
            user_input = get_user_input(input_task_list)
            if user_input == 'done':
                break
            elif user_input == 'back':
                continue
            else:
                index = user_input - 1
                del input_task_list[index]
        else:
            print("Invalid action, please try again.")
    
    print("\n###################")
    print("[Feedback system (task generation)]: Final task List")
    print("###################")

    final_task_table = PrettyTable()
    final_task_table.field_names = ["idx", "final task name"]
    final_task_table.align = "l" 
    for i, task in enumerate(input_task_list):
        final_task_table.add_row([i+1, task])
    print(final_task_table)
    
    return input_task_list

def feedback_task_action_sequence(input_task_list:list, input_task_deviceaction_dict:dict, input_action_type_dict:dict):
    # Iterate over each task in the task list
    for task_idx, task in enumerate(input_task_list):
        deviceactions = copy.deepcopy(input_task_deviceaction_dict[task])  # List to hold deviceactions for the current task
        # print("device-action:{}\n".format(json.dumps(input_action_type_dict, indent=4)))
        print(f"[Feedback system (match task-->device-action)]: Devices registration for {task} (type 'done' when finished)")
        
        while True:
            total_action_list=[]
            deviceaction_table = PrettyTable()
            deviceaction_table.field_names = ["device", "action list"]
            deviceaction_table.align = "l" 
            for device in input_action_type_dict.keys():
                deviceaction_table.add_row([device, input_action_type_dict[device]])
                for action in input_action_type_dict[device]:
                    total_action_list.append("{}_{}".format(device, action))
            print(deviceaction_table)
            
            print("\n###################")
            print("[Feedback system]: task {}-->{}".format(task_idx, task))
            print("###################")

            # delete undefined action
            len_deviceactions=copy.deepcopy(deviceactions)
            for deviceaction in len_deviceactions:
                if deviceaction not in total_action_list:
                    deviceactions.remove(deviceaction)
            # print recommend action
            recommended_deviceaction_table = PrettyTable()
            recommended_deviceaction_table.field_names = ["idx", f"{task} --> device:action"]
            recommended_deviceaction_table.align = "l" 
            for idx in range(len(deviceactions)):
                recommended_deviceaction_table.add_row([idx+1, deviceactions[idx]])
            print(recommended_deviceaction_table)

            # feedback system
            mode_type = input(f"Do you want to insert, switch or delete device action of {task}? ('i'/'s'/'d' or 'done'): ").strip().lower()
            if mode_type.lower() == 'done':
                break
            elif mode_type == 'i':
                try:
                    device_table = PrettyTable()
                    device_table.field_names = ["idx", "current devices"]
                    device_table.align = "l" 
                    for idx in range(len(list(input_action_type_dict.keys()))):
                        device_table.add_row([idx+1, list(input_action_type_dict.keys())[idx]])
                    print(device_table)
                    device_index = int(input(f"Enter a addtional device index for {task}: ").strip())
                    device_name=list(input_action_type_dict.keys())[device_index-1]
                    
                    deviceaction_table = PrettyTable()
                    deviceaction_table.field_names = ["idx", f"total actions of {device_name}"]
                    deviceaction_table.align = "l" 
                    for idx in range(len(input_action_type_dict[device_name])):
                        deviceaction_table.add_row([idx+1, input_action_type_dict[device_name][idx]])
                    print(deviceaction_table)
                    action_index = int(input(f"Enter a addtional device action index for {task}: ").strip())
                    action_name=input_action_type_dict[device_name][action_index-1]
                    
                    device_insert_index = int(input(f"Enter a index of inserted action for {task} (start --> 1): ").strip())
                    if device_insert_index >= 1 and device_insert_index <= len(deviceactions)+1:
                        deviceactions.insert(device_insert_index-1, f"{device_name}_{action_name}")
                    else:
                        print("IndexError --> Your input index:{}, please input 1 <= index <= {}".format(device_insert_index, len(deviceactions)+1))
                except KeyError:
                    print("Please input this device name: {}".format(list(input_action_type_dict.keys())))
                except ValueError as e:
                    print("Please input index number:",e)
            elif mode_type == 's':
                try:
                    deviceaction_1_index = int(input(f"Enter a index of the device action to switch: ").strip())
                    deviceaction_2_index = int(input(f"Enter the other index of device action to switch: ").strip())
                    deviceactions[deviceaction_1_index-1], deviceactions[deviceaction_2_index-1] = deviceactions[deviceaction_2_index-1], deviceactions[deviceaction_1_index-1]
                except ValueError as e:
                    print("Please input index number:",e)
            elif mode_type == 'd':
                try:
                    answer=input(f"Enter a index of device to delete for {task}, or 'back': ").strip()
                    if answer=="back":
                        continue
                    else:
                        device_insert_index = int(answer)
                        deviceactions.pop(device_insert_index-1)
                except IndexError as e:
                    print("Oversize of index (out of range), Please input correct index number:",e)
                except ValueError as e:
                    print("Please input index number:",e)
        
        # Add the deviceactions list to the dictionary with the task as the key
        input_task_deviceaction_dict[task] = deviceactions

    ##############################
    # Print the final dictionary
    ##############################
    print("\n###################")
    print("[Feedback system (match task-->device-action)]: Final Device:Action List")
    print("###################")

    task_deviceactionlist_table = PrettyTable()
    task_deviceactionlist_table.field_names = ["task", "device:action list"]
    task_deviceactionlist_table.align = "l" 
    for task, deviceaction_list in input_task_deviceaction_dict.items():
        task_deviceactionlist_table.add_row([task, deviceaction_list])
    print(task_deviceactionlist_table)

    return input_task_deviceaction_dict

def feedback_task_template(test_json_str: str):
    test_json=ast.literal_eval(test_json_str)
    save_test_json=copy.deepcopy(test_json)
    # Iterate over each task in the task list
    for task_idx, task_name in enumerate(list(test_json.keys())):
        task_data = copy.deepcopy(test_json[task_name]["Data"])
        
        print(f"[Feedback system (modify task template)]: Data modification for {task_name} template (type 'done' when finished)")
        
        while True:
            data_table = PrettyTable()
            data_table.field_names = ["index", f"key of '{task_name}'", f"value of '{task_name}'"]
            data_table.align = "l"
            
            for idx, (key, value) in enumerate(task_data.items(), 1):
                data_table.add_row([idx, key, value])
            print(data_table)
            
            print("\n###################")
            print(f"[Feedback system]: task {task_idx} --> '{task_name}'")
            print("###################")
            
            # Feedback system
            mode_type = input(f"Do you want to add, rename or delete data of '{task_name}' template? ('a'/'r'/'d' or 'done'): ").strip().lower()
            if mode_type == 'done':
                break
            elif mode_type == 'a':
                key = input(f"Enter an additional key for {task_name}: ").strip().capitalize()
                value = input(f"Is it quantitive value type for the key? 'y'/'n' or 'back' :'{key}': ").strip().lower()
                if value == "y":
                    dimension = input(f"Please input dimension of value (ex. mL, μL or mL/s, mPa, mV... etc) :'{key}': ").strip()
                    task_data[key] = {
                            "Value": 0,
                            "Dimension": dimension
                        }
                elif value == "n":
                    task_data[key] = {"Type": ""}
                elif value == "back":
                    continue
                else:
                    print("Please input 'y', 'n', or 'back', not {}".format(value))
            elif mode_type == 'r':
                try:
                    old_key_index = int(input(f"Enter the index of key to rename: ").strip())-1
                    old_key=list(task_data.keys())[old_key_index]

                    dimension_or_not=input(f"Do you want to rename key ('k') or value ('v')? press 'k'/'v' or 'back: ").strip()
                    if dimension_or_not == "k":
                        old_task_data=task_data.pop(old_key)
                        new_key = input(f"Enter the new key to rename: ").strip().capitalize()
                        value = input(f"Is it quantitive value type for the key? 'y'/'n' or 'back' :").strip().lower()
                        if value == "y":
                            dimension = input(f"Please input dimension of value (ex. mL, μL or mL/s, mPa, mV... etc) :").strip()
                            task_data[new_key] = old_task_data
                        elif value == "n":
                            task_data[new_key] = {"Type": ""}
                        elif value == "back":
                            continue
                        else:
                            print("Please input 'y', 'n', or 'back', not {}".format(value))
                    elif dimension_or_not == "v":
                        dimension = input(f"Please input dimension of value (ex. mL, μL or mL/s, mPa, mV... etc) :").strip()
                        task_data[old_key] = {
                                "Value": 0,
                                "Dimension": dimension
                            }
                    elif value == "back":
                        continue
                    else:
                        print("Please input 'y', 'n', or 'back', not {}".format(value))
                except KeyError:
                    print(f"No '{old_key}' key in key_list={list(task_data.keys())}")
            elif mode_type == 'd':
                try:
                    old_key_index = int(input(f"Enter the key to delete: ").strip())-1
                    if old_key == "back":
                        continue
                    else:
                        old_key=list(task_data.keys())[old_key_index]
                        task_data.pop(old_key)
                except KeyError:
                    print(f"No '{old_key}' key in key_list={list(task_data.keys())}")
        
        # Update the task data in the dictionary
        save_test_json[task_name]["Data"] = task_data
    
    ##############################
    # Print the final dictionary
    ##############################
    print("\n###################")
    print("[Feedback system (modify task template)]: Final Task Template")
    print("###################")
    
    task_data_table = PrettyTable()
    task_data_table.field_names = ["task", "template"]
    task_data_table.align = "l"
    
    for task_name, task_data in save_test_json.items():
        task_data_table.add_row([task_name, task_data["Data"]])
    print(task_data_table)

    return save_test_json

def feedback_device_standby_time_list(input_task_list:list):
    try:
        with open(f"Job/device_standby_time.json", 'r', encoding='utf-8') as f:
            device_standby_time_dict=json.load(f)
    except FileNotFoundError:
        device_standby_time_dict={}
    except json.decoder.JSONDecodeError:
        device_standby_time_dict={}
    module_name, _=input_task_list[0].split("_")

    return_task_list=[]
    def display_task_list(task_list:list):
        print("\n###################")
        print("[Feedback system (Address long device stanby time)]: current task List")
        print("###################")
        current_task_table = PrettyTable()
        current_task_table.field_names = ["idx", "current task name"]
        current_task_table.align = "l" 
        for i, task in enumerate(task_list):
            current_task_table.add_row([i+1, task])
        print(current_task_table)

    def get_user_input(task_list:list):
        while True:
            user_input = input("Enter the only task index to add/delete in long device standby time, derived bottleneck (or 'done' to finish, 'back' to return): ").strip().lower()
            if user_input == 'done' or user_input == 'back':
                return user_input
            elif user_input.isdigit() and 1 <= int(user_input) <= len(task_list):
                return int(user_input)
            else:
                print("Invalid input, please try again.")
    
    while True:
        display_task_list(input_task_list)
        mode_type = input("Do you want to add or delete this task with long device standby time (bottleneck in module)? ('a'/'d') (or 'done' to finish): ").strip().lower()
        if mode_type == 'done':
            break
        elif mode_type == 'a':
            user_input = get_user_input(input_task_list)
            if user_input == 'done':
                break
            elif user_input == 'back':
                continue
            else:
                index = user_input - 1
                return_task_list.append(input_task_list[index])
        elif mode_type == 'd':
            user_input = get_user_input(input_task_list)
            if user_input == 'done':
                break
            elif user_input == 'back':
                continue
            else:
                index = user_input - 1
                del return_task_list[index]
        else:
            print("Invalid action, please try again.")
    
        task_table = PrettyTable()
        task_table.field_names = ["idx", "final addressed task with device standby time"]
        task_table.align = "l" 
        for i, task in enumerate(return_task_list, 1):
            task_table.add_row([i, task])
        print(task_table)
    
    print("\n###################")
    print("[Feedback system (address device standby time)]: Final task List")
    print("###################")

    final_task_table = PrettyTable()
    final_task_table.field_names = ["idx", "final addressed task with device standby time"]
    final_task_table.align = "l" 
    for i, task in enumerate(return_task_list, 1):
        final_task_table.add_row([i, task])
    print(final_task_table)

    device_standby_time_dict[module_name]=return_task_list
    with open(f"Job/device_standby_time.json", 'w', encoding='utf-8') as json_file:
        json.dump(device_standby_time_dict, json_file, indent=4)
    
def extract_code_task(input_string:str):
    try:
        filecontent_pattern = re.compile(r'```python(.*?)```', re.DOTALL)
        filecontent = filecontent_pattern.findall(input_string)
        parsed_code = ast.parse(filecontent[0].strip())
        assign_node = parsed_code.body[0]
        tasks_list = ast.literal_eval(assign_node.value)

        return tasks_list
    
    except IndexError as e:
        IndexError("GPT results has wrong pattern of code generation.)", e)

def extract_code_task_pydantic(input_string:str):
    try:
        filecontent_pattern = re.compile(r'```python(.*?)```', re.DOTALL)
        filecontent_list = filecontent_pattern.findall(input_string)
        return filecontent_list[0]

    except IndexError as e:
        IndexError("GPT results has wrong pattern of code generation.)", e)

def extract_code_task_template(input_string:str):
    try:
        filecontent_pattern = re.compile(r'```json(.*?)```', re.DOTALL)
        filecontent_list = filecontent_pattern.findall(input_string)
        return filecontent_list[0]

    except IndexError as e:
        IndexError("GPT results has wrong pattern of code generation.)", e)

def extract_code_task_action_sequence(input_string:str):
    try:
        filecontent_pattern = re.compile(r'```json(.*?)```', re.DOTALL)
        filecontent_list = filecontent_pattern.findall(input_string)
        json_string_no_comments = re.sub(r'//.*', '', filecontent_list[0])
        return_task_deviceaction_dict = ast.literal_eval(json_string_no_comments)
        return return_task_deviceaction_dict

    except IndexError as e:
        IndexError("GPT results has wrong pattern of code generation.)", e)

def save_to_files_pydantic(module_name:str, code_str:str):
    with open(f"Task/Pydantic/{module_name}.py", 'w') as file:
        file.write(code_str)

def save_to_files_task_template(module_name:str, code_dict:dict):
    with open(f"Task/Template/{module_name}.json", 'w') as json_file:
        # file.write(code_str)
        json.dump(code_dict, json_file, indent=4)

def script_add_routing_table(input_module_name:str, ip:str, port:int):
    print("\n###################")
    print("[Code generation (ActionExecutor -> add routing table)]: add ip/port of module node in routing table")
    print("###################")
    try:
        with open("Action/routing_table.json", 'r', encoding='utf-8') as file:
            routing_table = json.load(file)
    except FileNotFoundError as e:
        routing_table=dict() # generate new ip_table_dict
    finally:
        ip_port_dict=dict()
        ip_port_dict["HOST"]=ip
        ip_port_dict["PORT"]=port
        routing_table[input_module_name]=ip_port_dict
        with open("Action/routing_table.json", 'w') as file:
            json.dump(routing_table, file, indent=4)

def json_add_template_module(input_module_name:str):
    print("\n###################")
    print("[Code generation (template registration)]: register template of module node in 'Task/Template/Template_module.json'")
    print("###################")
    if os.path.isdir(f"Task/Template") == False:
        os.makedirs(f"Task/Template")
    with open("Task/Template/Template_module.json", 'r', encoding='utf-8') as file:
        module_template = json.load(file)
    module_template[input_module_name]={
        "Module":input_module_name,
        "Data":[]
    }
    with open("Task/Template/Template_module.json", 'w') as file:
        json.dump(module_template, file, indent=4)

def script_generation_actiontranslator_class(formatted_time:str, author:str, input_module_name:str, 
                                        module_type:str, task_list:list, action_type_dict:dict, task_deviceaction_dict:dict):
    print("\n###################")
    print(f"[Code generation (ActionTranslator->{input_module_name})]: Code generation of {input_module_name} in AcionTranslator, followed by GPT/Feedback system result")
    print("###################")
    
    """
    action_type_dict={
        'STIRRER': ['Heat', 'Stir', 'Stop', 'heartbeat'], 
        'POWDERDISPENSER': ['Dispense', 'Stop', 'heartbeat'], 
        'WEIGHINGMACHINE': ['Stop', 'Tare', 'Weigh', 'heartbeat'], 
        'HEATER': ['Cool', 'Heat', 'Stop', 'heartbeat'], 
        'XRD': ['Align', 'Scan', 'Stop', 'heartbeat'], 
        'ROBOTARM': ['Grip', 'Move', 'Position', 'Release', 'Rotate', 'heartbeat'], 
        'PIPETTE': ['Aspirate', 'Calibrate', 'Dispense', 'Mix', 'Wash', 'heartbeat'], 
        'PUMP': ['Decrease', 'Increase', 'Reverse', 'Start', 'Stop', 'heartbeat']
    }
    task_deviceaction_dict={
        "SolidStateModule_LoadPowder" : ['POWDERDISPENSER_Dispense']
        "SolidStateModule_MeasureWeight" : ['WEIGHINGMACHINE_Tare', 'WEIGHINGMACHINE_Weigh']
        "SolidStateModule_MixPowders" : ['STIRRER_Stir']
        "SolidStateModule_PressPowder" : ['ROBOTARM_Position', 'ROBOTARM_Grip', 'ROBOTARM_Move', 'ROBOTARM_Release']
        "SolidStateModule_Sinter" : ['HEATER_Heat']
        "SolidStateModule_CoolDown" : ['HEATER_Cool']
        "SolidStateModule_Characterize" : ['ROBOTARM_Move', 'ROBOTARM_Position']
        "SolidStateModule_XRayDiffractionTest" : ['XRD_Align', 'XRD_Scan']
        "SolidStateModule_ScanningElectronMicroscopyTest" : ['ROBOTARM_Position', 'ROBOTARM_Move']
        "SolidStateModule_DensityMeasurementTest" : ['WEIGHINGMACHINE_Weigh', 'PIPETTE_Dispense']
        "SolidStateModule_PorosityTest" : ['ROBOTARM_Move', 'ROBOTARM_Position']
        "SolidStateModule_MechanicalStrengthTest" : ['ROBOTARM_Move', 'ROBOTARM_Position']
        "SolidStateModule_ThermalConductivityTest" : ['HEATER_Heat', 'PUMP_Start', 'PUMP_Stop']
        "SolidStateModule_MagneticPropertyTest" : ['ROBOTARM_Move', 'ROBOTARM_Position']
        "SolidStateModule_ElectricalConductivityTest" : ['ROBOTARM_Move', 'ROBOTARM_Position']
        "SolidStateModule_CalorimetryTest" : ['STIRRER_Heat', 'PUMP_Start', 'PUMP_Stop']
        "SolidStateModule_CleanUp" : ['STIRRER_Stop', 'HEATER_Stop', 'XRD_Stop', 'PIPETTE_Wash']
        "SolidStateModule_StoreSample" : ['ROBOTARM_Grip', 'ROBOTARM_Move', 'ROBOTARM_Release']
    }
    """
    script_analysis=f'''# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [{input_module_name}] Analysis function of {input_module_name} for raw spectrum
# author {author}
# GENEREATION {formatted_time}

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os, time
from collections import OrderedDict
        '''
    script_actiontranslator=f'''# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [{input_module_name}] {input_module_name} class file
# author {author}
# GENEREATION {formatted_time}

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
from Task.Pydantic.{input_module_name} import *


class {input_module_name}(ActionExecutor):
    """
    [{input_module_name}] {input_module_name} class 

    # Variable
    :param module_name="{input_module_name}" (str): set module name
    :param ResourceManager_obj=object (object): set resource manager object

    # Device : Actions
    {action_type_dict}

    # Task --> device_action list
    {task_deviceaction_dict}

    # function
        '''
    for idx, task in enumerate(task_list):
        if idx==0:
            script_actiontranslator+="\n"
        script_line=f"    {idx+1}. {task}(task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type='virtual')\n"
        script_actiontranslator+=script_line
    script_init=f'''
    """
    def __init__(self,module_name="{input_module_name}", ResourceManager_obj=object):
        ActionExecutor.__init__(self,)
        self.__{input_module_name}_name= module_name
        self.ResourceManager_obj=ResourceManager_obj

    def executeAction(self, module_name:str, jobID:int, device_name:str, action_type:str, action_data:Union[str, int, list], mode_type:str, TaskLogger_obj:object, data_dict:dict):
        TaskLogger_obj.debug(device_name, f"{{action_type}}-->Start!")
        command_str=self.packetFormatter(jobID,device_name,action_type,action_data,mode_type)
        TaskLogger_obj.debug(device_name, f"{{action_type}}-->Done!")
        res_msg = self.transferDeviceCommand(module_name, command_str=command_str)
        try:
            res_dict=json.loads(res_msg)
            data_dict[action_type]=res_dict
        except json.decoder.JSONDecodeError:
            pass
        return data_dict
        '''
    script_actiontranslator+=script_init
    for task in task_list:
        ##########################
        # upload templates of task
        ##########################
        try:
            with open(f"Task/Template/{input_module_name}.json", 'r', encoding='utf-8') as f:
                task_template=json.load(f)
            task_template=json.dumps(task_template[task], ensure_ascii=False, indent=4)
        except json.decoder.JSONDecodeError:
            raise json.decoder.JSONDecodeError("Oversize of GPT Token. Please check your "+f"Task/Template/{input_module_name}.json, and reduce or integrate some tasks")

        script_function_1='''
    def {input_task}(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        """
        Add solution depending on task_info_list. This list included 1 cycle batch synthesis process.

        :param task_info_list (list): "Task":"{input_task}","Data":[] <- task_info_list

        :return res_msg (str) : response message from Windows10 // str == real mode, bool == virtual mode
        """
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        TaskLogger_obj.debug(self.__{input_module_name}_name, "Start "+current_func_name+" Queue")
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
            TaskLogger_obj.current_module_name=self.__{input_module_name}_name+"-->"+current_func_name
            TaskLogger_obj.status=str(len(task_info_list))+"_"+str(task_idx)+"/"+str(TaskLogger_obj.totalExperimentNum)+":"+str(TaskLogger_obj.current_module_name) # in execution system

            # verify task_dict with task template
            try: # validation of task_dict
                _ = {input_task}_Data(**task_dict)
            except ValidationError as e:
                raise ValidationError(e)

            #################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            # action_type_dict : Please refer action type of this module
            """
            Please construct action_data, using below information (action_type_list, location_dict, task_dict, task_idx).

            1. action_type_list (list)={action_type_list}
            2. location_dict (dict)= --> result of ResouceManager.allocateResource
            3. task_dict ()={task_template}
            4. task_idx
            """
            data_dict=dict()
            # data_dict["Reference"]=reference_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
            # data_dict["Absorbance"]=absorbance_dict, # just example. please modify depending on your module, and add new code in "Analysis.Analysis.calculateData"
        '''.format(input_module_name=input_module_name, input_task=task, action_type_list=task_deviceaction_dict[task], task_template=task_template)
        script_actiontranslator+=script_function_1
        ##################################################################
        # add action following action sequence of task_deviceaction_dict
        ##################################################################
        for deviceaction in task_deviceaction_dict[task]:
            device_name, action_type=deviceaction.split("_")
            script_actiontranslator+=f"""
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            data_dict=self.executeAction(self.__{input_module_name}_name,jobID,"{device_name}","{action_type}","please extract action_data in task_dict",mode_type, TaskLogger_obj, data_dict)
            """
        if module_type=="Synthesis" or module_type=="Preprocess":
            script_actiontranslator+='''#################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)

        TaskLogger_obj.debug(self.__{input_module_name}_name, "Finish "+current_func_name+" Queue")

        return res_msg
            '''.format(input_module_name=input_module_name)
        elif module_type=="Evaluation" or module_type=="Characterization":
            temp_module_name, temp_task_name=task.split("_")
            if "test" in temp_task_name.lower() or "analyze" in temp_task_name.lower() or "record" in temp_task_name.lower() or "store" in temp_task_name.lower() or "perform" in temp_task_name.lower() or "measure" in temp_task_name.lower() or "data" in temp_task_name.lower():
                script_actiontranslator+='''#################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            result, each_calculate_res_dict=calculateData(current_func_name, data_dict) 
            TaskLogger_obj.debug(self.__{input_module_name}_name, "{{}} result : {{}}".format(task_idx, result))
            task_dict["Data"]=each_calculate_res_dict
            result_list.append(task_dict)

            self.ResourceManager_obj.updateStatus(current_func_name, False)
        
        TaskLogger_obj.debug(self.__{input_module_name}_name, "Finish "+current_func_name+" Queue")

        return result_list
            '''.format(input_module_name=input_module_name)
                script_analysis+=f'''
def {temp_task_name}(data_dict:dict):
    
    pass
    # return result, clean_dict
'''
            else:
                script_actiontranslator+='''#################################################################################################
            # Please configure the sequence and types of actions according to the module's robotic setting. #
            #################################################################################################
            self.ResourceManager_obj.updateStatus(current_func_name, False)
        
        TaskLogger_obj.debug(self.__{input_module_name}_name, "Finish "+current_func_name+" Queue")

        return res_msg
            '''.format(input_module_name=input_module_name)
        else:
            raise ValueError(f"Wrong module type:{module_type}. Please input correct module type, following ['Synthesis', 'Preprocess', 'Evaluation', 'Characterization']")
    
    # save task_device_actiontype_dict as json
    # {
    #   'SolidStatModule_Weigh':{'ROBOTARM': ['Grip', 'Move', 'Position', 'Release', 'Rotate', 'heartbeat'], 'WEIGHINGMACHINE': ['Stop', 'Tare', 'Weigh', 'heartbeat']},
    #   'SolidStatModule_Dispense':{'PIPETTE': ['Aspirate', 'Calibrate', 'Dispense', 'Mix', 'Wash', 'heartbeat'], 'ROBOTARM': ['Grip', 'Move', 'Position', 'Release', 'Rotate', 'heartbeat'], 'PUMP': ['Decrease', 'Increase', 'Reverse', 'Start', 'Stop', 'heartbeat']}
    # }

    ###########################################
    # save task -> device_action as json file
    ###########################################
    if os.path.isdir(f"Task/ActionSequence") == False:
        os.makedirs(f"Task/ActionSequence")
    with open(f"Task/ActionSequence/{input_module_name}.json", 'w', encoding='utf-8') as file:
        json.dump(task_deviceaction_dict, file, indent=4)

    ###########################################
    # save task -> device_action as json file
    ###########################################
    if os.path.isdir(f"Action/Module") == False:
        os.makedirs(f"Action/Module")
    with open(f"Action/Module/{input_module_name}.py", 'w') as file:
        file.write(script_actiontranslator)

    ###########################################
    # save analysis template
    ###########################################
    if os.path.isdir(f"Analysis/Module") == False:
        os.makedirs(f"Analysis/Module")
    with open(f"Analysis/Module/{input_module_name}.py", 'w') as file:
        file.write(script_analysis)

def script_generation_resourcemanager_class(formatted_time:str, author:str, input_module_name:str, 
                                        module_resource_dict:dict,action_type_dict:dict, task_deviceaction_dict:dict):
    """
    action_type_dict={
        'STIRRER': ['Heat', 'Stir', 'Stop', 'heartbeat'], 
        'POWDERDISPENSER': ['Dispense', 'Stop', 'heartbeat'], 
        'WEIGHINGMACHINE': ['Stop', 'Tare', 'Weigh', 'heartbeat'], 
        'HEATER': ['Cool', 'Heat', 'Stop', 'heartbeat'], 
        'XRD': ['Align', 'Scan', 'Stop', 'heartbeat'], 
        'ROBOTARM': ['Grip', 'Move', 'Position', 'Release', 'Rotate', 'heartbeat'], 
        'PIPETTE': ['Aspirate', 'Calibrate', 'Dispense', 'Mix', 'Wash', 'heartbeat'], 
        'PUMP': ['Decrease', 'Increase', 'Reverse', 'Start', 'Stop', 'heartbeat']
    }
    task_deviceaction_dict={
        "SolidStateModule_LoadPowder" : ['POWDERDISPENSER_Dispense']
        "SolidStateModule_MeasureWeight" : ['WEIGHINGMACHINE_Tare', 'WEIGHINGMACHINE_Weigh']
        "SolidStateModule_MixPowders" : ['STIRRER_Stir']
        "SolidStateModule_PressPowder" : ['ROBOTARM_Position', 'ROBOTARM_Grip', 'ROBOTARM_Move', 'ROBOTARM_Release']
        "SolidStateModule_Sinter" : ['HEATER_Heat']
        "SolidStateModule_CoolDown" : ['HEATER_Cool']
        "SolidStateModule_Characterize" : ['ROBOTARM_Move', 'ROBOTARM_Position']
        "SolidStateModule_XRayDiffractionTest" : ['XRD_Align', 'XRD_Scan']
        "SolidStateModule_ScanningElectronMicroscopyTest" : ['ROBOTARM_Position', 'ROBOTARM_Move']
        "SolidStateModule_DensityMeasurementTest" : ['WEIGHINGMACHINE_Weigh', 'PIPETTE_Dispense']
        "SolidStateModule_PorosityTest" : ['ROBOTARM_Move', 'ROBOTARM_Position']
        "SolidStateModule_MechanicalStrengthTest" : ['ROBOTARM_Move', 'ROBOTARM_Position']
        "SolidStateModule_ThermalConductivityTest" : ['HEATER_Heat', 'PUMP_Start', 'PUMP_Stop']
        "SolidStateModule_MagneticPropertyTest" : ['ROBOTARM_Move', 'ROBOTARM_Position']
        "SolidStateModule_ElectricalConductivityTest" : ['ROBOTARM_Move', 'ROBOTARM_Position']
        "SolidStateModule_CalorimetryTest" : ['STIRRER_Heat', 'PUMP_Start', 'PUMP_Stop']
        "SolidStateModule_CleanUp" : ['STIRRER_Stop', 'HEATER_Stop', 'XRD_Stop', 'PIPETTE_Wash']
        "SolidStateModule_StoreSample" : ['ROBOTARM_Grip', 'ROBOTARM_Move', 'ROBOTARM_Release']
    }
    """
    ################################
    # update device location
    ################################
    try:
        with open(f"Resource/device_location.json", 'r', encoding='utf-8') as f:
            task_device_location_dict=json.load(f)
    except FileNotFoundError:
        task_device_location_dict={}
    
    task_device_location_dict[input_module_name]=module_resource_dict
    ################################
    # update device status
    ################################
    try:
        with open(f"Resource/device_status.json", 'r', encoding='utf-8') as f:
            task_device_status_dict=json.load(f)
    except FileNotFoundError:
        task_device_status_dict={}

    task_device_status_dict[input_module_name]={}
    module_device_list=list(action_type_dict.keys())
    for module_device in module_device_list:
        task_device_status_dict[input_module_name][f"{input_module_name}_{module_device}"]=False
    ##############################################################
    # update masking table --> protect for collision between each devices
    ##############################################################
    try:
        with open(f"Resource/device_masking_table.json", 'r', encoding='utf-8') as f:
            task_device_mask_dict=json.load(f)
    except FileNotFoundError:
        task_device_mask_dict={}

    # reset
    task_device_mask_dict[input_module_name]={}

    # add new devices for each previous task (optional).
    print("\n###############")
    print("[Feedback system (ResourceManager->Masking Table)] (Optional) add new devices for each previous task")
    print("###############\n")
    previous_task_list=[]
    previous_task_masking_table_list=[]
    for module_masking_table in task_device_mask_dict.values():
        for task_name, task_masking_table in module_masking_table.items():
            previous_task_list.append(task_name)
            previous_task_masking_table_list.append(task_masking_table)
    
    current_all_task_masking_table = PrettyTable()
    current_all_task_masking_table.field_names = ["idx", "task name", "current masking table"]
    current_all_task_masking_table.align = "l" 
    for idx in range(len(previous_task_masking_table_list)):
        current_all_task_masking_table.add_row([idx+1, previous_task_list[idx], previous_task_masking_table_list[idx]])
    print(current_all_task_masking_table)
    while True:
        
        mode_type = input(f"Is there a system for sharing newly registered {input_module_name} and devices? ('y'/'n'): ").strip().lower()
        if mode_type == 'n':
            break
        elif mode_type == 'y':
            def get_user_input(task_list:list):
                while True:
                    user_input = input("Enter the only task index to add new devices in masking table (or 'done' to finish, 'back' to return): ").strip().lower()
                    if user_input == 'done' or user_input == 'back':
                        return user_input
                    elif user_input.isdigit() and 1 <= int(user_input) <= len(task_list):
                        return int(user_input)
                    else:
                        print("Invalid input, please try again.")
            user_input=get_user_input(previous_task_list)
            if user_input == 'done':
                break
            elif user_input == 'back':
                continue
            else:
                index = user_input - 1
                pick_task_name=previous_task_list[index]
                pick_task_masking_table=previous_task_masking_table_list[index]
                
                module_device_list=list(action_type_dict.keys())
                
                current_module_device_table = PrettyTable()
                current_module_device_table.field_names = ["idx", f"new {input_module_name} --> current devices"]
                current_module_device_table.align = "l" 
                for idx in range(len(module_device_list)):
                    current_module_device_table.add_row([idx+1, module_device_list[idx]])
                print(current_module_device_table)
                
                while True:
                    def get_user_input_device_index(task_list:list):
                        while True:
                            user_input_device_index = input("Enter the only device index to add in masking table (or 'done' to finish, 'back' to return): ").strip().lower()
                            if user_input_device_index == 'done' or user_input_device_index == 'back':
                                return user_input_device_index
                            elif user_input_device_index.isdigit() and 1 <= int(user_input_device_index) <= len(task_list):
                                return int(user_input_device_index)
                            else:
                                print("Invalid input, please try again.")
                    user_input_device_index=get_user_input_device_index(module_device_list)
                    if user_input_device_index == 'done':
                        break
                    elif user_input_device_index == 'back':
                        continue
                    else:
                        index = user_input_device_index - 1
                        device_name=module_device_list[index]
                        if "{}_{}".format(input_module_name, device_name) in pick_task_masking_table:
                            print("{}_{} is already added in masking table".format(input_module_name, device_name))
                        else:
                            pick_task_masking_table.append("{}_{}".format(input_module_name, device_name))
                    print(f'Add new device ({input_module_name}_{device_name}) in masking table: {pick_task_masking_table}')
        else:
            continue

    # add new module node in masking table
    module_task_list=list(task_deviceaction_dict.keys())
    for module_task in module_task_list:
        task_deviceaction_list=task_deviceaction_dict[module_task]
        current_all_device_list=[]
        for module_name in list(task_device_status_dict.keys()):
            current_all_moduledevice_list=list(task_device_status_dict[module_name].keys())
            current_all_device_list.extend(current_all_moduledevice_list)

        masking_device_list=[]
        for deviceaction in task_deviceaction_list:
            device, _ = deviceaction.split("_")
            masking_device_list.append(f"{input_module_name}_{device}")
        masking_device_list=list(set(masking_device_list))
        
        while True:
            print("\n###############")
            print("[Feedback system (ResourceManager->Masking Table)] current addressed device list")
            print("###############\n")
            current_all_device_table = PrettyTable()
            current_all_device_table.field_names = ["idx", f"{module_task} --> current all device"]
            current_all_device_table.align = "l" 
            for idx in range(len(current_all_device_list)):
                current_all_device_table.add_row([idx+1, current_all_device_list[idx]])
            print(current_all_device_table)
            
            print("\n###############")
            print("[Feedback system (ResourceManager->Masking Table)] masking device list")
            print("###############\n")
            masking_device_table = PrettyTable()
            masking_device_table.field_names = ["idx", f"{module_task} --> current masking device"]
            masking_device_table.align = "l" 
            for idx in range(len(masking_device_list)):
                masking_device_table.add_row([idx+1, masking_device_list[idx]])
            print(masking_device_table)

            mode_type = input(f"Do you want to add or delete masking device of {module_task}? ('a'/'d' or 'done'): ").strip().lower()
        
            if mode_type.lower() == 'done':
                break
            elif mode_type == 'a':
                device_index = int(input(f"Enter a index of masking device for {module_task}: ").strip())
                if device_index >= 1 and device_index <= len(current_all_device_list)+1:
                    masking_device_list.append(current_all_device_list[device_index-1])
                else:
                    print("IndexError --> Your input index:{}, please input 1 <= index <= {}".format(device_index, len(current_all_device_list)+1))
            elif mode_type == 'd':
                device_index = int(input(f"Enter a index of device to delete for {module_task}: ").strip())
                masking_device_list.pop(device_index-1)

        task_device_mask_dict[input_module_name][module_task]=masking_device_list

    print("\n###################")
    print(f"[Code generation (ResourceManager->{input_module_name})]: Code generation of {input_module_name} in ResourceManager, followed by GPT/Feedback system result")
    print("###################")
    
    script_content=f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [{input_module_name}] {input_module_name} resource allocator class file
# @author   {author}
# TEST {formatted_time}

import sys
from more_itertools import locate

class {input_module_name}:

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

    def get{input_module_name}Resource(self, module_name:str, jobID:int, total_recipe_template_list:list, task_device_location_dict:dict): 
    '''
    resource_key_list=list(module_resource_dict.keys())
    for resource_key in resource_key_list:
        script_content+=f'''
        popped_{resource_key}_index_list=[]'''
    script_content+='''
        while True: # while satisfy "if" condition'''
    for resource_key in resource_key_list:
        script_content+=f'''
            empty_{resource_key}_index_list=self.__find_indexes(task_device_location_dict[module_name]["{resource_key}"], "?")'''
    for idx, resource_key in enumerate(resource_key_list):
        if idx==0:
            script_content+=f'''
            if len(total_recipe_template_list) <= len(empty_{resource_key}_index_list)'''
        else:
            script_content+=f''' and len(total_recipe_template_list) <= len(empty_{resource_key}_index_list)'''
    script_content+=':'
    script_content+=f'''
                break'''
    script_content+='''
        for idx in range(len(total_recipe_template_list)):'''
    for resource_key in resource_key_list:
        script_content+=f'''
            popped_{resource_key}_index=empty_{resource_key}_index_list.pop(0) # pop first element in list
            task_device_location_dict[module_name]["{resource_key}"][popped_{resource_key}_index]=jobID
            popped_{resource_key}_index_list.append(popped_{resource_key}_index)
    '''
    script_content+='''
        task_location_dict={'''
    for resource_key in resource_key_list:
        script_content+=f'''
            "{resource_key}":popped_{resource_key}_index_list,'''
    script_content+='''}
        return task_location_dict, task_device_location_dict
    '''
    ###########################################
    # save device_location as json file
    ###########################################
    with open(f"Resource/device_location.json", 'w', encoding='utf-8') as file:
        json.dump(task_device_location_dict, file, indent=4)

    ###########################################
    # save device_status as json file
    ###########################################
    with open(f"Resource/device_status.json", 'w', encoding='utf-8') as file:
        json.dump(task_device_status_dict, file, indent=4)

    ###########################################
    # save device_masking_table as json file
    ###########################################
    with open(f"Resource/device_masking_table.json", 'w', encoding='utf-8') as file:
        json.dump(task_device_mask_dict, file, indent=4)

    ###########################################
    # save resource allocator for specific module as py file
    ###########################################

    if os.path.isdir(f"Resource/Module") == False:
        os.makedirs(f"Resource/Module")
    with open(f"Resource/Module/{input_module_name}.py", 'w') as file:
        file.write(script_content)