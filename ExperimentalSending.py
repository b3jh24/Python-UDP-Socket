'''
Created on Jun 15, 2016

@author: bhornak
'''
#from scapy.all import *
import socket
import os
import math
import time

'''
Testing with data from file -- see if we can give ID numbers, and detect 
what packets did (or didn't reach the other side)
'''

buf = 14000
s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
host ="10.102.46.218"   #Address of the guy hosting the UDP socket - in this case it's Andrew
port = 5005
addr = (host,port)

tcp_host = "10.102.46.218"  #Address of the guy (me) hosting the TCP socket - in this case it's Brian
tcp_port = 7007
tcp_buf = 20

packetQueue = []        #Empty list that contains each packet sent - used for retransmissions

f = open('file.txt', 'rb')

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
#FIXME: Need to add socket.SO_REUSEADDR to allow socket to be reused, but this needs privileges
TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
TCP_sock.bind((tcp_host, tcp_port))
TCP_sock.listen(1)

conn, tcp_addr = TCP_sock.accept()
<<<<<<< HEAD
conn.settimeout(1)
=======
>>>>>>> b5b5f8ffd9bafc1ff702838a1a2cb99aef17c29d
while 1:
    clientReq = conn.recv(tcp_buf)
    if not clientReq: break
    #print "Client request: ", clientReq
    if (clientReq == "GET_NUM_CHUNKS"):
        conn.send(str(getNumChunksToSend()))
     #   print "Sent GET_NUM_CHUNKS"
        break
    else:
        print "Command not recognized"
        break
#conn.close()
#TCP_sock.close()

def read_in_chunks(infile, chunk_size=buf):
    """Chunk the file before we send it.
    Arguments:
    infile -- the file to chunk
    chunk_size -- the size of the chunk in bytes (default 32KB)
    """

    while True:
        chunk = infile.read(chunk_size)
        if chunk:
            yield chunk
        else:
            # The chunk was empty, which means we're at the end of the file
            return

def run():
    didntRecvACK = False
    local_ID = 0
    numSent = 0
    count = 0
    start = time.time()
    for chunk in read_in_chunks(f):
#         pack = IP(dst=host, id=local_ID)/UDP()/chunk
#         sendPack = pack[UDP].load
#         id = pack[IP].id
#         idstring = str(id)
        if(s.sendto(chunk,addr) and s.sendto(str(local_ID),addr)):
            #print "sending ..."
            #print "\t\t ID: ",local_ID
            numSent += 1
            '''
            Store the packet being sent in the appropriate spot
            Indices are arranged by packet localID, and each spot contains the packets load (as a string)
            '''
            packetQueue.insert(local_ID,chunk)   
                 
            '''
            Wait on ACK packets from the client
            We will receive these packets over TCP (expecting the unique Packet ID/sequence number)
            We won't send another packet until we've received the ACK from the client
            If, after x seconds, we haven't received an ACK, we will assume packet was lost, and queue it for retransmission
            '''
            
<<<<<<< HEAD
            
            if(numSent >= 13):
                conn.settimeout(.05)
=======
            if(numSent >= 100):
                conn.settimeout(2)
>>>>>>> b5b5f8ffd9bafc1ff702838a1a2cb99aef17c29d
                try:
                    ACK = conn.recv(tcp_buf)
                    #print "ACK: "+ACK
                    if ACK:
                        numSent = 0
                    else:
                        print "ACK is NONE!"
                except socket.timeout:
                    ACK = None
<<<<<<< HEAD
                    #===========================================================
                    # Note that a timeout here simply means that the client hasn't gotten enough packets to send an ACK.
                    # that means packets were dropped along the way. So, if we frequently get timeout issues, it's debatable as to 
                    # how much "free reign" we should give the server. Letting him send packets as quick as he can invariably leads
                    # to significant packet loss, which means more data to resend, which, and I might be wrong here, takes longer than
                    # just slowing down the server in the first place
                    #===========================================================
                    print "Socket timed out (after "+str(count) +" loops) because we didn't get an ACK, let's send him some more packets"
                    #conn.settimeout(5)
=======
                    print "Socket timed out (after "+str(count) +" loops) because we didn't get an ACK, let's send him some more packets"
                    conn.settimeout(5)
>>>>>>> b5b5f8ffd9bafc1ff702838a1a2cb99aef17c29d
                    while (ACK is not "I got 20 packets"):
                        """
                        Continue with the main loop, and send more packets, 
                        until we get something back (i.e. the client got another 20 packets)
                        """
<<<<<<< HEAD
                        bigDataChunk  = packetQueue[local_ID] + packetQueue[local_ID] + packetQueue[local_ID]
                        s.sendto(bigDataChunk, addr)
                        try:
                            ACK = conn.recv(tcp_buf)
                            print "Nigga just ACKed the big ass data chunk: ",ACK
                        except socket.timeout:
                            pass
                            #print "Socket just timed out again...fuck me"
                       
=======
                        print "Sending more packets..."
                        s.sendto(packetQueue[local_ID], addr)
                        ACK = conn.recv(tcp_buf)
>>>>>>> b5b5f8ffd9bafc1ff702838a1a2cb99aef17c29d
                        if ACK:
                            print "This is the ACK: ", ACK
                            break    
                        else:
<<<<<<< HEAD
                            pass
                            #print "Need to send more packets yet"                          
=======
                            print "Need to send more packets yet"                          
>>>>>>> b5b5f8ffd9bafc1ff702838a1a2cb99aef17c29d
                    else:
                        print "We got an ACK: " + ACK
                        
                        '''
                        Compare this ACK (likely the packets received) against what we know we sent. 
                        There is probably some discrepancy that will need to be addressed. That is to say, he is probably missing some
                        packets, and we're gonna have to resend them now, or make a list to send them later
                        '''
                count += 1
                numSent = 0
            
            local_ID += 1
    end = time.time()
    s.close()      
    f.close()
    conn.close()
    TCP_sock.close()
    print "File sent!"
    print "Time: " + str(round(end-start,2)) + "s"
    fsize = os.path.getsize("file.txt")/10e8
    rate = fsize/(end-start)
    print "Rate: " + str(round(rate,2)) +" GB/s"
    print "Count: ", count

if (__name__ == '__main__'):
    run()
    



