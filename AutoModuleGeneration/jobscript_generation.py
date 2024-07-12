import json

def generate_jobscript_template(input_module_type:str, input_module_name:str, input_task_template:dict):
    task_key_list_dict={}
    sequence_list=[]
    fixedParams={}

    task_list=list(input_task_template.keys())
    for task_name in task_list:
        task_key_list=list(input_task_template[task_name]["Data"].keys())
        task_key_list.remove("Device")
        task_key_list_dict[task_name]=task_key_list
        # print(task_key_list_dict)
    # print(task_key_list_dict)
    for task_name, task_key_list in task_key_list_dict.items():
        if "Material" in task_key_list:
            task_name_material=task_name+"={Material}"
            sequence_list.append(task_name_material)
            if "Method" in task_key_list:
                task_key_list.remove("Method")
                task_key_list.remove("Material")
                fixedParams[task_name_material+"_Method"]=""
                for task_key in task_key_list:
                    if len(input_task_template[task_name]["Data"][task_key])==1:
                        fixedParams[task_name_material+"_"+task_key]=""
                    else:
                        fixedParams[task_name_material+"_"+task_key]=0
            else:
                task_key_list.remove("Material")
                for task_key in task_key_list:
                    if len(input_task_template[task_name]["Data"][task_key])==1:
                        fixedParams[task_name_material+"_"+task_key]=""
                    else:
                        fixedParams[task_name_material+"_"+task_key]=0
        else:
            sequence_list.append(task_name)
            if "Method" in task_key_list:
                task_key_list.remove("Method")
                fixedParams[task_name+"=Method"]=""
                for task_key in task_key_list:
                    if len(input_task_template[task_name]["Data"][task_key])==1:
                        fixedParams[task_name+"="+task_key]=""
                    else:
                        fixedParams[task_name+"="+task_key]=0
            else:
                for task_key in task_key_list:
                    if len(input_task_template[task_name]["Data"][task_key])==1:
                        fixedParams[task_name+"="+task_key]=""
                    else:
                        fixedParams[task_name+"="+task_key]=0

    job_script_template={
        "metadata" : 
        {
            "subject":"",
            "group":"",
            "logLevel":""
        },
        "algorithm":
        {
            "model":"",
            "totalExperimentNum":0,
            "inputParams":[]
        },
        "process":{
            input_module_type:{
                input_module_name:{
                    "Sequence":sequence_list,
                    "fixedParams":fixedParams
                }
            }
        }
    }
    # "Synthesis":{
    #     "SolidStateModule":{
    #         "Sequence":[
    #             "SolidStateModule_LoadSample",
    #             "SolidStateModule_AddPowder=IrCl3",
    #             "SolidStateModule_WeighPowder=IrCl3",
    #             "SolidStateModule_MixPowders",
    #             "SolidStateModule_PressPowder",
    #             "SolidStateModule_Sinter",
    #             "SolidStateModule_CoolDown",
    #             "SolidStateModule_UnloadSample"
    #         ],
    #         "fixedParams":
    #         {
    #             "SolidStateModule_LoadSample=SampleID":"test",
    #             "SolidStateModule_LoadSample=Container":"test",

    #             "SolidStateModule_AddPowder=IrCl3_Amount":1,
    #             "SolidStateModule_WeighPowder=IrCl3_TargetWeight":1,

    #             "SolidStateModule_MixPowders=Time":1,
    #             "SolidStateModule_MixPowders=Speed":1,
    #             "SolidStateModule_PressPowder=Pressure":1,
    #             "SolidStateModule_PressPowder=Duration":1,
    #             "SolidStateModule_Sinter=Temperature":1,
    #             "SolidStateModule_Sinter=Duration":1,
    #             "SolidStateModule_Sinter=Atmosphere":"test",
    #             "SolidStateModule_CoolDown=Rate":1,
    #             "SolidStateModule_UnloadSample=SampleID":"test"
    #         }
    #     }
    # },
    job_script_template_json=json.dumps(job_script_template, indent=4)
    with open(f"JobScriptTemplate/{input_module_name}.json", 'w') as file:
        file.write(job_script_template_json)
