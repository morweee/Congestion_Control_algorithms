import socket
import time
from collections import defaultdict

# total packet size
PACKET_SIZE = 1024
# bytes reserved for sequence id
SEQ_ID_SIZE = 4
# bytes available for message
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
# initial congestion window size
CWND = 1
# threshold
ssthresh = 64
# maximum sequence number
MAX_SEQ_NUM = 256

# read data
start = time.time()
with open('docker/file.mp3', 'rb') as f:
    data = f.read()
    data = data[:1000000]

# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

    delayDict = defaultdict(float)
    delayPacketID = 0
    # bind the socket to a OS port
    udp_socket.bind(("localhost", 5000))
    udp_socket.settimeout(1)

    # start sending data from 0th sequence
    seq_id = 0
    ack_record = defaultdict(int)
    while seq_id < len(data):

        # send packets in the congestion window
        for i in range(CWND):
            if seq_id < len(data):
                # construct message
                message = int.to_bytes(seq_id, SEQ_ID_SIZE, signed=True, byteorder='big') + data[seq_id : seq_id + MESSAGE_SIZE]
                # send message out
                if not delayDict[seq_id]:
                    delayDict[seq_id] = time.time()
                seq_id += MESSAGE_SIZE
                udp_socket.sendto(message, ('localhost', 5001))

        # wait for acknowledgement
        while True:
            try:
                # wait for ack and extract ack id
                ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
                
                while delayPacketID != ack_id:
                    delayDict[delayPacketID] = time.time()-delayDict[delayPacketID]
                    delayPacketID = min(delayPacketID+MESSAGE_SIZE,len(data))

                # account for each ack's occurence
                ack_record[ack_id] += 1
                
                # TRIPLE DUPLICATES ACK occurs
                # FAST RECOVERY: 
                #       resend the packet
                #       threshold = window / 2
                #       window = (previous threshold) + 3
                
                if ack_record[ack_id] >=3:
                    seq_id = ack_id + MESSAGE_SIZE
                    prev_ssthresh = ssthresh
                    ssthresh = CWND//2
                    CWND = prev_ssthresh + 3
                    break

                print(ack_id, ack[SEQ_ID_SIZE:])
                
                # if ack id == sequence id, move on
                if ack_id == min(seq_id,len(data)):
                    if CWND < ssthresh:
                        # slow start phase, exponential growth
                        CWND *= 2
                    else:
                        # congestion avoidance phase, linear growth
                        CWND += 1
                    break
                    
            except socket.timeout:
                # no ack, timeout, set ssthresh to half of CWND, and set CWND to 1
                seq_id = ack_id
                ssthresh = CWND // 2
                CWND = 1
                print("timeout, ssthresh:", ssthresh)
                break

    # send final closing message
    # send an empty message with the correct sequence id (seq_id + MESSAGE_SIZE)
    empty_message = int.to_bytes(len(data), 4, signed=True, byteorder='big')
    udp_socket.sendto(empty_message, ('localhost', 5001))
    while True:
            # wait for final ack
            final_ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            # get the final message id
            seq_id, message = final_ack[:SEQ_ID_SIZE], final_ack[SEQ_ID_SIZE:]
            if message == b'ack':
                continue
            if message == b'fin':
                udp_socket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big') + '==FINACK=='.encode(), ('localhost', 5001))
                break
    end = time.time()
    print(f"throughput: {len(data)//(end-start)} bytes per seconds")
    print(f"time lapse: {(end-start)} seconds")
    print(f"Average packet Delay: {sum(delayDict.values())/len(delayDict)}")