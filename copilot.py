import json
import ast
from prettytable import PrettyTable
from pydantic import BaseModel, constr, conint, conlist, ValidationError
from datetime import datetime
from AutoModuleGeneration.module_generation import ConfigValidation_DeviceServer, \
    save_to_files_modulenode, save_to_files_deviceserver, \
    script_generation_BaseUtils, script_generation_device_server, \
    script_generation_logging_class, script_generation_module_node, GPT_generate_module_deviceserver
from AutoModuleGeneration.module_registration import ConfigValidation_ModuleNode, \
    extract_code_task, extract_code_task_action_sequence, extract_code_task_pydantic, \
    extract_code_task_template, save_to_files_pydantic, save_to_files_task_template, script_add_routing_table, \
    script_generation_actiontranslator_class, script_generation_resourcemanager_class, json_add_template_module, \
    GPT_generate_task, GPT_generate_task_template, GPT_generate_task_pydantic, GPT_match_task_action_sequence, \
    feedback_task_list, feedback_task_template, feedback_task_action_sequence, feedback_device_standby_time_list
from AutoModuleGeneration.jobscript_generation import generate_jobscript_template

#########################
# please edit this part #
#########################``
api_key = "input_your_key"

module_node_config={
    "author":"Hyuk Jun Yoo (yoohj9475@kist.re.kr)",
    "module_name":"SolidStateModule",
    "module_type":"Synthesis", # ["Synthesis", "Preprocess", "Evaluation", "Characterization"]
    "module_description":"This module refers to a solid-state synthesis process via powder type.",
                                # More detailed information could improve the quality of GPT generation
    "device_type":["stirrer", "powder dispenser", "weighing machine", "heater"],
    "task_type":["AddPowder"], # must include this task
    "resource":{
        "vialHolder":["?"]*8,
        "heater":["?"]*8
    },
    "HOST":"192.168.1.13", # please implement your ip
    "PORT":54009, # Default = 54009, 54010 --> emergency stop PORT
    "gpt_on":True, # True --> using GPT // False --> using previous generated answer (txt file)
                    # in "AutoModuleGeneration/GPT_answer_generation" or "AutoModuleGeneration/GPT_answer_registration"
    "gpt_api_key":api_key, # your GPT api key
}
device_server_config_list=[
    {
        "server_name":"RobotArmDeviceServer",
        "device_type":["Robot arm", "Pipette"],
        "HOST":"192.168.1.13", # please implement your ip, "127.0.0.1" -> localhost
    },
    {
        "server_name":"PumpDeviceServer",
        "device_type":["Pump"],
        "HOST":"192.168.1.13", # please implement your ip, "127.0.0.1" -> localhost
    },
]

# module_node_config={
#     "author":"Hyuk Jun Yoo (yoohj9475@kist.re.kr)",
#     "module_name":"ElectroChemicalRDEModule",
#     "module_type":"Evaluation", # ["Synthesis", "Preprocess", "Evaluation", "Characterization"]
#     "module_description":"This module refers to a electrochemical evaluation process via rotating disk electrode.", 
#                             # More detailed information could improve the quality of GPT generation
#     "device_type":["Pipette", "RDE", "RDE rotator", "Sonication", "Humidifier", "Potentiostat", 
#                     "Cell", "IR ramp", "Milling machine", "Gas regulator"],
#     "task_type":[], # must include this task
#     "resource":{
#         "falcon":["?"]*8,
#         "falconHolder":["?"]*8,
#     },
#     "HOST":"192.168.3.11", # please implement your ip
#     "PORT":54009, # Default = 54009, 54010 --> emergency stop PORT
#     "gpt_on":True, # True --> using GPT // False --> using previous generated answer (txt file)
#                     # in "AutoModuleGeneration/GPT_answer_generation" or "AutoModuleGeneration/GPT_answer_registration"
#     "gpt_api_key":api_key, # your GPT api key
# }
# device_server_config_list=[
#     {
#         "server_name":"RobotArmDeviceServer",
#         "device_type":["Robot arm", "Linear actuator"],
#         "HOST":"192.168.3.11", # please implement your ip, "127.0.0.1" -> localhost
#     },
#     {
#         "server_name":"PumpDeviceServer",
#         "device_type":["Pump"],
#         "HOST":"192.168.3.11", # please implement your ip, "127.0.0.1" -> localhost
#     },
# ]
###########################################
# You only need to modify up to this line #
###########################################

###################
# add PORT number #
###################
for idx in range(len(device_server_config_list)):
    device_server_config_list[idx]["PORT"]=module_node_config["PORT"]+idx+1
###################
# record datetime #
###################
current_time = datetime.now()
formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

print("###################")
print(f"{module_node_config['module_name']} module generation started!")
print("###################")
#############################
# generation of config file #
#############################
try: # validation of config file
    _ = ConfigValidation_ModuleNode(**module_node_config)
except ValidationError as e:
    raise ValidationError(e)
for device_server_config in device_server_config_list:
    try: # validation of config file
        _ = ConfigValidation_DeviceServer(**device_server_config)
    except ValidationError as e:
        raise ValidationError(e)

###############################
# generation of device server #
###############################
modulenode_device_action_dict={}
for idx, device_server_config in enumerate(device_server_config_list):
    device_action_dict, answer = GPT_generate_module_deviceserver(formatted_time, module_node_config["author"], 
                                device_server_config["server_name"], device_server_config["device_type"], 
                                module_node_config["gpt_api_key"], module_node_config["gpt_on"])
    modulenode_device_action_dict.update(device_action_dict)
    # code_dict=extract_code_py(answer)
    device_class_name_list=list(answer.keys())
    # print(device_server_config['module_name'], device_class_name_list)
    device_server_config_list[idx]["converted_device_name_list"]=device_class_name_list
    save_to_files_deviceserver(module_node_config["module_name"], device_server_config["server_name"], answer)
    script_generation_logging_class(formatted_time=formatted_time, author=module_node_config["author"],
                                    input_module_name=module_node_config["module_name"],
                                    input_device_server_name=device_server_config["server_name"])
    script_generation_BaseUtils(formatted_time=formatted_time, author=module_node_config["author"],
                                input_module_name=module_node_config["module_name"],
                                input_device_server_name=device_server_config["server_name"])
    script_generation_device_server(formatted_time=formatted_time, author=module_node_config["author"],
                                    input_module_name=module_node_config["module_name"],
                                    input_device_server_name=device_server_config["server_name"], 
                                    device_list=device_class_name_list, 
                                    ip=device_server_config["HOST"], port=device_server_config["PORT"])

#############################
# generation of module node #
#############################
# with open(f'AutoModuleGeneration/GPT_answer_generation/GPT_{module_node_config["module_name"]}.txt', 'r', encoding='utf-8') as file:
#     answer_module = file.read()
device_action_dict, answer_module = GPT_generate_module_deviceserver(formatted_time, module_node_config["author"], 
                                module_node_config["module_name"], module_node_config["device_type"], 
                                module_node_config["gpt_api_key"], module_node_config["gpt_on"])
modulenode_device_action_dict.update(device_action_dict)
# code_dict_module=extract_code_py(answer_module)
device_class_name_list=list(answer_module.keys())
# print(module_node_config["module_name"], device_class_name_list)
save_to_files_modulenode(module_node_config["module_name"], answer_module)
script_generation_logging_class(formatted_time=formatted_time, author=module_node_config["author"],input_module_name=module_node_config["module_name"])
script_generation_BaseUtils(formatted_time=formatted_time, author=module_node_config["author"],input_module_name=module_node_config["module_name"])
script_generation_module_node(formatted_time=formatted_time, author=module_node_config["author"],
                            input_module_name=module_node_config["module_name"], device_list=list(answer_module.keys()), 
                            ip=module_node_config["HOST"], port=module_node_config["PORT"],
                            input_device_server_config_list=device_server_config_list)

print("###################")
print(f"{module_node_config['module_name']} module generation completed!")
print("###################")

print("###################")
print(f"{module_node_config['module_name']} module registration started!")
print("###################")

current_time = datetime.now()
formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

print("###################")
print(f"[{module_node_config['module_name']}]: get all action type of device from {module_node_config['module_name']}")
print("###################")

module_deviceaction_table = PrettyTable()
module_deviceaction_table.field_names = ["idx", "device name", f"{module_node_config['module_name']} action_type"]
module_deviceaction_table.align = "l" 
for i, device_name in enumerate(modulenode_device_action_dict.keys(), 1):
    module_deviceaction_table.add_row([i, device_name, modulenode_device_action_dict[device_name]])
print(module_deviceaction_table)

# --> {'STIRRER': ['Heat', 'Stir', 'Stop', 'heartbeat'], 'POWDERDISPENSER': ['Dispense', 'Stop', 'heartbeat'], 'WEIGHINGMACHINE': ['Stop', 'Tare', 'Weigh', 'heartbeat'], 'HEATER': ['Cool', 'Heat', 'Stop', 'heartbeat'], 'XRD': ['Align', 'Scan', 'Stop', 'heartbeat'], 'ROBOTARM': ['Grip', 'Move', 'Position', 'Release', 'Rotate', 'heartbeat'], 'PIPETTE': ['Aspirate', 'Calibrate', 'Dispense', 'Mix', 'Wash', 'heartbeat'], 'PUMP': ['Decrease', 'Increase', 'Reverse', 'Start', 'Stop', 'heartbeat']}
###########################
# generate task of module #
###########################
answer_task_list = GPT_generate_task(module_node_config["module_name"], module_node_config["module_description"], 
                                    module_node_config["task_type"], modulenode_device_action_dict, 
                                    module_node_config["gpt_api_key"], module_node_config["gpt_on"]) # Generate tasks via GPT
task_list=extract_code_task(answer_task_list) # extract task list
task_list=feedback_task_list(task_list)
########################################################
# match device actions in action sequence of each task #
########################################################
answer_action_sequence = GPT_match_task_action_sequence(module_node_config["module_name"], task_list, 
                                    modulenode_device_action_dict, module_node_config["gpt_api_key"], 
                                    module_node_config["gpt_on"]) # Generate tasks via GPT
task_action_sequence=extract_code_task_action_sequence(answer_action_sequence)
task_action_sequence=feedback_task_action_sequence(task_list, task_action_sequence, modulenode_device_action_dict)
#########################
# generate task template#
#########################
answer_task_template= GPT_generate_task_template(module_node_config["module_name"], task_list, 
                                        module_node_config["gpt_api_key"], module_node_config["gpt_on"])
task_template_str=extract_code_task_template(answer_task_template)
task_template=feedback_task_template(task_template_str)
save_to_files_task_template(module_node_config["module_name"], task_template)
##########################
# generate task Pydantic #
##########################
answer_task_pydantic=GPT_generate_task_pydantic(module_node_config["module_name"], task_list, task_template_str, 
                                                module_node_config["gpt_api_key"], module_node_config["gpt_on"])
task_pydantic_str=extract_code_task_pydantic(answer_task_pydantic)
save_to_files_pydantic(module_node_config["module_name"],task_pydantic_str)
# generate action translator for module
json_add_template_module(module_node_config["module_name"])
script_generation_actiontranslator_class(formatted_time=formatted_time, author=module_node_config["author"],
                                    input_module_name=module_node_config["module_name"], 
                                    module_type=module_node_config["module_type"],
                                    task_list=task_list, action_type_dict=modulenode_device_action_dict,
                                    task_deviceaction_dict=task_action_sequence)
######################################
# address IP/port in action executor #
######################################
script_add_routing_table(module_node_config["module_name"],module_node_config["HOST"],module_node_config["PORT"]) # add IP, PORT in routing table
#######################################
# address device standby time of task #
#######################################
feedback_device_standby_time_list(task_list)
########################################
# address resource in resource manager #
########################################
script_generation_resourcemanager_class(formatted_time=formatted_time, author=module_node_config["author"],
                                    input_module_name=module_node_config["module_name"], 
                                    module_resource_dict=module_node_config["resource"],
                                    action_type_dict=modulenode_device_action_dict,
                                    task_deviceaction_dict=task_action_sequence)
################################
# generate job script template #
################################
with open(f"Task/Template/{module_node_config['module_name']}.json", 'r', encoding="utf-8") as file:
    final_task_template = file.read()
final_task_template=ast.literal_eval(final_task_template)
generate_jobscript_template(module_node_config["module_type"], module_node_config["module_name"], final_task_template)

print("###################")
print(f"{module_node_config['module_name']} module registration completed!")
print("###################")
