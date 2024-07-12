#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @brief    [NodeLogger] Logging Class for controlling our command and log file in Autonomous System Laboratory
# author Hyuk Jun Yoo (yoohj9475@kist.re.kr)
# GENEREATION 2024-06-26 13:51:29


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
    