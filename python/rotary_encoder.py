from machine import Pin


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
        print("CW")
        if self._cw_fn:
            self._cw_fn(*self._cw_fn_args)

    def _call_ccw_fn(self):
        print("CCW")
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
        
RotaryEncoder(14,15,2)