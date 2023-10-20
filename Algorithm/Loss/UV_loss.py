#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [Loss] UV target (lambdamax or FWHM) file
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)   
# @version  1_2   
# TEST 2021-11-01
# TEST 2022-04-11
class Loss:
    def __init__(self, result_dict, target_condition_dict):
        self.result_dict = result_dict
        self.target_condition_dict = target_condition_dict
        
    # def intensityLoss(self):
    #     total_property_dict={}
    #     for key, each_action_target_condition_dict in self.target_condition_dict.items():
    #         optimal_value=0
    #         # key --> "GetUVdata"
    #         # each_action_target_condition_dict --> "Property":{"Intensity":0.3},"Ratio":{"Intensity":1}
    #         target_type_list = list(each_action_target_condition_dict["Property"].keys())  # target_type_list --> ["Intensity"]
    #         target_value_list = list(each_action_target_condition_dict["Property"].values()) # target_value_list --> [0.3]
    #         target_optimal_ratio_list = list(each_action_target_condition_dict["Ratio"].values()) # [1.0]
            
    #         for idx, each_target_type in enumerate(target_type_list): # property 별로 loss 계산하고, optimal_value에 통합
    #             # idx --> 0 (Intensity)
    #             # each_target_type --> "Intensity"
                
    #             # if len(self.result_dict[key]["Property"][each_target_type])==0:
    #             #     optimal_value += -1*target_optimal_ratio_list[idx]
    #             # else:
    #             optimal_value -= abs(1-self.result_dict[key]["Property"][each_target_type])*target_optimal_ratio_list[idx]
    #             total_property_dict[each_target_type]=self.result_dict[key]["Property"][each_target_type]

    #     return optimal_value,total_property_dict
    
    # def lambdamaxLoss(self):
    #     """
    #     calculate loss value for targeting lambdamax (this function has 550nm lambdamax target)

    #     :param result_dict (dict): {"GetUVdata":{"Wavelength":[...],"RawSpectrum":[...],"Property":{'lambdamax': [300.214759], 'FWHM': [549.221933]}}}
    #     :param target_condition_dict (dict): {"GetUVdata":{"Property":{"lambdamax":500,"FWHM":100},"Ratio":{"lambdamax":0.8,"FWHM":0.2}}}

    #     :return optimal_value (float): optimal_value
    #     """

    #     for key, each_action_target_condition_dict in self.target_condition_dict.items():
    #         optimal_value=0
    #         # key --> "GetUVdata"
    #         # each_action_target_condition_dict --> {"Property":{"lambdamax":500,"FWHM":100},"Ratio":{"lambdamax":0.8,"FWHM":0.2}}
    #         target_type_list = list(each_action_target_condition_dict["Property"].keys()) # target_type_list --> ["lambdamax", "FWHM"]
    #         target_value_list = list(each_action_target_condition_dict["Property"].values()) # target_value_list --> [500, 100]
    #         target_optimal_ratio_list = list(each_action_target_condition_dict["Ratio"].values()) # [0.8, 0.2]
            
    #         for idx, each_target_type in enumerate(target_type_list): # property 별로 loss 계산하고, optimal_value에 통합
    #             # idx --> 0, 1 (lambdamax or FWHM)
    #             # each_target_type --> "lambdamax", "FWHM"
    #             if len(self.result_dict[key]["Property"][each_target_type])==0:
    #                 optimal_value += -1*target_optimal_ratio_list[idx]
    #             else:
    #                 scaling_factor_left = self.result_dict[key]["Property"][each_target_type][0]-300
    #                 scaling_factor_right = 800-self.result_dict[key]["Property"][each_target_type][0]
    #                 if scaling_factor_left>scaling_factor_right:
    #                     optimal_value += -abs(target_value_list[idx]-self.result_dict[key]["Property"][each_target_type][0])/(scaling_factor_left)*target_optimal_ratio_list[idx]
    #                 else:
    #                     optimal_value += -abs(target_value_list[idx]-self.result_dict[key]["Property"][each_target_type][0])/(scaling_factor_right)*target_optimal_ratio_list[idx]

    #     return optimal_value


    # def lambdamaxFWHMLoss(self):
    #     """
    #     calculate loss value

    #     :param result_dict (dict): {"GetUVdata":{"Wavelength":[...],"RawSpectrum":[...],"Property":{'lambdamax': [300.214759], 'FWHM': [549.221933]}}}
    #     :param target_condition_dict (dict): {"GetUVdata":{"Property":{"lambdamax":500,"FWHM":100},"Ratio":{"lambdamax":0.8,"FWHM":0.2}}}

    #     :return optimal_value (float) and property_tuple (tuple): optimal_value
    #     """
    #     maxIdx=0
    #     for key, each_action_target_condition_dict in self.target_condition_dict.items():
    #         optimal_value=0
    #         # key --> "GetUVdata"
    #         # each_action_target_condition_dict --> {"Property":{"lambdamax":500,"FWHM":100},"Ratio":{"lambdamax":0.8,"FWHM":0.2}}
    #         target_type_list = list(each_action_target_condition_dict["Property"].keys()) # target_type_list --> ["lambdamax", "FWHM"]
    #         target_value_list = list(each_action_target_condition_dict["Property"].values()) # target_value_list --> [500, 100]
    #         target_optimal_ratio_list = list(each_action_target_condition_dict["Ratio"].values()) # [0.8, 0.2]
    #         lambdamax_single=None
    #         intensity_single=None
    #         FWHM_single=None
    #         for target_idx, each_target_type in enumerate(target_type_list): # property 별로 loss 계산하고, optimal_value에 통합
    #             # target_idx --> 0, 1 (lambdamax or FWHM)
    #             # each_target_type --> "lambdamax", "FWHM"
    #             if len(self.result_dict[key]["Property"][each_target_type])==0:
    #                 optimal_value += -1*target_optimal_ratio_list[target_idx]
    #                 lambdamax_single=0
    #                 intensity_single=0
    #                 FWHM_single=0
    #             else:
    #                 Intensity_peaks_list=self.result_dict[key]["Property"]["intensity"]
    #                 maxIdx = Intensity_peaks_list.index(max(Intensity_peaks_list))
    #                 if target_idx == 0:
    #                     lambdamax_scaling_factor_left = self.result_dict[key]["Property"][each_target_type][maxIdx]-300
    #                     lambdamax_scaling_factor_right = 800-self.result_dict[key]["Property"][each_target_type][maxIdx]

    #                     if lambdamax_scaling_factor_left>lambdamax_scaling_factor_right:
    #                         # lambdamax_loss = -abs(target_value_list[maxIdx]-self.result_dict[key]["Property"][each_target_type][maxIdx])/(lambdamax_scaling_factor_left)*target_optimal_ratio_list[target_idx]
    #                         # FWHM_loss = -abs(target_value_list[target_idx]-self.result_dict[key]["Property"][each_target_type][maxIdx])
    #                         optimal_value += -abs(target_value_list[target_idx]-self.result_dict[key]["Property"][each_target_type][maxIdx])/(lambdamax_scaling_factor_left)*target_optimal_ratio_list[target_idx]
    #                     else:
    #                         optimal_value += -abs(target_value_list[target_idx]-self.result_dict[key]["Property"][each_target_type][maxIdx])/(lambdamax_scaling_factor_right)*target_optimal_ratio_list[target_idx]
    #                 else:
    #                     FWHM_scaling_factor = 500
    #                     optimal_value += -abs(self.result_dict[key]["Property"][each_target_type][maxIdx])/(FWHM_scaling_factor)*target_optimal_ratio_list[target_idx]
    #                 lambdamax_single=self.result_dict["GetUVdata"]["Property"]["lambdamax"][maxIdx]
    #                 intensity_single=self.result_dict["GetUVdata"]["Property"]["intensity"][maxIdx]
    #                 FWHM_single=self.result_dict["GetUVdata"]["Property"]["FWHM"][maxIdx]
    #     property_tuple=(lambdamax_single, intensity_single, FWHM_single)
        
    #     return optimal_value, property_tuple

    def lambdamaxFWHMintensityLoss(self):
        """
        calculate loss value

        :param result_dict (dict): {"GetAbs":{"Wavelength":[...],"RawSpectrum":[...],"Property":{'lambdamax': 667.901297, 'intensity': 0.754869663, 'FWHM': 252.874914}}}
        :param target_condition_dict (dict): {"GetAbs":{"Property":{"lambdamax":500},"Ratio":{"lambdamax":0.9,"FWHM":0.03, "intenisty":0.07}}}

        :return optimal_value (float) and property_tuple (tuple): optimal_value
        :return total_property_dict (dict)
        """
        total_property_dict={}
        for key, each_action_target_condition_dict in self.target_condition_dict.items():
            optimal_value=0
            # key --> "GetAbs"
            # each_action_target_condition_dict --> {"Property":{"lambdamax":500,"FWHM":100},"Ratio":{"lambdamax":0.8,"FWHM":0.2}}
            target_type_list = list(each_action_target_condition_dict["Ratio"].keys()) # target_type_list --> ["lambdamax"]
            target_value_list = list(each_action_target_condition_dict["Property"].values()) # target_value_list --> [500]
            target_optimal_ratio_list = list(each_action_target_condition_dict["Ratio"].values()) # [0.9, 0.03, 0.07]
            for target_idx, each_target_type in enumerate(target_type_list): # property 별로 loss 계산하고, optimal_value에 통합
                # target_idx --> 0, 1, 2(lambdamax or FWHM, intensity)
                # each_target_type --> "lambdamax", "FWHM", "intensity"
                if self.result_dict[key]["Data"]["Property"][each_target_type]==0:
                    optimal_value += -1*target_optimal_ratio_list[target_idx]
                    optimal_value=float(optimal_value)
                else:
                    if each_target_type == "lambdamax":
                        lambdamax_scaling_factor_left = target_value_list[target_idx]-300
                        lambdamax_scaling_factor_right = 850-target_value_list[target_idx]

                        if lambdamax_scaling_factor_left>lambdamax_scaling_factor_right:
                            # lambdamax_loss = -abs(target_value_list[maxIdx]-self.result_dict[key]["Property"][each_target_type][maxIdx])/(lambdamax_scaling_factor_left)*target_optimal_ratio_list[target_idx]
                            # FWHM_loss = -abs(target_value_list[target_idx]-self.result_dict[key]["Property"][each_target_type][maxIdx])
                            optimal_value -= abs(target_value_list[target_idx]-self.result_dict[key]["Data"]["Property"][each_target_type])/(lambdamax_scaling_factor_left)*target_optimal_ratio_list[target_idx]
                        else:
                            optimal_value -= abs(target_value_list[target_idx]-self.result_dict[key]["Data"]["Property"][each_target_type])/(lambdamax_scaling_factor_right)*target_optimal_ratio_list[target_idx]
                    elif each_target_type == "FWHM":
                        FWHM_scaling_factor = 550
                        optimal_value -= abs(self.result_dict[key]["Data"]["Property"][each_target_type])/(FWHM_scaling_factor)*target_optimal_ratio_list[target_idx]
                    elif each_target_type == "intensity":
                        optimal_value -= abs(1-self.result_dict[key]["Data"]["Property"][each_target_type])*target_optimal_ratio_list[target_idx]
                total_property_dict[each_target_type]=self.result_dict[key]["Data"]["Property"][each_target_type]

        return optimal_value, total_property_dict

if __name__ == "__main__":
    """
    1. UV_Analysis 를 통해서 람다맥스와 반치폭을 manual 하게 구함
    2. result_dict에 넣어서 target_condition_dict와 연산한 것을 optimal_value로 출력
    """
    # result_dict1={"GetUVdata":{"Property":{'lambdamax': [420.256864] , 'FWHM': [365.664374]}}}
    # result_dict2={"GetUVdata":{"Property":{'lambdamax': [798.705306] , 'FWHM':  [71.48809099999994]}}}
    # result_dict3={"GetUVdata":{"Property":{'lambdamax': [700.33187] , 'FWHM':  [238.02947]}}}
    # result_dict4={"GetUVdata":{"Property":{'lambdamax': [452.039192] , 'FWHM':  [174.23193]}}}
    # result_dict1={"GetUVdata":{"Property":{'lambdamax': [763.493774],'intensity': [0.02617906131263644], 'FWHM': [158.49367399999994]}}}
    # result_dict2={"GetUVdata":{"Property":{'lambdamax': [798.705306] ,'intensity': [0.02617906131263644], 'FWHM':  [235.31000000000006]}}}
    # result_dict3={"GetUVdata":{"Property":{'lambdamax': [485.57] ,'intensity': [0.02617906131263644], 'FWHM':  [171.20000000000005]}}}
    # result_dict4={"GetUVdata":{"Property":{'lambdamax': [682.74] ,'intensity': [0.02617906131263644], 'FWHM':  [231.76999999999998]}}}

    # target_condition_dict1={
    #             "GetUVdata":
    #                 {
    #                     "Property":{"lambdamax":513,"FWHM":96},
    #                     "Ratio":{"lambdamax":0.8,"FWHM":0.2}
    #                 }
    #         }
    # target_condition_dict2={
    #             "GetUVdata":
    #                 {
    #                     "Property":{"lambdamax":573,"FWHM":134},
    #                     "Ratio":{"lambdamax":0.8,"FWHM":0.2}
    #                 }
    #         }
    # target_condition_dict3={
    #             "GetUVdata":
    #                 {
    #                     "Property":{"lambdamax":667,"FWHM":191},
    #                     "Ratio":{"lambdamax":0.8,"FWHM":0.2}
    #                 }
    #         }

    # optimal_value1_1 = lambdamaxFWHMLoss(result_dict=result_dict1,target_condition_dict=target_condition_dict1)
    # optimal_value2_1 = lambdamaxFWHMLoss(result_dict=result_dict2,target_condition_dict=target_condition_dict1)
    # optimal_value3_1 = lambdamaxFWHMLoss(result_dict=result_dict3,target_condition_dict=target_condition_dict1)
    # optimal_value4_1 = lambdamaxFWHMLoss(result_dict=result_dict4,target_condition_dict=target_condition_dict1)
    # print(optimal_value1_1)
    # print(optimal_value2_1)
    # print(optimal_value3_1)
    # print(optimal_value4_1)
    # print( )
    # optimal_value1_2 = lambdamaxFWHMLoss(result_dict=result_dict1,target_condition_dict=target_condition_dict2)
    # optimal_value2_2 = lambdamaxFWHMLoss(result_dict=result_dict2,target_condition_dict=target_condition_dict2)
    # optimal_value3_2 = lambdamaxFWHMLoss(result_dict=result_dict3,target_condition_dict=target_condition_dict2)
    # optimal_value4_2 = lambdamaxFWHMLoss(result_dict=result_dict4,target_condition_dict=target_condition_dict2)
    # print(optimal_value1_2)
    # print(optimal_value2_2)
    # print(optimal_value3_2)
    # print(optimal_value4_2)
    # print( )
    # optimal_value1_3 = lambdamaxFWHMLoss(result_dict=result_dict1,target_condition_dict=target_condition_dict3)
    # optimal_value2_3 = lambdamaxFWHMLoss(result_dict=result_dict2,target_condition_dict=target_condition_dict3)
    # optimal_value3_3 = lambdamaxFWHMLoss(result_dict=result_dict3,target_condition_dict=target_condition_dict3)
    # optimal_value4_3 = lambdamaxFWHMLoss(result_dict=result_dict4,target_condition_dict=target_condition_dict3)
    # print(optimal_value1_3)
    # print(optimal_value2_3)
    # print(optimal_value3_3)
    # print(optimal_value4_3)
    # print( )

    result_dict1={"GetUVdata":{"Property":{'lambdamax': 404.415851,'intensity': 0.043072696794065, 'FWHM': 110.397441}}}
    result_dict2={"GetUVdata":{"Property":{'lambdamax': 401.165333 ,'intensity': 0.466940867, 'FWHM':  380.448824}}}
    result_dict3={"GetUVdata":{"Property":{'lambdamax': 636.23956 ,'intensity': 0.445390398, 'FWHM':  417.371809}}}
    result_dict4={"GetUVdata":{"Property":{'lambdamax': 0, 'intensity': 0, 'FWHM': 0}}}

    target_condition_dict1={
                "GetUVdata":
                    {
                        "Property":{"lambdamax":513},
                        "Ratio":{"lambdamax":0.9,"FWHM":0.03, "intensity":0.07}
                    }
            }
    target_condition_dict2={
                "GetUVdata":
                    {
                        "Property":{"lambdamax":573},
                        "Ratio":{"lambdamax":0.9,"FWHM":0.03, "intensity":0.07}
                    }
            }
    target_condition_dict3={
                "GetUVdata":
                    {
                        "Property":{"lambdamax":667},
                        "Ratio":{"lambdamax":0.9,"FWHM":0.03, "intensity":0.07}
                    }
            }
    optimal_value1_1 = Loss.lambdamaxFWHMintensityLoss(result_dict=result_dict1,target_condition_dict=target_condition_dict1)
    optimal_value2_1 = Loss.lambdamaxFWHMintensityLoss(result_dict=result_dict2,target_condition_dict=target_condition_dict1)
    optimal_value3_1 = Loss.lambdamaxFWHMintensityLoss(result_dict=result_dict3,target_condition_dict=target_condition_dict1)
    optimal_value4_1 = Loss.lambdamaxFWHMintensityLoss(result_dict=result_dict4,target_condition_dict=target_condition_dict1)
    print(optimal_value1_1)
    print(optimal_value2_1)
    print(optimal_value3_1)
    print(optimal_value4_1)
    print( )
    optimal_value1_2 = Loss.lambdamaxFWHMintensityLoss(result_dict=result_dict1,target_condition_dict=target_condition_dict2)
    optimal_value2_2 = Loss.lambdamaxFWHMintensityLoss(result_dict=result_dict2,target_condition_dict=target_condition_dict2)
    optimal_value3_2 = Loss.lambdamaxFWHMintensityLoss(result_dict=result_dict3,target_condition_dict=target_condition_dict2)
    optimal_value4_2 = Loss.lambdamaxFWHMintensityLoss(result_dict=result_dict4,target_condition_dict=target_condition_dict2)
    print(optimal_value1_2)
    print(optimal_value2_2)
    print(optimal_value3_2)
    print(optimal_value4_2)
    print( )
    optimal_value1_3 = Loss.lambdamaxFWHMintensityLoss(result_dict=result_dict1,target_condition_dict=target_condition_dict3)
    optimal_value2_3 = Loss.lambdamaxFWHMintensityLoss(result_dict=result_dict2,target_condition_dict=target_condition_dict3)
    optimal_value3_3 = Loss.lambdamaxFWHMintensityLoss(result_dict=result_dict3,target_condition_dict=target_condition_dict3)
    optimal_value4_3 = Loss.lambdamaxFWHMintensityLoss(result_dict=result_dict4,target_condition_dict=target_condition_dict3)
    print(optimal_value1_3)
    print(optimal_value2_3)
    print(optimal_value3_3)
    print(optimal_value4_3)
    print( )
