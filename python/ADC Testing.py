import machine # REMINDER: DFT NOT DTFT!!!!
import utime
import neopixel
from ulab import numpy as np

save_data = True
ADC_pin = machine.Pin(28) 

sampling_period = 4 #Sampling rate fixed at 0.5MHz (2*10^-6s max) - Recorded in microseconds
num_leds = 16

num_cycles = num_leds # Must be a power of 2
y_data_lim = num_cycles #The pico can sometimes be absoloutely molasses at writing

y_index = 0
 
analog_value = machine.ADC(ADC_pin)


ADC_y = []
ADC_x = np.linspace(0, 3, num_cycles)

FFT_y = []
magnitudes = []
phases = []
frequency_samples = []

for p in range (1):
    for i in range (num_cycles):
        digital_value = analog_value.read_u16()     
        print("ADC: ", digital_value)

        if(y_index < y_data_lim): #Overwrite data if samples overflow y_data_lim (only for testing purposes)
            ADC_y.append(digital_value)
            y_index += 1
        else:
            ADC_y = []
            ADC_y.append(digital_value)
            y_index = 1
        
        utime.sleep_us(sampling_period) 

ADC_y = np.array(ADC_y)

real, imaginary = np.fft.fft(ADC_y)
      
frequency_resolution = (1/(sampling_period*(10**-6))/(num_cycles))

for k in range(len(ADC_y)):
    magnitudes.append(np.sqrt((real[k]**2) + (imaginary[k]**2)))
    phases.append(np.arctan2(imaginary[k], real[k]))
    
    frequency_samples.append((k)*frequency_resolution)
    
    if save_data:
        try:
            f = open("ADC_DATA.txt", "wt")
        except:
            raise RuntimeError("Could not write to file")
    
        f.write("Original ADC values:\n")
        f.write(', '.join(map(str, ADC_y)) + '\n')
    
        f.write("X values:\n")
        f.write(', '.join(map(str, ADC_x)) + '\n')
    
        f.write("FFT Magnitudes:\n")
        f.write(', '.join(map(str, magnitudes)) + '\n')
                
        f.write("FFT Phases:\n")
        f.write(', '.join(map(str, phases)) + '\n')
    
        f.write("Frequencies:\n")
        f.write(', '.join(map(str, frequency_samples)) + '\n')

        f.close()