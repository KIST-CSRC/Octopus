#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [DB_Class] MongoDB Class file
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# @version  1_2   
# TEST 2021-11-01
# TEST 2022-04-11

import os
import os,sys
import time
import json  
from pymongo import MongoClient, MongoReplicaSetClient, WriteConcern, read_concern, ReadPreference

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../TCP_Connection")))
from Task.TCP import ParameterTCP

"""
- Basically Avaliable
    기본적으로 언제든지 사용할 수 있다는 의미를 가지고 있다.
    즉, 가용성이 필요하다는 뜻을 가진다.
- Soft state
    외부의 개입이 없어도 정보가 변경될 수 있다는 의미를 가지고 있다.
    네트워크 파티션 등 문제가 발생되어 일관성(Consistency)이 유지되지 않는 경우 일관성을 위해 데이터를 자동으로 수정한다.
- Eventually consistent
    일시적으로 일관적이지 않은 상태가 되어도 일정 시간 후 일관적인 상태가 되어야한다는 의미를 가지고 있다.
    장애 발생시 일관성을 유지하기 위한 이벤트를 발생시킨다.
"""

class MongoDB_Class(ParameterTCP):
    """
    MongoDB Class treat MongoDB instances, methods.
    
    - getDatabaseNameList()
    - _getCollections(db_name, collection_name)
    - getDocument(db_name, collection_name, query={})
    - sendDocument(db_name, collection_name, document)
    """
    def __init__(self, MasterLogger_obj, mode_type="virtual"):
        super().__init__()

        self.MasterLogger_obj=MasterLogger_obj
        self.platform_name="MongoDB ({})".format(mode_type)
        self.mode_type=mode_type
        self.__mongodb_arg = 'mongodb://{}:{}/'.format(self.routing_table["DB"]["HOST"], self.routing_table["DB"]["PORT"])
        self.__mongo_client = MongoClient(self.__mongodb_arg)
        self.__wc_majority = WriteConcern("majority", wtimeout=1000)
        self.__private_db_list=['admin', 'config', 'local']

    def getDatabaseNameList(self):
        """
        get mongodb database name list

        :return: db_name_list (list) : exclude self.__private_db_list (['admin', 'config', 'local'])
        """
        db_name_list = self.__mongo_client.list_database_names()
        for private_db in self.__private_db_list:
            db_name_list.remove(private_db)

        return db_name_list

    def _getCollections(self, db_name, collection_name):
        """
        get mongodb data incldue content  

        :param db_name (str): input database name
        :param collection_name (str): input collection name

        :return: collection_obj (MongoClient object)
        """
        collection_obj = self.__mongo_client[db_name][collection_name]

        return collection_obj

    def getDocument(self, db_name, collection_name, query_list={}):
        """
        get mongodb document

        :param db_name (str): database name
        :param collection_name (str): collection name
        :param query_list (dict or list): 
            - if query_list==dict: # single query_list
            - elif type(query_list)==list: # Multi-query_list

        :return: res_data_list (list): dicts in list [document, document, ...]
        """
        if self.mode_type=="virtual":
            self.MasterLogger_obj.info(self.platform_name, "Start to get data into DB")
            self.MasterLogger_obj.info(self.platform_name, "Finish to get data into DB")
        else:
            self.MasterLogger_obj.info(self.platform_name, "Start to get data into DB")

            collection_obj = self._getCollections(db_name, collection_name)
            res_data_list=[]
            # single query
            if type(query_list)==dict:
                each_data = collection_obj.find()
                res_data_list.append(each_data)
            # Multi-query
            elif type(query_list)==list:
                for query in query_list:
                    each_data=collection_obj.find(query)
                    res_data_list.append(each_data)
            else:
                raise ValueError("Something wrong")
            self.MasterLogger_obj.info(self.platform_name, "Finish to get data into DB")

            return res_data_list

    def sendDocument(self, db_name, collection_name, document):
        """
        send document in collection_obj

        :param collection_obj (MongoClient object): MongoClient object
        :param document (json or json in list): MongoClient object
        
        :return: True (bool)
        """
        if self.mode_type=="virtual":
            self.MasterLogger_obj.info(self.platform_name, "Start to insert data into DB")
            db_name="mydb1"
            collection_name="foo"
            document=[{"sku": "abc123", "qty": 100}, {"abc": "xyz123", "dldl": 100}, {"Time":time.strftime("%Y%m%d_%H%M%S")}]
            collections = self.__mongo_client[db_name][collection_name]
            def callback(session):
                collections = session.client[db_name][collection_name]
                print(collections.find()[0])
                if type(document)==dict:
                    collections.insert_one(document, session=session)
                elif type(document)==list:   
                    collections.insert_many(document, session=session)

            with self.__mongo_client.start_session() as session:
                session.with_transaction(callback, read_concern=read_concern.ReadConcern('local'),
                                            write_concern=self.__wc_majority,
                                            read_preference=ReadPreference.PRIMARY)
            self.MasterLogger_obj.info(self.platform_name, "Finish to insert data into DB")
        else:
            self.MasterLogger_obj.info(self.platform_name, "Start to insert data into DB")
            collections = self.__mongo_client[db_name][collection_name]
            def callback(session):
                collections = session.client[db_name][collection_name]
                # collections = session.client[db_name][collection_name]
                # print(collections.find()[0])
                if type(document)==dict:
                    collections.insert_one(document, session=session)
                elif type(document)==list:   
                    collections.insert_many(document, session=session)

            with self.__mongo_client.start_session() as session:
                session.with_transaction(callback, read_concern=read_concern.ReadConcern('local'),
                                            write_concern=self.__wc_majority,
                                            read_preference=ReadPreference.PRIMARY)
            self.MasterLogger_obj.info(self.platform_name, "Finish to insert data into DB")

        return True


if __name__ == "__main__":

    import os, sys
    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))  # get import path : Logging_Class.py
    from Log.Logging_Class_previous import MasterLogger
    log_obj=MasterLogger()
    DB_obj=MongoDB_Class(log_obj, mode_type="real")
    DB_obj.sendDocument(db_name="mydb1", collection_name="foo", document=[{"sku": "abc123", "qty": 100}, {"abc": "xyz123", "dldl": 100}, {"Time":1, "test":0}])
    print(DB_obj.getDatabaseNameList())
    print(DB_obj.getDocument(db_name="mydb1", collection_name="foo"))

    # client = MongoClient('mongodb://161.122.22.146:27017,161.122.22.146:27017/?replicaSet=myRepl')
    # client = MongoClient('mongodb://161.122.22.146:27017/')
    # wc_majority = WriteConcern("majority", wtimeout=1000)
    # # Prereq: Create collections.
    # client.get_database(
    #     "mydb1", write_concern=wc_majority).foo.insert_one({'abc': 0})
    # client.get_database(
    #     "mydb2", write_concern=wc_majority).bar.insert_one({'xyz': 0})
    # # Step 1: Define the callback that specifies the sequence of operations to perform inside the transactions.
    # def callback(session):
    #     collection_one = session.client.mydb1.foo
    #     collection_two = session.client.mydb2.bar
    #     # Important:: You must pass the session to the operations.
    #     collection_one.insert_one({'abc': 1}, session=session)
    #     collection_two.insert_one({'xyz': 999}, session=session)
    #     print("Hello!!!")
    # # Step 2: Start a client session.
    # with client.start_session() as session:
    #     # Step 3: Use with_transaction to start a transaction, execute the callback, and commit (or abort on error).
    #     session.with_transaction(
    #         callback, read_concern=read_concern.ReadConcern('local'),
    #         write_concern=wc_majority,
    #         read_preference=ReadPreference.PRIMARY)