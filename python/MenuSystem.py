from machine import Timer

import clock_state
import Leds_Handler

# Time to wait in ms before reverting to the clock view display.
_RESET_DELAY = 10000

# Debug mode enabler.
_DEBUG = False

def print_debug(*args, **kwds):
    """
    Wrapper for the print function to disable printing when debug mode is off.
    """
    if _DEBUG:
        print(*args, **kwds)


class MenuHandler:
    """
    Main controller of the menu system for the clock radio.

    encoder(RotaryEncoder): Encoder used to navigate the menu and adjust values.
    accept_button(PushButton): Button for the user's signal-accept input.
    back_button(PushButton): Button for the user's signal-cancel input.
    state(ClockState): Clock state holder instance.
    display(Oled): Display instance used to draw to the display.
    leds(LEDS): Instance of the class used to handle the LED funcionality.
    """
    def __init__(self, encoder, accept_button, back_button, state, display,
            leds):
        # Initalize the attributes.
        self.state = state
        self.display = display
        self.root = None
        self._current = self.root
        self.pause_reset_timer = False
        self.alarm_screen = False

        # Link the input handler functions to the encoder and buttons.
        encoder.set_ccw_fn(self._ccw_handler)
        encoder.set_cw_fn(self._cw_handler)
        accept_button.set_press_fn(self._acceptpressed)
        back_button.set_press_fn(self._backpressed)

        # Initiazlie the display reset timer.
        self._reset_timer = Timer()

    def _start_reset_timer(self):
        """
        Begin the coundown to revert the current menu item back to the root
        menu item. If this is called again within the RESET_DELAY, the timer
        will just start over again without reverting the current menu item.
        """
        self._reset_timer.init(
            mode=Timer.ONE_SHOT,
            period=_RESET_DELAY,
            callback=self._reset_timer_handler
        )

    def _reset_timer_handler(self, timer):
        """
        Callback function to reset the current menu item back to the root menu
        item.
        """
        if self.pause_reset_timer:
            return

        self._current = self.root
        self.render()

    def render(self):
        """
        Populate the display with visuals. Resets the screen, draws its own
        data, and then calls the render method of the current menu item.
        """
        if not self._current:
            return

        # Only draw the alarm message and only draw it once to avoid SPI
        # communication noise.
        alarming = self.state.alarm_state in (
            clock_state._ALARM_SOUND, clock_state._ALARM_TEST)
        if alarming:
            if not self.alarm_screen:
                self.display.oled.fill(0)
                self.display.oled.text("!! ALARM !!", 20, 28)
                self.display.oled.show()
                self.alarm_screen = True
            return

        # Clear the display buffer.
        self.display.oled.fill(0)

        # Display the menu header if we are not at the root item.
        if self._current != self.root:
            self.display.oled.rect(0, 0, 128, 20, 1)
            self.display.oled.text(self._current.name, 4, 6, 2)
            print_debug(self._current.name + " ", end="")

        # Call the render method the current menu item.
        self._current.render()

        # Present the display data.
        self.display.oled.show()
        print_debug("")

        self.alarm_screen = False

    def _ccw_handler(self):
        """
        Callback function to handle rotating the encoder counter clockwise.
        """
        if not self._current:
            return

        # Restart the reset timer.
        self._start_reset_timer()

        # Dismiss the alarm if it is currently sounding.
        if self.state.alarm_enabled and self.state.alarm_sounding():
            self.state.shutoff_alarm()
            return

        # Call the ccw handler method of the current menu item.
        self._current.ccw()

        self.render()

    def _cw_handler(self):
        """
        Callback function to handle rotating the encoder clockwise.
        """
        if not self._current:
            return

        # Restart the reset timer.
        self._start_reset_timer()

        # Dismiss the alarm if it is currently sounding.
        if self.state.alarm_enabled and self.state.alarm_sounding():
            self.state.shutoff_alarm()
            return

        # Call the cw handler method of the current menu item.
        self._current.cw()

        self.render()

    def _acceptpressed(self):
        """
        Callback function to handle the user signal-accept.
        """
        if not self._current:
            return

        # Restart the reset timer.
        self._start_reset_timer()

        # Snooze the alarm if it is currently sounding.
        if self.state.alarm_enabled and self.state.alarm_sounding():
            self.state.snooze_alarm()
            return

        # Call the press handler method of the current menu item.
        self._current.press()

        self.render()

    def _backpressed(self):
        """
        Callback function to handle the user signal-cancel.
        """
        if not self._current:
            return

        # Snooze the alarm if it is currently sounding.
        if self.state.alarm_enabled and self.state.alarm_sounding():
            self.state.snooze_alarm()
            return

        # Call the back handler method of the current menu item.
        self._current.back()

        self.render()


class MenuItem:
    """
    Base class for the menu items of the menu tree. Should never be
    instantiated on its own only just inherited by sub-classes.

    parent(MenuItem): The parent menu item to this item.
    name(str): Name of this item. Displayed in the menu list and menu header.
    state(ClockState): State holder for the clock radio.
    display(Oled): Display instance used to draw to the display.
    leds(LEDS): Instance of the class used to handle the LED funcionality.
    handler(MenuHandler): Pointer back to the main menu handler.
    """
    def __init__(self, parent, name, state, display, leds, handler=None):
        # Save attributes.
        self.parent = parent
        self.name = name
        self.handler = handler
        self.state = state
        self.display = display
        self.leds = leds

        if handler is None:
            self.handler = parent.handler

        # The child menu nodes to this menu item.
        self.children = []

    def add_child(self, node):
        """
        Add a menu item as a child to this menu item.
        node(MenuItem): Menu item to add.
        """
        self.children.append(node)
        node.parent = self
        return node

    def enter(self):
        """
        Base function. Called when the user navigates to this item.
        """
        pass

    def cw(self):
        """
        Base function. Called when the user rotates the encoder clockwise.
        """
        pass

    def ccw(self):
        """
        Base function. Called whenthe user rotates the encoder counter
        clockwise.
        """
        pass

    def press(self):
        """
        Base function. Called when the user inputs a signal-accept.
        """
        pass

    def back(self):
        """
        Base function. Called when the user inputs a signal-cancel.
        """
        if self.parent:
            self.handler._current = self.parent

    def render(self):
        """
        Base function. Draws visuals to the display specific to the menu item.
        """
        pass


class Functionality_ChangeRGB(MenuItem):
    """
    Menu funcionality to set the RGB values of the LEDs.

    See MenuItem for the signature.
    """
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

        self.index = 0

    def ccw(self):
        """
        Decrease the value of the currently selected RGB channel.
        """
        color = list(self.state.led_color)
        color[self.index] -= 5

        self.state.set_led_color(color)

    def cw(self):
        """
        Increase the value of the currently selected RGB channel.
        """
        color = list(self.state.led_color)
        color[self.index] += 5

        self.state.set_led_color(color)

    def press(self):
        """
        Step between the channel to modify: R -> G -> B -> R...
        """
        if(self.index == 2):
            self.index = 0
        else:
            self.index += 1

    def render(self):
        """
        Draw the UI to the display.
        """
        self.display.oled.text("RGB:", 0, 36)

        for i, channel in enumerate(("r", "g", "b")):
            if self.index == i:
                self.display.oled.rect(43*i, 45, 32, 10, 1, True)

            value = self.state.led_color[i]
            self.display.oled.text(
                "{}={}".format(channel, value), 43*i, 46, self.index != i)

        message = "RGB: r={} g={} b={}".format(*self.state.led_color)
        print_debug(message, end="")


class Functionality_ChangeTimeFormat(MenuItem):
    """
    Change the current time format. Rotation of the encoder cw will set the
    mode to 24hr whereas ccw will set the mode to 12hr.

    See MenuItem for the signature
    """
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

    def ccw(self):
        self.state.set_clock_mode("12hr")

    def cw(self):
        self.state.set_clock_mode("24hr")

    def render(self):
        """
        Draw the UI to the display.
        """
        mstring = self.state.get_clock_mode_string()
        self.display.oled.text("Time format:", 0, 36)
        self.display.oled.text(mstring, 30, 46)

        message = "Time format: {}".format(mstring)
        print_debug(message, end="")


class Functionality_FrequencyChange(MenuItem):
    """
    Change the current radio frequency value. Pressing the encoder toggle
    between coarse 1 MHz resolution, fine 0.2 MHz resolution, and seek up/down
    mode.

    See MenuItem for the signature.
    """
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

        self.selections = [1, 0.2, "seek"]
        self.index = 0

    def ccw(self):
        """
        Perform the approriate coarse, fine, seek down function.
        """
        if self.index == 2:
            self.state.seek_down()
        else:
            freq = self.state.radio_freq
            freq -= self.selections[self.index]

            self.state.set_radio(freq=freq)

    def cw(self):
        """
        Perform the approriate coarse, fine, seek up function.
        """
        if self.index == 2:
            self.state.seek_up()
        else:
            freq = self.state.radio_freq
            freq += self.selections[self.index]

            self.state.set_radio(freq=freq)

    def press(self):
        """
        Step between the adjustment modes.
        """
        self.index = (self.index + 1) % 3

    def render(self):
        """
        Draw the UI to the display.
        """
        select = self.selections[self.index]
        self.display.oled.text("Frequency {}:".format(select), 0, 36)
        self.display.oled.text(
            "{:03.1f}".format(self.state.radio_freq), 30, 46)

        message = "Frequency: {:03.1f} ".format(self.state.radio_freq)
        print_debug(message, end="")


class Functionality_AlarmTime(MenuItem):
    """
    Change the current alarm time by adjusting each hour/min/sec value
    independently. Pressing the encoder toggles between which time component
    to adjust.

    See MenuItem for the signature.
    """
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

        self.selections = ["hour", "minute", "second"]
        self.index = 0

    def ccw(self):
        """
        Decrease the appropriate time component.
        """
        alarm_time = list(self.state.alarm_time)
        alarm_time[self.index] -= 1

        self.state.set_alarm(time=alarm_time)

    def cw(self):
        """
        Increase the appropriate time component.
        """
        alarm_time = list(self.state.alarm_time)
        alarm_time[self.index] += 1

        self.state.set_alarm(time=alarm_time)

    def press(self):
        """
        Toggle between which time component to adjust.
        """
        self.index = (self.index + 1) % 3

    def render(self):
        """
        Draw the UI to the display.
        """
        astring = self.state.get_alarm_string()
        parts = astring.split(":")

        self.display.oled.text("Alarm time:", 0, 36)
        self.display.oled.text(astring, 30, 46)

        message = "Alarm time: {}".format(astring)
        print_debug(message, end="")


class Functionality_ClockTime(MenuItem):
    """
    Change the current clock time by adjusting each hour/min/sec value
    independently. Pressing the encoder toggles between which time component
    to adjust.

    See MenuItem for the signature.
    """
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

        self.selections = ["hour", "minute", "second"]
        self.index = 0
        self.datetime = [0, 0, 0, 0, 0, 0, 0, 0]

    def enter(self):
        """
        Copy the current RTC datetime value into storage so it can be adjusted
        without the Pico constantly increasing the value every second. Also
        pause the reset timer.
        """
        self.handler.pause_reset_timer = True
        year, month, day, _, hour, minute, sec, _ = self.state.rtc.datetime()
        self.datetime = list(self.state.rtc.datetime())

    def ccw(self):
        """
        Decrease the appropriate time component and bound all the datetime
        values.
        """
        self.datetime[self.index+4] -= 1
        self.datetime[4] %= 24
        self.datetime[5] %= 60
        self.datetime[6] %= 60

    def cw(self):
        """
        Increase the appropriate time component and bound all the datetime
        values.
        """
        self.datetime[self.index+4] += 1
        self.datetime[4] %= 24
        self.datetime[5] %= 60
        self.datetime[6] %= 60

    def press(self):
        """
        Toggle between which time component to adjust.
        """
        self.index = (self.index + 1) % 3

    def back(self):
        """
        Apply the modified datetime value back onto the RTC before exiting out
        of this menu item and unmask the reset timer.
        """
        self.state.rtc.datetime(self.datetime)
        self.handler.pause_reset_timer = False
        super().back()

    def render(self):
        """
        Draw the UI to the display.
        """
        datetime = self.state.datetimezoned(self.datetime)
        tstring = self.state.format_clock_string(datetime)[0]

        selection = self.selections[self.index]
        self.display.oled.text("Change {}:".format(selection), 0, 36)
        self.display.oled.text(tstring, 30, 46)

        message = "Clock time: {}".format(tstring)
        print_debug(message, end="")


class Functionality_ClockDate(MenuItem):
    """
    Change the current clock date by adjusting each year/month/day value
    independently. Pressing the encoder toggles between which date component
    to adjust.

    See MenuItem for the signature.
    """
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

        self.selections = ["year", "month", "day"]
        self.index = 1
        self.datetime = [0, 0, 0, 0, 0, 0, 0, 0]

    def enter(self):
        """
        Copy the current RTC datetime value into storage so it can be adjusted
        without the Pico constantly increasing the value every second. Also
        pause the reset timer.
        """
        self.index = 1
        self.handler.pause_reset_timer = True
        year, month, day, _, hour, minute, sec, _ = self.state.rtc.datetime()
        self.datetime = list(self.state.rtc.datetime())

    def ccw(self):
        """
        Decrease the appropriate time component and bound all the datetime
        values.
        """
        self.datetime[self.index] -= 1
        self.datetime[0] = max(self.datetime[0], 0)
        self.datetime[1] = max(min(self.datetime[1], 12), 1)

        month = self.datetime[1]
        is_leap = clock_state.is_leap_year(self.datetime[0])
        monthdays = clock_state.MONTHDAYS[month] + int(is_leap and month == 2)

        self.datetime[2] = max(min(self.datetime[2], monthdays), 1)

    def cw(self):
        """
        Increase the appropriate time component and bound all the datetime
        values.
        """
        self.datetime[self.index] += 1
        self.datetime[0] = max(self.datetime[0], 0)
        self.datetime[1] = max(min(self.datetime[1], 12), 1)

        month = self.datetime[1]
        is_leap = clock_state.is_leap_year(self.datetime[0])
        monthdays = clock_state.MONTHDAYS[month] + int(is_leap and month == 2)

        self.datetime[2] = max(min(self.datetime[2], monthdays), 1)

    def press(self):
        """
        Toggle between which time component to adjust.
        """
        self.index = (self.index + 1) % 3

    def back(self):
        """
        Apply the modified datetime value back onto the RTC before exiting out
        of this menu item and unmask the reset timer.
        """
        self.state.rtc.datetime(self.datetime)
        self.handler.pause_reset_timer = False
        super().back()

    def render(self):
        """
        Draw the UI to the display.
        """
        datetime = self.state.datetimezoned(self.datetime)
        dstring = self.state.format_clock_string(datetime)[1]

        selection = self.selections[self.index]
        self.display.oled.text("Change {}:".format(selection), 0, 36)
        self.display.oled.text(dstring, 30, 46)

        message = "Clock date: {}".format(dstring)
        print_debug(message, end="")


class Functionality_Toggle(MenuItem):
    """
    Toggle between two states on a provided enable-disable pair.

    See MenuItem for the signature.
    """
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

        self._enabled = False
        self._enable_fn = None
        self._disable_fn = None

    def set_toggle_fns(self, enable_fn, disable_fn):
        """
        Assign enable display function to be called to toggle a value between
        two states.
        """
        self._enable_fn = enable_fn
        self._disable_fn = disable_fn

    def ccw(self):
        """
        Call the given disable function when the encoder is rotated conter
        clockwise.
        """
        if self._enabled and self._disable_fn:
            self._disable_fn()

        self._enabled = False

    def cw(self):
        """
        Call the given enable function when the encoder is rotated clockwise.
        """
        if not self._enabled and self._enable_fn:
            self._enable_fn()

        self._enabled = True

    def render(self):
        """
        Draw the UI to the display.
        """
        sstring = "<unlinked>"
        if self._disable_fn or self._enable_fn:
            sstring = "on" if self._enabled else "off"

        self.display.oled.text("State:", 0, 36)
        self.display.oled.text(sstring, 30, 46)

        message = "{} state: <{}>".format(self.name, sstring)
        print_debug(message, end="")


class Functionality_Roller(MenuItem):
    """
    Roll the value of a given parameter set-get pair by rotating the rotary
    encoder.

    See MenuItem for the signature.
    """
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

        self._value = None
        self._increment = 1
        self._str_fn = None

        self._set_fn = None
        self._get_fn = None

    def set_roller_fns(self, set_fn, get_fn, increment=1, str_fn=None):
        """
        Assign a set-get function pair to be called in order to roll a value.
        set_fn(function): Function that will apply a single given value.
        get_fn(function); Function that will return the current value of a
            single attribute.
        increment(int): How much to increase or decrease the given value for
            each encoder pulse.
        str_fn(function): Function to generate the text represention of the
            rolled  value.
        """
        self._set_fn = set_fn
        self._get_fn = get_fn
        self._increment = increment
        self._str_fn = str_fn

        self._value = self._get_fn()

    def ccw(self):
        """
        Decrement the linked value by the increment amount.
        """
        if not self._set_fn:
            return

        self._value -= self._increment
        self._set_fn(self._value)
        self._value = self._get_fn()

    def cw(self):
        """
        Increment the linked value by the increment amount.
        """
        if not self._set_fn:
            return

        self._value += self._increment
        self._set_fn(self._value)
        self._value = self._get_fn()

    def render(self):
        """
        Draw the UI to the display.
        """
        vstring = "<unlinked>"
        if self._set_fn and self._get_fn:
            vstring = str(self._str_fn() if self._str_fn else self._get_fn())

        self.display.oled.text("Value:", 0, 36)
        self.display.oled.text(vstring, 30, 46)

        message = "{}: <{}>".format(self.name, vstring)
        print_debug(message, end="")


class Functionality_AlarmPattern(Functionality_Roller):
    """
    Set which alarm pattern to play. Augments the roller with alarm test
    functionality.

    See MenuItem for the signature.
    """
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)
        self.alarm_state = clock_state._ALARM_OFF

    def enter(self):
        # Mask the reset callback and save the current alarm state.
        self.handler.pause_reset_timer = True
        self.alarm_state = self.state.alarm_state

    def cw(self):
        """
        Stop the alarm test if it is sounding, otherwise default input
        handling.
        """
        if self.state.alarm_sounding():
            self.state.alarm_state = self.alarm_state
            self.state._unsound_alarm()
        else:
            super().cw()

    def ccw(self):
        """
        Stop the alarm test if it is sounding, otherwise default input
        handling.
        """
        if self.state.alarm_sounding():
            self.state.alarm_state = self.alarm_state
            self.state._unsound_alarm()
        else:
            super().ccw()

    def press(self):
        """
        Begin or stop the alarm test.
        """
        if self.state.alarm_sounding():
            self.state.alarm_state = self.alarm_state
            self.state._unsound_alarm()
        else:
            self.state.alarm_state = clock_state._ALARM_TEST
            self.state._sound_alarm()

    def back(self):
        """
        Stop the alarm test if it is sounding, otherwise default input
        handling.
        """
        if self.state.alarm_sounding():
            self.state.alarm_state = self.alarm_state
            self.state._unsound_alarm()
        else:
            self.handler.pause_reset_timer = False
            super().back()


class Functionality_MenuSelect(MenuItem):
    """
    Encodes a folder-like menu item. This is meant to just hold other menu
    items in order to better organize the menu tree.

    See MenuItem for the signature.
    """
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

        self.index = 0

    def cw(self):
        """
        Select the next child menu item in this folder.
        """
        if(self.index < len(self.handler._current.children) -1):
            self.index += 1
        else:
            self.index = 0

    def ccw(self):
        """
        Select the previous child menu item of this folder.
        """
        if(self.index > 0):
            self.index -= 1
        else:
            self.index = (len(self.handler._current.children) - 1)

    def press(self):
        """
        Set the currently selected child item as the new active menu item. Also
        call the enter method on the item.
        """
        self.handler._current = self.children[self.index]
        self.handler._current.enter()

    def render(self):
        """
        Draw the UI to the display.
        """
        # Draw the currently selected item and up to 4 of its closest siblings.
        start = max(min(self.index + 4, len(self.children)) - 4, 0)
        end = min(self.index + 4, len(self.children))

        for k in range(start, end):
            line = "{}) {}".format(k+1, self.children[k].name)
            if len(line) > 16:
                line = line[:14] + ".."

            if k == self.index:
                self.display.oled.rect(0, 23 + 10*(k-start), 128, 9, 1, True)

            self.display.oled.text(line, 0, 24 + 10*(k-start), int(k != self.index))

        print_debug("<{}>".format(self.children[self.index].name), end="")


class Functionality_ClockDisplay(Functionality_MenuSelect):
    """
    The main clock display is just a subclass of the default menu item. It acts
    mostly as a folder just with a completely different render routine.

    See MenuItem for the signature.
    """
    def render(self):
        """
        Draw the UI to the display.
        """
        tstring, dstring = self.state.get_clock_string()

        # Draw the date string.
        self.display.oled.text(self.state.get_temp_string(), 0, 0)
        self.display.oled.text(dstring, 40, 0)

        # Draw the timezone offset.
        if self.state.tz_offset:
            self.display.oled.text("UTC{:+d}".format(self.state.tz_offset), 64, 9)

        # Draw the bell icon if the alarm is enabled.
        if self.state.alarm_enabled:
            self.display.bell(120, 9)

        # Draw the time string replacing the digits with tall digits.
        for k, char in enumerate(tstring):
            if "0" <= char and char <= "9":
                self.display.tall_digit(ord(char) - ord("0"), 8+10*k, 24)
            else:
                self.display.oled.text(char, 8+10*k, 31)

        # Draw the radio information if the radio is enabled.
        if self.state.radio_enabled:
            freq = self.state.radio_freq
            channel_name = self.state.stations.get(self.state.radio_freq, "")
            self.display.oled.text("{:.1f} {}".format(freq, channel_name), 0, 47)

            volume = self.state.radio_volume + 1
            if self.state.radio_muted:
                self.display.speaker_mute(0, 56)
            else:
                self.display.speaker_on(0, 56)
                self.display.oled.text("{:<2d}".format(volume), 10, 56)

            strength = self.state.radio.get_signal_strength()
            self.display.radio(32, 56)
            self.display.oled.text("{:<2d}".format(strength), 42, 56)

        print_debug(tstring, end="")

    def ccw(self):
        # Make a ccw input act as a press so any input opens the settings menu.
        self.press()

    def cw(self):
        # Make a cw input act as a press so any input opens the settings menu.
        self.press()


class Functionality_Change_Lighting(MenuItem):
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

    def press(self):
        """
        Toggle the value of the appropriate LED mode variable.
        """
        for item in self.state.led_states:
            if item != self.name:
                self.state.led_states[item] = False
            else:
                self.state.led_states[item] = not self.state.led_states[item]

        if self.name == "Set Colour":
            self.leds.set_mode(Leds_Handler.LEDS_CONT)
        elif self.name == "FFT":
            self.leds.set_mode(Leds_Handler.LEDS_FFT)
        else:
            self.leds.set_mode(Leds_Handler.LEDS_OFF)

    def ccw(self):
        # Make a ccw input act as a press so any input toggles.
        self.press()

    def cw(self):
        # Make a ccw input act as a press so any input toggles.
        self.press()

    def render(self):
        """
        Draw the UI to the display.
        """
        self.display.oled.text(
            '<' + str(self.state.led_states[self.name]) + '>', 0, 36)