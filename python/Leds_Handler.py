import utime

from clock_state import ClockState
from machine import Pin # REMINDER: DFT NOT DTFT!!!!
from machine import ADC
from neopixel import NeoPixel
from ulab import numpy as np


class LEDS():

    def __init__(self, ADC_pin, GPIO_pin, num_leds, state, num_cycles = 128, sampling_period  = 48, save_data = False):
        
        self.ADC_pin = ADC_pin #28
        self.num_leds = num_leds
        self.clock_state = state
        self.save_data = save_data
        self.sampling_period = sampling_period #Sampling rate fixed at 0.5MHz (2*10^-6s max) - Recorded in microseconds (48)
    
        self.num_cycles = num_cycles # Must be a power of 2
        self.__save_data = save_data
        # self.skip_DC_component = True
        self.ADC_pin = Pin(ADC_pin)
        self.GPIO_pin = GPIO_pin # 8

        # Definitions (Do not modify):

        self.npleds = NeoPixel(Pin(self.GPIO_pin), self.num_leds)
        self.analog_value = ADC(self.ADC_pin)
        self.ADC_y = np.empty(self.num_cycles)
        self.ADC_x = np.linspace(0, 3, self.num_cycles)
        self.FFT_y = np.empty(self.num_cycles)
        self.magnitudes = np.empty(self.num_cycles)
        self.phases = np.empty(self.num_cycles)
        self.average_magnitude = 0
        self.average_phase = 0
        self.frequency_samples = np.empty(self.num_cycles)
        
    
    
    def Constant(self, Off=False):
        
        for n in range(self.num_leds):
            
            if not Off:
                self.npleds[n] =  (self.clock_state.led_color[0], self.clock_state.led_color[1], self.clock_state.led_color[2])
               # print("here!")
            else:
                self.npleds[n] =  (0, 0, 0)
            
        self.npleds.write()
            
    def FFT_State(self): #Handles all logic

        while (True): #self.clock_state.led_states["FFT"]
        #for i in range (1000):
            
            if(self.clock_state.radio_muted != False or self.clock_state.radio_enabled != True or self.clock_state.led_states["FFT"] != True): #Due to noise, even if the radio is off, the ADC still reads values
                
                if(self.clock_state.led_states["Set Colour"] and not state_changed):
                    state_changed = True
                    self.Constant(False)
                    
                else:
                    self.Constant(True) # Assume "OFF" State
                    state_changed = False
                
            

            
            else:
                for i in range (self.num_cycles):
                    
                    self.digital_value = self.analog_value.read_u16()     
                   # print("ADC: ", self.digital_value)
                    
                    self.ADC_y[i] = (self.digital_value)        
                    utime.sleep_us(self.sampling_period) 

                self.real, self.imaginary = np.fft.fft(self.ADC_y)
                  
                self.frequency_resolution = (1/(self.sampling_period*(10**-6))/(self.num_cycles))

                for k in range(self.num_cycles):
                
                    self.magnitudes[k] = (np.sqrt((self.real[k]**2) + (self.imaginary[k]**2)))
                
                    self.phases[k] = (np.arctan2(self.imaginary[k], self.real[k]))
                
                    self.frequency_samples[k] = ((k)*self.frequency_resolution)
                
                #Bin 1: 1* numcycles/numleds
                #Bin 16 (max num of leds): numleds * numcycles/numleds

                self.counter = 0

                self.led_def = np.array([0,1,1]) #Default led state, when phase = 0

                for n in range (self.num_leds):
                    
                    start_time = utime.ticks_ms()
                
                    self.prev_counter = self.counter
                    self.counter = n * self.num_cycles/self.num_leds
                
                    for q in range (self.prev_counter, self.counter): # Divide the frequencies into sections/a band
                    
                        self.q = int(q) # for some reason iterating between two numbers makes the iterator a float
                    
                        self.average_magnitude += self.magnitudes[self.q] # Take the average mangitude and phase of that frequency band (each led represents a frequency band)
                        self.average_phase += self.phases[self.q]
                        
                    self.c = 50 # scalar 
               
                    self.num_bins_per_led = self.num_cycles // self.num_leds
                    self.average_magnitude /= (self.num_bins_per_led * 255)
                    self.average_phase /= self.num_bins_per_led * self.c

                    self.linear_decrease = -(2/np.pi)*self.average_phase + 1
                    self.linear_increase = (1/np.pi)*self.average_phase
                    
                    if(self.average_phase > np.pi):
                        self.average_phase = np.pi
                    elif(self.average_phase< -np.pi):
                        self.average_phase = -np.pi #Only here because of scaling

                    if self.average_phase >= -(np.pi / 2) and self.average_phase < 0:
                        self.npleds[n] = tuple(map(int, np.ceil((self.led_def[0], self.led_def[1], (self.led_def[2] + self.linear_decrease) * self.average_magnitude))))  # Decrease blue
                    
                    elif self.average_phase >= -np.pi and self.average_phase < -(np.pi / 2):
                        self.npleds[n] = tuple(map(int, np.ceil(((self.led_def[0] + self.linear_increase) * self.average_magnitude, self.led_def[1], self.led_def[2]))))  # Increase red
                    
                    elif self.average_phase >= 0 and self.average_phase < (np.pi / 2):
                        self.npleds[n] = tuple(map(int, np.ceil((self.led_def[0], (self.led_def[1] + self.linear_decrease) * self.average_magnitude, self.led_def[2]))))  # Decrease green
                    
                    elif self.average_phase >= (np.pi / 2) and self.average_phase < np.pi:
                        self.npleds[n] = tuple(map(int, np.ceil(((self.led_def[0] + self.linear_increase) * self.average_magnitude, self.led_def[1], self.led_def[2]))))  # Increase red
                    
                    #print(self.npleds[n][0], self.npleds[n][1], self.npleds[n][2])
                    self.npleds.write()
                
                elapsed_time = utime.ticks_diff(utime.ticks_ms(), start_time)
                if elapsed_time > 100:
                    utime.sleep_ms(1)  # Yield control to allow interrupts
                    
            
        if self.__save_data:
            try:
                self.f = open("ADC_DATA.txt", "wt")
                
                self.f.write("Original ADC values:\n")
                self.f.write(', '.join(map(str, self.ADC_y)) + '\n')
            
                self.f.write("X values:\n")
                self.f.write(', '.join(map(str, self.ADC_x)) + '\n')
            
                self.f.write("FFT Magnitudes:\n")
                self.f.write(', '.join(map(str, self.magnitudes)) + '\n')
                        
                self.f.write("FFT Phases:\n")
                self.f.write(', '.join(map(str, self.phases)) + '\n')
            
                self.f.write("Frequencies:\n")
                self.f.write(', '.join(map(str, self.frequency_samples)) + '\n')

                self.f.close()
                
            except Exception as e:
                self.f.close() # Just in case...
                raise RuntimeError("Could not write to file,", e)
    
