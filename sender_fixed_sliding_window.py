# This sliding window protocol allows the sender to send multiple packets at a time 
# before waiting for an acknowledgement.

import socket
import time
from collections import defaultdict
# total packet size
PACKET_SIZE = 1024
SEQ_ID_SIZE = 4
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
# window size: 100 packets
WINDOW_SIZE = 100

# read data
with open('docker/file.mp3', 'rb') as f:
    data = f.read()
    data = data[:1000000]

# create a udp socket

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
    start = time.time()
    delayDict = defaultdict(float)
    delayPacketID = 0
    # bind the socket to a OS port
    udp_socket.bind(("localhost", 5000))
    udp_socket.settimeout(1)

    # start sending data from 0th sequence
    base = 0
    next_seq_num = 0
    packets = {}

    while base < len(data):
        print(f"base: {base}")
        # send new packets if window is not full
        while next_seq_num < base + WINDOW_SIZE * MESSAGE_SIZE and next_seq_num < len(data):
            # construct and send message
            message = int.to_bytes(next_seq_num, SEQ_ID_SIZE, signed=True, byteorder='big') + data[next_seq_num : next_seq_num + MESSAGE_SIZE]
            udp_socket.sendto(message, ('localhost', 5001))
            delayDict[next_seq_num] = time.time()
            # store the packet
            packets[next_seq_num] = message
            # move sequence id forward
            next_seq_num += MESSAGE_SIZE

        # wait for acknowledgement
        while True:
            try:
                # wait for ack and extract ack id
                ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
                print(ack_id, ack[SEQ_ID_SIZE:])
                #print(min(base + WINDOW_SIZE * MESSAGE_SIZE, len(data)))
                # ack id == base position, move on
                # last ack_id is len(data)
                while delayPacketID != ack_id:
                    delayDict[delayPacketID] = time.time()-delayDict[delayPacketID]
                    delayPacketID = min(delayPacketID+MESSAGE_SIZE,len(data))
                if ack_id == min(base + WINDOW_SIZE * MESSAGE_SIZE, len(data)):
                    base = ack_id
                    break
                
            except socket.timeout:
                # no ack, resend all packets in the window
                print("resend")
                for seq_id, message in packets.items():
                    if seq_id >= base and seq_id < base + WINDOW_SIZE * MESSAGE_SIZE:
                        udp_socket.sendto(message, ('localhost', 5001))

    # send final closing message
    # send an empty message with the correct sequence id (seq_id + MESSAGE_SIZE)
    empty_message = int.to_bytes(len(data), 4, signed=True, byteorder='big')
    udp_socket.sendto(empty_message, ('localhost', 5001))
    while True:
            # wait for final ack
            final_ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            # get the final message id
            seq_id, message = final_ack[:SEQ_ID_SIZE], final_ack[SEQ_ID_SIZE:]
            if message == b'fin':
                udp_socket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big') + '==FINACK=='.encode(), ('localhost', 5001))
                break
            
    end = time.time()
    throughput = len(data)//(end-start)
    Average_packet_Delay = sum(delayDict.values())/len(delayDict)
    print(f"throughput: {round(throughput, 2)} bytes per seconds", end=", ")
    print(f"Average packet Delay: {round(Average_packet_Delay, 2)} seconds", end=", ")
    print(f"performance metric (throughput/average per packet delay): {round((throughput // Average_packet_Delay), 2)}")