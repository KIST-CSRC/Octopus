#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author Hyuk Jun Yoo (yoohj9475@kist.re.kr)
# GENEREATION 2024-06-26 13:51:29

from Pipette.Pipette import Pipette
from Rde.Rde import Rde
from RdeRotator.RdeRotator import RdeRotator
from Sonication.Sonication import Sonication
from Humidifier.Humidifier import Humidifier
from Potentiostat.Potentiostat import Potentiostat
from Cell.Cell import Cell
from IrRamp.IrRamp import IrRamp
from MillingMachine.MillingMachine import MillingMachine
from GasRegulator.GasRegulator import GasRegulator
from Log.Logging_Class import NodeLogger
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
    MODULE_HOST='127.0.0.1'  # set IP address of module node computer
    MODULE_PORT=54009 # if you want, can change. but match port number with master node and device server
    module_name='ElectroChemicalRDEModule' # set module name

    NodeLogger_obj = NodeLogger(platform_name=module_name,setLevel="DEBUG",SAVE_DIR_PATH="Log")
    base_tcp_node_obj = BaseTCPNode()

    # Wihtout device server : direct connection with module node
    Pipette_obj = Pipette(NodeLogger_obj) # please check your device class
    Rde_obj = Rde(NodeLogger_obj) # please check your device class
    RdeRotator_obj = RdeRotator(NodeLogger_obj) # please check your device class
    Sonication_obj = Sonication(NodeLogger_obj) # please check your device class
    Humidifier_obj = Humidifier(NodeLogger_obj) # please check your device class
    Potentiostat_obj = Potentiostat(NodeLogger_obj) # please check your device class
    Cell_obj = Cell(NodeLogger_obj) # please check your device class
    IrRamp_obj = IrRamp(NodeLogger_obj) # please check your device class
    MillingMachine_obj = MillingMachine(NodeLogger_obj) # please check your device class
    GasRegulator_obj = GasRegulator(NodeLogger_obj) # please check your device class
    # Device server
    RobotArm_obj = TCP_Class('RobotArm', '127.0.0.1', 54010, NodeLogger_obj) # please check your device class
    LinearActuator_obj = TCP_Class('LinearActuator', '127.0.0.1', 54010, NodeLogger_obj) # please check your device class
    Pump_obj = TCP_Class('Pump', '127.0.0.1', 54011, NodeLogger_obj) # please check your device class
    device_obj_dict={
        "Pipette":Pipette_obj,
        "Rde":Rde_obj,
        "RdeRotator":RdeRotator_obj,
        "Sonication":Sonication_obj,
        "Humidifier":Humidifier_obj,
        "Potentiostat":Potentiostat_obj,
        "Cell":Cell_obj,
        "IrRamp":IrRamp_obj,
        "MillingMachine":MillingMachine_obj,
        "GasRegulator":GasRegulator_obj,
        "RobotArm":RobotArm_obj,
        "LinearActuator":LinearActuator_obj,
        "Pump":Pump_obj,
    }

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
