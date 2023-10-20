
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ##
# @brief    [py example simple] UV analysis function for raw spectrum
# @author   Nayeon Kim (kny@kist.re.kr), Hyuk Jun Yoo (yoohj9475@kist.re.kr)
# TEST 2022-02-21, 2022-08-10 

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
from scipy.signal import find_peaks, peak_prominences, peak_widths
from collections import OrderedDict

# with open("/home/sdl-pc/catkin_ws/src/doosan-robot/ref_UV.json", "r") as json_file:
#     reference_dict = json.load(json_file)
# with open("/home/sdl-pc/catkin_ws/src/doosan-robot/Abs_UV.json", "r") as json_file:
#     uv_dict = json.load(json_file)


def getCleanSpecturm(uv_dict, reference_dict):
    '''
    get clean spectrum using ref 
    :param uv_dict (dict): get uv information (in dict) belong to USB2000+
    :prarm reference_dict(dict): get uv information (in dict) belong to USB2000+

    :retrun: uv_dict (dict): clean data using reference peak
    '''
    # uv_dict['RawSpectrum'] = [np.log10(np.asarray(reference_dict['RawSpectrum'][i])/np.asarray(uv_dict['RawSpectrum'][i])) for i in range(len(uv_dict['RawSpectrum']))]
    absorbances = []
    for ref, measured  in zip (reference_dict['RawSpectrum'], uv_dict['RawSpectrum']):
        try:
            if ref == 0 or measured == 0:
                continue
            absorbances.append(np.log10(ref/measured))
        except:
            break
    uv_dict['RawSpectrum'] = absorbances
    return uv_dict

def getSpectrumArray(uv_dict):
    '''
    extract rawspectrum data from jsonfile

    :param uv_dict (dict): get uv information (in dict) belong to USB2000+

    :return: rawspectrum (numpy.array): [[Wavelength],[Intensity]]
    '''   
    dataWavelength = uv_dict['Wavelength']
    dataIntensity = uv_dict['RawSpectrum']
    dataWavelength_array = np.array(dataWavelength)
    dataIntensity_array = np.array(dataIntensity)
    concatWavelengthIntensity = np.concatenate((dataWavelength_array, dataIntensity_array),axis = 0)
    rawspectrum = concatWavelengthIntensity.reshape((2,int(len(concatWavelengthIntensity)/2)))

    return rawspectrum

def getLocalSpectrumArray(file_path = ''):
    '''
    extract rawspectrum data from jsonfile

    :param file_path (str): location of UV data file

    :instance uv_dict (dict): get uv information (in dict) belong to USB2000+

    :return: rawspectrum (numpy.array): [[Wavelength],[Intensity]]
    '''   
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # Recipe_Json의 format이 바뀌면 바꿔야할 부분 
    # uv_dict=data[0]["result"][0] 
    # dataWavelength = uv_dict['GetUVdata']['Wavelength']
    # dataIntensity = uv_dict['GetUVdata']['RawSpectrum']
    dataWavelength = data['Wavelength']
    dataIntensity = data['RawSpectrum']
    
    dataWavelength_array = np.array(dataWavelength)
    dataIntensity_array = np.array(dataIntensity)
    concatWavelengthIntensity = np.concatenate((dataWavelength_array, dataIntensity_array),axis = 0)
    rawspectrum = concatWavelengthIntensity.reshape((2,int(len(concatWavelengthIntensity)/2)))

    return rawspectrum

def getSliceSpectrum(rawSpectrum=[],min=350, max=800):
    """
    extract specific range of spectrum

    :param min (int): set minimum point of target Wavelengh range
    :param max (int): set maximum point of target Wavelengh range
    :param rawSpectrum (numpy.array): [[Wavelength],[Intensity]]
    
    :return: sliceSpectrum (numpy.array): sliced spectrum -> range(min, max)
    """
    sliceWavelength=[]
    sliceIntensity=[]
    for i in range(len(rawSpectrum[0])):
        if rawSpectrum[0][i] > min and rawSpectrum[0][i] < max:
            sliceWavelength.append(rawSpectrum[0][i])
            sliceIntensity.append(rawSpectrum[1][i])
    concatWavelengthIntensity = np.concatenate((sliceWavelength, sliceIntensity), axis = 0)
    sliceSpectrum = concatWavelengthIntensity.reshape((2, int(len(concatWavelengthIntensity)/2)))

    return sliceSpectrum

def normalizeSpectrum(input_rawSpectrum):
    '''
    normalize spectrum

    :param input_rawSpectrum (numpy.array): [[Wavelength],[Intensity]]

    :return: input_rawSpectrum (list): normalized input_rawSpectrum

    '''
    wavelength=input_rawSpectrum[0]
    absorbance_spectrum=input_rawSpectrum[1]
    input_rawSpectrum[1] = (absorbance_spectrum - np.min(absorbance_spectrum)) / (np.max(absorbance_spectrum) - np.min(absorbance_spectrum))
    return input_rawSpectrum

def smooth_Boxcar(rawSpectrum, box_size):
    '''
        Remove noise from raw spectrum using boxcar algorithm

        :param rawSpectrum (numpy.array): [[Wavelength],[Intensity]]
        
        :retrun: smoothingSpectrum (numpy.array): rawSpectrum after smoothing -> [[Wavelength],[Intensity]]
    '''
    box = np.ones(box_size)/box_size
    spectrum_smooth = np.convolve(rawSpectrum[1], box, mode='same')
    spectrum_smooth = spectrum_smooth.reshape((1,len(rawSpectrum[1])))
    smoothingSpectrum = np.concatenate((rawSpectrum.T,spectrum_smooth.T), axis=1)
    smoothingSpectrum = np.delete(smoothingSpectrum.T, (1),axis=0)
    return smoothingSpectrum

def analysisMultiPeak(rawSpectrum, prominence = 0.01, width =20):
    '''
        Anaylsis multi-Peak properties

        :param rawSpectrum (numpy.array): [[Wavelength],[Intensity]]
        :param prominence (float): minimum peak Intensity for detection
        :param width (int): minumum peak width for detection(ref. theoretical limits=22nm)

        :return: lambdamax_list (list): wavelength of each peaks
        :return: Intensity_peaks_list (list): intensity of each peaks
        :return: FWHM_peaks_list (list): width of each peaks

    '''
    Idx_peaks, properties = find_peaks(rawSpectrum[1], prominence=prominence, width=width)
    lambdamax_list = []
    Intensity_peaks_list = []
    FWHM_peaks_list = []

    if len(Idx_peaks)==0:
        pass

    else:    
        lambdamax_list = rawSpectrum[0][Idx_peaks].tolist()
        Intensity_peaks_list = properties["prominences"].tolist()
        FWHM_peaks_list = [rawSpectrum[0][int(properties["right_ips"][i])]-rawSpectrum[0][int(properties["left_ips"][i])] for i in range(len(properties['right_ips']))]
        
    return lambdamax_list, Intensity_peaks_list, FWHM_peaks_list

def analysisSinglePeak(rawSpectrum, prominence = 0.01, width = 20):
    '''
    Anaylsis single-Peak properties

    :param rawSpectrum (numpy.array): [[Wavelength],[Intensity]]
    :param prominence (float): minimum peak Intensity for detection
    :param width (int): minumum peak width for detection

    :return: max_Wavelength (float): wavelength of each peaks
    :return: max_Intensity (float): intensity of each peaks
    :return: max_FWHM (float): width of each peaks

    '''    
    Wavelength_peaks, Intensity_peaks, FWHM_peaks = analysisMultiPeak(rawSpectrum,  prominence=prominence, width=width)
    max_Wavelength = 0
    max_Intensity = 0
    max_FWHM = 0
    if len(Wavelength_peaks) == 0:
        pass
    else:    
        maxIdx = Intensity_peaks.index(max(Intensity_peaks))

        max_Wavelength = Wavelength_peaks[maxIdx] # Wavelength_peaks[maxIdx] = [value]
        max_Intensity = Intensity_peaks[maxIdx]
        max_FWHM = FWHM_peaks[maxIdx]

    return max_Wavelength, max_Intensity, max_FWHM

def getPlot(Wavelength_peaks, smooth_result, prominence=0.01, width=20, filename="test.png"):
    dir_name=time.strftime("%Y%m%d")
    TOTAL_PLOT_FOLDER = "{}/{}/{}/{}".format("DB","plot",dir_name, "individualPlot")
    if os.path.isdir(TOTAL_PLOT_FOLDER) == False:
        os.makedirs(TOTAL_PLOT_FOLDER)

    Idx_peaks, properties = find_peaks(smooth_result[1], prominence=prominence, width=width)

    if len(Wavelength_peaks)==0:
        plt.plot(smooth_result[0],smooth_result[1])
        plt.title(filename)
    else: 
        Idx_peaks = []
        properties["left_ips"]=properties["left_ips"].astype(int)
        properties["right_ips"]=properties["right_ips"].astype(int)
        
        for i in Wavelength_peaks:
            Idx_peaks.extend(np.where(smooth_result[0]==i)[0])
        plt.plot(smooth_result[0],smooth_result[1])
        plt.plot(Wavelength_peaks, smooth_result[1][Idx_peaks], "x")
        plt.title(filename)
        
        plt.vlines(x=smooth_result[0][Idx_peaks], ymin=smooth_result[1][Idx_peaks] - properties["prominences"],
            ymax = smooth_result[1][Idx_peaks], color = "C1")
        
        for i in range(len(Wavelength_peaks)):
            plt.hlines(y=properties["width_heights"][i], xmin=smooth_result[0][properties["left_ips"][i]],
            xmax=smooth_result[0][properties["right_ips"][i]], color = "C1")

    plot_filename="{}/{}".format(TOTAL_PLOT_FOLDER, filename)
    plt.savefig(plot_filename)
    plt.close()

def comparePlot(UV_result, MasterLoggerName, experiment_num, filename):
    """
    :params: UV_result (numpy.array)
    => [
        "Wavelength": [...],
        "RawSpectrum": [...],
    ]
    :param masterLoggerName (str): implement in dirname of plot --> self.MasterLoggerName
    :param experiment_num=0 (int): similar with cycle_num
    :param filename (str): implement in filename of plot
    """
    dir_name=time.strftime("%Y%m%d")
    TOTAL_PLOT_FOLDER = "{}/{}/{}/{}".format("DB","plot",dir_name, "comparePlot")
    if os.path.isdir(TOTAL_PLOT_FOLDER) == False:
        os.makedirs(TOTAL_PLOT_FOLDER)
    literature_data={
        "Find lambda_max=513nm & FWHM=96nm":"Analysis/Dataset(513nm).csv",
        "Find lambda_max=573nm & FWHM=134nm":"Analysis/Dataset(573nm).csv",
        "Find lambda_max=667nm & FWHM=191nm":"Analysis/Dataset(667nm).csv",
    }
    literauture_df=None
    target_subject=""
    for keys in literature_data.keys():
        if keys in MasterLoggerName:
            literauture_df=pd.read_csv(literature_data[keys])
            target_subject=keys
            break
    literauture_df
    literature_x=literauture_df["Wavelength"].to_numpy()
    literature_y=literauture_df["Intensity"].to_numpy()

    f, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(literature_x,literature_y, linewidth=2.0, color="#800000", label="literature")
    ax.plot(UV_result[0],UV_result[1], linewidth=2.0, color="#000080",label="our result")
    # ax.fill_between(x_extra, y_extra, color='#FA8072', alpha=.25)
    ax.set(xlim=(300.0, 800.0))
    plt.title(target_subject)
    filename="{}/{}_{}(literature vs our result).png".format(TOTAL_PLOT_FOLDER, target_subject, experiment_num)
    plt.legend()
    plt.savefig(filename)
    plt.close()

def calculateUV_Data(uv_dict, reference_dict, WavelengthMin=300, WavelengthMax=849, BoxCarSize=10, Prominence=0.01, PeakWidth=20):
    '''
    Anaylsis multi-Peak properties

    :param uv_dict (dict) : 
    {
        "Name": "C:/Data/20211129_113238_Ag_1.json", 
        "Wavelength": [...],
        "RawSpectrum": [...],
    }
    :param WavelengthMin=300 (int): slice wavlength section depending on WavelengthMin and WavelengthMax
    :param WavelengthMax=800 (int): slice wavlength section depending on wavelength_min and WavelengthMax
    :param BoxCarSize=10 (int): smooth strength
    :param Prominence=0.01 (float): minimum peak Intensity for detection
    :param width=20 (int): minumum peak width for detection
    :param experiment_num=0 (int): similar with cycle_num
    :param masterLoggerName (str): implement in filename of plot

    :return: UV_result, uv_dict (dict) : 
    uv_dict-->{
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
    
    clean_dict=getCleanSpecturm(uv_dict,reference_dict)
    rawSpectrum = getSpectrumArray(uv_dict=clean_dict)
    sliceSpectrum = getSliceSpectrum(rawSpectrum, min=WavelengthMin, max=WavelengthMax)
    smooth_result = smooth_Boxcar(sliceSpectrum,box_size=BoxCarSize)
    lambdamax_list, Intensity_peaks_list, FWHM_peaks_list = analysisMultiPeak(rawSpectrum=smooth_result, prominence=Prominence, width=PeakWidth)
    lambdamax_single, Intensity_peaks_single, FWHM_peaks_single = analysisSinglePeak(rawSpectrum=smooth_result, prominence=Prominence, width=PeakWidth)

    UV_result = OrderedDict()
    # UV_result["lambdamax_multi"] = lambdamax_list
    # UV_result["intensity_multi"] = Intensity_peaks_list
    # UV_result["FWHM_multi"] = FWHM_peaks_list
    UV_result["lambdamax"] = lambdamax_single
    UV_result["intensity"] = Intensity_peaks_single
    UV_result["FWHM"] = FWHM_peaks_single

    uv_dict["Property"]=UV_result
    
    # normalize_spectrum = normalizeSpectrum(smooth_result)
    # plot_filename="{}_{}.png".format(masterLoggerName, experiment_num)
    # getPlot(lambdamax_list, smooth_result=smooth_result, filename=plot_filename)
    # comparePlot(normalize_spectrum, masterLoggerName, experiment_num, plot_filename)

    return UV_result, uv_dict


if __name__ == "__main__":
    rawSpectrum = getLocalSpectrumArray(file_path="./Analysis/test_recipe4.json")
    # clean_dict=getCleanSpecturm(uv_dict,reference_dict)
    # rawSpectrum = getSpectrumArray(uv_dict=clean_dict)
    sliceSpectrum = getSliceSpectrum(rawSpectrum=rawSpectrum, min=300, max=850)
    # print(sliceSpectrum)
    smooth_result = smooth_Boxcar(sliceSpectrum,60)
    # Idx_peaks, properties = find_peaks(sliceSpectrum[1], prominence=0.001, width=20)

    # Wavelength_peaks, Intensity_peaks, FWHM_peaks  = analysisSinglePeak(rawSpectrum=smooth_result, prominence=0.01, width=20) 
    Wavelength_peaks, Intensity_peaks, FWHM_peaks = analysisMultiPeak(rawSpectrum=smooth_result, prominence=0.01, width=20) 
    # FWHM_peaks_list = peak_widths(sliceSpectrum[1], Idx_peaks, rel_height = 0.5)
    print('lambda: ',Wavelength_peaks, 'Intensity: ', Intensity_peaks, 'maxFWHM: ', FWHM_peaks)