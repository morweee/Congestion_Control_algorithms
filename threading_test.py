import socket
import time
from collections import defaultdict
import threading

PACKET_SIZE = 1024
SEQ_ID_SIZE = 4
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
CWND = 1
ssthresh = 64
MAX_SEQ_NUM = 256

# Read data
start = time.time()
with open('docker/file.mp3', 'rb') as f:
    data = f.read()
    # data = data[:1000000]

# Create a udp socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind(("localhost", 5000))
udp_socket.settimeout(1)

seq_lock = threading.Lock()
ack_record = defaultdict(int)
start_send = True
seq_id = 0
target_id = seq_id + MESSAGE_SIZE*CWND
getCWNDTarget = True
CWNDTarget = 0
RecvAllPacket = False


def send_packets():
    global seq_id, CWND, ssthresh, target_id, getCWNDTarget,CWNDTarget, RecvAllPacket
    while not RecvAllPacket:
        while seq_id < len(data):
            # print(start_send)
            while seq_id<=target_id:
                message = int.to_bytes(seq_id, SEQ_ID_SIZE, signed=True, byteorder='big') + data[seq_id: seq_id + MESSAGE_SIZE]
                seq_id += MESSAGE_SIZE
                udp_socket.sendto(message, ('localhost', 5001))
                # for i in range(CWND):
                #         if seq_id < len(data):
                #             message = int.to_bytes(seq_id, SEQ_ID_SIZE, signed=True, byteorder='big') + data[seq_id: seq_id + MESSAGE_SIZE]
                #             seq_id += MESSAGE_SIZE
                #             udp_socket.sendto(message, ('localhost', 5001))
                #             # print(f"Send Packet:{seq_id//MESSAGE_SIZE}")
                #             # time.sleep(0.005)
                # time.sleep(0.1)
            if getCWNDTarget:
                CWNDTarget = seq_id + MESSAGE_SIZE * CWND
                getCWNDTarget = False
            

def receive_packets():
    global seq_id, CWND, ssthresh,target_id, getCWNDTarget,CWNDTarget ,RecvAllPacket
    while True:
        try:
            # wait for ack and extract ack id
            ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
            
            # account for each ack's occurence
            ack_record[ack_id] += 1
            
            if ack_record[ack_id] >=3:
                print("Duplicate occur, ssthresh:", ssthresh)
                seq_id = ack_id
                ssthresh = CWND//2
                CWND = ssthresh+3
                target_id = ack_id + MESSAGE_SIZE*CWND
                continue
            
            print(ack_id, ack[SEQ_ID_SIZE:])
            target_id = ack_id + MESSAGE_SIZE*CWND
            # if ack id == sequence id, move on
            if ack_id == len(data):
                RecvAllPacket = True
                break
            if ack_id == min(CWNDTarget,len(data)):
                getCWNDTarget = True
                if CWND < ssthresh:
                    # slow start phase, exponential growth
                    CWND *= 2
                else:
                    # congestion avoidance phase, linear growth
                    CWND += 1

                continue
                
        except socket.timeout:
            # no ack, timeout, set ssthresh to half of CWND, and set CWND to 1
            seq_id = ack_id
            ssthresh = CWND // 2
            CWND = 1
            target_id = ack_id + MESSAGE_SIZE*CWND
            print("timeout, ssthresh:", ssthresh)
            continue

# Start threads
send_thread = threading.Thread(target=send_packets)
receive_thread = threading.Thread(target=receive_packets)

send_thread.start()
receive_thread.start()

# Wait for both threads to finish
send_thread.join()
receive_thread.join()

print("123")
# Send final closing message
empty_message = int.to_bytes(len(data), 4, signed=True, byteorder='big')
udp_socket.sendto(empty_message, ('localhost', 5001))

while True:
    final_ack, _ = udp_socket.recvfrom(PACKET_SIZE)
    seq_id, message = final_ack[:SEQ_ID_SIZE], final_ack[SEQ_ID_SIZE:]
    if message == b'ack':
        continue
    if message == b'fin':
        udp_socket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big') + '==FINACK=='.encode(), ('localhost', 5001))
        break

end = time.time()
print(f"throughput: {len(data) // (end - start)} bytes per second")
print(f"time lapse: {(end - start)} seconds")