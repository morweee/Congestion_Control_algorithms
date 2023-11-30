# stop n wait: sender sends packet one at a time, and waits for ACK
# only send next packet if the sender receives correct ACK from the receiver

import socket
import time 

# total packet size
PACKET_SIZE = 1024
# bytes reserved for sequence id
SEQ_ID_SIZE = 4
# bytes available for message
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE

# read data
with open('docker/file.mp3', 'rb') as f:
    data = f.read()
    data = data[0:len(data)//15]
 
# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

    # bind the socket to a OS port
    udp_socket.bind(("localhost", 5000))
    udp_socket.settimeout(1)
    
    # start sending data from 0th sequence
    seq_id = 0
    start = time.time()
    while seq_id < len(data):
        
        # construct message
        # sequence id of length SEQ_ID_SIZE + message of remaining PACKET_SIZE - SEQ_ID_SIZE bytes
        message = int.to_bytes(seq_id, SEQ_ID_SIZE, signed=True, byteorder='big') + data[seq_id : seq_id + MESSAGE_SIZE]
        
        # send message out
        udp_socket.sendto(message, ('localhost', 5001))
        
        # wait for acknowledgement
        while True:
            try:
                # wait for ack
                ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                
                # extract ack id
                ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
                print(ack_id, ack[SEQ_ID_SIZE:])
                
                # ack id == sequence id, move on
                if ack_id == seq_id:
                    break
            except socket.timeout:
                # no ack, resend message
                udp_socket.sendto(message, ('localhost', 5001))
                print("resend")
                
        # move sequence id forward
        seq_id += MESSAGE_SIZE
        
    # send final closing message
    udp_socket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big'), ('localhost', 5001))
    end = time.time()
    print(f"throughput: {len(data)//(end-start)} bytes per seconds")
    print(f"time lapse: {(end-start)} seconds")
