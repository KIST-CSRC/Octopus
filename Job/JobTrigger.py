from more_itertools import locate
import json


class JobTrigger:
    
    def __init__(self) -> None:

        with open(f"Job/device_standby_time.json", 'r', encoding='utf-8') as f:
            self.device_standby_time_dict=json.load(f)
        
        # self.device_standby_time_dict={
        #     "BatchSynthesisModule":["React"],
        #     "WashingModule":["Oven", "Centrifugation"],
        #     "UVVisModule":"" 
        # }

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
        # np_lst = np.array(lst)
        # indexes = np.where(np.equal(np_lst,value))[0]
        # indexes = np.where(np_lst==value)[0]
        # return indexes.tolist()

        return list(locate(lst, lambda x: x == value))

    def FCFS(self, job_wait_queue:list, job_exec_queue:list, ResourceManager_obj:object):
        """
        [FCFS = First-Come,First-Served]
        
        If the job_execution_queue is empty:
        or
        if a specific platform is empty but only wants to use the empty platform:
        
        The return value should always be a list containing Job script files.

        return (list)
        """
        if len(job_wait_queue)==0:
            return []
        else:
            if len(job_exec_queue)==0:
                return [job_wait_queue.pop(0)]
            else:
                return []

    def Gang(self, job_wait_queue:list, job_exec_queue:list):
        pass

    def Backfill(self, job_wait_queue:list, job_exec_queue:list, ResourceManager_obj:object):
        """
        ResourceManager_obj.task_device_location_dict
        =>
        {
            "BatchSynthesis":{ 
                "Stirrer":["?"]*8,
                "vialHolder":["?"]*8
            },
            "UV":{ 
                "vialHolder":["?"]*8
            }
        }
        
        job scheduler 
        """
        if len(job_wait_queue)==0 and len(job_exec_queue)==0:
            return []
        elif len(job_wait_queue)!=0 and len(job_exec_queue)==0:
            popped_job_wait=job_wait_queue.pop(0)
            return [popped_job_wait]
        else:
            # update bottleneck timeline for each module
            module_device_standby_time_status_list=[]
            for job_exec in job_exec_queue:
                for module_name, module_device_standby_time_list in self.device_standby_time_dict.items():
                    for module_device_standby_time in module_device_standby_time_list:
                        if module_device_standby_time in job_exec.TaskLogger_obj.status: # Synthesis, Preprocess, Characterizatin, Evaluation
                            module_device_standby_time_status_list.append(module_name)
                            break
                        
            # update device resource
            resource_dict={}
            for module_name, module_resource_dict in ResourceManager_obj.task_device_location_dict.items():
                for device_name, device_resource_list in module_resource_dict.items():
                    empty_location_list=self.__find_indexes(device_resource_list, "?")
                    resource_dict[module_name]=len(empty_location_list)
            
            # extract best job
            result_job_list=[]
            for job_wait in job_wait_queue:
                for process_dict in job_wait.process_dict.values(): # "Synthesis":{}, "Preprocess":{}, "Characterization":{}, "Evaluation":{}
                    for module_name, module_dict in process_dict.items(): # BatchSynthesis, UV ...
                        if len(module_dict)!=0 and module_name in module_device_standby_time_status_list:
                            if job_wait.algorithm_dict["model"]=="Manual":
                                if job_wait.algorithm_dict["inputParams"] <= resource_dict[module_name]:
                                    job_wait_index=job_wait_queue.index(job_wait)
                                    popped_job_wait=job_wait_queue.pop(job_wait_index)
                                    result_job_list.append(popped_job_wait)
                                    return result_job_list
                            else:
                                if job_wait.algorithm_dict["batchSize"] <= resource_dict[module_name]:
                                    job_wait_index=job_wait_queue.index(job_wait)
                                    popped_job_wait=job_wait_queue.pop(job_wait_index)
                                    result_job_list.append(popped_job_wait)
                                    return result_job_list
    
    def ClosedPacking(self, job_wait_queue:list, job_exec_queue:list, ResourceManager_obj:object):
        """
        ResourceManager_obj.task_device_location_dict
        =>
        {
            "BatchSynthesis":{ 
                "Stirrer":["?"]*8,
                "vialHolder":["?"]*8
            },
            "UV":{ 
                "vialHolder":["?"]*8
            }
        }
        
        job scheduler 
        """
        if len(job_wait_queue)==0 and len(job_exec_queue)==0:
            return []
        elif len(job_wait_queue)==0 and len(job_exec_queue)!=0:
            return []
        elif len(job_wait_queue)!=0 and len(job_exec_queue)==0:
            popped_job_wait=job_wait_queue.pop(0)
            return [popped_job_wait]
        elif len(job_wait_queue)!=0 and len(job_exec_queue)!=0:
            # update device resource
            resource_dict={}
            for module_name, module_resource_dict in ResourceManager_obj.task_device_location_dict.items():
                for device_name, device_resource_list in module_resource_dict.items():
                    empty_location_list=self.__find_indexes(device_resource_list, "?")
                    resource_dict[module_name]=len(empty_location_list)
                    
            # update bottleneck timeline for each module
            module_device_standby_time_status_list=[]
            for job_exec in job_exec_queue:
                for module_name, module_device_standby_time_list in self.device_standby_time_dict.items():
                    for module_device_standby_time in module_device_standby_time_list:
                        if module_device_standby_time in job_exec.TaskLogger_obj.status: # Synthesis, Preprocess, Characterizatin, Evaluation
                            module_device_standby_time_status_list.append(module_name)
            
            # extract best job
            for job_wait in job_wait_queue:
                for process_dict in job_wait.process_dict.values(): # "Synthesis":{}, "Preprocess":{}, "Characterization":{}, "Evaluation":{}
                    for module_name, module_dict in process_dict.items(): # BatchSynthesis, UV ...
                        if len(module_dict)!=0 and module_name in module_device_standby_time_status_list and len(resource_dict[module_name])!=0:
                            job_wait_index=job_wait_queue.index(job_wait)
                            popped_job_wait=job_wait_queue.pop(job_wait_index)
                            return [popped_job_wait]
            return [] 

    def SJF(self, job_wait_queue:list, job_exec_queue:list):
        """
        [SJF = Shortest Job First]
        """
        pass

    def Priority(self, job_wait_queue:list, job_exec_queue:list):
        pass

    def RoundRobin(self, job_wait_queue:list, job_exec_queue:list):
        pass
