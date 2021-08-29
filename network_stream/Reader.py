from abc import ABC
import socket
import struct
from Buffer import BufferWithLen as Message

class ReaderState:
    pass

class MoreDataRequired(ReaderState):
    def __init__(self):
        self.reqd = None
    

class ConnectionBroken(ReaderState):
    def __init__(self):
        pass

class PrimePacket(ReaderState):
    def __init__(self):
        pass

class OutOfSync(ReaderState):
    def __init__(self):
        pass


class Reader(ABC):

    def __init__(self,conn):
        self.conn = conn

    def read(self):
        raise NotImplemented

class ReaderWithLen(Reader):

    def __init__(self,conn):
        self.conn = conn
        self.message = Message()
        self.header_len = 4
        self.next_is_header = True

    def gen_message(self):
        try:
            len_reqd = yield PrimePacket
            #print(f"priming with {len_reqd}")
            self.message.clear()
            self.message.total_len = len_reqd
            while True:
                chunk = self.conn.recv(len_reqd)
                if chunk == b'':
                    return ConnectionBroken
                else:
                    self.message.set_message(chunk)
                if self.message.is_ready:
                    #print(f"whole message {self.message.buffer}")
                    len_reqd = yield self.message.buffer
                    self.message.clear()
                    #print(f"getting {len_reqd}")
                    self.message.total_len = len_reqd
                else:

                    mdr = MoreDataRequired()
                    mdr.reqd = self.message.total_len - self.message.cur_len
                    yield mdr

        except socket.error as error:
            last_err = error.errno
            print(f"got socket {last_err}",end=" ")
            print(f"{error.strerror}")
            return ConnectionBroken

        except Exception as E:
            print(f"exception as {E}")
            yield self.message.buffer

    def prime_msg_gen(self):
        self.packet_len_gen = self.gen_message()
        next(self.packet_len_gen)

    def get_next_header(self):
        try:
            if self.next_is_header:
                reqd = self.header_len
                while True:
                    packet_len = self.packet_len_gen.send(reqd)
                    if isinstance(packet_len,MoreDataRequired):
                        ## need to poll it somehow 
                        ## 1. call next but we do not provide next len
                        ## 2. MoreDataRequired tracking next message len give that
                        ##    a. change reqd 
                        reqd -= packet_len.reqd
                        if reqd < 0:
                            print("header of of sync")
                            return OutOfSync()
                    elif isinstance(packet_len,PrimePacket):
                        ## again poll it
                        ## ideally no need to handle
                        raise ValueError("invalid packet")
                    elif isinstance(packet_len,ConnectionBroken):
                        return packet_len
                    elif isinstance(packet_len,bytearray):
                        ## now we have our message
                        packet_len = struct.unpack('i',packet_len)[0]
                        #print(packet_len)
                        self.next_is_header = False
                        return packet_len
                    else:
                        return packet_len
        except Exception as E:
            print(f"exception in header {E}")
            con_break = ConnectionBroken()
            return con_break

    def message_generator(self):
        try:
            self.prime_msg_gen()
            reqd = None
            while True:
                if self.next_is_header:
                    nxt_hdr_len = self.get_next_header()
                    #print(f"next header {type(nxt_hdr_len)}")
                    if isinstance(nxt_hdr_len,ConnectionBroken):
                        self.packet_len_gen.close()
                        yield nxt_hdr_len
                    elif isinstance(nxt_hdr_len,int):
                        reqd = nxt_hdr_len
                message = self.packet_len_gen.send(reqd)
                if isinstance(message,MoreDataRequired):
                    if reqd:
                        ##TODO: figure out why reduce message size
                        ##here as well slow client is getting out of
                        ##sync
                        reqd -= message.reqd
                        print(f"value of reqd is {reqd}")
                        if reqd < 0:
                            print("message out of sync")
                            return OutOfSync()
                        yield message
                    else:
                        print(f"message is {message}")
                elif isinstance(message,PrimePacket):
                    raise ValueError("invalid packet")
                elif isinstance(message,ConnectionBroken):
                    yield message
                else:
                    self.next_is_header = True
                    yield message

        except Exception as e:
            print(f"exception in mgen {e}")
            return ConnectionBroken()
