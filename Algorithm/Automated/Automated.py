#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [Automatic.py] Bayesian Optimization Discrete file
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# @version  1_1

import json
import numpy as np
import time
import pickle
import os, sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

class Automatic:
    
    def __init__(self, algorithm_dict, **kwargs):
        for key, value in algorithm_dict.items():
            setattr(self, key, value)

    def suggestNextStep(self):
        """
        :return next_points (dict): candidate of condition
        """
        return self.inputParams
