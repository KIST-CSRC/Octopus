#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [IntegratedMessenger] KakaotalkMessenger Class send our error message to researcher to prevent error immediately
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# TEST 2021-07-21

import requests
import json
import logging

class KakaotalkMessenger:
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
    def __init__(self, KAKAOTALK_TARGET_URL, KAKAOTALK_TOKEN, KAKAOTALK_REFRESH_TOKEN):
        # get information, URL, TOKEN
        self.__KAKAOTALK_TARGET_URL = KAKAOTALK_TARGET_URL
        self.__KAKAOTALK_TOKEN = KAKAOTALK_TOKEN
        self.__KAKAOTALK_REFRESH_TOKEN = KAKAOTALK_REFRESH_TOKEN

    def makeToken(self, new_rest_api_key, new_authorize_code) -> str:
        url = 'https://kauth.kakao.com/oauth/token'
        new_rest_api_key = new_rest_api_key
        redirect_uri = 'https://example.com/oauth'
        new_authorize_code = new_authorize_code

        data = {
            'grant_type':'authorization_code',
            'client_id':new_rest_api_key,
            'redirect_uri':redirect_uri,
            'code': new_authorize_code,
            }

        response = requests.post(url, data=data)
        tokens = response.json()
        print(tokens)

        with open("kakao_code.json","w") as fp:
            json.dump(tokens, fp)

    def refreshToken(self, config_path) -> str:

        with open("Information.json","r") as f:
            ALL_INFO = json.load(f)

        REST_API_KEY = ALL_INFO["KAKAOTALK"]["KAKAOTALK_rest_api_key"]
        REDIRECT_URI = "https://kauth.kakao.com/oauth/token"

        data = {
            "grant_type": "refresh_token", # 얘는 단순 String임. "refresh_token"
            "client_id":f"{REST_API_KEY}",
            "refresh_token": self.__KAKAOTALK_REFRESH_TOKEN # 여기가 위에서 얻은 refresh_token 값
        }    
    
        resp = requests.post(REDIRECT_URI , data=data)
        new_token = resp.json()
        print(new_token)

        ALL_INFO["KAKAOTALK"]["KAKAOTALK_access_token"] = new_token['access_token']

        with open(config_path, 'w', encoding='utf-8') as make_file:
            json.dump(ALL_INFO, make_file, indent="\t")

        return new_token['access_token']

    def sendMessage(self, full_text, config_path) -> None:
        """
        :param full_text (str): text information
        :param config_path (list): config file path information
        """
        try:
            response = requests.post(
                url=self.__KAKAOTALK_TARGET_URL,
                headers={
                    'Authorization': 'Bearer ' + self.__KAKAOTALK_TOKEN
                },
                data={
                "template_object": json.dumps({
                "object_type":"text",
                "text":full_text,
                "link":{
                    "web_url": "https://developers.kakao.com",
                    "mobile_web_url": "https://developers.kakao.com"
                    },
                "button_title": "바로 확인"})
                }
            )
            # succeed request
            print(response.text)
            print(response.status_code)

            if (response.status_code) == 401:
                self.refreshToken(config_path)
                response = requests.post(
                    url=self.__KAKAOTALK_TARGET_URL,
                    headers={
                        'Authorization': 'Bearer ' + self.__KAKAOTALK_TOKEN
                    },
                    data={
                    "template_object": json.dumps({
                    "object_type":"text",
                    "text":full_text,
                    "link":{
                        "web_url": "https://developers.kakao.com",
                        "mobile_web_url": "https://developers.kakao.com"
                        },
                    "button_title": "바로 확인"})
                    }
                )
                # suceed request
                print(response.text)
                print(response.status_code)

            elif (response.status_code) == 200:
                print("[KakaoTalk] : Send Message!")
            else:
                print(str(response.status_code) + " : Something Error!")

        except Exception as e:
            print(e)

    def sendMessageURL(self, full_text, URL) -> None:
        try:
            response = requests.post(
                url=self.__KAKAOTALK_TARGET_URL,
                headers={
                    'Authorization': 'Bearer ' + self.__KAKAOTALK_TOKEN
                },
                data={
                    "template_object": json.dumps({
                    "object_type":"text",
                    "text":full_text,
                    "link":{
                        "web_url": "https://developers.kakao.com",
                        "mobile_web_url": "https://developers.kakao.com"
                        },
                    "button_title": "바로 확인"})
                }
            )
            # suceed request
            print(response.text)
            print(response.status_code)
            print("[KakaoTalk] : Send Message!")

        except Exception as e:
            print(e)

