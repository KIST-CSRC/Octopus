from datetime import datetime
from queue import Queue
from Task.TCP import ParameterTCP, TCP_Class
from Job.Job_Class import Job
import paramiko

class JobScriptError:

    def setBoundary(self):
        """
        constant.py를 통해 설정된 boundary가 존재함. 
        이를 반영해서, job script file을 잘 못 만들면 어떤 부분을 몇 미만으로 수정해라 이런식에 에러를 띄워야함
        """
        pass

    def checkJobScript(self, job_script_dict):
        pass

class JobScheduler(JobScriptError, ParameterTCP):
    """
    [JobScheduler] JobScheduler Class for scheduling job

    # function
    - qsub(client_socket, user_name, job_script_name, job_script):
    - qdel(client_socket, job_id)
    - qhold(client_socket, job_id)
    - qrestart(client_socket, job_id)
    - qstat(client_socket)
    """

    def __init__(self, server_logger:object, job_wait_queue:list, job_exec_queue:list, job_hold_queue:list, ResourceManager_obj:object):
        JobScriptError.__init__(self)
        ParameterTCP.__init__(self)
        self.tcp_obj=TCP_Class()
        self.BUFF_SIZE = 4096
        self.the_number_of_job=9999 # can change the CAPA of job_queue
        self.server_logger=server_logger
        self.job_id_generator=Queue() # use Queue (because of FIFO) not list
        # job queue
        self.job_wait_queue=job_wait_queue
        self.job_exec_queue=job_exec_queue
        self.job_hold_queue=job_hold_queue
        # hardware status
        self.ResourceManager_obj=ResourceManager_obj
        self.task_hardware_status_dict=self.ResourceManager_obj.task_hardware_status_dict
        # print("self.task_hardware_status_dict",id(self.task_hardware_status_dict))
        # print("self.ResourceManager_obj.task_hardware_status_dict",id(self.ResourceManager_obj.task_hardware_status_dict))

    def updateNode(self, client_socket):
        """
        update module node information

        :param client_socket (object) : socket object
        :param user_name (str) : userName ex) HJ, NY...
        """
        self.ResourceManager_obj.task_hardware_info_dict=self.ResourceManager_obj.requestHardwareInfo()
        command_byte="succeed to update module node information:{}".format(self.ResourceManager_obj.task_hardware_info_dict)
        client_socket.sendall(command_byte.encode('utf-8'))

    def qsub(self, client_socket, user_name, job_script_filename, job_script, mode_type):
        """
        submit job script

        :param client_socket (object) : socket object
        :param user_name (str) : userName ex) HJ, NY...
        :param job_script_filename (str) : 20230516_automatic -> real path : "USER/{user_name}/job_script/{job_script_filename}.json"
        :param job_script (dict) : read job_script 
            -> job_script={
                "metadata":{}
                "recipe":{}
            }
        :param mode_type (str) : "real" or "virtual"
        """
        empty_true = self.job_id_generator.empty()
        if empty_true==True:
            for job_id in range(self.the_number_of_job):
                self.job_id_generator.put(job_id)
        job_id=self.job_id_generator.get()
        
        # Only insert this information in jobscheduler (not jobExecution file)
        job_script["metadata"]["userName"]=user_name
        job_script["metadata"]["modeType"]=mode_type
        job_script["metadata"]["jobID"]=job_id
        job_script["metadata"]["jobFileName"]=job_script_filename
        
        job_execution_obj=Job(job_script) # convert job script file to job execution object
        self.job_wait_queue.append(job_execution_obj)

        command_byte="succeed to submit job, userName:{}, jobID:{}".format(user_name, job_id)
        client_socket.sendall(command_byte.encode('utf-8'))

    def qdel(self, client_socket, user_name, job_id):
        """
        delete job script or job execution (wait and hold)

        :param client_socket (object) : socket object
        :param user_name (str) : userName ex) HJ, NY...
        :param job_id (int) : generated jobID ex) 1,2,...
        """
        # check job script queue
        # extract jobID from job_script_queue
        total_job_queue=self.job_wait_queue+self.job_hold_queue # exclude job_exec_queue
        try:
            job_id_list=[]
            for job_exec in total_job_queue:
                job_exec_id=job_exec.metadata_dict["jobID"]
                job_id_list.append(job_exec_id)
            job_id_index=job_id_list.index(job_id)
            # match requested userName == submitted userName
            if user_name == total_job_queue[job_id_index].metadata_dict["userName"]:
                popped_job_exec=total_job_queue.pop(job_id_index)
                # delete job script in job_script_queue
                if "Waiting" in popped_job_exec.TaskLogger_obj.status:
                    self.job_wait_queue.remove(popped_job_exec)
                    self.ResourceManager_obj.refreshTotalLocation(job_id)
                    res_msg=popped_job_exec.delete()
                    command_byte="succeed to delete job (jobID:{})".format(job_id)
                    client_socket.sendall(command_byte.encode('utf-8'))
                # delete holded job script in hold_job_script_queue
                elif "Holding" in popped_job_exec.TaskLogger_obj.status:
                    self.job_hold_queue.remove(popped_job_exec)
                    self.ResourceManager_obj.refreshTotalLocation(job_id)
                    res_msg=popped_job_exec.delete()
                    command_byte="succeed to delete job (jobID:{})".format(job_id)
                    client_socket.sendall(command_byte.encode('utf-8'))
                # wrong status. unspecified status (Please check status from admin) 
                else:
                    command_byte="Wrong status:{}. Please check status from admin".format(job_id, popped_job_exec.TaskLogger_obj.status)
                    client_socket.sendall(command_byte.encode('utf-8'))
            # requested userName != submitted userName
            else:
                command_byte='JobExecution object is not subscriptable'
                client_socket.sendall(command_byte.encode('utf-8'))
        # ValueError --> job_id_index=job_id_list.index(job_id)
        # job_id isn't include in job_script_queue --> could inside in job_exec_queue
        except ValueError as e:
            command_byte="You cannot delete directly. Please hold job_id:{} exec file first & delete sequentially & error message:{}".format(job_id, e)
            print(e)
            client_socket.sendall(command_byte.encode('utf-8'))
        except TypeError as e:
            command_byte="You cannot delete directly. Please hold job_id:{} exec file first & delete sequentially & error message:{}".format(job_id, e)
            print(e)
            client_socket.sendall(command_byte.encode('utf-8'))
        
    def qhold(self, client_socket, user_name, job_id): 
        """
        hold job script or job execution (wait and hold)

        :param client_socket (object) : socket object
        :param user_name (str) : userName ex) HJ, NY...
        :param job_id (int) : generated jobID ex) 1,2,...
        """
        # check job script queue
        # extract jobID from job_script_queue 
        job_id_exec_list=[]
        try:
            for job_exec in self.job_exec_queue:
                job_exec_id=job_exec.metadata_dict["jobID"]
                job_id_exec_list.append(job_exec_id)
            job_id_index=job_id_exec_list.index(job_id)
            # match requested userName == submitted userName
            if user_name == self.job_exec_queue[job_id_index].metadata_dict["userName"]:
                popped_job_exec=self.job_exec_queue.pop(job_id_index)
                _, task_name=popped_job_exec.TaskLogger_obj.status.split("-->")
                res_msg=popped_job_exec.hold()
                self.ResourceManager_obj.updateStatus(task_name, False)
                popped_job_exec.TaskLogger_obj.status="Holding&"+popped_job_exec.TaskLogger_obj.status
                self.job_hold_queue.append(popped_job_exec)
                command_byte="succeed to hold job (jobID: {})".format(job_id)
                client_socket.sendall(command_byte.encode('utf-8'))
            else:
                command_byte="It is not your job (user_name={}). please check your jobID".format(user_name)
                client_socket.sendall(command_byte.encode('utf-8'))
        except ValueError as e:
            command_byte="ValueError:{}. It is not inside queue (user_name={}). please check your jobID:{}".format(e, user_name, job_id)
            client_socket.sendall(command_byte.encode('utf-8'))

    def qrestart(self, client_socket, user_name, job_id):
        """
        restart job script or job execution (wait and hold)

        :param client_socket (object) : socket object
        :param user_name (str) : userName ex) HJ, NY...
        :param job_id (int) : generated jobID ex) 1,2,...
        """
        # extract jobID from job_script_queue
        job_id_exec_list=[]
        for job_exec in self.job_hold_queue:
            job_exec_id=job_exec.metadata_dict["jobID"]
            job_id_exec_list.append(job_exec_id)
        try:
            job_id_index=job_id_exec_list.index(job_id)
            # match requested userName == submitted userName
            if user_name == self.job_hold_queue[job_id_index].metadata_dict["userName"]:
                poped_job_hold=self.job_hold_queue.pop(job_id_index)
                res_msg=poped_job_hold.restart()
                _, previous_status=poped_job_hold.TaskLogger_obj.status.split("&")
                poped_job_hold.TaskLogger_obj.status=previous_status
                self.job_exec_queue.append(poped_job_hold)
                command_byte="succeed to restart job (jobID: {})".format(job_id)
                client_socket.sendall(command_byte.encode('utf-8'))
            else:
                command_byte="It is not your job (user_name={}). please check your jobID".format(user_name)
                client_socket.sendall(command_byte.encode('utf-8'))
        except ValueError as e:
            command_byte="ValueError:{}.It is not inside queue (user_name={}). please check your jobID:{}".format(e, user_name, job_id)
            client_socket.sendall(command_byte.encode('utf-8'))

    def qstat(self, client_socket):
        """
        check status of job script queue (wait and hold) & job execution queue (wait and hold)
        :param client_socket (object) : socket object
            --> column_names_list = ["userName", "jobTime", "jobID", "jobFileName", "batchSize", "status", "modeType"]
        """
        column_names_list = ["userName", "jobSubmitTime", "jobID", "jobFileName", "currentExperimentNum", "totalExperimentNum", "jobStatus", "modeType"]

        total_row_list=[]
        try:
            # Add rows from job execution file to status table
            total_queue_list=[]
            exec_queue_list=self.job_wait_queue+self.job_exec_queue+self.job_hold_queue
            if len(exec_queue_list)!=0:
                for job_exec in exec_queue_list:
                    row=[]
                    for column_name in column_names_list:
                        # update job status & currentExperiment number based on Task Scheduler's Task Logger object
                        if column_name=="jobStatus":
                            row.append(job_exec.TaskLogger_obj.status)
                        elif column_name=="currentExperimentNum":
                            row.append(job_exec.TaskLogger_obj.currentExperimentNum)
                        elif column_name=="totalExperimentNum":
                            row.append(job_exec.TaskLogger_obj.totalExperimentNum)
                        else:
                            row.append(job_exec.metadata_dict[column_name])
                    total_row_list.append(row)
            else:
                pass # return total_row_list=[]
        except TypeError as e:
            print("TypeError", e)

        client_socket.sendall(str(total_row_list).encode('utf-8'))

    def ashutdown(self, client_socket, platform_name):
        """
        a --> "a" means admin function
          --> "shutdown" means shutdown platform_name ex) ashutdown batchsyntehsis --> shutdown batchsynthesis

        :param client_socket (object) : socket object
        :param platform_name (str) : batch, flow, washing, mobile, 
        """
        # SSHClient Instance
        try:
            command_bytes =str.encode("ashutdown/{}".format(platform_name))
            res_msg=self.tcp_obj.callServer_acommand(command_bytes, platform_name)
            client_socket.sendall(str("ashutdown platform_name").encode('utf-8'))
        except Exception as e:
            client_socket.sendall(str("ashutdown {} error, {}".format(platform_name, e)).encode('utf-8'))

    def areboot(self, client_socket, platform_name):
        """
        a --> "a" means admin function
          --> "reboot" means reboot platform_name ex) areboot batchsyntehsis --> reboot batchsynthesis

        :param client_socket (object) : socket object
        :param platform_name (str) : please check in ["BATCH", "UV", "MOBILE", "FLOW", "WASHING", "INK", "RDE"]
        """
        # SSHClient Instance
        try:
            platform_name_list=["BATCH", "UV", "MOBILE", "FLOW", "WASHING", "INK", "RDE"]
            platform_name=platform_name.upper()
            if platform_name not in platform_name_list:
                res_msg="input platform_name{} is not in platform_name_list : {}".format(platform_name, platform_name_list)
                client_socket.sendall(res_msg.encode('utf-8'))
            else:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
                PLATFORM_HOST=self.routing_table[platform_name]["HOST"]
                PLATFORM_USERNAME=self.routing_table[platform_name]["NAME"]
                PLATFORM_PWD=self.routing_table[platform_name]["PWD"]
                ssh.connect(PLATFORM_HOST, PLATFORM_USERNAME, PLATFORM_PWD)
                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} : SSH CONNECTED")
                stdin, stdout, stderr = ssh.exec_command("sh reboot_node_manager.sh") # sh --> windows, bash --> ubuntu
                stdin.close()
                stdout_data = stdout.readlines()
                print(stdout_data)
                client_socket.sendall(str("areboot {}, {}".format(platform_name, stdout_data)).encode('utf-8'))
                ssh.close()
        except Exception as e:
            client_socket.sendall(str("areboot {} error, {}".format(platform_name, e)).encode('utf-8'))

    def aregUser(self, client_socket, user_name, user_pwd):
        """
        a --> "a" means admin function
          --> shutdown means 

        :param client_socket (object) : socket object
        :param user_name (str) : userName ex) HJ, NY...
        :param job_id (int) : generated jobID ex) 1,2,...
        """
        pass

    def adelUser(self, client_socket, user_name):
        """
        a --> "a" means admin function
          --> shutdown means 

        :param client_socket (object) : socket object
        :param user_name (str) : userName ex) HJ, NY...
        :param job_id (int) : generated jobID ex) 1,2,...
        """
        pass

    def amodUser(self, client_socket, user_name):
        """
        a --> "a" means admin function
          --> shutdown means 

        :param client_socket (object) : socket object
        :param user_name (str) : userName ex) HJ, NY...
        :param job_id (int) : generated jobID ex) 1,2,...
        """
        pass