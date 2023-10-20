# User Manual
## Installation
### 1. Using conda
```
conda env create -f requirements_conda.txt
```

### 2. Using pip
```
pip install -r requirements_pip.txt
```

## Prerequisites
### 1. Modularization of experimental process
1. You should modularize by grouping by experimental process. You can see some code samples in [BatchSynthesisModule](https://github.com/KIST-CSRC/BatchSynthesisModule) and [UV-VisModule](https://github.com/KIST-CSRC/UV-VisModule)
2. Set your module internal network IP address and port number in wireless router. Ex. "192.168.XXX.YYY"

### 2. [Task/TCP.py](Task/TCP.py)
1. You need to insert IP address and port number in `self.routing_table`.
```python
class ParameterTCP:
    def __init__(self):
        self.routing_table={
            "BATCH":{
                "HOST":"192.168.{XXX}.{YYY}",  # Please write IP address of module 
                "PORT":{port_num}, # Please write port of module
                "NAME":"kist", # Windows name
                "PWD":"selfdriving!" # Windows pwd
            }
        }
```
2. You need to define `callserver_{module_name}` in `TCP_Class`.
```python
class TCP_Class(ParameterTCP):
    ...
    def callServer_{module_name}(self, command_str="info/{module_name}/None/all/virtual"):
        command_bytes=str.encode(command_str)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.routing_table["{module_name}"]["HOST"], self.routing_table["{module_name}"]["PORT"]))
            time.sleep(1)
            s.sendall(command_bytes)
            message_recv = b''
            while True:
                part = s.recv(self.BUFF_SIZE)
                if "finish" in part.decode("utf-8") or "success" in part.decode("utf-8"):
                    s.close()
                    break
                elif "finish" not in part.decode("utf-8") or "success" not in part.decode("utf-8"):
                    message_recv += part
                else:
                    raise ConnectionError("Wrong tcp message")
            return message_recv.decode("utf-8")
```
### 3. [Task/TaskGenerator_Class.py](Task/TaskGenerator_Class.py)
1. Define module template.
```python
class Template:
    def __init__(self,):
        """
        Process (Middle part: Module)
        """
        self.BatchSynthesis_template={
            "Module":"BatchSynthesis",
            "Data":[]  
        },
        self.Washing_template={
            "Module":"Washing",
            "Data":[]  
        }
```
2. Define task template of module. It depends on module
```python
        """
        Process (bottom part: Task)
        """
        # BatchSynthesis
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
        # Washing
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
```
3. Define task template of evaluation or characterization module. This template need to register more details of experimental devices due to reliability of extracted material data. The contents of `"Device"` will be filled by resource manager. And, the contents of `"Hyperparameter"` value will be filled by job script. You just write only `"Hyperparameter"` in template before.
```python
        # UV-VIS
        self.GetAbs_template={
            "Task":"GetAbs",
            "Data":{
                "Device":{},
                "Hyperparameter":{
                    "WavelengthMin":{
                        "Description":"WavelengthMin (int): slice start point of wavlength",
                        "Value": 0,
                        "Dimension": "nm"
                    },
                    "WavelengthMax":{
                        "Description":"WavelengthMax (int): slice final point of wavlength",
                        "Value": 0,
                        "Dimension": "nm"
                    },
                    "BoxCarSize":{
                        "Description":"BoxCarSize (int): smooth strength",
                        "Value": 0,
                        "Dimension": "None"
                    },
                    "Prominence":{
                        "Description":"Prominence (float): minimum peak intensity",
                        "Value": 0,
                        "Dimension":"None"
                    },
                    "PeakWidth":{
                        "Description":"PeakWidth (int): minumum peak width",
                        "Value": 0,
                        "Dimension": "nm"
                    }
                }
            },
        }
```
4. Register task type in `__allocateTaskSequence` function.
```python
class TaskGenerator(Template,TCP_Class):
    ...
    def __allocateTaskSequence(self, task_type:str, integrated_parameter_dict:dict):
        if "AddSolution" in task_type:
            empty_template=copy.deepcopy(self.AddSolution_template)
        ...
        elif "Centrifugation" in task_type:
            empty_template=copy.deepcopy(self.MoveContainer_template) 
            # uploaded by job script file
            empty_template["Data"]["Power"]["Value"]=integrated_parameter_dict["Centrifugation=RPM"]
            empty_template["Data"]["Time"]["Value"]=integrated_parameter_dict["Centrifugation=Time"] 
            # uploaded by hardware Device from resource manager
            empty_template["Data"]["Device"]=self.task_hardware_info_dict["Washing"]["Centrifuge"] 
```
### 4. [Task/TaskScheduler_Class.py](Task/TaskScheduler_Class.py)
1. Define module class in TaskScheduler_Class.py. 
- set module name
- inherit TCP_Class
- define consumable chemical vessels, such as vial, cuvette, tip, falcon tube, etc.
```python
class RobotMovPlatform(TCP_Class):
    def __init__(self, platform_name="{module_name}", ResourceManager_obj={}):
        TCP_Class.__init__(self,)
        self.batch_module_name= "{}".format(module_name)
        self.vial_bottom_queue = Queue()
        self.the_number_of_vial = 80
        self.__initVialBottom()
        self.ResourceManager_obj=ResourceManager_obj
```
2. Define function of consumable chemical vessels, such as vial, cuvette, tip, falcon tube, etc.
```python
    def __initVialBottom(self):
        """
        initialize vial number depending on Queue.

        :return: None: 
        """
        for num in range(self.the_number_of_vial):
            self.vial_bottom_queue.put(num)  

    def __popVialBottom(self):
        """
        pop vial number depending on Queue.

        :return: vial_num (int): get vial number in vial_bottom_queue
        """
        empty_true = self.vial_bottom_queue.empty()
        if empty_true==True:
            self.__initVialBottom()
        vial_num=self.vial_bottom_queue.get()

        return vial_num
```
3. Define alert function with digitalsecretary for sending message to administrators directly.
```python
    def __alertVialNum(self, TaskLogger_obj, mode_type="virtual"):
        text_content="[{}] vial number ({}) is not enough, please fill vial".format(self.robot_module_name, self.vial_bottom_queue.qsize())
        if self.vial_bottom_queue.qsize() <=10:
            AlertMessage(text_content=text_content, key_path="./Log", message_module_list=["dooray"], mode_type=mode_type)
        else:
            pass

```
4. Define task function to digitalize abstracted task
```python
    def AddSolution(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        
        # execution for each task depending on batch size of cycle
        for vial_task_idx, pump_dict in enumerate(task_info_list): # for each vial
            # check & update status of device, report delay time in result
            taskStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time=self.ResourceManager_obj.checkStatus(current_func_name) # wait until not busy
            taskFinishTime=time.strftime("%Y-%m-%d %H:%M:%S")
            delay_time_str="{}~{}".format(taskStartTime, taskFinishTime)
            TaskLogger_obj.addDelayTime(delay_time)
            TaskLogger_obj.appendDelayTime(delay_time_str, delay_time)
            self.ResourceManager_obj.updateStatus(current_func_name, True)

            # update status of device every batch
            TaskLogger_obj.current_module_name="{}-->{}".format(self.batch_module_name, "AddSolution")
            TaskLogger_obj.status="{}_{}/{}:{}".format(len(task_info_list), vial_task_idx, TaskLogger_obj.totalExperimentNum, TaskLogger_obj.current_module_name) # in execution system

            # execute real action to module using packeformatter and TCP_Class object
            command_str=self.packetFormatter(jobID,"LA","down",location_dict["Stirrer"][vial_task_idx],mode_type)
            TaskLogger_obj.debug("LA", "move down-->Start!")
            res_msg=self.callServer_BATCH(command_str=command_str)
            TaskLogger_obj.debug("LA", "move down-->Done!")
            ...
```
5. If you want to develop novel algorithm of task scheduling methods, then please define in `TaskScheduler.scheduleAllTask` function.
```python
class TaskScheduler(RobotMovModule, BatchSynthesisModule, UVModule):
    def scheduleAllTask(self, total_recipe_template_list:list, jobID:int, TaskLogger_obj:object, mode_type:str):
        if self.schedule_mode == "FCFS" or self.schedule_mode == "BackFill":
            ...
        elif self.schedule_mode=="ClosedPacking":
            ...
```
### 5. [Resource.ResourceManager_Class.py](Resource.ResourceManager_Class.py)
1. Define device status table in `self.task_hardware_status_dict`
```python
class ResourceManager(TCP_Class):
    """
    ResourceManager class check status of devices, and update device information from NodeManager
    
    # function
    """
    def __init__(self, serverLogger_obj:object):
        TCP_Class.__init__(self,)
        self.task_hardware_status_dict={
            "Batch_RoboticArm":False,
            "Batch_VialStorage":False,
            "Batch_LinearAcutator":False,
            "Batch_Pump":False,
            "UV_RoboticArm":False,
            "UV_Pipette":False,
            "UV_Spectroscopy":False
        }
```
2. Define module resource information in `self.task_hardware_location_dict`
```python
        self.task_hardware_location_dict={
                "BatchSynthesis":{ 
                    "Stirrer":["?"]*8,
                    "vialHolder":["?"]*8
                },
                "UV":{ 
                    "vialHolder":["?"]*8
                }
            }
```
3. Define masking table in `self.task_hardware_mask_dict`. According to sharing devices between modules, the device names are prefixed with the module name to differentiate and allow for device intersections in the table.
```python
        # protect for collision between each devices
        self.task_hardware_mask_dict={
            "PrepareContainer":["Batch_RoboticArm","Batch_VialStorage","Batch_LinearAcutator","UV_RoboticArm"],
            "AddSolution":["Batch_LinearAcutator","Batch_Pump"],
            "React":["Batch_RoboticArm","Batch_LinearAcutator","UV_RoboticArm"],
            "PrepareCuvette":["Batch_RoboticArm", "UV_RoboticArm", "UV_Pipette"],
            "GetAbs":["UV_RoboticArm", "UV_Pipette", "UV_Spectroscopy"],
            "StoreCuvette":["Batch_RoboticArm", "UV_RoboticArm", "UV_Pipette"],
            "MoveContainer":["Batch_RoboticArm","Batch_VialStorage","Batch_LinearAcutator","UV_RoboticArm"],
        }
```
4. Customize `allocationLocation` function depending on module settings. This function decide to allocate device location information to task schduler. Please refer [Resource.ResourceManager_Class.py](Resource.ResourceManager_Class.py)
```python
    def allocateLocation(self, module_type:str, jobID:int, total_recipe_template_list:list):
        if module_type == "BatchSynthesis":
            ...
        elif module_type == "Washing":
            ...
```
5. Customize `notifyNumbersOfTasks` function. This function notify to remaining device location information to task schduler. Please refer [Resource.ResourceManager_Class.py](Resource.ResourceManager_Class.py)
```python
    def notifyNumbersOfTasks(self, total_recipe_template_list:list):
        if "BatchSynthesis"==module_seq_list[0]:
            ...
        elif "Washing"==module_seq_list[0]:
            ...
```
### 6. [Log](Log)
Customize messenger information in [Log/Information.json](Log/Information.json). Please refer API for each SNS.
### 7. [USER](USER)
Directory Structure
```
USER
├── job_script: job script of client
├── DB (automatic generation during progress): material data. It also store in MongoDB
├── Log (automatic generation during progress): log file of all job progress 
└── SaveModel (automatic generation during progress): model object based on sklearn. In future, we will upgrade until pytorch or tensorflow
```
Client should customize [Job script](USER\HJ\job_script).

1. metadata
```json
    "metadata" : 
        {
            "subject":"jobID_0_AI",
            "group":"KIST_CSRC",
            "logLevel":"DEBUG"
        }
```
2. algorithm
It depends on model selection, "Automatic" or AI based models, such as "BayesianOptimization"
- "Automatic"
```json
    "algorithm":
    {
        "model":"Automatic",
        "totalExperimentNum":4,
        "inputParams":[
            {
                "AddSolution=AgNO3_Concentration" : 1250,
                "AddSolution=AgNO3_Volume" : 2000,
                "AddSolution=AgNO3_Injectionrate" : 200
            },
            {
                "AddSolution=AgNO3_Concentration" : 1250,
                "AddSolution=AgNO3_Volume" : 2000,
                "AddSolution=AgNO3_Injectionrate" : 200
            },
            {
                "AddSolution=AgNO3_Concentration" : 1250,
                "AddSolution=AgNO3_Volume" : 2000,
                "AddSolution=AgNO3_Injectionrate" : 200
            },
            {
                "AddSolution=AgNO3_Concentration" : 1250,
                "AddSolution=AgNO3_Volume" : 2000,
                "AddSolution=AgNO3_Injectionrate" : 200
            }
        ]
    }
```
- "BayesianOptimization"
```json
    "algorithm":
        {
            "model":"BayesianOptimization",
            "batchSize":6,
            "totalCycleNum":3,
            "verbose":0,
            "randomState":0,
            "sampling":{
                "samplingMethod":"latin",
                "samplingNum":20
            },
            "acq":{
                "acqMethod":"ucb",
                "acqSampler":"greedy",
                "acqHyperparameter":{
                    "kappa":10.0
                }
            },
            "loss":{
                "lossMethod":"lambdamaxFWHMintensityLoss",
                "lossTarget":{
                    "GetAbs":{
                        "Property":{
                            "lambdamax":573
                        },
                        "Ratio":{
                            "lambdamax":0.9,
                            "FWHM":0.03, 
                            "intensity":0.07
                        }
                    }
                }
            }, 
            "prange":{
                "AddSolution=AgNO3_Concentration" : [25, 375, 25],
                "AddSolution=AgNO3_Volume" : [100, 1200, 50],
                "AddSolution=AgNO3_Injectionrate" : [50, 200, 50]
            },
            "initParameterList":[],
            "constraints":[]
        }
```
3. process
```json
    "process":
    {
        "Synthesis":{
            "BatchSynthesis":{
                "fixedParams":
                {
                    "BatchSynthesis=Sequence":["AddSolution_Citrate","AddSolution_H2O2", "AddSolution_NaBH4","Stir","Heat","Mix", "AddSolution_AgNO3", "React"],

                    "AddSolution=H2O2_Concentration" : 375,
                    "AddSolution=H2O2_Volume" : 1200,
                    "AddSolution=H2O2_Injectionrate" : 200,
                    "AddSolution=Citrate_Concentration" : 20,
                    "AddSolution=Citrate_Volume" : 1200,
                    "AddSolution=Citrate_Injectionrate" : 200,
                    "AddSolution=NaBH4_Concentration" : 10,
                    "AddSolution=NaBH4_Volume" : 3000,
                    "AddSolution=NaBH4_Injectionrate" : 200,

                    "Stir=StirRate":1000,
                    "Heat=Temperature":25,
                    "Mix=Time":300,
                    "React=Time":2400
                }
            },
            "FlowSynthesis":{}
        },
        "Preprocess":{
            "Washing":{},
            "Ink":{}
        },
        "Characterization":{
            "UV":{}
        },
        "Evaluation":{
            "RDE":{},
            "Electrode":{}
        }
    }
```