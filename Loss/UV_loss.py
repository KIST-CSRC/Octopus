#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [Loss] UV target (lambdamax or FWHM) file
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# @version  1_2   
# TEST 2021-11-01
# TEST 2022-04-11


class LossFunction:
    def __init__(self, result_dict, target_condition_dict):
        pass        

    def lambdamaxFWHMintensityLoss(self, result_dict, target_condition_dict):
        """
        calculate loss value

        result_dict (dict): {"GetAbs":{"Wavelength":[...],"RawSpectrum":[...],"Property":{'lambdamax': 667.901297, 'intensity': 0.754869663, 'FWHM': 252.874914}}}
        target_condition_dict (dict): {"GetAbs":{"Property":{"lambdamax":500},"Ratio":{"lambdamax":0.9,"FWHM":0.03, "intenisty":0.07}}}

        :return optimal_value (float) and property_tuple (tuple): optimal_value
        :return total_property_dict (dict)
        """
        total_property_dict={}
        for key, each_action_target_condition_dict in target_condition_dict.items():
            optimal_value=0
            # key --> "GetAbs"
            # each_action_target_condition_dict --> {"Property":{"lambdamax":500,"FWHM":100},"Ratio":{"lambdamax":0.8,"FWHM":0.2}}
            target_type_list = list(each_action_target_condition_dict["Ratio"].keys()) # target_type_list --> ["lambdamax"]
            target_optimal_ratio_list = list(each_action_target_condition_dict["Ratio"].values()) # [0.9, 0.03, 0.07]
            # target_value_list = list(each_action_target_condition_dict["Property"].values()) # target_value_list --> [500]
            for target_idx, each_target_type in enumerate(target_type_list): # property 별로 loss 계산하고, optimal_value에 통합
                # target_idx --> 0, 1, 2(lambdamax or FWHM, intensity)
                # each_target_type --> "lambdamax", "FWHM", "intensity"
                if result_dict[key]["Data"]["Property"][each_target_type]==0:
                    optimal_value += -1*target_optimal_ratio_list[target_idx]
                    optimal_value=float(optimal_value)
                else:
                    if each_target_type == "lambdamax":
                        print("each_action_target_condition_dict['Property'][each_target_type]", each_action_target_condition_dict["Property"][each_target_type])
                        # lambdamax_scaling_factor_left = target_value_list[target_idx]-300
                        # lambdamax_scaling_factor_right = 850-target_value_list[target_idx]
                        lambdamax_scaling_factor_left = each_action_target_condition_dict["Property"][each_target_type]-300
                        lambdamax_scaling_factor_right = 850-each_action_target_condition_dict["Property"][each_target_type]
                        
                        if lambdamax_scaling_factor_left>lambdamax_scaling_factor_right:
                            # lambdamax_loss = -abs(target_value_list[maxIdx]-result_dict[key]["Property"][each_target_type][maxIdx])/(lambdamax_scaling_factor_left)*target_optimal_ratio_list[target_idx]
                            # FWHM_loss = -abs(target_value_list[target_idx]-result_dict[key]["Property"][each_target_type][maxIdx])
                            optimal_value -= abs(each_action_target_condition_dict["Property"][each_target_type]-result_dict[key]["Data"]["Property"][each_target_type])/(lambdamax_scaling_factor_left)*target_optimal_ratio_list[target_idx]
                        else:
                            optimal_value -= abs(each_action_target_condition_dict["Property"][each_target_type]-result_dict[key]["Data"]["Property"][each_target_type])/(lambdamax_scaling_factor_right)*target_optimal_ratio_list[target_idx]
                    elif each_target_type == "FWHM":
                        FWHM_scaling_factor = 550
                        optimal_value -= abs(result_dict[key]["Data"]["Property"][each_target_type])/(FWHM_scaling_factor)*target_optimal_ratio_list[target_idx]
                    elif each_target_type == "intensity":
                        optimal_value -= abs(1-result_dict[key]["Data"]["Property"][each_target_type])*target_optimal_ratio_list[target_idx]
                total_property_dict[each_target_type]=result_dict[key]["Data"]["Property"][each_target_type]

        return optimal_value, total_property_dict