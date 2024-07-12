#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author Hyuk Jun Yoo (yoohj9475@kist.re.kr)
# GENEREATION 2024-06-26 13:51:29

from RobotArm.RobotArm import RobotArm
from LinearActuator.LinearActuator import LinearActuator
from Log.Logging_Class import NodeLogger
from BaseUtils.TCP_Node import BaseTCPNode
import socket

def getActionType(obj):
    methods = [method for method in dir(obj) if callable(getattr(obj, method)) and not method.startswith("__")]
    return methods

SIZE = 104857600
device_server_name='RobotArmDeviceServer'
NodeLogger_obj = NodeLogger(platform_name=device_server_name, setLevel="DEBUG", SAVE_DIR_PATH="Log")
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

base_tcp_node_obj = BaseTCPNode()
server_socket.bind(('127.0.0.1', 54010))  # Specifying IP address and port number
server_socket.listen()  # Waiting for a module node's connection request

RobotArm_obj = RobotArm(NodeLogger_obj) # please check your device class
LinearActuator_obj = LinearActuator(NodeLogger_obj) # please check your device class
device_obj_dict={
    "RobotArm":RobotArm_obj,
    "LinearActuator":LinearActuator_obj,
}

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
