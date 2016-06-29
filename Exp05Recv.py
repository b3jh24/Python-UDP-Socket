'''
Created on Jun 16, 2016

@author: bhornak
'''
from _socket import SO_RCVBUF
#from scapy.all import *
import socket


UDP_IP = "10.102.46.218"  # Address of the guy (me) hosting the UDP socket (in this case it's Andrew) 
UDP_PORT = 5005
buf = 14000  # Buffer size in bytes for each chunk (max is like 62000)

TCP_IP = "10.102.46.218"  # Address of the guy hosting the TCP socket (in this case it's Brian)


actualNumChunks = 0

tcp_port = 7007
tcp_buf = 1024
sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP
sock.bind((UDP_IP, UDP_PORT))

'''
Create TCP socket to make basic communication requests
'''
# FIXME: Need to add socket.SO_REUSEADDR to allow socket to be reused, but this needs privileges
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.connect((TCP_IP, tcp_port))
tcp_sock.send("GET_NUM_CHUNKS")
numChunksToRecv = tcp_sock.recv(tcp_buf)
#print "Expecting to receive ",numChunksToRecv        #--KEEP
# tcp_sock.close()                                    --NO GOOD

numRecv = 0
f = open('expRecv.txt', 'wb')
dataChunk, addr = sock.recvfrom(buf)
packID, junkAddr = sock.recvfrom(buf)
packIDString = str(packID)          
numRecv += 1
count  = 0
# Create an ACK packet (based on the ID of the packet we just received, and send it back to our server
#TCP_ACK = IP() / TCP(flags='A') / packIDString
#tcp_sock.send(packIDString)


try:
    while(dataChunk):
        if(numRecv >= 5):
            #print "Stuff" 
            sock.settimeout(4)
            tcp_sock.send("I got 20 packets")
            count +=1
            numRecv = 0
        else:
            actualNumChunks += 1
            numRecv +=1
            f.write(dataChunk)
            sock.settimeout(4)
            dataChunk, addr = sock.recvfrom(buf)
            packID, junkAddr = sock.recvfrom(buf)
            packIDString = str(packID)
            #tcp_sock.send(packIDString)
except socket.timeout:
    f.close()
    sock.close()
    tcp_sock.close()
    #print "File received!"  # --KEEP
    print "A total of " + str(actualNumChunks) +" chunks were received"            #--KEEP
    print "Count: ", count
    
