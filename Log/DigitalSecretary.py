#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [DigitalSecretary] DigitalSecretary Class to send our error message to researcher to prevent error immediately
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# TEST 2021-07-21

import json
import datetime
import time
import os, sys
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../Log")))
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# from facebook_Class import FacebookMessenger
from MessageAPI.mail_Class import MailMessenger
from MessageAPI.telegram_Class import TelegramMessenger
# from kakaotalk_Class import KakaotalkMessenger
from MessageAPI.line_Class import LineMessenger
from MessageAPI.dooray_Class import DoorayMessenger

dt_now = datetime.datetime.now()
d_today = datetime.date.today()


class DigitalSecretary:
    """
    [DigitalSecretary] DigitalSecretary Class to send our error message to researcher to prevent error immediately

    # Variable

    :param information_path="Log" (str): set information json file path
    :param mode_type="virtual" (str): set virtual or real mode
    
    # function
    - makeText(vial_num_list)
    - makeImg2Byte(image_path)
    - addUserInfo(content)
    - deleteUserInfo(content)
    - FACEBOOK_MESSENGER_alert(text, image_path)
    - MAIL_alert(toPerson_ID, text, image, image_path)
    - TELEGRAM_alert(text, image)
    - KAKAOTALK_alert(text)
    - LINE_alert(text, image)
    """ 
    def __init__(self, information_path="Log", mode_type="virtual"):
        """
        
        """
        # User Information
        self.__config_path = information_path + "/" +"Information.json"
        with open(self.__config_path,"r") as f:
            ALL_INFO = json.load(f)

        # facebook messenger
        self.__FACEBOOK_MESSENGER_USER = ALL_INFO["FACEBOOK_MESSENGER"]
        # Mail
        self.__MAIL_GMAIL_USER = ALL_INFO["MAIL"]
        # telegram
        self.__TELEGRAM_USER = ALL_INFO["TELEGRAM"]
        # # kakaotalk
        # # self.__KAKAOTALK_TARGET_URL=ALL_INFO["KAKAOTALK"]["KAKAOTALK_TARGET_URL"]
        # # self.__KAKAOTALK_TOKEN=ALL_INFO["KAKAOTALK"]["KAKAOTALK_access_token"]
        # # self.__KAKAOTALK_REFRESH_TOKEN=ALL_INFO["KAKAOTALK"]["KAKAOTALK_refresh_token"]
        # Line
        self.__LINE_USER = ALL_INFO["LINE"]
        # Dooray
        self.__DOORAY_USER=ALL_INFO["DOORAY"]

        self.__mail_toPerson_ID_list=["yoohj9475@kist.re.kr","kny@kist.re.kr"]
        self.__subject = "[KIST Autonomous Laboratory]"
        self.__mode_type=mode_type

    def getMail2PersonIDlist(self, ):
        return self.__mail_toPerson_ID_list

    def _makeImg2Byte(self, image_path):
        image = open(image_path,'rb')
        return image

    # def FACEBOOK_MESSENGER_alert(self, text, image_path):
    #     """
        
    #     """
    #     for user in self.__FACEBOOK_MESSENGER_USER:
    #         FACEBOOK_MESSENGER_USER_ID=user["FACEBOOK_MESSENGER_USER_ID"]
    #         FACEBOOK_MESSENGER_USER_PWD=user["FACEBOOK_MESSENGER_USER_PWD"]
    #         self.__fb_messenger = FacebookMessenger(FACEBOOK_MESSENGER_USER_ID=self.__FACEBOOK_MESSENGER_USER_ID, FACEBOOK_MESSENGER_USER_PWD=self.__FACEBOOK_MESSENGER_USER_PWD, max_tries=10)
    #         self.__fb_messenger.sendLocalImage(image_path=image_path)
    #         self.__fb_messenger.sendMessage(full_text=text)
        # self.__fb_messenger.logOutSession()

    def MAIL_alert(self, toPerson_ID_list, text, *image_information):
        """ 
        :param toPerson_ID_list (list): input toPerson_ID_list
        :param text (str): set message contents
        :param *image_information (list): set image_information

        :return: None
        """
        for user in self.__MAIL_GMAIL_USER:
            MAIL_ID=user["MAIL_GMAIL_USER_ID"]
            MAIL_PWD=user["MAIL_GMAIL_USER_PWD"]
            self.__mail_messenger = MailMessenger(MAIL_GMAIL_USER_ID=MAIL_ID, MAIL_GMAIL_USER_PWD=MAIL_PWD, mode_type=self.__mode_type)
            if image_information == True:
                self.__mail_messenger.sendEmail(subject=text, toPersonList=toPerson_ID_list, text=text, file_information=image_information)
            else:
                self.__mail_messenger.sendEmail(subject=text, toPersonList=toPerson_ID_list, text=text)
    
    def TELEGRAM_alert(self, text, *image):
        """
        :param text (str): set message contents
        :param *image (list): set image information list

        :return: None
        """
        for user in self.__TELEGRAM_USER:
            TELEGRAM_CHAT_ID=user["TELEGRAM_USER_ID"]
            TELEGRAM_TOKEN=user["TELEGRAM_USER_TOKEN"]
            self.__telegram_messenger = TelegramMessenger(TELEGRAM_CHAT_ID=TELEGRAM_CHAT_ID, TELEGRAM_TOKEN=TELEGRAM_TOKEN, mode_type=self.__mode_type)
            if image == True:
                self.__telegram_messenger.sendImage(image=image)
            else:
                self.__telegram_messenger.sendMessage(full_text=text)

    # def KAKAOTALK_alert(self, text):
    #     """
        
    #     """
    #     self.__kakaotalk_messenger = KakaotalkMessenger(KAKAOTALK_TARGET_URL=self.__KAKAOTALK_TARGET_URL, KAKAOTALK_TOKEN=self.__KAKAOTALK_TOKEN, KAKAOTALK_REFRESH_TOKEN=self.__KAKAOTALK_REFRESH_TOKEN)
    #     self.__kakaotalk_messenger.sendMessage(full_text=text, config_path=self.__config_path)
        # self.__kakaotalk_messenger.refreshToken(self.__config_path)

    def LINE_alert(self, text, *image):
        """
        :param text (str): set message contents
        :param *image (list): set image information list

        :return: None
        """
        for user in self.__LINE_USER:
            LINE_TARGET_URL=user["LINE_TARGET_URL"]
            LINE_TOKEN=user["LINE_USER_TOKEN"]
            self.__line_messenger = LineMessenger(LINE_TARGET_URL=LINE_TARGET_URL, LINE_TOKEN=LINE_TOKEN, mode_type=self.__mode_type)
            if image == True:
                self.__line_messenger.sendMessageImage(full_text=text, image=image)
            else:
                self.__line_messenger.sendMessage(full_text=text)

    def DOORAY_alert(self, text, *image):
        """
        :param text (str): set message contents
        :param *image (list): set image information list

        :return: None
        """
        for user in self.__DOORAY_USER:
            DOORAY_TARGET_URL=user["DOORAY_TARGET_URL"]
            DOORAY_TOKEN=user["DOORAY_USER_TOKEN"]
            self.__dooray_messenger = DoorayMessenger(DOORAY_TARGET_URL=DOORAY_TARGET_URL, DOORAY_TOKEN=DOORAY_TOKEN, mode_type=self.__mode_type)
            if image == True:
                self.__dooray_messenger.sendMessageImage(full_text=text, image=image)
            else:
                self.__dooray_messenger.sendMessage(full_text=text)


def AlertError(text_content, key_path, image_path, message_platform_list, mode_type='virtual'):
    """
    send Message to Researcher to notify our system's errors

    :param text_content (str): message information
    :param key_path (str): set information.json key path
    :param image_path (str): set image of error scene
    :param message_platform_list (list): set platform type list
    :param mode_type='virtual' (str): set mode type. ex) "virtual","real"
    
    :return: True
    """
    messenger_bot = DigitalSecretary(key_path=key_path, mode_type=mode_type)
    text_content = text_content
    image_byte_content = messenger_bot._makeImg2Byte(image_path=image_path)
    image_byte_content_read = image_byte_content.read()
    # messenger_bot.FACEBOOK_MESSENGER_alert(text=text_content, image_path=image_path)
    # time.sleep(3)
    # messenger_bot.MAIL_alert(toPerson_ID=mail_toPerson_ID, text=text_content, image=image_byte_content, image_path=image_path)
    # time.sleep(3)
    # messenger_bot.TELEGRAM_alert(text=text_content, image=image_byte_content_read)
    # time.sleep(3)
    try:
        if "line" in message_platform_list:
            messenger_bot.LINE_alert(text=text_content, image=image_byte_content_read)
        # elif "mail" in message_platform_list:
        #     MAIL_alert(toPerson_ID_list=mail_toPerson_ID, text=text_content, image=image_byte_content, image_path=image_path)
        elif "telegram" in message_platform_list:
            messenger_bot.TELEGRAM_alert(text=text_content, image=image_byte_content_read)
        return True
    except Exception:
        raise Exception("Messenger API is wrong")

def AlertMessage(text_content, key_path, message_platform_list, mode_type="virtual"):
    """
    send Message to Researcher to notify our system's works

    :param text_content (str): message information
    :param key_path (str): set information.json key path
    :param message_platform_list (list): set platform type list
    :param mode_type='virtual' (str): set mode type. ex) "virtual","real"
    
    :return: True
    """
    # messenger_bot.FACEBOOK_MESSENGER_alert(text=text_content, image_path=image_path)
    # time.sleep(3)
    # messenger_bot.MAIL_alert(toPerson_ID=mail_toPerson_ID, text=text_content, image=image_byte_content, image_path=image_path)
    # time.sleep(3)
    # messenger_bot.TELEGRAM_alert(text=text_content, image=image_byte_content_read)
    # time.sleep(3)
    messenger_bot = DigitalSecretary(information_path=key_path, mode_type=mode_type)
    Mail2PersonIDlist = messenger_bot.getMail2PersonIDlist()
    for platform in message_platform_list:
        if platform=="dooray":
            messenger_bot.DOORAY_alert(text=text_content)
        elif platform=="line":
            messenger_bot.LINE_alert(text=text_content)
        elif platform=="mail":
            messenger_bot.MAIL_alert(toPerson_ID_list=Mail2PersonIDlist, text=text_content)
        elif platform=="telegram":
            messenger_bot.TELEGRAM_alert(text=text_content)

    return True

if __name__ == "__main__":
    # meta = {
    #         "subject":"message test",
    #         "researcherGroup":"KIST_CSRC",
    #         "researcherName":"HJ",
    #         "researcherId":"yoohj9475@kist.re.kr",
    #         "researcherPwd":"1234",
    #         "element":"Ag",
    #         "experimentType":"autonomous",
    #         "logLevel":"INFO",
    #         "modeType":"real",
    #         "saveDirPath":"/home/sdl-pc/catkin_ws/src/doosan-robot",
    #         "totalIterNum":1,
    #         "batchSize":8
    #     }
    # AlertMessage("진짜 된다!!", "./Log", message_platform_list=["dooray"], mode_type="real")
    text_list=[
        # "[{}] vial number ({}) is not enough, please move vial to another where".format("BatchSynthesis", 6),
        # "[{}] vial number ({}) is not enough, please fill vial".format("BatchSynthesis", 6),
        # "[{}] tip number ({}) is not enough, please fill tip".format("UV-Vis", 8),
        "[{}] {} is disconnected, please check status of connection".format("UV-Vis", "Pipetting Machine (uArm Swift Pro)"),
    ]
    for text_content in text_list:
        AlertMessage(
                text_content=text_content, 
                key_path="./Log", message_platform_list=["dooray"], mode_type="real")