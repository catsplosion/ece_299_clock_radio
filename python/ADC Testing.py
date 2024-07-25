import utime

from machine import Pin # REMINDER: DFT NOT DTFT!!!!
from neopixel import NeoPixel
from ulab import numpy as np

#Use controlled:

save_data = True
# skip_DC_component = True

ADC_pin = Pin(28)

sampling_period = 48 #Sampling rate fixed at 0.5MHz (2*10^-6s max) - Recorded in microseconds

num_leds = 16

num_cycles = 128 # Must be a power of 2

# Definitions (Do not modify):

leds = NeoPixel(Pin(0), num_leds)

analog_value = machine.ADC(ADC_pin)

ADC_y = np.empty(num_cycles)

ADC_x = np.linspace(0, 3, num_cycles)

FFT_y = np.empty(num_cycles)

magnitudes = np.empty(num_cycles)

phases = np.empty(num_cycles)

average_magnitude = 0

average_phase = 0

frequency_samples = np.empty(num_cycles)

for p in range (1500):
    for i in range (num_cycles):
        
        digital_value = analog_value.read_u16()     
        print("ADC: ", digital_value)
        
        ADC_y[i] = (digital_value)        
        utime.sleep_us(sampling_period) 

    real, imaginary = np.fft.fft(ADC_y)
      
    frequency_resolution = (1/(sampling_period*(10**-6))/(num_cycles))

    for k in range(num_cycles):
    
        magnitudes[k] = (np.sqrt((real[k]**2) + (imaginary[k]**2)))
    
        phases[k] = (np.arctan2(imaginary[k], real[k]))
    
        frequency_samples[k] = ((k)*frequency_resolution)
    
    #Bin 1: 1* numcycles/numleds
    #bin 16 (max num of leds): numleds * numcycles/numleds



    counter = 0

    led_def = np.array([0,1,1]) #Default led state, when phase = 0

    for n in range (num_leds):
    
        prev_counter = counter
        counter = n * num_cycles/num_leds
    
        for q in range (prev_counter, counter): # Divide the frequencies into sections/a bamd
        
            q = int(q) # for some reason iterating between two numbers makes the iterator a float
        
            average_magnitude += magnitudes[q] # Take the average mangitude and phase of that frequency band (each led represents a frequency band)
            average_phase += phases[q]
            
        c = 1 # scalar 
   
        average_magnitude = average_magnitude/num_cycles
        average_phase = average_phase/num_cycles * c
    
        if(average_magnitude > 255): # Hmm. This is really only a case of when there is a DC component, for the first frequency band.
            average_magnitude = 255

        linear_decrease = -(2/np.pi)*average_phase + 1
        linear_increase = (1/np.pi)*average_phase

        if average_phase >= -(np.pi / 2) and average_phase < 0:
            leds[n] = tuple(map(int, np.ceil((led_def[0], led_def[1], (led_def[2] + linear_decrease) * average_magnitude))))  # Decrease blue
        
        elif average_phase >= -np.pi and average_phase < -(np.pi / 2):
            leds[n] = tuple(map(int, np.ceil(((led_def[0] + linear_increase) * average_magnitude, led_def[1], led_def[2]))))  # Increase red
        
        elif average_phase >= 0 and average_phase < (np.pi / 2):
            leds[n] = tuple(map(int, np.ceil((led_def[0], (led_def[1] + linear_decrease) * average_magnitude, led_def[2]))))  # Decrease green
        
        elif average_phase >= (np.pi / 2) and average_phase < np.pi:
            leds[n] = tuple(map(int, np.ceil(((led_def[0] + linear_increase) * average_magnitude, led_def[1], led_def[2]))))  # Increase red
        
        print(leds[n][0], leds[n][1], leds[n][2])
        leds.write()
        
    
if save_data:
    try:
        f = open("ADC_DATA.txt", "wt")
        
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
        
    except Exception as e:
        raise RuntimeError("Could not write to file,", e)    