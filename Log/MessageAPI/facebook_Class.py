#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [IntegratedMessenger] FacebookMessenger Class send our error message to researcher to prevent error immediately
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# TEST 2021-07-21

from fbchat import Client
from fbchat.models import *
import fbchat
import re
import json
import logging
fbchat._util.USER_AGENTS = ["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"]
fbchat._state.FB_DTSG_REGEX = re.compile(r'"DTSGInitData",\[\],\{"token":"(.*?)"')
"""
예제코드
https://fbchat.readthedocs.io/en/latest/examples.html

주의할 점

1. fbchat\_client.py 들어가서 무조건 time.sleep 길게 해야함.
2. 아래 2개는 무조건 진행해야함. (fbchat._util.USER_AGENTS, fbchat._state.FB_DTSG_REGEX)
"""


class FacebookMessenger:
    """
    FacebookMessenger class send message and image to researcher to recognize our situation
    
    # Variable

    :param FACEBOOK_MESSENGER_USER_ID: facebook id
    :param FACEBOOK_MESSENGER_USER_PWD: facebook password
    :param max_tries=10: try to send packet to facebook server

    # Function
    - sendMessage(full_text)
    - sendLocalImage(image_path)
    - logOutSession()
    """
    def __init__(self, MasterLogger_obj, FACEBOOK_MESSENGER_USER_ID, FACEBOOK_MESSENGER_USER_PWD, max_tries=10, mode_type="virtual"):
        self.__MasterLogger_obj=MasterLogger_obj
        self.__platform_name = "{}-{} ({})".format("MessageAPI", "Facebook", mode_type)
        # get information, ID, PWD
        self.__FACEBOOK_MESSENGER_USER_ID = FACEBOOK_MESSENGER_USER_ID
        self.__FACEBOOK_MESSENGER_USER_PWD = FACEBOOK_MESSENGER_USER_PWD
        self.__mode_type=mode_type

        # make Facebook chat object
        """
        def session_factory(user_agent=None):
            session = requests.session()
            session.headers["Referer"] = "https://www.facebook.com"
            session.headers["Accept"] = "text/html"

            # TODO: Deprecate setting the user agent manually
            session.headers["User-Agent"] = user_agent or random.choice(_util.USER_AGENTS)
            print(session.headers["User-Agent"])
            return session
        """
        self.__client = Client(self.__FACEBOOK_MESSENGER_USER_ID, self.__FACEBOOK_MESSENGER_USER_PWD, max_tries=max_tries)
        self.__sess = self.__client.getSession()

    def sendMessage(self, full_text):
        """
        :param full_text (str): text information
        """
        try:
            self.__client.send(Message(text=full_text), thread_id=self.__client.uid, thread_type=ThreadType.USER)
            self.__MasterLogger_obj.debug(self.__platform_name, debug_msg="Send Message")

        except Exception as e:
            self.__MasterLogger_obj.debug(self.__platform_name, debug_msg=str(e))

    def sendLocalImage(self, image_path):
        """
        :param image_path (list): file path information list
        """
        try:
            self.__client.sendLocalImage(
                image_path,
                message=Message(text="This is a local image"),
                thread_id=self.__client.uid,
                thread_type=ThreadType.USER,
            )
            self.__MasterLogger_obj.debug(self.__platform_name, debug_msg="Send Local Image!")

        except Exception as e:
            self.__MasterLogger_obj.debug(self.__platform_name, debug_msg=str(e))

    def logOutSession(self):
        self.__client.logout()
