import time

from machine import ADC
from machine import I2C
from machine import Pin
from machine import PWM
from machine import RTC
from machine import Timer

import rda5807

# Month number to name mapping.
MONTHS = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec"
}

# Month number to number of days mapping.
MONTHDAYS = {
    1: 31,
    2: 28,
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31
}

# Frequency patterns for the alarm. Frequncy in Hz. 0 turns off the tone and -1
# continues the current tone without change. Each value is played for 1/4 of a
# second.
ALARM_PATTERN = [
    [620, 0, 620, 0, 620, 0, -1, -1, -1, -1],
    [370, -1, 523, -1],
    [880, -1, -1, -1, 0, 0, 0, 0]
]

# Mode values for the alarm.
_ALARM_OFF = 0
_ALARM_ON = 1
_ALARM_SOUND = 2
_ALARM_SNOOZE = 3
_ALARM_TEST = 4

# Mode values for the clock format.
_CLOCK_12HR = 0
_CLOCK_24HR = 1


def is_leap_year(year):
    """
    Determines if the provided year is a leap year. Returns True or False.
    """
    return not year % 4 or not year % 100 or not year % 400


class ClockState():
    """
    Holder for all the state information regarding the clock radio.
    """
    def __init__(self):
        # Clock related attributes.
        self.rtc = RTC()
        self.rtc.datetime((2024, 1, 1, 0, 0, 0, 0, 0))
        self.clock_mode = _CLOCK_12HR
        self.tz_offset = 0

        # Alarm related attributes.
        self.alarm_state = _ALARM_OFF
        self.alarm_enabled = False
        self.alarm_time = (0, 0, 0)
        self.alarm_volume = 2
        self.alarm_pattern = 0
        self.alarm_stime = (0, 0, 0)
        self.alarm_sdelay = 5
        self._alarm_sounding = False

        # PWM related attributes.
        self._pwm_tick = 0
        self._pwm_lohi = False
        self._pwm = PWM(22)
        Pin(22, Pin.IN)
        self._pwm_pattern = Timer()
        self._pwm_freq = Timer()

        # Radio related attributes.
        self.radio = rda5807.Radio(I2C(1, scl=7, sda=6, freq=100000))
        self.radio_enabled = False
        self.radio_muted = True
        self.radio_freq = 100.3
        self.radio_volume = 2

        # Initialize the radio modile as muted.
        self.mute_radio()

        # Station frequency to name mapping.
        self.stations = {
            98.5 : "CIOC",
            100.3 : "CKKQ",
            91.3 : "CJZN",
            103.1 : "CHTT",
            107.3 : "CHBE",
            90.5 : "CBCV",
            107.9 : "CILS",
            1070 : "CFAX",
            101.9 : "CFUV"
        }

        # LED related attributes.
        self.led_states = {
            "Set Colour" : False,
            "FFT" : False,
            "OFF" : False # On = True Off = False
        }
        self.led_color = [0, 0, 0]

        # Temperature related attributes.
        self.temp_adc = ADC(ADC.CORE_TEMP)
        self.temp_timer = Timer(mode=Timer.PERIODIC, period=10000, callback=self._poll_temp)
        self.temp = 99

        self._poll_temp(self.temp_timer)

    def update(self):
        """
        Update the state of the clock based on the current RTC time.
        """
        # Check the alarm time only when the alarm is enabled.
        if self.alarm_state == _ALARM_ON:
            if self.get_time() == self.alarm_time:
                self.alarm_state = _ALARM_SOUND
                self._sound_alarm()

        # Handle the alarm snooze mode.
        elif self.alarm_state == _ALARM_SNOOZE:
            now = self.get_time()
            seconds = (now[1] - self.alarm_stime[1])*60
            seconds += now[2] - self.alarm_stime[2]
            if seconds >= self.alarm_sdelay:
                self.alarm_state = _ALARM_SOUND
                self._sound_alarm()

    def _sound_alarm(self):
        """
        Start the PWM system to play current alarm patern.
        """

        # Set the audio out pins on the RDA5807 to high impedance mode.
        self.radio.update_reg(
            rda5807.RDA5807M_REG_CONFIG, rda5807.RDA5807M_FLG_DHIZ, 0)

        # Init the PWM with 300kHz carrier frquency.
        self._pwm = PWM(22)
        self._pwm.freq(300000)
        self._pwm.duty_u16(0)

        # Reset the square wave generator callback timer.
        self._pwm_freq.deinit()

        # Start the pattern ticker.
        self._pwm_tick = 0
        self._pwm_pattern.init(
            mode=Timer.PERIODIC,
            freq=4,
            callback=self._pwm_pattern_handler
        )

        self._alarm_sounding = True

    def _unsound_alarm(self):
        """
        Shut off the PWM system to stop playing the alarm.
        """
        self._pwm_pattern.deinit()
        self._pwm_freq.deinit()
        self._pwm.deinit()
        Pin(22, Pin.IN)

        # Put the audio out pins on the RDA5807 back into normal mode.
        self.radio.update_reg(
            rda5807.RDA5807M_REG_CONFIG, rda5807.RDA5807M_FLG_DHIZ,
            rda5807.RDA5807M_FLG_DHIZ
        )

        self._alarm_sounding = False

    def _pwm_set_freq(self, freq):
        """
        Set the square wave geneator to create the given frequency, or shut it
        off.
        """
        if freq < 0:
            return
        elif freq == 0:
            self._pwm_freq.deinit()
            self._pwm.duty_u16(0)
        else:
            self._pwm_freq.init(
                mode=Timer.PERIODIC,
                freq=freq*2,
                callback=self._pwm_freq_handler
            )

    def _pwm_pattern_handler(self, timer):
        """
        Callback to tick through the current alarm pattern.
        """
        pattern = ALARM_PATTERN[self.alarm_pattern % len(ALARM_PATTERN)]
        freq = pattern[self._pwm_tick % len(pattern)]
        self._pwm_set_freq(freq)

        self._pwm_tick += 1

    def _pwm_freq_handler(self, timer):
        """
        Tone generator callback for the PWM system.
        """
        if self._pwm_lohi:
            pwm_volume = int(self.alarm_volume * 65535 / 16)
            self._pwm.duty_u16(pwm_volume)
        else:
            self._pwm.duty_u16(0)

        self._pwm_lohi = not self._pwm_lohi

    def datetimezoned(self, datetime=None):
        """
        Given a datetime tuple (or using the current RTC time) apply the
        current timezone offset and adjust the date appropriately. Returns an
        adjusted datetime tuple:
            (year, month, day, _, hour, minute, second, _)
        """
        datetime = datetime or self.rtc.datetime()
        year, month, day, wk, hour, minute, sec, ms = datetime

        hour += self.tz_offset

        # Adjust the date values one by one, least to most significant.
        if hour < 0:
            day -= 1
        elif hour >= 24:
            day += 1

        if day <= 0:
            month -= 1
        elif day > MONTHDAYS[month] + int(is_leap_year(year) and month == 2):
            month += 1

        if month <= 0:
            year -= 1
        elif month > 12:
            year += 1

        # Bound the resulting values to their respective ranges.
        month = max(min(month, 12), 1)
        is_leap = is_leap_year(year)
        monthdays = MONTHDAYS[month] + int(is_leap and month == 2)

        day = max(min(day, monthdays), 1)
        hour = hour % 24

        return year, month, day, wk, hour, minute, sec, ms

    def set_time(self, time):
        """
        Set the current clock time. Hour is from 0 to 23.
        time(tuple): (hour, minute, second)
        """
        now = list(self.rtc.datetime())
        now = now[:4] + list(time) + now[7:]
        self.rtc.datetime(now)

    def get_time(self):
        """
        Return the current time as a tuple in the form (hour, min, sec).
        """
        return self.rtc.datetime()[4:7]

    def set_date(self, date):
        """
        Set the current clock date.
        time(tuple): (year, month, day)
        """
        now = list(self.rtc.datetime())
        now = list(date) + now[3:]
        self.rtc.datetime(now)

    def get_date(self):
        """
        Return the current date as a tuple in the form (year, month, day).
        """
        return self.rtc.datetime()[0:3]

    def set_clock_mode(self, mode):
        """
        Set the clock's display mode.
        mode(str): Clock display mode: "12hr" or "24hr".
        """
        self.clock_mode = _CLOCK_24HR if mode == "24hr" else _CLOCK_12HR

    def get_clock_mode_string(self):
        """
        Return the name of the current clock mode as a string.
        """
        mstring = "12hr" if self.clock_mode == _CLOCK_12HR else "24hr"
        return mstring

    def get_tz_offset(self):
        """
        Return the current timezone offset.
        """
        return self.tz_offset

    def set_tz_offset(self, offset):
        """
        Set the clock's timezone offset.
        offset(int): Offset value -12 to 14.
        """
        self.tz_offset = max(min(offset, 14), -12)

    def format_clock_string(self, datetime):
        """
        Generates a clock display string based on the given datetime tuple
        and the current time format mode.
        datetime(tuple): See RTC.datetime() for tuple values.

        Returns: (time string (str), date string (str))
        """
        year, month, day, _, hour, minute, sec, _ = datetime
        tstring = "?:?:?"
        if self.clock_mode == _CLOCK_12HR:
            mod = "am" if hour < 12 else "pm"
            hour = (hour - 1) % 12 + 1
            tstring = "{:2d}:{:02d}:{:02d} {}".format(hour, minute, sec, mod)
        elif self.clock_mode == _CLOCK_24HR:
            tstring = "{:02d}:{:02d}:{:02d}".format(hour, minute, sec)

        dstring = "{}/{:02d}/{:04d}".format(MONTHS[month], day, year)

        return tstring, dstring

    def get_clock_string(self):
        """
        Return the clock values as a 2-tuple of strings.

        Returns:
            (time, date)
        """
        return self.format_clock_string(self.datetimezoned())

    def set_alarm(self, time=None, volume=None, pattern=None, snooze=None):
        """
        Set the alarm. Arguents set to None will not be modified.
        time(tuple): (hour, min, sec)
        volume(int): 1 to 15 volume, 15 being loudest
        pattern(int): Alarm pattern to play.
        snooze(int): Snooze time in minutes.
        """
        self.alarm_time = time or self.alarm_time
        self.alarm_volume = volume or self.alarm_volume
        self.alarm_pattern = pattern or self.alarm_pattern
        self.alarm_sdelay = snooze or self.alarm_sdelay

        self.alarm_time = (
            self.alarm_time[0] % 24,
            self.alarm_time[1] % 60,
            self.alarm_time[2] % 60
        )

        self.alarm_volume = max(min(16, self.alarm_volume), 1)
        self.alarm_sdelay = max(min(self.alarm_sdelay, 60), 1)

    def set_alarm_volume(self, volume):
        """
        Set the alarm volume.
        volume(int) 1-16.
        """
        self.set_alarm(volume=volume)

    def get_alarm_volume(self):
        """
        Returns the current alarm volume.
        """
        return self.alarm_volume

    def set_alarm_pattern(self, pattern):
        """
        Set the alarm pattern to use.
        pattern(int): Position of the pattern in the ALARM_PATTERN list.
        """
        self.alarm_pattern = pattern % len(ALARM_PATTERN)

    def get_alarm_pattern(self):
        """
        Return the current alarm pattern.
        """
        return self.alarm_pattern

    def set_snooze_delay(self, snooze):
        """
        Set the snooze delay amount.
        snooze(int): Delay time in seconds.
        """
        self.set_alarm(snooze=snooze)

    def get_snooze_delay(self):
        """
        Return the current snooze delay amount.
        """
        return self.alarm_sdelay

    def get_alarm_string(self):
        """
        Return the current alarm value.

        Returns:
            (hour, min, sec)
        """
        hour, minute, sec = self.alarm_time

        hour = (hour + self.tz_offset) % 24

        astring = "?:?:?"
        if self.clock_mode == _CLOCK_12HR:
            mod = "am" if hour < 12 else "pm"
            hour = (hour - 1) % 12 + 1
            astring = "{: 2d}:{:02d}:{:02d} {}".format(hour, minute, sec, mod)
        elif self.clock_mode == _CLOCK_24HR:
            astring = "{:02d}:{:02d}:{:02d}".format(hour, minute, sec)

        return astring

    def enable_alarm(self):
        """
        Enable the alarm for the current alarm settings.
        """
        self.alarm_state = _ALARM_ON
        self.alarm_enabled = True

    def disable_alarm(self):
        """
        Disable and shut off the alarm.
        """
        self.alarm_state = _ALARM_OFF
        self._unsound_alarm()
        self.alarm_enabled = False

    def shutoff_alarm(self):
        """
        Turn off the alarm sound, but leave the alarm on so it will trigger
        the next day.
        """
        if self.alarm_state != _ALARM_OFF:
            self.alarm_state = _ALARM_ON
            self._unsound_alarm()

    def snooze_alarm(self):
        """
        Snooze the current alarm.
        """
        if self.alarm_state != _ALARM_SOUND:
            return

        self.alarm_stime = self.get_time()
        self._unsound_alarm()
        self.alarm_state = _ALARM_SNOOZE

    def alarm_sounding(self):
        """
        Return if the alarm is currently sounding.
        """
        return self._alarm_sounding

    def set_radio(self, freq=None, volume=None):
        """
        Set the current radio state. Any argument set to None will not be
        modified.

        freq(float): Station frequency in MHz.
        volume(int): Volume of the radio. 0 is lowest, 15 is highest.
        """
        if freq:
            freq = round(freq * 10) / 10
            freq = max(min(freq, 108.1), 88.1)

            self.radio_freq = freq
            self.radio.set_frequency_MHz(freq)

        if volume is not None:
            self.radio_volume = max(min(volume, 15), 0)
            self.radio.set_volume(self.radio_volume)

    def set_radio_volume(self, volume):
        """
        Set the radio volume.
        volume(int): 0 to 15.
        """
        self.set_radio(volume=volume)

    def get_radio_volume(self):
        """
        Get the current radio volume value.
        """
        return self.radio_volume

    def seek_up(self):
        """
        Seek the radio up. Does not return until a new channel was found or the
        frequency looped all the way back.
        """
        self.radio.seek_up()
        self.radio_freq = self.radio.get_frequency_MHz()

    def seek_down(self):
        """
        Seek the radio down. Does not return until a new channel was found or
        the frequency looped all the way back.
        """
        self.radio.seek_down()
        self.radio_freq = self.radio.get_frequency_MHz()

    def mute_radio(self):
        """
        Mute the radio module.
        """
        self.radio.mute(True)
        self.radio_muted = True

    def unmute_radio(self):
        """
        Unmute the radio module.
        """
        self.radio.mute(not self.radio_enabled)
        self.radio_muted = False

    def enable_radio(self):
        """
        Initialize and turn on the radio.
        """
        self.radio.bass_boost(False)
        self.radio.mono(True)
        self.radio.set_frequency_MHz(self.radio_freq)
        self.radio.set_volume(self.radio_volume)
        self.radio_enabled = True
        self.unmute_radio()

    def disable_radio(self):
        """
        Turn off the radio.
        """
        self.radio_enabled = False
        self.mute_radio()

    def set_led_color(self, color):
        """
        Set the color of the LEDs.
        color(tuple): Three-tuple of the components. (r, g, b)
        """
        self.led_color = (
            max(min(color[0], 255), 0),
            max(min(color[1], 255), 0),
            max(min(color[2], 255), 0)
        )

    def _poll_temp(self, timer):
        """
        Timer callback to poll the current temperature ADC and convert it into
        a degree value.
        """
        temp = self.temp_adc.read_u16()
        self.temp = 27 - (temp * 3.3 / 65535 - 0.706) / 0.001721

    def get_temp_string(self):
        """
        Generatue and return a temperature string of the current temperature
        value.
        """
        return "{:2d}C".format(max(min(int(self.temp), 99), -9))
