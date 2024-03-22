#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @brief    [Execution file] 
# @version  1_1
# @version  2_1: author  Hyuk Jun Yoo (yoohj9475@kist.re.kr) // TEST    2023-09-05

import os, sys
import json
import time
import datetime
import pickle
import pandas as pd
import copy
from queue import Queue

from Algorithm.Bayesian.BOdiscreteTest import ASLdiscreteBayesianOptimization
# from Algorithm.ReactionSpace.ReactionSpace import Reactionspace
from Algorithm.Automatic.Automated import Automatic
from Algorithm.Loss.UV_loss import Loss
from Log.DigitalSecretary import AlertMessage
from Log.Logging_Class import TaskLogger
from DB.DB_Class import MongoDB_Class
from TaskAction.ActionExecutor import ActionExecutor


class Job(object):
    '''
    '''
    def __init__(self, jobScript):
        # generate class variable
        self.jobScript = jobScript
        self.metadata_dict = self.jobScript["metadata"]
        self.algorithm_dict = self.jobScript["algorithm"]
        self.process_dict = self.jobScript["process"]

        ### defintion of jobscheduler ###
        self.TaskLogger_obj=TaskLogger(self.metadata_dict, self.metadata_dict["userName"])
        self.TaskLogger_obj.current_platform_name="Job-->Submitted & Waiting" # while experiment, TaskScheduler will update every process done!
        self.TaskLogger_obj.status="{}".format(self.TaskLogger_obj.current_platform_name) # in execution system
        self.metadata_dict["jobStatus"]="{}".format(self.TaskLogger_obj.current_platform_name) # in execution system
        # self.algorithm_dict["totalExperimentNum"]=0 # initialize
        # self.DB_obj = MongoDB_Class(self.TaskLogger_obj)
        self.tcp_obj=ActionExecutor()
        ### defintion of metadata ###
        self.platform_name="JobExecution"
        self.metadata_dict["jobStatus"]="Waiting..."
        self.metadata_dict["temperature"]=25
        self.metadata_dict["humidity"]="68%"
        # check submission time
        self.metadata_dict["jobSubmitTime"]=time.strftime("%Y-%m-%d %H:%M:%S")
        self.jobSubmissionTime=time.time()

        # Algorithm

        # Make each model
        # Autonomous:BayesianOptimization
        if self.algorithm_dict["model"] == "BayesianOptimization": #YOO -> 이름 
            self.Algorithm_obj=ASLdiscreteBayesianOptimization(self.algorithm_dict)
            message="[jobID={0}] Algorithm, model : {1}".format(self.metadata_dict["jobID"], self.algorithm_dict["model"])
            self.TaskLogger_obj.info(self.platform_name, message)
        # Autonomous:ReactionSpace
        # elif self.algorithm_dict["model"] == "ReactionSpace":
        #     RS_obj = Reactionspace(self.algorithm_dict)
        #     self.Algorithm_obj=RS_obj
        #     message="[jobID={0}] Algorithm, model : {1}".format(self.metadata_dict["jobID"], self.algorithm_dict["model"])
        #     self.TaskLogger_obj.info(self.platform_name, message)
        # load previous model
        elif self.algorithm_dict["model"] == "PreviousModel":
            self.Algorithm_obj=self.loadModel(self.algorithm_dict["modelPath"])
            message="[jobID={0}] Algorithm, model : {1}".format(self.metadata_dict["jobID"], self.algorithm_dict["model"])
            self.TaskLogger_obj.info(self.platform_name, message)
        elif self.algorithm_dict["model"] == "Automatic":
            self.Algorithm_obj=Automatic(self.algorithm_dict)
            message="[jobID={0}] Algorithm, model : {1}".format(self.metadata_dict["jobID"], self.algorithm_dict["model"])
            self.TaskLogger_obj.info(self.platform_name, message)
        else:
            raise ValueError("job script file error")

    def __openJsonFile(self, json_path:str):
        """
        :params json_path (str): json path

        :return json_data (dict) json_data
        """
        with open(json_path, "r") as f:
            json_data = json.load(f)
        return json_data
    
    def __writeJsonFile(self, json_path:str, process_template_dict:dict):
        """
        :params: json_path (str): json path

        :return: None
        """
        with open(json_path,'w') as f:
            json.dump(process_template_dict, f, indent=5)
    
    def saveDictToJSON(self, dict_obj:dict, TOTAL_DATA_FOLDER:str, file_name:str):
        """
        extract task type and task data

        :param dict_obj (dict): process dict
        :param file_name (str): time_str=time.strftime("%Y%m%d_%H%M")
        :param mode (args): 
            if bool(mode) == False: --> just 
            elif bool(mode) == True: --> add mode[0](str, sub_dir) in path
        
        :return TOTAL_DATA_FOLDER/file_name (str): {dir}/{filename}.json
        """
        if os.path.isdir(TOTAL_DATA_FOLDER) == False:
            os.makedirs(TOTAL_DATA_FOLDER)
        with open(TOTAL_DATA_FOLDER+"/"+file_name+".json", 'w') as outfile:
            json.dump(dict_obj, outfile, indent=5)
        print(TOTAL_DATA_FOLDER)

        return TOTAL_DATA_FOLDER

    def MakeAllDataforMulti(self, experiment_idx_queue:Queue, metadata_dict:dict, algorithm_dict:dict, process_dict:dict, result:dict):
        """
        allocate synthesis sequence process in json file (process) depending on metadata, process, real_data
        
        :param experiment_idx_queue (Queue) : 
        :param metadata_dict (dict) : metadata for explaining experiment's information ( ex). StartTime, Experiment, Element, Humidity, Temperature...etc)
        :param algorithm_dict={} (dict) : algorithm information, hyparameter
            - if "Automatic" --> 
            - if not "Autonmatic" --> 
        :param process_dict (dict) : process information included Synthesis, Preprocess, Characterization
        :param result (dict) : real_data information

        :return all_data_template (dict): all_data_template
        
        all_data_template_list={
            "metadata":metadata_dict,
            "algorithm":algorithm_dict, # depending on Automatic, or {AI-based ex) BayesianOptimization} func
            "process":process_dict,
            "result":result
            // [{'lambdamax': [300.214759], 'FWHM': [574.825725], 'intensity': [549.221933]]
        }
        """
        all_data_template={}
        copy_metadata_dict=copy.deepcopy(metadata_dict)
        copy_metadata_dict["experimentIdx"]=experiment_idx_queue.get()
        all_data_template["metadata"]=copy_metadata_dict
        all_data_template["algorithm"]=algorithm_dict
        all_data_template["process"]=process_dict
        all_data_template["result"]=result
        return all_data_template

    def execute(self, TaskScheduler_obj:object, ProcessGenerator_obj:object):
        # run cycle
        self.TaskLogger_obj.info(self.platform_name, info_msg="######### Cycle start #########")
        # total_iter_num=0
        # just check only in one cycle
        # if self.metadata_dict["modeType"]=="virtual":
        #     self.algorithm_dict["totalCycleNum"]=1
        # else:
        #     pass
        if self.algorithm_dict["model"] != "Automatic":
            # calculate job start time, job waiting time
            start_date=time.time()
            jobStartTime=time.strftime("%Y-%m-%d %H:%M:%S")
            
            # rename dirname
            start_dir_name=time.strftime("%Y%m%d")
            # Modify metadata
            self.algorithm_dict["totalExperimentNum"]=self.algorithm_dict["batchSize"]*self.algorithm_dict["totalCycleNum"]
            self.TaskLogger_obj.totalExperimentNum=self.algorithm_dict["totalExperimentNum"]
            
            experiment_idx_queue=Queue()
            for num in range(self.algorithm_dict["totalExperimentNum"]):
                experiment_idx_queue.put(num)
            
            for iter_num in range(self.algorithm_dict["totalCycleNum"]):
                
                # Suggest Next Step
                self.TaskLogger_obj.current_platform_name="{}-->suggest next step".format(self.algorithm_dict["model"])
                self.TaskLogger_obj.status="{}/{}:{}".format(self.TaskLogger_obj.currentExperimentNum, self.TaskLogger_obj.totalExperimentNum, self.TaskLogger_obj.current_platform_name) # in execution system
                self.metadata_dict["jobStatus"]="{}/{}:{}".format(self.TaskLogger_obj.currentExperimentNum, self.TaskLogger_obj.totalExperimentNum, self.TaskLogger_obj.current_platform_name) # in execution system
                
                self.TaskLogger_obj.info(self.algorithm_dict["model"], info_msg="batchSize={}".format(self.algorithm_dict["batchSize"]))
                total_next_points, total_norm_next_points = self.Algorithm_obj.suggestNextStep()# reaction space 이런 format 으로 바꾸기 
                
                for idx, next_point in enumerate(total_next_points):
                    self.TaskLogger_obj.info("Algorithm [{}]".format(idx), info_msg="next_point {}: {}".format(idx, next_point))
                
                # Generate Recipe depending on Task_sequence_list
                self.TaskLogger_obj.current_platform_name="ProcessGenerator-->generate process"
                self.TaskLogger_obj.status="{}/{}:{}".format(self.TaskLogger_obj.currentExperimentNum, self.TaskLogger_obj.totalExperimentNum, self.TaskLogger_obj.current_platform_name) # in execution system
                self.metadata_dict["jobStatus"]="{}/{}:{}".format(self.TaskLogger_obj.currentExperimentNum, self.TaskLogger_obj.totalExperimentNum, self.TaskLogger_obj.current_platform_name) # in execution system
                
                total_process_template_list=[]
                for batch_idx, total_next_point in enumerate(total_next_points):
                    each_process=ProcessGenerator_obj.generateRecipe(self.process_dict, input_next_point=total_next_point)
                    total_process_template_list.append(each_process)
                    self.__writeJsonFile("Test_{}_idx_{}.json".format(self.algorithm_dict["model"], batch_idx), each_process)
                self.TaskLogger_obj.info("ProcessGenerator", info_msg="Allocate all of process based on job script!")
                    
                # Allocate hardware --> Cycle running
                self.TaskLogger_obj.current_platform_name="TaskScheduler-->schedule all Task"
                self.TaskLogger_obj.status="{}/{}:{}".format(self.TaskLogger_obj.currentExperimentNum, self.TaskLogger_obj.totalExperimentNum, self.TaskLogger_obj.current_platform_name) # in execution system
                self.metadata_dict["jobStatus"]="{}/{}:{}".format(self.TaskLogger_obj.currentExperimentNum, self.TaskLogger_obj.totalExperimentNum, self.TaskLogger_obj.current_platform_name) # in execution system
                
                done_message="######### [{}-{}] Cycle {}/{} is running #########".format(self.metadata_dict["subject"], self.metadata_dict["userName"], iter_num+1, self.algorithm_dict["totalCycleNum"])
                self.TaskLogger_obj.info(self.platform_name, info_msg=done_message)
                AlertMessage(text_content=done_message, key_path="./Log",message_platform_list=["dooray"], mode_type=self.metadata_dict["modeType"])
                return_result_list_to_db=TaskScheduler_obj.scheduleAllTask(total_process_template_list, self.metadata_dict["jobID"], self.TaskLogger_obj, self.metadata_dict["modeType"])

                # Evaluation --> Loss: extract data to dict
                batch_finish_time=time.strftime("%Y%m%d_%H%M%S")
                optimal_value_list=[]
                property_dict_list=[]
                # Calculate Loss, register point and save point to csv file : Yoo 이부분 Reaction space 따로 만들어야 할듯
                self.TaskLogger_obj.current_platform_name="Loss-->calculate loss"
                self.TaskLogger_obj.status="{}/{}:{}".format(self.TaskLogger_obj.currentExperimentNum, self.TaskLogger_obj.totalExperimentNum, self.TaskLogger_obj.current_platform_name) # in execution system
                self.metadata_dict["jobStatus"]="{}/{}:{}".format(self.TaskLogger_obj.currentExperimentNum, self.TaskLogger_obj.totalExperimentNum, self.TaskLogger_obj.current_platform_name) # in execution system
                
                for batch_idx, result_dict in enumerate(return_result_list_to_db):
                    Loss_obj=Loss(result_dict, self.Algorithm_obj.lossTarget)
                    optimal_value, property_dict = getattr(Loss_obj, self.Algorithm_obj.lossMethod)()
                    optimal_value_list.append(optimal_value)
                    property_dict_list.append(property_dict)
                    self.TaskLogger_obj.info("Algorithm", info_msg="{} optimal_value : {}".format(batch_idx, optimal_value))

                dirname="USER/{}/DB/{}/{}/{}".format(self.metadata_dict["userName"], self.metadata_dict["subject"], start_dir_name, self.metadata_dict["modeType"])
                filename="{}_{}_data".format(batch_finish_time, iter_num)
                self.Algorithm_obj.registerPoint(input_next_points=total_next_points, norm_input_next_points=total_norm_next_points, property_list=property_dict_list, input_result_list=optimal_value_list)
                self.Algorithm_obj.output_space(dirname+"/loss_norm", filename)
                self.Algorithm_obj.output_space_realCondition(dirname+"/loss_real", filename)
                self.Algorithm_obj.output_space_property(dirname+"/property", filename)

                done_message="######### [{}-{}] Cycle {}/{} is done #########".format(self.metadata_dict["subject"], self.metadata_dict["userName"], iter_num+1, self.algorithm_dict["totalCycleNum"])
                self.TaskLogger_obj.info(self.platform_name, info_msg=done_message)
                AlertMessage(done_message,key_path="./Log", message_platform_list=["dooray"], mode_type=self.metadata_dict["modeType"])
                
                # Save our model : 수정하기 
                self.TaskLogger_obj.current_platform_name="Algorithm-->save model"
                self.TaskLogger_obj.status="{}/{}:{}".format(self.TaskLogger_obj.currentExperimentNum, self.TaskLogger_obj.totalExperimentNum, self.TaskLogger_obj.current_platform_name) # in execution system
                self.metadata_dict["jobStatus"]="{}/{}:{}".format(self.TaskLogger_obj.currentExperimentNum, self.TaskLogger_obj.totalExperimentNum, self.TaskLogger_obj.current_platform_name) # in execution system
                each_cycle_num=int(len(self.Algorithm_obj.res)/self.algorithm_dict["batchSize"]) # reaction space 도 체커 만들어서 같은 이름으로 함수 만들고 넣으면 될듯 
                self.savedModel(directory_path="USER/{}/SaveModel/{}/{}/{}".format(self.metadata_dict["userName"], self.metadata_dict["subject"], start_dir_name, self.metadata_dict["modeType"]), 
                                                    filename="{}_{}_obj".format(batch_finish_time, each_cycle_num))
                self.TaskLogger_obj.info("Algorithm", info_msg="Save our model object, filename={}".format("{}_{}_obj".format(batch_finish_time, each_cycle_num)))
                
                # address job metadata in metadata_dict
                self.metadata_dict["jobStartTime"]=jobStartTime
                self.metadata_dict["jobWaitingTime(sec)"]=round(start_date-self.jobSubmissionTime,2)
                self.metadata_dict["jobFinishTime"]="Now Recording...Please check final data"
                self.metadata_dict["jobTurnAroundTime(sec)"]="Now Recording...Please check final data"
                # caculate finish time, turnaround time, Only record final data
                if iter_num==self.algorithm_dict["totalCycleNum"]-1: 
                    finish_date=time.time()
                    self.metadata_dict["jobFinishTime"]=time.strftime("%Y-%m-%d %H:%M:%S")
                    self.metadata_dict["jobTurnAroundTime(sec)"]=round(finish_date-start_date, 2)
                self.metadata_dict["jobDelayTimeList"]=self.TaskLogger_obj.delayTimeList
                self.metadata_dict["jobDelayTime(sec)"]=self.TaskLogger_obj.delayTime

                # save total data dict in RecipsJson folder
                self.TaskLogger_obj.current_platform_name="DB-->store in DB"
                self.TaskLogger_obj.status="{}/{}:{}".format(self.TaskLogger_obj.currentExperimentNum, self.TaskLogger_obj.totalExperimentNum, self.TaskLogger_obj.current_platform_name) # in execution system
                self.metadata_dict["jobStatus"]="{}/{}:{}".format(self.TaskLogger_obj.currentExperimentNum, self.TaskLogger_obj.totalExperimentNum, self.TaskLogger_obj.current_platform_name) # in execution system
                # generate total_data_dict (to integrate metadata_dict, algorithm_dict, process_dict_list, result_list)
                total_data_dict_list=[]
                for batch_idx in range(len(total_process_template_list)):
                    total_data_dict_list.append(self.MakeAllDataforMulti(experiment_idx_queue=experiment_idx_queue, metadata_dict=self.metadata_dict,algorithm_dict=self.algorithm_dict, 
                                                    process_dict=total_process_template_list[batch_idx], result=return_result_list_to_db[batch_idx]))
                for idx, total_data_dict in enumerate(total_data_dict_list):
                    dirname="USER/{}/DB/{}/{}/{}".format(self.metadata_dict["userName"], self.metadata_dict["subject"], start_dir_name, self.metadata_dict["modeType"])
                    filename="{}_{}_{}_data".format(batch_finish_time, idx, iter_num)
                    # for code debugging
                    self.saveDictToJSON(total_data_dict, dirname, filename) 

                # Add DB later
                # for idx in range(len(self.DB_obj_list)):
                #     self.DB_obj.sendDocument(db_name="Data", collection_name=self.metadata_dict["element"], document=total_data_dict_list[idx])
                
            # All cycle is done
            done_message="######### [{}-{}] All Cycle is done #########".format(self.metadata_dict["subject"], self.metadata_dict["userName"])
            self.TaskLogger_obj.info(self.platform_name, info_msg=done_message)
            AlertMessage(done_message, key_path="./Log", message_platform_list=["dooray"], mode_type=self.metadata_dict["modeType"])
            

        elif self.algorithm_dict["model"]=="Automatic":
            # calculate job start time, job waiting time
            start_date=time.time()
            
            # rename dirname
            start_dir_name=time.strftime("%Y%m%d")
            
            # Suggest Next Step
            total_next_points= self.Algorithm_obj.suggestNextStep()# reaction space 이런 format 으로 바꾸기 
            self.TaskLogger_obj.totalExperimentNum=self.algorithm_dict["totalExperimentNum"]
            # genearte experiment_idx_queue
            experiment_idx_queue=Queue()
            for num in range(self.algorithm_dict["totalExperimentNum"]):
                experiment_idx_queue.put(num)
            
            self.TaskLogger_obj.info(self.algorithm_dict["model"], info_msg="total experiments={}".format(self.algorithm_dict["totalExperimentNum"]))
            self.TaskLogger_obj.current_platform_name="{}-->suggest next step".format(self.algorithm_dict["model"])
            self.TaskLogger_obj.status="{}:{}".format(self.TaskLogger_obj.current_platform_name, self.algorithm_dict["totalExperimentNum"]) # in execution system
            self.metadata_dict["jobStatus"]="{}:{}".format(self.TaskLogger_obj.current_platform_name, self.algorithm_dict["totalExperimentNum"]) # in execution system
            for idx, next_point in enumerate(total_next_points):
                self.TaskLogger_obj.info("{} [{}]".format(self.algorithm_dict["model"], idx), info_msg="next_point {}: {}".format(idx, next_point))
            
            # Generate Recipe depending on task_sequence_list
            self.TaskLogger_obj.current_platform_name="ProcessGenerator-->generate recipe"
            self.TaskLogger_obj.status="{}:{}".format(self.TaskLogger_obj.current_platform_name, self.algorithm_dict["totalExperimentNum"]) # in execution system
            self.metadata_dict["jobStatus"]="{}:{}".format(self.TaskLogger_obj.current_platform_name, self.algorithm_dict["totalExperimentNum"]) # in execution system
            # generate recipe
            total_process_template_list=[]
            for batch_idx in range(self.algorithm_dict["totalExperimentNum"]):
                next_point={}
                try:
                    next_point=total_next_points[batch_idx]
                except Exception as e:
                    pass
                each_process=ProcessGenerator_obj.generateRecipe(self.process_dict, input_next_point=next_point)
                total_process_template_list.append(each_process)
                self.__writeJsonFile("Test_{}_idx_{}.json".format(self.algorithm_dict["model"], batch_idx), each_process)
            self.TaskLogger_obj.info("ProcessGenerator", info_msg="Allocate all of process based on job script!")
            
            # Allocate hardware --> Cycle running
            self.TaskLogger_obj.current_platform_name="TaskScheduler-->schedule all task"
            self.TaskLogger_obj.status="{}:{}".format(self.TaskLogger_obj.current_platform_name, self.algorithm_dict["totalExperimentNum"]) # in execution system
            self.metadata_dict["jobStatus"]="{}:{}".format(self.TaskLogger_obj.current_platform_name, self.algorithm_dict["totalExperimentNum"]) # in execution system
            done_message="######### [{}-{}] Experiment {} is running #########".format(self.metadata_dict["subject"], self.metadata_dict["userName"], self.algorithm_dict["totalExperimentNum"])
            self.TaskLogger_obj.info(self.platform_name, info_msg=done_message)
            AlertMessage(text_content=done_message, key_path="./Log",message_platform_list=["dooray"], mode_type=self.metadata_dict["modeType"])
            return_result_list_to_db=TaskScheduler_obj.scheduleAllTask(total_process_template_list, self.metadata_dict["jobID"], self.TaskLogger_obj, self.metadata_dict["modeType"])

            # caculate finish time, turnaround time
            finish_date=time.time()
            
            # address job metadata in metadata_dict
            self.metadata_dict["jobStartTime"]=time.strftime("%Y-%m-%d %H:%M:%S")
            self.metadata_dict["jobWaitingTime(sec)"]=round(start_date-self.jobSubmissionTime,2)
            self.metadata_dict["jobFinishTime"]=time.strftime("%Y-%m-%d %H:%M:%S")
            self.metadata_dict["jobTurnAroundTime(sec)"]=round(finish_date-start_date, 2)
            self.metadata_dict["jobDelayTimeList"]=self.TaskLogger_obj.delayTimeList
            self.metadata_dict["jobDelayTime(sec)"]=self.TaskLogger_obj.delayTime
            
            # generate total_data_dict (to integrate metadata_dict, algorithm_dict, process_dict_list, result_list)
            total_data_dict_list=[]
            for batch_idx in range(len(total_process_template_list)):
                total_data_dict_list.append(self.MakeAllDataforMulti(experiment_idx_queue=experiment_idx_queue, metadata_dict=self.metadata_dict, algorithm_dict=self.algorithm_dict, 
                                                process_dict=total_process_template_list[batch_idx], result=return_result_list_to_db[batch_idx]))

            # save total data dict in RecipsJson folder
            self.TaskLogger_obj.current_platform_name="DB-->store in DB"
            self.TaskLogger_obj.status="{}:{}".format(self.TaskLogger_obj.current_platform_name, self.algorithm_dict["totalExperimentNum"]) # in execution system
            self.metadata_dict["jobStatus"]="{}:{}".format(self.TaskLogger_obj.current_platform_name, self.algorithm_dict["totalExperimentNum"]) # in execution system
            total_finish_time=time.strftime("%Y%m%d_%H%M%S")
            for idx, total_data_dict in enumerate(total_data_dict_list):
                dirname="USER/{}/DB/{}/{}/{}".format(self.metadata_dict["userName"], self.metadata_dict["subject"], start_dir_name, self.metadata_dict["modeType"])
                filename="{}_{}_data".format(total_finish_time, idx)
                # for code debugging
                self.saveDictToJSON(total_data_dict, dirname, filename) 

            # Add DB later
            # self.DB_obj.sendDocument(db_name="Data", collection_name=self.metadata_dict["element"], document=total_data_dict_list[idx])

            done_message="######### [{}-{}] Experiment {} is done #########".format(self.metadata_dict["subject"], self.metadata_dict["userName"], self.algorithm_dict["totalExperimentNum"])
            self.TaskLogger_obj.info(self.platform_name, info_msg=done_message)
            AlertMessage(done_message,key_path="./Log", message_platform_list=["dooray"], mode_type=self.metadata_dict["modeType"])

        return True
    
    # @alertError
    def delete(self):
        command_str ="qdel/{}".format(self.metadata_dict["jobID"])
        res_msg=self.tcp_obj.callServer_qcommand(command_str)
        
        return res_msg

    # @alertError
    def hold(self):
        command_str ="qhold/{}".format(self.metadata_dict["jobID"])
        res_msg=self.tcp_obj.callServer_qcommand(command_str)
        
        return res_msg
    
    # @alertError
    def restart(self):
        command_str ="qrestart/{}".format(self.metadata_dict["jobID"])
        res_msg=self.tcp_obj.callServer_qcommand(command_str)
        
        return res_msg

    # @alertError
    def savedModel(self, directory_path, filename='bo_obj'):
        """
        save ML model to use already fitted model later.
        
        Arguments
        ---------
        directory_path (str)
        model_index (int) : order of model object
        filename='bo_obj' (str)
        
        Returns
        -------
        return None
        """
        if os.path.isdir(directory_path) == False:
            os.makedirs(directory_path)
        fname = os.path.join(directory_path, filename+".pickle")
        with open(fname, 'wb') as f:
            pickle.dump(self.Algorithm_obj, f)

    # @alertError
    def loadModel(self, path):
        """
        load ML model to use already fitted model later depending on filename.
        
        Arguments
        ---------
        path (str)
        
        Returns
        -------
        return model_obj : loaded_model
        """

        try:
            with open(path, 'rb') as f:
                model_obj = pickle.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("File is not existed")

        return model_obj
