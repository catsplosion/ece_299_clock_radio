from machine import Timer

import clock_state
import Leds_Handler


_RESET_DELAY = 10000
_DEBUG = False

def print_debug(*args, **kwds):
    if _DEBUG:
        print(*args, **kwds)


class MenuHandler: #keeping track of what is currently selected,
    def __init__(self, encoder, accept_button, back_button, state, display, leds):
        self.state = state
        self.display = display
        self.root = None #This creates an attribute local to the instance. Self is automatically passed?
        self._current = self.root
        self.pause_reset_timer = False
        self.alarm_screen = False

        encoder.set_ccw_fn(self._ccw_handler)
        encoder.set_cw_fn(self._cw_handler)
        accept_button.set_press_fn(self._acceptpressed)
        back_button.set_press_fn(self._backpressed)

        self._reset_timer = Timer()
        

    def __del__(self):
        pass

    def _start_reset_timer(self):
        self._reset_timer.init(
            mode=Timer.ONE_SHOT,
            period=_RESET_DELAY,
            callback=self._reset_timer_handler
        )

    def _reset_timer_handler(self, timer):
        if self.pause_reset_timer:
            return

        self._current = self.root
        self.render()

    def render(self):
        if not self._current:
            return

        if self.state.alarm_state in (clock_state._ALARM_SOUND, clock_state._ALARM_TEST):
            if not self.alarm_screen:
                self.display.oled.fill(0)
                self.display.oled.text("!! ALARM !!", 20, 28)
                self.display.oled.show()
                self.alarm_screen = True
            return

        self.display.oled.fill(0)

        if self._current != self.root:
            #draw square or something (constant)
            self.display.oled.rect(0, 0, 128, 20, 1)
            self.display.oled.text(self._current.name, 4, 6, 2)
            print_debug(self._current.name + " ", end="")

        self._current.render()
        self.display.oled.show()
        print_debug("")

        self.alarm_screen = False

    def _ccw_handler(self):
        if not self._current:
            return

        self._start_reset_timer()

        if self.state.alarm_enabled and self.state.alarm_sounding():
            self.state.shutoff_alarm()
            return

        self._current.ccw()
        self.render()

    def _cw_handler(self):
        if not self._current:
            return

        self._start_reset_timer()

        if self.state.alarm_enabled and self.state.alarm_sounding():
            self.state.shutoff_alarm()
            return

        self._current.cw()
        self.render()

    def _acceptpressed(self): ## _ thigns outside the class cant touch it __, no subclasses touching it
        if not self._current:
            return

        self._start_reset_timer()

        if self.state.alarm_enabled and self.state.alarm_sounding():
            self.state.snooze_alarm()
            return

        self._current.press()
        self.render()

    def _backpressed(self):
        if not self._current:
            return

        if self.state.alarm_enabled and self.state.alarm_sounding():
            self.state.snooze_alarm()
            return

        self._current.back()
        self.render()

class MenuItem:
    def __init__(self, parent, name, state, display, leds, handler=None):
        self.parent = parent #Attributes
        self.name = name
        self.handler = handler
        self.state = state
        self.display = display
        self.leds = leds
        
        if handler is None:
            self.handler = parent.handler

        self.children = [] # Array of MenuItems

    def add_child(self, node): #Append a MenuItem as a child to the current MenuItem
        self.children.append(node)
        node.parent = self
        return node #so you can actually do stuff with it (ex new = node.add_child(...))

    def enter(self):
        pass

    def cw(self): #all of this will be overloaded.
        pass

    def ccw(self):
        pass

    def press(self):
        pass

    def back(self):
        if self.parent:
            self.handler._current = self.parent

    def render(self):
        #special stuff
        pass


class Functionality_ChangeRGB(MenuItem):
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

        #self.selections = ['r', 'g', 'b']
        self.index = 0

    def ccw(self):
        color = list(self.state.led_color)
        color[self.index] -= 5

        self.state.set_led_color(color)

    def cw(self):
        color = list(self.state.led_color)
        color[self.index] += 5

        self.state.set_led_color(color)

    def press(self):
        if(self.index == 2):
            self.index = 0
        else:
            self.index += 1

    def render(self):
        self.display.oled.text("RGB:", 0, 36)

        for i, channel in enumerate(("r", "g", "b")):
            if self.index == i:
                self.display.oled.rect(43*i, 45, 32, 10, 1, True)

            value = self.state.led_color[i]
            self.display.oled.text("{}={}".format(channel, value), 43*i, 46, self.index != i)

        message = "RGB: r={} g={} b={}".format(*self.state.led_color)
        print_debug(message, end="")


class Functionality_ChangeTimeFormat(MenuItem):
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

    def ccw(self):
        self.state.set_clock_mode("12hr")

    def cw(self):
        self.state.set_clock_mode("24hr")

    def press(self):
        pass

    def render(self):
        mstring = self.state.get_clock_mode_string()
        self.display.oled.text("Time format:", 0, 36)
        self.display.oled.text(mstring, 30, 46)

        message = "Time format: {}".format(mstring)
        print_debug(message, end="")


class Functionality_FrequencyChange(MenuItem):

    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

        self.selections = [1, 0.2, "seek"]
        self.index = 0

    def ccw(self):
        if self.index == 2:
            self.state.seek_down()
        else:
            freq = self.state.radio_freq
            freq -= self.selections[self.index]

            self.state.set_radio(freq=freq)

    def cw(self):
        if self.index == 2:
            self.state.seek_up()
        else:
            freq = self.state.radio_freq
            freq += self.selections[self.index]

            self.state.set_radio(freq=freq)

    def press(self):
        self.index = (self.index + 1) % 3

    def render(self):
        select = self.selections[self.index]
        self.display.oled.text("Frequency {}:".format(select), 0, 36)
        self.display.oled.text("{:03.1f}".format(self.state.radio_freq), 30, 46)

        message = "Frequency: {:03.1f} ".format(self.state.radio_freq)
        print_debug(message, end="")


class Functionality_AlarmTime(MenuItem):
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

        self.selections = ["hour", "minute", "second"]
        self.index = 0

    def ccw(self):
        alarm_time = list(self.state.alarm_time)
        alarm_time[self.index] -= 1

        self.state.set_alarm(time=alarm_time)

    def cw(self):
        alarm_time = list(self.state.alarm_time)
        alarm_time[self.index] += 1

        self.state.set_alarm(time=alarm_time)

    def press(self):
        self.index = (self.index + 1) % 3

    def render(self):
        astring = self.state.get_alarm_string()
        parts = astring.split(":")

        self.display.oled.text("Alarm time:", 0, 36)
        self.display.oled.text(astring, 30, 46)

        message = "Alarm time: {}".format(astring)
        print_debug(message, end="")


class Functionality_ClockTime(MenuItem):
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

        self.selections = ["hour", "minute", "second"]
        self.index = 0
        self.datetime = [0, 0, 0, 0, 0, 0, 0, 0]

    def enter(self):
        self.handler.pause_reset_timer = True
        year, month, day, _, hour, minute, sec, _ = self.state.rtc.datetime()
        self.datetime = list(self.state.rtc.datetime())

    def ccw(self):
        self.datetime[self.index+4] -= 1
        self.datetime[4] %= 24
        self.datetime[5] %= 60
        self.datetime[6] %= 60

    def cw(self):
        self.datetime[self.index+4] += 1
        self.datetime[4] %= 24
        self.datetime[5] %= 60
        self.datetime[6] %= 60

    def press(self):
        self.index = (self.index + 1) % 3

    def back(self):
        self.state.rtc.datetime(self.datetime)
        self.handler.pause_reset_timer = False
        super().back()

    def render(self):
        datetime = self.state.datetimezoned(self.datetime)
        tstring = self.state.format_clock_string(datetime)[0]

        selection = self.selections[self.index]
        self.display.oled.text("Change {}:".format(selection), 0, 36)
        self.display.oled.text(tstring, 30, 46)

        message = "Clock time: {}".format(tstring)
        print_debug(message, end="")


class Functionality_ClockDate(MenuItem):
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

        self.selections = ["year", "month", "day"]
        self.index = 1
        self.datetime = [0, 0, 0, 0, 0, 0, 0, 0]

    def enter(self):
        self.index = 1
        self.handler.pause_reset_timer = True
        year, month, day, _, hour, minute, sec, _ = self.state.rtc.datetime()
        self.datetime = list(self.state.rtc.datetime())

    def ccw(self):
        self.datetime[self.index] -= 1
        self.datetime[0] = max(self.datetime[0], 0)
        self.datetime[1] = max(min(self.datetime[1], 12), 1)
        
        month = self.datetime[1]
        is_leap = clock_state.is_leap_year(self.datetime[0])
        monthdays = clock_state.MONTHDAYS[month] + int(is_leap and month == 2)
        
        self.datetime[2] = max(min(self.datetime[2], monthdays), 1)

    def cw(self):
        self.datetime[self.index] += 1
        self.datetime[0] = max(self.datetime[0], 0)
        self.datetime[1] = max(min(self.datetime[1], 12), 1)
        
        month = self.datetime[1]
        is_leap = clock_state.is_leap_year(self.datetime[0])
        monthdays = clock_state.MONTHDAYS[month] + int(is_leap and month == 2)
        
        self.datetime[2] = max(min(self.datetime[2], monthdays), 1)

    def press(self):
        self.index = (self.index + 1) % 3

    def back(self):
        self.state.rtc.datetime(self.datetime)
        self.handler.pause_reset_timer = False
        super().back()

    def render(self):
        datetime = self.state.datetimezoned(self.datetime)
        dstring = self.state.format_clock_string(datetime)[1]

        selection = self.selections[self.index]
        self.display.oled.text("Change {}:".format(selection), 0, 36)
        self.display.oled.text(dstring, 30, 46)

        message = "Clock date: {}".format(dstring)
        print_debug(message, end="")


class Functionality_Toggle(MenuItem):
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

        self._enabled = False
        self._enable_fn = None
        self._disable_fn = None

    def set_toggle_fns(self, enable_fn, disable_fn):
        self._enable_fn = enable_fn
        self._disable_fn = disable_fn

    def ccw(self):
        if self._enabled and self._disable_fn:
            self._disable_fn()

        self._enabled = False

    def cw(self):
        if not self._enabled and self._enable_fn:
            self._enable_fn()

        self._enabled = True

    def render(self):
        sstring = "<unlinked>"
        if self._disable_fn or self._enable_fn:
            sstring = "on" if self._enabled else "off"

        self.display.oled.text("State:", 0, 36)
        self.display.oled.text(sstring, 30, 46)

        message = "{} state: <{}>".format(self.name, sstring)
        print_debug(message, end="")


class Functionality_Roller(MenuItem):
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)

        self._value = None
        self._increment = 1
        self._str_fn = None

        self._set_fn = None
        self._get_fn = None

    def set_roller_fns(self, set_fn, get_fn, increment=1, str_fn=None):
        self._set_fn = set_fn
        self._get_fn = get_fn
        self._increment = increment
        self._str_fn = str_fn

        self._value = self._get_fn()

    def ccw(self):
        if not self._set_fn:
            return

        self._value -= self._increment
        self._set_fn(self._value)
        self._value = self._get_fn()

    def cw(self):
        if not self._set_fn:
            return

        self._value += self._increment
        self._set_fn(self._value)
        self._value = self._get_fn()

    def render(self):
        vstring = "<unlinked>"
        if self._set_fn and self._get_fn:
            vstring = str(self._str_fn() if self._str_fn else self._get_fn())

        self.display.oled.text("Value:", 0, 36)
        self.display.oled.text(vstring, 30, 46)

        message = "{}: <{}>".format(self.name, vstring)
        print_debug(message, end="")


class Functionality_AlarmPattern(Functionality_Roller):
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)
        self.alarm_state = clock_state._ALARM_OFF

    def enter(self):
        self.handler.pause_reset_timer = True
        self.alarm_state = self.state.alarm_state

    def cw(self):
        if self.state.alarm_sounding():
            self.state.alarm_state = self.alarm_state
            self.state._unsound_alarm()
        else:
            super().cw()

    def ccw(self):
        if self.state.alarm_sounding():
            self.state.alarm_state = self.alarm_state
            self.state._unsound_alarm()
        else:
            super().ccw()

    def press(self):
        if self.state.alarm_sounding():
            self.state.alarm_state = self.alarm_state
            self.state._unsound_alarm()
        else:
            self.state.alarm_state = clock_state._ALARM_TEST
            self.state._sound_alarm()

    def back(self):
        if self.state.alarm_sounding():
            self.state.alarm_state = self.alarm_state
            self.state._unsound_alarm()
        else:
            self.handler.pause_reset_timer = False
            super().back()


class Functionality_MenuSelect(MenuItem): #Draw '<' "Item" '>'
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler) 

        self.index = 0

    def cw(self):
        if(self.index < len(self.handler._current.children) -1):
            self.index += 1
        else:
            self.index = 0

    def ccw(self):
        if(self.index > 0):
            self.index -= 1 
        else:
            self.index = (len(self.handler._current.children) - 1)

    def press(self): 
        self.handler._current = self.children[self.index]
        self.handler._current.enter()

    def render(self):
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
    def render(self):
        tstring, dstring = self.state.get_clock_string()
        self.display.oled.text(self.state.get_temp_string(), 0, 0)
        self.display.oled.text(dstring, 40, 0)

        if self.state.tz_offset:
            self.display.oled.text("UTC{:+d}".format(self.state.tz_offset), 64, 9)

        if self.state.alarm_enabled:
            self.display.bell(120, 9)

        for k, char in enumerate(tstring):
            if "0" <= char and char <= "9":
                self.display.tall_digit(ord(char) - ord("0"), 8+10*k, 24)
            else:
                self.display.oled.text(char, 8+10*k, 31)

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
        self.press()

    def cw(self):
        self.press()

class Functionality_Change_Lighting(MenuItem):
    def __init__(self, parent, name, state, display, leds, handler):
        super().__init__(parent, name, state, display, leds, handler)
                
    def press(self):
        
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
        self.press()

    def cw(self):
        self.press()

    def render(self):
        #print(self.values_list[0])
        self.display.oled.text('<' + str(self.state.led_states[self.name]) + '>', 0, 36)