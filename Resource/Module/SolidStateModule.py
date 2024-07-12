#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [SolidStateModule] SolidStateModule resource allocator class file
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)
# TEST 2024-07-12 14:14:10

import sys
from more_itertools import locate

class SolidStateModule:

    def __find_indexes(self, lst:list, value:int):
        """
        extract index in lst, matching with value
        
        Examples
        ----------------
        >>> lst=[0,0,"?","?","?",0,0,0]
        >>> jobID=0
        >>> index_list = self.__find_indexes(lst, jobID)
        >>> print(index_list)
        [0,1,5,6,7] 
        """
        return list(locate(lst, lambda x: x == value))

    def getSolidStateModuleResource(self, module_name:str, jobID:int, total_recipe_template_list:list, task_device_location_dict:dict): 
    
        popped_vialHolder_index_list=[]
        popped_heater_index_list=[]
        while True: # while satisfy "if" condition
            empty_vialHolder_index_list=self.__find_indexes(task_device_location_dict[module_name]["vialHolder"], "?")
            empty_heater_index_list=self.__find_indexes(task_device_location_dict[module_name]["heater"], "?")
            if len(total_recipe_template_list) <= len(empty_vialHolder_index_list) and len(total_recipe_template_list) <= len(empty_heater_index_list):
                break
        for idx in range(len(total_recipe_template_list)):
            popped_vialHolder_index=empty_vialHolder_index_list.pop(0) # pop first element in list
            task_device_location_dict[module_name]["vialHolder"][popped_vialHolder_index]=jobID
            popped_vialHolder_index_list.append(popped_vialHolder_index)
    
            popped_heater_index=empty_heater_index_list.pop(0) # pop first element in list
            task_device_location_dict[module_name]["heater"][popped_heater_index]=jobID
            popped_heater_index_list.append(popped_heater_index)
    
        task_location_dict={
            "vialHolder":popped_vialHolder_index_list,
            "heater":popped_heater_index_list,}
        return task_location_dict, task_device_location_dict
    