#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @brief    [TCP_Class] TCP_Class class file
# author Hyuk Jun Yoo (yoohj9475@kist.re.kr)
# GENEREATION 2024-06-26 13:51:29


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
    