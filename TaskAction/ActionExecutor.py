#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [ActionExecutor] ActionExecutor Class for controlling another computer (windows, ubuntu)
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)
# @version  2_1      
# TEST 2021-09-23 // 2022-01-17

import socket, json
import time

class ParameterTCP:
    """
    TCP information : to protect our system due to hacker
    
    internal network : 192.168.{big process type}.{module index}
        def big process type: Synthesis:1, Preprocess:2, Evaluation:3, Charaterization:4, Database:5
        def module index : Synthesis:{"BatchSynthesis":11, "FlowSyntheis":12, "SolvothermalSynthesis":13...}

    - (AMR_HOST : Doosan Robotics + Omron) 
    - (BATCH_HOST : Batch synthesis) 
    - (UV_HOST : UV-Vis analysis) 
    - (DB_HOST : Database (MongoDB)) 
    """
    def __init__(self):
        self.routing_table={
            "BATCH":{
                "HOST":"192.168.1.11",  # (WINDOWS : Batch synthesis) The server"s hostname or IP address (231: linux)
                "PORT":54009, # server port
                "NAME":"kist", # Windows name
                "PWD":"selfdriving!" # Windows pwd
            },
            "UV":{
                "HOST":"192.168.4.11",  # (WINDOWS : UV analysis) The server"s hostname or IP address
                "PORT":54009, # server port
                "NAME":"user", # Windows name
                "PWD":"selfdriving!" # Windows pwd
            },
            "DB":{
                "HOST":"192.168.5.11",  # (WINDOWS : Database (MongoDB)) The server's hostname or IP address
                "PORT":54009, # The port used by the mongodb server (54009)
                "NAME":"user", # Windows name
                "PWD":"selfdriving!" # Windows pwd
            }
        }


class ActionExecutor(ParameterTCP):
    """
    [ActionExecutor] TCP Class for controlling another computer
    - callServer_BATCH(self, command_str="info/BATCH/None/all/virtual")
    - callServer_UV(self, command_str="info/UV/None/all/virtual")
    - callServer_qcommand(self, command_str="qhold/1") # queue function
    - callServer_acommand(self, command_str="ashutdown/all") # admin function
    """

    def __init__(self):
        self.BUFF_SIZE = 4096
        ParameterTCP.__init__(self,)

    def _combineActionData(self, action_data):
        """
        combine action data on "{},{},{}..." using punctuation

        :param action_data (str or list) : 
            str --> action data
            list --> action datas in list, ex) action_data=[solution_name,volume,concentration,injection_rate]

        return action_data_str (str) : ex) "solution_name,volume,concentration,injection_rate"
        """
        if type(action_data)==str or type(action_data)==int:
            return str(action_data)
        elif type(action_data)==list:
            action_data_str=""
            for idx, action_data in enumerate(action_data):
                if idx != 0:
                    action_data_str+=","
                action_data_str+=str(action_data)
            return action_data_str
        else:
            raise Exception("action data type is wrong, action_data:{}, type:{}".format(action_data, type(action_data)))

    def _combineCommandStr(self, job_id, device_name, action_type, action_data, mode_type):
        """
        convert str to bytes for packet transferin module node

        return command_bytes (bytes) --> str.encode("{}/{}/{}/{}/{}".format(job_id, device_name, action_type, action_data, mode_type))
        """
        command_str="{}/{}/{}/{}/{}".format(job_id, device_name, action_type, action_data, mode_type)

        return command_str

    def packetFormatter(self, job_id, device_name, action_type, action_data_list, mode_type):
        action_data_str=self._combineActionData(action_data=action_data_list)
        command_str=self._combineCommandStr(job_id, device_name, action_type, action_data_str, mode_type)

        return command_str

    def emergencyStop(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(("192.168.255.255", 54010))
            time.sleep(1)
            # activate broadcast option
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto("shutdown".encode(), "192.168.255.255")
            message="emergency stop"
            return message

    def transferDeviceCommand(self, module_name, command_str):
        """
        receive command_byte & send tcp packet using socket 

        #########
        # Batch #
        #########
        1) INFO
        :param command_str="info/BatchSynthesis/None/all/{mode_type}" (str) : input command string type
            - {jobID} (str): info, get self.{}_info
            - device_name="BatchSynthesis" (str) (LA, ABS, STIRRER, PUMP, STORAGE, PIPETTE)
            - action_type=None (str) ... (str): get self.{}_info
            - action_data=all (str) ... (str)
            - mode_type = "virtual" (str): set mode type --> real, virtual
        :return each_info_dict (dict): has BatchSynthesis's device information
        
        2) if action
        :param command_byte = {jobID}/DS_B/{storage_empty_to_stirrer}/{pick_num&place_num}/{mode_type}' (byte) : input command string type
            - {jobID} (int): depending on jobID 
            - device_name="DS_B" (str): (LA, ABS, STIRRER, PUMP, STORAGE, PIPETTE, DS_B)
            - action_type="storage_empty_to_stirrer" (str) : ex) "storage_empty_to_stirrer"
            - action_data="{}&{}" (str): set action data
                - pick_num=0 (int): pick vial or pick cuvette
                - place_num=1 (int): set place_num
            - mode_type="virtual" (str): set mode type --> real, virtual
        :return: status_message (str)

        :param command_byte = '{jobID}/PIPETTE/{sample}/{pipette_volume&inject_volume&tip_loc&pump_in_loc&pump_out_loc&mixing_time}/{mode_type}' (byte) : input command string type 
            - {jobID} (int): depending on jobID
            - device_name="PIPETTE" (str): (LA, ABS, STIRRER, PUMP, STORAGE, PIPETTE)
            - action_type="sample" (str): set action type (ex) "sample", "synthesis"
            - action_data="{}&{}&{}&{}&{}&{}" (str): set action data
                - pipette_volume="20-200" (str): set type of pipette (ex) 2-20, 20-200, 100-1000 ...
                - inject_volume=2 (int): set volume of injection
                - tip_loc=0,1,2... (int): set pipette tip's position idx
                - pump_in_loc=0 (int): set pump in location
                - pump_out_loc=3 (int): set pump out location
                - mixing_time=3 (int): set mixing time
            - mode_type="virtual" (str): set mode type --> real, virtual
            ex) "20-200", 2, 0, 0, 3,
        :return: status_message (str)

        :param command_str='{jobID}/STORAGE/open/1/{mode_type}' (byte) : input command string type
            - {jobID} (int): depending on jobID 
            - device_name="STORAGE" (str) (LA, ABS, STIRRER, PUMP, STORAGE, PIPETTE)
            - action_type="open" (str): set action type
            - action_data="{}" (str): set action data
                - entrance_num = 1 (int): set entrance number of storage
            - mode_type = "virtual" (str): set mode type --> real, virtual
        :return: status_message (str)

        :param command_str='{jobID}/PUMP/single/{solution_name}&{volume}&{concentration}&{injection_rate}/{mode_type}' (byte) or
               command_str='{jobID}/PUMP/multi/AgNO3&1500&2000-NaBH4&1500&2000/real'): input command string type 
               command_str='{jobID}/PUMP/info/real'): request pump information (solution_name_list, solution_addr_list, solution_type_list)
            - {jobID} (int): depending on jobID
            - device_name="PUMP" (str) (LA, ABS, STIRRER, PUMP, STORAGE, PIPETTE)
            - action_type="single" or "multi" (str): set action type
            - action_data="{}&{}&{}" (str): set action data
                - solution_name (str or list): set solution name (AgNO3, H2O, Citrate, PVP...) 
                - volume (int or list) : set volume (ul)
                - concentration (int or list) : set concentration (mM)
                - injection_rate (int or list) : set flow rate (ul/s)
            - mode_type = "virtual" (str): set mode type --> real, virtual
        :return: status_message (str)

        :param command_byte = b'{jobID}/STIRRER/heat/{stirrer_address}&{temperature}/{mode_type}' (byte) : input command string type
            - {jobID} (int): depending on jobID 
            - device_name="STIRRER" (str) : (LA, UV, STIRRER, PUMP, STORAGE, PIPETTE)
            - action_type="heat" (str) : (heat, stir, stop)
            - action_data="{}&{}" (str): set action data
                - stirrer_address = 0 or 1... (int): set stirrer address (Address number) 
                - action_data = 50 or 800 (int): set temperature or stir rate (Celsius or rpm) 
            - mode_type = "virtual" (str): set mode type --> real, virtual
        :return: status_message (str)

        :param command_str='{jobID}/LA/home/null/{mode_type}' (byte) : input command string type
        if action type == "home" --> '1/LA/home/null/{mode_type}'
            - {jobID} (int): depending on jobID
            - device_name=LA (str) : set device name in batch platform
            - action_type = home or stirrer_0... (str): set action type
            - action_data="null" (str): set action data
            - mode_type = "virtual" (str): set mode type --> real, virtual 
        elif action type == "center" --> '1/LA/home/null/{mode_type}'
            - {jobID} (int): depending on jobID
            - device_name=LA (str) : set device name in batch platform
            - action_type = home or stirrer_0... (str): set action type
            - action_data="null" (str): set action data
            - mode_type = "virtual" (str): set mode type --> real, virtual 
        elif action type == "down" or "up" --> '1/LA/down/0/{mode_type}'
            - {jobID} (int): depending on jobID
            - device_name=LA (str) : set device name in batch platform
            - action_type = "up" or "down"... (str): set action type
            - action_data="{}" (str): set action data
                - location_number = 0,1,2..... depending on stirrer
            - mode_type = "virtual" (str): set mode type --> real, virtual 
        :return: status_message

        ######
        # UV #
        ######
        :param command_str="info/UV/None/all/virtual" (str) : input command string type
            - {jobID} (str): INFO
            - device_name="UV" (str) (LA, UV, STIRRER, PUMP, STORAGE, PIPETTE)
            - action_type=None (str) ... (str): get self.{}_info
            - action_data=all (str) ... (str): get self.{}_info
            - mode_type="virtual" (str): set mode type --> real, virtual
        :return each_info_dict (dict): has UV's device information

        :param command_str="{jobID}/SPECTROSCOPY/Abs/Ag/virtual" (str) : input command string type 
            - {jobID} (int): depending on jobID
            - device_name="SPECTROSCOPY" (str) (LA, ABS, STIRRER, PUMP, STORAGE, PIPETTE)
            - action_type="Abs" or "Ref" (str) ... (str): set action type
            - action_data="AgNP" (str) ... (str): set action data
            - mode_type = "virtual" (str): set mode type --> real, virtual
        :return: status_message
        """
        command_bytes=str.encode(command_str)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.routing_table[module_name]["HOST"], self.routing_table[module_name]["PORT"]))
            time.sleep(1)
            s.sendall(command_bytes)
            message_recv = b''
            while True:
                part = s.recv(self.BUFF_SIZE)
                if "finish" in part.decode("utf-8") or "success" in part.decode("utf-8"):
                    s.close()
                    break
                elif "finish" not in part.decode("utf-8") or "success" in part.decode("utf-8"):
                    message_recv += part
                else:
                    raise ConnectionError("Wrong tcp message in {} module, ip:{},port:".format(module_name, self.routing_table[module_name]["HOST"], self.routing_table[module_name]["PORT"]))
            return message_recv.decode("utf-8")

    def callServer_qcommand(self, command_str="qhold/1"):
        """
        receive command_byte & send tcp packet using socket 

        :param command_str="{qcommand}/{jobID}" (str) : input command string type
            - {qcommand} (str): qhold, qdel, qrestart ...  
            - {jobID} (int): depending on jobID 

        :return each_info_dict (dict): has UV's device information
        """
        command_bytes=str.encode(command_str)
        for module_name in list(self.routing_table.keys()):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # print(module_name)
                # print(type(module_name))
                s.connect((self.routing_table[module_name]["HOST"], self.routing_table[module_name]["PORT"]))
                time.sleep(1)
                s.sendall(command_bytes)
                message_recv = b''
                while True:
                    part = s.recv(self.BUFF_SIZE)
                    message_recv += part
                    if len(part) < self.BUFF_SIZE:
                        s.close()
                        break
            return message_recv.decode("utf-8")

    def callServer_acommand(self, command_str="ashutdown/all"):
        """
        receive command_byte & send tcp packet using socket 

        :param command_str="{qcommand}/{jobID}" (str) : input command string type
            - {qcommand} (str): ashutdown, areboot, qrestart ...  
            - {jobID} (int): depending on jobID 

        :return each_info_dict (dict): has UV's device information
        """
        command_bytes=str.encode(command_str)
        acommand, module=command_bytes.decode("utf-8").split("/")
        if "ashutdown" in command_str and module == 'all':
            message=self.emergencyStop()
            return message
        else:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                for module_name in list(self.routing_table.keys()):
                    s.connect((self.routing_table[module_name]["HOST"], self.routing_table[module_name]["PORT"]))
                    time.sleep(1)
                    s.sendall(command_bytes)
                    message_recv = b''
                    while True:
                        part = s.recv(self.BUFF_SIZE)
                        message_recv += part
                        if len(part) < self.BUFF_SIZE:
                            s.close()
                            break
                    message=message_recv.decode("utf-8")
            return message