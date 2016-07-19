'''
Created on Jun 15, 2016

@author: bhornak
'''
#from scapy.all import *
import socket
import os
import math
import time
import logging
from __builtin__ import int
from time import sleep

buf = 8972
s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
host ="10.102.46.218"   #Address of the guy hosting the UDP socket - in this case it's Andrew
port = 5005
addr = (host,port)
s.setsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF, 185760) #50485760


tcp_host = "10.102.46.218"  #Address of the guy (me) hosting the TCP socket - in this case it's Brian
tcp_port = 7007
tcp_buf = 2048


f = open('file.txt', 'rb')

class BadChunkRequest(Exception):
    def __init__(self):
        Exception.__init__(self, "Expecting to receive an integer value for number of chunks requested!")


def getNumChunksToSend():
    """Returns the number of chunks that will be sent to the client
    The client will use this to know how many blocks it should receive (useful for data verification)
    """
    #TODO change file name from file.txt to be whatever the data/file actually is
    size = os.path.getsize("file.txt")
    numToRound = float(size)/float(buf)  #Use float point math because int's wont give correct number
    return math.ceil(numToRound)         #File size/chunk size = number of chunks - rounded up

'''
Create a TCP socket to enable communication between server and client
'''
TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
TCP_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
TCP_sock.bind((tcp_host, tcp_port))
TCP_sock.listen(1)

conn, tcp_addr = TCP_sock.accept()
conn.settimeout(1)
while 1:
    clientReq = conn.recv(tcp_buf)
    if not clientReq: break
    #print "Client request: ", clientReq
    if (clientReq == "GET_NUM_CHUNKS"):
        conn.send(str(getNumChunksToSend()))
        #print "Sent GET_NUM_CHUNKS"
        break
    else:
        print "Command not recognized"
        break
#conn.close()
#TCP_sock.close()

def read_in_chunks(infile, chunk_size):
    """Chunk the file before we send it.
    
    Args:
        infile -- the file to chunk
        chunk_size -- the size of the chunk in bytes (using 512 b/c thats what the FPGA uses)
    """
    chunkStartTime = time.time()
    while True:
        chunk = infile.read(chunk_size)
        if chunk:
            yield chunk
        else:
            # The chunk was empty, which means we're at the end of the file
            chunkEndTime = time.time()
            print "ChunkTime: ",(chunkEndTime-chunkStartTime)
            return

def run():
    local_ID = 0
    totalNumSent = 0
    numSent = 0
    sendLoop = 0
    #howManyToSend = 4000      #Number of chunks the client wants us to send - hardcoded for now
    conn.settimeout(None)
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    
    '''
    First, we need to get some basic info from the client.
    Let's see if he's ready to receive data, and if so, how much does he want?
    '''
    howManyToSend = conn.recv(tcp_buf)
    if howManyToSend.isdigit() == False:
        raise BadChunkRequest()
        
    howManyToSend = int(howManyToSend)
    logging.info("He wants us to send him " + str(howManyToSend) + " chunks of data, let's do it!")
    conn.send("Chunks on their way!")
    
    packetQueue = [None] * howManyToSend        #Empty list that contains each packet sent - used for retransmissions (can only contain the
                                 #number of packets that the client requested (after that, it dumps everything)
    
    
    '''
    How the hell this works:
    
    We want to only send as many packets (chunks) as the client asks for, no more no less. However, we want to make sure that each packet is a new data chunk (not the same one over
    and over again like I had in the old code). So, we loop through our file, pulling out chunks as we go along. Once we pull out that chunk, and before we send it 
    we check to see if we've sent as many chunks as the client wanted. If we have, we wait for an ACK, and proceed accordingly. Then, after we've clarified that the client is ready 
    for more, we send the current chunk we pulled out. Then we go to the next chunk. Once we get to the last group of data to be sent (a group being all the chunks we send before an ACK)
    then signal that this is the last group we're gonna send, and finish off the transfer.
    '''
    keepGoing = True
    start = time.time()
    #while(totalNumSent < getNumChunksToSend() and keepGoing):
        #print "Titties"
    forTime = time.time()
    for chunk in read_in_chunks(f,buf):  
        if(numSent == howManyToSend):
            '''
            We've done our part, and sent the number of chunks he wanted, now we wait to hear from him
            We should expect to hear from him, because once he times out (i.e. after we sent our data, and he stopped receiving it)
            he'll at least tell us what went wrong
     
            The ACK will either be something of the form "I got everything you sent me, send more", or "These are the packets I didn't get"
            '''
            ACK = conn.recv(tcp_buf)
            #print "ACK: "+ACK
            if(ACK != "I got the 60 packets I requested, you can send some more"):
                '''
                He didn't get all 60 packets, but he *probably* told us what he did get, and that's good enough
                We just need to figure out how many we need to resend (and what packets in particular)
     
                First, I need to convert the string (the ACK) into a list of strings (each item is the ID as a string)
                Then, convert every item on the list from a string to an int. At this point, I can do stuff with it
                '''
                packetsToResend = ACK
                packetsToResend = packetsToResend.strip('[,]')
                packetsToResend = packetsToResend.replace(",","")
                packetsToResend = packetsToResend.replace(",","")
                packetsToResend = packetsToResend.split()
                packetsToResend = [int(i) for i in packetsToResend]
                numResent = 0
                while (numResent < len(packetsToResend)):
                    '''
                    Breakdown/format of lists:
                    packetQueue:
                        Index = id of each packet
                        Object = data chunk associated with that ID
                    packetsToResend:
                        Index = unimportant (just the order that packets we dropped, but not relevant)
                        Object = ID of a packet we didn't receive
                    numResent (not a list):
                        keeps track of what packet we're resending from the packetsToResend list
                    What happens below:
                        Assume 20 is the number of packets to resend
                        We send the 0th to the 19th (20 total) packets - tracked using numResent
                        We know which packet to use based on the object of the packetsToResend list
                        We then know what data to send based on the object of the packetQueue list.
                    '''
                    if(s.sendto(packetQueue[packetsToResend[numResent]],addr) and s.sendto(str(packetsToResend[numResent]),addr)):
                        print "Resent packet number: " + str(packetsToResend[numResent])
                        numResent+=1
                else:
                    '''
                    We've resent the packets he asked for again, now we wait to make sure he's got them
                    '''
                    ACK = conn.recv(tcp_buf)
                    print "Resent ACK: "+ACK
                    sendLoop +=1
            else:
                '''
                He got all of our chunks, let's continue sending things
                '''
                #print "client got our chunks"
                numSent = 0
                sendLoop += 1
        if(s.sendto(chunk,addr) and s.sendto(str(local_ID),addr)):
            try:
                packetQueue[local_ID - (sendLoop * howManyToSend)] = chunk
            except IndexError:
                print "\nIndex: ", (local_ID - (sendLoop * howManyToSend))
                print "Send Loop: ",sendLoop
                print "ID: ", local_ID
                sleep(3)
            numSent += 1
            local_ID += 1
            totalNumSent += 1
    else:
        keepGoing = False
        endFor = time.time()
    end = time.time()
    s.close()      
    f.close()
    conn.close()
    TCP_sock.close()
    print "Total Num Sent: ",totalNumSent
    print "File sent!"
    print "Time: " + str(round(end-start,4)) + "s"
    fsize = os.path.getsize("file.txt")/10e8
    rate = fsize/(end-start)
    print "Rate: " + str(round(rate,3)) +" GB/s = " + str(round(rate*8,3))+" Gb/s"
    print "Loops: ", sendLoop
    print "For Loop Time: ", (endFor-forTime)
if (__name__ == '__main__'):
    run()
