from machine import Pin, SPI
from ssd1306 import SSD1306_SPI
import framebuf


# Hold the bit arrays for the tall digits. Bits ordered from top left to bottom
# right. Index 0 is digit 0, index 1 is digit 1, and so on.
NUMBER_BITS = [
    bytearray.fromhex("3c3c66666E6E7676666666663C3C"),
    bytearray.fromhex("1818181838381818181818187E7E"),
    bytearray.fromhex("3C3C666606060C0C303060607E7E"),
    bytearray.fromhex("3C3C666606063C3C060666663C3C"),
    bytearray.fromhex("06060E0E1E1E66667F7F06060606"),
    bytearray.fromhex("7E7E60607C7C0606060666663C3C"),
    bytearray.fromhex("3C3C666660607C7C666666663C3C"),
    bytearray.fromhex("7E7E66660E0E1818181818181818"),
    bytearray.fromhex("3C3C666666663C3C666666663C3C"),
    bytearray.fromhex("3C3C666666663E3E060666663C3C")
]

# Hold the bit arrays for each icon. Same bit order as the tall digits.
ICON_BITS = [
    bytearray.fromhex("18247E4242817E18"),
    bytearray.fromhex("1031F1F5F5F1F110"),
    bytearray.fromhex("1035F5F2F2F53510"),
    bytearray.fromhex("FE92543810101010")
]


class Oled:
    """
    Wrapper class for the SSD1306 display module driver.

    sck(int): The SPI CCK line.
    sda(int): The SPI SDA line.
    res(int): The RES line to the display module.
    dc(int): The DC line to the display module.
    cd(int): The CD line to the display module.
    line(int): PICO SPI line to use.
    baudrate(int): Base SPI clock rate to use.
    width(int): Pixel width of the display.
    height(int): Pixel height of the display.
    """
    def __init__(self, sck, sda, res, dc ,cs, line=0, baudrate=100000,
            width=128, height=64):
        # Store all the given arugments.
        self.sck = Pin(sck)
        self.sda = Pin(sda)
        self.res = Pin(res)
        self.dc = Pin(dc)
        self.cs = Pin(cs)
        self.line = line
        self.baudrate = baudrate
        self.width = width
        self.height = height

        # Intialize the display driver.
        self.oled_spi = SPI(
            self.line, self.baudrate, sck=self.sck, mosi=self.sda)
        self.oled = SSD1306_SPI(
            self.width, self.height, self.oled_spi, self.dc, self.res,
            self.cs, True
        )
        self.oled.fill(0)

        # Convert the digits and then icons into FrameBuffer objects.
        self._number_buf = [None]*10
        for i in range(10):
            self._number_buf[i] = framebuf.FrameBuffer(
                NUMBER_BITS[i], 8, 14, framebuf.MONO_HLSB)

        self._icon_buf = [None]*len(ICON_BITS)
        for i in range(len(ICON_BITS)):
            self._icon_buf[i] = framebuf.FrameBuffer(
                ICON_BITS[i], 8, 8, framebuf.MONO_HLSB)

    def tall_digit(self, digit, x, y):
        """
        Draw tall digit to the display with the top left corner at (x,y).
        """
        self.oled.blit(self._number_buf[digit], x, y)

    def bell(self, x, y):
        """
        Draw a bell icon to the display with the top left corner at (x,y).
        """
        self.oled.blit(self._icon_buf[0], x, y)

    def speaker_on(self, x, y):
        """
        Draw a speaker icon to the display with the top left corner at (x,y)
        """
        self.oled.blit(self._icon_buf[1], x, y)

    def speaker_mute(self, x, y):
        """
        Draw a muted speaker icon to the display with the top left corner at
        (x,y)
        """
        self.oled.blit(self._icon_buf[2], x, y)

    def radio(self, x, y):
        """
        Draw a radio signal icon to the display with the top left corner at
        (x,y)
        """
        self.oled.blit(self._icon_buf[3], x, y)