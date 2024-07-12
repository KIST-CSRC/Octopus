#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [py example simple] Integration of analysis function for raw spectrum
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)
# TEST 2022-02-21, 2022-08-10, 2024-06-25

import json
import importlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os, time
from collections import OrderedDict


def calculateData(current_func_name:str, data_dict:dict):
    '''
    :param data_dict (dict) : 
        :param raw_data (dict) : 
        {
            "Name": "C:/Data/20211129_113238_Ag_1.json", 
            "Wavelength": [...],
            "RawSpectrum": [...],
        }

    :return: result, raw_data (dict) : 
    raw_data-->{
        "Name": "C:/Data/20YYMMDD_hhmmss_Abs_NP.json",
        "Wavelength": [...],
        "RawSpectrum": [...],
        "Property": {
            "lambdamax":[...],
            "Intensity":[...],
            "FWHM":[...],
        } // add new key:value
    }
    '''
    if len(data_dict)!=0:
        module_name, task_name=current_func_name.split("_")
        module=importlib.import_module(f"Analysis.Module.{module_name}")
        result_log_ver, result_dict = getattr(module, task_name)(data_dict)
        return result_log_ver, result_dict
    else:
        return {}, {}