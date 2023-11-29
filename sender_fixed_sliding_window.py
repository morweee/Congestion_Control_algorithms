# This protocol allows the sender to send multiple packets at a time 
# before waiting for an acknowledgement.

import socket
from datetime import datetime

# total packet size
PACKET_SIZE = 1024
# bytes reserved for sequence id
SEQ_ID_SIZE = 4
# bytes available for message
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
# window size
WINDOW_SIZE = 100

# read data
with open('send.txt', 'rb') as f:
    data = f.read()

# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

    # bind the socket to a OS port
    udp_socket.bind(("localhost", 5000))
    udp_socket.settimeout(1)

    # start sending data from 0th sequence
    base = 0
    next_seq_num = 0
    packets = {}

    while base < len(data):

        # send new packets if window is not full
        while next_seq_num < base + WINDOW_SIZE and next_seq_num < len(data):
            # construct message
            message = int.to_bytes(next_seq_num, SEQ_ID_SIZE, signed=True, byteorder='big') + data[next_seq_num : next_seq_num + MESSAGE_SIZE]
            # send message out
            udp_socket.sendto(message, ('localhost', 5001))
            # store the packet
            packets[next_seq_num] = message
            # move sequence id forward
            next_seq_num += MESSAGE_SIZE

        # wait for acknowledgement
        while True:
            try:
                # wait for ack
                ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                # extract ack id
                ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
                print(ack_id, ack[SEQ_ID_SIZE:])
                # if ack id >= base, move base forward
                if ack_id >= base:
                    base = ack_id + MESSAGE_SIZE
                    break
            except socket.timeout:
                # no ack, resend all packets in the window
                for seq_id, message in packets.items():
                    if seq_id >= base and seq_id < base + WINDOW_SIZE:
                        udp_socket.sendto(message, ('localhost', 5001))

    # send final closing message
    udp_socket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big'), ('localhost', 5001))
