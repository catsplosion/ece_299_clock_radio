from machine import I2C
from machine import Pin
from machine import Timer
from neopixel import NeoPixel

from rda5807 import Radio
from rda5807 import RDA5807M_FLG_DHIZ, RDA5807M_REG_CONFIG

from push_button import PushButton
from rotary_encoder import RotaryEncoder


T_NONE = 0
T_RADIO = 1
T_BUTTON = 2
T_LEDS = 3


LED_PATTERN = [(255,0,0), (0,255,0), (0,0,255), (255,255,255), (0,0,0)]


class Testing():
    def __init__(self):
        self.test = T_NONE
        self.step = 0
        self.counter = 0

        self.radio = None
        self.button = None
        self.leds = None

        self.led_timer = Timer()
        self.led_index = 0
        self.lef_fade = 1

    def next(self):
        if self.test == T_NONE:
            raise RuntimeError("A test module must be initialized first!")
        elif self.test == T_RADIO:
            self._next_radio_output()
        elif self.test == T_BUTTON:
            self._next_push_button()
        elif self.test == T_LEDS:
            self._next_leds()

    def start_radio_output(self):
        self.radio = Radio(I2C(1, scl=7, sda=6, freq=100000))
        self.radio.bass_boost(False)
        self.radio.mono(True)
        self.radio.set_frequency_MHz(100.3)
        self.radio.set_volume(8)
        self.radio.mute(False)
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
            self.radio.update_reg(RDA5807M_REG_CONFIG, RDA5807M_FLG_DHIZ, 0)
            self.radio.mute(True)
            self.radio.set_volume(0)

            self.test = T_NONE
            self.radio = None

            print("4) The radio test has concluded.")

        self.step += 1

    def set_frequency(self, freq):
        if not self.radio:
            raise RuntimeError("Radio test must be initiazlied first!")

        self.radio.set_frequency_MHz(freq)

    def start_push_button(self):
        self.button = PushButton(10)
        self.button.set_press_fn(self._button_handler)

        self.test = T_BUTTON
        self.step = 0

        print("1) Please press the push button once normally.")

    def _next_push_button(self):
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
        if self.step == 0 or self.step == 1:
            print("{}) Button input successful!".format(self.step+1))
        elif self.step == 2:
            self.counter += 1
            if self.counter == 5:
                print("3) 5 inputs detected.")
            elif self.counter == 6:
                print("3) All 6 inputs detected successfully!")

    def button_parameters(self, delay_period=4, delay_threshold=4):
        if not self.button:
            raise RuntimeError("Push button test must be initiazlied first!")

        self.button.delay_period = delay_period
        self.button.delay_threshold = delay_threshold

    def start_leds(self):
        self.leds = NeoPixel(Pin(8), 8)
        self.led_index = 0
        self.led_fade = 1
        self._led_handler_1(None)
        self.led_timer = Timer(
            mode=Timer.PERIODIC, period=5000, callback=self._led_handler_1)

        self.test = T_LEDS
        self.step = 0

        print(
            "1) All 8 LEDs should emit the same color at the same intensity. "
            "Every 5 seconds the LEDs should cycle between RED, GREEN, BLUE, "
            "WHITE, and OFF."
        )

    def _next_leds(self):
        if self.step == 0:
            self.led_timer.deinit()
            self.led_timer.init(
                mode=Timer.PERIODIC, period=5000, callback=self._led_handler_2)
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
                mode=Timer.PERIODIC, period=40, callback=self._led_handler_3)

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

    def _led_handler_1(self, timer):
        for n in range(8):
            self.leds[n] = LED_PATTERN[self.led_index % len(LED_PATTERN)]

        self.leds.write()

        self.led_index += 1

    def _led_handler_2(self, timer):
        for n in range(8):
            index = (self.led_index + n) % len(LED_PATTERN)
            self.leds[n] = LED_PATTERN[index]

        self.leds.write()

        self.led_index += 1

    def _led_handler_3(self, timer):
        for n in range(8):
            self.leds[n] = [self.led_fade % 256]*3

        self.leds.write()

        self.led_fade += 1 if self.led_fade > 0 else -1

        if self.led_fade > 255:
            self.led_fade = -1
        elif self.led_fade <= -256:
            self.led_fade = 1


test = Testing()


if __name__ == "__main__":
    print("Clock radio testing suite. Please enter in a command:")
    print("test.start_radio_ouput()")
    print("test.start_push_button()")
    print("test.start_leds()")