from machine import Timer

from clock_state import ClockState
# from Display import Oled
# import MenuSystem
from push_button import PushButton
from rotary_encoder import RotaryEncoder


state = ClockState()


def update_handler(timer):
    state.update()


if __name__ == "__main__":
    encoder = RotaryEncoder(3, 4)
    accept_button = PushButton(5)
    back_button = PushButton(10)
    # display = Oled(18,19,21,20,17)

    # menu_handler = menu.MenuHandler(encoder, accept_button, back_button, state)

    update_timer = Timer(mode=Timer.PERIODIC, freq=1, callback=update_handler)