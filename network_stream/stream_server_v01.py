import socket
import struct
import time
import select

CHUNK_SIZE = 1024 

class StreamingServer:

    def __init__(self,sock):
        self.sock = sock
        self.connections = [sock]

    def gen_message(self):
        try:
            message = bytearray()
            hdr_size = yield None
            #print(f"recived {hdr_size}")
            while True:
                chunk = self.conn.recv(hdr_size)

                if chunk == b'':
                    yield None

                message += chunk

                if len(message) >= hdr_size:
                    #print(f"message now {message}")
                    new_hdr_size = yield message[:hdr_size]
                    #print(f"recived {new_hdr_size}")
                    if len(message):
                        message = message[hdr_size:]
                    else:
                        message = bytearray()
                    hdr_size = new_hdr_size

        except Exception as e:
            print(f"exception is {e}")
            yield None

    def get_next_header(self):
        try:
            next_pack_size = self.conn.recv(4)
            if next_pack_size != b'':
                print(f"header recieved {next_pack_size}")
                next_pack_size = struct.unpack('i',next_pack_size)
                return next_pack_size[0]
            else:
                return None
        except Exception as e:
            print(f"received exception {e} sending None")
            return None

    def message_generator(self):
        ## prime the gen
        mgen = self.gen_message()
        next(mgen)

        while True:
            nsize = self.get_next_header()
            #print(f"next pack size is {nsize}")
            if nsize == None:
                mgen.close()
                yield None
            yield mgen.send(nsize)

    def add_client(self,conn):
        self.connections.append(conn)
                

    def serve(self):
        try:
            while True:
                readable,writable,excepted = select.select(self.connections,[],self.connections)
                for conn in readable:
                    if conn == self.sock:
                        new_conn,addr = conn.accept()
                        print(f"got new conn from {addr}")
                        self.add_client(new_conn)
                    else:
                        ## TODO : serve in different thread for each connection
                        ## right now it is blocking the select poll
                        self.conn = conn
                        mgen = self.message_generator()
                        count = 0
                        for ind,message in enumerate(mgen):
                            if message == None:
                                print(f"we received {message} at {ind}")
                                if count > 0:
                                    raise StopIteration
                                    count += 1
                                    continue
                            print(f"{ind} . {message}")
                for conn in excepted:
                    print(f"removing {conn} from list")
                    self.connection.remove(conn)

        except Exception as E:
            print(f"received exception {E}")

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
        

