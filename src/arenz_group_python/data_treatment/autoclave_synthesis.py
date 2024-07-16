import numpy as np
#from scipy.signal import savgol_filter
#import matplotlib.pyplot as plt
import pandas as pd
from nptdms import TdmsFile
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt

from .util import plot_options

K_TO_DEGC = 273.15
PA_TO_BAR = 1.0e5

class AutoClaveSynthesis:
    
    def __init__(self, path):
        self.Time = []
        self.Temp_R = []
        self.Temp_HP = []
        self.Temp_set = []
        self.Overpressure = []
        self.Rot = []
        self.path = ""

        try:
            tdms_file = TdmsFile.read(path)
            tdms_file.close()
            self.path = str(path)
            self.Time = (tdms_file['Synthesis']['Time'].data)
            self.Temp_R = (tdms_file['Synthesis']['T_Reactor'].data)
            self.Temp_HP = (tdms_file['Synthesis']['T_HotPlate'].data)
            self.Overpressure = (tdms_file["Synthesis"]["P_Reactor"].data)
            self.Rot = tdms_file['Synthesis']['Rot'].data
            self.name = tdms_file.properties['name']

        except FileNotFoundError:
            print(f"TDMS file was not found: {path}")
        except KeyError as e:
            print(f"TDMS error: {e}")

    def __str__(self):
        return f"{self.name}"

    def get_channel(self, datachannel: str):
        match datachannel:
            case "Time":
                return self.Time, "t", "s"
            case "Time_in_min":
                return self.Time / 60.0, "t", "min"
            case "T_Reactor":
                return self.Temp_R, "T", "K"
            case "T_Reactor_in_C":
                return self.Temp_R - K_TO_DEGC, "T", "°C"
            case "T_HotPlate":
                return self.Temp_HP, "T", "K"
            case "T_HotPlate_in_C":
                return self.Temp_HP - K_TO_DEGC, "T", "°C"
            case "P_Reactor":
                return self.Overpressure, "P", "bar"
            case "P_Reactor":
                return self.Overpressure / PA_TO_BAR , "P", "bar"
            case "Rot":
                return self.Rot, "v", "rpm"
            case _:
                raise NameError("The channel name is not supported")

    def clean_outliers(self, data, window_size, threshold):
        clean_data = data.copy()
        half_window = window_size // 2

        for i in range(len(data)):
            start = max(0, i - half_window)
            end = min(len(data), i + half_window)
            window = data[start:end]

            mean_val = np.mean(window)
            std_val = np.std(window)

            if np.abs(data[i] - mean_val) > threshold * std_val:
                clean_data[i] = mean_val

        return clean_data
    
    def plot(self, x_channel: str, y_channel: str, **kwargs):
        #xlabel = "wrong channel name"
        #xunit = "wrong channel name"
        #ylabel = "wrong channel name"
        #yunit = "wrong channel name"
        
        options=plot_options(kwargs)
        options.name = self.name

        try:
            options.x_data, options.x_label, options.x_unit = self.get_channel(x_channel)
        except NameError:
            print(f"xchannel {x_channel} not supported")
        try:
            options.y_data, options.y_label, options.y_unit = self.get_channel(y_channel)
        except NameError:
            print(f"ychannel {y_channel} not supported")

        return options.exe()

    def AC_synthesis(self, **kwargs):
        options = {
            'time_smooth': 0,
            'pressure_smooth': 0,
            "temp_smooth": 0}
        options.update(kwargs)

        cleaned_temp_R = self.clean_outliers(self.Temp_R, window_size=20, threshold=1)

        window_length = min(51, len(cleaned_temp_R) // 2 * 2 + 1)
        polyorder = min(3, window_length - 1)
        if window_length > 1:
            smoothed_temp_R = savgol_filter(cleaned_temp_R, window_length=window_length, polyorder=polyorder)
        else:
            smoothed_temp_R = cleaned_temp_R

        if len(smoothed_temp_R) == 0 or np.isnan(smoothed_temp_R).all():
            raise ValueError("Smoothed temperature data is empty or contains only NaN values.")

        # Calculate the maximum temperature of the smoothed data
        max_temperature_R = round(float(max(smoothed_temp_R)), 2)
        # Round the maximum temperature to the nearest multiple of 25
        set_temperature = round(max_temperature_R / 25) * 25

        time_set_temp = None
        for i, temp in enumerate(smoothed_temp_R):
            if temp >= set_temperature:
                time_set_temp = self.Time[i]
                break

        if time_set_temp is None:
            time_set_temp = max(self.Time)

        max_overpressure = round(max(self.Overpressure), 2)
        max_time = round(max(self.Time), 2)
        rotation = int(max(self.Rot))

        parameters = {
            "Set Temperature [°C]": set_temperature,
            'Max Temperature of Reactor [°C]': round(max_temperature_R, 2),
            'Time to Set Temperature [min]': round(time_set_temp, 2),
            'Heating Rate [°C/min]': round(((set_temperature - smoothed_temp_R[0]) / time_set_temp), 2),
            'Max Overpressure [bar]': max_overpressure,
            'Time to Max Overpressure [min]': round(self.Time[self.Overpressure.argmax()], 2),
            'Pressure Increase Rate [bar/min]': round((max_overpressure - self.Overpressure[0]) / round(self.Time[self.Overpressure.argmax()], 2), 2),
            "Rotation Rate [rpm]": rotation,
            "Time of Synthesis [min]": max_time
        }

        # Create a DataFrame to format the values correctly
        parameters_df = pd.DataFrame(list(parameters.items()), columns=['Parameter', 'Value'])
        parameters_df['Value'] = parameters_df['Value'].astype(float)


        fig, axs = plt.subplots(1, 2, figsize=(12, 6))
        fig.suptitle(self.name, fontsize = 20)

        temp_smooth = int(options["temp_smooth"])
        if temp_smooth > 0:
            smoothed_temp = savgol_filter(smoothed_temp_R, min(temp_smooth, len(smoothed_temp_R) // 2 * 2 + 1), 1)
        else:
            smoothed_temp = smoothed_temp_R

        pressure_smooth = int(options["pressure_smooth"])
        if pressure_smooth > 0:
            smoothed_pressure = savgol_filter(self.Overpressure, min(pressure_smooth, len(self.Overpressure) // 2 * 2 + 1), 1)
        else:
            smoothed_pressure = self.Overpressure

        time_smooth = int(options["time_smooth"])
        if time_smooth > 0:
            smoothed_time = savgol_filter(self.Time, min(time_smooth, len(self.Time) // 2 * 2 + 1), 1)
        else:
            smoothed_time = self.Time

        ax_temp = axs[0]
        ax_pres = ax_temp.twinx()

        ax_temp.plot(smoothed_time, smoothed_temp, 'g-', label='Temperature [°C]')
        ax_pres.plot(smoothed_time, smoothed_pressure, 'b-', label='Overpressure [bar]')

        ax_temp.set_ylabel('Temperature [°C]', color='g', fontsize = 13)
        ax_pres.set_ylabel('Overpressure [bar]', color='b', fontsize = 13)

        ax_temp.set_ylim(0, max_temperature_R + (max_temperature_R / 10))
        ax_pres.set_ylim(0, max_overpressure + (max_overpressure / 10))

        lines_temp, labels_temp = ax_temp.get_legend_handles_labels()
        lines_pres, labels_pres = ax_pres.get_legend_handles_labels()

        ax_temp.legend(lines_temp + lines_pres, labels_temp + labels_pres, loc='best')

        ax_temp.set_xlabel('Time [min]', fontsize = 13)
        ax_temp.set_xlim(0, max_time + (max_time / 10))

        axs[1].axis('off')

        # Create table with formatted DataFrame
        table = axs[1].table(cellText=parameters_df.values, colLabels=parameters_df.columns, cellLoc='center', loc='center', edges='horizontal')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)

        # Make column names bold
        for (i, j), cell in table.get_celld().items():
            if i == 0:
                cell.set_text_props(weight="bold")

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.show()