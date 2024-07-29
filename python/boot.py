from machine import Timer

from clock_state import ClockState
from Display import Oled
import MenuSystem as menu
from push_button import PushButton
from rotary_encoder import RotaryEncoder


encoder = RotaryEncoder(3, 4)
accept_button = PushButton(5)
back_button = PushButton(10)
display = Oled(18, 19, 21, 20, 17)

state = ClockState()
menu_handler = menu.MenuHandler(encoder, accept_button, back_button, state, display)


def update_handler(timer):
    state.update()
    menu_handler.render()

if __name__ == "__main__":
    clock_view = menu.Functionality_ClockDisplay(None, "display", state, display, menu_handler)
    menu_handler.root = clock_view
    menu_handler._current = clock_view

    menu_root = menu.Functionality_MenuSelect(None, "Settings", state, display, menu_handler)
    menu_alarm = menu.Functionality_MenuSelect(None, "Alarm Settings", state, display, menu_handler)
    menu_time = menu.Functionality_MenuSelect(None, "Time Settings", state, display, menu_handler)
    menu_radio = menu.Functionality_MenuSelect(None, "Radio Settings", state, display, menu_handler)

    alarm_time = menu.Functionality_AlarmTime(None, "Alarm Time", state, display, menu_handler)
    change_rgb = menu.Functionality_ChangeRGB(None, "Change RGB", state, display, menu_handler)
    change_time_format = menu.Functionality_ChangeTimeFormat(None, "Change Format", state, display, menu_handler)
    frequency_change = menu.Functionality_FrequencyChange(None, "Change Freq.", state, display, menu_handler)

    toggle_radio = menu.Functionality_Toggle(None, "Enable Radio", state, display, menu_handler)
    toggle_radio.set_toggle_fns(state.enable_radio, state.disable_radio)

    mute_radio = menu.Functionality_Toggle(None, "Mute Radio", state, display, menu_handler)
    mute_radio.set_toggle_fns(state.mute_radio, state.unmute_radio)

    radio_volume = menu.Functionality_Roller(None, "Radio Volume", state, display, menu_handler)
    radio_volume.set_roller_fns(state.set_radio_volume, state.get_radio_volume, 1)

    toggle_alarm = menu.Functionality_Toggle(None, "Enable Alarm", state, display, menu_handler)
    toggle_alarm.set_toggle_fns(state.enable_alarm, state.disable_alarm)

    alarm_volume = menu.Functionality_Roller(None, "Alarm Volume", state, display, menu_handler)
    alarm_volume.set_roller_fns(state.set_alarm_volume, state.get_alarm_volume, 1)

    led_toggle = menu.Functionality_Toggle(None, "Enable LEDs", state, display, menu_handler)
    led_toggle.set_toggle_fns(state.enable_led, state.disable_led)

    alarm_snooze = menu.Functionality_Roller(None, "Snooze Delay", state, display, menu_handler)
    alarm_snooze.set_roller_fns(state.set_snooze_delay, state.get_snooze_delay)

    zone_offset = menu.Functionality_Roller(None, "Time Zone", state, display, menu_handler)
    zone_offset.set_roller_fns(state.set_tz_offset, state.get_tz_offset)

    clock_view.add_child(menu_root)

    menu_root.add_child(menu_alarm)
    menu_alarm.add_child(alarm_time)
    menu_alarm.add_child(toggle_alarm)
    menu_alarm.add_child(alarm_volume)
    menu_alarm.add_child(alarm_snooze)

    menu_root.add_child(menu_time)
    menu_time.add_child(change_time_format)
    menu_time.add_child(zone_offset)

    menu_root.add_child(menu_radio)
    menu_radio.add_child(toggle_radio)
    menu_radio.add_child(frequency_change)
    menu_radio.add_child(radio_volume)
    menu_radio.add_child(mute_radio)

    menu_root.add_child(change_rgb)
    menu_root.add_child(led_toggle)

    menu_handler.render()

    update_timer = Timer(mode=Timer.PERIODIC, freq=1, callback=update_handler)
