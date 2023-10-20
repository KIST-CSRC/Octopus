#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [IntegratedMessenger] LineMessenger Class send our error message to researcher to prevent error immediately
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# TEST 2021-07-21

import os, sys
from MessageAPI.dooray_api import ServiceClient 

class DoorayMessenger:
    """
    DoorayMessenger class send message and image to researcher to recognize our situation
    
    # Variable

    :param DOORAY_TARGET_URL: facebook id
    :param DOORAY_TOKEN: facebook password
    :param mode_type="virtual"

    # Function

    - sendMessage(full_text)
    - sendMessageImage(full_text, image)
    """
    def __init__(self, DOORAY_TARGET_URL, DOORAY_TOKEN, mode_type="virtual"):
        # get information, URL, TOKEN
        self.__DOORAY_TARGET_URL = DOORAY_TARGET_URL
        self.__DOORAY_TOKEN = DOORAY_TOKEN
        self.__platform_name = "{}-{} ({})".format("MessageAPI", "Dooray", mode_type)
        self.mode_type=mode_type

    def sendMessage(self, full_text):
        """
        send message using line message

        :param full_text (str): text information
        """
        if self.mode_type=="real":
            headers={
                    'Authorization': 'dooray-api ' + self.__DOORAY_TOKEN,
                    'Content-Type': 'application/json'
                }
            data={
                'text': full_text,
            }
            service_client=ServiceClient(
                    host=self.__DOORAY_TARGET_URL,
                    request_headers=headers,
                    # /project/v1/projects/{project-id}/posts/{post-id}
                    # POST /messenger/v1/channels/{channeld}/logs
                    ).post(data)
            # suceed request
        elif self.mode_type=="virtual":
            pass

    # def sendMessageImage(self, full_text, image):
    #     """
    #     send message & image using line message

    #     :param full_text (str): text information
    #     :param image (byte): image file
    #     """
    #     if self.mode_type=="real":
    #         try:
    #             response = requests.post(
    #                 url=self.__DOORAY_TARGET_URL,
    #                 headers={
    #                     'Authorization': 'dooray-api ' + self.__DOORAY_TOKEN,
    #                     'Content-Type': 'application/json'
    #                 },
    #                 data={
    #                     'text': full_text,
    #                 },
    #                 # files={
    #                 #     'imageFile' : image
    #                 # }
    #             )
    #             # suceed request

    #         except Exception as e:
    #             print(e)
    #     elif self.mode_type=="virtual":


# from dooray_api import ServiceClient 
# host='https://hook.gov-dooray.com/services/2901831766878928764/3446065439331131231/bT-w4J4mQ1mDCZTT1pxthQ'
# request_headers={
#     'Authorization': 'dooray-api m1olidaukdr7:Lv2nz0ZLT5irff90D2h6kQ',
#     'Content-Type': 'application/json'
# }
# channel_id="3408686331464717947"
# service_client=ServiceClient(
#     host=host,
#     request_headers=request_headers,
#     # /project/v1/projects/{project-id}/posts/{post-id}
#     # POST /messenger/v1/channels/{channeld}/logs
#     ).post({"text":"여러분 dooray도 되네요!!감격스럽습니다"})
#     # ).messenger.v1.channels.direct-send.post({"text":"Hi!!","organizationMemberId":3036855360280884332})
# body, status_code=service_client.to_dict, service_client.status_code
# print(body)
# #  {'organizationMemberId': '2888709708850455062', 'name': '이재준', 'workflowId': '2888709710732876099'}}], 'cc': []}, 'workflowClass': 'registered', 'milestone': None, 'workflow': {'id': '8709710732876099', 'name': '등록'}}}
# print(status_code)
# # curl -H 'Authorization: dooray-api m1olidaukdr7:Lv2nz0ZLT5irff90D2h6kQ' -H 'Content-Type: application/json' -d "text=Hello World&organizationMemberId=3036855360280884332" https://api.dooray.com/messenger/v1/channels/direct-send
# # curl -H 'Authorization: dooray-api m1olidaukdr7:Lv2nz0ZLT5irff90D2h6kQ' -H 'Content-Type: application/json' -s -d '{"text":"자신이 쓰고싶은 내용"}' 'https://hook.gov-dooray.com/services/2901831766878928764/3446065439331131231/bT-w4J4mQ1mDCZTT1pxthQ'