# udp_debug_listener.py
import socket
import struct

UDP_IP = "localhost"
UDP_PORT = 7000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

while True:
    data, addr = sock.recvfrom(2048)
    gpio = data[0]
    rgb_data = data[1:]
    pixels = list(struct.iter_unpack('BBB', rgb_data))
    print(f"\nFrom {addr} | GPIO {gpio} | {len(pixels)} pixels")
    for i, (r, g, b) in enumerate(pixels):
        print(f"  {i:03}: R={r:3} G={g:3} B={b:3}")
