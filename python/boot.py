import clock_state
import menu
from push_button import PushButton
from rotary_encoder import RotaryEncoder


if __name == "__main__":
    encoder = RotaryEncoder()
    accept_button = PushButton()
    back_button = PushButton()

    state = ClockState()
    menu_handler = menu.MenuHandler(encoder, accept_button, back_button, state)