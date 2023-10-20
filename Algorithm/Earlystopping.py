#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [EarlyStopping.py] EarlyStopping for autonomous laboratory
# @Inspiration
    # https://github.com/Bjarten/early-stopping-pytorch/blob/master/pytorchtools.py
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# @version  1_1
# TEST 2022-12-01
# TEST 2023-02-11

import numpy as np

class EarlyStopping_AutoLab:
    """
    Early stops the training if validation loss doesn't improve after a given patience.
        fork from https://github.com/Bjarten/early-stopping-pytorch/blob/master/pytorchtools.py

    Customization for autonomous laboratory to add filter
    """
    def __init__(self, patience=5, verbose=False, delta=0, filter_value=-0.1, trace_func=print):
        """
        Args:
            patience (int): How long to wait after last time validation loss improved.
                            Default: 5
            verbose (bool): If True, prints a message for each validation loss improvement. 
                            Default: False
            delta (float): Minimum change in the monitored quantity to qualify as an improvement.
                            Default: 0
            filter_value (float) --> add new arguments: only consider over filter value.
                            Default: -0.1
            trace_func (function): trace print function.
                            Default: print            
        """
        self.patience = patience
        self.verbose = verbose
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        self.val_loss_min = np.Inf
        self.delta = delta
        self.filter_value=filter_value
        self.trace_func = trace_func

    def __call__(self, fitness):
        """
        :param fitness (int): fitness of target nanoparticle

        :return self.early_stop (boolean): return True or False
        """
        score = -fitness

        if score < self.filter_value: # filter function
            pass
        elif score >= self.filter_value: # consider only over filter_value
            if self.best_score is None:
                self.best_score = score
            elif score < self.best_score + self.delta:
                self.counter += 1
                self.trace_func(f'EarlyStopping counter: {self.counter} out of {self.patience}')
                if self.counter >= self.patience:
                    self.early_stop = True
            else:
                self.best_score = score
                self.counter = 0
        
        return self.early_stop