#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [IntegratedMessenger] TelegramMessenger Class send our error message to researcher to prevent error immediately
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# TEST 2021-07-21

import telegram

class TelegramMessenger:
    """
    TelegramMessenger class send message and image to researcher to recognize our situation
    
    # Variable

    :param MasterLogger_obj (MasterLogger_obj): set logging object
    :param TELEGRAM_CHAT_ID (int): token id
    :param TELEGRAM_TOKEN (str): telegram token
    :param mode_type="virtual" (str): set virtual or real mode

    # Function
    - sendMessage(full_text)
    - sendImage(image)
    """
    def __init__(self, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN, mode_type="virtual"):
        self.__platform_name = "{}-{} ({})".format("MessageAPI", "Telegram", mode_type)
        # get information, ID, Token
        self.__TELEGRAM_CHAT_ID = TELEGRAM_CHAT_ID
        self.__TELEGRAM_TOKEN = TELEGRAM_TOKEN
        # make telegram bot object
        self.__bot = telegram.Bot(token = self.__TELEGRAM_TOKEN)
        self.__mode_type=mode_type

    def sendMessage(self, full_text):
        """
        send message using telegram

        :param full_text (str): make full text
        """
        if self.__mode_type=="real":
            try:
                self.__bot.sendMessage(chat_id = self.__TELEGRAM_CHAT_ID, text=full_text)
            except Exception as e:
                print(e)
        elif self.__mode_type=="virtual":
            pass

    def sendImage(self, image):
        """
        send image using telegram

        :param image (str): send image information
        """
        if self.__mode_type=="real":
            try:
                self.__bot.sendPhoto(chat_id = self.__TELEGRAM_CHAT_ID, photo=image)
            except Exception as e:
                print(e)
        elif self.__mode_type=="virtual":
            pass

