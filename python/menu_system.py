from machine import Pin, SPI, Timer
from ssd1306 import SSD1306_SPI
import framebuf



_START = 0
_CW1 = 1
_CW2 = 2
_CW3 = 3
_CCW1 = 4
_CCW2 = 5
_CCW3 = 6

_TTABLE = [
    [_START, _CCW1,  _CW1,   _START],
    [_CW2,   _START, _CW1,   _START],
    [_CW2,   _CW3,   _CW1,   _START],
    [_CW2,   _CW3,   _START, _START],
    [_CCW2,  _CCW1,  _START, _START],
    [_CCW2,  _CCW1,  _CCW3,  _START],
    [_CCW2,  _START, _CCW3,  _START],
    [_START, _START, _START, _START],
]


# Define columns and rows of the Oled display. These numbers are the standard values. 
SCREEN_WIDTH = 128 
SCREEN_HEIGHT = 64 


# Initialize I/O pins associated with the Oled display SPI interface

SPI_SCK = Pin(18) 
SPI_SDA = Pin(19) 
SPI_RES = Pin(21) 
SPI_DC  = Pin(20) 
SPI_CS  = Pin(17)  

SPI_DEVICE = 0

# Initialize the SPI interface for the Oled display

OLED_SPI = SPI(SPI_DEVICE, baudrate= 100000, sck= SPI_SCK, mosi=SPI_SDA)


# Initialize the display

OLED = SSD1306_SPI(SCREEN_WIDTH, SCREEN_HEIGHT, OLED_SPI, SPI_DC, SPI_RES, SPI_CS, True)


# Assign a value to a variable
Count = 3113

_HOLD_UP = 0
_FALLING = 1
_HOLD_DOWN = 2
_RISING = 3


class PushButton(object):
    """
    Configure a machine.Pin as a push button input. Handles de-bouncing using a
    delay check. Calls a given press function at the end of the button
    press-release cycle. The `pull_up` parameter determines whether the press
    function is called on rising edge (True) or falling edge (False).

    pin(any): Id of the button pin. See id arg of machine.Pin.__init__.
    pull_up(bool): Set pin in pull-up mode if True, otherwise pull-down mode.
    delay(int): Time in ms to delay before re-checking the pin value.
    """
    def __init__(self, pin, pull_up=True, delay=8):
        self._pull = Pin.PULL_UP if pull_up else Pin.PULL_DOWN
        self._delay = delay
        self._state = _HOLD_UP if pull_up else _HOLD_DOWN

        self._pin = Pin(pin, Pin.IN, self._pull)
        self._pin.irq(self._irq_handler, Pin.IRQ_FALLING | Pin.IRQ_RISING)

        self._timer = Timer()

        self._press_fn = None
        self._press_fn_args = []

    def __del__(self):
        self._timer.deinit()
        self._pin.irq(None)

    def _irq_handler(self, pin):
        falling = pin.irq().flags() & 4
        rising = pin.irq().flags() & 8

        if self._state == _HOLD_UP and falling:
            self._state = _FALLING
            self._start_timer()
        elif self._state == _HOLD_DOWN and rising:
            self._state = _RISING
            self._start_timer()

    def _timer_handler(self, timer):
        pvalue = self._pin.value()

        if self._state == _FALLING and not pvalue:
            self._call_fall_fn()
        elif self._state == _RISING and pvalue:
            self._call_rise_fn()

        self._state = _HOLD_UP if pvalue else _HOLD_DOWN

    def _start_timer(self):
        self._timer.init(
            mode=Timer.ONE_SHOT,
            period=self._delay,
            callback=self._timer_handler
        )

    def _call_fall_fn(self):
        if self._pull == Pin.PULL_DOWN and self._press_fn:
            self._press_fn(*self._press_fn_args)

    def _call_rise_fn(self):
        if self._pull == Pin.PULL_UP and self._press_fn:
            self._press_fn(*self._press_fn_args)

    def set_press_fn(self, fn, args=[]):
        """
        Assign a function to be called at the end of the button press-release
        cycle.

        fn(function): Function to call.
        args(list): Arguments to provide the function when called. No other
            arguments will be provided.
        """
        self._press_fn = fn
        self._press_fn_args = args



class RotaryEncoder(object):
    """
    Initializes two specifed pins as inputs for a rotary encoder. Handles the
    rotation and debounce logic, calling given response functions as
    appropriate.

    pin_clk(any): Id of the rotary clk pin. See id arg of machine.Pin.__init__.
    pin_dir(any): Id of the rotary dir pin. See id arg of machine.Pin.__init__.
    pull_up(bool): Set pins in pull-up mode if True, otherwise pull-down mode.
    """
    def __init__(self, pin_clk, pin_dir, pull_up=True):
        self._pull = Pin.PULL_UP if pull_up else Pin.PULL_DOWN

        self._pin_clk = Pin(pin_clk, Pin.IN, self._pull)
        self._pin_dir = Pin(pin_dir, Pin.IN, self._pull)

        self._pin_clk.irq(self._irq_handler, Pin.IRQ_FALLING | Pin.IRQ_RISING)
        self._pin_dir.irq(self._irq_handler, Pin.IRQ_FALLING | Pin.IRQ_RISING)

        self._state = _START
        self._cw_fn = None
        self._cw_fn_args = []
        self._ccw_fn = None
        self._ccw_fn_args = []

    def __del__(self):
        self._pin_clk.irq(None)
        self._pin_dir.irq(None)
    
    def _irq_handler(self, pin):
        index = self._pin_clk.value() + self._pin_dir.value()*2

        if self._pull is not Pin.PULL_UP:
            index = 3 - index
 
        if self._state == _CW3 and index == 3:
            self._call_cw_fn()
        elif self._state == _CCW3 and index == 3:
            self._call_ccw_fn()

        self._state = _TTABLE[self._state][index]
   
    def _call_cw_fn(self):
        if self._cw_fn:
            self._cw_fn(*self._cw_fn_args)

    def _call_ccw_fn(self):
        if self._ccw_fn:
            self._ccw_fn(*self._ccw_fn_args)

    def set_cw_fn(self, fn, args=[]):
        """
        Assign a function to be called when the encoder is rotated clockwise.

        fn(function): Function to call.
        args(list): Arguments to provide the function when called. No other
            arguments will be provided.
        """
        self._cw_fn = fn
        self._cw_fn_args = args

    def set_ccw_fn(self, fn, args=[]):
        """
        Assign a function to be called when the encoder is rotated counter-
        clockwise.

        fn(function): Function to call.
        args(list): Arguments to provide the function when called. No other
            arguments will be provided.
        """
        self._ccw_fn = fn
        self._ccw_fn_args = args


class Menu():
    
    def GetSize(self, Array): #No numpy lol
        Count = 0
        for item in Array:
            Count += 1
        return Count
     
    
    def UpdateOLED(self, Text):
        
        OLED.fill(0) # Clear the buffer
            
        for x in range (5):
            
            OLED.text("⇐"+Text+"⇒", 4, 10)
            
        OLED.show() # Transfer the buffer to the screen
    

    def UpdateMenu(self, NewMenu: dict): # Eastereggs coming soon
        self.__Menu_Items = NewMenu
        self.__menu_list = []
        
        for SubMenu in NewMenu:
            self.__menu_list.append(SubMenu)
    
    def __init__(self, Encoder, Button): #PushButton and Rotary Encoder for the menu
        
        self.__Menu_Items = {
            "Radio Freq" : {
                "Hundreds" : 0,
                "Tens" : 0,
                "Ones" : 0,
                "Hundredths" : 0,
                "Mode" : "FM",
                "Back" : None
            },
            
            "Mute" : {
                "IsMuted" : False,
                "Back" : None
            },
            
            "Volume" : {
                "Current_Volume" : 5,
                "Back" : None
            },
            
                "Back" : {
            }
            
        }
        
        Encoder.set_cw_fn(self.__Menu_CW_Handler)
        Encoder.set_ccw_fn(self.__Menu_CCW_Handler)
        Button.set_press_fn(self.__Menu_Select)
        
        self.__menu_list = []
        self.__Position = 0 # Position In MenuList
        self.__Is_Displayed = False # If Menu Is currently being displayed
        self.__selected_item = None  # Track currently selected item
        self.__InSubMenu = False
        
        self.__Sub_Keys = None
        self.__Selected_Item  = None
        
        self.UpdateMenu(self.__Menu_Items)
        
        self.__MenuSize = self.GetSize(self.__menu_list)
        
        print(self.__MenuSize)
        print(self.__menu_list)
        
        
        self.UpdateMenu(self.__Menu_Items)

    def __Menu_CW_Handler(self):
        print("Menu Moved CW")
        if(self.__Is_Displayed and not self.__InSubMenu):
            if(self.__Position >= 0 and self.__Position < 3):
                self.__Position += 1
                self.UpdateOLED(self.__menu_list[self.__Position])
            else:
                self.__Position = 0
                self.UpdateOLED(self.__menu_list[self.__Position])
        if(self.__InSubMenu):
            if self.__Position > 0:
                self.__Position -= 1
                self.UpdateOLED(self.__Sub_Keys[self.__Position])
        
    def __Menu_CCW_Handler(self):
        print("Menu Moved CCW")
        if(self.__Is_Displayed and not self.__InSubMenu):
            if(self.__Position <= 3 and self.__Position > 0):
                self.__Position -= 1
                self.UpdateOLED(self.__menu_list[self.__Position])
            else:
                self.__Position = 3
                self.UpdateOLED(self.__menu_list[self.__Position])
        if(self.__InSubMenu):
            if self.__Position < self.__MenuSize:
                self.__Position += 1
                self.UpdateOLED(self.__Sub_Keys[self.__Position])
            
            
    def __Menu_Select(self):
        print("Pushed")
        
        if(not self.__Is_Displayed):
           self.__Is_Displayed = True
           self.__Position = 0
           self.UpdateOLED(self.__menu_list[0])
        else:
            self.__Selected_Item = self.__menu_list[self.__Position]
            self.__Sub_Keys = list(self.__Menu_Items[self.__Selected_Item].keys())
            print("Sub-keys of", self.__Selected_Item, ":", self.__Sub_Keys)
            self.__Position = 0 # Reset position for navigating sub-keys
            self.UpdateOLED(self.__Sub_Keys[self.__Position])
            self.__InSubMenu = True
            self.__MenuSize = self.GetSize(self.__Sub_Keys[self.__Position])

            
                
            
OLED.fill(0) # Clear the buffer
OLED.show()
  
RotaryEncoder_1 = RotaryEncoder(0,1)

Button_1 = PushButton(15)

Menu1 = Menu(RotaryEncoder_1, Button_1)


'''     
OLED.text("Welcome to ECE", 0, 0)
    
OLED.text("299", 45, 10)
    
OLED.text("Count is: %4d" % Count, 0, 30 )  
        
OLED.rect(0, 50, 128, 5, 1)        

OLED.show() # Transfer the buffer to the screen
'''