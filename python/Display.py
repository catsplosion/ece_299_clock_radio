from machine import Pin, SPI 
from ssd1306V2 import SSD1306_SPI 
import framebuf 

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
        
    
