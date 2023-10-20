#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [IntegratedMessenger] MailMessenger Class send our error message to researcher to prevent error immediately
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# TEST 2021-07-21

import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


class MailMessenger:
    """
    MailMessenger class send message and image to researcher to recognize our situation
    
    # Variable
    :param MasterLogger_obj (MasterLogger_obj): set logging object
    :param MAIL_GMAIL_USER_ID (str): mail id
    :param MAIL_GMAIL_USER_PWD (str): mail password
    :param mode_type="virtual" (str): set virtual or real mode

    # Function
    - sendEmail(subject, toPersonList, text, *file_information)
    """
    def __init__(self, MAIL_GMAIL_USER_ID, MAIL_GMAIL_USER_PWD, mode_type="virtual"):
        self.__platform_name = "{}-{} ({})".format("MessageAPI", "Mail", mode_type)
        # make mail message object
        self.__msg_obj = MIMEMultipart('alternative')
        self.__MAIL_GMAIL_USER_ID = MAIL_GMAIL_USER_ID
        self.__MAIL_GMAIL_USER_PWD = MAIL_GMAIL_USER_PWD

        self.__msg_obj['From'] = MAIL_GMAIL_USER_ID

        self.__mode_type=mode_type

    def __attachFile(self, file, file_path):
        """
        attach file (image) in html file format

        :param file (byte): file information
        :param file_path (str): file path information
        """
        # attach Image File
        try:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition','attachment; filename="%s"' % os.path.basename(file_path))
            self.__msg_obj.attach(part) 

        except Exception as AttachFileError:
            print("AttachFileError : " + str(AttachFileError))
    
    def __embedText(self, text):
        """
        embed text in html file format

        :param text (str): send text information
        """
        text_obj = MIMEText(text)
        self.__msg_obj.attach(text_obj)

    def __embedFile(self, file_path):
        """
        embed file in html file format

        :param file_path (str): file path information        
        """
        try:
            # Embed Image File
            image_text = MIMEText('<img src="cid:image1">', 'html')
            self.__msg_obj.attach(image_text)
            part_image = MIMEImage(open(file_path, 'rb').read())
            # Define the image's ID as referenced in the HTML body above
            part_image.add_header('Content-ID', '<image1>')
            self.__msg_obj.attach(part_image)
            
        except Exception as EmbedFileError:
            print("EmbedFileError : " + str(EmbedFileError))

    def sendEmail(self, subject, toPersonList, text, *file_information):
        """
        :param subject (str): set email subject
        :param toPersonList (list): input email list
        :param text (str): text information
        :param file_information (list): file path information list
        """
        self.__msg_obj['Subject'] = subject
        self.__msg_obj['toPerson'] = toPersonList
        if file_information == True:
            self.__attachFile(file=file_information[0], file_path=file_information[1])
            self.__embedFile(file_path=file_information[1])
        self.__embedText(text)
        if self.__mode_type=="real":
            try:
                # open port & send e-mail   
                __mailServer = smtplib.SMTP("smtp.gmail.com", 587)
                __mailServer.ehlo()
                __mailServer.starttls()
                __mailServer.ehlo()
                __mailServer.login(self.__MAIL_GMAIL_USER_ID, self.__MAIL_GMAIL_USER_PWD)
                for user in toPersonList:
                    __mailServer.sendmail(self.__MAIL_GMAIL_USER_ID, user, self.__msg_obj.as_string())
                __mailServer.close()

            except Exception as SendEmailError:
                print("SendEmailError : " + str(SendEmailError))
        elif self.__mode_type=="virtual":
            pass