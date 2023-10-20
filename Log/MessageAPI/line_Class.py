#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [IntegratedMessenger] LineMessenger Class send our error message to researcher to prevent error immediately
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# TEST 2021-07-21

import os, sys
import requests

class LineMessenger:
    """
    FacebookMessenger class send message and image to researcher to recognize our situation
    
    # Variable

    :param LINE_TARGET_URL: facebook id
    :param LINE_TOKEN: facebook password
    :param mode_type="virtual"

    # Function

    - sendMessage(full_text)
    - sendMessageImage(full_text, image)
    """
    def __init__(self, LINE_TARGET_URL, LINE_TOKEN, mode_type="virtual"):
        # get information, URL, TOKEN
        self.__LINE_TARGET_URL = LINE_TARGET_URL
        self.__LINE_TOKEN = LINE_TOKEN
        self.__platform_name = "{}-{} ({})".format("MessageAPI", "Line", mode_type)
        self.mode_type=mode_type

    def sendMessage(self, full_text):
        """
        send message using line message

        :param full_text (str): text information
        """
        if self.mode_type=="real":
            try:
                response = requests.post(
                    url=self.__LINE_TARGET_URL,
                    headers={
                        'Authorization': 'Bearer ' + self.__LINE_TOKEN
                    },
                    data={
                        'message': full_text,
                    }
                )
            except Exception as e:
                print(e)
        elif self.mode_type=="virtual":
            pass

    def sendMessageImage(self, full_text, image):
        """
        send message & image using line message

        :param full_text (str): text information
        :param image (byte): image file
        """
        if self.mode_type=="real":
            try:
                response = requests.post(
                    url=self.__LINE_TARGET_URL,
                    headers={
                        'Authorization': 'Bearer ' + self.__LINE_TOKEN
                    },
                    data={
                        'message': full_text,
                    },
                    files={
                        'imageFile' : image
                    }
                )
            except Exception as e:
                print(e)
        elif self.mode_type=="virtual":
            pass