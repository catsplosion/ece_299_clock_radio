from clock_state import ClockState
from Display import Oled
import MenuSystem
from push_button import PushButton
from rotary_encoder import RotaryEncoder


if __name__ == "__main__": #changed __name to __name__
    encoder = RotaryEncoder(14,15,2)
    accept_button = PushButton(13)
    back_button = PushButton(16)
    display = Oled(18,19,21,20,17)

    state = ClockState()
    menu_handler = menu.MenuHandler(encoder, accept_button, back_button, state)
