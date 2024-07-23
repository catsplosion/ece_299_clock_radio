from machine import Timer

from clock_state import ClockState
from Display import Oled
import MenuSystem as menu
from push_button import PushButton
from rotary_encoder import RotaryEncoder


state = ClockState()


def update_handler(timer):
    state.update()

if __name__ == "__main__":
    encoder = RotaryEncoder(3, 4)
    accept_button = PushButton(5)
    back_button = PushButton(10)
    display = Oled(18, 19, 21, 20, 17)

    menu_handler = menu.MenuHandler(encoder, accept_button, back_button, state, display)

    alarm_time = menu.Functionality_AlarmTime(None, "Set Alarm", state, display, menu_handler)
    change_rgb = menu.Functionality_ChangeRGB(None, "Change RGB", state, display, menu_handler)
    change_time_format = menu.Functionality_ChangeTimeFormat(None, "Change Format", state, display, menu_handler)
    frequency_change = menu.Functionality_FrequencyChange(None, "Change Freq.", state, display, menu_handler)

    toggle_radio = menu.Functionality_Toggle(None, "Enable Radio", state, display, menu_handler)
    toggle_radio.set_toggle_fns(state.enable_radio, state.disable_radio)

    mute_radio = menu.Functionality_Toggle(None, "Mute Radio", state, display, menu_handler)
    mute_radio.set_toggle_fns(state.mute_radio, state.unmute_radio)

    toggle_alarm = menu.Functionality_Toggle(None, "Enable Alarm", state, display, menu_handler)
    toggle_alarm.set_toggle_fns(state.enable_alarm, state.disable_alarm)

    menu_handler.root.add_child(alarm_time)
    menu_handler.root.add_child(change_rgb)
    menu_handler.root.add_child(change_time_format)
    menu_handler.root.add_child(frequency_change)
    menu_handler.root.add_child(toggle_radio)
    menu_handler.root.add_child(mute_radio)
    menu_handler.root.add_child(toggle_alarm)

    menu_handler.render()

    update_timer = Timer(mode=Timer.PERIODIC, freq=1, callback=update_handler)
