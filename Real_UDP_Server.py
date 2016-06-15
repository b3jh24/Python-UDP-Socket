'''
Created on Jun 14, 2016

Server (sender) for a UDP file transfer

Read the data in from a file, chunk it into 32KB chunks (32000 bytes), send each chunk as a 
datagram to client

@author: bhornak
'''

"""
Issues: 
Chunking works as it's supposed to, but the UDP transfer loses data, need to work on creating
a way to identify each chunk being sent (label it or something like that), and then make sure 
we get it on the receiving end

SEE: http://www.binarytides.com/python-packet-sniffer-code-linux/
[Important info for getting packet data]

"""

from socket import *
import sys
from PacketSniffer import get_checksum, get_dest_port, get_source_port

s = socket(AF_INET,SOCK_DGRAM)
host ="127.0.0.1"
port = 5005
buf = 32000
addr = (host,port)

count = 0

def read_in_chunks(infile, chunk_size=buf):
    """Chunk the file before we send it.
    Arguements:
    infile -- the file to chunk
    chunk_size -- the size of the chunk in bytes (default 32KB)
    """

    # TODO: Get checksums for each packet - right now I need root privileges

    while True:
        chunk = infile.read(chunk_size)
        if chunk:
            yield chunk
        else:
            # The chunk was empty, which means we're at the end of the file
            return

f = open('file.txt', 'rb')
for chunk in read_in_chunks(f):
    count += 1
    print "Source: ", str(get_source_port())
    if(s.sendto(chunk,addr)):
        if(get_dest_port() == str(port) and get_source_port() == str(port)):
            cs = get_checksum()
            print "CS: ",cs
            print "sending ..."
            print "\t\t Count: ",count
        
s.close()        
f.close()
print "File sent!"

