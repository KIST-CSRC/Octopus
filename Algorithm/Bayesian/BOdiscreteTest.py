#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [BOdisceteTest.py] Bayesian Optimization Discrete file
# @Inspiration
    # https://github.com/fmfn/BayesianOptimization
    # https://github.com/CooperComputationalCaucus/kuka_optimizer
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# @version  1_2   
# TEST 2021-11-01
# TEST 2022-04-11

import random
import json
# from random import random
from re import X
import numpy as np
import time
from collections import Counter
import pickle
import os, sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from Algorithm.Bayesian.bayesian_optimization import DiscreteBayesianOptimization,Events
from Algorithm.Bayesian.target_space import DiscreteSpace, PropertySpace
from Algorithm.Bayesian.util import UtilityFunction
from Algorithm.Earlystopping import EarlyStopping_AutoLab


class ASLdiscreteBayesianOptimization(DiscreteBayesianOptimization):
    """
    This class Discrete Bayesian Optimization for generating synthesis condition in autonomous laboratory.

    :param algorithm_dict (dict) : include all of information about algorithm config
    {
        "sampling_method" : "grid"
        "initRandom":1,
        "batchSize":8,
        "model":"BayesianOptimization",
        "verbose":0,
        "sampler":"greedy",
        "acqMethod":["ucb"],
        "randomState":2,
        "lossTarget":
            {
                "GetUVdata":
                    {
                        "Property":{"lambdamax":550,"FWHM":100},
                        "Ratio":{"lambdamax":1,"FWHM":0}
                    }
            },
        "prange" : 
        {
            "AgNO3" : [500, 3000, 100],
            "NaBH4": [500, 3000, 100]
        }
    }
    :param kwargs: --> suggestion = disc_constrained_acq_max(
                    ac=utility_function.utility,
                    instance=self,
                    **kwargs) 여기로 들어가
    Sub_Params
        :param prange (dict): dict of 3-tuples for variable min, max, step
        :param verbose=2 (int): verbosity
        :param batchSize=8 (int): number of points in a batch (1 cycle에 몇개의 batch 합성을 할 것인가?)
        :param initRandom=1 (int): number of random batches (cycle 초반에 얼마나 random하게 진행할 것인가?)
        :param randomState=1 (int): random seed
        :param sampler=greedy (str): "greedy" or "KMBBO" or "capitalist"
        :param lossTarget (dict) : calculate loss
        :param samplingMethod (str) : "grid" or "latin" or " random" (cycle 초반의 sampling을 어떤 방법으로 진행할 것인가?)
        :param initParameterList=[] (list) : initial condition
        :param constraints=[] (list) : constraint condition
        :param expectedMax=None: float, expected maximum for proximity return (얼마나 max인 것을 찾을 것이냐? )
    """
    def __init__(self, algorithm_dict, **kwargs):
        for key, value in algorithm_dict.items():
            setattr(self, key, value)
        for key, value in self.sampling.items():
            setattr(self, key, value)
        for key, value in self.acq.items():
            setattr(self, key, value)
        for key, value in self.loss.items():
            setattr(self, key, value)
        # self.model=algorithm_dict["model"]
        # self.prange=algorithm_dict["prange"]
        # self.verbose=algorithm_dict["verbose"]
        # self.batchSize=algorithm_dict["batchSize"]
        # self.randomState = algorithm_dict["randomState"]
        # self.verbose = algorithm_dict["verbose"]
            # self.samplingMethod = self.sampling["samplingMethod"]
            # self.samplingNum = self.sampling["samplingNum"]
            
            # self.acqMethod = self.acq["acqMethod"]
            # self.acqSampler = self.acq["acqSampler"]
            # self.acqHyperparameter = self.acq["acqHyperparameter"]
            
            # self.lossMethod = self.loss["lossMethod"]
            # self.lossTarget = self.loss["lossTarget"]
        # self.initParameterList=None
        # self.constraints=[]

        # if "initParameterList" in algorithm_dict:
        #     self.initParameterList=algorithm_dict["initParameterList"]
        # if "constraints" in algorithm_dict:
        #     self.constraints=algorithm_dict["constraints"]
        # if "expectedMax" in algorithm_dict:
        #     self.expectedMax=algorithm_dict["expectedMax"]

        self.countSamplingNum=0
        
        if self.verbose:
            self._prime_subscriptions()
            self.dispatch(Events.OPTMIZATION_START)
        # 여기 바꿈
        self.normPrange=self._getNormalizeList(self.prange)
        DiscreteBayesianOptimization.__init__(self, f=None,
            prange=self.normPrange,
            verbose=int(self.verbose),
            random_state=self.randomState,
            constraints=self.constraints)
        
        self._real_space = DiscreteSpace(target_func=None, prange=self.prange, random_state=self.randomState)
        self._property_space = PropertySpace(pbounds=self.prange, target_condition_dict=self.lossTarget)
        self.earlystopping=EarlyStopping_AutoLab()

        self.max_val = {'proximity': -1, 'iter': 0, 'val': 0}
        self.process_start_time = time.time()

    def _getNormalizeList(self, prange):
        '''
        :param prange (dict) : 
        
        ex)
            {
                "AgNO3" : [100, 3000, 50],
                "H2O2" : [100, 3000, 50],
                "NaBH4": [100, 3000, 50]
            }

        :return : normPrange
        '''
        normPrange={}
        for chemical, rangeList in prange.items():
            new_range_list=[]
            
            new_range_list.append(0) # normalize min value = 0
            new_range_list.append(1) # normalize max value = 1
            new_range_list.append(rangeList[2]/(rangeList[1]-rangeList[0]))

            normPrange[chemical] = new_range_list
        return normPrange

    def _getNormalizedCondition(self, real_next_points):
        """
        convert real condition to normalized condition

        :param real_next_points (list) : 
            [
                {'AgNO3': 3300.0, 'Citrate': 500.0, 'H2O': 1300.0, 'H2O2': 3500.0, 'NaBH4': 3100.0}
                {'AgNO3': 3500.0, 'Citrate': 500.0, 'H2O': 1300.0, 'H2O2': 3500.0, 'NaBH4': 3500.0}
                {'AgNO3': 800.0,  'Citrate': 500.0, 'H2O': 1300.0, 'H2O2': 3500.0, 'NaBH4': 3500.0}
                {'AgNO3': 3500.0, 'Citrate': 500.0, 'H2O': 3500.0, 'H2O2': 3500.0, 'NaBH4': 3500.0}
            ]

        :return : normalized_next_points (list)
        """
        normalized_next_points = []
        for _, next_point in enumerate(real_next_points):
            new_value={}
            for chemical, rangeList in self.prange.items():
                new_value[chemical]=(next_point[chemical]-rangeList[0])/(rangeList[1]-rangeList[0]) # X' = (value - V_min)/(V_max - V_min) 
            normalized_next_points.append(new_value)
        
        return normalized_next_points

    def _getRealCondition(self, normalized_next_points):
        """
        convert normalized condition to real condition

        :param normalized_next_points (list) : 
            [
                {'AgNO3': 0.02123154896, 'Citrate': 0.4563211120887, 'H2O': 0.122471125, 'H2O2': 0.6337412354, 'NaBH4': 1.0}
                ...
            ]

        :return : real_next_points (list)
        """
        real_next_points = []
        for _, normalized_next_point in enumerate(normalized_next_points):
            new_value={}
            for chemical, rangeList in self.prange.items():
                new_value[chemical]=round(normalized_next_point[chemical]*(rangeList[1]-rangeList[0])+rangeList[0])
            real_next_points.append(new_value)
            
        return real_next_points

    def _earlystopping(self, fitness_list):
        """
        :param iter_num (int): iter_num
        :param fitness (int): fitness
        :param bound_expected_max=0.97 (int) : result > bound_expected_max * self.expected_max

        :return : None
        """
        # if result > self.max_val['val']: # result이 max_val의 정보를 가지고 있는 dict에서의 val 값보다 크다면 갱신
        #     self.max_val['val'] = result # result value를 갱신
        #     self.max_val['iter'] = iter_num # result이 어느 iter 까지 가는지 파악하기 위해서

        # # 근접을 구하는 이유는 어느 사이클 부터 근접을 갔는지를 파악하기 위해서
        # if (self.expected_max) and (result > bound_expected_max * self.expected_max) and (self.max_val['proximity'] == -1): 
        #     # expected_max 이거나?
        #     # result이 expected_max 0.97배 했던 것 보다 크거나
        #     # self.max_val['proximity'] == -1 --> 처음 사이클을 시작하는 경우
        #     # self.max_val['proximity'] 을 iter_num으로 갱신, 해당 self.max_val['proximity'] 에서부터 expected_max가 시작됨.
        #     self.max_val['proximity'] = iter_num # result을 제일 먼저 도달한 iter을 갱신
        for fitness in fitness_list:
            earlystoppping_type = self.earlystopping(fitness)

        return earlystoppping_type
    
    def _checkCandidateNumber(self, count, candidate_list):
        """
        to check and cut candidate in "candidate_list" depending on "count" nunmber

        :param count (int): the number of candidate
        :param candidate_list (list): candidate_list. ex) [{}, {}, {}, {} ... ]

        :return candidate_list, trash_list (list, list): candidate_list, trash_list
        """
        trash_list = []
        if len(candidate_list) != count:
            for _ in range(len(candidate_list)-count):
                trash = candidate_list.pop()
                trash_list.append(trash)

        return candidate_list, trash_list
    
    def _register(self, space, params, target):
        """
        space.register(params, target)
        """
        space.register(params, target)

    def _extractParamsTarget(self, space_res_list):
        params_list=[]
        target_list=[]
        for res in space_res_list:
            params_list.append(res["params"])
            target_list.append(res["target"])
        
        return params_list, target_list

    # def _suggestRandomSampling(self, experiment_num):
    #     norm_next_points = [self._space.array_to_params(self.space._bin(
    #                 self._space.random_sample(constraints=self.get_constraint_dict()))) for _ in range(experiment_num)]
        
    #     return norm_next_points

    def _suggestSampling(self,sampling_method, experiment_num):
        """
        :param sampling_method (str) : grid or random or latin
        :param experiment_num (int) : the number of experiments

        :return sampling_list (dicts in list)
        [
            {'AddSolution=AgNO3_Concentration': 125, 'AddSolution=AgNO3_Volume': 150, 'AddSolution=AgNO3_Injectionrate': 150}, 
            {'AddSolution=AgNO3_Concentration': 25, 'AddSolution=AgNO3_Volume': 750, 'AddSolution=AgNO3_Injectionrate': 50}, 
            {'AddSolution=AgNO3_Concentration': 250, 'AddSolution=AgNO3_Volume': 550, 'AddSolution=AgNO3_Injectionrate': 50}, 
            {'AddSolution=AgNO3_Concentration': 300, 'AddSolution=AgNO3_Volume': 350, 'AddSolution=AgNO3_Injectionrate': 50}, 
            {'AddSolution=AgNO3_Concentration': 325, 'AddSolution=AgNO3_Volume': 450, 'AddSolution=AgNO3_Injectionrate': 100}, 
            {'AddSolution=AgNO3_Concentration': 75, 'AddSolution=AgNO3_Volume': 950, 'AddSolution=AgNO3_Injectionrate': 100}, 
            {'AddSolution=AgNO3_Concentration': 175, 'AddSolution=AgNO3_Volume': 800, 'AddSolution=AgNO3_Injectionrate': 150}, 
            {'AddSolution=AgNO3_Concentration': 200, 'AddSolution=AgNO3_Volume': 1150, 'AddSolution=AgNO3_Injectionrate': 150}
        ]
        """
        if sampling_method == "grid":
            if len(self.space.bounds) == 1:
                targetrng = self.space.bounds.tolist()[0] #만약 prange[0]  - Agno3아닌가여
                sample = []
                sampling_list = []
                if experiment_num > 1:
                    for  i in range(experiment_num):
                        step = (max(targetrng) - min(targetrng))/(experiment_num-1)
                        sampling = [min(targetrng) + step* i ]
                        sample.append(sampling)
                    for i in range(len(sample)):
                        round_sample= self.space._bin(sample[i])
                        # print(type(round_sample))
                        sampling_list.append(self._space.array_to_params(round_sample))
                elif experiment_num == 1:
                    sample = random.choice([np.array([500]), np.array([3000])]) 
                    # print(sample)
                    round_sample= self.space._bin(sample)
                    
                    sampling_list.append(self._space.array_to_params(round_sample))
            else :                
                sample =self._space.grid_sample(experiment_num).tolist()
                sampling_list = [] 
                for i in range(len(sample)):
                    round_sample= self.space._bin(sample[i])
                    # if i==0:
                    #     print("previous sample", type(sample[i]))
                    #     print("round_sample",type(round_sample))
                    sampling_list.append(self._space.array_to_params(round_sample))
                    # sampling_list.append(self._space.array_to_params(np.array(sample[i])))

        elif sampling_method == "latin":
            sample =self._space.latin_sample(experiment_num).tolist()        
            sampling_list = [] 
            for i in range(len(sample)):
                round_sample= self.space._bin(sample[i])
                sampling_list.append(self._space.array_to_params(round_sample))

        elif sampling_method == "random":          
            sampling_list = [self._space.array_to_params(self.space._bin(
                        self._space.random_sample(constraints=self.get_constraint_dict()))) for _ in range(self.batchSize)]

        return sampling_list

    def _suggestAI(self, experiment_num):
        if type(self.acqMethod) == str:
            if self.acqMethod == 'ucb':
                temp_utility = UtilityFunction(kind='ucb', kappa=self.acqHyperparameter["kappa"])
            elif self.acqMethod == 'ei':
                temp_utility = UtilityFunction(kind='ei', xi=self.acqHyperparameter["xi"])
            elif self.acqMethod == 'poi':
                temp_utility = UtilityFunction(kind='poi')
            elif self.acqMethod == 'es':
                temp_utility = UtilityFunction(kind='es')
            norm_next_points = self.suggest(temp_utility,sampler=self.acqSampler,
                                    n_acqs=experiment_num) # return list
            if len(norm_next_points) > experiment_num:
                norm_next_points, trash_list = self._checkCandidateNumber(experiment_num, norm_next_points)
                # print("preprcoess norm_next_points: ",len(norm_next_points))
            elif len(norm_next_points)<experiment_num:
                raise ValueError("Candiate of condition is not match to batch_size. norm_next_points: {} != batch_size: {}. Please check this part.".format(str(len(norm_next_points)), str(experiment_num)))
        # list인 경우는 각각 batch의 갯수를 count한 후, 해당 function으로 해당 경우의 수만 suggest 진행
        elif type(self.acqMethod) == list:
            norm_next_points=[]
            # if acqMethod == ['ucb', 'ucb', 'ucb', 'ucb', 'ei', 'ei', 'es', 'es']
            # ucb 4개, ei 2개, es 2개 의 경우를 suggest 한다
            if len(self.acqMethod) == experiment_num:
                acqMethod_dict = Counter(self.acqMethod)
                # acqMethod_dict = {'ucb':4,'ei':2,'es':2}
                for utility_key, count in acqMethod_dict.items():
                    if utility_key == 'ucb':
                        temp_utility = UtilityFunction(kind='ucb', kappa=self.acqHyperparameter["kappa"])
                        ucb_norm_next_points = self.suggest(temp_utility,sampler=self.acqSampler,
                                    n_acqs=count) # return list
                        # print("count:", count)
                        real_ucb_norm_next_points, ucb_trash_list = self._checkCandidateNumber(count, ucb_norm_next_points)
                        # print("real_ucb_norm_next_points : ", real_ucb_norm_next_points, len(real_ucb_norm_next_points))
                        norm_next_points.extend(real_ucb_norm_next_points)
                    elif utility_key == 'ei':
                        temp_utility = UtilityFunction(kind='ei', xi=self.acqHyperparameter["xi"])
                        ei_norm_next_points = self.suggest(temp_utility,sampler=self.acqSampler,
                                    n_acqs=count) # return list
                        # print("count:", count)
                        real_ei_norm_next_points, ei_trash_list = self._checkCandidateNumber(count, ei_norm_next_points)
                        # print("real_ei_norm_next_points : ", real_ei_norm_next_points, len(real_ei_norm_next_points))
                        norm_next_points.extend(real_ei_norm_next_points)
                    elif utility_key == 'poi':
                        temp_utility = UtilityFunction(kind='poi')
                        poi_norm_next_points = self.suggest(temp_utility,sampler=self.acqSampler,
                                    n_acqs=count) # return list
                        # print("count:", count)
                        real_poi_norm_next_points, poi_trash_list = self._checkCandidateNumber(count, poi_norm_next_points)
                        # print("poi_norm_next_points : ", real_poi_norm_next_points, len(real_poi_norm_next_points))
                        norm_next_points.extend(real_poi_norm_next_points)
                    elif utility_key == 'es':
                        temp_utility = UtilityFunction(kind='es')
                        es_norm_next_points = self.suggest(temp_utility,sampler=self.acqSampler,
                                    n_acqs=count) # return list
                        # print("count:", count)
                        real_es_norm_next_points, es_trash_list = self._checkCandidateNumber(count, es_norm_next_points)
                        # print("es_norm_next_points : ", real_es_norm_next_points, len(real_es_norm_next_points))
                        norm_next_points.extend(real_es_norm_next_points)
            else:
                raise IndexError("Please fill utility list to match experiment_num")
        else:
            raise TypeError("Please give string type or filled list")
        
        return norm_next_points

    def _pop_n_items(self, lst, n):
        popped_items = []
        for _ in range(n):
            if lst:
                popped_items.append(lst.pop(0))
            else:
                break
        return popped_items[::-1]

    def suggestNextStep(self):
        """
        :return next_points (dict): candidate of condition
        """
        # init random이 suggest_num보다 작을 때 초기 sampling 
        if self.countSamplingNum < self.samplingNum and (self.countSamplingNum+self.batchSize) < self.samplingNum:
            # 사람이 초기 파라미터를 지정해주지 않는 경우.            
            if len(self.initParameterList)==0: # initParameterList 없으면
                norm_next_points=self._suggestSampling(self.samplingMethod, self.batchSize)
            else: # initParameterList 있으면
                norm_next_points=self._pop_n_items(self.initParameterList, self.batchSize)
        elif self.countSamplingNum < self.samplingNum and (self.countSamplingNum+self.batchSize) > self.samplingNum:
            random_experiment_num=self.samplingNum-self.countSamplingNum
            if len(self.initParameterList)==0: # initParameterList 없으면
                norm_next_points=self._suggestSampling(self.random_experiment_num)
            else: # initParameterList 있으면
                norm_next_points=self._pop_n_items(self.initParameterList, random_experiment_num)
        else: # if self.countSamplingNum satify SamplingNum value
            self._suggestAI(self.batchSize)
        # norm_next_points는 list, dict인 next_point들로 구성
        real_next_points=self._getRealCondition(norm_next_points)

        # count random synthesis condition
        self.countSamplingNum+=len(real_next_points)
        
        return real_next_points, norm_next_points

    def registerPoint(self, input_next_points, norm_input_next_points, property_list, input_result_list):
        """
        :param input_next_points (dict in list) : [{},{},{}] --> this list has sequence of condition which follow utility function
            ex) ['ucb', 'ucb', 'ucb', 'ucb', 'ei', 'ei', 'es', 'es']
        :param input_result_list (dict in list): [] --> include each result_dict, 
                                            this list has sequence of synthesis condition which called input_next_points
        :return : None
        """
        for process_idx, real_next_point in enumerate(input_next_points):
            optimal_value = input_result_list[process_idx]
            self._register(space=self._real_space, params=real_next_point, target=optimal_value)
        for process_idx, property_dict in enumerate(property_list):
            optimal_value = input_result_list[process_idx]
            self._property_space._keys=list(input_next_points[process_idx].keys())+list(property_dict.keys())
            self._register(space=self._property_space, params=list(input_next_points[process_idx].values())+list(property_dict.values()), target=optimal_value)
        for process_idx, norm_next_point in enumerate(norm_input_next_points):
            optimal_value = input_result_list[process_idx]
            self._register(space=self.space,params=norm_next_point, target=optimal_value)

    def output_space_realCondition(self, dirname, filename):
        """
        [Modified by HJ]

        Outputs complete space as csv file. --> convert normalize condition to real condition
        Simple function for testing
        
        Parameters
        ----------
        dirname (str) :"DB/2022XXXX
        filename : "{}_data" + .csv
        
        Returns
        -------
        None
        """
        total_path="{}/{}.csv".format(dirname, filename)
        if os.path.isdir(dirname) == False:
            os.makedirs(dirname)
        df = pd.DataFrame(data=self._real_space.params, columns=self._real_space.keys)
        df['Target'] = self._real_space.target
        df.to_csv(total_path, index=False)

    def output_space_property(self, dirname, filename):
        """
        [Modified by HJ]

        Outputs complete space as csv file. --> extract until all property based on real condition
        Simple function for testing
        
        Parameters
        ----------
        dirname (str) :"DB/2022XXXX
        filename : "{}_data" + .csv
        
        Returns
        -------
        None
        """
        total_path="{}/{}.csv".format(dirname, filename)
        if os.path.isdir(dirname) == False:
            os.makedirs(dirname)
        df = pd.DataFrame(data=self._property_space.params, columns=self._property_space.keys)
        df.to_csv(total_path, index=False)

    def closeModel(self,):
        """
        close model & print time table and maximum value
        
        Parameters
        ----------
        None
        
        Returns
        -------
        opt_msg, max_value_msg
        """
        if self.verbose:
            self.dispatch(Events.OPTMIZATION_END)
        
        self.process_end_time = time.time()
        
        opt_msg = "Time taken for {} optimizaiton: {:8.2f} seconds".format(self.acqSampler, self.process_end_time - self.process_start_time)
        max_value_msg = "Maximum value {:.3f} found in {} batches".format(self.max_val['val'], self.max_val['iter'])
        
        return opt_msg, max_value_msg

    def savedModel(self, directory_path, filename='bo_obj'):
        """
        save ML model to use already fitted model later.
        
        Arguments
        ---------
        directory_path (str)
        filename='bo_obj' (str) +.pickle
        
        Returns
        -------
        return None
        """
        fname = os.path.join(directory_path, filename+".pickle")
        if os.path.isdir(directory_path) == False:
            os.makedirs(directory_path)
        else:
            with open(fname, 'wb') as f:
                pickle.dump(self, f)
                time.sleep(3)
                
    def loadModel(self, directory_path, filename='optimizer'):
        """
        load ML model to use already fitted model later depending on filename.
        
        Arguments
        ---------
        directory_path (str)
        filename='optimizer' (str)
        
        Returns
        -------
        return loaded_model, model_obj
        """
        fname = os.path.join(directory_path, filename+".pickle")

        # try:
        with open(fname, 'rb') as f:
            model_obj = pickle.load(f)
        # except Exception as e:
            # print(e)
            # raise FileNotFoundError("File is not existed")

        return model_obj

def draw2dPlot(x, y, filename):
        xmin, xmax, ymin, ymax = 0, 3000, 0, 3000
        plt.scatter(x[:len(x)-1], y[:len(x)-1], color="orange", s=50)
        if len(x)!=1:
            plt.scatter(x[len(x)-1], y[len(x)-1], color="purple", s=40)
        plt.xlim((xmin, xmax))
        plt.ylim((ymin, ymax))
        plt.savefig(filename+".png")
    
def draw2dPlot_grid(x, y, filename):
    xmin, xmax, ymin, ymax = 0, 3100, 0, 3100
    
    for i in range(1, len(x)):
        plt.scatter(x[:i], y[:i], color="orange", s=50)
        plt.scatter(x[i], y[i], color="purple", s=40)
        plt.xlim((xmin, xmax))
        plt.ylim((ymin, ymax))
        plt.savefig(filename+"_{}.png".format(i))
        plt.close()

def draw3dPlot(x, y, z, filename):
    xmin, xmax, ymin, ymax, zmin, zmax = 100, 3000, 100, 3000, 100, 3000
    cmin, cmax = 0, 2

    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(x, y, z, marker='o', s=15, cmap='Greens')

    plt.xlim((xmin, xmax))
    plt.ylim((ymin, ymax))
    
    ax.set_xlabel('x axis')
    ax.set_ylabel('y axis')
    ax.set_zlabel('z axis')

    plt.savefig(filename+".png")

def calLoss(result_dict, each_target_value, target_optimal_ratio_dict):
    """
    
    :params result_dict (dict) : {"lambdamax":673.88661931, "FWHM":101.1231578843, "intensity":0.34261781872}
    :params each_target_value (dict) : {"lambdamax":573.88661931}
    :params target_optimal_ratio_dict (dict) : {"lambdamax":0.9, "FWHM":0.03, "intensity":0.07}
    """
    optimal_value=0
    for each_target_type, each_property_value in result_dict.items():
        if result_dict[each_target_type]==0:
            optimal_value -= 1*target_optimal_ratio_dict[each_target_type]
        else:
            if each_target_type == "lambdamax":
                lambdamax_scaling_factor_left = each_target_value[each_target_type]-300
                lambdamax_scaling_factor_right = 850-each_target_value[each_target_type]

                if lambdamax_scaling_factor_left>=lambdamax_scaling_factor_right:
                    optimal_value -= abs(each_target_value[each_target_type]-each_property_value)/(lambdamax_scaling_factor_left)*target_optimal_ratio_dict[each_target_type]
                else:
                    optimal_value -= abs(each_target_value[each_target_type]-each_property_value)/(lambdamax_scaling_factor_right)*target_optimal_ratio_dict[each_target_type]
            elif each_target_type == "FWHM":
                FWHM_scaling_factor = 550
                optimal_value -= (each_property_value)/(FWHM_scaling_factor)*target_optimal_ratio_dict[each_target_type]
            elif each_target_type == "intensity":
                optimal_value -= (1-each_property_value)*target_optimal_ratio_dict[each_target_type]
    optimal_value=float(optimal_value)
    return optimal_value

def makePickle():
    target_list=[
        573
    ]
    var_list=[
        3
        ]
    for var in var_list:
        for target in target_list:
            config_json_path="/home/sdl-pc/catkin_ws/src/doosan-robot/config/20230218/2023-02-18_autonomous_BO_var{}_{}nm_make_pickle.json".format(var, target)
            filename="sampling_csv/100-4000 (1_25mM AgNO3, 0_375% H2O2)/latin/latin_{}d_20cycles_seed=0_100_4000.csv".format(var)
            with open(config_json_path, "r") as f:
                config_data_inst = json.load(f)
            bo_object=ASLdiscreteBayesianOptimization(config_data_inst["algorithm"])
            df = pd.read_csv(filename)
            # print(df[['lambdamax']])
            # df_property=df[['lambdamax','intensity','FWHM']]
            df_property=df[list(bo_object.lossTarget["GetUVdata"]["Ratio"].keys())]
            df_condition=df.drop(list(bo_object.lossTarget["GetUVdata"]["Ratio"].keys()), axis=1)
            params=df_condition.to_dict('records')
            norm_params=bo_object._getNormalizedCondition(params)
            propertys=df_property.to_dict('records')
            targets=[]
            for property_value in propertys:
                optimal_loss=calLoss(property_value, bo_object.lossTarget["GetUVdata"]["Property"], bo_object.lossTarget["GetUVdata"]["Ratio"])
                targets.append(optimal_loss)
            bo_object.registerPoint(0, params, norm_params, propertys, targets)
            bo_object.output_space("DB/Ag_autonomous/20230218(make_pickle)/real", config_data_inst["metadata"]["subject"]+"_basedOnLatin")
            bo_object.output_space_realCondition("DB/Ag_autonomous/20230218(make_pickle)/real", config_data_inst["metadata"]["subject"]+"_realCondition_basedOnLatin")
            bo_object.output_space_property("DB/Ag_autonomous/20230218(make_pickle)/real", config_data_inst["metadata"]["subject"]+"_property_basedOnLatin")
            bo_object.savedModel(directory_path="Algorithm/SaveModel/Ag_autonomous/20230218(make_pickle)", filename=config_data_inst["metadata"]["subject"]+"_basedOnLatin")
            new_obj=bo_object.loadModel(directory_path="Algorithm/SaveModel/Ag_autonomous/20230218(make_pickle)", filename=config_data_inst["metadata"]["subject"]+"_basedOnLatin")
            time.sleep(2)
            print(len(new_obj.res))
            print('prange : ',bo_object.prange)
            print('target : ' , bo_object.lossTarget)

if __name__ == "__main__":

    ##################
    # grid sampling
    ##################

    algorithm_dict={
        "model":"BayesianOptimization",
        "samplingMethod":"latin",
        "samplingNum":20,
        "initRandomNum":20,
        "batchSize":6,
        "totalIterNum":1,
        "verbose":0,
        "randomState":0,
        "acquisitionFunc":
        {
            "acqMethod":"ucb",
            "sampler":"greedy",
            "acqHyperparameter":{
                "kappa":10.0
            }
        },
        "loss": "lambdamaxFWHMintensityLoss",
        "lossTarget":
            {
                "GetAbs":
                    {
                        "Property":{"lambdamax":573},
                        "Ratio":{"lambdamax":0.9,"FWHM":0.03, "intensity":0.07}
                    }
            },
        "prange" : 
        {
            "AddSolution=AgNO3_Concentration" : [25, 375, 25],
            "AddSolution=AgNO3_Volume" : [100, 1200, 50],
            "AddSolution=AgNO3_Injectionrate" : [50, 200, 50]
        },
        "initParameterList":[],
        "constraints":[]
    }
    bo_object=ASLdiscreteBayesianOptimization(algorithm_dict)
    grid_result_list=bo_object._suggestSampling("latin", 8)
    print(grid_result_list)
    real_grid_result_list=bo_object._getRealCondition(grid_result_list)
    print(real_grid_result_list)
    # df_grid=pd.DataFrame(real_grid_result_list)

    # df_grid=df_grid.sort_values(by=['AgNO3','H2O2'], ascending=False)
    # # df_grid=df_grid.sort_values(by=['AgNO3','Citrate', 'H2O', 'H2O2', "NaBH4"])
    # print(df_grid.columns)
    # df_grid.to_csv("sampling_csv/100-4000 (1_25mM AgNO3, 0_375% H2O2)/latin/latin_2d_20cycles_seed=0_100_4000.csv",index=False)

    # grid_x=list(df_grid["AgNO3"])
    # grid_y=list(df_grid["H2O2"])
    # grid_z=df_grid["NaBH4"]

    # draw2dPlot_grid(grid_x, grid_y, "random_2d_100cycles")

    ################
    # Latin sampling
    ################
    # total_random_result_list=[]
    # for i in range(10):
    #     algorithm_dict={
    #         "sampling_method" : "latin",
    #         "initRandom":0,
    #         "batchSize":20,
    #         "algorithmType":"BayesianOptimization",
    #         "verbose":0,
    #         "sampler":"greedy",
    #         "acqMethod":["ucb"],
    #         "acquisitionFunc":
    #         {
    #             "acqMethod":"ucb",
    #             "sampler":"greedy",
    #             "hyperparameter":5.0
    #         },
    #         "randomState":i,
    #         "lossTarget":
    #             {
    #                 "GetUVdata":
    #                     {
    #                         "Property":{"lambdamax":513},
    #                         "Ratio":{"lambdamax":0.9,"FWHM":0.03, "intensity":0.07}
    #                     }
    #             },
    #         "prange" : 
    #         {
    #             "AgNO3" : [100, 4000, 50],
    #             "H2O2": [100, 4000, 50],
    #             "NaBH4" : [100, 4000, 50]
    #         }
    #     }

    #     sampling_method=algorithm_dict["sampling_method"]
    #     var_num=len(algorithm_dict["prange"])
    #     cycle_num=algorithm_dict["batchSize"]
    #     random_state=algorithm_dict["randomState"]

    #     bo_object=ASLdiscreteBayesianOptimization(algorithm_dict)
    #     random_result_list=bo_object._getSamplingList(sampling_method)
    #     random_result_list=sorted(random_result_list, key=lambda d: d['AgNO3'])
    #     df_random=pd.DataFrame(random_result_list)
    #     df_random = df_random.loc[:, ~df_random.columns.str.contains('^Unnamed')]

    #     filename="{}_{}var_{}cycles_{}randomState".format(sampling_method, var_num, cycle_num, random_state)
    #     df_random.to_csv(filename+".csv", index=False)

        # random_x=df_random["AgNO3"]
        # random_y=df_random["H2O2"]
        # random_z=df_random["NaBH4"]

        # draw2dPlot(grid_x, grid_y, filename=filename)
        # draw2dPlot(random_x, random_y, filename=filename)
        # draw3dPlot(grid_x, grid_y, grid_z, filename=filename)
        # draw3dPlot(random_x, random_y, random_z, filename=filename)


