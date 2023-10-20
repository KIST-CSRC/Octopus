#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @brief    [UserManager] UserManager Class for managing user information during login process
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)
# @version  1_1    
# TEST 2023-10-19

import hashlib
import sqlite3
import time

class UserManager(object):

    def __init__(self):
        self.conn = sqlite3.connect("UserManager/user.db")
        self.cursor = self.conn.cursor()
        try:
            self.cursor.execute("SELECT * FROM your_table")
        except sqlite3.OperationalError as e:
            self.db_create_table()
        self.__covert_num=40

    def __convertPassword(self, password):
        for i in range(self.__covert_num):
            # 비밀번호를 해시화하기 위한 해시 함수 선택 (여기서는 SHA256 사용)
            hash_func = hashlib.sha256()

            # 비밀번호를 바이트로 변환하여 해시 함수에 업데이트
            hash_func.update(password.encode())

            # 해시된 비밀번호 출력
            password = hash_func.hexdigest()
        return password

    def db_create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                password TEXT
            )
        ''')
        self.conn.commit()

    def db_insert_user(self, username, password):
        convert_password=self.__convertPassword(password=username+password)
        self.cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, convert_password))
        self.conn.commit()

    def db_update_user_password(self, username, new_password):
        convert_password=self.__convertPassword(password=username+new_password)
        self.cursor.execute('UPDATE users SET password = ? WHERE username = ?', (convert_password, username))
        self.conn.commit()

    def db_delete_user(self, username):
        self.cursor.execute('DELETE FROM users WHERE username = ?', (username,))
        self.conn.commit()

    def db_get_user_info(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_info = cursor.fetchone()
        if user_info:
            return {"username": user_info[1], "password": user_info[2]}
            # return {"id": user_info[0], "username": user_info[1], "password": user_info[2]}
        else:
            None

    def db_close(self):
        self.conn.close()

    def matchPassword(self, input_user_name, input_user_password):

        stored_user_info=self.db_get_user_info(input_user_name)

        password=input_user_name+input_user_password
        converted_password=self.__convertPassword(password)

        converted_user_info= {
            "username": input_user_name,
            "password": converted_password
        }

        # print("converted_user_info:", converted_user_info)
        # print("stored_user_info:",stored_user_info)
        if stored_user_info==None:
            login_status="login failure: no user information. Please register your username, password via admin"
        else:
            if converted_user_info == stored_user_info:
                login_status = 'login success'
            else:
                if converted_user_info["username"]==stored_user_info["username"]:
                    login_status = 'login failure: wrong password'
                else:
                    login_status = 'login failure: wrong username'

        return login_status

if __name__ == "__main__":
    user_manager_obj=UserManager()
    # user_manager_obj.db_create_table()
    user_manager_obj.db_insert_user("admin", "selfdriving!")
    user_manager_obj.db_insert_user("HJ", "123123")
    user_manager_obj.db_insert_user("NY", "123123")
    user_manager_obj.db_insert_user("HS", "123123")
    user_manager_obj.db_insert_user("Daeho", "123123")
    result=user_manager_obj.matchPassword("HJ","123123")
    print(result)