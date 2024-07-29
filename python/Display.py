from machine import Pin, SPI
from ssd1306 import SSD1306_SPI
import framebuf


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


class Oled:
    def __init__(self, sck, sda, res, dc ,cs, line=0, baudrate=100000, width=128, height=64):

        self.sck = Pin(sck) #Initalize as pin objects!
        self.sda = Pin(sda)
        self.res = Pin(res)
        self.dc = Pin(dc)
        self.cs = Pin(cs)
        self.line = line
        self.baudrate = baudrate
        self.width = width
        self.height = height

        self.oled_spi = SPI(self.line, self.baudrate, sck=self.sck, mosi=self.sda)

        self.oled = SSD1306_SPI(self.width, self.height, self.oled_spi, self.dc, self.res, self.cs, True)

        self.oled.fill(0)

        self._number_buf = [None]*10
        for i in range(10):
            self._number_buf[i] = framebuf.FrameBuffer(NUMBER_BITS[i], 8, 14, framebuf.MONO_HLSB)

    def tall_digit(self, digit, x, y):
        self.oled.blit(self._number_buf[digit], x, y)