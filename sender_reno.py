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
with open('docker/file.mp3', 'rb') as f:
    data = f.read()

# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

    # bind the socket to a OS port
    udp_socket.bind(("localhost", 5000))
    udp_socket.settimeout(1)

    # start sending data from 0th sequence
    seq_id = 0
    start = time.time()
    ack_record = defaultdict(int)
    while seq_id < len(data):

        # send packets in the congestion window
        for i in range(CWND):
            if seq_id + i * MESSAGE_SIZE < len(data):
                # construct message
                message = int.to_bytes(seq_id + i * MESSAGE_SIZE, SEQ_ID_SIZE, signed=True, byteorder='big') + data[seq_id + i * MESSAGE_SIZE : seq_id + (i + 1) * MESSAGE_SIZE]
                # send message out
                udp_socket.sendto(message, ('localhost', 5001))

        # wait for acknowledgement
        while True:
            try:
                # wait for ack and extract ack id
                ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
                
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
                if ack_id == seq_id:
                    seq_id += CWND * MESSAGE_SIZE
                    if CWND < ssthresh:
                        # slow start phase, exponential growth
                        CWND *= 2
                    else:
                        # congestion avoidance phase, linear growth
                        CWND += 1
                    break
                    
            except socket.timeout:
                # no ack, timeout => set ssthresh to half of CWND, and set CWND to 1
                ssthresh = CWND // 2
                CWND = 1
                print("timeout, ssthresh:", ssthresh)

    # send final closing message
    udp_socket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big'), ('localhost', 5001))
    end = time.time()
    print(f"throughput: {len(data)//(end-start)} bytes per seconds")
    print(f"time lapse: {(end-start)} seconds")
