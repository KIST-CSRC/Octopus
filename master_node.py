import socket
import threading
import json
from Log.Logging_Class import JobLogger
from UserManager.UserManager_Class import UserManager
from Job.JobScheduler_Class import JobScheduler
from Job.JobTrigger import JobTrigger
from Task.TaskGenerator_Class import TaskGenerator
from Task.TaskScheduler_Class import TaskScheduler
from Resource.ResourceManager_Class import ResourceManager

def handle_client(client_socket, client_address, server_logger, JobScheduler_obj):
    try:
        server_logger.info("Master", f"{client_address} is connected.")
        user_manager_obj=UserManager() # include user information
        
        # connect with Client
        while True:
            # input id
            client_socket.sendall(str.encode('Please enter your id: '))
            username = client_socket.recv(4096).decode()

            # input password
            client_socket.sendall(str.encode('Please enter your password: '))
            password = client_socket.recv(4096).decode()
            
            # verify id, password
            login_status=user_manager_obj.matchPassword(username, password)
            if login_status == "login success":
                client_socket.sendall(login_status.encode('utf-8'))
                server_logger.info("Master", "login status:{}, username:{}".format(login_status, username))
                break
            else:
                client_socket.sendall(login_status.encode('utf-8'))
                server_logger.info("Master", "login status:{}, username:{}".format(login_status, username))
        
        while True:
            command_byte = client_socket.recv(4096).decode('utf-8')
            if "qstat" in command_byte:
                JobScheduler_obj.qstat(client_socket)
            elif "qhold" in command_byte:
                _, job_id = command_byte.split("?")
                job_id=int(job_id)
                JobScheduler_obj.qhold(client_socket, username, job_id)
            elif "qdel" in command_byte:
                _, job_id = command_byte.split("?")
                job_id=int(job_id)
                JobScheduler_obj.qdel(client_socket, username, job_id)
            elif "qrestart" in command_byte:
                _, job_id = command_byte.split("?")
                job_id=int(job_id)
                JobScheduler_obj.qrestart(client_socket, username, job_id)
            elif "qsub" in command_byte:
                _, user_name, job_script_filename, job_script_str, mode_type= command_byte.split("?", maxsplit=4)
                json_acceptable_string = job_script_str.replace("'", "\"") # if job script has ` or " in path-->need to modify
                job_script_dict=json.loads(json_acceptable_string)
                JobScheduler_obj.qsub(client_socket, user_name, job_script_filename, job_script_dict, mode_type)
            elif "ashutdown" in command_byte:
                _, platform_name = command_byte.split("?")
                JobScheduler_obj.ashutdown(client_socket, platform_name)
            elif "areboot" in command_byte:
                _, platform_name = command_byte.split("?")
                JobScheduler_obj.areboot(client_socket, platform_name)
            elif "aregUser" in command_byte:
                _, user_name, user_password = command_byte.split("?")
                JobScheduler_obj.aregUser(client_socket, user_name, user_password)
            elif "adelUser" in command_byte:
                _, user_name, user_password = command_byte.split("?")
                JobScheduler_obj.adelUser(client_socket, user_name, user_password)
            elif "amodUser" in command_byte:
                _, user_name, user_password, modified_part, modified_content = command_byte.split("?")
                JobScheduler_obj.amodUser(client_socket, user_name, user_password, modified_part, modified_content)
            elif "updateNode" in command_byte:
                JobScheduler_obj.updateNode(client_socket)
            elif "qlogout" in command_byte:
                client_socket.sendall("okay. Bye~".encode('utf-8'))
                break
            else:
                data="Error commands : {}".format(command_byte)
                client_socket.sendall(data.encode('utf-8'))
                server_logger.info("Master", "Error commands: {}".format(command_byte))
            
            server_logger.info("Master", "{} {}: {}".format(username, client_address, command_byte))
        server_logger.info("Master", "{} {}: Connection was closed.".format(username, client_address))
        client_socket.close()

    except ConnectionAbortedError as e:
        server_logger.info("Master", "{} {}: Connection was forcibly closed.".format(username, client_address))


def executeJob(JobTrigger_obj, job_schedule_mode, job_wait_queue, job_exec_queue, TaskScheduler_obj, TaskGenerator_obj, ResourceManager_obj):
    while True:
        # if len(job_wait_queue)>0:
        # Scheduling algorithm에 맞는 job script pop
        popped_job_queue=getattr(JobTrigger_obj, job_schedule_mode)(job_wait_queue, job_exec_queue, ResourceManager_obj)
        if type(popped_job_queue)==None or len(popped_job_queue)==0:
            pass
        elif len(popped_job_queue)!=0:
            # define Start jobExecution function
            def startExecution(input_job_exec_obj, input_job_exec_queue, input_TaskScheduler_obj, input_TaskGenerator_obj):
                input_job_exec_queue.append(input_job_exec_obj)
                input_job_exec_obj.execute(input_TaskScheduler_obj, input_TaskGenerator_obj)
                input_job_exec_queue.remove(input_job_exec_obj)
            
            # generate thread
            thread_list=[]
            for _ in range(len(popped_job_queue)): # popped_job_queue is empty --> will not execute for loop, seems like pass
                popped_job_exec_obj=popped_job_queue.pop(0)
                thread = threading.Thread(target=startExecution, args=(popped_job_exec_obj, job_exec_queue, TaskScheduler_obj, TaskGenerator_obj))
                thread_list.append(thread)
            # start thread
            for thread in thread_list: 
                thread.start()
            # main thread wait thread termination
            for thread in thread_list:
                thread.join()
        else:
            pass


# def executeJob(JobTrigger_obj, job_schedule_mode, job_wait_queue, job_exec_queue, TaskScheduler_obj, TaskGenerator_obj, ResourceManager_obj):
#     while True:
#         # Scheduling algorithm에 맞는 job script pop
#         popped_job_exec_obj=getattr(JobTrigger_obj, job_schedule_mode)(job_wait_queue, job_exec_queue, ResourceManager_obj)
        
#         # define Start jobExecution function
#         def startExecution(input_job_exec_obj, input_job_exec_queue, input_TaskScheduler_obj, input_TaskGenerator_obj):
#             input_job_exec_queue.append(input_job_exec_obj)
#             input_job_exec_obj.execute(input_TaskScheduler_obj, input_TaskGenerator_obj)
#             input_job_exec_queue.remove(input_job_exec_obj)
#         # generate thread
#         thread_list=[]
#         thread = threading.Thread(target=startExecution, args=(popped_job_exec_obj, job_exec_queue, TaskScheduler_obj, TaskGenerator_obj))
#         thread_list.append(thread)
#         # start thread
#         for thread in thread_list: 
#             thread.start()
#         # main thread wait thread termination
#         for thread in thread_list:
#             thread.join()

def start_server():
    SERVER_HOST=''  # permit from all interfaces
    SERVER_PORT=5555 # if you want, can change
    SERVER_ACCESS_NUM=100 # permit to accept the number of maximum client
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 20)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 20)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(SERVER_ACCESS_NUM) # permit to accept 
    server_logger=JobLogger("Master", "DEBUG")
    # server_logger=JobLogger("Master", "INFO")

    ########################################################
    # status of all components (queue, hardware, location) #
    ########################################################
    job_wait_queue = [] # use list type due to access index & changing job sequence from priority
    job_exec_queue = [] # job script file --> JobExecution object in list
    job_hold_queue = [] # holded JobExecution object in list
    
    ##################################
    # mode type of scheduling system #
    ##################################
    # schedule_mode="FCFS"
    # schedule_mode="Backfill"
    schedule_mode="ClosedPacking" 

    ###################
    # generate object #
    ###################
    ResourceManager_obj=ResourceManager(server_logger)
    TaskGenerator_obj=TaskGenerator(server_logger, ResourceManager_obj)
    TaskScheduler_obj=TaskScheduler(server_logger, ResourceManager_obj, schedule_mode)
    JobScheduler_obj=JobScheduler(server_logger, job_wait_queue, job_exec_queue, job_hold_queue, ResourceManager_obj)
    JobTrigger_obj=JobTrigger()

    print("[Master] Server on at {}:{}.".format(SERVER_HOST, SERVER_PORT))
    print("[Master] Waiting...")
    
    while True:
        # start JobExecution handler thread (while loop, always proceed)
        client_thread_1 = threading.Thread(target=executeJob, args=(JobTrigger_obj, schedule_mode, job_wait_queue, job_exec_queue, TaskScheduler_obj, TaskGenerator_obj, ResourceManager_obj))
        client_thread_1.start()
        # start Client handler thread (while loop, wait for client request)
        client_socket, client_address = server_socket.accept()
        client_thread_2 = threading.Thread(target=handle_client, args=(client_socket, client_address, server_logger, JobScheduler_obj))
        client_thread_2.start()

start_server()

###############
# port block? #
###############

# >>> sudo lsof -i :5555
# COMMAND   PID     USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
# python  96988 sdl-main    3u  IPv4 975995      0t0  TCP localhost:5555 (LISTEN)
# python  96988 sdl-main    5u  IPv4 976000      0t0  TCP localhost:5555->localhost:57954 (CLOSE_WAIT)
# >>> sudo kill -9 96988

stirrer_list=[
    posx(-251.000, 628.000, 315.300, 0, -180, 135),
    posx(-217.500, 628.100, 315.500, 0, -180, 135),
    posx(-171.100, 627.980, 316.010, 0, -180, 135),
    posx(-135.700, 627.500, 316.010, 0, -180, 135),
    posx(-252.800, 593.200, 316.010, 0, -180, 135),
    posx(-217.800, 592.500, 316.010, 0, -180, 135),
    posx(-172.000, 592.000, 316.010, 0, -180, 135),
    posx(-136.700, 592.500, 316.030, 0, -180, 135),
    posx(-253.000, 547.600, 316.000, 0, -180, 135),
    posx(-218.300, 547.000, 316.010, 0, -180, 135),
    posx(-172.990, 546.300, 316.020, 0, -180, 135),
    posx(-137.400, 545.700, 316.010, 0, -180, 135),
    posx(-253.300, 512.800, 316.010, 0, -180, 135),
    posx(-218.400, 512.200, 316.020, 0, -180, 135),
    posx(-172.490, 512.000, 316.020, 0, -180, 135),
    posx(-138.000, 510.500, 316.000, 0, -180, 135)
]

