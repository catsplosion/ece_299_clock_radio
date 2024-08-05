import time

from machine import Timer

import clock_state
from Display import Oled
from Leds_Handler import LEDS
import MenuSystem as menu
from push_button import PushButton
from rotary_encoder import RotaryEncoder


# Initialize the input/output classes.
encoder = RotaryEncoder(3, 4)
accept_button = PushButton(5)
back_button = PushButton(10)
display = Oled(18, 19, 21, 20, 17)
leds = LEDS(28, 8, 8, state)

# Initialize the state holder for the clock radio.
state = clock_state.ClockState()

# Initialze the menu system
menu_handler = menu.MenuHandler(
    encoder, accept_button, back_button, state, display, leds)


def update_handler(timer):
    # Timer callback to periodically update the state and display.
    state.update()
    menu_handler.render()


def get_radio_volume():
    # Helper function to fix +1 offset of the radio volume.
    return state.get_radio_volume() + 1

if __name__ == "__main__":
    # Build the menu tree.
    # Start with the root of the tree. The main clock display.
    clock_view = menu.Functionality_ClockDisplay(
        None, "display", state, display, leds, menu_handler)

    # Set the clock display as the root of the menu system.
    menu_handler.root = clock_view
    menu_handler._current = clock_view

    # Create the settings menu root.
    menu_root = menu.Functionality_MenuSelect(
        None, "Settings", state, display, leds, menu_handler)

    # Create the category folders on the first level of the settings menu.
    menu_alarm = menu.Functionality_MenuSelect(
        None, "Alarm Settings", state, display, leds, menu_handler)
    menu_time = menu.Functionality_MenuSelect(
        None, "Time Settings", state, display, leds, menu_handler)
    menu_radio = menu.Functionality_MenuSelect(
        None, "Radio Settings", state, display, leds, menu_handler)
    lighting_state = menu.Functionality_MenuSelect(
        None, "Lighting", state, display, leds, menu_handler)

    # Create the LED related menu items.
    FFT = menu.Functionality_Change_Lighting(
        None, "FFT", state, display, leds, menu_handler)
    cosntant = menu.Functionality_Change_Lighting(
        None, "Set Colour", state, display, leds, menu_handler)
    led_mode = menu.Functionality_Change_Lighting(
        None, "OFF", state, display, leds, menu_handler)
    change_rgb = menu.Functionality_ChangeRGB(
        None, "Change RGB", state, display, leds, menu_handler)

    # Create the radio related menu items.
    frequency_change = menu.Functionality_FrequencyChange(
        None, "Change Freq.", state, display, leds, menu_handler)

    toggle_radio = menu.Functionality_Toggle(
        None, "Enable Radio", state, display, leds, menu_handler)
    toggle_radio.set_toggle_fns(state.enable_radio, state.disable_radio)

    mute_radio = menu.Functionality_Toggle(
        None, "Mute Radio", state, display, leds, menu_handler)
    mute_radio.set_toggle_fns(state.mute_radio, state.unmute_radio)

    radio_volume = menu.Functionality_Roller(
        None, "Radio Volume", state, display, leds, menu_handler)
    radio_volume.set_roller_fns(
        state.set_radio_volume, state.get_radio_volume, str_fn=get_radio_volume)

    # Create the alarm related menu items.
    alarm_time = menu.Functionality_AlarmTime(
        None, "Alarm Time", state, display, leds, menu_handler)

    toggle_alarm = menu.Functionality_Toggle(
        None, "Enable Alarm", state, display, leds, menu_handler)
    toggle_alarm.set_toggle_fns(state.enable_alarm, state.disable_alarm)

    alarm_volume = menu.Functionality_Roller(
        None, "Alarm Volume", state, display, leds, menu_handler)
    alarm_volume.set_roller_fns(
        state.set_alarm_volume, state.get_alarm_volume, 1)

    alarm_delay = menu.Functionality_Roller(
        None, "Snooze Delay", state, display, leds, menu_handler)
    alarm_delay.set_roller_fns(
        state.set_snooze_delay, state.get_snooze_delay)

    alarm_pattern = menu.Functionality_AlarmPattern(
        None, "Alarm Pattern", state, display, leds, menu_handler)
    alarm_pattern.set_roller_fns(
        state.set_alarm_pattern, state.get_alarm_pattern)

    # Create the clock related menu items.
    change_time_format = menu.Functionality_ChangeTimeFormat(
        None, "Change Format", state, display, leds, menu_handler)

    zone_offset = menu.Functionality_Roller(
        None, "Time Zone", state, display, leds, menu_handler)
    zone_offset.set_roller_fns(state.set_tz_offset, state.get_tz_offset)

    clock_time = menu.Functionality_ClockTime(
        None, "Clock Time", state, display, leds, menu_handler)
    clock_date = menu.Functionality_ClockDate(
        None, "Clock Date", state, display, leds, menu_handler)

    # Parent all the menu items together into a tree structure.
    # Start with the root of the settings.
    clock_view.add_child(menu_root)

    # Arrange the alarm submenu.
    menu_root.add_child(menu_alarm)
    menu_alarm.add_child(alarm_time)
    menu_alarm.add_child(toggle_alarm)
    menu_alarm.add_child(alarm_volume)
    menu_alarm.add_child(alarm_delay)
    menu_alarm.add_child(alarm_pattern)

    # Arrange the clock submenu.
    menu_root.add_child(menu_time)
    menu_time.add_child(clock_time)
    menu_time.add_child(clock_date)
    menu_time.add_child(change_time_format)
    menu_time.add_child(zone_offset)

    # Arrange the radio submenu.
    menu_root.add_child(menu_radio)
    menu_radio.add_child(toggle_radio)
    menu_radio.add_child(frequency_change)
    menu_radio.add_child(radio_volume)
    menu_radio.add_child(mute_radio)

    # Add in the LED color select.
    menu_root.add_child(change_rgb)

    # Arrange the FFT submenu.
    menu_root.add_child(lighting_state)
    lighting_state.add_child(FFT)
    lighting_state.add_child(cosntant)
    lighting_state.add_child(led_mode)

    # Draw the menu to the display.
    menu_handler.render()

    # Initialize the update timer to once every second.
    update_timer = Timer(mode=Timer.PERIODIC, freq=1, callback=update_handler)

    # Begin the sample and FFT processing loop for the LEDs.
    leds.fft_loop()
