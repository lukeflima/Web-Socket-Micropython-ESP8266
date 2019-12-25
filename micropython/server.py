import socket
import hashlib
import binascii
import struct
import os
import machine

DEBUG=True

def xor(msg, key):
    m = len(key)
    return ''.join([chr(msg[i] ^ key[i%m]) for i in range(len(msg))])

def server_handshake():
    clr = cl.makefile("rwb", 0)
    l = clr.readline()
    #sys.stdout.write(repr(l))

    webkey = None

    while 1:
        l = clr.readline()
        if not l:
            raise OSError("EOF in headers")
        if l == b"\r\n":
            break
    #    sys.stdout.write(l)
        h, v = [x.strip() for x in l.split(b":", 1)]
        if DEBUG:
            print((h, v))
        if h == b'Sec-WebSocket-Key':
            webkey = v

    if not webkey:
        raise OSError("Not a websocket request")

    if DEBUG:
        print("[!] Sec-WebSocket-Key:", webkey, len(webkey))

    d = hashlib.sha1(webkey)
    d.update(b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11")
    respkey = d.digest()
    respkey = binascii.b2a_base64(respkey)[:-1]
    if DEBUG:
        print("[!] Respkey:", respkey)

    cl.send(b"""HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: """)
    cl.send(respkey)
    cl.send("\r\n\r\n")

    return clr


def recv_msg():
    header = cl_file.recv(2)
    print(bin(header[0]))
    if(not header[1] & 0b10000000):
        return ""

    if DEBUG:
        print("Masked")

    length = header[1] & 0b01111111
    if(length == 126):
        length = struct.unpack(">H",cl_file.recv(2))[0]
    elif(length == 127):
        length = struct.unpack(">Q",cl_file.recv(8))[0]

    if DEBUG:
        print("Length payload:", length)
    
    mask = cl_file.recv(4)

    if DEBUG:
        print("Mask:", mask)

    payload = cl_file.recv(length) if length > 0 else ""
    payload = xor(payload, mask)

    if DEBUG:
        print("Payload:", payload)
    
    # if(not header[0] & 0b10000000):
    #     payload += recv_msg()
    return payload


def send_msg(msg):
    print("[Header]")
    header = [0, 0]
    header[0] = struct.pack(">B", 0x81)
    length = ext_payload_length = len(msg)

    if length > 125 and length < 65536:
        ext_payload_length = struct.pack(">H", length)
        length = 126
    elif length > 65536:
        ext_payload_length = struct.pack(">Q",length & 0xEFFFFFFF)
        length = 127
    header[1] = struct.pack(">B", length & 0b01111111)

    if length != ext_payload_length:
        header[1] += ext_payload_length

    cl.send( header[0] + header[1] + msg.encode('utf8'))
    if DEBUG:
        print("[!] Header", header)
        print("[!] Length payload", length)
        if length != ext_payload_length:
            print("[!] Extended payload length", ext_payload_length)
        print("[!] Msg", msg)

addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

print('[+] Listening on', addr)

pin = machine.Pin(2, machine.Pin.OUT)
pin.on()

while True:
    cl, addr = s.accept()
    print('[!] Client connected from', addr)
    cl_file = server_handshake()
    while True:
        payload = recv_msg()

        if payload == 'toggle-led':
            if DEBUG:
                if pin.value():
                    print("Truning off led")
                else:
                    print("Truning on led")

            pin.value(not pin.value())
            if pin.value():
                send_msg("OFF")
            else:
                send_msg("ON")
        elif payload == 'is-led-on':
            send_msg("OFF" if pin.value() else "ON")
        elif payload == "":
            print("[!] Closing connection from", addr)
            break
    cl.close()
