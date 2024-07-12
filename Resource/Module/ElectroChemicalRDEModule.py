#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [ElectroChemicalRDEModule] ElectroChemicalRDEModule resource allocator class file
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)
# TEST 2024-06-26 13:51:49

import sys
from more_itertools import locate

class ElectroChemicalRDEModule:

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

    def getElectroChemicalRDEModuleResource(self, module_name:str, jobID:int, total_recipe_template_list:list, task_device_location_dict:dict): 
    
        popped_falcon_index_list=[]
        popped_falconHolder_index_list=[]
        while True: # while satisfy "if" condition
            empty_falcon_index_list=self.__find_indexes(task_device_location_dict[module_name]["falcon"], "?")
            empty_falconHolder_index_list=self.__find_indexes(task_device_location_dict[module_name]["falconHolder"], "?")
            if len(total_recipe_template_list) <= len(empty_falcon_index_list) and len(total_recipe_template_list) <= len(empty_falconHolder_index_list):
                break
        for idx in range(len(total_recipe_template_list)):
            popped_falcon_index=empty_falcon_index_list.pop(0) # pop first element in list
            task_device_location_dict[module_name]["falcon"][popped_falcon_index]=jobID
            popped_falcon_index_list.append(popped_falcon_index)
    
            popped_falconHolder_index=empty_falconHolder_index_list.pop(0) # pop first element in list
            task_device_location_dict[module_name]["falconHolder"][popped_falconHolder_index]=jobID
            popped_falconHolder_index_list.append(popped_falconHolder_index)
    
        task_location_dict={
            "falcon":popped_falcon_index_list,
            "falconHolder":popped_falconHolder_index_list,}
        return task_location_dict, task_device_location_dict
    