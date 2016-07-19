'''
Created on Jun 16, 2016


@author: bhornak
'''
import logging
import socket
import time
import collections
import threading
import os

UDP_IP = "10.102.46.218"  # Address of the guy (me) hosting the UDP socket (in this case it's Andrew) 
UDP_PORT = 5005
buf = 8972  # buffer size in bytes for each chunk

TCP_IP = "10.102.46.218"  # Address of the guy hosting the TCP socket (in this case it's Brian)

actualNumChunks = 0

tcp_port = 7007
tcp_buf = 2048
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
numChunksToRecv = tcp_sock.recv(tcp_buf)  # The number of chunks we should get by the end of this thing
print "Expecting to receive ", numChunksToRecv  # --KEEP
#Convert numChunksToRecv to an int (from a string)
numChunksToRecv = float(numChunksToRecv)
numChunksToRecv = int(numChunksToRecv)
sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF, 50485760)   #50485760
numRecv = 0  # The number of chunks we've received so far (reset after each ACK)
totalNumRecv = 0  # The total number of chunks we've received so far, never resets. Used to know when we've got everything
canRecv = False
numChunksRequested = 50  # The number of chunks we're gonna ask for
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

'''
Request that the server send us some chunks - we're ready for it
Do this via a TCP stream    
'''
tcp_sock.send(str(numChunksRequested));
if(tcp_sock.recv(tcp_buf)):
    # We got a response from the server, let's get ready for those chunks
    print "Server about to send some chunks"
    canRecv = True


totalNumLoops = numChunksToRecv / numChunksRequested        #The total number of loops we expect to go through. In essence, this is the number of ACKs we will end up sending
totalNumBytesToRecv = numChunksToRecv * buf                 #The total number of bytes we expect to receive by the end of the transfer
progressMultiplier = 1                                      #Range 1-20: Used for figuring out how much data we've received as a percentage of the total amount we should expect
                                                            #Every 5% we will notify

#The number of "bad" packets. A bad packet is a packet that was lost, or had a missing ID, or something of the sort
global badPacket
badPacket = 0

def write_to_file(path, writeBuffer, terminate_signal):
    """Write the datagram chunks to a file in a separate thread, so long as data is provided
    
    Args:
        path - the location of the file to write to
        writeBuffer - the list (if you will) containing the data to be written
        terminate_signal - an indicator that we've finished receiving data and do no not expect more data to write
    """
    with open(path, 'wb') as out_file:  # close file automatically on exit
        while not terminate_signal.is_set() or writeBuffer:  # go on until end is signaled
            try:
                data = writeBuffer.pop()  # pop from RIGHT end of writeBuffer
            except IndexError:
                time.sleep(0.5)  # wait for new data
            else:
                out_file.write(data)  # write a chunk
    print "File closed"
    
    
    
chunkIDsRecv = [0] * (numChunksRequested)  # List of IDs received 
'''
The  number of loops we've gone through. A loop is defined as every time we've gotten as many packets as we've asked for (either received originally, or retransmitted).
Essentially, a completed loop is when we send an ACK. We use this to keep store things in lists properly because ID numbers don't necessarily correspond to list indices after the first
loop/round
'''  
loop = 0
writeBuffer = collections.deque()  # writeBuffer for reading/writing
terminate_signal = threading.Event()  # shared signal
threads = [
    threading.Thread(target= write_to_file, kwargs=dict(
    path="t1.txt",
    writeBuffer=writeBuffer,
    terminate_signal=terminate_signal
  ))]
threads[0].start()


def RecvResentPackets(writeBuffer, numBeingResent):
    """Receive packets that were resent (separate from initial receiving loop.
    
    Args:
        f - file-like object to write resent packets to
        numBeingResent- the number of packets that will be resent (so we can know how many we should be expecting)
    
    Return:
        1 - on successfully receiving all resent packets
        0 - we failed to get all of the data that was resent
    """
    numResentRecv = 0
    resentLoop = 0
    global loop
    global numChunksRequested
    try:
        while(canRecv):
            sock.settimeout(2)
            dataChunk, addr = sock.recvfrom(buf)
            packID, junkAddr = sock.recvfrom(buf)
            if(packID.isdigit() and dataChunk):
                numResentRecv += 1
                global totalNumRecv
                totalNumRecv += 1
                print "Resent PackID: " + packID
                '''
                Once we've received an ID, we want to store it in a list. We put it in the index that corresponds to it's ID number
                and flag it as received (with a 1). Once we've timed out, we can check this list to see what we're missing
                '''
                try:
                    chunkIDsRecv[int(packID) - (resentLoop*numChunksRequested)] = 1
                except IndexError:
                    print "Index: " + str(int(packID) - (resentLoop*numChunksRequested))
                    print "Loop: ",resentLoop
                    print "ID: ",packID
                    time.sleep(4)
                writeBuffer.appendleft(dataChunk)  # append to LEFT of writeBuffer so we can write the resent data
            else:
                logging.warning("The resend got fucked up...")
            if(numResentRecv == numBeingResent):
                # We've got the packets we asked for, let's alert the server to this fact
                tcp_sock.send("I got the 60 packets I requested, you can send some more")
                print "We got the " + str(numResentRecv) + " resent packets"
                resentLoop +=1
                return 1
            if(totalNumRecv == int(numChunksToRecv)):
                # We've got all the chunks we were supposed to get for the whole transfer, let's close the socket and files
                tcp_sock.send("I got all the data")
                sock.close()
                tcp_sock.close()
                print "File received, we got " + str(totalNumRecv) + " chunks"
                time.sleep(.5)
                gb = round(os.path.getsize("t1.txt")/10e8,2)
                tb = round(os.path.getsize("t1.txt")/10e11,4)
                print "Total data: " + str(os.path.getsize("t1.txt")) + " bytes = " + str(gb) + "GB = " + str(tb) + "TB"
                terminate_signal.set()
    except socket.timeout:
        print "We didn't get all the packets that were resent, gotta get them back somehow"
        print "But we did get a total of " + str(totalNumRecv) + " chunks ("+str(numResentRecv)+" were resent packets)"
        return 0



def transfer_statistics(progMult, badPacks, totalPacksRecv):
    print "-------Transfer statistics-------"
    print str(progMult*5) + "% of data received"
    percentLost = float(badPacks/totalPacksRecv)
    print "Total number of lost packets: "+ str(badPacks) + " ("+ str(percentLost )+"% of total transfer)\n"
    
########################################
########################################

def Recv():
    global canRecv
    global numRecv
    global totalNumRecv
    global chunkIDsRecv
    global progressMultiplier
    global loop
        
    try:
        while(canRecv):
            sock.settimeout(2)
            dataChunk, addr = sock.recvfrom(buf)
            packID, junkAddr = sock.recvfrom(buf)
            if(packID.isdigit() and dataChunk):
                numRecv += 1
                totalNumRecv += 1
                '''
                Once we've received an ID, we want to store it in a list. We put it in the index that corresponds to it's ID number
                and flag it as received (with a 1). Once we've timed out, we can check this list to see what we're missing
                '''
                chunkIDsRecv[int(packID) - (loop*numChunksRequested)] = 1
                writeBuffer.appendleft(dataChunk)  # append to LEFT of write
                '''
                Provide a progress/status update to the operator
                TODO: We also want to let the server know that we've gotten this much data too
                '''
                if(totalNumRecv*buf >= progressMultiplier * .05 * totalNumBytesToRecv):
                    transfer_statistics(progressMultiplier, badPacket, totalNumRecv)
                    progressMultiplier += 1
            else:
                logging.warning("Something got fucked up - either lost data packet, or missing ID number")
                global badPacket
                badPacket += 1
           
            if(numRecv == numChunksRequested):
                # We've got the packets we asked for, let's alert the server to this fact
                tcp_sock.send("I got the 60 packets I requested, you can send some more")
                #print "We got " + str(numRecv) + " packets"
                loop += 1
                numRecv = 0
                chunkIDsRecv = [0] * numChunksRequested     #Clear out the cache
                continue
            if(totalNumRecv == int(numChunksToRecv)):
                # We've got all the chunks we were supposed to get for the whole transfer, let's close the socket and files
                tcp_sock.send("I got all the data")
                sock.close()
                tcp_sock.close()
                print "File received, we got " + str(totalNumRecv) + " chunks"
                time.sleep(.5)
                gb = round(os.path.getsize("t1.txt")/10e8,2)
                tb = round(os.path.getsize("t1.txt")/10e11,4)
                print "Total data: " + str(os.path.getsize("t1.txt")) + " bytes = " + str(gb) + "GB = " + str(tb) + "TB"
                terminate_signal.set()
                canRecv = False 
    except socket.timeout:
        '''
        Something happened, and we didn't get all the packets we requested in time (we timed out).
        Let's not let the server panic, and tell him what happened,and how many packets we got so far.
        '''
        print "Timed out, but have no fear, we got " + str(numRecv) + " chunks"
        # The number of chunks I'm still waiting on
        numINeed = numChunksRequested - numRecv    
        canRecv = False
        '''
        Now we have to figure out what packets we're missing (by checking our list), and telling the server
        to send us those missing packets before we can be get move on to the next round
        
        The packets we want are packets from our list that don't have a 1 as their list value
        Remember, the list is as such: Index: ID_NUM    Value: 1/0    
        '''
        packetsINeed = []
        for i in xrange(0, len(chunkIDsRecv)):
            if chunkIDsRecv[i] is 0:
                packetsINeed.append(i)
        
        print "Packets I need: " + str(packetsINeed) + " -- Length: "+str(len(packetsINeed)) + "\n"
        tcp_sock.send(str(packetsINeed))
        canRecv = True
        if(RecvResentPackets(writeBuffer, len(packetsINeed))):
            #TODO: Figure out how to go back to the main receiving loop
            #We successfully received all the data that was resent, go back to the main receiving loop
            print "Received resent data"
            loop +=1
            chunkIDsRecv = [0] * (numChunksRequested)  # List of IDs received 
            Recv();
            
        else:
            #TODO: Figure out what we do with the missing resent data?
            #We didn't get all of the resent data, now what the fuck do we do?
            print "FIXME"
        
if __name__ == '__main__':
    Recv()        
