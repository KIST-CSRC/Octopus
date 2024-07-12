# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [Stirrer] Stirrer class with action function 
# author Hyuk Jun Yoo (yoohj9475@kist.re.kr)
# GENEREATION 2024-07-12 14:13:54

import sys
        

class Stirrer:

    def __init__(self, logger_obj, device_name="Stirrer"):
        ################################################################################################
        # Please configure the device information according to the Stirrer manufacturer guidelines.
        # ex) self.info['Port']='COM3' or '/dev/ttyUSB0'
        # ex) self.info['BaudRate']=9600
        ################################################################################################
        
        self.info={}
        self.info['DeviceName']=device_name
        
        self.logger_obj=logger_obj
        self.device_name=device_name

        ################################################################################################
        # Please configure the types of actions according to the Stirrer manufacturer guidelines.
        # if some device is made of yourself (ex. arduino),                                        
        # >>> self.arduinoData = serial.Serial(self.info["Port"], self.info["BaudRate"])           
        # if some device import manufacturer library and generate object in here                 
        # >>> from Tecan import TecanAPI                                                           
        # >>> self.syringe_pump = TecanAPI()                                                       
        ################################################################################################
    
    def heartbeat(self,) -> str:
        debug_device_name='{} ({})'.format(self.device_name, "heartbeat")

        ############################################################################################
        # Please configure the types of actions according to the Stirrer manufacturer guidelines. 
        ################################################################################################
        
        debug_msg="Hello World!! Succeed to connection to main computer!"
        self.logger_obj.debug(device_name=debug_device_name, debug_msg=debug_msg)

        return_res_msg='[{}] : {}'.format(self.device_name, debug_msg)
        return return_res_msg
        
    def Stir(self, action_data:str, mode_type:str="virtual") -> str:
        '''
        :param action_data (str) :
        :param mode_type="virtual" (str): set virtual or real mode
        
        :return: return_res_msg
        '''
        current_action_type=sys._getframe().f_code.co_name
        device_name="{} ({})".format(self.device_name, mode_type)
        debug_msg="Start {} action, action_data={}".format(current_action_type, action_data)
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

        debug_msg="Finish {} action, action_data={}".format(current_action_type, action_data)
        self.logger_obj.debug(device_name=device_name, debug_msg=debug_msg)
        
        return_res_msg="[{}] : {}".format(device_name, debug_msg)
        return return_res_msg

    def Stop(self, action_data:str, mode_type:str="virtual") -> str:
        '''
        :param action_data (str) :
        :param mode_type="virtual" (str): set virtual or real mode
        
        :return: return_res_msg
        '''
        current_action_type=sys._getframe().f_code.co_name
        device_name="{} ({})".format(self.device_name, mode_type)
        debug_msg="Start {} action, action_data={}".format(current_action_type, action_data)
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

        debug_msg="Finish {} action, action_data={}".format(current_action_type, action_data)
        self.logger_obj.debug(device_name=device_name, debug_msg=debug_msg)
        
        return_res_msg="[{}] : {}".format(device_name, debug_msg)
        return return_res_msg
