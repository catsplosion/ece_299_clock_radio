from machine import Pin, Timer


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
