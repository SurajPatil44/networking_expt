import socket
import struct
import time
import select
import sys
import traceback
from queue import Queue
import queue
import errno
from Reader import ReaderWithLen as Client
from Reader import MoreDataRequired,ConnectionBroken,PrimePacket,OutOfSync

CHUNK_SIZE = 1024 


def send_message(conn,message):
    slen = len(message)
    slen = struct.pack('i',slen)
    conn.send(slen)
    conn.send(message)

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
                        new_conn.setblocking(0)
                        new_conn.settimeout(10)
                        con_obj = Client(new_conn)
                        ##prime only once 
                        mgen = con_obj.message_generator()
                        message_q = Queue()
                        self.con_mgr[new_conn] = (con_obj,mgen,message_q)
                        self.add_client(new_conn)
                    else:
                        ## TODO : serve in different thread for each connection
                        ## right now it is blocking the select poll
                        con_obj = self.con_mgr[conn][0]
                        mgen = self.con_mgr[conn][1]
                        msg_q = self.con_mgr[conn][2]
                        message = next(mgen)
                        print(f"generated {message} of {type(message)}")
                        if message:
                            if isinstance(message,ConnectionBroken):
                                raise StopIteration
                            if isinstance(message,OutOfSync):
                                msg_q.put_nowait(message)
                            elif isinstance(message,MoreDataRequired):
                                print(f"reqd {message.reqd}")
                            elif isinstance(message,bytearray):
                                try:
                                    msg_q.put_nowait(message)
                            #print("messge q is ",msg_q)
                                    print(f"received {bytes(message)} from {conn.getpeername()}")
                                except Exception as e:
                                    print(f"{traceback.print_exc()}")
                            else:
                                print(f"the type is {message}")

                for conn in writable:
                    #print(f"we can write also for {conn.getpeername()}")
                    msg_q = self.con_mgr[conn][2]
                    next_msg = None
                    try:
                        next_msg = msg_q.get_nowait()
                        print(f"got {next_msg} from queue")
                    except queue.Empty:
                        #print("is empty ???")
                        pass
                    else:
                        if isinstance(next_msg,OutOfSync):
                            oos = b"server went out of sync"
                            send_message(conn,oos)
                            raise StopIteration
                        elif isinstance(next_msg,bytearray):
                            print(f"sending {next_msg} to {conn.getpeername()}")
                            send_message(conn,bytes(next_msg))
                        else:
                            print(f"message is {next_msg}")
                        #conn.send(next_msg)
                    
                for conn in excepted:
                    print(f"removing {conn} from list")
                    self.connection.remove(conn)

            except StopIteration as Exc:
                try:
                    print(f"closing {conn.getpeername()}")
                except OSError as exc:
                    print(f"this is for that linux patch")
                    print(f"linux gives {exc} when client dies")
                    print(f"and we access peername")
                conn.close()
                del self.con_mgr[conn]
                self.connections.remove(conn)
                continue

            except Exception as E:
                if "StopIteration" in E.args[0]:
                    print(f"closing {conn.getpeername()}")
                    conn.close()
                    del self.con_mgr[conn]
                    self.connections.remove(conn)
                    continue
                else:
                    print(f"closing {conn.getpeername()}")
                    conn.close()
                    del self.con_mgr[conn]
                    self.connections.remove(conn)
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
        print(f"somehow {E}")
        print(f"{traceback.print_exc()}")
    finally:
        sock.close() 
        

