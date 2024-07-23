from clock_state import ClockState
from Display import Oled
import MenuSystem as menu
from push_button import PushButton
from rotary_encoder import RotaryEncoder


if __name__ == "__main__": #changed __name to __name__
    encoder = RotaryEncoder(14,15,2)
    accept_button = PushButton(0)
    back_button = PushButton(16)
    display = Oled(18,19,21,20,17)

    state = ClockState()
    menu_handler = menu.MenuHandler(encoder, accept_button, back_button, state, display)
    
    alarm_time = menu.Functionality_AlarmTime(None, "Set Alarm", state, display, menu_handler)
    change_rgb = menu.Functionality_ChangeRGB(None, "Change RGB", state, display, menu_handler)
    change_time_format = menu.Functionality_ChangeTimeFormat(None, "Change Format", state, display, menu_handler)
    frequency_change = menu.Functionality_FrequencyChange(None, "Change Freq.", state, display, menu_handler)
    
    menu_handler.root.add_child(alarm_time)
    menu_handler.root.add_child(change_rgb)
    menu_handler.root.add_child(change_time_format)
    menu_handler.root.add_child(frequency_change)
    
    menu_handler.render()
