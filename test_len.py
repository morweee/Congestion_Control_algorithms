
import socket
import time 

with open('docker/file.mp3', 'rb') as f:
    data = f.read()
    data = data[0:len(data)//15]
    print(len(data))