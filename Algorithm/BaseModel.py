import math
import datetime
import matplotlib as mpl
import numpy as np
import pandas as pd
import time
import random
from itertools import product
from Self_Driving_Lab_KIST.Algorithm.Bayesian import BayesianOptimization, UtilityFunction
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class ControlPandas(object):
    '''
        __author__ = Hyuk Jun's Yoo (KIST, Computational Science Research Center)

        DataPreprocessing class control all of data.

        Method 
        ------------------------------------------------------------
        - read_DF_2_csv(self, path, filename):
        - init_DF(self, path, filename, column_list):
        - make_DF(self, column_list):
        - save_DF_2_csv(self, path, filename, df):
        - load_df_2_Xy(self, df, feature_columns, y_column):
    '''
    def read_DF_2_csv(self, path, filename):
        """
            Purpose : read file in (path+filname) route. if file doesn't exist in route, raise OsError
            input : input path, filename
            return : df, DataFrame (type : pandas.DataFrame)
        """
        try:
            df = pd.read_csv(path +'/'+filename)
            return df
        except:
            raise OSError

    def read_DF_2_json(self, path, filename):
        """
            Purpose : read file in (path+filname) route. if file doesn't exist in route, raise OsError
            input : input path, filename
            return : df, DataFrame (type : pandas.DataFrame)
        """
        try:
            df = pd.read_json(path +'/'+filename, orient='records')
            return df
        except:
            raise OSError

    def init_DF(self, path, filename, column_list):
        """
            Purpose : if file exists, read // else, make DF, 
            input : input path, filename, column_list
            return : DataFrame(type : pandas.DataFrame)
        """
        try:
            df = self.read_DF_2_csv(path, filename)
        except:
            df = self.make_DF(column_list)
        finally:
            print("DataFrame Success!")

        return df
           
    def make_DF(self, column_list):
        """
            Purpose : make DataFrame based on column_list.
            input : input path, filename
            return : Empty DataFrame which has only columns (type : pandas.DataFrame)
        """
        
        df = pd.DataFrame(columns=column_list)
        return df
    
    def save_DF_2_csv(self, path, filename, df):
        """
            Purpose : save df(DataFrame) in csv.file. if Error, print Error code.
            input : input path (./Algorithm/Gaussian), filename
            return : Nothing, only execute
        """
        try:
            df.to_csv (path+'/'+filename, index = False, header=True)
        except Exception as e:
            print(e,' : Something is wrong about file')
            
    def save_DF_2_json(self, path, filename, df):
        """
            Purpose : save df(DataFrame) in csv.file. if Error, print Error code.
            input : input path (./Algorithm/Gaussian), filename
            return : Nothing, only execute
        """
        try:
            df.to_json (path+'/'+filename, orient='records')
        except Exception as e:
            print(e,' : Something is wrong about file')
            
    def load_df_2_Xy(self, df, feature_columns, y_column):
        """
            Purpose : input DataFrame and extract real X, y.
            input : input df (if columns = para1, para2 ... paraN, Result, Data_Type...), feature_columns (['NaBH4', 'KBr']), y_column ('Result') 
            return : X, y (type : numpy.array)
        """
        try:
            # df[[]] vs df[]
            # df[] : series // df[[]] : DataFrame
            y_test = df[y_column]
            y_test = np.array([y_test]).T

            # feature_columns = list(df.columns.difference(['Result']))
            X_test = df[feature_columns]
            X_test = np.array(X_test)
            
            return X_test, y_test
        
        except TypeError:
            raise TypeError


class ControlNumpy(object):
    '''
        __author__ = Hyuk Jun's Yoo (KIST, Computational Science Research Center)

        The Purpose of ControlNumpy class control all of data using Numpy.

        Method : 
        ------------------------------------------------------------
        - sep_2D_linspace(self, X, space_range=50):
        - sep_nD_linspace(self, X, space_range=50):
        - make_2D_lattice(self, x1, x2):
        - make_fisrt_6point_y(self, total_cycle=6):
        - make_uniform_6point(self, x1_range, x2_range, total_point=6):
        - make_random_point(self, data_range_list, digit_criterion=2):
        - make_random_condition(self,get_random_number_amount, data_range_list):
        - seperate_point_2_target_condition(self, data_list):
        - calculate_difference(self, max_point, data_list):
        - judge_stop_cycle(self, max_count ,differenece_param, difference_list):
        
    '''
    def find_minmax_x(self, X_real, y_real):
        """
            Purpose
            ---------
            decrease DataSpace depending on minmax_x

            input
            ---------
            - X_real (type : numpy.array, example : np.array([ [], [] ]))
            - y_real (type : numpy.array, example : np.array([ [], [] ]))

            return
            ---------
            result (type : numpy.array)

            <np.where>
            >>> B = np.array([[1], [2]]) 
            >>> np.where(B==B.max()) 
            (array([1], dtype=int64), array([0], dtype=int64)) == (1,0)
            >>> np.where(B==B.min()) 
            (array([0], dtype=int64), array([0], dtype=int64)) == (0,0)
        """
        max_y = y_real.max()
        min_y = y_real.min()

        max_index = np.where(y_real == max_y)[0][0]
        min_index = np.where(y_real == min_y)[0][0]

        minmax_x = np.array([X_real[min_index], X_real[max_index]])
        
        return minmax_x

    def decrease_datapace(self, minmax_x, X_real, y_real):
        """
            Purpose
            ---------
            decrease DataSpace depending on minmax_x

            input
            ---------
            - minmax_x (type : numpy.array, example : np.array([ [], [] ]))
            - X_real (type : numpy.array, example : np.array([ [], [] ]))
            - y_real (type : numpy.array, example : np.array([ [], [] ]))

            return
            ---------
            x_result, y_result (type : numpy.array)
        """
        x_result = []

        for x in X_real:
            if (x[0] >= minmax_x[:,0].min() and x[0]<= minmax_x[:,0].max()) and (x[1] >= minmax_x[:,1].min() and x[1]<= minmax_x[:,1].max()):
                x_result.append(x)
        x_result = np.array(x_result)

        y_result = []
        for x in x_result:
            selected_x_index = np.where(X_real == x)[0][0]
            y_result.append(y_real[selected_x_index])
        y_result = np.array(y_result)
        
        return x_result, y_result
    
    def sep_2D_linspace(self, X, space_range=50):
        """
            Purpose
            ---------
            seperate x1,x2

            input
            ---------
            - X (only 2-dimension, type : numpy.array)
            - space_range (seperate our x1 --> x1 1, x1 2, x1 3, ..... x1 n)
                space_range's default is 50.
            
            return
            ---------
            x1, x2 (type : numpy.array)
        """
        x1 = np.linspace(X[:,0].min(), X[:,0].max(), space_range) #p
        x2 = np.linspace(X[:,1].min(), X[:,1].max(), space_range) #q
        
        return x1,x2
    
    def sep_nD_linspace(self, X, space_range=50):
        """
            Purpose
            ---------
            seperate x1,x2

            input
            ---------
            - X (only n-dimension, type : numpy.array)
            - space_range (seperate our x1 --> x1 1, x1 2, x1 3, ..... x1 n)
                space_range's default is 50.
            
            return
            ---------
            x1, x2 (type : numpy.array)
        """
        _, length = X.shape
        result = []
        for element in range(length):
            x = np.linspace(X[:,element].min(), X[:,element].max(), space_range) #p
            result.append(x)

        return result
    
    def make_2D_lattice(self, x1, x2):
        """
            Purpose : make lattice using our x1, x2. It seems like lattice to cover data space uniformally.
            input : Input x1, x2. Using x1,x2 that we seperate in data_range, we make all point based on x1,x2
            return : x1x2, (type : numpy.array) (lattice point (to cover surface in matplotlib.pyplot))
        """
        x1x2 = np.array(list(product(x1,x2)))
        
        return x1x2

    def make_fisrt_6point_y(self, total_cycle=6):
        """
            Purpose : insert y_data depending on our condition.
            input : Input X --> return lattice point (to cover surface in matplotlib.pyplot)
            return : y_point_list (type : list)
        """
        y_point_list = []

        for cycle in range(total_cycle):
            y_data = [int(input("Please input "+str(cycle+1)+"'s result respectively : "))]
            y_point_list.append(y_data)

        return y_point_list

    def make_uniform_6point(self, x1_range, x2_range, total_point=6):
        """
            Purpose : dot point intendently to make first point to store database.
            input : Input x1_range, x2_range total_point=6 (we can experiment 6times per cycle.)\
            return : X_point_selected_list (type : list(list)). all 6points' range start 0 value.

            -----------------------
            |          o2       o6|
            |                     |
            |                     |
            |x o3      o5       o4| x2_range
            |                     |
            |                     |
            |          o1         |
            |          x          |
            ---------------------
                    x1_range

        """

        X_point_total_list = [ [x1_range/2 , x2_range/10], 
                        [x1_range/2 , x2_range], 
                        [x1_range/10 , x2_range/2], 
                        [x1_range , x2_range/2], 
                        [x1_range/2 , x2_range/2], 
                        [x1_range , x2_range] ]

        X_point_selected_list=[]
        
        # consider case that cycle < 6 
        for X_point_index in range(total_point):
            X_point_selected_list.append(X_point_total_list[X_point_index])

        return X_point_selected_list

    def make_random_point(self, data_range_list, digit_criterion=2):
        """
            Purpose :  dot point randomly to make random point to store database.
            input : Input data_range_list. For example data_range_list is [(1,10),(0,5)]. digit_criterion is default value,2. 
            return : result (random point, to get random point before start ) (type : list)
        """
        result = []

        # data_range_list = [(1,10) , (0,5)]...etc
        for data_range in data_range_list:
            data_random_point = random.uniform(data_range[0], data_range[1])
            round_data_random_point = round(data_random_point,digit_criterion)
            result.append(round_data_random_point)

        # result = [a, b]
        if result[0] == 0:
            result[0] = 1
        if result[1] == 0:
            result[1] = 1

        return result

    def seperate_data_space(self, Data_space, sep_num=4):
        """
            ------------------------
            |          |           |
            |     3    |     4     |
            |          |           |
            |          |           | x2_range
            -----------------------
            |          |           |
            |          |           |
            |     1    |     2     |
            |          |           |
            ------------------------
                    x1_range

        """
        [(Data_space_x1_1, Data_space_x1_2), (Data_space_x2_1, Data_space_x2_2)] = Data_space

        if sep_num %2 == 1:
            raise ValueError("please input sep_num even number")
        else:
            mid_x1 = Data_space_x1_1 + (Data_space_x1_2 - Data_space_x1_1)/2
            mid_x2 = Data_space_x2_1 + (Data_space_x2_2 - Data_space_x2_1)/2
            space_1 = [(Data_space_x1_1, mid_x1), (Data_space_x2_1, mid_x2)]
            space_2 = [(mid_x1, Data_space_x1_2), (Data_space_x2_1, mid_x2)]
            space_3 = [(Data_space_x1_1, mid_x1), (mid_x2, Data_space_x2_2)]
            space_4 = [(mid_x1, Data_space_x1_2), (mid_x2, Data_space_x2_2)]

            result = [space_1, space_2, space_3, space_4]

            return result
            
    def make_random_condition(self,get_random_number_amount, data_range_list):
        """
            Purpose : modify condition using round function to 
            input : Input get_random_number_amount, data_range_list. 
                get_random_number_amount means how many point we want. This system want 6 point depending on our platform. data_space is such as [(1,10),(0,5)]
            return : condition_list (to fit random point before start ) (type : list)
        """
        condition_list = []
        for _ in range(get_random_number_amount):
            random_point = self.make_random_point(data_range_list, digit_criterion=2)
            condition = {'NaBH4' : random_point[0], 'KBr' : random_point[1]}
            condition_list.append(condition)
        
        return condition_list

    def seperate_point_2_target_condition(self, data_list):
        """
            Purpose : seperate point to target & condition intom list.
            input : Input data_list.
                --> data_list type is list(dict), such as "[{'target': 293.0, 'params': {'NaBH4': 0.5, 'KBr': 0.4}}, {'target': 745.0, 'params': {'NaBH4': 4.5, 'KBr': 3.6}}]"
            return : target_list, condition_list (type : list)
        """
        target_list = [element['target'] for element in data_list]
        condition_list = [element['params'] for element in data_list]

        return target_list, condition_list

    def calculate_difference(self, max_point, data_list):
        """
            Purpose : calculate difference with maxpoint to other point.
            input : input max_point (criterion to stop cycle_count), data_list 
            return : difference_list (type : list)
        """
        data_array = np.array(data_list)
        difference_list = list(data_array - max_point)

        return difference_list


class ControlTime(object):
    """
        __author__ = Hyuk Jun's Yoo (KIST, Computational Science Research Center)

        ControlTime class consists of code that applicate Time.
        
        Method
        -----------------------------------------------------
        - write_time_date(self) : 
        - cal_time(self, previous_time, final_time) :
    """

    def write_time_date(self):
        """
            Purpose : write time, date data
            input : None
            return self_time, date
        """
         # time check
        self_time = time.time()
        date = time.strftime('%c', time.localtime(self_time))
        
        return self_time, date

    def cal_time(self, previous_time, final_time):
        """
            Purpose : calculate time gap which means that our experiment cycle's period.
            input : previous_time, final_time (type : time.time())
            return : 'Total process time : {} day, {} hour, {} min, {} sec'.format(day, hour, min, sec) (type : string)
        """

        # calculate time gap
        total_time = final_time - previous_time
    
        day = total_time//86400
        hour = (total_time%86400)//3600
        min = ((total_time%86400)%3600)//60
        sec = ((total_time%86400)%3600)%60
        
        result = str('Total process time : {} day, {} hour, {} min, {} sec'.format(day, hour, min, sec))

        return result
    
class Draw_3DPlot(object):
    """
        __author__ = Hyuk Jun's Yoo (KIST, Computational Science Research Center)

        DrawPlot is to make Gaussian Process, and this class has 2 parameters (now, but we will expand  parameter more)

        parameter
        ---------------------------------------------------------
        self.X_1_label = X_1_label , self.X_2_label = X_2_label

        Methods
        ---------------------------------------------------------
        - make_2D_lattice_onplot(self, x1x2, y_pred, sep_number):
        - draw_3D_plot(self, X0p ,X1p, Zp, *args, save_img=True):
                
    """
    def __init__(self, X_1_label, X_2_label):
        """
            type --> X_1_label, X_2_label : string.
        """
        self.X_1_label = X_1_label
        self.X_2_label = X_2_label
        
    def make_2D_lattice_onplot(self, x1x2, y_pred, sep_number):
        """
            Purpose
            ----------
            dot point in graph (x1, x2, z)

            input
            ----------
            Input x1x2, y__pred, sep_number 
            
            return
            ----------
            lattice point (to cover surface in matplotlib.pyplot) // return X0p, X1p, Zp
        """

        X0p, X1p = x1x2[:,0].reshape(sep_number,sep_number), x1x2[:,1].reshape(sep_number,sep_number)
        Zp = np.reshape(y_pred,(sep_number,sep_number))
        
        return X0p, X1p, Zp
        
    def draw_3D_plot(self, X0p ,X1p, Zp, *args, save_img=False):
        """
            Purpose
            ----------
            show 3D Graph using matplotlib
            input
            ----------
            Input X0p, X1p, Zp *args save_img
            return
            ----------
            None
        """
        fig = plt.figure(figsize=(10,8))
        ax = fig.add_subplot(111)
        ax.pcolormesh(X0p, X1p, Zp)
        ax = fig.add_subplot(111, projection='3d')            
        ax.plot_surface(X0p,X1p, Zp, rstride=1, cstride=1,alpha=0.3, color='blue', cmap='jet',edgecolor='black')
   
        if args:
            arg1, arg2 = args
            ax.view_init(arg1, arg2)
        plt.xlabel('$'+self.X_1_label+'$')
        plt.ylabel('$'+self.X_2_label+'$')
        plt.show()

        if args == False:
            filename = "face"

        elif args == [20,10]:
            filename = "NaBH4"

        elif args == [0, -90]:
            filename = "KBr"

        dt = datetime.datetime.now()
        dt_string = dt.strftime("%Y-%m-%d-%H-%M")
        if save_img == True:
            final_fig = plt.gcf()
            final_fig.savefig('Plot_jpg/'+ dt_string + filename +'.png', dpi=fig.dpi)

class DataPreprocessing(ControlPandas, ControlNumpy, ControlTime):
    '''
        __author__ = Hyuk Jun's Yoo (KIST, Computational Science Research Center)

        DataPreprocessing class control all of data.

    ------------------------------------------------------------

    * Method : 

    @ ControlPandas
    
        - read_DF_2_csv(self, path, filename):
        - init_DF(self, path, filename, column_list):
        - make_DF(self, column_list):
        - save_DF_2_csv(self, path, filename, df):
        - load_df_2_Xy(self, df, feature_columns, y_column):
    
    @ ControlNumpy
    
        - sep_2D_linspace(self, X, space_range=50):
        - sep_nD_linspace(self, X, space_range=50):
        - make_2D_lattice(self, x1, x2):
        - make_fisrt_6point_y(self, total_cycle=6):
        - make_uniform_6point(self, x1_range, x2_range, total_point=6):
        - make_random_point(self, data_range_list, digit_criterion=2):
        - make_random_condition(self,get_random_number_amount, data_range_list):
        - seperate_point_2_target_condition(self, data_list):
        - calculate_difference(self, max_point, data_list):
        - judge_stop_cycle(self, max_count ,differenece_param, difference_list):

    @ ControlTime

        - write_time_date(self):
        - cal_time(self, previous_time, final_time):
        
    '''
    
if __name__ == "__main__":
    a = ControlTime()

    first_time, first_date = a.write_time_date()
    time.sleep(3)
    next_time, next_date = a.write_time_date()
    
    result = a.cal_time(first_time, next_time)

    print(result)