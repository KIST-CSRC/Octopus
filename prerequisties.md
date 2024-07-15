# User Manual
## Environment setting
```
pip install -r requirements.txt
```

## Copilot of OCTOPUS
Please refer this [Supplementary Guidelines for OCTOPUS]().

You should modularize by grouping by experimental process. You can see some code samples in [BatchSynthesisModule](https://github.com/KIST-CSRC/BatchSynthesisModule) and [UV-VisModule](https://github.com/KIST-CSRC/UV-VisModule)

## (Optional) Example of code modification

### 1. Additional function for consumable chemical vessel storage in [Action/Module/{ModuleName}.py](Action/Module)
If you want to utilize the `location index` of consumable chemical vessels storage (e.g. vial, cuvette, tip, falcon tube, etc) in `ActionTranslator`, define function to return location index of consumable chemical vessel storage. (Don't confused resource and consumable chemical vessels)
```python
class BatchSynthesisModule(ActionExecutor):
    def __init__(self,module_name="BatchSynthesisModule", ResourceManager_obj=object):
        ActionExecutor.__init__(self,)
        self.__BatchSynthesisModule_name= module_name
        self.ResourceManager_obj=ResourceManager_obj

        ###################################################
        # define consumable function in action translator #
        ###################################################
        self.vial_bottom_queue = Queue()
        self.the_number_of_vial = 80
        self.__initVialBottom()

    ###################################################
    # define consumable function in action translator #
    ###################################################
    def __initVialBottom(self):
        """
        initialize vial number depending on Queue.

        :return: None: 
        """
        for num in range(self.the_number_of_vial):
            self.vial_bottom_queue.put(num)  

    ###################################################
    # define consumable function in action translator #
    ###################################################
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
Then, you need to use defined function in task function of `action translator` ([Action/Module/{ModuleName}.py](Action/Module))
```python
    def AddSolution(self, task_info_list:list, jobID:int, location_dict:dict, TaskLogger_obj:object, mode_type="virtual"):
        res_msg=""
        current_func_name=sys._getframe().f_code.co_name
        # execution for each task depending on batch size of cycle
        for vial_task_idx, pump_dict in enumerate(task_info_list): # for each vial
            ...
            # please extract action_data in task_dict, and location dict from resource manager
            self.ResourceManager_obj.updateStatus(current_func_name, True)
            ####################################################
            # utilize consumable function in action translator #
            ####################################################
            vial_loc=self.__popVialBottom()
            action_data=[location_dict["Stirrer"][task_idx], vial_loc]
            ####################################################
            # utilize consumable function in action translator #
            ####################################################
            data_dict=self.executeAction(self.__SolidStateModule_name,jobID,"RobotArm","Move",action_data,mode_type, TaskLogger_obj, data_dict)

            ... 
```
### 2. Define alert function using digitalsecretary in action translator 
If you want to add alert system in OCTOPUS, please define alert function with `DigitalSecretary` for sending message to administrators directly.
```python
    def __alertVialNum(self, TaskLogger_obj, mode_type="virtual"):
        text_content="[{}] vial number ({}) is not enough, please fill vial".format(self.robot_module_name, self.vial_bottom_queue.qsize())
        if self.vial_bottom_queue.qsize()<=10:
            AlertMessage(text_content=text_content, key_path="./Log", message_module_list=["dooray"], mode_type=mode_type)
        else:
            pass
```
Above example represents alert system for monitoring vial storage. If the number of vials is below 10, alert system send message to researchers for restock in vial storage. 

### 3. Add new task scheduling methods
If you want to develop novel algorithm of task scheduling methods, then please define in `TaskScheduler.scheduleAllTask` function.
```python
class TaskScheduler(ActionTranslator):
    def scheduleAllTask(self, total_recipe_template_list:list, jobID:int, TaskLogger_obj:object, mode_type:str):
        if self.schedule_mode == "FCFS" or self.schedule_mode == "BackFill":
            ...
        elif self.schedule_mode=="ClosedPacking":
            ...
```
### 4. Customize allocation function in ResourceManager

If you want to customize `allocationLocation` function depending on module settings, please customize `get{Module Name}Resource` function in [Resource/Module/{Module Name}.py](Resource/Module).
```python
    def allocateLocation(self, module_type:str, jobID:int, total_recipe_template_list:list):
        if module_type == "BatchSynthesis":
            ...
        elif module_type == "Washing":
            ...
```
5. Customize `notifyNumbersOfTasks` function. This function notify to remaining device location information to task schduler. Please refer [Resource/ResourceManager_Class.py](Resource/ResourceManager_Class.py)
```python
    def notifyNumbersOfTasks(self, total_recipe_template_list:list):
        if "BatchSynthesis"==module_seq_list[0]:
            ...
        elif "Washing"==module_seq_list[0]:
            ...
```