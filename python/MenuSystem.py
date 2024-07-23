#import rotary_encoder as re
#import push_button as pb
#from machine import Pin, SPI


class MenuHandler: #keeping track of what is currently selected,
    def __init__(self, encoder, accept_button, back_button, state, display):

        self.display = display
        self.root = Functionality_MenuSelect(None, "root_node", state, display, self) #This creates an attribute local to the instance. Self is automatically passed?
        self._current = self.root

        encoder.set_ccw_fn(self._ccw_handler)
        encoder.set_cw_fn(self._cw_handler)
        accept_button.set_press_fn(self._acceptpressed)
        back_button.set_press_fn(self._backpressed)

    def __del__(self):
        pass

    def render(self):
        #draw square or something (constant)
        self.display.oled.fill(0)
        self.display.oled.rect(0, 0, 128, 20, 1)
        self.display.oled.text("Swag Swag Swag", 8, 6)
        print("Swag Swag Swag: ", end="")
        self._current.render()
        self.display.oled.show()
        print("")

    def _ccw_handler(self):
        self._current.ccw()

    def _cw_handler(self):
        self._current.cw()

    def _acceptpressed(self): ## _ thigns outside the class cant touch it __, no subclasses touching it
        self._current.press()

    def _backpressed(self):
        self._current.back()


class MenuItem:
    def __init__(self, parent, name, state, display, handler=None):
        self.parent = parent #Attributes
        self.name = name
        self.handler = handler
        self.state = state
        self.display = display

        if handler is None:
            self.handler = parent.handler

        self.children = [] # Array of MenuItems

    def add_child(self, node): #Append a MenuItem as a child to the current MenuItem
        self.children.append(node)
        node.parent = self
        return node #so you can actually do stuff with it (ex new = node.add_child(...))

    def cw(self): #all of this will be overloaded.
        pass

    def ccw(self):
        pass

    def press(self):
        pass

    def back(self):
        pass

    def render(self):
        #special stuff
        pass


class Functionality_ChangeRGB(MenuItem):
    def __init__(self, parent, name, state, display, handler):
        super().__init__(parent, name, state, display, handler)

        self.selections = ['r', 'g', 'b']
        self.index = 0

    def ccw(self):
        color = list(self.state.led_color)
        color[self.index] -= 5

        self.state.set_led_color(color)
        self.handler.render()

    def cw(self):
        color = list(self.state.led_color)
        color[self.index] += 5

        self.state.set_led_color(color)
        self.handler.render()

    def press(self):
        if(self.index == 2):
            self.index = 0
        else:
            self.index += 1

    def back(self):
        self.handler._current = self.parent
        self.handler.render()

    def render(self):
        message = "RGB: r={} g={} b={}".format(*self.state.led_color)
        self.display.oled.text(message, 0, 36)
        print(message, end="")


class Functionality_ChangeTimeFormat(MenuItem):
    def __init__(self, parent, name, state, display, handler):
        super().__init__(parent, name, state, display, handler)

    def ccw(self):
        self.state.set_clock_mode("12hr")
        self.handler.render()

    def cw(self):
        self.state.set_clock_mode("24hr")
        self.handler.render()

    def press(self):
        pass

    def back(self):
        self.handler._current = self.parent
        self.handler.render()

    def render(self):
        mstring = self.state.get_clock_mode_string()
        message = "Time format: {}".format(mstring)
        self.display.oled.text(message, 0, 36)
        print(message, end="")


class Functionality_FrequencyChange(MenuItem):

    def __init__(self, parent, name, state, display, handler):
        super().__init__(parent, name, state, display, handler)

        self.selections = [1, 0.2]
        self.index = 0

    def ccw(self):
        freq = self.state.radio_freq
        freq -= self.selections[self.index]

        self.state.set_radio(freq=freq)
        self.handler.render()

    def cw(self):
        freq = self.state.radio_freq
        freq += self.selections[self.index]

        self.state.set_radio(freq=freq)
        self.handler.render()

    def press(self):
        self.index = 0 if self.index else 1

    def back(self):
        self.handler._current = self.parent
        self.handler.render()

    def render(self):
        message = "Frequency: {:03.1f} ".format(self.state.radio_freq)
        self.display.oled.text(message, 0, 36)
        print(message, end="")


class Functionality_AlarmTime(MenuItem):
    def __init__(self, parent, name, state, display, handler):
        super().__init__(parent, name, state, display, handler)

        self.selections = ["hour", "minute"]
        self.index = 0

    def ccw(self):
        alarm_time = list(self.state.alarm_time)
        alarm_time[self.index + 1] -= 1

        self.state.set_alarm(time=alarm_time)
        self.handler.render()

    def cw(self):
        alarm_time = list(self.state.alarm_time)
        alarm_time[self.index + 1] += 1

        self.state.set_alarm(time=alarm_time)
        self.handler.render()

    def press(self):
        self.index = 0 if self.index else 1

    def back(self):
        self.handler._current = self.parent
        self.handler.render()

    def render(self):
        astring = self.state.get_alarm_string()
        message = "Alarm time: {}".format(astring)
        self.display.oled.text(message, 0, 36)
        print(message, end="")


class Functionality_MenuSelect(MenuItem): #Draw '<' "Item" '>'
    def __init__(self, parent, name, state, display, handler):
        super().__init__(parent, name, state, display, handler) #function super() makes it so that it initalizes all the methods in MenuItem (goofy python moment)

        self.index = 0

    def ccw(self):
        if(self.index < len(self.handler._current.children) -1):
            self.index += 1
        else:
            self.index = 0

        self.handler.render()

    def cw(self):
        if(self.index > 0):
            self.index -= 1 #Reminder: self. refrences the attribute to that object, if it was just Index = then thats a local var
        else:
            self.index = (len(self.handler._current.children) - 1)

        self.handler.render()

    def press(self): ## _ thigns outside the class cant touch it __, no subclasses touching it
        self.handler._current = self.children[self.index]

        self.handler.render()

    def back(self):
        self.handler._current = self.parent

        self.handler._current.render()

    def render(self):
        self.display.oled.text('<' + self.children[self.index].name + '>', 0, 36)
        print("<{}>".format(self.children[self.index].name), end="")
