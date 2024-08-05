import utime

from clock_state import ClockState
from machine import Pin
from machine import ADC
from neopixel import NeoPixel
from ulab import numpy as np


# LED mode values.
LEDS_OFF = 0
LEDS_FFT = 1
LEDS_CONT = 2


class LEDS():
    """
    Handles both the LED lighting funcionality and the audio sampling and
    analysis routines.

    ADC_pin(int): GPIO pin to use for the audio input ADC.
    GPIO_pin(int): GPIO pin to use to send data to the LED module.
    num_leds(int): Number of LEDs to update.
    state(ClockState): Clock state holder instance.
    num_cycles(int): Number of samples to read before analysis.
    sampling_period(int): Time in us to wait between sampling.
    """
    def __init__(self, ADC_pin, GPIO_pin, num_leds, state, num_cycles=128,
        sampling_period=48):

        self.ADC_pin = ADC_pin
        self.num_leds = num_leds
        self.clock_state = state
        self.sampling_period = sampling_period

        # Cycles must be a power of 2.
        self.num_cycles = num_cycles
        self.ADC_pin = Pin(ADC_pin)
        self.GPIO_pin = GPIO_pin

        self.leds_enabled = False

        self.npleds = NeoPixel(Pin(self.GPIO_pin), self.num_leds)
        for n in range(self.num_leds):
            self.npleds[n] = (0, 0, 0)
            self.npleds.write()

        Pin(self.GPIO_pin, Pin.IN)

        # Hold these here so the large arrays are only created once.
        self.analog_value = ADC(self.ADC_pin)
        self.ADC_y = np.empty(self.num_cycles)
        self.ADC_x = np.linspace(0, 3, self.num_cycles)
        self.FFT_y = np.empty(self.num_cycles)
        self.magnitudes = np.empty(self.num_cycles)
        self.phases = np.empty(self.num_cycles)
        self.average_magnitude = 0
        self.average_phase = 0
        self.frequency_samples = np.empty(self.num_cycles)

        self.leds_mode = LEDS_OFF

    def turn_on(self):
        """
        Turn on and enable the LED driver only if it is disabled.
        """
        if not self.leds_enabled:
            self.npleds = NeoPixel(Pin(self.GPIO_pin), self.num_leds)
            self.leds_enabled = True

    def turn_off(self):
        """
        Turn off and disable the LED driver only if it is enabled. Importantly
        this sets the PWM pin back to high impedance mode.
        """
        if self.leds_enabled:
            for n in range(self.num_leds):
                self.npleds[n] = (0, 0, 0)
            self.npleds.write()
            Pin(self.GPIO_pin, Pin.IN)
            self.leds_enabled = False

    def set_mode(self, mode):
        """
        Set the LED mode.
        """
        self.leds_mode = mode

    def fft_loop(self):
        """
        Runs the main sampling and analysis loop forever once called.
        """
        while(True):
            # Logic to appropriately turn off the LEDs when the alarm is
            # sounding since the LED PWM scrambles the audio PWM.
            if self.clock_state.alarm_sounding():
                self.turn_off()

            # Handle the LED constant color mode.
            elif(self.leds_mode == LEDS_CONT):
                self.turn_on()
                for n in range(self.num_leds):
                    self.npleds[n] =  self.clock_state.led_color

                self.npleds.write()

            # Handle the LED FFT mode.
            elif(self.leds_mode == LEDS_FFT):
                # Shut off the LEDs when the audio is muted.
                if self.clock_state.radio_muted:
                    self.turn_off()
                    continue

                self.turn_on()

                # Collected num_cycles amount of samples from the ADC pin.
                for i in range (self.num_cycles):
                    self.digital_value = self.analog_value.read_u16()
                    self.ADC_y[i] = (self.digital_value)
                    utime.sleep_us(self.sampling_period)

                # Perform a FFT on the samples.
                self.real, self.imaginary = np.fft.fft(self.ADC_y)

                self.frequency_resolution = (
                    1/(self.sampling_period*(10**-6))/(self.num_cycles))

                # Convert the FFT results into magnitude and phase components.
                for k in range(self.num_cycles):
                    self.magnitudes[k] = (
                        np.sqrt((self.real[k]**2) + (self.imaginary[k]**2)))
                    self.phases[k] = (
                        np.arctan2(self.imaginary[k], self.real[k]))
                    self.frequency_samples[k] = ((k)*self.frequency_resolution)

                # Default led state when phase = 0.
                self.led_def = np.array([0,1,1])

                # Calculate the new color for each LED.
                self.counter = 0
                for n in range (self.num_leds):
                    start_time = utime.ticks_ms()

                    # Divide the frequencies into sections/a bands.
                    self.prev_counter = self.counter
                    self.counter = n * self.num_cycles/self.num_leds

                    # Find the total mangitude and phase over the band.
                    for q in range (self.prev_counter, self.counter):
                        self.q = int(q)
                        self.average_magnitude += self.magnitudes[self.q]
                        self.average_phase += self.phases[self.q]

                    # Phase scaling value.
                    self.c = 50

                    # Calcuate the average magnitude and phase over the band.
                    self.num_bins_per_led = self.num_cycles // self.num_leds
                    self.average_magnitude /= (self.num_bins_per_led * 255)
                    self.average_phase /= self.num_bins_per_led * self.c

                    self.linear_decrease = -(2/np.pi)*self.average_phase + 1
                    self.linear_increase = (1/np.pi)*self.average_phase

                    # Bound the average phase.
                    if(self.average_phase > np.pi):
                        self.average_phase = np.pi
                    elif(self.average_phase< -np.pi):
                        self.average_phase = -np.pi

                    if self.average_phase >= -(np.pi / 2) and \
                            self.average_phase < 0:
                        # Decrease blue
                        self.npleds[n] = tuple(map(
                            int,
                            np.ceil((
                                self.led_def[0],
                                self.led_def[1],
                                (self.led_def[2] + self.linear_decrease) \
                                    * self.average_magnitude
                            ))
                        ))

                    elif self.average_phase >= -np.pi and \
                            self.average_phase < -(np.pi / 2):
                        # Increase red
                        self.npleds[n] = tuple(map(
                            int,
                            np.ceil((
                                (self.led_def[0] + self.linear_increase) \
                                    * self.average_magnitude,
                                self.led_def[1],
                                self.led_def[2]
                            ))
                        ))

                    elif self.average_phase >= 0 and \
                            self.average_phase < (np.pi / 2):
                        # Decrease green
                        self.npleds[n] = tuple(map(
                            int,
                            np.ceil((
                                self.led_def[0],
                                (self.led_def[1] + self.linear_decrease) \
                                    * self.average_magnitude,
                                self.led_def[2]
                            ))
                        ))

                    elif self.average_phase >= (np.pi / 2) \
                            and self.average_phase < np.pi:
                        # Increase red
                        self.npleds[n] = tuple(map(
                            int,
                            np.ceil((
                                (self.led_def[0] + self.linear_increase) \
                                    * self.average_magnitude,
                                self.led_def[1],
                                self.led_def[2]
                            ))
                        ))

                    self.npleds.write()

                    elapsed_time = utime.ticks_diff(
                        utime.ticks_ms(), start_time)
                    if elapsed_time > 100:
                        # Yield control to avoid locking out all interrupts.
                        utime.sleep_ms(1)
            else:
                self.turn_off()
