import socket
import struct
import random
import select
import sys
import time

def recv_all(conn,total_len):
    message = bytearray()
    while True:
        chunk = conn.recv(total_len)
        if chunk == b'':
            break
        message += chunk
        if len(message) >= total_len:
            return message

def send_message(conn,message):
    ## prepare len
    slen = len(message)
    slen = struct.pack('i',slen)
    #print(f"sending {slen} ")
    conn.send(slen)
    #print(f"sending message")
    conn.send(message)

def send_message_stopping(conn,message):
    try:
        slen  = len(message)
        print(f"message len is {slen}")
        slen_h = slen // 2;
        slenb = struct.pack('i',slen)
        conn.send(slenb)
        print(f"sent header....")
        part1 = message[:slen_h]
        part2 = message[slen_h:]
        print(f"I sent {len(part1)} ")
        conn.send(part1)
        time.sleep(0.5)
        print(f"now sending sent {len(part2)} ")
        conn.send(part1)
        conn.send(part2)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    try:
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.connect(('localhost',8888))
        sock.setblocking(0)
        sock.settimeout(10)
        connections = [sock]
        tot_pack = 0
        N = 100

        while True and tot_pack <= N:

            read,write,exc = select.select(connections,connections,connections,0)

            for conn in read:
                if conn == sock:
                    read_len = recv_all(conn,4)
                    read_len = struct.unpack('i',read_len)[0]
                    message = recv_all(conn,read_len)
                    print(message)
                else:
                    pass

            for conn in write:
                if conn == sock:
                    sl = random.randint(1,3)
                    time.sleep(sl)
                    send_message_stopping(conn,b'n'*random.randint(20,40))
                    tot_pack += 1
                    #size_fmt = '\r{:>6.1%}'.format(tot_pack/N)
                    #sys.stdout.write(size_fmt)
                    #sys.stdout.flush()

                else:
                    pass

            for conn in exc: 
                print(f"exception on {conn}")
                ##conn.shutdown()
                conn.close()
                break

    except Exception as E:
        print(E)
        if sock:
            ##sock.shutdown(5)
            sock.close()

