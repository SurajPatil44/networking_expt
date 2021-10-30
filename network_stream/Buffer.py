from abc import ABC


## test : checking vim extension

class Buffer(ABC):
    def __init__(self):
        self.buffer = bytearray()
        self.is_ready = False

    def set_message(self,data):
        raise NotImplemented



class BufferWithLen(Buffer):
    def __init__(self):
        self.buffer = bytearray()
        self.is_ready = False
        self.cur_len = 0
        self._total_len = 0

    def clear(self):
        self.__init__()

    def set_message(self,data):
        self.buffer += data
        self.cur_len += len(data)
        #print(f"{self.cur_len} and {self.total_len}")
        if self.cur_len >= self.total_len:
            self.is_ready = True
            self.cur_len = 0
            if self.total_len == 0:
                self.is_ready = False
        else:
            self.is_ready = False

    @property
    def total_len(self):
        return self._total_len 

    @total_len.setter
    def total_len(self,ln):
        self._total_len = ln
    
