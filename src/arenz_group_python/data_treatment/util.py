"""
Utility module.

"""

import math
from scipy.signal import savgol_filter, medfilt
from scipy import ndimage, datasets
import matplotlib.pyplot as plt


NEWPLOT = "new_plot"

def extract_value_unit(s:str):
    """_summary_

    Args:
        s (str): _description_

    Returns:
        value(float): the extracted value 
        unit(str): extract unit
    """
    unit =""
    value = math.nan
    try:
        list = s.strip().split(" ")
        value = float(list[0])
        unit = list[1]    
    finally:
        pass
    return value, unit



class plot_options:
    def __init__(self, kwargs):
        self.name = NEWPLOT
        self.x_label="x"
        self.x_unit = "xunit"
        self.y_label = "y"
        self.y_unit = "y_unit"
        self.x_data = []
        self.y_data =[]
        #self.x = tuple(self.x_data,self.x_label,self.x_unit)
        self.options = {
            'x_smooth' : 0,
            'y_smooth' : 0,
            'y_median'   : 0,
            'plot' : NEWPLOT,
            'dir' : "all",
            'legend' : "noName",
            'xlabel' : "def",
            'ylabel' : "def",
            'style'  : ""
        }

        self.options.update(kwargs)
        return
    
    def set_y_txt(self, label, unit):
        self.y_label = label
        self.y_unit = unit
        
    def set_x_txt(self, label, unit):
        self.x_label = label
        self.x_unit = unit
        

    def get_y_txt(self):
        return str(self.y_label + "("+ self.y_unit +")")
    def get_x_txt(self):
        return str(self.x_label + "("+ self.x_unit +")")
    
    def get_legend(self):
        return str(self.options['legend'])
    
    def get_x_smooth(self):
        return int(self.options['x_smooth'])
    
    def get_y_smooth(self):
        return int(self.options['y_smooth'])
    
    def get_dir(self):
        return str(self.options['dir'])
    
    def get_plot(self):
        
        
        return self.options['plot']
    
    def smooth_y(self, ydata =[]):
        try:
            y_smooth = self.get_y_smooth()
            if(y_smooth > 0):
                ydata = savgol_filter(ydata, y_smooth, 1)
        except:
            pass
        return ydata
    
    def median_y(self, ydata =[]):
        try:
            y_median = self.options["y_median"]
            if(y_median>0): 
                if y_median % 2 ==0:
                    y_median +=1           
                ydata_s = medfilt(ydata, y_median)
            else:
                ydata_s = ydata
        except:
            pass
        return ydata_s
    
    def smooth_x(self, xdata):
        try:
            x_smooth = self.get_x_smooth()
            if(x_smooth > 0):
                xdata = savgol_filter(xdata, x_smooth, 1)
        except:
            pass
        return xdata
    
    def fig(name, **kwargs):
        try:
            ax = kwargs['plot']
        except:
            fig = plt.figure()
            #  plt.subtitle(self.name)
            ax = fig.subplots()

    def exe(self):
        
        ax = self.options['plot']
        if ax == NEWPLOT:
            fig = plt.figure()
            plt.suptitle(self.name)
            ax = fig.subplots()
        
        try:
            y_median = int(self.options['y_median'])
            if y_median > 0:
                if y_median % 2 ==0:
                    y_median +=1 
                #print("median filter Y", y_median)
                self.y_data = medfilt(self.y_data, y_median)
            y_smooth = int(self.options['y_smooth'])
            if y_smooth > 0:
                self.y_data = savgol_filter(self.y_data, y_smooth, 1)
        except:
            pass
        try:
            x_smooth = int(self.options['x_smooth'])
            if x_smooth > 0:
                self.x_data = savgol_filter(self.x_data, x_smooth, 1)
        except:
            pass

        try:
            line = ax.plot(self.x_data, self.y_data, self.options['style'])
        except:
            pass
        ax.set_xlabel(f'{self.x_label} / {self.x_unit}')
        ax.set_ylabel(f'{self.y_label} / {self.y_unit}')
        return line, ax
        
            