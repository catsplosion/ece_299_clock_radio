#import rotary_encoder as re
#import push_button as pb
#from machine import Pin, SPI

class MenuHandler: #keeping track of what is currently selected, 
        
    def __init__(self, encoder, accept_button, back_button, state):
        self.root = Functionality_MenuSelect(None, "root_node") #This creates an attribute local to the instance. Self is automatically passed?
        self._current = self.root
        
        button.set_button_press(self._buttonpressed) #Note sure if set_button_press is right
        
        encoder.set_ccw_fn(self._ccw_handler)
        
        encoder.set_cw_fn(self._cw_handler)
        
        accept_button.set_press_fn(self._acceptpressed)
        
        back_button.set_press_fn(self._backpressed)
    
    def __del__(self):
        pass
        
    def render(self):
        #draw square or something (constant)
        self.current.render(self)
    
    def _ccw_handler(self):
        self.current.ccw()
        
    def _cw_handler(self):
        self.current.cw()
        
    def _acceptpressed(self): ## _ thigns outside the class cant touch it __, no subclasses touching it
        self.current.press()
    
    def _backpressed(self):
        self.current.back()



class MenuItem:
    def __init__(self, parent, name, state, handler=None):
        
        print("Created a node with name ", name, "Parent: ", parent)
        
        self.parent = parent #Attributes 
        self.name = name
        self.handler = handler
        self.state = state
        
        if handler is None:
            self.handler = parent
        
        # self.selection = 0 # Keeps track of what node we are looking at in the children array.  (Not needed) 
        
        self.children = [] # Array of MenuItems        
    
    def add_child(self, node): #Append a MenuItem as a child to the current MenuItem
        self.Children.append(node)
        node.parent = self
        return node #so you can actually do stuff with it (ex new = node.add_child(...))
        
    def cw(self): #all of this will be overloaded.
        pass
    
    def ccw(self):
        pass
    
    def press(self):
        pass
    
    def back(self):
        pass
    
    def render(self):
        #special stuff
        pass
    
class Functionality_ChangeRGB(MenuItem):
    def __init__(self, parent, name, state, handler):
        super().__init__(parent, name, state, handler)
        
        self.selections = ['r', 'g', 'b']
        self.index = 0
    
    def ccw(self):
        if(clockstate.selections[index] <= 0):
            clockstate.selections[index] = 255
        else:
            clockstate.selections[index] -= 1
    
    def cw(self):
        if(clockstate.selections[index] >= 255):
            clockstate.selections[index] = 0
        else:
            clockstate.selections[index] += 1
    
    
    def press(self):
        if(index == 2):
            index = 0
        else:
            index += 1
    
    def back(self):
        handler.current = self.parent
    
class Functionality_ChangeTimeFormat(MenuItem):
    def __init__(self, parent, name, state, handler):
        super().__init__(parent, name, state, handler)
    
    def ccw(self):
        clockstate.clock_12hr = False
    
    def cw(self):
        clockstate.clock_12hr = True
        self.index = 0
    def press(self):
        pass
    
    def back(self):
        handler.current = self.parent


class Functionality_FrequencyChange(MenuItem): 
    
    def __init__(self, parent, name, state, handler):
        super().__init__(parent, name, state, handler)
        
        self.selections = [10, 0.2]
        self.index = 0
    
    def ccw(self):
        clockstate.frequency -= selections[index]
    
    def cw(self):
        clockstate.frequency += selections[index]
    
    def press(self):
        index = 0 if index else 1
    
    def back(self):
        handler.current = self.parent

class Functionality_AlarmTime(MenuItem):
    def __init__(self, parent, name, state, handler):
        super().__init__(parent, name, state, handler)
        
        self.selections = ["hour", "minute"]
        self.index = 0
    
    def ccw(self):
        clockstate.selections[index] -= 1
    
    def cw(self):
        clockstate.selections[index] += 1
    
    def press(self):
        index = 0 if index else 1
    
    def back(self):
        handler.current = self.parent

class Functionality_MenuSelect(MenuItem): #Draw '<' "Item" '>'
    
    def __init__(self, parent, name, state, handler):
        super().__init__(parent, name, state, handler) #function super() makes it so that it initalizes all the methods in MenuItem (goofy python moment)
        
        self.index = 0
    
    def ccw(self, handler):
        if(self.index < len(handler.current.children)):
            self.index += 1
        else:
            self.index = 0
        
        self.hanlder.render()
        
        print(children[index].name)
    
    def cw(self):
        if(self.index > 0):
            self.index -= 1 #Reminder: self. refrences the attribute to that object, if it was just Index = then thats a local var
        else:
            self.index = (len(current.children) - 1)
            
        self.hanlder.render()
            
        print(children[index].name)
        
    def press(self): ## _ thigns outside the class cant touch it __, no subclasses touching it
        
        hanlder._current = self.children[self.index]
        self.index = 0
        
        self.hanlder.render()

    
    def back(self):
        handler._current = self.parent
        
        self.hanlder.render()

    
    def render(self):
        pass
    


