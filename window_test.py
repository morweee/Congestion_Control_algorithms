import socket
import time
from datetime import datetime

# total packet size
PACKET_SIZE = 1024
# bytes reserved for sequence id
SEQ_ID_SIZE = 4
# bytes available for message
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
# window size in terms of number of packets
WINDOW_SIZE = 10  # Adjust this to set the number of packets in the window

# read data
with open('/Users/morrishsieh/Desktop/Computer_Network/hw3/docker/file.mp3', 'rb') as f:
    data = f.read()
    data = data[0:len(data)//15]

# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
    udp_socket.bind(("localhost", 5000))
    udp_socket.settimeout(1)

    base = 0
    next_seq_num = 0
    packets = {}

    start = time.time()
    while base < len(data):
        # Send new packets if window is not full
        while (next_seq_num // MESSAGE_SIZE) < (base // MESSAGE_SIZE) + WINDOW_SIZE and next_seq_num < len(data):
            message = int.to_bytes(next_seq_num // MESSAGE_SIZE, SEQ_ID_SIZE, signed=True, byteorder='big') + data[next_seq_num : next_seq_num + MESSAGE_SIZE]
            udp_socket.sendto(message, ('localhost', 5001))
            packets[next_seq_num // MESSAGE_SIZE] = message
            next_seq_num += MESSAGE_SIZE

        # Wait for acknowledgement
        while True:
            try:
                ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
                print(ack_id, ack[SEQ_ID_SIZE:])
                if ack_id >= (base // MESSAGE_SIZE):
                    base = (ack_id + 1) * MESSAGE_SIZE
                    break
            except socket.timeout:
                for seq_id, message in packets.items():
                    if seq_id >= (base // MESSAGE_SIZE) and seq_id < (base // MESSAGE_SIZE) + WINDOW_SIZE:
                        udp_socket.sendto(message, ('localhost', 5001))

    udp_socket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big'), ('localhost', 5001))