import socket
import struct
import time
import select
import sys
import traceback

CHUNK_SIZE = 1024 

class MoreDataRequired:
    def __init__(self,reqd):
        self.reqd = reqd

class ConnectionBroken:
    def __init__(self):
        pass

class PrimePacket:
    def __init__(self):
        pass

class Message:
    '''This is abstract class for message
    message could be following type
    full message
    partial message
    exception message
    '''
    def __init__(self):
        self.buffer = bytearray()
        self.is_full = False
        self.cur_len = 0
        self._total_len = 0

    def clear(self):
        self.__init__()

    def set_message(self,data):
        self.buffer += data
        self.cur_len += len(data)
        print(f"{self.cur_len} and {self.total_len}")
        if self.cur_len >= self.total_len:
            self.is_full = True
            self.cur_len = 0
            if self.total_len == 0:
                self.is_full = False
        else:
            self.is_full = False

    @property
    def total_len(self):
        return self._total_len 

    @total_len.setter
    def total_len(self,ln):
        self._total_len = ln
    
    #@property
    #def buffer(self):
     #   return self.buffer
        
class Client:

    def __init__(self,conn):
        self.conn = conn
        self.message = Message()
        self.header_len = 4
        self.next_is_header = True

    def gen_message(self):
        try:
            len_reqd = yield PrimePacket
            print(f"priming with {len_reqd}")
            self.message.clear()
            self.message.total_len = len_reqd
            while True:
                chunk = self.conn.recv(len_reqd)
                if chunk == b'':
                    yield ConnectionBroken
                self.message.set_message(chunk)
                if self.message.is_full:
                    print(f"whole message {self.message.buffer}")
                    len_reqd = yield self.message.buffer
                    self.message.clear()
                    print(f"getting {len_reqd}")
                    self.message.total_len = len_reqd
                else:
                    yield MoreDataRequired(self.message.total_len - self.message.cur_len)  

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
                    elif isinstance(packet_len,PrimePacket):
                        ## again poll it
                        ## ideally no need to handle
                        raise ValueError("invalid packet")
                    elif isinstance(packet_len,ConnectionBroken):
                        return packet_len
                    else:
                        ## now we have our message
                        packet_len = struct.unpack('i',packet_len)[0]
                        print(packet_len)
                        self.next_is_header = False
                        return packet_len
        except Exception as E:
            print(f"exception in header {E}")

    def message_generator(self):
        try:
            self.prime_msg_gen()
            while True:
                if self.next_is_header:
                    nxt_hdr_len = self.get_next_header()
                    if isinstance(nxt_hdr_len,ConnectionBroken):
                        yield nxt_hdr_len
                    elif isinstance(nxt_hdr_len,int):
                        reqd = nxt_hdr_len
                message = self.packet_len_gen.send(reqd)
                if isinstance(message,MoreDataRequired):
                    reqd -= message.reqd
                elif isinstance(message,PrimePacket):
                    raise ValueError("invalid packet")
                elif isinstance(message,ConnectionBroken):
                    yield message
                else:
                    self.next_is_header = True
                    yield message

        except Exception as e:
            print(f"exception in mgen {e}")

class StreamingServer:

    def __init__(self,sock):
        self.sock = sock
        self.connections = [sock]
        self.con_mgr = {}

    def add_client(self,conn):
        self.connections.append(conn)

    def serve(self):
        while True:
            try:
                readable,writable,excepted = select.select(self.connections,self.connections,self.connections,0)
                for conn in readable:
                    if conn == self.sock:
                        new_conn,addr = conn.accept()
                        print(f"got new conn from {addr}")
                        con_obj = Client(new_conn)
                        self.con_mgr[new_conn] = con_obj
                        self.add_client(new_conn)
                    else:
                        ## TODO : serve in different thread for each connection
                        ## right now it is blocking the select poll
                        con_obj = self.con_mgr[conn]
                        mgen = con_obj.message_generator()
                        message = next(mgen)
                        if message:
                            if isinstance(message,ConnectionBroken):
                                raise StopIteration
                            print(f"received {message}")
                for conn in excepted:
                    print(f"removing {conn} from list")
                    self.connection.remove(conn)

            except StopIteration:
                del self.con_mgr[conn]
                self.connections.remove(conn)
                print("{conn} has stopped abruptly")
                continue

            except Exception as E:

                if "StopIteration" in E.args[0]:
                    del self.con_mgr[conn]
                    self.connection.remove(conn)
                    continue
                else:
                    print(f"received exception {E}")
                    print(f"{traceback.print_exc()}")
                    sys.exit(1)

if __name__ == "__main__":
    try:
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.setblocking(0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        sock.bind(('localhost',8888))
        try:
            sock.listen(5)
        except Exception as e:
            print(f"e")
        sock.settimeout(10)
        while True:
            #conn,addr = sock.accept()
            Server = StreamingServer(sock)
            Server.serve()
    except Exception as E:
        print(E)
    finally:
        sock.close() 
        

