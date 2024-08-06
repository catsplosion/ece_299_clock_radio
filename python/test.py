from machine import I2C
from machine import Pin
from machine import Timer
from neopixel import NeoPixel

from rda5807 import Radio
from rda5807 import RDA5807M_FLG_DHIZ, RDA5807M_REG_CONFIG

from push_button import PushButton
from rotary_encoder import RotaryEncoder


# Test state values. Current testing program.
T_NONE = 0
T_RADIO = 1
T_BUTTON = 2
T_LEDS = 3

# LED color shift pattern.
LED_PATTERN = [(255,0,0), (0,255,0), (0,0,255), (255,255,255), (0,0,0)]


class Testing():
    """
    Holds all the test functionality.
    """
    def __init__(self):
        # General attributes.
        self.test = T_NONE
        self.step = 0

        # Radio test attributes.
        self.radio = None

        # Button test attributes.
        self.button = None
        self.counter = 0

        # LED test attributes.
        self.leds = None
        self.led_timer = Timer()
        self.led_index = 0
        self.led_fade = 1

    def next(self):
        """
        Called to avance to the next stage in the current test program.
        """
        if self.test == T_NONE:
            raise RuntimeError("A test module must be initialized first!")
        elif self.test == T_RADIO:
            self._next_radio_output()
        elif self.test == T_BUTTON:
            self._next_push_button()
        elif self.test == T_LEDS:
            self._next_leds()

    def start_radio_output(self):
        """
        Begin the radio output test. Initializes and requirements.
        """
        self.radio = Radio(I2C(1, scl=7, sda=6, freq=100000))
        self.radio.bass_boost(False)
        self.radio.mono(True)
        self.radio.set_frequency_MHz(100.3)
        self.radio.set_volume(8)
        self.radio.mute(False)
        # Set the radio module output to regular mode.
        self.radio.update_reg(
            RDA5807M_REG_CONFIG, RDA5807M_FLG_DHIZ, RDA5807M_FLG_DHIZ)

        self.test = T_RADIO
        self.step = 0

        print(
            "1) Radio broadcast or white noise should now be audible. Use the "
            "command test.set_frequency(freq) to tune the radio module to a "
            "strong FM radio station."
        )

    def _next_radio_output(self):
        """
        Advance the radio test to the next stage.
        """
        if self.step == 0:
            self.radio.set_volume(4)

            print(
                "2) The radio volume should now be about half its previous "
                "amplitude."
            )

        elif self.step == 1:
            self.radio.mute(True)

            print("3) The radio should now be completely muted.")

        elif self.step == 2:
            # Set the radio module output to high impedance mode.
            self.radio.update_reg(RDA5807M_REG_CONFIG, RDA5807M_FLG_DHIZ, 0)
            self.radio.mute(True)
            self.radio.set_volume(0)

            self.test = T_NONE
            self.radio = None

            print("4) The radio test has concluded.")

        self.step += 1

    def set_frequency(self, freq):
        """
        Set the radio module frequency.
        freq(float): Channel center frequency in MHz.
        """
        if not self.radio:
            raise RuntimeError("Radio test must be initiazlied first!")

        self.radio.set_frequency_MHz(freq)

    def start_push_button(self):
        """
        Begin the push button test.
        """
        self.button = PushButton(10)
        self.button.set_press_fn(self._button_handler)

        self.test = T_BUTTON
        self.step = 0

        print("1) Please press the push button once normally.")

    def _next_push_button(self):
        """
        Adance the push button test to the next stage.
        """
        if self.step == 0:
            print(
                "2) Please press and hold the button for 2 seconds, and then "
                "release the button."
            )

        elif self.step == 1:
            self.counter = 0
            print(
                "3) Please press the button 5 times quickly."
            )

        elif self.step == 2:
            self.button._disable_irq()
            self.button = None
            self.test = T_NONE

            print("4) The button test has concluded.")

        self.step += 1

    def _button_handler(self):
        """
        Handles the push button press event.
        """
        if self.step == 0 or self.step == 1:
            print("{}) Button input successful!".format(self.step+1))
        elif self.step == 2:
            self.counter += 1
            if self.counter == 5:
                print("3) 5 inputs detected.")
            elif self.counter == 6:
                print("3) All 6 inputs detected successfully!")

    def button_parameters(self, delay_period=4, delay_threshold=4):
        """
        Changes the push button parameters that control the consistency check.
        delay_period(int): The time between checks of the pin value. In ms.
        delay_threshold(int): The number of consistency checks requried before
            the edge event is considered valid.
        """
        if not self.button:
            raise RuntimeError("Push button test must be initiazlied first!")

        self.button.delay_period = delay_period
        self.button.delay_threshold = delay_threshold

    def start_leds(self):
        """
        Begin the LEDs test.
        """
        self.leds = NeoPixel(Pin(8), 8)
        self.led_index = 0
        self.led_fade = 1
        self._led_handler_0(None)
        self.led_timer = Timer(
            mode=Timer.PERIODIC, period=5000, callback=self._led_handler_0)

        self.test = T_LEDS
        self.step = 0

        print(
            "1) All 8 LEDs should emit the same color at the same intensity. "
            "Every 5 seconds the LEDs should cycle between RED, GREEN, BLUE, "
            "WHITE, and OFF."
        )

    def _next_leds(self):
        """
        Advance the LEDs test to the next stage.
        """
        if self.step == 0:
            self.led_timer.deinit()
            self.led_timer.init(
                mode=Timer.PERIODIC, period=5000, callback=self._led_handler_1)
            self.led_index = 0

            print(
                "2) The LEDs now should be displaying a pattern of different "
                "colors, cycling through the same RED, GREEN, BLUE, WHITE, "
                "and OFF sequence. Every 5 seconds, the pattern should shift "
                "one LED over."
            )

        elif self.step == 1:
            self.led_timer.deinit()
            self.led_timer.init(
                mode=Timer.PERIODIC, period=40, callback=self._led_handler_2)

            print(
                "3) The LEDs now should fading in and out as the color WHITE."
            )

        elif self.step == 2:
            self.led_timer.deinit()
            for n in range(8):
                self.leds[n] = (0, 0, 0)
            self.leds.write()

            self.leds = None

            print("4) The LED test has now concluded.")

        self.step += 1

    def _led_handler_0(self, timer):
        """
        Handle the LEDs test stage 0 light patten.
        """
        for n in range(8):
            self.leds[n] = LED_PATTERN[self.led_index % len(LED_PATTERN)]

        self.leds.write()

        self.led_index += 1

    def _led_handler_1(self, timer):
        """
        Handle the LEDs test stage 1 light patten.
        """
        for n in range(8):
            index = (self.led_index + n) % len(LED_PATTERN)
            self.leds[n] = LED_PATTERN[index]

        self.leds.write()

        self.led_index += 1

    def _led_handler_2(self, timer):
        """
        Handle the LEDs test stage 2 light patten.
        """
        for n in range(8):
            self.leds[n] = [self.led_fade % 256]*3

        self.leds.write()

        self.led_fade += 1 if self.led_fade > 0 else -1

        if self.led_fade > 255:
            self.led_fade = -1
        elif self.led_fade <= -256:
            self.led_fade = 1


# Initialize the class so the user can enter in test commands.
test = Testing()


if __name__ == "__main__":
    print("Clock radio testing suite. Please enter in a command:")
    print("test.start_radio_ouput()")
    print("test.start_push_button()")
    print("test.start_leds()")