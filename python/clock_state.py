from machine import I2C
from machine import RTC
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


class ClockState():
    def __init__(self):
        self.rtc = RTC()
        self.rtc.datetime((2024, 1, 1, 0, 0, 0, 0))
        self.clock_mode = "12hr"

        self.alarm_enabled = False
        self.alarm_on = False
        self.alarm_time = (0, 0, 0)
        self.alarm_last = (0, 0, 0)
        self.alarm_volume = 4
        self.alarm_pattern = 0
        self.alarm_snooze = 5

        self.radio = Radio(I2C(1, scl=7, sda=6, freq=100000))
        self.radio_enabled = False
        self.radio_muted = True
        
        self.mute_radio(True)
        self.radio.set_frequency_MHz(100.3)
        self.radio.bass_boost(False)
        self.radio.mono(True)
        self.radio.set_volume(4)

    def set_clock(self, time, mode):
        """
        Set the current clock value.
        time(tuple): (hour, minute, second)
        mode(str): "12hr" or "24hr" mode.
        """
        now = list(self.rtc.datetime())
        now[3:6] = time
        self.rtc.datetime(now)
        self.clock_mode = mode

    def get_clock_string(self):
        """
        Return the clock values as a 3-tuple of strings.

        Returns:
            (time, date, am/pm)
        """
        now = self.rtc.datetime()

        tstring = "?:?:?"
        if self.clock_mode == "12hr":
            hours = now[0] % 12 + 1
            tstring = "{: 2d}:{:02d}:{:02d}".format(hours, now[4:6])

        dstring = "{} {}, {}".format(MONTHS[now[1]], now[2], now[0])
            
        astring = None
        if self.clock_mode == "12hr":
            astring = "am" if now[0] < 12 else "pm"
            
        return tstring, dstring, astring

    def set_alarm(self, time, volume=4, pattern=0, snooze=5):
        """
        Set the alarm.
        time(tuple): (hour, minute, second)
        volume(int): 1 to 15 volume, 15 being loudest
        pattern(int): Alarm pattern to play.
        snooze(int): Snooze time in minutes.
        """
        self.alarm_time = time
        self.alarm_volume = volume
        self.alarm_last = (0, 0, 0)
        self.alarm_pattern = pattern
        self.alarm_snooze = snooze

    def enable_alarm(self):
        """
        Enable the alarm for the current alarm settings.
        """
        self.alarm_enabled = True
        self.alarm_on = False

    def disable_alarm(self):
        """
        Disable and shut off the alarm.
        """
        self.alarm_enabled = False
        self.alarm_on = False

    def snooze_alarm(self):
        """
        Snooze the current alarm.
        """
        self.alarm_on = False
        self.alarm_last = self.rtc.datetime()[3:6]

    def mute_radio(self, mute=True):
        """
        Mute or unmute the radio module.
        mute(bool): Whether to mute or unmute.
        """
        self.radio.mute(mute)
        regval = 0 if mute else RDA5807M_FLG_DHIZ
        self.radio.update_reg(RDA5807M_REG_CONFIG, RDA5807M_FLG_DHIZ, regval)
        self.radio_muted = mute

    def enable_radio(self):
        """
        Turn on the radio.
        """
        self.radio_enabled = True
        self.mute_radio(False)
    
    def disable_radio(self):
        "Turn off the raido."
        self.radio_enabled = False
        self.mute_radio(True)