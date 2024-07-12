import openai
import re
import os, time
import ast
from prettytable import PrettyTable
from pydantic import BaseModel, constr, conint, conlist, ValidationError
from datetime import datetime

def GPT_generate_module_deviceserver(formatted_time:str, author:str, input_module_name:str, device_list:list, api_key:str, gpt_on=False):

    def convert_device_name(device_list):
        converted_device_list = []
        for device_name in device_list:
            words = device_name.split()
            capitalized_words = [word.capitalize() for word in words]
            joined_words = ''.join(capitalized_words)
            converted_device_list.append(joined_words)
        return converted_device_list

    def extract_code_py(input_string:str):
        try:
            filename_pattern = re.compile(r'\*\*(.*?)\*\*', re.DOTALL)
            filecontent_pattern = re.compile(r'```python(.*?)```', re.DOTALL)
            filename_list = filename_pattern.findall(input_string)
            filecontent_list = filecontent_pattern.findall(input_string)
            code_dict = {}
            for i, filename in enumerate(filename_list):
                filename=filename.replace(".py", "")
                code_dict[filename] = filecontent_list[i]
            return code_dict
        except IndexError:
            IndexError("GPT results has wrong pattern of code generation. It should get **RoboticArm.py**, ```python``")

    def extract_code_json(input_string:str):
        try:
            filecontent_pattern = re.compile(r'```json(.*?)```', re.DOTALL)
            filecontent_list = filecontent_pattern.findall(input_string)
            filecontent=filecontent_list[0]
            dictionary = ast.literal_eval(filecontent)
            return dictionary
        except IndexError:
            IndexError("GPT results has wrong pattern of code generation. It should get **RoboticArm.py**, ```python``")

    def display_action_list(name, input_action_dict):
        all_device_actiontype_table = PrettyTable()
        all_device_actiontype_table.field_names = ["idx", name, "action types recommended by GPT"]
        all_device_actiontype_table.align = "l" 
        for idx, key in enumerate(input_action_dict.keys(), 1):
            all_device_actiontype_table.add_row([idx, key, input_action_dict[key]])
        print(all_device_actiontype_table)

    def get_user_input():
        user_input = input("Select the device index you want to modify (enter 'done' to finish, 'back' to return): ").strip()
        if user_input.lower() in ['done', 'back']:
            return user_input.lower()
        else:
            try:
                return int(user_input)
            except ValueError:
                print("Invalid input, please enter a index, 'done', or 'back'.")
                return None

    def add_action(input_action_dict:dict, input_device_name:str):
        new_action = input("Enter the new action to add (or 'back' to return): ").strip().capitalize()
        if new_action.lower() == 'back':
            return input_action_dict, 'back'
        input_action_dict[input_device_name].append(new_action)
        print(f"Action '{new_action}' added to {input_device_name}.")
        return input_action_dict, None

    def modify_action(input_action_dict:dict, input_device_name:str, input_action_to_modify_index:int):
        input_action_to_modify=input_action_dict[input_device_name][input_action_to_modify_index-1]
        while True:
            new_action = input(f"Enter the new action_type to replace '{input_action_to_modify}' (or 'done' to finish, 'back' to return): ").strip().lower()
            if new_action == 'done' or new_action == 'back':
                return input_action_dict, None
            else:
                input_action_dict[input_device_name][input_action_to_modify_index-1] = new_action.capitalize()
                print(f"Action '{input_action_to_modify}' modified to '{new_action}' in {input_device_name}.")
                return input_action_dict, None

    def delete_action(input_action_dict:dict, input_device_name:str, input_action_to_delete_index:int):
        deleted_action_type=input_action_dict[input_device_name][input_action_to_delete_index-1]
        confirm = input(f"Are you sure you want to delete action '{deleted_action_type}'? ('y'/'n', 'back' to return): ").strip().lower()
        if confirm == 'back':
            return input_action_dict, 'back'
        if confirm == 'y':
            if 1 <= input_action_to_delete_index <= len(input_action_dict[input_device_name]):
                input_action_dict[input_device_name].pop(input_action_to_delete_index-1)
                print(f"Action '{deleted_action_type}' deleted from {input_device_name}.")
            else:
                print(f"Action '{deleted_action_type}' not found in {input_device_name}.")
        else:
            print("Deletion canceled.")
        return input_action_dict, None
    
    openai.api_key = api_key
    converted_device_list=convert_device_name(device_list)
    device_str=""
    for idx, arg in enumerate(converted_device_list):
        device_str+=arg
        if idx != len(converted_device_list)-1:
            device_str+=", "
    ###################################
    # generate actions of all devices #
    ###################################
    print("###################")
    print("[GPT (ModuleNode or DeviceServer)]: action generation for devices...")
    print("###################")
    messages=[
        {
            "role": "system",
            "content": """You are administrator of autonomous laboratory, which control AI and robotics for chemical experiments, 
            and your role is the module generation for chemical experiments execution with chemical devices.""",
        },
        {
            "role": "user",
            "content":f"""
            chemical actions define as "simple word for devices action, not over 2 words", such as stirrer has "Stir", "Heat", "Stop" actions.
            "pipette draw" or "move to position" is wrong action name.
            The first letter of the action must always be captialized.
            
            Please recommend various actions for each device listed below:
            {device_str}.
            
            Please save as json, and key of json is device name, value of json is action list.
            """,
        }
            # please generate actions for controlling chemical devices in {name}. 
            # You must not combine between devices or regenerate new device name. 
            # For example, when you get "Robot arm" and "Pipette", don't combine or regenerate "RobotArmPipette".
    ]
    if gpt_on==True:
        completion = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",  # 사용할 GPT 모델 엔진
            # prompt=question,
            # max_tokens=150,  # 생성할 응답의 최대 토큰 수
            # n=1,  # 생성할 응답 수
            # stop=None,  # 응답 생성 중단 시퀀스
            temperature=0,  # 응답의 창의성 (0.0~1.0)
            messages=messages
        )
        answer = completion.choices[0].message.content
        print(completion.usage)

        with open(f"AutoModuleGeneration/GPT_answer_generation/{input_module_name}_actions.txt", 'w') as file:
            file.write(answer)
    else:
        with open(f'AutoModuleGeneration/GPT_answer_generation/{input_module_name}_actions.txt', 'r', encoding='utf-8') as file:
            answer = file.read()
    answer_dict={"role": "assistant", "content": answer}
    messages.append(answer_dict)
    ############################################
    # add/modify/delete actions of all devices #
    ############################################
    device_action_dict=extract_code_json(answer)

    print("\n###################")
    print("[Feedback system (action generation)]")
    print("###################")

    while True:
        print("\n###############")
        print(f"Recommended {input_module_name}'s device action")
        print("###############\n")
        display_action_list(input_module_name, device_action_dict)
        user_input = get_user_input()
        
        if user_input == 'done':
            break
        if user_input is None or user_input == 'back':
            continue

        index = user_input - 1
        keys = list(device_action_dict.keys())
        device_name = keys[index]

        device_actiontype_table = PrettyTable()
        device_actiontype_table.field_names = ["idx", f"{device_name} --> action recommended by GPT"]
        device_actiontype_table.align = "l" 
        for idx, action_type in enumerate(device_action_dict[device_name], 1):
            device_actiontype_table.add_row([idx, action_type])
        print(device_actiontype_table)

        action = input("Do you want to add, modify or delete a action_type? ('a'/'m'/'d' or 'back' to return): ").strip().lower()
        
        if action == 'back':
            continue
        elif action == 'a':
            device_action_dict, back = add_action(device_action_dict, device_name)
            if back == 'back':
                continue
        elif action == 'm':
            try:
                action_to_modify = input(f"Enter the action index to modify in {device_name} (or 'back' to return): ").strip()
                if action_to_modify.lower() == 'back':
                    continue
                else:
                    device_action_dict, back = modify_action(device_action_dict, device_name, int(action_to_modify))
                    if back == 'back':
                        continue
            except ValueError as e:
                print("Please input action index via int, or only 'back': ", e)
        elif action == 'd':
            task_to_delete = input(f"Enter the action index to delete in {device_name} (or 'back' to return): ").strip()
            if task_to_delete.lower() == 'back':
                continue
            device_action_dict, back = delete_action(device_action_dict, device_name, int(task_to_delete))
            if back == 'back':
                continue
        else:
            print("Invalid action, please try again.")

    print("\n###############")
    print(f"Final {input_module_name}'s device action type")
    print("###############\n")
    display_action_list(input_module_name, device_action_dict)
    #########################################################
    # generate device class, referred by device_action_dict #
    #########################################################
    code_dict={}
    for device_name, action_list in device_action_dict.items():
        code_script="""# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [{device_name}] {device_name} class with action function 
# author {author}
# GENEREATION {formatted_time}

import sys
        

class {device_name}:

    def __init__(self, logger_obj, device_name="{device_name}"):
        ################################################################################################
        # Please configure the device information according to the {device_name} manufacturer guidelines.
        # ex) self.info['Port']='COM3' or '/dev/ttyUSB0'
        # ex) self.info['BaudRate']=9600
        ################################################################################################
        
        self.info={{}}
        self.info['DeviceName']=device_name
        
        self.logger_obj=logger_obj
        self.device_name=device_name

        ################################################################################################
        # Please configure the types of actions according to the {device_name} manufacturer guidelines.
        # if some device is made of yourself (ex. arduino),                                        
        # >>> self.arduinoData = serial.Serial(self.info["Port"], self.info["BaudRate"])           
        # if some device import manufacturer library and generate object in here                 
        # >>> from Tecan import TecanAPI                                                           
        # >>> self.syringe_pump = TecanAPI()                                                       
        ################################################################################################
    
    def heartbeat(self,) -> str:
        debug_device_name='{{}} ({{}})'.format(self.device_name, "heartbeat")

        ############################################################################################
        # Please configure the types of actions according to the {device_name} manufacturer guidelines. 
        ################################################################################################
        
        debug_msg="Hello World!! Succeed to connection to main computer!"
        self.logger_obj.debug(device_name=debug_device_name, debug_msg=debug_msg)

        return_res_msg='[{{}}] : {{}}'.format(self.device_name, debug_msg)
        return return_res_msg
        """.format(device_name=device_name, author=author, formatted_time=formatted_time)
        for action_type in action_list:
            action_func="""
    def {action_type}(self, action_data:str, mode_type:str="virtual") -> str:
        '''
        :param action_data (str) :
        :param mode_type="virtual" (str): set virtual or real mode
        
        :return: return_res_msg
        '''
        current_action_type=sys._getframe().f_code.co_name
        device_name="{{}} ({{}})".format(self.device_name, mode_type)
        debug_msg="Start {{}} action, action_data={{}}".format(current_action_type, action_data)
        self.logger_obj.debug(device_name=device_name, debug_msg=debug_msg)
        action_data_list=action_data.split("&")
        
        if mode_type=="real":
            ############################################################################################
            # Please configure the types of actions according to the device manufacturer guidelines. #
            ############################################################################################
            action_data_list
            pass
        elif mode_type=="virtual":
            pass

        debug_msg="Finish {{}} action, action_data={{}}".format(current_action_type, action_data)
        self.logger_obj.debug(device_name=device_name, debug_msg=debug_msg)
        
        return_res_msg="[{{}}] : {{}}".format(device_name, debug_msg)
        return return_res_msg
""".format(action_type=action_type)
            code_script+=action_func
        code_dict[device_name]=code_script

    # with open(f"AutoModuleGeneration/GPT_answer_generation/GPT_{name}_class.txt", 'w') as file:
    #     file.write(str(code_dict))

    return device_action_dict, code_dict

def save_to_files_deviceserver(module_name:str, device_serve_name:str, code_dict:dict):
    if os.path.isdir(f"AutoModuleGeneration/{module_name}/{device_serve_name}") == False:
        os.makedirs(f"AutoModuleGeneration/{module_name}/{device_serve_name}")
    for device_filename, code in code_dict.items():
        if os.path.isdir(f"AutoModuleGeneration/{module_name}/{device_serve_name}/{device_filename}") == False:
            os.makedirs(f"AutoModuleGeneration/{module_name}/{device_serve_name}/{device_filename}")
    for device_filename, code in code_dict.items():
        # device_filename[:-3] --> delete ".py"
        with open(f"AutoModuleGeneration/{module_name}/{device_serve_name}/{device_filename}/{device_filename}.py", 'w') as file:
            file.write(code)

def save_to_files_modulenode(module_name:str, code_dict:dict):
    if os.path.isdir(f"AutoModuleGeneration/{module_name}") == False:
        os.makedirs(f"AutoModuleGeneration/{module_name}")
    for device_filename, code in code_dict.items():
        if os.path.isdir(f"AutoModuleGeneration/{module_name}/{device_filename}") == False:
            os.makedirs(f"AutoModuleGeneration/{module_name}/{device_filename}")
    for device_filename, code in code_dict.items():
        # device_filename[:-3] --> delete ".py"
        with open(f"AutoModuleGeneration/{module_name}/{device_filename}/{device_filename}.py", 'w') as file:
            file.write(code)

def script_generation_BaseUtils(formatted_time:str, author:str, input_module_name:str, input_device_server_name:str=""):
    script_content_json_func=f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [{input_module_name}] {input_module_name} class file
# author {author}
# GENEREATION {formatted_time}

import json
import socket
import time

class PreprocessJSON(object):

    def openJSON(self, filename):
        """open JSON file to object"""
        with open(filename, 'r') as f:
            json_obj = json.load(f)

        return json_obj

    def encodeJSON(self, json_obj):
        """encode JSON file to bytes --> return ourbyte"""
        ourbyte=b''
        ourbyte = json.dumps(json_obj).encode("utf-8")

        return ourbyte

    def writeJSON(self, filename, json_obj):
        """Linear Actuator IP, PORT, location dict, move_z"""
        with open(filename, "w") as json_file:
            json.dumps(json_obj, json_file)
    '''
    script_content_tcp='''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @brief    [TCP_Class] TCP_Class class file
'''+f'''# author {author}
# GENEREATION {formatted_time}

'''+'''
import json
import socket
import time


class BaseTCPNode(object):

    def __init__(self):
        self.BUFF_SIZE = 4096
    
    def checkSocketStatus(self, client_socket, res_msg, device_name, action_type):
        if bool(res_msg) == True:
            if isinstance(res_msg,dict) or isinstance(res_msg,list):  
                ourbyte=b''
                ourbyte = json.dumps(res_msg).encode("utf-8")
                self._sendTotalJSON(client_socket, ourbyte)
                # send finish message to main computer
                time.sleep(3)
                finish_msg="finish"
                client_socket.sendall(finish_msg.encode())
            else:
                cmd_string_end = "[{}] {} succeed to finish action".format(device_name, action_type)
                client_socket.sendall(cmd_string_end.encode())
        elif bool(res_msg) == False:
            cmd_string_end = "[{}] {} action error".format(device_name, action_type)
            client_socket.sendall(cmd_string_end.encode())
            raise ConnectionError("{} : Please check".format(cmd_string_end))

    def _callServer(self, host, port, command_byte):
        res_msg=""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # receive filename (XXXXXX.json)
            s.connect((host, port))
            time.sleep(1)
            s.sendall(command_byte)
            msg = b''
            while True:
                part = s.recv(self.BUFF_SIZE)
                msg += part
                if len(part) < self.BUFF_SIZE:
                    s.close()
                    break
            res_msg=msg.decode('UTF-8')
        return res_msg
    
    def _sendTotalJSON(self, client_socket, ourbyte):
        cnt=0
        while (cnt+1)*self.BUFF_SIZE < len(ourbyte):
            msg_temp = b""+ourbyte[cnt * self.BUFF_SIZE: (cnt + 1) * self.BUFF_SIZE]
            client_socket.sendall(msg_temp)
            cnt += 1
            print(msg_temp)
        msg_temp = b"" + ourbyte[cnt * self.BUFF_SIZE: len(ourbyte)]
        client_socket.sendall(msg_temp)

class TCP_Class(BaseTCPNode):
    """
    [TCP_Class] TCP Class for controlling another computer

    # (PUMP : Syringe pump)
    - Centris, XCaliburD (Syringe pump)

    # function
    - callServer(command_byte=b'PUMP/single/AgNO3&1500&2000/virtual')
    """

    def __init__(self, device_name, ip, port, NodeLogger_obj):
        BaseTCPNode.__init__(self,)
        self.device_name=device_name
        self.NodeLogger_obj=NodeLogger_obj
        self.ip=ip
        self.port=port

        command_byte_info=str.encode("{}/{}/{}/{}/{}".format(None, device_name, "INFO", "None", "virtual"))
        res_str=self._callServer(self.ip, self.port, command_byte_info)
        res_str_dict = res_str.replace("'", '"') # path 중에 "`"가 있고, '"'가 있음. 이를 수정하기위함
        self.info=json.loads(res_str_dict)

        command_byte=str.encode("{}/{}/{}/{}/{}".format(None, device_name, "ACTION", "None", "virtual"))
        res_str_list=self._callServer(self.ip, self.port, command_byte)
        self.action_type=json.loads(res_str_list)

    def heartbeat(self):
        """
        get connection status using TCP/IP (socket)
        
        :return res_msg (str): "Hello World!! Succeed to connection to main computer!"
        """
        debug_device_name="{} ({})".format(self.device_name, "heartbeat")

        command_byte = str.encode("{}/{}/{}/{}/{}".format(None, self.device_name, "heartbeat", "None", "virtual"))
        res_msg=self._callServer(self.ip, self.port, command_byte)

        self.NodeLogger_obj.debug(device_name=debug_device_name, debug_msg=res_msg)

        return res_msg

    def callServer(self, command_byte=b'DS_B/stirrer_to_holder/{pick_num}&{place_num}/virtual'):
        """
        receive command_byte & send tcp packet using socket

        :param command_byte (byte) =b'PUMP/single/AgNO3&1500&2000/virtual' or
                                    b'DS_B/stirrer_to_holder/{pick_num}&{place_num}/virtual'
        :return: status_message (str)
        """
        debug_device_name="{} ({})".format(self.device_name, "callServer")
        
        res_msg=self._callServer(self.ip, self.port, command_byte)
        self.NodeLogger_obj.debug(device_name=debug_device_name, debug_msg=res_msg)
        return res_msg
    '''
    if len(input_device_server_name)!=0:
        path=f"AutoModuleGeneration/{input_module_name}/{input_device_server_name}"
    else:
        path=f"AutoModuleGeneration/{input_module_name}"
    if os.path.isdir(f"{path}/BaseUtils") == False:
        os.makedirs(f"{path}/BaseUtils")
        time.sleep(2)
    with open(f"{path}/BaseUtils/json_func.py", 'w') as file:
        file.write(script_content_json_func)
    with open(f"{path}/BaseUtils/TCP_Node.py", 'w') as file:
        file.write(script_content_tcp)

def script_generation_logging_class(formatted_time:str, author:str, input_module_name:str, input_device_server_name:str=""):
    script_content=f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @brief    [NodeLogger] Logging Class for controlling our command and log file in Autonomous System Laboratory
# author {author}
# GENEREATION {formatted_time}

'''+'''
import os
import sys
import time
import logging

class NodeLogger(object):
    """
    [NodeLogger] Logging Class for controlling our command and log file to upgrade in Node computer

    # Variable
    :param element (str) : DEFAULT="Ag-Au"
    :param experiment_type (str) : DEFAULT="nanoparticle"
    :param set_level (str) : DEFAULT="INFO"
    :param SAVE_DIR_PATH (str) : DEFAULT="Log"
    :param set_level (str) : "INFO"
    
    # function
    1. setLoggingLevel(self, level)
    2. get_logger(self, total_path)
    3. info(self, part="Doosan M0609", info_msg="info!")
    4. warning(self, part="Doosan M0609", warning_msg="warning!")
    5. error(self, part="Doosan M0609", error_msg="error!")
    """   
    def __init__(self, platform_name="Batch Synthesis Server", setLevel="DEBUG",SAVE_DIR_PATH="Log"):
        
        self.__platform_name=platform_name
        time_str_day=time.strftime('%Y-%m-%d')
        time_str=time.strftime('%Y-%m-%d_%H-%M-%S')
        TOTAL_LOG_FOLDER = SAVE_DIR_PATH+"/"+time_str_day

        if os.path.isdir(TOTAL_LOG_FOLDER) == False:
            os.makedirs(TOTAL_LOG_FOLDER)
        self.__TOTAL_LOG_FILE = os.path.join(TOTAL_LOG_FOLDER, "{}.log".format(time_str))
        self.__setLevel = setLevel

        self.mylogger = logging.getLogger(self.__platform_name)
        self.setLoggingLevel(setLevel)
        formatter_string = '%(asctime)s - %(name)s::%(levelname)s -- %(message)s'
        self.setFileHandler(formatter_string, total_path=self.__TOTAL_LOG_FILE)
        self.setStreamHandler(formatter_string)

        self.cycle_num=1

    def getPlatformName(self):
        """:return: self.__platform_name """
        return self.__platform_name

    def getSetLevel(self):
        """:return: self.__setLevel """
        return self.__setLevel

    def getLogFilePath(self):
        """:return: self.__TOTAL_LOG_FILE"""
        return self.__TOTAL_LOG_FILE

    def setLoggingLevel(self,level="INFO"):
        """
        Set Logging Level

        :param level (str) : "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        :return: None
        """
        try:
            if level == "DEBUG":
                self.mylogger.setLevel(logging.DEBUG)
            elif level == "INFO":
                self.mylogger.setLevel(logging.INFO)
            elif level == "WARNING":
                self.mylogger.setLevel(logging.WARNING)
            elif level == "ERROR":
                self.mylogger.setLevel(logging.ERROR)
            elif level == "CRITICAL":
                self.mylogger.setLevel(logging.CRITICAL)
            else:
                raise ValueError("set_levelError")
        except ValueError as e:
            self.info("[Basic Logger] : set_level is incorrect word!")

    def setStreamHandler(self, formatter_string):
        """
        Sets up the logger object for logging messages
        
        :param formatter_string (str) : logging.Formatter(formatter_string)
        :param total_path (str) : "/home/sdl-pc/catkin_ws/src/doosan-robot/Log/present_time" + a
        :return: None
        """
        stream_handler = logging.StreamHandler()
        logging.basicConfig(format=formatter_string)
        # stream_handler.setFormatter(formatter_string)
        # self.mylogger.addHandler(formatter_string)

    def setFileHandler(self, formatter_string, total_path):
        """
        Sets up the logger object for logging messages

        formatter_string
        :param total_path (str) : "/home/sdl-pc/catkin_ws/src/doosan-robot/Log/present_time" + a
        :return: None
        """
        formatter=logging.Formatter(formatter_string)
        total_file_handler = logging.FileHandler(filename=total_path)
        total_file_handler.setFormatter(formatter)
        self.mylogger.addHandler(total_file_handler)

    def debug(self, device_name="Doosan M0609", debug_msg="debug!"):
        """
        write infomration log message in total.log with debug message and show command

        :param device_name (str) : write hardware machine or software
        :param debug_msg (str) : Message to log
        :return: True
        """

        msg = "[{}] : {}".format(device_name, debug_msg)
        self.mylogger.debug(msg)

        return True

    def info(self, part_name="Synthesis platorm", info_msg="info!"):
        """
        write infomration log message in total.log with info message and show command

        :param part_name (str) : write platorm name
        :param info_msg (str) : Message to log
        :return: True
        """

        msg = "[{}] : {}".format(part_name, info_msg)
        self.mylogger.info(msg)

        return True

    def warning(self, device_name="Doosan M0609", warning_msg="warning!"):
        """
        write warning log message in total.log with warning log and show command

        :param device_name (str) : write hardware machine or software
        :param warning_msg (str) : Message to log
        :return: True
        """

        msg = "[{}] : {}".format(device_name, warning_msg)
        self.mylogger.warning(msg)
        
        return True

    def error(self, device_name="Doosan M0609", error_msg="error!"):
        """
        write error log message in error.log and show command

        :param device_name (str) : write hardware machine or software
        :param error_msg (str) : Message to log
        :return: True
        """

        msg = "[{}] : {}".format(device_name, error_msg)
        self.mylogger.error(msg)

        return True
    '''
    if len(input_device_server_name)!=0:
        path=f"AutoModuleGeneration/{input_module_name}/{input_device_server_name}"
    else:
        path=f"AutoModuleGeneration/{input_module_name}"
    if os.path.isdir(f"{path}/Log") == False:
        os.makedirs(f"{path}/Log")
    with open(f"{path}/Log/Logging_Class.py", 'w') as file:
        file.write(script_content)

def script_generation_module_node(formatted_time:str, author:str, input_module_name:str, device_list:list, ip:str, port:int, input_device_server_config_list:list):
    import_lines=""
    for device_name in device_list:
        import_lines+=f"from {device_name}.{device_name} import {device_name}\n"
    script_content1=f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author {author}
# GENEREATION {formatted_time}

"""+import_lines+"""from Log.Logging_Class import NodeLogger
from BaseUtils.TCP_Node import BaseTCPNode, TCP_Class
import socket
import time, sys
import threading

def handle_client(module_name, input_client_socket, input_NodeLogger_obj,
                    input_base_tcp_node_obj, input_qhold_jobID_list, input_qhold_packet_list, input_restart_jobID_list, obj_dict):
    while True:
        data = input_client_socket.recv(4096)
        if str(data.decode())=='':
            continue
        packet_info = str(data.decode()).split(sep="/")
        input_NodeLogger_obj.info(module_name, "packet information list:"+str(packet_info))

        if packet_info[0]!="qhold" and packet_info[0]!="qrestart" and packet_info[0]!="qdel" and packet_info[0]!="qshutdown" and packet_info[0]!="None":
            jobID, device_name, action_type, action_data, mode_type = packet_info
            jobID=int(jobID)
            if jobID not in input_qhold_jobID_list:
                if isinstance(obj_dict[device_name], TCP_Class): # device server
                    res_msg=obj_dict[device_name].callServer(command_byte=data)
                    input_base_tcp_node_obj.checkSocketStatus(input_client_socket, res_msg, device_name, action_type)
                else:
                    res_msg=getattr(obj_dict[device_name], action_type)(action_data, mode_type)
                    base_tcp_node_obj.checkSocketStatus(input_client_socket, res_msg, device_name, action_type)
            elif jobID in input_qhold_jobID_list:
                input_NodeLogger_obj.info(module_name, "holded jobID:"+str(jobID))
                input_NodeLogger_obj.info(module_name, "current input_qhold_jobID_list:"+str(input_qhold_jobID_list))
                packet_info.append(input_client_socket)
                input_qhold_packet_list[jobID]=packet_info
                while True:
                    time.sleep(1)
                    if input_restart_jobID_list[0] not in input_qhold_jobID_list:
                        pass
                    else:
                        break
                popped_packet_info=input_qhold_packet_list.pop(input_restart_jobID_list[0])
                input_qhold_jobID_list.remove(input_restart_jobID_list[0])
                input_qhold_packet_list.insert(input_restart_jobID_list[0], 0)
                input_restart_jobID_list[0]="?"
                jobID, popped_device_name, popped_action_type, popped_action_data, popped_mode_type, popped_client_socket=popped_packet_info
                if isinstance(obj_dict[popped_device_name], TCP_Class): # device server
                    res_msg=obj_dict[popped_device_name].callServer(command_byte=data)
                    input_base_tcp_node_obj.checkSocketStatus(input_client_socket, res_msg, popped_device_name, popped_action_type)
                else: # no device server
                    res_msg=getattr(obj_dict[popped_device_name], popped_action_type)(popped_action_data, popped_mode_type)
                    base_tcp_node_obj.checkSocketStatus(input_client_socket, res_msg, popped_device_name, popped_action_type)
            else:
                res_msg="["+str(jobID)+"] Packet Error : command_byte is wrong"
                input_base_tcp_node_obj.checkSocketStatus(input_client_socket, res_msg, "jobID", "command_byte is wrong")
                raise ValueError("["+str(jobID)+"] Packet Error : command_byte is wrong")    
        
        elif packet_info[2]=="INFO":
            total_dict = dict()
            for obj_name, obj in obj_dict.items():
                obj.heartbeat()
                total_dict[obj_name]=obj.info
            NodeLogger_obj.debug(module_name, total_dict)
            input_base_tcp_node_obj.checkSocketStatus(input_client_socket, total_dict, "INFO", "getTotalDeviceInformation")

        elif packet_info[2]=="ACTION":
            NodeLogger_obj.debug(module_name, device_action_type_dict)
            input_base_tcp_node_obj.checkSocketStatus(input_client_socket, device_action_type_dict, "ACTION", "getTotalActionType")

        elif packet_info[0]=="qhold":
            input_hold_jobID=int(packet_info[1])
            input_qhold_jobID_list.append(input_hold_jobID)
            res_msg="qhold:jobID ["+str(input_hold_jobID)+"] is holded"
            NodeLogger_obj.debug(module_name, res_msg)
            input_base_tcp_node_obj.checkSocketStatus(input_client_socket, res_msg, "jobID", res_msg)
        
        elif packet_info[0]=="qrestart":
            request_restart_jobID=int(packet_info[1])
            input_restart_jobID_list[0]=request_restart_jobID
            if request_restart_jobID not in input_qhold_jobID_list:
                res_msg="jobID not in input_qhold_jobID_list"
                input_base_tcp_node_obj.checkSocketStatus(input_client_socket, res_msg, "qrestart", res_msg)
            else:
                res_msg="qrestart:jobID ["+str(request_restart_jobID)+"] is restarted".format(request_restart_jobID)
                input_base_tcp_node_obj.checkSocketStatus(input_client_socket, res_msg, "qrestart", res_msg)
        
        elif packet_info[0]=="qdel":
            input_del_jobID=int(packet_info[1])
            input_del_jobID_index=input_qhold_jobID_list.index(input_del_jobID)
            input_qhold_jobID_list.pop(input_del_jobID_index) # initialize index
            input_qhold_packet_list[input_del_jobID_index]="?" # initialize element to "?" (null)
            res_msg="qdel:jobID ["+str(input_del_jobID)+"] is deleted".format(input_del_jobID)
            input_base_tcp_node_obj.checkSocketStatus(input_client_socket, res_msg, "qdel", res_msg)
        
        elif packet_info[0]=="ashutdown":
            NodeLogger_obj.info("node_manager", "ashutdown")
            input_base_tcp_node_obj.checkSocketStatus(input_client_socket, res_msg, "ashutdown", res_msg)
            sys.exit("shutdown")
        
        else:
            raise ValueError("Packet Error : command_byte is wrong"+str(packet_info))


def startModuleNode():
    MODULE_ACCESS_NUM=100 # permit to accept the number of maximum client

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 20)
    server_socket.bind((MODULE_HOST, MODULE_PORT))
    server_socket.listen(MODULE_ACCESS_NUM) # permit to accept 

    print("["+module_name+"] node on at " + MODULE_HOST + ":" + str(MODULE_PORT))
    print("["+module_name+"] Waiting...")
    
    while True:
        # start thread (while loop, wait for client request)
        client_socket, client_address = server_socket.accept()  # 연결 요청을 수락함. 그러면 아이피주소, 포트등 데이터를 return
        client_thread= threading.Thread(target=handle_client, 
                                        args=(module_name, client_socket, NodeLogger_obj, base_tcp_node_obj, qhold_jobID_list, qhold_packet_list, restart_jobID_list, device_obj_dict))
        client_thread.start()
    
# Emergency Stop via Broadcast
def emergencyStop():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((MODULE_HOST, 54010)) # 54010 --> fixed port number of emergency stop 
    print(f"[Emergency Stop] Waiting...")
    
    while True:
        data, addr = udp_socket.recvfrom(1024)
        print("Broadcast data: "+data.decode())
        NodeLogger_obj.info("module node", "emergency stop")
        sys.exit("shutdown")

def getActionType(obj):
    if isinstance(obj, TCP_Class): # device server
        action_types = obj.action_type
    else:
        action_types = [method for method in dir(obj) if callable(getattr(obj, method)) and not method.startswith("__")]
    return action_types


if __name__ == "__main__":
    # TCP/IP
    MODULE_HOST='{ip}'  # set IP address of module node computer
    MODULE_PORT={port} # if you want, can change. but match port number with master node and device server
    module_name='{input_module_name}' # set module name

    NodeLogger_obj = NodeLogger(platform_name=module_name,setLevel="DEBUG",SAVE_DIR_PATH="Log")
    base_tcp_node_obj = BaseTCPNode()

    # Wihtout device server : direct connection with module node
""".format(input_module_name=input_module_name, ip=ip, port=port)
    
    # device (in module) object generation
    object_generation_lines=""
    for device_name in device_list:
        object_generation_lines+=f"    {device_name}_obj = {device_name}(NodeLogger_obj) # please check your device class\n"
    object_generation_lines+="    # Device server\n"
    
    # device server (outside module) object generation
    for device_server_dict in input_device_server_config_list:
        for converted_device_name in device_server_dict["converted_device_name_list"]:
            object_generation_lines+=f"    {converted_device_name}_obj = TCP_Class('{converted_device_name}', '{device_server_dict['HOST']}', {device_server_dict['PORT']}, NodeLogger_obj) # please check your device class\n"
    
    # combined device (in module) object to device server (outside module) in single dictionary
    object_dict_lines="    device_obj_dict={\n"
    for device_name in device_list:
        object_dict_lines+=f'        "{device_name}":{device_name}_obj,\n'
    for device_server_dict in input_device_server_config_list:
        for converted_device_name in device_server_dict["converted_device_name_list"]:
            object_dict_lines+=f'        "{converted_device_name}":{converted_device_name}_obj,\n'
    object_dict_lines+="    }\n"

    script_content2="""
    qhold_jobID_list=[]
    qhold_packet_list=["?"]*100 # [ ['1', 'LA', '...'....] , []] # action
    restart_jobID_list=["?"]

    device_action_type_dict=dict()
    for obj_name, device_obj in device_obj_dict.items():
        action_type_list=getActionType(device_obj)
        device_action_type_dict[obj_name] = action_type_list

    # TCP & UDP generate reception thread
    tcp_thread = threading.Thread(target=startModuleNode)
    udp_thread = threading.Thread(target=emergencyStop)

    # Thread start
    tcp_thread.start()
    udp_thread.start()

    # Thread termination - wait
    tcp_thread.join()
    udp_thread.join()
"""
    total_script_content=script_content1+object_generation_lines+object_dict_lines+script_content2
    with open(f"AutoModuleGeneration/{input_module_name}/module_node.py", 'w') as file:
        file.write(total_script_content)

def script_generation_device_server(formatted_time:str, author:str, input_module_name:str, input_device_server_name:str, device_list:list, ip:str, port:int):
    import_lines=""
    for device_name in device_list:
        import_lines+=f"from {device_name}.{device_name} import {device_name}\n"
    script_content1=f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author {author}
# GENEREATION {formatted_time}

"""+import_lines+"""from Log.Logging_Class import NodeLogger
from BaseUtils.TCP_Node import BaseTCPNode
import socket

def getActionType(obj):
    methods = [method for method in dir(obj) if callable(getattr(obj, method)) and not method.startswith("__")]
    return methods

SIZE = 104857600
device_server_name='{input_device_server_name}'
NodeLogger_obj = NodeLogger(platform_name=device_server_name, setLevel="DEBUG", SAVE_DIR_PATH="Log")
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

base_tcp_node_obj = BaseTCPNode()
server_socket.bind(('{ip}', {port}))  # Specifying IP address and port number
server_socket.listen()  # Waiting for a module node's connection request

""".format(input_device_server_name=input_device_server_name, ip=ip, port=port)
    
    object_generation_lines=""
    for device_name in device_list:
        object_generation_lines+=f"{device_name}_obj = {device_name}(NodeLogger_obj) # please check your device class\n"
    object_dict_lines="device_obj_dict={\n"
    for device_name in device_list:
        object_dict_lines+=f'    "{device_name}":{device_name}_obj,\n'
    object_dict_lines+="}\n"
    
    script_content2="""
device_action_type_dict=dict()
for obj_name, device_obj in device_obj_dict.items():
    action_type_list=getActionType(device_obj)
    device_action_type_dict[obj_name]=action_type_list

try:
    while True:
        client_socket, addr = server_socket.accept()  # Accepting a connection request. This returns data such as IP address and port number.
        data = client_socket.recv(SIZE)  # Receiving data from the client. The output buffer size determines the amount of data transmitted (e.g., if set to 2, only two pieces of data are sent).

        packet_info = str(data.decode()).split(sep="/")
        print("packet information list : ", packet_info)
        job_id, device_name, action_type, action_data, mode_type = packet_info

        if action_type == "INFO": # return device information for each device in device server
            res_msg=device_obj_dict[device_name].info # return dict
        elif action_type == "ACTION": # return action type for each device in device server
            res_msg=device_action_type_dict[device_name] # return list
        else:
            if action_type != "heartbeat":
                res_msg=getattr(device_obj_dict[device_name], action_type)(action_data, mode_type) # return str
            else:
                res_msg=getattr(device_obj_dict[device_name], action_type)() # return str
        base_tcp_node_obj.checkSocketStatus(client_socket, res_msg, device_name, action_type)

except ValueError:
    raise ValueError("[" + device_name + "] Packet Error : device_name is wrong, :"+str(packet_info))
        
except KeyboardInterrupt:
    print('Ctrl + C --> termination')
"""

    total_script_content=script_content1+object_generation_lines+object_dict_lines+script_content2
    with open(f"AutoModuleGeneration/{input_module_name}/{input_device_server_name}/device_server.py", 'w') as file:
        file.write(total_script_content)

class ConfigValidation_DeviceServer(BaseModel):
    server_name: str
    device_type: list
    HOST: str

if __name__ == "__main__":

    #########################
    # please edit this part #
    #########################
    # OpenAI API key setting

    module_node_config={
        "author":"Hyuk Jun Yoo (yoohj9475@kist.re.kr)",
        
        "name":"SolidStateModule",
        "module_type":"Synthesis", # ["Synthesis", "Preprocess", "Evaluation", "Characterization"]
        "module_description":"This module refers to a solid-state synthesis process via powder type.", # More detailed information could improve the quality of GPT generation
        "device_type":["stirrer", "powder dispenser", "weighing machine", "heater", "XRD"],
        
        "task_type":["AddPowder"], # must include this task
        
        "resource":{
            "vialHolder":["?"]*8,
            "heater":["?"]*8,
            "XRD":["?"]*16
        },

        "HOST":"127.0.0.1", # please implement your ip
        "PORT":54009, # Default = 54009, 54010 --> emergency stop PORT
        "gpt_on":True, # True --> using GPT // False --> using previous generated answer (txt file)
    }
    device_server_config_list=[
        {
            "author":"Hyuk Jun Yoo (yoohj9475@kist.re.kr)",
            "name":"RobotArmDeviceServer",
            "device_type":["Robot arm", "Pipette"],
            "HOST":"127.0.0.1", # please implement your ip
            "gpt_on":True, # True --> using GPT // False --> using previous generated answer (txt file)
        },
        {
            "author":"Hyuk Jun Yoo (yoohj9475@kist.re.kr)",
            "name":"PumpDeviceServer",
            "device_type":["Pump"],
            "HOST":"127.0.0.1", # please implement your ip
            "gpt_on":True, # True --> using GPT // False --> using previous generated answer (txt file)
        },
    ]
    for idx in range(len(device_server_config_list)):
        device_server_config_list[idx]["PORT"]=module_node_config["PORT"]+idx+1
    #########################################
    # please edit this part until this line #
    #########################################

    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

    modulenode_device_action_dict={}

    for idx, device_server_config in enumerate(device_server_config_list):
        try:
            _ = ConfigValidation_DeviceServer(**device_server_config)
        except ValidationError as e:
            raise ValidationError(e)
        # with open(f"AutoModuleGeneration/GPT_answer_generation/GPT_{device_server_config['name']}.txt", 'r', encoding='utf-8') as file:
        #     answer = file.read()
        device_action_dict, answer = GPT_generate_module_deviceserver(device_server_config["name"], device_server_config["device_type"], device_server_config["gpt_on"])
        modulenode_device_action_dict.update(device_action_dict)
        # code_dict=extract_code_py(answer)
        device_class_name_list=list(answer.keys())
        # print(device_server_config['name'], device_class_name_list)
        device_server_config_list[idx]["converted_device_name_list"]=device_class_name_list
        save_to_files_modulenode(device_server_config["name"], answer)
        script_generation_logging_class(formatted_time=formatted_time, author=module_node_config["author"],input_module_name=module_node_config["name"],
                                        input_device_server_name=device_server_config["name"])
        script_generation_BaseUtils(formatted_time=formatted_time, author=module_node_config["author"],input_module_name=module_node_config["name"],
                                    input_device_server_name=device_server_config["name"])
        script_generation_device_server(formatted_time=formatted_time, author=module_node_config["author"],input_module_name=module_node_config["name"],
                                        input_device_server_name=device_server_config["name"], device_list=device_class_name_list, 
                                        ip=device_server_config["HOST"], port=device_server_config["PORT"])

    try:
        _ = ConfigValidation_DeviceServer(**module_node_config)
    except ValidationError as e:
        raise ValidationError(e)
    # with open(f'AutoModuleGeneration/GPT_answer_generation/GPT_{module_node_config["name"]}.txt', 'r', encoding='utf-8') as file:
    #     answer_module = file.read()
    device_action_dict, answer_module = GPT_generate_module_deviceserver(module_node_config["name"], module_node_config["device_type"], module_node_config["gpt_on"])
    modulenode_device_action_dict.update(device_action_dict)
    # code_dict_module=extract_code_py(answer_module)
    device_class_name_list=list(answer_module.keys())
    # print(module_node_config["name"], device_class_name_list)
    save_to_files_modulenode(module_node_config["name"], answer_module)
    script_generation_logging_class(formatted_time=formatted_time, author=module_node_config["author"],input_module_name=module_node_config["name"])
    script_generation_BaseUtils(formatted_time=formatted_time, author=module_node_config["author"],input_module_name=module_node_config["name"])
    script_generation_module_node(formatted_time=formatted_time, author=module_node_config["author"],
                                input_module_name=module_node_config["name"], device_list=list(answer_module.keys()), 
                                ip=module_node_config["HOST"], port=module_node_config["PORT"],
                                input_device_server_config_list=device_server_config_list)
