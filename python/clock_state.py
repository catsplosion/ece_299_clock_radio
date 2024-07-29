import time

from machine import ADC
from machine import I2C
from machine import PWM
from machine import RTC
from machine import Timer

import rda5807


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

_ALARM_OFF = 0
_ALARM_ON = 1
_ALARM_SOUND = 2
_ALARM_SNOOZE = 3

_CLOCK_12HR = 0
_CLOCK_24HR = 1


def is_leap_year(year):
    return not (year % 4 or year % 100 or year % 400)


class ClockState():

    def __init__(self):
        self.rtc = RTC()
        self.rtc.datetime((2024, 1, 1, 0, 0, 0, 0, 0))
        self.clock_mode = _CLOCK_12HR
        self.tz_offset = 0

        self.alarm_state = _ALARM_OFF
        self.alarm_time = (0, 0, 0)
        self.alarm_volume = 2
        self.alarm_pattern = 0
        self.alarm_stime = (0, 0, 0)
        self.alarm_sdelay = 5

        self._pwm_tick = 0
        self._pwm_lohi = False
        self._pwm = PWM(22)
        self._pwm.deinit()
        self._pwm_pattern = Timer()
        self._pwm_freq = Timer()

        self.radio = rda5807.Radio(I2C(1, scl=7, sda=6, freq=100000))
        self.radio_enabled = False
        self.radio_muted = True
        self.radio_freq = 100.3
        self.radio_volume = 2

        self.mute_radio()

        self.led_color = (0, 0, 0)

        self.temp_adc = ADC(ADC.CORE_TEMP)
        self.temp_timer = Timer(mode=Timer.PERIODIC, period=10000, callback=self._poll_temp)
        self.temp = 99

        self._poll_temp(self.temp_timer)

    def update(self):
        """
        Update the state of the clock based on the current RTC time.
        """
        if self.alarm_state == _ALARM_ON:
            if self.get_time() == self.alarm_time:
                self.alarm_state = _ALARM_SOUND
                self._sound_alarm()

        elif self.alarm_state == _ALARM_SNOOZE:
            now = self.get_time()
            seconds = (now[1] - self.alarm_stime[1])*60
            seconds += now[2] - self.alarm_stime[2]
            if seconds >= self.alarm_sdelay:
                self.alarm_state = _ALARM_SOUND
                self._sound_alarm()

    def _sound_alarm(self):
        self._pwm.freq(300000)
        self._pwm.duty_u16(0)

        self._pwm_tick = 0
        self._pwm_pattern.init(
            mode=Timer.PERIODIC,
            freq=2,
            callback=self._pwm_pattern_handler
        )

        self.radio.update_reg(
            rda5807.RDA5807M_REG_CONFIG, rda5807.RDA5807M_FLG_DHIZ, 0)

    def _unsound_alarm(self):
        self.radio.update_reg(
            rda5807.RDA5807M_REG_CONFIG, rda5807.RDA5807M_FLG_DHIZ,
            rda5807.RDA5807M_FLG_DHIZ
        )

        self._pwm_pattern.deinit()
        self._pwm_freq.deinit()
        self._pwm.deinit()

    def _pwm_set_freq(self, freq):
        self._pwm_freq.init(
            mode=Timer.PERIODIC,
            freq=freq*2,
            callback=self._pwm_freq_handler
        )

    def _pwm_pattern_handler(self, timer):
        if self.alarm_state != _ALARM_SOUND:
            self._unsound_alarm()

        if self._pwm_tick % 2 == 0:
            self._pwm_set_freq(370)
        else:
            self._pwm_set_freq(523)

        self._pwm_tick += 1

    def _pwm_freq_handler(self, timer):
        if self._pwm_lohi:
            pwm_volume = int(self.alarm_volume * 64000 / 15)
            self._pwm.duty_u16(pwm_volume)
        else:
            self._pwm.duty_u16(0)

        self._pwm_lohi = not self._pwm_lohi

    def datetimezoned(self):
        year, month, day, _, hour, minute, sec, _ = self.rtc.datetime()

        hour += self.tz_offset

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

        month = (month - 1) % 12 + 1
        day = (day - 1) % MONTHDAYS[month] + int(is_leap_year(year) and month == 2) + 1
        hour = hour % 24

        return year, month, day, hour, minute, sec

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
        return self.tz_offset

    def set_tz_offset(self, offset):
        self.tz_offset = max(min(offset, 14), -12)

    def get_clock_string(self):
        """
        Return the clock values as a 2-tuple of strings.

        Returns:
            (time, date)
        """
        year, month, day, hour, minute, sec = self.datetimezoned()

        tstring = "?:?:?"
        if self.clock_mode == _CLOCK_12HR:
            mod = "am" if hour < 11 else "pm"
            hour = (hour - 1) % 12 + 1
            tstring = "{:2d}:{:02d}:{:02d} {}".format(hour, minute, sec, mod)
        elif self.clock_mode == _CLOCK_24HR:
            tstring = "{:02d}:{:02d}:{:02d}".format(hour, minute, sec)

        dstring = "{:2d}/{:02d}/{:04d}".format(month, day, year)

        return tstring, dstring

    def set_alarm(self, time=None, volume=None, pattern=None, snooze=None):
        """
        Set the alarm.
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

        self.alarm_volume = max(min(15, self.alarm_volume), 1)
        self.alarm_sdelay = max(min(self.alarm_sdelay, 60), 1)

    def set_alarm_volume(self, volume):
        self.set_alarm(volume=volume)

    def get_alarm_volume(self):
        return self.alarm_volume

    def set_snooze_delay(self, snooze):
        self.set_alarm(snooze=snooze)

    def get_snooze_delay(self):
        return self.alarm_sdelay

    def get_alarm_string(self):
        """
        Return the current alarm value.

        Returns:
            (hour, min, sec)
        """
        hour, minute, sec = self.alarm_time

        hour = (hour + self.tz_offset) % 12

        astring = "?:?:?"
        if self.clock_mode == _CLOCK_12HR:
            hour = (hour - 1) % 12 + 1
            mod = "am" if hour < 12 else "pm"
            astring = "{: 2d}:{:02d}:{:02d} {}".format(hour, minute, sec, mod)
        elif self.clock_mode == _CLOCK_24HR:
            astring = "{:02d}:{:02d}:{:02d}".format(hour, minute, sec)

        return astring

    def enable_alarm(self):
        """
        Enable the alarm for the current alarm settings.
        """
        self.alarm_state = _ALARM_ON

    def disable_alarm(self):
        """
        Disable and shut off the alarm.
        """
        self.alarm_state = _ALARM_OFF
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
        Return if the alarm is currently snoozed.
        """
        return self.alarm_state == _ALARM_SOUND

    def set_radio(self, freq=None, volume=None):
        """
        Set the current radio state.
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
        self.set_radio(volume=volume)

    def get_radio_volume(self):
        return self.radio_volume

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
        Turn on the radio.
        """
        self.radio.bass_boost(False)
        self.radio.mono(True)
        self.radio.set_frequency_MHz(self.radio_freq)
        self.radio.set_volume(self.radio_volume)
        self.radio_enabled = True
        self.unmute_radio()

    def disable_radio(self):
        "Turn off the radio."
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

    def enable_led(self):
        """
        """
        pass

    def disable_led(self):
        """
        """
        pass

    def _poll_temp(self, timer):
        temp = self.temp_adc.read_u16()
        self.temp = 27 - (temp * 3.3 / 65535 - 0.706) / 0.001721

    def get_temp_string(self):
        return "{:2d}C".format(max(min(int(self.temp), 99), -9))