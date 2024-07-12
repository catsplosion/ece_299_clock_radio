#import rotary_encoder as re
#import push_button as pb
#from machine import Pin, SPI

#from ssd1306 import SSD1306_SPI 
#import framebuf 


class MenuHandler: #keeping track of what is currently selected, 
        
    def __init__(self, encoder, button):
        self.root = Functionality_MenuSelect(None, "root_node") #This creates an attribute local to the instance. Self is automatically passed?
        self._current = root
        
        button.set_button_press(self._buttonpressed) #Note sure if set_button_press is right
        
        encoder.set_ccw_fn(self._ccw_handler)
        
        encoder.set_cw_fn(self._cw_handler)
    
    def __del__(self):
        pass
        
    def render(self):
        pass
    
    def _ccw_handler(self):
        self.current.ccw()
        
    def _cw_handler(self):
        self.current.cw()

        
    def _buttonpressed(self): ## _ thigns outside the class cant touch it __, no subclasses touching it
        self.current.press(self)



class MenuItem:
    def __init__(self, parent, name):
        
        print("Created a node with name ", name, "Parent: ", parent)
        
        self.parent = parent #Attributes 
        self.name = name
        
        # self.selection = 0 # Keeps track of what node we are looking at in the children array.  (Not needed) 
        
        self.children = [] # Array of MenuItems        
    
    def add_child(self, node): #Append a MenuItem as a child to the current MenuItem
        self.Children.append(node)
        node.parent = self
        return node #so you can actually do stuff with it (ex new = node.add_child(...))
        
    def cw(self, handler): #all of this will be overloaded.
        pass
    
    def ccw(self):
        pass
    
    def press(self, handler):
        pass
    
    def back(self):
        pass
    
    def render(self):
        pass

class Functionality_MenuSelect(MenuItem): #MenuFunctionality1 is a subclass of MenuItem
    def __init__(self, parent, name):
        super().__init__(parent,name) #function super() makes it so that it initalizes all the methods in MenuItem (goofy python moment)
        self.index = 0

    
    def ccw(self, handler):
        if(self.index < len(handler.current.children)):
            self.index += 1
        else:
            self.index = 0
        
        print(children[index].name)
    
    def cw(self):
        if(self.index > 0):
            self.index -= 1 #Reminder: self. refrences the attribute to that object, if it was just Index = then thats a local var
        else:
            self.index = (len(current.children) - 1)
            
        print(children[index].name)
        
    def press(self, handler): ## _ thigns outside the class cant touch it __, no subclasses touching it
        
        hanlder._current = self.children[self.index]
        self.index = 0
    
    def back(self):
        pass
    
    def render(self):
        pass
