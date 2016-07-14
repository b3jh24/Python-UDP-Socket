'''
Created on Jun 14, 2016

Client (receiver) for a UDP file transfer:
Receive file in 32KB chunks (32000 bytes), arrange them in the proper order, tell the server of success

@author: bhornak
'''

"""
Issues: 
Chunking works as it's supposed to, but the UDP transfer loses data, need to work on creating
a way to identify each chunk being sent (label it or something like that), and then make sure 
we get it on the receiving end
"""

import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
buf = 32000     #Buffer size in bytes for each chunk

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

f = open('recv.txt','wb')

dataChunk,addr = sock.recvfrom(buf)
try:
    while(dataChunk):
        f.write(dataChunk)
        sock.settimeout(2)
        dataChunk,addr = sock.recvfrom(buf)
except socket.timeout:
    f.close()
    sock.close()
    print "File received!"
