#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [ActionExecutor] ActionExecutor Class for controlling another computer (windows, ubuntu)
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)
# @version  3_1      
# TEST 2021-09-23 // 2022-01-17 // 2024-06-10
from typing import Union

import socket, json
import time


class ActionExecutor:
    """
    [ActionExecutor] TCP Class for controlling another computer
    
    TCP information : to protect our system due to hacker
    
    internal network : 192.168.{big process type}.{module index}
        def big process type: Synthesis:1, Preprocess:2, Evaluation:3, Charaterization:4, Database:5
        def module index : Synthesis:{"BatchSynthesis":11, "FlowSyntheis":12, "SolvothermalSynthesis":13...}
    
    - _combineActionData(action_data)
    - _combineCommandStr(job_id:int, device_name:str, action_type:str, action_data:str, mode_type:str)
    - packetFormatter(job_id:int, device_name:str, action_type:str, action_data_list:Union[str, list], mode_type:str)
    - emergencyStop()
    - transferDeviceCommand(module_name, command_str)
    - transfer_qcommand(command_str="qhold/1") # queue function
    - transfer_acommand(command_str="ashutdown/all") # admin function
    """

    def __init__(self):
        self.BUFF_SIZE = 4096
        with open("Action/routing_table.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
        self.routing_table=data

    def _combineActionData(self, action_data:Union[str, list]):
        """
        combine action data on "{},{},{}..." using punctuation

        :param action_data (str or list) : 
            str --> action data
            list --> action datas in list, ex) action_data=[solution_name&volume&concentration&injection_rate]

        return action_data_str (str) : ex) "solution_name&volume&concentration&injection_rate"
        """
        if type(action_data)==str or type(action_data)==int:
            return str(action_data)
        elif type(action_data)==list:
            action_data_str=""
            for idx, action_data in enumerate(action_data):
                if idx != 0:
                    action_data_str+="&"
                action_data_str+=str(action_data)
            return action_data_str
        else:
            raise Exception("action data type is wrong, action_data:{}, type:{}".format(action_data, type(action_data)))

    def _combineCommandStr(self, job_id:int, device_name:str, action_type:str, action_data:str, mode_type:str):
        """
        convert str to bytes for packet transferin module node

        return command_bytes (bytes) --> str.encode("{}/{}/{}/{}/{}".format(job_id, device_name, action_type, action_data, mode_type))
        """
        command_str="{}/{}/{}/{}/{}".format(job_id, device_name, action_type, action_data, mode_type)

        return command_str

    def packetFormatter(self, job_id:int, device_name:str, action_type:str, action_data_list:Union[str, list], mode_type:str):
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

    def transferDeviceCommand(self, module_name:str, command_str:str):
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
        
        :param command_byte = '{jobID}/LIMPETTE/{sample}/{volume&tip_loc&extract_loc&dispense_loc}/{mode_type}' (byte) : input command string type 
            - {jobID} (int): depending on jobID
            - device_name="LIMPETTE" (str): (LA, ABS, STIRRER, PUMP, STORAGE, PIPETTE, LIMPETTE)
            - action_type="sample" (str): set action type (ex) "sample", "synthesis"
            - action_data="{}&{}&{}&{}&{}&{}" (str): set action data
                - volume=200 (int): set type of pipette (ex) 2-20, 20-200, 100-1000 ...
                - tip_loc=0,1,2... (int): set pipette tip's position idx
                - extract_loc=0 (int): set extract location
                - dispense_loc (int): set dispense location --> In UV, 0 is default (cuvette holder)
            - mode_type="virtual" (str): set mode type --> real, virtual
            ex) 200&2&4&3&0
        :return: status_message (str)
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

    def transfer_qcommand(self, command_str="qhold/1"):
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

    def transfer_acommand(self, command_str="ashutdown/all"):
        """
        receive command_byte & send tcp packet using socket 

        :param command_str="{qcommand}/{jobID}" (str) : input command string type
            - {qcommand} (str): ashutdown, areboot, ...  
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
        


if __name__ == '__main__':
    tcp_object = ActionExecutor()
    # tcp_object.transferDeviceCommand(module_name="BatchSynthesis", command_str="0/LA/down/Stirrer_1&8/virtual")
    tcp_object.transferDeviceCommand(module_name="BatchSynthesis",command_str='0/PUMP/single/IrCl3&1000&0.1&100/real')
    # tcp_object.MOMA("ID/AMR/status/None/virtual")
    # tcp_object.MOMA("ID/AMR/move_place/Storage/real")
    # tcp_object.transferDeviceCommand("BatchSynthesis", "0/PUMP/single/HAuCl4&4000&0.5&200/virtual")
    # tcp_object.transferDeviceCommand("BatchSynthesis","0/UVPIPETTE/sample/20-200&2&0&0&0&3/real")
    # tcp_object.MOMA("ID/AMR/pick_place/AMR&vial&0&Storage&vial&0/real")
    
    #240418 moma test
    # while True:
    # tcp_object.MOMA("ID/AMR/status/None/real")
    # time.sleep(1)
    # tcp_object.MOMA("ID/AMR/move_place/BatchSynthesis/real")
    # time.sleep(1)
    # tcp_object.MOMA("ID/AMR/pick_place/BatchSynthesis&vial&2&AMR&vial&0/real")
    # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&vial&1&BatchSynthesis&vial&1/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&vial&2&BatchSynthesis&vial&2/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&vial&3&BatchSynthesis&vial&3/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&vial&4&BatchSynthesis&vial&4/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&vial&5&BatchSynthesis&vial&5/real")
        # time.sleep(120)
    # tcp_object.MOMA("ID/AMR/pick_place/BatchSynthesis&vial&0&AMR&vial&0/real")
    # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/BatchSynthesis&vial&1&AMR&vial&1/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/BatchSynthesis&vial&2&AMR&vial&2/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/BatchSynthesis&vial&3&AMR&vial&3/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/BatchSynthesis&vial&4&AMR&vial&4/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/BatchSynthesis&vial&5&AMR&vial&5/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/status/None/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/move_place/BatchSynthesis/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&vial&0&Preprocess&vial&0/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&vial&1&Preprocess&vial&1/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&vial&2&Preprocess&vial&2/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&vial&3&Preprocess&vial&3/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&vial&4&Preprocess&vial&4/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&vial&5&Preprocess&vial&5/real")
        # time.sleep(10)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&falcon&0&Preprocess&falcon&0/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&falcon&1&Preprocess&falcon&1/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&falcon&2&Preprocess&falcon&2/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&falcon&3&Preprocess&falcon&3/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&falcon&4&Preprocess&falcon&4/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&falcon&5&Preprocess&falcon&5/real")
        # time.sleep(120)
        # tcp_object.MOMA("ID/AMR/pick_place/Preprocess&vial&0&AMR&vial&0/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/Preprocess&vial&1&AMR&vial&1/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/Preprocess&vial&2&AMR&vial&2/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/Preprocess&vial&3&AMR&vial&3/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/Preprocess&vial&4&AMR&vial&4/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/Preprocess&vial&5&AMR&vial&5/real")
        # time.sleep(10)
        # tcp_object.MOMA("ID/AMR/pick_place/Preprocess&falcon&0&AMR&falcon&0/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/Preprocess&falcon&1&AMR&falcon&1/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/Preprocess&falcon&2&AMR&falcon&2/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/Preprocess&falcon&3&AMR&falcon&3/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/Preprocess&falcon&4&AMR&falcon&4/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/Preprocess&falcon&5&AMR&falcon&5/real")
        # time.sleep(120)
        # tcp_object.MOMA("ID/AMR/status/None/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/move_place/RDE/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&falcon&0&RDE&falcon&0/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&falcon&1&RDE&falcon&1/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&falcon&2&RDE&falcon&2/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&falcon&3&RDE&falcon&3/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&falcon&4&RDE&falcon&4/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/AMR&falcon&5&RDE&falcon&5/real")
        # time.sleep(120)
        # tcp_object.MOMA("ID/AMR/pick_place/RDE&falcon&0&AMR&falcon&0/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/RDE&falcon&1&AMR&falcon&1/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/RDE&falcon&2&AMR&falcon&2/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/RDE&falcon&3&AMR&falcon&3/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/RDE&falcon&4&AMR&falcon&4/real")
        # time.sleep(1)
        # tcp_object.MOMA("ID/AMR/pick_place/RDE&falcon&5&AMR&falcon&5/real")
        # time.sleep(1)


    
    """
    print(tcp_object.transfer_BATCH(command_str='{jobID}/STORAGE/open/0/real'))
    time.sleep(1)
    print(tcp_object.transfer_DS_B(command_str='{jobID}/DS_B/storage_empty_to_stirrer/0,0/real'))
    time.sleep(1)
    print(tcp_object.transfer_PUMP(command_str='{jobID}/PUMP/single/H2O,2000,4000/real'))
    time.sleep(1)
    print(tcp_object.transfer_BATCH(command_str='{jobID}/LA/up/Stirrer_0,0/real'))
    print(tcp_object.transfer_BATCH(command_str='{jobID}/LA/home/null/real'))
    print(tcp_object.transfer_DS_B(command_str='{jobID}/DS_B/stirrer_to_holder/0,0/real'))
    print(tcp_object.transfer_DS_B(command_str='{jobID}/DS_B/cuvette_storage_to_cuvette_holder/0,0/real'))
    print(tcp_object.transfer_DS_B(command_str='{jobID}/DS_B/cuvette_holder_to_UV/0,0/real'))
    print(tcp_object.transfer_BATCH(command_str='{jobID}/PIPETTE/sample/20-200,2,A2,0,0,3/real'))
    print(tcp_object.transfer_DS_B(command_str='{jobID}/DS_B/UV_to_cuvette_storage/0,7/real'))
    """
    """
    time.sleep(1)
    time.sleep(1)
    print(tcp_object.transfer_BATCH(command_str=command_bytes))
    
    """

    
    # print(tcp_object.transfer_AMR(command_str))
    # print(tcp_object.transfer_PUMP(command_str='{jobID}/PUMP/single/AgNO3,2000,5,5000/real'))
    # print(tcp_object.transfer_DS_B(command_str='{jobID}/DS_B/holder_to_storage_filled/7,0/real'))
    # time.sleep(1)
    # print(tcp_object.transfer_BATCH(command_str='{jobID}/STORAGE/open/5/real'))
    
    # print(tcp_object.transfer_BATCH(command_str='{jobID}/LA/up/Stirrer_0/3/virtual'))
    # print(tcp_object.transfer_BATCH(command_str='{jobID}/STIRRER/stir/0/600/real'))
    # print(tcp_object.transfer_BATCH(command_str='{jobID}/STIRRER/stop/real'))

    # print(tcp_object.transfer_PUMP(command_str='{jobID}/PUMP/multi/NaBH4,H2O/1500,2000/2000,2000/real'))
    
    # for i in range(8):
    #     print(11)
    #     Reference_result = tcp_object.transfer_UV(command_str="{jobID}/UV/Reference/real")
    #     Reference_dict=json.loads(Reference_result)
    #     with open("Reference_UV.json", 'w') as outfile:
    #         json.dump(Reference_dict, outfile)
    #     tcp_object.transfer_BATCH(b'PIPETTE/sample/0/A5/real')

    #     Abs_result = tcp_object.transfer_UV(command_str="{jobID}/UV/Abs/real")
    #     Abs_dict=json.loads(Abs_result)
    #     with open("Abs_UV.json", 'w') as outfile:
    #         json.dump(Abs_dict, outfile)

    # import time

    # time.sleep(10)
    


        
    # print(type(result))
    
    
    #Electrochem test
    # tcp_object.Electrochem_Module_test("1","RDEACTUATOR","heartbeat","null","virtual")
    # tcp_object.Electrochem_Module_test("1","PUMP","heartbeat","electrolyte","virtual")
    # tcp_object.Electrochem_Module_test("1","SONIC","heartbeat","null","virtual")
    # tcp_object.Electrochem_Module_test("1","SOLENOID","heartbeat","null","virtual")
    # tcp_object.Electrochem_Module_test("1","MFC","heartbeat","null","virtual")
    # tcp_object.Electrochem_Module_test("1","RDEROTOR","heartbeat","null","virtual")
    # tcp_object.Electrochem_Module_test("1","POTENTIOSTAT","heartbeat","null","virtual")
    # tcp_object.Electrochem_Module_test("1","IRLAMP","heartbeat","null","virtual")
    # tcp_object.Electrochem_Module_test("1","HUMIDIFIER","heartbeat","null","virtual")
    # tcp_object.Electrochem_Module_test("1","MICROSCOPE","heartbeat","null","virtual")
    # tcp_object.Electrochem_Module_test("1","POLISHINGTOOL","heartbeat","null","virtual")

#####prerpocess test#####
    
#     batch_size = 6

#     pipetting = 3 

#     for current_experiment in range(batch_size):
#         tcp_object.Preprocess_Module_test("2","PRE_ROBOT","pick_pipette",0)
#         tcp_object.Preprocess_Module_test("2","PRE_ROBOT","get_pipetteTip",0)
#         for i in range(pipetting):
#             tcp_object.Preprocess_Module_test("2","PRE_ROBOT","TransferLiquid_vial_to_falcon",current_experiment)
#         tcp_object.Preprocess_Module_test("2","PRE_ROBOT","remove_the_tip",current_experiment)
#     tcp_object.Preprocess_Module_test("2","PRE_ROBOT","place_pipette",current_experiment)
    
#     for batch in range(batch_size):
#         tcp_object.Preprocess_Module_test("2","PRE_ROBOT","place_falcon_to_centri",batch)
    # tcp_object.Preprocess_Module_test("2","Centrifuge","Centri_Door_Close","null")
    # tcp_object.Preprocess_Module_test("2","PreprocessSonic","operate_Sonic","10&10")
#     tcp_object.Preprocess_Module_test("2","PRE_ROBOT","change_the_gripper_to_VCG","")
#     for batch in range(batch_size):
#             tcp_object.Preprocess_Module_test("2","PRE_ROBOT","pick_falcon_from_centri",batch)
#     tcp_object.Preprocess_Module_test("2","PRE_ROBOT","change_the_gripper_to_RG6","null")
#     for batch in range(batch_size):
#         tcp_object.Preprocess_Module_test("2","PRE_ROBOT","holder_to_DeskLA",current_experiment)
    # tcp_object.Preprocess_Module_test("2","DeskLA","Desk_to_Washing","null")
#         tcp_object.Preprocess_Module_test("2","DispenserLA","DispenserLA_Down","12000")
#         tcp_object.Preprocess_Module_test("2","PreprocessPump","PrePumpOn","100&500")
#         tcp_object.Preprocess_Module_test("2","DispenserLA","DispenserLA_UP","12000")
    # tcp_object.Preprocess_Module_test("2","DeskLA","Washing_to_Home","null")
#         tcp_object.Preprocess_Module_test("2","PRE_ROBOT","DeskLA_to_holder",current_experiment)
# ###################################Washing Protocol is done##################################
#         time.sleep(2)
#         ###################################Ink Protocol is started##################################
        
#         tcp_object.Preprocess_Module_test("2","PRE_ROBOT","holder_to_weighing",current_experiment)
#         tcp_object.Preprocess_Module_test("2","PRE_ROBOT","weighing_to_holder",current_experiment)
#         tcp_object.Preprocess_Module_test("2","PRE_ROBOT","pick_pipette",current_experiment)
#         tcp_object.Preprocess_Module_test("2","PRE_ROBOT","get_pipetteTip",current_experiment + 3)
#         tcp_object.Preprocess_Module_test("2","PRE_ROBOT","remove_the_tip",current_experiment)
#         for batch in range(batch_size):
#             tcp_object.Preprocess_Module_test("2","PRE_ROBOT","holder_to_sonic",current_experiment)
#         tcp_object.Preprocess_Module_test("2","PreprocessSonic","operate","10&2")
#         for batch in range(batch_size):
#             tcp_object.Preprocess_Module_test("2","PRE_ROBOT","sonic_to_holder",current_experiment)
        
