import socket
import struct
import time
import select

CHUNK_SIZE = 1024 

class Message:
    '''This is abstract class for message
    message could be following type
    full message
    partial message
    exception message
    '''
    def __init__(self):
        self.message = bytearray()
        self.is_full = False
        self.cur_len = 0

    def clear(self):
        self.message = bytearray()

    def set_message(self,data,total_len):
        self.message += data
        self.cur_len += len(data)
        if cur_len >= total_len:
            self.is_full = True
        else:
            self.is_full = False
        


class Client:

    def __init__(self,conn):
        self.conn = conn

    def gen_message(self):
        raise NotImplementedError

    def get_next_header(self):
        raise NotImplementedError

    def message_generator(self):
        raise NotImplementedError



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
                readable,writable,excepted = select.select(self.connections,[],self.connections)
                for conn in readable:
                    if conn == self.sock:
                        new_conn,addr = conn.accept()
                        print(f"got new conn from {addr}")
                        con_obj = Client(new_conn)
                        self.conn_mgr[new_conn] = con_obj
                        self.add_client(new_conn)
                    else:
                        ## TODO : serve in different thread for each connection
                        ## right now it is blocking the select poll
                        con_obj = self.conn_mgr[conn]
                        mgen = con_obj.message_generator()
                        message = next(mgen)
                        if messagge:
                            print(message)
                for conn in excepted:
                    print(f"removing {conn} from list")
                    self.connection.remove(conn)

            except Exception as E:

                if "StopIteration" in E.args[0]:
                    del elf.conn_mgr[conn]
                    self.connection.remove(conn)
                    continue
                else:
                    print(f"received exception {E}")
                    break

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
        

