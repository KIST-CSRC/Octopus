import socket
import json
from prettytable import PrettyTable
from Log.Logging_Class import JobLogger

class Client:
    """
    [Client] control job & task of client between job_server

    ## function
    
    ### qstat
    :purpose: check status of job_script_queue in job_server & job_exec_queue in task_server --> ex) qstat
    
    ### qsub {jobFileName} {modeType}
    :purpose: read USER_{USER_NAME}/job_script/{jobFileName}.json & submit job_script to job_server --> ex) qsub 20230516_autonomous virtual

    :param jobFileName: input filename of json file. --> ex) {20230516_autonomous}.json
    :param modeType: input "real" or "virtual --> ex) real or virtual
    
    ### qdel {jobID}
    :purpose: kill job in job_script_queue of job_server (job_server에 걸려있던 job을 kill, 진행중인 job들을 일제히 중단 {모든 hardware platform에 qhold가 날라오면 raise error시키기}) --> ex) qdel 0
    
    :param jobID: jobID. --> ex) 0
    
    ### qhold {jobID}
    :purpose: hold job in job_exec_queue of task_server (진행중인 들을 일제히 중단-->모든 hardware platform에 qhold가 날라오면 raise error시키기) --> ex) qhold 0
    
    :param jobID: jobID. --> ex) 0
    
    ### qrestart {jobID}
    :purpose: restart job in job_exec_queue of task_server --> ex) qrestart 0
    
    :param jobID: input jobID. --> ex) 0
    
    ### qlogout 
    :purpose: logout from job_server --> ex) qlogout
    
    """

    def __init__(self, log_level):
        self.client_logger=JobLogger("JobClient", log_level)
        self.BUFF_SIZE=4096

    def __checkJSON(self, job_script):
        """
        add later
        """
        return job_script

    def __readJSON(self, job_script_path):
        try: 
            with open(job_script_path, "r") as f:
                job_script_file = json.load(f)
                job_script_file=self.__checkJSON(job_script_file)
            return job_script_file
        except FileNotFoundError as e:
            self.client_logger.info("Client", "path error : {}".format(e))
            return False

    def __compressJSON(self, json_obj):
        json_file=json.dumps(json_obj)

        return json_file

    def __sendRecv(self,client_socket, command_byte):

        client_socket.sendall(command_byte)
        message_recv = b''
        while True:
            part = client_socket.recv(self.BUFF_SIZE)
            message_recv += part
            if len(part) < self.BUFF_SIZE:
                break
            else:
                raise ConnectionError("Wrong tcp message")
        decoded_message_recv=message_recv.decode("utf-8")

        return decoded_message_recv

    def updateNode(self, client_socket, user_name):
        """
        kill job in job_script_queue of job_server (job_server에 걸려있던 job을 kill, 진행중인 job들을 일제히 중단 {모든 hardware platform에 qhold가 날라오면 raise error시키기}) --> ex) qdel 0
        
        :param client_socket (object) : client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        :param user_name (str) : username
        """
        command_byte=str.encode("updateNode")
        self.client_logger.info(user_name, "request to update Node Server")

        decoded_message_recv=self.__sendRecv(client_socket, command_byte)
        self.client_logger.info(user_name, decoded_message_recv)

    def qsub(self, client_socket, job_script_filename, user_name, mode_type):
        """
        read USER_{USER_NAME}/job_script/{jobFileName}.json & submit job_script to job_server --> ex) qsub 20230516_autonomous virtual

        :param client_socket (object) : client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        :param job_script_filename (str) : user's job_script filename
        :param user_name (str) : username
        :param mode_type (str) : user's job_script mode_type (it affects to job execution files)
        """
        job_script_path="USER/{}/job_script/{}.json".format(user_name, job_script_filename)
        self.client_logger.info(user_name, "request to submit job : {}".format(job_script_path))

        job_script_dict=self.__readJSON(job_script_path)
        if mode_type=="real" or mode_type=="virtual":
            if type(job_script_dict)==dict:
                command_byte=str.encode("qsub?{}?{}?{}?{}".format(user_name, job_script_filename, job_script_dict, mode_type))
            
                decoded_message_recv=self.__sendRecv(client_socket, command_byte)
                self.client_logger.info(user_name, decoded_message_recv)
            else:
                pass
        else:
            self.client_logger.info(user_name, "Wrong mode type. Please insert correct mode type. ex) virtual, real")

    def qdel(self, client_socket, job_id, user_name):
        """
        kill job in job_script_queue of job_server (job_server에 걸려있던 job을 kill, 진행중인 job들을 일제히 중단 {모든 hardware platform에 qhold가 날라오면 raise error시키기}) --> ex) qdel 0
        
        :param client_socket (object) : client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        :param job_id (int or str) : user's jobID
        :param user_name (str) : username
        """
        command_byte=str.encode("qdel?{}".format(job_id))
        self.client_logger.info(user_name, "request to delete job (jobID:{})".format(job_id))

        decoded_message_recv=self.__sendRecv(client_socket, command_byte)
        self.client_logger.info(user_name, decoded_message_recv)

    def qhold(self, client_socket, job_id, user_name):
        """
        hold job in job_exec_queue of task_server (진행중인 들을 일제히 중단-->모든 hardware platform에 qhold가 날라오면 raise error시키기) --> ex) qhold 0

        :param client_socket (object) : client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        :param job_id (int or str) : user's jobID
        :param user_name (str) : username
        """
        command_byte=str.encode("qhold?{}".format(job_id))
        self.client_logger.info(user_name, "request to hold job (jobID:{})".format(job_id))

        decoded_message_recv=self.__sendRecv(client_socket, command_byte)
        self.client_logger.info(user_name, decoded_message_recv)

    def qrestart(self, client_socket, job_id, user_name):
        """
        restart job in job_exec_queue of task_server

        :param client_socket (object) : client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        :param job_id (int or str) : user's jobID
        :param user_name (str) : username
        """
        command_byte=str.encode("qrestart?{}".format(job_id))
        self.client_logger.info(user_name, "request to restart job (jobID:{})".format(job_id))

        decoded_message_recv=self.__sendRecv(client_socket, command_byte)
        self.client_logger.info(user_name, decoded_message_recv)

    def qstat(self, client_socket, user_name):
        """
        check status of job_script_queue in job_server & job_exec_queue in task_server --> ex) qstat
        
        :param client_socket (object) : client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        :param user_name (str) : username
        """
        command_byte=str.encode("qstat")
        self.client_logger.info(user_name, "request to check job status")

        decoded_message_recv=self.__sendRecv(client_socket, command_byte)
        # self.client_logger.info(user_name, decoded_message_recv)

        total_row=eval(decoded_message_recv)

        myTable = PrettyTable()
        myTable.field_names = ["userName", "jobTime", "jobID", "jobFileName", "current", "total", "status", "modeType"]
        for row in total_row:
            myTable.add_row(row)
        # 정렬 설정
        myTable.sortby = "jobID"  # 나이 열을 기준으로 정렬
        myTable.reversesort = True  # 내림차순 정렬
        print(myTable)

        self.client_logger.info(user_name, "succeed to check job status")

    def qlogout(self, client_socket, user_name):
        """
        [Job Queue function] logout from job_server --> ex) qlogout
        
        :param client_socket (object) : client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        :param user_name (str) : username
        """
        command_byte=str.encode("qlogout")
        self.client_logger.info(user_name, "request to logout")

        decoded_message_recv=self.__sendRecv(client_socket, command_byte)
        self.client_logger.info(user_name, "succeed to logout")

    def ashutdown(self, client_socket, platform_name):
        """
        [Admin function] shutdown platform or all platform

        :param client_socket (object) : client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        :param platform_name (str) : BATCH, FLOW, INK, WASHING, MOBILE, RDE, ALL
        """
        command_byte=str.encode("ashutdown?{}".format(platform_name))
        self.client_logger.info("Admin", "request to shutdown platform:{}".format(platform_name))

        decoded_message_recv=self.__sendRecv(client_socket, command_byte)
        self.client_logger.info("Admin", decoded_message_recv)

    def areboot(self, client_socket, platform_name):
        """
        [Admin function] reboot platform or all platform

        :param client_socket (object) : client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        :param platform_name (str) : BATCH, FLOW, INK, WASHING, MOBILE, RDE, ALL
        """
        command_byte=str.encode("areboot?{}".format(platform_name))
        self.client_logger.info("Admin", "request to reboot platform:{}".format(platform_name))

        decoded_message_recv=self.__sendRecv(client_socket, command_byte)
        self.client_logger.info("Admin", decoded_message_recv)

    def aregUser(self, client_socket, user_name, user_password):
        """
        [Admin function] register new user

        :param client_socket (object) : client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        :param user_name (str) : user name
        :param user_password (str) : user password
        """
        command_byte=str.encode("aregUser?{}?{}".format(user_name, user_password))
        self.client_logger.info("Admin", "request to register new user (user_name:{})".format(user_name))

        decoded_message_recv=self.__sendRecv(client_socket, command_byte)
        self.client_logger.info("Admin", decoded_message_recv)

    def adelUser(self, client_socket, user_name, user_password):
        """
        [Admin function] restart job in job_exec_queue of task_server

        :param client_socket (object) : client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        """
        command_byte=str.encode("adelUser?{}?{}".format(user_name, user_password))
        self.client_logger.info("Admin", "request to delete new user (user_name:{})".format(user_name))

        decoded_message_recv=self.__sendRecv(client_socket, command_byte)
        self.client_logger.info("Admin", decoded_message_recv)
    
    def amodUser(self, client_socket, user_name, user_password, modified_part, modified_content):
        """
        [Admin function] restart job in job_exec_queue of task_server

        :param client_socket (object) : client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        :param modified_part (str) : modified part ex) id, password
        :param modified_content (str) : modified content ex) modified id or modified password
        """
        command_byte=str.encode("amodUser?{}?{}?{}?{}".format(user_name, user_password, modified_part, modified_content))
        self.client_logger.info("Admin", "request to modify user (user_name:{}, modified_part:{})".format(user_name, modified_part))

        decoded_message_recv=self.__sendRecv(client_socket, command_byte)
        self.client_logger.info("Admin", decoded_message_recv)


def start_client():
    JOB_HOST = '127.0.0.1'  # 서버의 IP 주소
    JOB_PORT = 5555
    LOG_LEVEL = "DEBUG"
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((JOB_HOST, JOB_PORT))
    
    # 서버로부터 메시지 수신 및 전송
    while True:
        data=client_socket.recv(4096).decode()
        user_name = input("{}: ".format(data))
        client_socket.sendall(str.encode(user_name))

        data=client_socket.recv(4096).decode()
        password = input("{}: ".format(data))
        client_socket.sendall(str.encode(password))

        login_data = client_socket.recv(4096).decode()

        if login_data=="login success":
            print(f"Server: {login_data}")
            Client_obj=Client(LOG_LEVEL)
            break
        elif login_data == "login failure":
            print(f"Server: {login_data}")

    while True:
        try:
            message = input("input commands (if terminate: input 'qlogout'): ")
            if message == "qstat":
                Client_obj.qstat(client_socket, user_name)

            elif "qhold" in message:
                action, job_id = message.split()
                Client_obj.qhold(client_socket, job_id, user_name)

            elif "qdel" in message:
                action, job_id = message.split()
                Client_obj.qdel(client_socket, job_id, user_name)

            elif "qrestart" in message:
                action, job_id = message.split(" ")
                Client_obj.qrestart(client_socket, job_id, user_name)

            elif "qsub" in message:
                action, job_script_path, mode_type = message.split(" ")
                Client_obj.qsub(client_socket, job_script_path, user_name, mode_type)

            elif "ashutdown" in message:
                action, platform_name = message.split()
                Client_obj.ashutdown(client_socket, platform_name, user_name)

            elif "areboot" in message:
                action, platform_name = message.split()
                Client_obj.areboot(client_socket, platform_name, user_name)

            elif "aregUser" in message:
                _, user_name, user_password = message.split("?")
                Client_obj.aregUser(client_socket, user_name, user_password)

            elif "adelUser" in message:
                _, user_name, user_password = message.split("?")
                Client_obj.adelUser(client_socket, user_name, user_password)

            elif "amodUser" in message:
                _, user_name, user_password, modified_part, modified_content = message.split("?")
                Client_obj.amodUser(client_socket, user_name, user_password, modified_part, modified_content)

            elif "updateNode" in message:
                Client_obj.updateNode(client_socket, user_name)

            elif message == 'qlogout':
                Client_obj.qlogout(client_socket, user_name)
                break

            elif message == "qhelp":
                print(help(Client))

            else:
                print("Please enter proper name of function")

        except ValueError as e:
            print("Please enter proper job id, error code : {}".format(e))

    client_socket.close()

start_client()
