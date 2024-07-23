from machine import Pin, Timer


_HOLD_UP = 0
_FALLING = 1
_HOLD_DOWN = 2
_RISING = 3

_DELAY_PERIOD = 4
_DELAY_THRESHOLD = 4


class PushButton(object):
    """
    Configure a machine.Pin as a push button input. Handles de-bouncing using a
    consistency check. The check is called every _DELAY_PERIOD ms and if it
    finds the expected HI or LO value _DELAY_THRESHOLD times in a row, a rising
    or falling event is triggered. Calls a given press function at the end of
    the button press-release cycle. The `pull_up` parameter determines whether
    the press function is called on rising edge (True) or falling edge (False).

    pin(any): Id of the button pin. See id arg of machine.Pin.__init__.
    pull_up(bool): Set pin in pull-up mode if True, otherwise pull-down mode.
    """
    def __init__(self, pin, pull_up=True):
        self._pull = Pin.PULL_UP if pull_up else Pin.PULL_DOWN
        self._state = _HOLD_UP if pull_up else _HOLD_DOWN

        self._irq_enable = False
        self._timer_enabled = False

        self._pin = Pin(pin, Pin.IN, self._pull)
        self._enable_irq()

        self._timer = Timer()

        self._stable_count = 0

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
            self._stable_count = 0
            self._disable_irq()
            self._start_timer()
        elif self._state == _HOLD_DOWN and rising:
            self._state = _RISING
            self._stable_count = 0
            self._disable_irq()
            self._start_timer()

    def _timer_handler(self, timer):
        pvalue = self._pin.value()

        if self._state == _FALLING and pvalue or self._state == _RISING and not pvalue:
            self._stop_timer()
            self._state = _HOLD_UP if self._state == _FALLING else _HOLD_DOWN
            self._enable_irq()
            return

        if self._stable_count < _DELAY_THRESHOLD:
            self._stable_count += 1
            return

        self._stop_timer()

        if self._state == _FALLING:
            self._call_fall_fn()
            self._state = _HOLD_DOWN
        elif self._state == _RISING:
            self._call_rise_fn()
            self._state = _HOLD_UP

        self._enable_irq()

    def _enable_irq(self):
        self._pin.irq(self._irq_handler, Pin.IRQ_FALLING | Pin.IRQ_RISING)
        self._irq_enabled = True

    def _disable_irq(self):
        self._pin.irq(handler=None)
        self._irq_enabled = False

    def _start_timer(self):
        self._timer.init(
            mode=Timer.PERIODIC,
            period=_DELAY_PERIOD,
            callback=self._timer_handler
        )
        self._timer_enabled = True

    def _stop_timer(self):
        self._timer.deinit()
        self._timer_enabled = False

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

