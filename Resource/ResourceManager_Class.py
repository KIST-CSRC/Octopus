import time
import os, sys
import json, copy
import socket
# import numpy as np
import threading
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from more_itertools import locate
from TaskAction.ActionExecutor import ActionExecutor

class ResourceManager(ActionExecutor):
    """
    ResourceManager class check status of devices, and update device information from NodeManager
    
    # function
    """
    def __init__(self, module_list:list, serverLogger_obj:object):
        ActionExecutor.__init__(self,)
        self.serverLogger_obj=serverLogger_obj
        self.module_list=module_list
        self.component_name="ResourceManager"
        ################################
        # module로부터 매번 받도록 하기 #
        # 특정 job에서 module 실행한다고 하면, 아예 처음부터 지정해버리기
        ################################
        self.task_device_location_dict={
            "AMR":{ 
                "vialHolder":["?"]*1,
                "falconHolder":["?"]*1
            },
            "BatchSynthesis":{
                "Stirrer":["?"]*1,
                "vialHolder":["?"]*1
            },
            "UV":{ 
                "vialHolder":["?"]*8
            },
            "Preprocess":{ 
                "vial":["?"]*6,
                "falcon":["?"]*6,
                "vialHolder":["?"]*1,
                "falconHolder":["?"]*1,
                "Centrifuge":["?"]*6,
                "PreprocessSonic":["?"]*6
            },
            "RDE":{ 
                "falconHolder":["?"]*1,
                "falcon" : ["?"]*1
            }
        }
        ################################
        # module로부터 매번 받도록 하기 #
        ################################
        self.task_device_status_dict={
            "AMR_RoboticArm":False,
            "BatchSynthesis_RoboticArm":False,
            "BatchSynthesis_VialStorage":False,
            "BatchSynthesis_LinearAcutator":False,
            "BatchSynthesis_Pump":False,
            "UV_RoboticArm":False,
            "UV_Pipette":False,
            "UV_Spectroscopy":False,
            "Preprocess_RoboticArm":False,
            "Preprocess_Centrifuge":False,
            "Preprocess_Pump":False,
            "Preprocess_Sonic":False,
            "Preprocess_Piepette":False,
            "Preprocess_DispenserLA":False,
            "Preprocess_DeskLA":False,
            "Preprocess_Weighing":False,            
            "Washing_Centrifuge":False,
            
            "RDE_RoboticArm":False,
            "RDE_Module":False,
        }
        #########################################
        # module로부터 처음 연결할 때 받도록 하기 #
        #########################################
        # task_device_info_dict 받을 때 같이 
        #########################################
        # protect for collision between each devices
        self.task_device_mask_dict={
            "BatchSynthesis_PrepareContainer":["BatchSynthesis_RoboticArm","BatchSynthesis_VialStorage","BatchSynthesis_LinearAcutator","UV_RoboticArm"],
            "BatchSynthesis_AddSolution":["BatchSynthesis_LinearAcutator","BatchSynthesis_Pump"],
            "BatchSynthesis_React":["BatchSynthesis_RoboticArm","BatchSynthesis_LinearAcutator","UV_RoboticArm"],
            "UV_PrepareCuvette":["BatchSynthesis_RoboticArm", "UV_RoboticArm", "UV_Pipette"],
            "UV_GetAbs":["UV_RoboticArm", "UV_Pipette", "UV_Spectroscopy"],
            "UV_StoreCuvette":["BatchSynthesis_RoboticArm", "UV_RoboticArm", "UV_Pipette"],
            "AMR_MoveContainer":["BatchSynthesis_RoboticArm","BatchSynthesis_VialStorage","BatchSynthesis_LinearAcutator","UV_RoboticArm"],
            
            "Preprocess_TransferLiquid": ["Preprocess_RoboticArm","Preprocess_DeskLA","Preprocess_DispenserLA","Preprocess_Pump"],
            "Preprocess_Centrifugation": ["Preprocess_RoboticArm","Preprocess_Centrifuge"],
            "Preprocess_WashingAddSolution": ["Preprocess_RoboticArm","Preprocess_DeskLA","Preprocess_DispenserLA","Preprocess_Pump"],
            "Preprocess_Weighing": ["Preprocess_RoboticArm","Preprocess_Weighing"],
            "Preprocess_InkAddSolution": ["Preprocess_RoboticArm","Preprocess_Piepette"],
            "Preprocess_Washing_RemoveLiquid": ["Preprocess_RoboticArm","Preprocess_DeskLA","Preprocess_DispenserLA","Preprocess_Pump"],
            "Preprocess_Diffuse": ["Preprocess_RoboticArm","Preprocess_Sonic"],
            "Preprocess_Mix": ["Preprocess_RoboticArm","Preprocess_Sonic"],          
            
            "RDE_PrepareSample":["RDE_RoboticArm"],
            "RDE_SetupEvaluation": ["RDE_Module"],
            "RDE_Dropcasting": ["RDE_RoboticArm"],
            "RDE_PrepareElectrode": ["RDE_Module"],
            "RDE_StartEvaluation": ["RDE_Module"],
            "RDE_ReturnSample": ["RDE_RoboticArm"],
            "RDE_CleanUp": ["RDE_Module"],      
        }
        self.task_device_info_dict = self.requestHardwareInfo()

    ##################################################
    # callServer를 하나로 만들어서 paramater에서 받기  #
    ##################################################
    def requestHardwareInfo(self):
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
            for module_name in self.module_list:
                total_device_info_dict[module_name] = json.loads(self.transferDeviceCommand(module_name, "info/{}/None/all/virtual".format(module_name)))
                self.serverLogger_obj.info(self.component_name,"receive information of {}".format(module_name))
        except Exception as e:
            raise ConnectionError("Each module node cannot connect each device --> error message : {}".format(e))
        
        return total_device_info_dict
    
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
    
    ##################################################
    # callServer로 받아오는걸로 바꾸고, 해당 함수는 각 모듈로 옮기기  #
    ##################################################
    def allocateLocation(self, module_idx:int, module_type:str, jobID:int, total_recipe_template_list:list):
        """
        :param module_type: "BatchSynthesis", "FlowSynthesis", "UV" ... 
        :param jobID: allocate jobID in location_dict
        :param total_recipe_template_list: reflect recipe information in hardware location
        
        self.task_device_location_dict (dict)

        ex) self.task_device_location_dict={
                "Stirrer":["?","?","?","?","?","?","?","?"], # "?"==empty
                "vialHolder":["?","?","?","?","?","?","?","?"]
            }
        }
        """
        # allocate location information in self.location_dict depending on temperature 
        if module_type == "BatchSynthesis":

            Stirrer_set_temperature_list=[]
            for stirrer_value in list(self.task_device_info_dict[module_type]["Stirrer"].values()): # upload tempearture setting of stirrer
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
                    if task_dict["Task"]=="BatchSynthesis_Heat": # we split depending on temperature (differenet temperature --> different stirrer)
                        temperature_in_recipe_list.append(task_dict["Data"]["Temperature"]["Value"])
                    # if task_dict["Task"]!="Stir": # if we control stir, activate this
                    #     stirrate_list.append(task_dict["Data"]["StirRate"]["Value"])
                    else: # exclude AddSolution, Wait, React, Pipette...
                        pass
            if 50 in temperature_in_recipe_list: # mix some temperature include 50
                empty_stirrer_0_hole_index=[]
                # empty_stirrer_1_hole_index=[]
                empty_vialHolder_index=[]
                while True: # while satisfy "if" condition
                    empty_stirrer_0_hole_index=self.__find_indexes(self.task_device_location_dict[module_type]["Stirrer"][:8], "?") # "?" == empty, calculate "?" or not
                    # empty_stirrer_1_hole_index=self.__find_indexes(self.task_device_location_dict[module_type]["Stirrer"][8:], "?") # "?" == empty, calculate "?" or not
                    empty_vialHolder_index=self.__find_indexes(self.task_device_location_dict[module_type]["vialHolder"],"?") # "?" == empty
                    # match recipe information with spare location of stirrer
                    if temperature_in_recipe_list.count(50) <= len(empty_stirrer_0_hole_index) and \
                        len(temperature_in_recipe_list) <= len(empty_vialHolder_index):
                        break
                popped_stirrer_hole_index_list=[]
                popped_vialHolder_index_list=[]
                for idx, temperature in enumerate(temperature_in_recipe_list):
                    if temperature == 50:
                        popped_stirrer_hole_index=empty_stirrer_0_hole_index.pop(0) # pop first element in list
                        self.task_device_location_dict[module_type]["Stirrer"][popped_stirrer_hole_index]=jobID
                        popped_stirrer_hole_index_list.append(popped_stirrer_hole_index)
                    # elif temperature == 50:
                    #     popped_stirrer_hole_index=empty_stirrer_1_hole_index.pop(0) # pop first element in list
                    #     self.task_device_location_dict[module_type]["Stirrer"][popped_stirrer_hole_index]=jobID
                    #     popped_stirrer_hole_index_list.append(popped_stirrer_hole_index) 
                    popped_vialHolder_index=empty_vialHolder_index.pop(0) # pop first element in list
                    self.task_device_location_dict[module_type]["vialHolder"][popped_vialHolder_index]=jobID
                    popped_vialHolder_index_list.append(popped_vialHolder_index)
            
            else: # all temperature set 25 (RT)
                empty_stirrer_hole_index=[]
                empty_vialHolder_index=[]
                while True: # while satisfy "if" condition
                    empty_vialHolder_index=self.__find_indexes(self.task_device_location_dict[module_type]["vialHolder"],jobID) # "?" == empty
                    empty_stirrer_hole_index=self.__find_indexes(self.task_device_location_dict[module_type]["Stirrer"], "?") # "?" == empty
                    if temperature_in_recipe_list.count(25) <= len(empty_stirrer_hole_index) and len(temperature_in_recipe_list) <= len(empty_vialHolder_index):
                        break
                # print(empty_stirrer_hole_index)
                # print(empty_vialHolder_index)
                popped_stirrer_hole_index_list=[]
                popped_vialHolder_index_list=[]
                for idx in range(len(temperature_in_recipe_list)):

                    popped_stirrer_hole_index=empty_stirrer_hole_index.pop(0) # pop first element in list
                    self.task_device_location_dict[module_type]["Stirrer"][popped_stirrer_hole_index]=jobID
                    popped_stirrer_hole_index_list.append(popped_stirrer_hole_index)

                    popped_vialHolder_index=empty_vialHolder_index.pop(0) # pop first element in list
                    self.task_device_location_dict[module_type]["vialHolder"][popped_vialHolder_index]=jobID
                    popped_vialHolder_index_list.append(popped_vialHolder_index)
            
            task_location_dict={
                "Stirrer":popped_stirrer_hole_index_list,
                "vialHolder":popped_vialHolder_index_list
            }

        elif module_type=="UV": # 
            popped_vialHolder_index_list=[]
            while True: # while satisfy "if" condition
                empty_vialHolder_index_list=self.__find_indexes(self.task_device_location_dict[module_type]["vialHolder"], "?")
                if len(total_recipe_template_list) <= len(empty_vialHolder_index_list):
                    break
            for idx in range(len(total_recipe_template_list)):
                popped_vialHolder_index=empty_vialHolder_index_list.pop(0) # pop first element in list
                self.task_device_location_dict[module_type]["vialHolder"][popped_vialHolder_index]=jobID
                popped_vialHolder_index_list.append(popped_vialHolder_index)
            task_location_dict={
                "vialHolder":popped_vialHolder_index_list
            }

        elif module_type=="Preprocess": # 
            empty_Centrifuge_index = []
            empty_falcon_index = []
            empty_falconHolder_index= []
            empty_vialHolder_index= []
            empty_PreprocessSonic_index = []

            while True: 
                empty_Centrifuge_index = self.__find_indexes(self.task_device_location_dict[module_type]["Centrifuge"], "?")
                empty_falcon_index = self.__find_indexes(self.task_device_location_dict[module_type]["falcon"], "?")
                empty_falconHolder_index = self.__find_indexes(self.task_device_location_dict[module_type]["falconHolder"], jobID)
                print("empty_falconHolder_index",empty_falconHolder_index)
                empty_vialHolder_index = self.__find_indexes(self.task_device_location_dict[module_type]["vialHolder"], jobID)
                empty_PreprocessSonic_index = self.__find_indexes(self.task_device_location_dict[module_type]["PreprocessSonic"], "?")
                
                if len(total_recipe_template_list) <= len(empty_Centrifuge_index) <= len(empty_falcon_index):
                    break

            popped_Centrifuge_index_list = []
            popped_falcon_index_list = []
            popped_falconHolder_index_list = []
            popped_vialHolder_index_list = []
            popped_PreprocessSonic_index_list = []

            for idx in range(len(total_recipe_template_list)):
                popped_Centrifuge_index = empty_Centrifuge_index.pop(0)
                self.task_device_location_dict[module_type]["Centrifuge"][popped_Centrifuge_index] = jobID
                popped_Centrifuge_index_list.append(popped_Centrifuge_index)

                popped_falcon_index = empty_falcon_index.pop(0)
                self.task_device_location_dict[module_type]["falcon"][popped_falcon_index] = jobID
                popped_falcon_index_list.append(popped_falcon_index)
                
                popped_PreprocessSonic_index = empty_PreprocessSonic_index.pop(0)
                self.task_device_location_dict[module_type]["PreprocessSonic"][popped_PreprocessSonic_index] = jobID
                popped_PreprocessSonic_index_list.append(popped_PreprocessSonic_index)                

            task_location_dict = {
                "Centrifuge": popped_Centrifuge_index_list,
                "falcon": popped_falcon_index_list,
                "falconHolder": self.task_device_location_dict[module_type]["falconHolder"],
                "vialHolder": popped_vialHolder_index_list,
                "PreprocessSonic": popped_PreprocessSonic_index_list
            }
            return task_location_dict
                    
        elif module_type=="AMR": # 
            total_task_list=[]
            for key, values in total_recipe_template_list[0].items(): 
                # key -> Synthesis, Preprocess, Evaluation, Characterization
                # values -> {"Module":[...]},{"Module":[...]},...
                for value in values:
                    task_dict_list=[]
                    if "Module" in value:
                        for task_dict in value["Data"]:
                            task_dict_list.append(task_dict)
                    total_task_list.append(task_dict_list)
            
            amr_task_dict=total_task_list[module_idx][0]["Data"]
            PLACE_A=amr_task_dict["From"]
            PLACE_B=amr_task_dict["To"]
            print("PLACE_A, PLACE_B", PLACE_A, PLACE_B)
            CONTAINER_NAME=amr_task_dict["Container"]
            AMR_HOLDER_NAME=amr_task_dict["Container"]+"Holder"
            popped_AMR_holder_index_list=[]
            popped_PLACE_A_index_list=[]
            popped_PLACE_B_index_list=[]
            empty_AMR_index_list=[]
            empty_PLACE_A_index_list=[]
            empty_PLACE_B_index_list=[]
            if PLACE_A  == "Storage" or PLACE_B == "Storage":
                if PLACE_A  == "Storage":
                    while True: # while satisfy "if" condition
                        empty_AMR_index_list=self.__find_indexes(self.task_device_location_dict["AMR"][AMR_HOLDER_NAME], "?")
                        empty_PLACE_B_index_list=self.__find_indexes(self.task_device_location_dict[PLACE_B][AMR_HOLDER_NAME], "?")
                        if len(total_recipe_template_list) <= len(empty_AMR_index_list) and len(total_recipe_template_list) <= len(empty_PLACE_B_index_list) :
                            break
                    for idx in range(len(total_recipe_template_list)):
                        popped_AMR_holder_index=empty_AMR_index_list.pop(0) # pop first element in list
                        popped_PLACE_B_index=empty_PLACE_B_index_list.pop(0) # pop first element in list
                        self.task_device_location_dict["AMR"][AMR_HOLDER_NAME][popped_AMR_holder_index]=jobID
                        self.task_device_location_dict[PLACE_B][AMR_HOLDER_NAME][popped_PLACE_B_index]=jobID # reset
                        popped_AMR_holder_index_list.append(popped_AMR_holder_index)
                        popped_PLACE_B_index_list.append(popped_PLACE_B_index)
                    task_location_dict={
                        module_type:{CONTAINER_NAME:popped_AMR_holder_index_list},
                        PLACE_B:{CONTAINER_NAME:popped_PLACE_B_index_list}
                    }
                elif PLACE_B == "Storage":
                    while True: # while satisfy "if" condition
                        empty_AMR_index_list=self.__find_indexes(self.task_device_location_dict["AMR"][AMR_HOLDER_NAME], "?")
                        empty_PLACE_A_index_list=self.__find_indexes(self.task_device_location_dict[PLACE_A][AMR_HOLDER_NAME], jobID)
                        if len(total_recipe_template_list) <= len(empty_AMR_index_list) and len(total_recipe_template_list) <= len(empty_PLACE_A_index_list) :
                            break
                    for idx in range(len(total_recipe_template_list)):
                        popped_AMR_holder_index=empty_AMR_index_list.pop(0) # pop first element in list
                        popped_PLACE_A_index=empty_PLACE_A_index_list.pop(0) # pop first element in list
                        self.task_device_location_dict["AMR"][AMR_HOLDER_NAME][popped_AMR_holder_index]=jobID
                        self.task_device_location_dict[PLACE_A][AMR_HOLDER_NAME][popped_PLACE_A_index]=jobID # reset
                        popped_AMR_holder_index_list.append(popped_AMR_holder_index)
                        empty_PLACE_A_index_list.append(popped_PLACE_A_index)
                    task_location_dict={
                        module_type:{CONTAINER_NAME:popped_AMR_holder_index_list},
                        PLACE_A:{CONTAINER_NAME:empty_PLACE_A_index_list}
                    }
            else:
                while True: # while satisfy "if" condition
                    empty_PLACE_A_index_list=self.__find_indexes(self.task_device_location_dict[PLACE_A][AMR_HOLDER_NAME], jobID)
                    empty_AMR_index_list=self.__find_indexes(self.task_device_location_dict["AMR"][AMR_HOLDER_NAME], "?")
                    empty_PLACE_B_index_list=self.__find_indexes(self.task_device_location_dict[PLACE_B][AMR_HOLDER_NAME], "?")
                    if len(total_recipe_template_list) <= len(empty_PLACE_A_index_list) and len(total_recipe_template_list) <= len(empty_PLACE_B_index_list):
                        break
                for idx in range(len(total_recipe_template_list)):
                    popped_PLACE_A_index=empty_PLACE_A_index_list.pop(0) # pop first element in list
                    popped_AMR_holder_index=empty_AMR_index_list.pop(0) # pop first element in list
                    popped_PLACE_B_index=empty_PLACE_B_index_list.pop(0) # pop first element in list
                    self.task_device_location_dict[PLACE_A][AMR_HOLDER_NAME][popped_PLACE_A_index]="?" # reset
                    self.task_device_location_dict["AMR"][AMR_HOLDER_NAME][popped_AMR_holder_index]=jobID
                    self.task_device_location_dict[PLACE_B][AMR_HOLDER_NAME][popped_PLACE_B_index]=jobID
                    popped_AMR_holder_index_list.append(popped_AMR_holder_index)
                    popped_PLACE_A_index_list.append(popped_PLACE_A_index)
                    popped_PLACE_B_index_list.append(popped_PLACE_B_index)
                task_location_dict={
                    module_type:{CONTAINER_NAME:popped_AMR_holder_index_list},
                    PLACE_A:{CONTAINER_NAME:popped_PLACE_A_index_list},
                    PLACE_B:{CONTAINER_NAME:popped_PLACE_B_index_list}
                }

        elif module_type=="RDE": # 
            popped_falcon_index_list=[]
            popped_falconHolder_index_list=[]

            while True: # while satisfy "if" condition
                empty_falcon_index_list=self.__find_indexes(self.task_device_location_dict[module_type]["falcon"], "?")
                empty_falconHolder_index_list=self.__find_indexes(self.task_device_location_dict[module_type]["falconHolder"], jobID)
                if len(total_recipe_template_list) <= len(empty_falcon_index_list) and len(total_recipe_template_list) <= len(empty_falconHolder_index_list):
                    break
            for idx in range(len(total_recipe_template_list)):
                popped_falcon_index=empty_falcon_index_list.pop(0) # pop first element in list
                popped_falconHolder_index=empty_falconHolder_index_list.pop(0) # pop first element in list

                self.task_device_location_dict[module_type]["falcon"][popped_falcon_index]=jobID
                self.task_device_location_dict[module_type]["falconHolder"][popped_falcon_index]=jobID
                popped_falcon_index_list.append(popped_falcon_index)
                popped_falconHolder_index_list.append(popped_falconHolder_index)
                
            task_location_dict={
                "falcon":popped_falcon_index_list,
                "falconHolder":popped_falconHolder_index_list,
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
        # module_seq_list[0]을 보는 이유 : 뒤에 있는 공정들은 어차피 나중에 할거니깐. 
        # 지금 당장 시작해야하는 공정이 비어있으면 일단 실행.
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
    # callServer를 하나로 만들어서 paramater에서 받기  #
    ##################################################
    def refreshDeviceLocation(self, module_type:str, device_type:str, jobID:int):
        """
        :param module_type (str): reflect process information of hardware location in module (BatchSynthesis, UV)
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
        :param module_type (str): reflect process information of hardware location in module (BatchSynthesis, UV)
        :param jobID (int) : return job id

        :return self.task_device_location_dict[module_type] (dict)
        """
        for device_type, device_values in self.task_device_location_dict[module_type].items():
            location_index_list=self.__find_indexes(device_values, jobID)
            for location_index in location_index_list:
                self.task_device_location_dict[module_type][device_type][location_index]="?"
        return self.task_device_location_dict[module_type]

    ##################################################
    # callServer를 하나로 만들어서 paramater에서 받기  #
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
            "BatchSynthesis_RoboticArm":False,
            "BatchSynthesis_VialStorage":False,
            "BatchSynthesis_LinearAcutator":True,
            "BatchSynthesis_Pump":False,
            "UV_RoboticArm":False,
            "UV_Pipette":False,
            "UV_Spectroscopy":False
        }
        self.task_device_mask_dict={
            "PrepareContainer":["BatchSynthesis_RoboticArm","BatchSynthesis_VialStorage","BatchSynthesis_LinearAcutator","UV_RoboticArm"],
            "AddSolution":["BatchSynthesis_RoboticArm","BatchSynthesis_LinearAcutator","BatchSynthesis_Pump"],
            "React":["BatchSynthesis_RoboticArm","BatchSynthesis_LinearAcutator","UV_RoboticArm"],
            "GetAbs":["BatchSynthesis_RoboticArm", "UV_RoboticArm", "UV_Pipette", "UV_Spectroscopy"],
            "MoveContainer":["BatchSynthesis_RoboticArm","BatchSynthesis_VialStorage","BatchSynthesis_LinearAcutator","UV_RoboticArm"],
        }
        """
        # self.serverLogger_obj.debug(self.component_name,"start to update status")
        time.sleep(1)
        device_criterion_list=self.task_device_mask_dict[task_name]
        
        # thread function
        def update_status_each(input_device_name, input_status):
            self.task_device_status_dict[input_device_name]=input_status # UV_RoboticArm is okay. (not disturb in AddSolution task)
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
            device_criterion_list=self.task_device_mask_dict[task_name]
            # thread function
            def countCriterion(device_name):
                criterion_count_list.append(self.task_device_status_dict[device_name])
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